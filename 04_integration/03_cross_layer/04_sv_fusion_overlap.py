#!/usr/bin/env python3
"""Objective 4, 04_sv_fusion_overlap.py: fusion transcripts explained by a rare SV in the same participant.

For every fusion call that passed filters F1-F6 (01_single_layer/01d_filter_fusions.py), find SV events carried by the
same participant that span BOTH fusion breakpoints (intrachromosomal fusions only). The chance expectation is
computed by assigning each fusion call to a random participant: for call i, P(match) = (number of participants
carrying a qualifying SV that spans both breakpoints) / (number of participants). The expected count is the sum
over calls; the p-value is the Poisson upper tail, checked by a label permutation.

For each matched case the script reports the RNA effect of the SV on every gene it overlaps (taken from the
SV carrier expression scan, 01_single_layer/01e_sv_carrier_expression_scan.py) and, where the carrier is in the v5 proteomic
cohort, the protein abundance of those genes in the carrier as a robust z-score against all other participants.

SV events and carrier lists are read from the scan output tables, so only events that overlap at least one
expressed protein-coding gene are considered.

Usage (from 04_integration/):
  python 03_cross_layer/04_sv_fusion_overlap.py \
     --fusions 01_single_layer/01d_results_filter_fusions/fusion_calls_pass.tsv \
     --sv-tests 01_single_layer/01e_results_sv_carrier_expression_scan_unfiltered/intersection_sv_gene_expression_tests.tsv \
                01_single_layer/01e_results_sv_carrier_expression_scan_unfiltered/union_only_sv_gene_expression_tests.tsv \
     --coldata data/answerals_cohort_coldata.csv \
     --protein 01_single_layer/01b_results_consolidate_proteomic_batches/protein_by_participant.log2.tsv \
     --pgdb-metadata ../03_proteogenomic_database/03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_metadata.tsv \
     --outdir 03_cross_layer/04_results_sv_fusion_overlap
"""
import argparse, json, math, os, re, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from common import pgdb_gene_mapper

rx = re.compile(r'((?:CASE|CTRL)-NEU[A-Z0-9]+)')
CONTROL_LINE = 'CTRL-NEUEU392AE8'


