#!/usr/bin/env python3
"""Objective 4 feasibility: count within-participant links across genome (SV),
transcriptome (fusion / gene expression) and proteome (DIA peptides), pooled over the batches in lib/paths.py BATCHES
(default batches 1-6; RNA batch N and quantms-diann batch N contain the same participants).

CORRECTED October 2026: the rnasplice SUPPA PSI and diffSplice results were produced with the
wrong library strandedness and are no longer used. Splice-isoform peptides are linked to the
ANNOTATED event of their PGDB entry, with participant-level RNA support taken from gene
expression in the AnswerALS consortium count matrix (log2 CPM), not from PSI.

Links (all within the SAME participant):
  E1 peptide -> event : novel peptide detected in P; fusion peptides need the fusion called in P's RNA;
                        isoform peptides are linked to their annotated event and report the gene's RNA level in P
  E2 variant -> event : SV carried by P lies within/near the splice event or fusion breakpoints seen in P
  chain               : variant -> event -> peptide
Run:  python3 01_link_peptides_to_events.py <out_dir>
"""
import sys, os, re, csv, json, collections
import pandas as pd
csv.field_size_limit(10**9)
OUT = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from paths import PATHS as C, BATCHES, CONTROL_LINE, dia_file, dia_runs, excluded_runs, rna_samples as pooled_rna_samples
PGDB = C['PGDB']
GTF = C['GTF']
SVVCF = C['SV_VCF']
REF_FASTAS = [C['UNIPROT_REF'], C['UNIPROT_ISO']]
MIN_LOG2CPM, SPLICE_WIN, FUSION_WIN, RARE_MAX = 1.0, 5_000, 100_000, 17   # gene 'expressed' if log2(CPM+1) >= 1; 17 = 5% of 347
from rna_answerals import load_rna_log2cpm
from common import part, read_fasta_seqs
os.makedirs(OUT, exist_ok=True)
log = {}

# ---------- participants (RNA samples of the pooled batches; technical control line excluded)
rna_samples = pooled_rna_samples()
participants = sorted({part(s) for s in rna_samples} - {None, CONTROL_LINE})
log['participants'] = len(participants)

# ---------- proteome: detected precursors per participant
pr_by_batch = [pd.read_csv(dia_file(b, 'pr'), sep='\t', low_memory=False) for b in BATCHES]
runs = [c for b, t in zip(BATCHES, pr_by_batch) for c in dia_runs(b, t.columns)]   # control line + failed runs (EXCLUDE_RUNS) dropped
pr = pd.concat(pr_by_batch, ignore_index=True)
run_part = {r: part(r) for r in runs}
meta = pd.read_csv(f'{PGDB}/proteogenomic_metadata.tsv', sep='\t', dtype=str)
src = dict(zip(meta.sequence_id, meta.source))
mp = pd.read_csv(f'{PGDB}/proteogenomic_mapping.tsv', sep='\t', dtype=str,
                 usecols=['sequence_id', 'sequence_sha256', 'source', 'event_ids', 'gene_symbols', 'event_types'])
def ids(s): return [x.split('|')[1] for x in s.split(';')]
pr['pgdb_ids'] = pr['Protein.Ids'].map(ids)
pr['sources'] = pr['pgdb_ids'].map(lambda l: set(src.get(i, '?') for i in l))
nov = pr[pr.sources.map(lambda s: not any('reference' in x or 'crap' in x for x in s))].copy()
log['precursors_total'] = len(pr); log['precursors_nonreference_entries_only'] = len(nov)

# strict novelty: peptide (I/L-equivalent) absent from UniProt canonical + isoforms
refstr = '#'.join(read_fasta_seqs(REF_FASTAS)).replace('I', 'L')
peps = nov['Stripped.Sequence'].unique()
novel_set = {p for p in peps if p.replace('I', 'L') not in refstr}
# FIX 15 Oct 2026: E1 previously ran on the 6 strictly novel peptides only, so the 557 known-isoform
# peptides were never linked. All variant-only peptides now enter E1; novelty is kept as a label.
nov['novel'] = nov['Stripped.Sequence'].isin(novel_set)
log['unique_peptides_nonref_entries'] = len(peps); log['unique_peptides_absent_from_uniprot_incl_isoforms'] = len(novel_set)

rows = []
for _, r in nov.iterrows():
    det = sorted({run_part[c] for c in runs if pd.notna(r[c])} - {None})
    for i in r.pgdb_ids:
        rows.append(dict(peptide=r['Stripped.Sequence'], pgdb_id=i, source=src.get(i), genes=r['Genes'], participants=';'.join(det), n_participants=len(det), novel=bool(r['novel'])))
