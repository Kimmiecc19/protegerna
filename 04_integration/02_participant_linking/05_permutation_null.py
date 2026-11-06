#!/usr/bin/env python3
"""Stage 5: permutation null for Stage 4. Keep every SV-gene pair and its number of carriers (pooled batches),
but give the 'carrier' label to random participants; count how many pairs pass the same effect
rules. Gives an empirical p-value and FDR for the observed counts. Usage: 13e_permutation_null.py OUT [N_PERM]"""
import sys, os, json
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
OUT = sys.argv[1]; NPERM = int(sys.argv[2]) if len(sys.argv) > 2 else 200
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obj4_paths import PATHS as C, load_protein_by_gene
GTF = C['GTF']
from rna_answerals import load_rna_log2cpm   # CORRECTED Oct 2026: AnswerALS counts replace rnasplice TPMs
Z_SINGLE, LFC_MIN, P_MAX, MIN_CPM, MIN_DETECT = 2.5, 0.5, 0.05, 1.0, 0.5
res = pd.read_csv(f'{OUT}/variant_gene_rna_protein.tsv', sep='\t')
prot = load_protein_by_gene()
rna = load_rna_log2cpm(GTF, set(prot.columns), counts_path=C['COUNTS'])
rna = rna[rna.index.isin(set(res.gene))]; rna = rna[(2 ** rna - 1).median(axis=1) >= MIN_CPM]
parts = sorted(set(prot.columns) & set(rna.columns)); idx = {p: i for i, p in enumerate(parts)}
def prep(mat, need):
    out = {}
    for g in set(res.gene):
        if g in mat.index:
            x = mat.loc[g, parts].values.astype(float)
            if np.mean(~np.isnan(x)) >= need: out[g] = x
    return out
PM, RM = prep(prot, MIN_DETECT), prep(rna, 0.0)
def eff(x, car):
    m = np.zeros(len(x), bool); m[car] = True
    a, b = x[m & ~np.isnan(x)], x[~m & ~np.isnan(x)]
    if len(a) == 0 or len(b) < 5: return False
    med = np.median(b); mad = 1.4826 * np.median(np.abs(b - med)); lfc = np.median(a) - med
    if abs(lfc) < LFC_MIN: return False
    if len(a) == 1: return mad > 0 and abs(lfc / mad) >= Z_SINGLE
    return mannwhitneyu(a, b).pvalue < P_MAX
pairs = [(r.gene, [idx[c] for c in str(r.carriers_measured).split(';') if c in idx]) for r in res.itertuples()]
def count(rng=None):
    n_p = n_r = n_b = 0
    for g, car in pairs:
        if not car: continue
        if rng is not None: car = list(rng.choice(len(parts), len(car), replace=False))
        ep = g in PM and eff(PM[g], car); er = g in RM and eff(RM[g], car)
        n_p += ep; n_r += er; n_b += ep and er
    return n_p, n_r, n_b
obs = count(); rng = np.random.default_rng(1)
null = np.array([count(rng) for _ in range(NPERM)])
out = {}
for i, k in enumerate(['protein_effects', 'rna_effects', 'rna_and_protein']):
    out[k] = dict(observed=int(obs[i]), null_mean=round(float(null[:, i].mean()), 1), null_95pct=float(np.percentile(null[:, i], 95)),
                  empirical_p=round(float((1 + (null[:, i] >= obs[i]).sum()) / (NPERM + 1)), 4),
                  est_FDR=round(float(min(1, null[:, i].mean() / obs[i])), 2) if obs[i] else None)
out['n_perm'] = NPERM
json.dump(out, open(f'{OUT}/permutation_null_summary.json', 'w'), indent=2); print(json.dumps(out, indent=2))
