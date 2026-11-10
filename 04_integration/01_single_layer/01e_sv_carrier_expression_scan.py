#!/usr/bin/env python3
"""
01e_sv_carrier_expression_scan.py  -  do structural variants change expression of the genes they overlap?

Genome-wide carrier vs non-carrier RNA scan for every SV event in one or more AnnotSV event
prioritisation tables (intersection and/or union-only), using AnswerALS release-7 counts.

Expression: log2(CPM+1) per participant; protein-coding genes with mean CPM >= 1; residualised per gene
on seq_batch + sex + condition (OLS) and standardised to z (residual / residual SD).
Per event x overlapped gene: k carriers with RNA; statistic S = mean(z_carriers) * sqrt(k)
(~N(0,1) under no effect); p from the normal; BH-FDR within each table.
Calibration: the same carrier sets scored on random expressed genes (empirical null, 20 draws per pair);
reported as genomic inflation lambda and as an empirical p per pair.
Positive control: expected direction (DEL down, DUP up) by SV length bin.

Usage: python 01e_sv_carrier_expression_scan.py --tables <intersection.tsv> [<union_only.tsv>]
         --labels intersection union_only --counts <AnswerALS release7 csv> --coldata <remove_btc_raw_coldata_filtered (2).csv>
         --gene-map <ensg_symbol.tsv: ENSG<TAB>symbol>  --outdir <new folder>
         [--max-carrier-frac 0.5] [--alsod <alsod_gene_list.csv>]
"""
import argparse, os, sys, json
import numpy as np, pandas as pd
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from common import part, bh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tables', nargs='+', required=True); ap.add_argument('--labels', nargs='+', required=True)
    ap.add_argument('--counts', required=True); ap.add_argument('--coldata', required=True)
    ap.add_argument('--gene-map', required=True); ap.add_argument('--alsod')
    ap.add_argument('--max-carrier-frac', type=float, default=0.5)
    ap.add_argument('--min-mean-cpm', type=float, default=1.0)
    ap.add_argument('--outdir', required=True); ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=False); out = lambda f: os.path.join(a.outdir, f)
    rng = np.random.default_rng(a.seed)

    # ---- expression
    cd = pd.read_csv(a.coldata); cd['participant'] = cd.iloc[:, 0].map(part)
    cd = cd.drop_duplicates('participant').set_index('participant')
    raw = pd.read_csv(a.counts, encoding='utf-8-sig', low_memory=False)
    gcol = next(c for c in raw.columns if raw[c].astype(str).head(100).str.startswith('ENSG').mean() > 0.9)
    raw[gcol] = raw[gcol].astype(str).str.split('.').str[0]; raw = raw.set_index(gcol)
    cols = [c for c in raw.columns if part(c) in cd.index]
    cnt = raw[cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    cnt.columns = [part(c) for c in cols]; cnt = cnt.T.groupby(level=0).sum().T
    cpm = cnt / cnt.sum() * 1e6
    gm = pd.read_csv(a.gene_map, sep='\t', header=None, names=['ensg', 'sym']).drop_duplicates('ensg')
    cpm = cpm.loc[cpm.index.intersection(gm.ensg)]
    cpm = cpm[cpm.mean(axis=1) >= a.min_mean_cpm]
    sym = gm.set_index('ensg').sym.reindex(cpm.index)
    lg = np.log2(cpm + 1)
    lg = lg.groupby(sym.values).mean()                       # one row per symbol
    P = list(lg.columns); meta = cd.loc[P]
    X = pd.get_dummies(meta[['seq_batch', 'sex', 'condition']], drop_first=True).astype(float)
    X.insert(0, 'icpt', 1.0); X = X.values
    Y = lg.values.T                                           # participants x genes
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None); R = Y - X @ beta
    Z = R / R.std(axis=0, ddof=X.shape[1])
    Z = pd.DataFrame(Z, index=P, columns=lg.index)
    pidx = {p: i for i, p in enumerate(P)}; N = len(P)
    print(f'RNA: {N} participants, {Z.shape[1]} expressed protein-coding genes')

    alsod = set()
    if a.alsod:
        al = pd.read_csv(a.alsod); alsod = set(al.iloc[:, 0].astype(str).str.upper())  # case-insensitive: ALSoD writes e.g. 'EphA3'

    allres, summ = [], {'rna_participants': N, 'expressed_genes': int(Z.shape[1])}
    Zv = Z.values; gpos = {g: j for j, g in enumerate(Z.columns)}
    for path, lab in zip(a.tables, a.labels):
        d = pd.read_csv(path, sep='\t', low_memory=False)
        wgs = {part(x) for v in d.samples.dropna() for x in v.split(';')}
        both = wgs & set(P)
        rows = []
        for r in d.itertuples(index=False):
            if not isinstance(r.genes, str) or not isinstance(r.samples, str): continue
            car = sorted({part(x) for x in r.samples.split(';')} & both)
            k = len(car)
            if k == 0 or k > a.max_carrier_frac * len(both): continue
            ci = [pidx[c] for c in car]
            # non-carriers = WGS participants with RNA who do not carry the event
            for g in set(r.genes.split(';')):
                if g not in gpos: continue
                z = Zv[ci, gpos[g]]
                rows.append(dict(table=lab, event_id=r.event_id, sv_type=r.sv_type, sv_length_bp=r.sv_length_bp,
                                 gene=g, alsod_gene=g.upper() in alsod or (isinstance(r.alsod_gene_hits, str) and g in r.alsod_gene_hits),
                                 manual_review_priority=r.manual_review_priority, n_carriers_wgs=r.sample_count,
                                 n_carriers_rna=k, carriers=';'.join(car), carrier_z=';'.join(f'{v:.2f}' for v in z),
                                 mean_z=z.mean(), S=z.mean() * np.sqrt(k), _ci=ci))
        res = pd.DataFrame(rows)
        if res.empty: continue
        res['p'] = 2 * stats.norm.sf(np.abs(res.S))
        # empirical null: same carrier sets on random genes
        G = Zv.shape[1]; nullS = []
        for ci in res._ci:
            js = rng.integers(0, G, 20); nullS.append(Zv[np.ix_(ci, js)].mean(axis=0) * np.sqrt(len(ci)))
        nullS = np.array(nullS)
        srt = np.sort(np.abs(nullS.ravel()))
        res['p_empirical'] = (srt.size - np.searchsorted(srt, np.abs(res.S.values), side='left') + 1) / (srt.size + 1)  # pooled null
        res['fdr'] = bh(res.p); res['fdr_empirical'] = bh(res.p_empirical)
        lam = np.median(res.S ** 2) / stats.chi2.ppf(0.5, 1); lam0 = np.median(nullS.ravel() ** 2) / stats.chi2.ppf(0.5, 1)
        res['expected_dir'] = np.where(res.sv_type == 'DEL', -1, np.where(res.sv_type == 'DUP', 1, 0))
        res['len_bin'] = pd.cut(res.sv_length_bp.abs(), [0, 1e3, 1e4, 1e5, 1e9], labels=['<1kb', '1-10kb', '10-100kb', '>100kb'])
        directed = res[res.expected_dir != 0].assign(_in_dir=lambda x: np.sign(x.S) == x.expected_dir)
        pc = (directed.groupby(['sv_type', 'len_bin'], observed=True)
              .agg(pairs=('S', 'size'), median_mean_z=('mean_z', 'median'),
                   frac_nominal_p05=('p_empirical', lambda x: (x < 0.05).mean()),
                   frac_in_expected_direction=('_in_dir', 'mean'), _k=('_in_dir', 'sum')).reset_index())
        pc['sign_test_p'] = [stats.binomtest(int(k), int(n), 0.5).pvalue for k, n in zip(pc._k, pc.pairs)]
        pc = pc.drop(columns='_k')
        pc.insert(0, 'table', lab); pc.to_csv(out(f'{lab}_positive_control_by_length.tsv'), sep='\t', index=False)
        res = res.drop(columns=['_ci']).sort_values('p_empirical')
        res.to_csv(out(f'{lab}_sv_gene_expression_tests.tsv'), sep='\t', index=False)
        summ[lab] = dict(events_in_table=int(len(d)), wgs_participants=len(wgs), wgs_with_rna=len(both),
                         event_gene_pairs_tested=int(len(res)), events_tested=int(res.event_id.nunique()),
                         genes_tested=int(res.gene.nunique()), lambda_observed=round(float(lam), 3), lambda_null=round(float(lam0), 3),
                         fdr05_pairs=int((res.fdr_empirical < 0.05).sum()), fdr10_pairs=int((res.fdr_empirical < 0.10).sum()),
                         fdr05_alsod_pairs=int(((res.fdr_empirical < 0.05) & res.alsod_gene).sum()),
                         alsod_pairs_tested=int(res.alsod_gene.sum()),
                         alsod_nominal_p05=int(((res.p_empirical < 0.05) & res.alsod_gene).sum()))
        allres.append(res)
    json.dump(summ, open(out('summary.json'), 'w'), indent=2)
    print(json.dumps(summ, indent=2))


if __name__ == '__main__':
    main()
