#!/usr/bin/env python3
r"""
16_integration_evaluation_table.py  -  Objective 4: does integration change the interpretation of each candidate?

For every candidate that a single layer would put forward, this script records the single-layer conclusion,
the evidence from the other layers in the same participants, the integrated conclusion, the change class
(confirmed / rejected / reclassified / unchanged) and the evidence level (Table 6.6 of the chapter):

  1 technical            the candidate passes its own layer's QC (audit, fusion filters, peptide FDR)
  2 molecular consequence an effect in another layer in the same participants
  3 cross-layer concordance consistent effects in at least two downstream layers
  4 disease association   ALS vs healthy controls at FDR < 0.05

Candidate categories
  primary_SV        Objective 2 audited primary candidates (carriers = participant_support support_rule_met)
  ALS_gene_SV       SVs overlapping ALSoD genes from the script-15 scans (BH within ALSoD genes)
  novel_peptide     variant-only peptides absent from UniProt and GENCODE (script 06); fusion-derived ones are
                    tested for co-occurrence with the RNA fusion call in the same participants (Fisher)
  isoform_peptide   variant-only peptides that are known UniProt isoforms or GENCODE-only; RNA check = gene
                    expressed (CPM >= 1) in >= 90% of peptide-positive participants, detected in >= 50% of a batch
  recurrent_fusion  filtered fusions with >= 3 carriers (script 12); checked against SV carriers in the partner genes
                    and against fusion-derived peptides
  DE_gene           genes at FDR < 0.05 in the RNA (01) or protein (02) ALS vs HC analysis, checked in the other layer

Carrier tests (SVs) use the same statistic as script 15: expression residualised on seq_batch + sex + diagnosis,
z-scored per gene; S = mean(carrier z) * sqrt(k); empirical p from the same carriers on 1,000 random genes.
Protein carrier tests use per-run median-centred log2 intensities, z-scored per protein, same statistic.

Usage (PowerShell; replace <...>):
  python 16_integration_evaluation_table.py `
    --rna-counts <...>\AnswerALS-1276-T-v1-release7_raw-counts.csv `
    --rna-coldata "<...>\remove_btc_raw_coldata_filtered (2).csv" --gene-map <...>\ensg_symbol.tsv `
    --sv-primary <Obj2>\primary_candidates.tsv --sv-support <Obj2>\participant_support.tsv `
    --sv-scan <15 out>\intersection_sv_gene_expression_tests.tsv <15 out>\union_only_sv_gene_expression_tests.tsv `
    --sv-tables <...>\Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv <...>\Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv `
    --peptides results\peptide_sources_b4to6\variant_only_peptides.tsv --protein-cohort <...>\cohort_samples.tsv `
    --fusion-dir results\fusions_oct2026 `
    [--spectral-review spectral_review.tsv] `
    [--protein-gene-matrix <07 out>\protein_by_participant_gene.log2.tsv] `
    [--rna-results <01 output>.csv] [--protein-results <02 output>.csv] `
    --outdir results\integration_evaluation

--spectral-review: TSV with columns peptide, verdict (pass / fail), optional note.

Outputs
  evaluation_full.tsv        every candidate (one row per candidate x gene)
  evaluation_main_table.tsv  the rows for the thesis table (all categories except the bulk of isoform peptides
                             and null ALS-gene SVs, which are summarised)
  evaluation_summary.tsv     counts per category x change class and per category x evidence level
  summary.json
"""
import argparse, json, os, re, warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
import numpy as np, pandas as pd
from scipy import stats

FDR, NOM = 0.05, 0.05
MIN_CPM, EXPR_FRAC, REPRO = 1.0, 0.9, 0.5
LARGE_SV = 10_000
CONTROL_LINE = 'CTRL-NEUEU392AE8'
POLYMORPHIC_17Q21 = {"KANSL1", "ARL17A", "ARL17B", "LRRC37A", "LRRC37A2", "LRRC37A3", "LRRC37A4P", "NSF", "MAPT",
                     "CRHR1", "KANSL1-AS1", "MAPK8IP1P2"}