varpep = pd.DataFrame(rows)                                  # all variant-only peptides (for E1)
novpep = varpep[varpep.novel].drop(columns='novel') if len(varpep) else varpep
novpep.to_csv(f'{OUT}/novel_peptides_detected.tsv', sep='\t', index=False)   # unchanged output: novel only

# ---------- transcriptome: per-participant event evidence
# gene-level RNA expression per participant (AnswerALS consortium counts; replaces SUPPA PSI)
rna = load_rna_log2cpm(None, GTF, participants, counts_path=C['COUNTS'])
log['rna_participants_with_expression'] = int(rna.shape[1])
def rna_level(gene, p):
    if not isinstance(gene, str) or gene not in rna.index or p not in rna.columns: return None
    return float(rna.at[gene, p])
def suppa_key(e):   # PGDB event id -> SUPPA local event id "ENSG;TYPE:coords"
    m = re.match(r'(ENSG[0-9.]+)(?:_and_ENSG[0-9.]+)*_([A-Z0-9]+:chr.*)$', e)
    return f'{m.group(1)};{m.group(2)}' if m else None

# fusions: PGDB sequence -> samples (via sha256), samples of the pooled batches only
fs = pd.read_csv(f'{PGDB}/fusion.sequence_samples.tsv', sep='\t', dtype=str,
                 usecols=['sequence_hash', 'sequence_type', 'sample_id', 'fusion_name', 'pair_token'])
fs = fs[(fs.sequence_type == 'protein') & fs.sample_id.isin(rna_samples)]
fmeta = pd.read_csv(f'{PGDB}/fusion.metadata.tsv', sep='\t', dtype=str,
                    usecols=['sample_id', 'fusion_name', 'pair_token', 'chrom1', 'chrom2', 'breakpoint1', 'breakpoint2', 'contributing_caller_count'])
fmeta = fmeta[fmeta.sample_id.isin(rna_samples)]
log['fusion_calls'] = len(fmeta.drop_duplicates(['sample_id', 'fusion_name']))
sha = dict(zip(mp.sequence_id, mp.sequence_sha256))

# ---------- E1: peptide -> event in the same participant
E1_COLS = ['participant', 'peptide', 'pgdb_id', 'layer', 'event', 'gene', 'rna_evidence', 'rna_gene_log2cpm', 'novel']
_e1f = f'{OUT}/links_peptide_event.tsv'
def _has_rows(f):
    try:
        with open(f) as fh: return sum(1 for _ in fh) > 1
    except OSError: return False
REUSE = _has_rows(_e1f)      # FIX 15 Oct 2026: an empty or header-only file is rebuilt, not reused
e1 = []
# one PGDB id can have several source records -> aggregate (indexing a duplicated index returns a Series)
ev_by_id = mp.dropna(subset=['event_ids']).groupby('sequence_id').event_ids.apply(lambda x: ';'.join(x)).to_dict()
gene_by_id = mp.dropna(subset=['gene_symbols']).groupby('sequence_id').gene_symbols.first().to_dict()
# FIX 15 Oct 2026: one PGDB id can have SUPPA, rMATS and FusionInspector records; use all of them, not the single metadata source
srcs_by_id = mp.dropna(subset=['source']).groupby('sequence_id').source.apply(lambda x: '+'.join(sorted(set(x)))).to_dict()
for _, r in ([] if REUSE else varpep.iterrows()):
    parts_det = set(r.participants.split(';')) if r.participants else set()
    s = (srcs_by_id.get(r.pgdb_id) or r.source or '').lower()
    if 'fusioninspector' in s:
        hit = fs[fs.sequence_hash == sha.get(r.pgdb_id)]
        for _, h in hit.iterrows():
            p = part(h.sample_id)
            if p in parts_det:
                e1.append(dict(participant=p, peptide=r.peptide, pgdb_id=r.pgdb_id, layer='fusion', event=h.fusion_name,
                               rna_evidence='fusion_called_in_participant', rna_gene_log2cpm=None, novel=r.novel))
    if 'suppa' in s:
        evs = ev_by_id.get(r.pgdb_id, '')
        gene = gene_by_id.get(r.pgdb_id, '').split(';')[0] or None
        for e in set(filter(None, (suppa_key(x) for x in re.split(r'[;,]', evs)))):
            for p in parts_det:
                v = rna_level(gene, p)
                e1.append(dict(participant=p, peptide=r.peptide, pgdb_id=r.pgdb_id, layer='isoform_event', event=e, gene=gene,
                               rna_evidence='gene_expressed' if v is not None and v >= MIN_LOG2CPM else
                                            ('gene_not_expressed' if v is not None else 'gene_not_in_rna_matrix'),
                               rna_gene_log2cpm=v, novel=r.novel))
    # rMATS-only entries lack batch provenance and a SUPPA event id; they stay unlinked here (gene-level RNA is in stage 16)