def poisson_sf(k, lam):
    """P(X >= k) for X ~ Poisson(lam)."""
    if k <= 0: return 1.0
    return max(0.0, 1.0 - sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--fusions', required=True)
    ap.add_argument('--sv-tests', nargs='+', required=True)
    ap.add_argument('--coldata', required=True)
    ap.add_argument('--protein'); ap.add_argument('--pgdb-metadata')
    ap.add_argument('--max-carriers', type=int, default=17, help='rare SV: at most this many carriers (5%% of 347 genomes)')
    ap.add_argument('--n-perm', type=int, default=1000)
    ap.add_argument('--outdir', required=True)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)

    fu = pd.read_csv(a.fusions, sep='\t')
    tests = pd.concat([pd.read_csv(f, sep='\t') for f in a.sv_tests], ignore_index=True)
    ev = tests.drop_duplicates('event_id')[['table', 'event_id', 'sv_type', 'sv_length_bp', 'n_carriers_wgs', 'carriers']].copy()
    ev = ev[ev.n_carriers_wgs <= a.max_carriers]
    p = ev.event_id.str.split('_', expand=True)
    ev['chrom'] = 'chr' + p[0]; ev['start'] = p[1].astype(int); ev['end'] = p[2].astype(int)
    ev['carrier_set'] = ev.carriers.astype(str).map(lambda s: set(rx.findall(s)))

    cd = pd.read_csv(a.coldata)
    cd['participant'] = cd.iloc[:, 0].astype(str).str.extract(rx, expand=False)
    cd = cd.drop_duplicates('participant').set_index('participant')
    participants = sorted(set(cd.index) - {CONTROL_LINE})
    N = len(participants)

    rows, exp, spanning_sets = [], 0.0, []
    for _, c in fu.iterrows():
        c1, b1, _ = str(c.LeftBreakpoint).split(':'); c2, b2, _ = str(c.RightBreakpoint).split(':')
        b1, b2 = int(b1), int(b2)
        if c1 != c2:
            spanning_sets.append(set()); continue
        sp = ev[(ev.chrom == c1) & (ev.start <= min(b1, b2)) & (ev.end >= max(b1, b2))]
        car = set().union(*sp.carrier_set) if len(sp) else set()
        car &= set(participants)
        spanning_sets.append(car)
        exp += len(car) / N
        for _, e in sp.iterrows():
            if c.participant in e.carrier_set:
                rows.append(dict(participant=c.participant, fusion=c.pair, junction_reads=c.JunctionReadCount,
                                 spanning_frags=c.SpanningFragCount, ffpm=c.FFPM, coding=c.PROT_FUSION_TYPE,
                                 left_breakpoint=c.LeftBreakpoint, right_breakpoint=c.RightBreakpoint,
                                 sv_event=e.event_id, sv_table=e.table, sv_type=e.sv_type, sv_length_bp=e.sv_length_bp,
                                 sv_carriers=e.n_carriers_wgs))
    hits = pd.DataFrame(rows).drop_duplicates(['participant', 'fusion', 'sv_event']) if rows else pd.DataFrame()
    obs_calls = int(hits[['participant', 'fusion', 'left_breakpoint', 'right_breakpoint']].drop_duplicates().shape[0]) if len(hits) else 0

    # label permutation: each call given to a random participant
    rng = np.random.default_rng(1)
    null = np.zeros(a.n_perm, int)
    for k in range(a.n_perm):
        draw = rng.integers(0, N, len(spanning_sets))
        null[k] = sum(participants[d] in s for d, s in zip(draw, spanning_sets) if s)
    perm_p = (1 + (null >= obs_calls).sum()) / (a.n_perm + 1)

    # RNA effects of each matched SV on the genes it overlaps (from the expression scan)
    rna = tests[tests.event_id.isin(set(hits.sv_event))][['event_id', 'gene', 'mean_z', 'p_empirical', 'fdr_empirical']] if len(hits) else pd.DataFrame()

    # protein in carriers (v5 cohort), robust z against all other participants
    prot_rows = []
    if a.protein and a.pgdb_metadata and len(hits):
        meta = pd.read_csv(a.pgdb_metadata, sep='\t', dtype=str, usecols=['sequence_id', 'gene'])
        pg_gene = pgdb_gene_mapper(dict(zip(meta.sequence_id, meta.gene)))
        pm = pd.read_csv(a.protein, sep='\t', index_col=0)
        pm.index = [pg_gene(x) for x in pm.index]
        pm = pm[pm.index.notna()].apply(pd.to_numeric, errors='coerce')
        pm = pm - pm.median()                         # median-centre each participant
        pm = pm.groupby(level=0).mean()
        for _, h in hits.iterrows():
            if h.participant not in pm.columns: continue
            for g in rna[rna.event_id == h.sv_event].gene.unique():
                if g not in pm.index:
                    prot_rows.append(dict(participant=h.participant, sv_event=h.sv_event, gene=g, protein_status='not_quantified')); continue
                x = pm.loc[g]; v = x.get(h.participant)
                others = x.drop(h.participant).dropna()
                if pd.isna(v) or len(others) < 10:
                    prot_rows.append(dict(participant=h.participant, sv_event=h.sv_event, gene=g, protein_status='not_quantified_in_carrier')); continue
                med = others.median(); mad = 1.4826 * (others - med).abs().median()
                prot_rows.append(dict(participant=h.participant, sv_event=h.sv_event, gene=g, protein_status='quantified',
                                      protein_log2_diff=round(float(v - med), 3), protein_robust_z=round(float((v - med) / mad), 2) if mad > 0 else None,
                                      n_other=len(others)))
    prot = pd.DataFrame(prot_rows)

    if len(hits):
        hits['diagnosis'] = hits.participant.map(cd['diagnosis']) if 'diagnosis' in cd else None
        hits['sex'] = hits.participant.map(cd['sex']) if 'sex' in cd else None
        hits['both_breakpoints_in_sv'] = True
    hits.to_csv(f'{a.outdir}/sv_fusion_overlap.tsv', sep='\t', index=False)
    rna.to_csv(f'{a.outdir}/sv_fusion_overlap_rna_effects.tsv', sep='\t', index=False)
    prot.to_csv(f'{a.outdir}/sv_fusion_overlap_protein_in_carriers.tsv', sep='\t', index=False)
    summ = dict(passing_fusion_calls=int(len(fu)), passing_fusion_pairs=int(fu.pair.nunique()),
                private_pairs=int((fu.groupby('pair').participant.nunique() == 1).sum()),
                participants=N, max_sv_carriers=a.max_carriers,
                calls_explained_by_rare_sv_in_same_participant=obs_calls,
                expected_by_chance=round(exp, 4), poisson_p=poisson_sf(obs_calls, exp),
                permutation_p=perm_p, n_perm=a.n_perm, null_max=int(null.max()),
                sv_types=hits.sv_type.value_counts().to_dict() if len(hits) else {},
                by_diagnosis=hits.drop_duplicates(['participant', 'fusion']).diagnosis.value_counts().to_dict() if len(hits) else {})
    json.dump(summ, open(f'{a.outdir}/summary.json', 'w'), indent=2, default=str)
    print(json.dumps(summ, indent=2, default=str))


if __name__ == '__main__':
    main()