rx = re.compile(r'(CASE|CTRL)[-_](NEU[A-Z0-9]+)')
part = lambda s: (lambda m: f'{m.group(1)}-{m.group(2)}' if m else None)(rx.search(str(s)))


def bh(p):
    p = np.asarray(p, float); out = np.full(len(p), np.nan); ok = ~np.isnan(p)
    if ok.sum() == 0: return out
    q = p[ok]; o = np.argsort(q); n = len(q)
    r = q[o] * n / np.arange(1, n + 1); r = np.minimum.accumulate(r[::-1])[::-1]
    tmp = np.empty(n); tmp[o] = np.minimum(r, 1); out[ok] = tmp; return out


# ------------------------------------------------------------------ data loaders
def load_rna(counts, coldata, gene_map):
    cd = pd.read_csv(coldata); cd['participant'] = cd.iloc[:, 0].map(part)
    cd = cd.drop_duplicates('participant').set_index('participant')
    raw = pd.read_csv(counts, encoding='utf-8-sig', low_memory=False)
    gcol = next(c for c in raw.columns if raw[c].astype(str).head(100).str.startswith('ENSG').mean() > 0.9)
    raw[gcol] = raw[gcol].astype(str).str.split('.').str[0]; raw = raw.set_index(gcol)
    cols = [c for c in raw.columns if part(c) in cd.index]
    cnt = raw[cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    cnt.columns = [part(c) for c in cols]; cnt = cnt.T.groupby(level=0).sum().T
    cpm = cnt / cnt.sum() * 1e6
    gm = pd.read_csv(gene_map, sep='\t', header=None, names=['ensg', 'sym']).drop_duplicates('ensg').set_index('ensg').sym
    cpm = cpm.loc[cpm.index.intersection(gm.index)]
    cpm = cpm.groupby(gm.reindex(cpm.index).values).sum()                    # symbol x participant
    expr = cpm[cpm.mean(axis=1) >= MIN_CPM]
    lg = np.log2(expr + 1); P = list(lg.columns); meta = cd.loc[P]
    X = pd.get_dummies(meta[['seq_batch', 'sex', 'condition']], drop_first=True).astype(float)
    X.insert(0, 'icpt', 1.0); X = X.values; Y = lg.values.T
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None); R = Y - X @ beta
    Z = pd.DataFrame(R / R.std(axis=0, ddof=X.shape[1]), index=P, columns=lg.index)
    return Z, cpm, meta


def load_protein(matrix, samples, pgdb_meta):
    pm = pd.read_csv(matrix, sep='\t', index_col=0, na_values=['NA', ''])
    ps = pd.read_csv(samples, sep='\t')
    ps = ps[(ps.sample_type == 'participant') & ps.cohort_run.isin(pm.columns)]
    pm = pm[ps.cohort_run]; pm = pm - pm.median()
    meta = pd.read_csv(pgdb_meta, sep='\t', dtype=str); id2gene = dict(zip(meta.sequence_id, meta.gene))
    def pg_gene(pg):
        g = {id2gene.get(i) for i in re.findall(r'PGDB_U\d+', str(pg))} - {None, 'NA', ''}
        return g.pop() if len(g) == 1 else None
    pm.index = [pg_gene(i) for i in pm.index]; pm = pm[pm.index.notna()].groupby(level=0).mean()
    pm.columns = [part(p) for p in ps.participant_id]; pm = pm.T.groupby(level=0).mean()   # participant x gene
    return (pm - pm.mean()) / pm.std()


