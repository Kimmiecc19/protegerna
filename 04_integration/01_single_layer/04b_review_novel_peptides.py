#!/usr/bin/env python3
"""
04b_review_novel_peptides.py - score-based spectral review of the ten novel peptide candidates (Chapter 6).

Input: scores_b{1..6}.tsv written by 04a_extract_spectral_scores.sh from each v5 diann_report.tsv (every row of the 649
variant-only peptides plus a systematic 1-in-150 sample of all other rows) and variant_only_peptide_classes.tsv.

Identifications are rows passing the Chapter 6 thresholds (Q.Value, Global.Q.Value and Global.PG.Q.Value
<= 0.01). For each identification the following DIA-NN evidence is summarised:
  CScore, PEP, Q.Value, Evidence, Spectrum.Similarity, Ms1.Profile.Corr
  good fragments  number of library fragments with Fragment.Correlations >= 0.7
  median fragment correlation
  |RT - Predicted.RT| (min)
and, per peptide and batch, the spread (SD) of the apex RT across runs.

Each novel candidate is compared with two reference sets from the same batch:
  isoform  known-UniProt-isoform variant-only peptides (identified with the same database, same batch)
  background  sampled reference-explained identifications
restricted to peptides of similar length (+/- 3 residues). The candidate's median for each score is
expressed as a percentile of the per-peptide medians of the background peptides.

Pre-specified verdict (per candidate, using its best-supported batch):
  Five evidence dimensions are flagged when the candidate's median is in the worst 10% of the reference
  identifications (same batch, length +/- 3, intensity +/- 0.5 log10):
    confidence (CScore; PEP and q-values are derived from it and are not counted separately),
    spectrum similarity, fragment co-elution (good-fragment count or median fragment correlation),
    RT prediction error (|RT - Predicted.RT|), and RT reproducibility across runs (SD of apex RT, against
    known-isoform peptides of the same batch with >= 10 identifications, length-matched when possible).
  fail  if two or more dimensions are flagged
  pass  otherwise
  The verdict is score-based only; visual inspection of fragment XICs is still recommended for any pass.

Usage: python 04b_review_novel_peptides.py IN_DIR OUT_PREFIX
"""
import sys, os
import numpy as np, pandas as pd

IN, OUT = sys.argv[1], sys.argv[2]
cls = pd.read_csv(os.path.join(IN, 'variant_only_peptide_classes.tsv'), sep='\t')
cls = dict(zip(cls.peptide, cls.peptide_class))
NUM = ['Q.Value', 'PEP', 'Global.Q.Value', 'Global.PG.Q.Value', 'Precursor.Quantity', 'RT', 'Predicted.RT',
       'Ms1.Profile.Corr', 'Evidence', 'Spectrum.Similarity', 'Mass.Evidence', 'CScore']

frames = []
for b in range(1, 7):
    d = pd.read_csv(os.path.join(IN, f'scores_b{b}.tsv'), sep='\t', low_memory=False)
    for c in NUM: d[c] = pd.to_numeric(d[c], errors='coerce')
    d = d[(d['Q.Value'] <= 0.01) & (d['Global.Q.Value'] <= 0.01) & (d['Global.PG.Q.Value'] <= 0.01)].copy()
    fc = d['Fragment.Correlations'].fillna('').str.strip(';').str.split(';')
    fcv = fc.map(lambda v: np.array([float(x) for x in v if x not in ('', 'nan')]))
    d['good_fragments'] = fcv.map(lambda a: int((a >= 0.7).sum()))
    d['median_frag_corr'] = fcv.map(lambda a: float(np.median(a)) if len(a) else np.nan)
    d['abs_dRT'] = (d['RT'] - d['Predicted.RT']).abs()
    d['length'] = d['Stripped.Sequence'].str.len()
    d['class'] = d['Stripped.Sequence'].map(cls).fillna('reference (background sample)')
    d.loc[(d.set == 'background') & d['Stripped.Sequence'].isin(cls), 'class'] = 'drop'
    frames.append(d[d['class'] != 'drop'])
d = pd.concat(frames, ignore_index=True)
d['group'] = d['class'].map({'known UniProt isoform': 'isoform', 'novel candidate (not in UniProt or GENCODE)': 'novel'}).fillna('background')

FEAT = ['CScore', 'PEP', 'Q.Value', 'Evidence', 'Spectrum.Similarity', 'Ms1.Profile.Corr', 'good_fragments', 'median_frag_corr', 'abs_dRT']
# per peptide x batch medians (identifications pooled over precursors)
g = d.groupby(['group', 'batch', 'Stripped.Sequence'])
pep = g[FEAT].median()
pep['n_ids'] = g.size()
pep['RT_sd'] = g['RT'].std()
pep['length'] = g['length'].first()
pep['log10_intensity'] = np.log10(g['Precursor.Quantity'].median())
pep = pep.reset_index()

