#!/usr/bin/env python3
"""Variant-to-event links within participants, and variant-to-event-to-peptide chains.
CORRECTED October 2026: no SUPPA PSI / diffSplice (strand-affected). Isoform events are the annotated
SUPPA events that produced a PGDB protein; a link records an SV of participant P within SPLICE_WIN of the
event, plus the gene's RNA level in P from the AnswerALS consortium counts. Fusion links are unchanged.
Pooled over paths.BATCHES. Needs outputs of scripts 01-02: sv_carriers.tsv, links_peptide_event.tsv. Usage: 03_link_svs_to_events.py OUT"""
import sys, os, re, json, collections
import numpy as np, pandas as pd
OUT = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from paths import PATHS as C, BATCHES, CONTROL_LINE, rna_samples as pooled_rna_samples
PGDB, GTF = C['PGDB'], C['GTF']
MIN_LOG2CPM, SPLICE_WIN, FUSION_WIN, RARE_MAX = 1.0, 5_000, 100_000, 17
from rna_answerals import load_rna_log2cpm
from common import part
rna_samples = pooled_rna_samples()
participants = sorted({part(s) for s in rna_samples} - {None, CONTROL_LINE})

rna = load_rna_log2cpm(None, GTF, participants, counts_path=C['COUNTS'])
mp = pd.read_csv(f'{PGDB}/proteogenomic_mapping.tsv', sep='\t', dtype=str, usecols=['source', 'event_ids', 'gene_symbols'])
def suppa_key(e):
    m = re.match(r'(ENSG[0-9.]+)(?:_and_ENSG[0-9.]+)*_([A-Z0-9]+:chr.*)$', e); return f'{m.group(1)};{m.group(2)}' if m else None
ev_gene = {}
for v, g in mp[mp.source == 'suppa'][['event_ids', 'gene_symbols']].dropna(subset=['event_ids']).itertuples(index=False):
    for x in re.split(r'[;,]', v):
        k = suppa_key(x)
        if k: ev_gene.setdefault(k, str(g).split(';')[0])
pg_events = set(ev_gene)
def coords(e):
    m = re.search(r':(chr[^:]+):(.*):([+-])$', e)
    if not m: return None
    n = [int(x) for x in re.findall(r'\d+', m.group(2))]; return m.group(1), min(n), max(n)
events = sorted(pg_events)
by_chr = collections.defaultdict(list)
for e in events:
    c = coords(e)
    if c: by_chr[c[0]].append((c[1], c[2], e))
arr = {k: (np.array([a for a, _, _ in v]), np.array([b for _, b, _ in v]), [x for _, _, x in v]) for k, v in by_chr.items()}

sv = pd.read_csv(f'{OUT}/sv_carriers.tsv', sep='\t')
rows = []
for r in sv.itertuples():
    if r.chrom not in arr: continue
    S, E, names = arr[r.chrom]
    m = (S <= r.end + SPLICE_WIN) & (E >= r.pos - SPLICE_WIN)
    for i in np.flatnonzero(m):
        e = names[i]; g = ev_gene.get(e)
        v = float(rna.at[g, r.participant]) if g in rna.index and r.participant in rna.columns else None
        inside = S[i] >= r.pos and E[i] <= r.end
        rows.append(dict(participant=r.participant, sv_id=r.sv_id, svtype=r.svtype, chrom=r.chrom, sv_pos=r.pos, sv_end=r.end,
                         sv_len=r.end - r.pos, n_cohort_carriers=r.n_cohort_carriers, rare=r.n_cohort_carriers <= RARE_MAX,
                         relation='event_within_sv' if inside else 'sv_within_5kb', layer='isoform_event', event=e, gene=g,
                         rna_gene_log2cpm=v, rna_gene_expressed=(v is not None and v >= MIN_LOG2CPM)))
# fusions: same-chromosome DEL/DUP whose breakends sit near both fusion breakpoints
fm = pd.read_csv(f'{PGDB}/fusion.metadata.tsv', sep='\t', dtype=str, usecols=['sample_id', 'fusion_name', 'chrom1', 'chrom2', 'breakpoint1', 'breakpoint2'])
fm = fm[fm.sample_id.isin(rna_samples)].drop_duplicates(['sample_id', 'fusion_name'])
svg = {p: g for p, g in sv.groupby('participant')}
for f in fm.itertuples():
    p = part(f.sample_id)
    if f.chrom1 != f.chrom2 or p not in svg: continue
    g = svg[p]; g = g[g.chrom == f.chrom1]
    b = sorted([int(f.breakpoint1), int(f.breakpoint2)])
    h = g[((g.pos - b[0]).abs() <= FUSION_WIN) & ((g.end - b[1]).abs() <= FUSION_WIN)]
    for r in h.itertuples():
        rows.append(dict(participant=p, sv_id=r.sv_id, svtype=r.svtype, chrom=r.chrom, sv_pos=r.pos, sv_end=r.end, sv_len=r.end - r.pos,
                         n_cohort_carriers=r.n_cohort_carriers, rare=r.n_cohort_carriers <= RARE_MAX, relation='sv_spans_fusion_breakpoints',
                         layer='fusion', event=f.fusion_name, gene=None, rna_gene_log2cpm=None, rna_gene_expressed=None))
e2 = pd.DataFrame(rows, columns=['participant', 'sv_id', 'svtype', 'chrom', 'sv_pos', 'sv_end', 'sv_len', 'n_cohort_carriers', 'rare', 'relation', 'layer', 'event', 'gene', 'rna_gene_log2cpm', 'rna_gene_expressed']).drop_duplicates(); e2.to_csv(f'{OUT}/links_variant_event.tsv', sep='\t', index=False)
try:
    e1 = pd.read_csv(f'{OUT}/links_peptide_event.tsv', sep='\t')
except pd.errors.EmptyDataError:      # no peptide->event links in stage 1
    e1 = pd.DataFrame(columns=['participant', 'peptide', 'pgdb_id', 'layer', 'event', 'gene', 'rna_evidence', 'rna_gene_log2cpm'])
ch = e2.merge(e1, on=['participant', 'layer', 'event'], suffixes=('', '_pep')); ch.to_csv(f'{OUT}/chains_variant_event_peptide.tsv', sep='\t', index=False)
def s(df):
    if not len(df): return {'links': 0}
    return {'links': len(df), 'participants': df.participant.nunique(), 'events': df.event.nunique(),
            'events_by_layer': df.groupby('layer').event.nunique().to_dict(),
            'events_with_rna_gene_expressed': int(df[df.get('rna_gene_expressed', pd.Series(False, index=df.index)).fillna(False).astype(bool)].event.nunique()) if 'rna_gene_expressed' in df else None} | (
           {'events_with_rare_sv': int(df[df.rare.astype(bool)].event.nunique()), 'rare_links': int(df.rare.astype(bool).sum()),
            'events_inside_sv': int(df[df.relation == 'event_within_sv'].event.nunique())} if 'rare' in df else {})
out = {'participants': len(participants), 'annotated_isoform_events_with_pgdb_product': len(events),
       'fusion_calls': len(fm), 'batches': BATCHES, 'sv_carrier_rows': len(sv),
       'E1_peptide_event': s(e1), 'E2_variant_event': s(e2), 'chains': s(ch),
       'params': dict(MIN_LOG2CPM=MIN_LOG2CPM, SPLICE_WIN=SPLICE_WIN, FUSION_WIN=FUSION_WIN, RARE_MAX=RARE_MAX, rna_source='AnswerALS release 7')}
json.dump(out, open(f'{OUT}/summary.json', 'w'), indent=2, default=str); print(json.dumps(out, indent=2, default=str))