e1 = pd.read_csv(_e1f, sep='\t') if REUSE else pd.DataFrame(e1, columns=E1_COLS).drop_duplicates()
e1.to_csv(f'{OUT}/links_peptide_event.tsv', sep='\t', index=False)

# ---------- genome: SVs per participant
sv = collections.defaultdict(list); carriers_n = {}
with open(SVVCF) as f:
    for l in f:
        if l.startswith('##'): continue
        t = l.rstrip('\n').split('\t')
        if l.startswith('#'):
            cols = {i: part(c) for i, c in enumerate(t[9:], 9)}; continue
        if t[6] != 'PASS': continue
        info = dict(x.split('=', 1) for x in t[7].split(';') if '=' in x)
        car = [cols[i] for i in range(9, len(t)) if t[i].split(':')[0] not in ('0/0', './.', '.', '0|0')]
        rec = dict(id=t[2], chrom=t[0], pos=int(t[1]), end=int(info.get('END', t[1])), chr2=info.get('CHR2', t[0]),
                   svtype=info.get('SVTYPE'), n_carriers=len(car))
        for p in set(car):
            if p in participants: sv[p].append(rec)
log['sv_records_in_participants'] = sum(len(v) for v in sv.values())

def near(a, b, w): return abs(a - b) <= w
e2 = []
# (isoform-event E2 is built in stage 2, link_variant_event.py)
for p in participants:
    for _, f in fmeta[fmeta.sample_id.map(part) == p].iterrows():
        b1, b2 = int(f.breakpoint1), int(f.breakpoint2)
        for r in sv.get(p, []):
            ok = (r['chrom'] == f.chrom1 and near(r['pos'], b1, FUSION_WIN) and r['chr2'] == f.chrom2 and near(r['end'], b2, FUSION_WIN)) or \
                 (r['chrom'] == f.chrom2 and near(r['pos'], b2, FUSION_WIN) and r['chr2'] == f.chrom1 and near(r['end'], b1, FUSION_WIN))
            if ok:
                e2.append(dict(participant=p, sv_id=r['id'], svtype=r['svtype'], sv_chrom=r['chrom'], sv_pos=r['pos'], sv_end=r['end'],
                               sv_cohort_carriers=r['n_carriers'], rare=r['n_carriers'] <= RARE_MAX, layer='fusion', event=f.fusion_name))
e2 = pd.DataFrame(e2, columns=['participant', 'sv_id', 'svtype', 'sv_chrom', 'sv_pos', 'sv_end', 'sv_cohort_carriers', 'rare', 'layer', 'event']).drop_duplicates()
e2.to_csv(f'{OUT}/links_variant_event.tsv', sep='\t', index=False)

# ---------- chains
chains = e2.merge(e1, on=['participant', 'layer', 'event']) if len(e1) and len(e2) else pd.DataFrame()
chains.to_csv(f'{OUT}/chains_variant_event_peptide.tsv', sep='\t', index=False)

def cnt(df, extra=None):
    if not len(df): return dict(links=0)
    d = dict(links=len(df), participants=df.participant.nunique(), events=df.event.nunique())
    d['by_layer'] = df.groupby('layer').event.nunique().to_dict()
    if 'rna_evidence' in df: d['by_rna_evidence'] = df.groupby('rna_evidence').event.nunique().to_dict()
    if 'rare' in df: d['events_with_rare_sv'] = int(df[df.rare].event.nunique())
    return d
log['novel_peptide_sources'] = novpep.drop_duplicates('peptide').source.value_counts().to_dict() if len(novpep) else {}
log['variant_only_peptides_entering_E1'] = int(varpep.peptide.nunique()) if len(varpep) else 0
if len(e1) and 'novel' in e1: log['E1_unique_peptides_linked'] = {'novel': int(e1[e1.novel.astype(bool)].peptide.nunique()), 'known_isoform': int(e1[~e1.novel.astype(bool)].peptide.nunique())}
log['E1_peptide_event'] = cnt(e1); log['E2_variant_event'] = cnt(e2); log['chains'] = cnt(chains)
log['params'] = dict(MIN_LOG2CPM=MIN_LOG2CPM, SPLICE_WIN=SPLICE_WIN, FUSION_WIN=FUSION_WIN, RARE_MAX=RARE_MAX, sv_vcf=os.path.basename(SVVCF),
                     rna_source='AnswerALS release 7 raw counts (log2 CPM)', batches=BATCHES, dia=[dia_file(b, 'pr') for b in BATCHES],
                     excluded_dia_runs=sorted(f'{b}/{f}' for b, f in excluded_runs() if b in BATCHES))
json.dump(log, open(f'{OUT}/summary.json', 'w'), indent=2, default=str)
print(json.dumps(log, indent=2, default=str))