class CarrierTest:
    """S = mean(z of carriers) * sqrt(k); empirical p from the same carriers on random genes."""
    def __init__(self, Z, n_null=1000, seed=1):
        self.Z, self.n_null, self.rng = Z, n_null, np.random.default_rng(seed)
        self.pidx = {p: i for i, p in enumerate(Z.index)}; self.V = Z.values
    def __call__(self, gene, carriers):
        if self.Z is None or gene not in self.Z.columns: return dict(status='not_measured')
        ci = [self.pidx[c] for c in carriers if c in self.pidx]
        if not ci: return dict(status='no_carrier_measured')
        if len(ci) > len(self.pidx) / 2: return dict(status='too_common')
        z = self.V[ci, self.Z.columns.get_loc(gene)]; z = z[~np.isnan(z)]
        if len(z) == 0: return dict(status='no_carrier_measured')
        S = z.mean() * np.sqrt(len(z))
        js = self.rng.integers(0, self.V.shape[1], self.n_null)
        nul = self.V[np.ix_(ci, js)]; k = (~np.isnan(nul)).sum(0)
        nS = np.nanmean(nul, 0) * np.sqrt(np.maximum(k, 1)); nS = nS[k > 0]
        p = (np.sum(np.abs(nS) >= abs(S)) + 1) / (len(nS) + 1)
        return dict(status='tested', k=len(z), mean_z=float(z.mean()), p=float(p))


def direction(sv_type):
    return {'DEL': -1, 'DUP': 1}.get(str(sv_type).upper(), 0)


def effect_ok(res, d, p_col='p', thr=NOM):
    """significant (by the chosen p/q column) and in the expected direction (any direction if d == 0)."""
    if res.get('status') != 'tested' or res.get(p_col) is None or np.isnan(res.get(p_col, np.nan)): return False
    return res[p_col] < thr and (d == 0 or np.sign(res['mean_z']) == d)