LOW = ['CScore', 'Spectrum.Similarity', 'median_frag_corr', 'good_fragments', 'Evidence']   # low = worse
HIGH = ['PEP', 'abs_dRT']                                                                   # high = worse


def midrank_pct(ref, x):
    ref = ref.dropna().values
    if len(ref) == 0 or pd.isna(x): return np.nan
    return 100 * ((ref < x).sum() + 0.5 * (ref == x).sum()) / len(ref)


rows = []
li = np.log10(d['Precursor.Quantity'].clip(lower=1))
nov = pep[pep.group == 'novel']
for _, r in nov.iterrows():
    out = dict(peptide=r['Stripped.Sequence'], batch=r.batch, length=int(r.length), n_identifications=int(r.n_ids),
               log10_intensity=round(r.log10_intensity, 2))
    ids = d[(d.group == 'novel') & (d.batch == r.batch) & (d['Stripped.Sequence'] == r['Stripped.Sequence'])]
    out['frac_ids_Q_gt_0.005'] = round(float((ids['Q.Value'] > 0.005).mean()), 3)
    out['frac_ids_runPGQ_gt_0.01'] = round(float((pd.to_numeric(ids['PG.Q.Value'], errors='coerce') > 0.01).mean()), 3)
    # identification-level reference rows: same batch, length +/- 3, intensity +/- 0.5 log10
    for ref in ('background', 'isoform'):
        R = d[(d.group == ref) & (d.batch == r.batch) & d.length.between(r.length - 3, r.length + 3) &
              (li - r.log10_intensity).abs().le(0.5)]
        out[f'n_{ref}_ids'] = len(R)
        for f in FEAT:
            out[f'{f}_pct_vs_{ref}'] = round(midrank_pct(R[f], r[f]), 1)
    # RT reproducibility across runs, against isoform peptides of the same batch with >= 10 identifications
    Ri = pep[(pep.group == 'isoform') & (pep.batch == r.batch) & (pep.n_ids >= 10)]
    Rl = Ri[Ri.length.between(r.length - 3, r.length + 3)]
    if len(Rl) >= 10: Ri = Rl
    out['n_isoform_peptides_RT'] = len(Ri)
    out['RT_sd_pct_vs_isoform'] = round(midrank_pct(Ri['RT_sd'], r['RT_sd']), 1)
    for f in FEAT + ['RT_sd']:
        out[f] = round(float(r[f]), 4) if pd.notna(r[f]) else np.nan
    P = lambda f: out.get(f'{f}_pct_vs_background', 50)
    flags = []
    if P('CScore') < 10: flags.append('confidence (CScore)')          # PEP and q-values derive from CScore
    if P('Spectrum.Similarity') < 10: flags.append('spectrum similarity')
    if P('good_fragments') < 10 or P('median_frag_corr') < 10: flags.append('fragment co-elution')
    if P('abs_dRT') > 90: flags.append('RT prediction error')
    if out['RT_sd_pct_vs_isoform'] > 90: flags.append('RT reproducibility')
    out['flags'] = ';'.join(flags)
    out['n_flags'] = len(flags)
    rows.append(out)
res = pd.DataFrame(rows).sort_values(['peptide', 'n_identifications'], ascending=[True, False])
best = res.groupby('peptide').head(1).copy()
best['verdict'] = np.where(best.n_flags >= 2, 'fail', 'pass')
res.to_csv(OUT + '_by_batch.tsv', sep='\t', index=False)
best.to_csv(OUT + '_summary.tsv', sep='\t', index=False)
best['note'] = 'score-based review; flags: ' + best['flags'].replace('', 'none').fillna('none')
best[['peptide', 'verdict', 'note']].to_csv(os.path.join(os.path.dirname(OUT) or '.', 'spectral_review.tsv'), sep='\t', index=False)

# reference distributions (for the write-up)
ref = pep[pep.n_ids >= 3].groupby('group')[['CScore', 'PEP', 'Spectrum.Similarity', 'median_frag_corr', 'good_fragments', 'abs_dRT', 'RT_sd']].median()
ref.to_csv(OUT + '_reference_medians.tsv', sep='\t')
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
print(ref.round(3))
cols=['peptide','batch','n_identifications','n_background_ids']+[c for c in best.columns if c.endswith('_pct_vs_background')]+['RT_sd_pct_vs_isoform','frac_ids_Q_gt_0.005','frac_ids_runPGQ_gt_0.01','flags','verdict']
print(best[cols].to_string(index=False))
