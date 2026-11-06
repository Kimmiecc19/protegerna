#!/usr/bin/env python3
"""Stage 4: variant -> gene-level RNA expression and protein abundance (carrier test).
For every rare SV (<= RARE_MAX cohort carriers) overlapping a protein-coding gene (+/- FLANK),
compare carriers vs non-carriers among participants of the pooled batches (obj4_paths.BATCHES) for:
  RNA      : log2(CPM+1) from the AnswerALS consortium raw counts (release 7)
             [CORRECTED Oct 2026: replaces strand-affected rnasplice Salmon TPMs]
  protein  : log2 DIA-NN PG.MaxLFQ (pg_matrix, v5 search), genes via PGDB metadata, median-centred per run
Runs from the same participant (e.g. the repeated control line) are averaged first.
Evidence tiers: A = protein and RNA effect; B = protein or RNA effect; C = neither.
(The Stage 3 splice carrier test used strand-affected PSI and has been removed.)
Usage: 13d_protein_rna_link.py OUT"""
import sys, os, re, json
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
OUT = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obj4_paths import PATHS as C, BATCHES, load_protein_by_gene
GTF = C['GTF']
from rna_answerals import load_rna_log2cpm
RARE_MAX, FLANK, MIN_DETECT = 17, 5_000, 0.5          # 17 = 5% of 347; protein must be quantified in >=50% of participants
Z_SINGLE, LFC_MIN, P_MAX, MIN_CPM = 2.5, 0.5, 0.05, 1.0
# --- gene coordinates (protein-coding genes)
genes = []
with open(GTF) as f:
    for l in f:
        if l.startswith('#'): continue
        t = l.split('\t', 9)
        if t[2] != 'gene' or 'gene_type "protein_coding"' not in t[8]: continue
        gid = re.search(r'gene_id "([^"]+)"', t[8]).group(1); gn = re.search(r'gene_name "([^"]+)"', t[8]).group(1)
        genes.append((t[0], int(t[3]), int(t[4]), gid, gn))
genes = pd.DataFrame(genes, columns=['chrom', 'start', 'end', 'gene_id', 'gene'])

# --- omics matrices -> participant x gene
prot = load_protein_by_gene()                                 # gene x participant, pooled batches
rna = load_rna_log2cpm(GTF, set(prot.columns), counts_path=C['COUNTS'])                 # participant x gene log2(CPM+1)
rna = rna[rna.index.isin(set(genes.gene))]                        # protein-coding genes
rna = rna[(2 ** rna - 1).median(axis=1) >= MIN_CPM]               # expressed genes only (median CPM >= 1)
participants = sorted(set(prot.columns) & set(rna.columns))

# --- rare SVs overlapping genes
sv = pd.read_csv(f'{OUT}/sv_carriers.tsv', sep='\t')
sv = sv[sv.n_cohort_carriers <= RARE_MAX]
pairs = []
for chrom, g in sv.groupby('chrom'):
    gc = genes[genes.chrom == chrom]
    if gc.empty: continue
    S, E = gc.start.values - FLANK, gc.end.values + FLANK
    for (sid, pos, end, svt, n), car in g.groupby(['sv_id', 'pos', 'end', 'svtype', 'n_cohort_carriers']).participant:
        for i in np.flatnonzero((S <= end) & (E >= pos)):
            r = gc.iloc[i]
            rel = 'whole_gene' if pos <= r.start and end >= r.end else ('within_gene' if pos <= r.end and end >= r.start else 'flank_5kb')
            pairs.append(dict(sv_id=sid, chrom=chrom, sv_pos=pos, sv_end=end, svtype=svt, sv_len=end - pos, n_cohort_carriers=n,
                              gene=r.gene, gene_id=r.gene_id, relation=rel, carriers=sorted(set(car))))

def test(mat, gene, carriers, need_detect):
    if gene not in mat.index: return dict(status='not_measured')
    x = mat.loc[gene, participants]
    if x.notna().mean() < need_detect: return dict(status='low_detection')
    a, b = x[x.index.isin(carriers)].dropna(), x[~x.index.isin(carriers)].dropna()
    if len(a) == 0: return dict(status='missing_in_carrier')
    med, mad = b.median(), 1.4826 * (b - b.median()).abs().median()
    z = (a.median() - med) / mad if mad > 0 else np.nan
    p = mannwhitneyu(a, b).pvalue if len(a) >= 2 else np.nan
    lfc = a.median() - med
    eff = abs(lfc) >= LFC_MIN and ((len(a) == 1 and abs(z) >= Z_SINGLE) or (len(a) >= 2 and p < P_MAX))
    return dict(status='tested', n_car=len(a), n_non=len(b), log2fc=lfc, robust_z=z, p=p, effect=bool(eff),
                direction='down' if lfc < 0 else 'up')
rows = []
for pr in pairs:
    car = [c for c in pr['carriers'] if c in participants]
    if not car: continue
    r = {k: v for k, v in pr.items() if k != 'carriers'}; r['carriers_measured'] = ';'.join(car)
    for lay, mat, nd in (('rna', rna, 0.0), ('prot', prot, MIN_DETECT)):
        for k, v in test(mat, pr['gene'], car, nd).items(): r[f'{lay}_{k}'] = v
    rows.append(r)
res = pd.DataFrame(rows)

pd.set_option('future.no_silent_downcasting', True)
res['rna_effect'] = res.rna_effect.astype('boolean').fillna(False).astype(bool); res['prot_effect'] = res.prot_effect.astype('boolean').fillna(False).astype(bool)
res['n_layers_beyond_dna'] = res.rna_effect.astype(int) + res.prot_effect.astype(int)
res['concordant_down'] = res.rna_effect & res.prot_effect & (res.rna_direction == res.prot_direction)
res['tier'] = np.select([res.prot_effect & res.rna_effect, res.n_layers_beyond_dna >= 1], ['A', 'B'], 'C')
res = res.sort_values(['tier', 'n_layers_beyond_dna', 'n_cohort_carriers'], ascending=[True, False, True])
res.to_csv(f'{OUT}/variant_gene_rna_protein.tsv', sep='\t', index=False)
summ = dict(batches=BATCHES, participants=len(participants), rare_sv_gene_pairs=len(res), protein_tested=int((res.prot_status == 'tested').sum()),
            rna_tested=int((res.rna_status == 'tested').sum()), prot_effect=int(res.prot_effect.sum()),
            rna_effect=int(res.rna_effect.sum()), concordant_rna_protein=int((res.rna_effect & res.prot_effect & (res.rna_direction == res.prot_direction)).sum()),
            tiers=res.tier.value_counts().to_dict(),
            params=dict(RARE_MAX=RARE_MAX, FLANK=FLANK, MIN_DETECT=MIN_DETECT, Z_SINGLE=Z_SINGLE, MIN_CPM=MIN_CPM, LFC_MIN=LFC_MIN, P_MAX=P_MAX,
                        rna_source='AnswerALS release 7 raw counts, log2(CPM+1)'))
json.dump(summ, open(f'{OUT}/variant_gene_rna_protein_summary.json', 'w'), indent=2, default=str)
print(json.dumps(summ, indent=2, default=str))
pd.set_option('display.width', 250)
cols = ['tier', 'gene', 'svtype', 'sv_len', 'relation', 'n_cohort_carriers', 'carriers_measured', 'rna_log2fc', 'rna_robust_z', 'prot_log2fc', 'prot_robust_z', 'prot_p']
print(res[res.tier != 'C'][cols].head(40).to_string())