# ------------------------------------------------------------------ SV classification
def classify_sv(r, rna, prot, rna_q):
    d = direction(r['sv_type']); length = abs(float(r.get('sv_length_bp') or 0))
    size_note = (f"{r['sv_type']} of {length/1000:.1f} kb: " +
                 ("within the size range where the positive control shows expression effects" if length >= LARGE_SV and d
                  else "below the size range where SVs typically change expression (positive control)"))
    rna_eff = rna.get('status') == 'tested' and rna_q is not None and not np.isnan(rna_q) and rna_q < FDR and \
        (d == 0 or np.sign(rna['mean_z']) == d)
    prot_eff = effect_ok(prot, d)
    if rna.get('status') != 'tested':
        return ('unchanged', 1, f"Not assessable in RNA ({rna.get('status')}). {size_note}.")
    if rna_eff and prot_eff:
        return ('confirmed', 3, f"Carriers show RNA (q = {rna_q:.3g}) and protein (p = {prot['p']:.3g}) "
                                f"in the expected direction. {size_note}.")
    if rna_eff:
        return ('confirmed', 2, f"Carriers show an RNA change in the expected direction (q = {rna_q:.3g}); protein "
                                f"{prot.get('status', 'not measured')}. {size_note}.")
    if effect_ok(rna, d):
        return ('unchanged', 1, f"Exploratory RNA signal only (p = {rna['p']:.3g}, q = {rna_q:.3g}). {size_note}.")
    return ('reclassified', 1, f"No detectable RNA effect in {rna['k']} carrier(s) (p = {rna['p']:.3g}). {size_note}.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rna-counts', required=True); ap.add_argument('--rna-coldata', required=True)
    ap.add_argument('--gene-map', required=True)
    ap.add_argument('--sv-primary', required=True); ap.add_argument('--sv-support', required=True)
    ap.add_argument('--sv-scan', nargs='+', required=True); ap.add_argument('--sv-tables', nargs='*', default=[])
    ap.add_argument('--peptides', required=True); ap.add_argument('--protein-cohort', required=True)
    ap.add_argument('--fusion-dir', required=True); ap.add_argument('--spectral-review')
    ap.add_argument('--protein-gene-matrix', help='07 output protein_by_participant_gene.log2.tsv (preferred)')
    ap.add_argument('--protein-matrix'); ap.add_argument('--protein-samples'); ap.add_argument('--pgdb-metadata')
    ap.add_argument('--rna-results'); ap.add_argument('--protein-results')
    ap.add_argument('--outdir', required=True); ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=False); out = lambda f: os.path.join(a.outdir, f)

    Z, cpm, rmeta = load_rna(a.rna_counts, a.rna_coldata, a.gene_map)
    rna_test = CarrierTest(Z, seed=a.seed)
    if a.protein_gene_matrix:
        pg = pd.read_csv(a.protein_gene_matrix, sep='\t', index_col=0, na_values=['NA', ''])
        pg.columns = [part(c) for c in pg.columns]; pg = pg.T
        PZ = (pg - pg.mean()) / pg.std()
    else:
        PZ = load_protein(a.protein_matrix, a.protein_samples, a.pgdb_metadata) if a.protein_matrix else None
    prot_test = CarrierTest(PZ, seed=a.seed + 1) if PZ is not None else (lambda g, c: dict(status='not_measured'))
    rna_parts = set(Z.index)
    print(f'RNA: {len(rna_parts)} participants; protein: {0 if PZ is None else len(PZ)} participants')
    rows = []

    # ============ 1. primary SV candidates
    prim = pd.read_csv(a.sv_primary, sep='\t', dtype=str)
    sup = pd.read_csv(a.sv_support, sep='\t', dtype=str)
    sup = sup[sup.support_rule_met.str.lower() == 'true']
    prim_rows = []
    for r in prim.itertuples():
        car = sorted({part(s) for s in sup.loc[sup.event_id == r.event_id, 'sample_id']} - {None})
        for g in str(r.genes).split(';'):
            prim_rows.append(dict(event_id=r.event_id, gene=g, sv_type=r.sv_type, sv_length_bp=r.sv_length_bp,
                                  alsod=r.highest_alsod_evidence, carriers=car,
                                  rna=rna_test(g, car), prot=prot_test(g, car)))
    q = bh([x['rna'].get('p', np.nan) for x in prim_rows])
    for x, qq in zip(prim_rows, q):
        cls, lvl, why = classify_sv(x, x['rna'], x['prot'], qq)
        rows.append(dict(category='primary_SV', candidate=x['event_id'], gene=x['gene'], alsod=x['alsod'],
                         single_layer_source='DNA (Objective 2 audit)',
                         single_layer_conclusion=f"Prioritised {x['sv_type']} candidate in {x['gene']} "
                                                 f"({len(x['carriers'])} audited carriers)",
                         DNA=f"{len(x['carriers'])} audited carriers",
                         RNA=fmt(x['rna'], qq), protein=fmt(x['prot']), peptide='',
                         change_class=cls, evidence_level=lvl, integrated_conclusion=why))
    prim_keys = {(x['event_id'], x['gene']) for x in prim_rows}

    # ============ 2. ALS-gene SVs from the genome-wide scan
    scan = pd.concat([pd.read_csv(f, sep='\t') for f in a.sv_scan], ignore_index=True)
    al = scan[scan.alsod_gene.astype(str).str.lower() == 'true'].sort_values('p_empirical') \
        .drop_duplicates(['event_id', 'gene']).copy()
    al['q_alsod'] = bh(al.p_empirical.values)
    for r in al.itertuples():
        if (r.event_id, r.gene) in prim_keys: continue
        car = str(r.carriers).split(';')
        rres = dict(status='tested', k=int(r.n_carriers_rna), mean_z=float(r.mean_z), p=float(r.p_empirical))
        pres = prot_test(r.gene, car)
        cls, lvl, why = classify_sv(dict(sv_type=r.sv_type, sv_length_bp=r.sv_length_bp), rres, pres, r.q_alsod)
        rows.append(dict(category='ALS_gene_SV', candidate=r.event_id, gene=r.gene, alsod='ALSoD gene',
                         single_layer_source=f'DNA (AnnotSV {r.table} table)',
                         single_layer_conclusion=f"{r.sv_type} overlapping ALS gene {r.gene} ({r.n_carriers_wgs} carriers)",
                         DNA=f"{r.n_carriers_wgs} carriers ({r.n_carriers_rna} with RNA)", RNA=fmt(rres, r.q_alsod),
                         protein=fmt(pres), peptide='', change_class=cls, evidence_level=lvl, integrated_conclusion=why,
                         _len=abs(r.sv_length_bp), _p=r.p_empirical))

    # ============ shared inputs for peptides / fusions
    peps = pd.read_csv(a.peptides, sep='\t')
    coh = pd.read_csv(a.protein_cohort, sep='\t', dtype=str)
    coh = coh[coh.sample_type == 'participant']; coh['participant'] = coh.participant_id.map(part)
    batch_parts = coh.groupby('batch').participant.apply(set).to_dict()
    fpath = os.path.join(a.fusion_dir, 'fusion_calls_all.tsv')
    fus = pd.read_csv(fpath if os.path.exists(fpath) else fpath + '.gz', sep='\t', low_memory=False)
    man = pd.read_csv(os.path.join(a.fusion_dir, 'sample_manifest.tsv'), sep='\t')
    fus_parts = set(man.participant.dropna()) - {CONTROL_LINE}
    fus['pair_dash'] = fus.pair.astype(str).str.replace('--', '-', regex=False)
    review = {}
    if a.spectral_review:
        sr = pd.read_csv(a.spectral_review, sep='\t', dtype=str)
        review = {r.peptide: (str(r.verdict).lower(), getattr(r, 'note', '')) for r in sr.itertuples()}
    pep_parts = lambda r: set(str(r.participants).split(';')) - {'', 'nan'}
    def universe(r):
        u = set().union(*[batch_parts.get(b, set()) for b in str(r.batches).split(';')])
        return u - {CONTROL_LINE}
    def gene_list(s): return sorted({x.replace('GN=', '') for x in str(s).split(';')} - {'', 'nan'})
    def expressed_frac(genes, parts):
        best = np.nan
        for g in genes:
            if g in cpm.index:
                v = cpm.loc[g, [p for p in parts if p in cpm.columns]]
                if len(v): best = np.nanmax([best, float((v >= MIN_CPM).mean())]) if not np.isnan(best) else float((v >= MIN_CPM).mean())
        return best

    # ============ 3. novel peptides
    fusion_peptide_support = {}
    nov = peps[peps.peptide_class.str.startswith('novel')]
    for r in nov.itertuples():
        pp, U = pep_parts(r), universe(r) & fus_parts
        genes = gene_list(r.genes); verdict, vnote = review.get(r.peptide, ('pending', ''))
        spectral = f'spectral review: {verdict}' + (f' ({vnote})' if vnote else '')
        if 'fusioninspector' in str(r.sources):
            calls = fus[fus.pair_dash.isin(genes)]
            fc, fpass = set(calls.participant) & U, set(calls[calls.pass_core].participant) & U
            ppU = pp & U
            t = [[len(ppU & fc), len(ppU - fc)], [len(fc - ppU), len(U - ppU - fc)]]
            OR, p = stats.fisher_exact(t, alternative='greater') if len(U) else (np.nan, np.nan)
            rna_txt = (f"RNA fusion called in {len(ppU & fc)}/{len(ppU)} peptide-positive vs "
                       f"{len(fc - ppU)}/{len(U - ppU)} peptide-negative participants (Fisher p = {p:.3g}); "
                       f"{len(fpass)} participants with a call passing filters")
            supported = (p < NOM) and len(fpass) > 0
            for g in genes: fusion_peptide_support[g] = (supported, r.peptide, p)
            if verdict == 'fail':
                cls, lvl, why = 'rejected', 1, f'Failed spectral review. {rna_txt}.'
            elif supported:
                cls, lvl, why = 'confirmed', 2, f'Peptide tracks the RNA fusion in the same participants. {rna_txt}; {spectral}.'
            else:
                cls, lvl, why = 'rejected', 1, (f'Peptide detection is independent of the RNA fusion, so the fusion is '
                                                f'not supported as its source. {rna_txt}; {spectral}.')
        else:
            ef = expressed_frac(genes, pp)
            rna_txt = f"gene expressed (CPM >= {MIN_CPM}) in {ef:.0%} of peptide-positive participants" if not np.isnan(ef) \
                else 'gene not in RNA data'
            if verdict == 'fail':
                cls, lvl, why = 'rejected', 1, f'Failed spectral review; {rna_txt}.'
            else:
                cls, lvl, why = 'unchanged', 1, (f'RNA cannot test the splice event because splicing quantification was '
                                                 f'excluded; {rna_txt}; {spectral}.')
        rows.append(dict(category='novel_peptide', candidate=r.peptide, gene=';'.join(genes), alsod='',
                         single_layer_source='Proteogenomic search (v5)',
                         single_layer_conclusion=f'Novel peptide ({r.sources}) in {r.n_participants_detected} participants',
                         DNA='', RNA=rna_txt, protein='', peptide=f"{r.n_participants_detected} participants; "
                         f"max {r.max_fraction_runs_detected:.0%} of a batch's runs", change_class=cls,
                         evidence_level=lvl, integrated_conclusion=why))

    # ============ 4. isoform peptides
    iso = peps[~peps.peptide_class.str.startswith('novel')]
    for r in iso.itertuples():
        pp, genes = pep_parts(r), gene_list(r.genes)
        ef = expressed_frac(genes, pp)
        repro = r.max_fraction_runs_detected >= REPRO
        if not np.isnan(ef) and ef >= EXPR_FRAC and repro:
            cls, lvl, why = 'confirmed', 2, (f'Isoform peptide reproducibly detected and the gene is expressed in '
                                             f'{ef:.0%} of the same participants.')
        elif not repro:
            cls, lvl, why = 'unchanged', 1, 'Sporadically detected peptide (< 50% of runs in every batch).'
        else:
            cls, lvl, why = 'unchanged', 1, ('Gene not expressed in the peptide-positive participants or not in the RNA '
                                             'data' if np.isnan(ef) else f'Gene expressed in only {ef:.0%} of peptide-positive participants.')
        rows.append(dict(category='isoform_peptide', candidate=r.peptide, gene=';'.join(genes), alsod='',
                         single_layer_source='Proteogenomic search (v5)',
                         single_layer_conclusion=f'{r.peptide_class} peptide ({r.sources})', DNA='',
                         RNA='' if np.isnan(ef) else f'expressed in {ef:.0%} of peptide-positive participants',
                         protein='', peptide=f"{r.n_participants_detected} participants; max {r.max_fraction_runs_detected:.0%} of a batch's runs",
                         change_class=cls, evidence_level=lvl, integrated_conclusion=why))

    # ============ 5. recurrent fusions
    rec = pd.read_csv(os.path.join(a.fusion_dir, 'fusion_recurrence_tests.tsv'), sep='\t')
    svt = pd.concat([pd.read_csv(f, sep='\t', low_memory=False, usecols=['event_id', 'sv_type', 'genes', 'samples'])
                     for f in a.sv_tables], ignore_index=True) if a.sv_tables else pd.DataFrame()
    wgs_parts = {part(x) for v in svt.samples.dropna() for x in v.split(';')} if len(svt) else set()
    fusion_rows = []
    for r in rec.itertuples():
        g1, g2 = r.fusion_pair.split('--', 1)
        carriers = set(fus[(fus.pair == r.fusion_pair) & fus.pass_core].participant)
        best = (np.nan, '', '')
        if len(svt):
            U = wgs_parts & fus_parts; fc = carriers & U
            hit = svt[svt.genes.fillna('').str.split(';').map(lambda gs: g1 in gs or g2 in gs)]
            for h in hit.itertuples():
                sc = {part(x) for x in str(h.samples).split(';')} & U
                if not sc or len(sc) > len(U) / 2: continue
                t = [[len(sc & fc), len(sc - fc)], [len(fc - sc), len(U - sc - fc)]]
                p = stats.fisher_exact(t, alternative='greater')[1]
                if np.isnan(best[0]) or p < best[0]:
                    best = (p, h.event_id, f'{len(sc & fc)}/{len(fc)} fusion carriers carry {h.event_id}')
        pep = [fusion_peptide_support[k] for k in (r.fusion_pair.replace('--', '-'), ) if k in fusion_peptide_support]
        fusion_rows.append(dict(r=r, g1=g1, g2=g2, n=len(carriers), sv_p=best[0], sv_event=best[1], sv_txt=best[2], pep=pep))
    qs = bh([x['sv_p'] for x in fusion_rows])
    for x, q in zip(fusion_rows, qs):
        r = x['r']; poly = {x['g1'], x['g2']} & POLYMORPHIC_17Q21
        dna_ok = not np.isnan(q) and q < FDR
        pep_ok = bool(x['pep']) and x['pep'][0][0]
        notes = []
        if poly: notes.append('partner in the polymorphic 17q21.31 inversion region')
        if r.padj_BH < FDR: lvl4 = True
        else: lvl4 = False
        if dna_ok and pep_ok: cls, lvl = 'confirmed', 3
        elif dna_ok or pep_ok: cls, lvl = 'confirmed', 2
        else: cls, lvl = 'unchanged', 1
        if lvl4: lvl = 4
        why = (f"ALS vs HC: {r.n_ALS}/286 vs {r.n_HC}/50 (q = {r.padj_BH:.3g}). "
               f"DNA: {x['sv_txt'] + f' (q = {q:.3g})' if x['sv_event'] else 'no SV in partner genes tested'}. "
               f"Peptide: {('fusion peptide ' + ('tracks' if pep_ok else 'does not track') + ' the RNA call') if x['pep'] else 'no fusion-derived peptide'}."
               + (f" Note: {'; '.join(notes)}." if notes else ''))
        rows.append(dict(category='recurrent_fusion', candidate=r.fusion_pair, gene=f"{x['g1']};{x['g2']}", alsod='ALS gene partner' if str(r.als_gene_partner) == 'True' else '',
                         single_layer_source='RNA fusion calling (filtered)',
                         single_layer_conclusion=f"Recurrent filtered fusion in {x['n']} participants",
                         DNA=x['sv_txt'], RNA=f"{x['n']} carriers; ALS vs HC q = {r.padj_BH:.3g}",
                         protein='', peptide='' if not x['pep'] else f"peptide {x['pep'][0][1]}", change_class=cls,
                         evidence_level=lvl, integrated_conclusion=why, _n=x['n']))

    # ============ 6. DE genes (RNA or protein), checked in the other layer
    def load_de(path):
        if not path: return None
        d = pd.read_csv(path); name = 'gene_name' if 'gene_name' in d else 'gene'
        d = d.dropna(subset=[name]).sort_values('P.Value').drop_duplicates(name).set_index(name)
        return d[['logFC', 'P.Value', 'adj.P.Val']]
    R, Pn = load_de(a.rna_results), load_de(a.protein_results)
    for lay, A, B, other in (('RNA', R, Pn, 'protein'), ('protein', Pn, R, 'RNA')):
        if A is None: continue
        for g, x in A[A['adj.P.Val'] < FDR].iterrows():
            if lay == 'protein' and R is not None and g in R.index and R.loc[g, 'adj.P.Val'] < FDR: continue  # listed once, under RNA
            if B is None or g not in B.index:
                cls, why = 'unchanged', f'{other} not measured for this gene.'
            else:
                y = B.loc[g]
                if y['P.Value'] < NOM and np.sign(y.logFC) == np.sign(x.logFC):
                    cls, why = 'confirmed', f'Same direction in {other} (logFC {y.logFC:.2f}, p = {y["P.Value"]:.3g}).'
                elif y['P.Value'] < NOM:
                    cls, why = 'reclassified', f'Opposite direction in {other} (logFC {y.logFC:.2f}, p = {y["P.Value"]:.3g}).'
                else:
                    cls, why = 'unchanged', f'No change in {other} (p = {y["P.Value"]:.3g}).'
            rows.append(dict(category='DE_gene', candidate=g, gene=g, alsod='', single_layer_source=f'{lay} ALS vs HC',
                             single_layer_conclusion=f'{lay} logFC {x.logFC:.2f}, q = {x["adj.P.Val"]:.3g}',
                             DNA='', RNA='' if lay != 'RNA' else f'logFC {x.logFC:.2f}, q = {x["adj.P.Val"]:.3g}',
                             protein='' if lay != 'protein' else f'logFC {x.logFC:.2f}, q = {x["adj.P.Val"]:.3g}',
                             peptide='', change_class=cls, evidence_level=4, integrated_conclusion=why))

    # ============ outputs
    ev = pd.DataFrame(rows)
    cols = ['category', 'candidate', 'gene', 'alsod', 'single_layer_source', 'single_layer_conclusion', 'DNA', 'RNA',
            'protein', 'peptide', 'integrated_conclusion', 'change_class', 'evidence_level']
    ev[cols].to_csv(out('evaluation_full.tsv'), sep='\t', index=False)
    main_mask = (ev.category.isin(['primary_SV', 'novel_peptide', 'DE_gene']) |
                 ((ev.category == 'ALS_gene_SV') & ((ev.get('_len', 0) >= LARGE_SV) | (ev.get('_p', 1) < 0.01) |
                                                   (ev.change_class == 'confirmed'))) |
                 ((ev.category == 'recurrent_fusion') & ((ev.get('_n', 0) >= 10) | (ev.change_class == 'confirmed'))))
    order = {'primary_SV': 0, 'ALS_gene_SV': 1, 'novel_peptide': 2, 'recurrent_fusion': 3, 'DE_gene': 4}
    ev[main_mask].assign(_o=ev.category.map(order)).sort_values(['_o', 'evidence_level'], ascending=[True, False])[cols] \
        .to_csv(out('evaluation_main_table.tsv'), sep='\t', index=False)
    s1 = ev.pivot_table(index='category', columns='change_class', values='candidate', aggfunc='count', fill_value=0)
    s2 = ev.pivot_table(index='category', columns='evidence_level', values='candidate', aggfunc='count', fill_value=0)
    s2.columns = [f'level_{c}' for c in s2.columns]
    summ = s1.join(s2); summ['total'] = s1.sum(axis=1)
    summ.to_csv(out('evaluation_summary.tsv'), sep='\t')
    js = dict(candidates=int(len(ev)), by_category_and_class=json.loads(s1.to_json(orient='index')),
              by_category_and_level=json.loads(s2.to_json(orient='index')),
              changed_by_integration=int(ev.change_class.isin(['confirmed', 'rejected', 'reclassified']).sum()),
              inputs=vars(a), thresholds=dict(FDR=FDR, NOMINAL=NOM, MIN_CPM=MIN_CPM, EXPR_FRAC=EXPR_FRAC,
                                              REPRODUCIBLE_FRACTION=REPRO, LARGE_SV_BP=LARGE_SV))
    json.dump(js, open(out('summary.json'), 'w'), indent=2, default=str)
    print(summ.to_string())


def fmt(res, q=None):
    s = res.get('status', '')
    if s != 'tested': return s.replace('_', ' ')
    t = f"{res['k']} carriers, mean z {res['mean_z']:+.2f}, p = {res['p']:.3g}"
    return t + (f", q = {q:.3g}" if q is not None and not np.isnan(q) else '')


if __name__ == '__main__':
    main()
