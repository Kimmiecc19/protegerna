"""Shared helper: participant x gene RNA expression from the AnswerALS consortium count matrix.

Replaces the strand-affected rnasplice Salmon TPMs. Returns log2(CPM + 1) with gene symbols
(from the GENCODE GTF) as rows and participant IDs (CASE-NEUxxxx / CTRL-NEUxxxx) as columns.
Several samples of one participant are averaged (only the control line has repeats).
"""
import os, re
import numpy as np, pandas as pd
from common import PART_RX as _rx, part

ANSWERALS_COUNTS = '5_ALS_case_study/2_transcriptomics/4_matrix_transcriptomics_answerals/AnswerALS-1276-T-v1-release7_raw-counts.csv'


def gene_id_to_name(gtf):
    """Unversioned Ensembl gene ID -> gene name. Accepts a GENCODE GTF (all gene types) or a
    two-column tab-separated map ENSG<TAB>symbol such as ensg_symbol.tsv (protein-coding only)."""
    out = {}
    with open(gtf) as f:
        first = next((l for l in f if not l.startswith('#')), '')
    if len(first.rstrip('\n').split('\t')) == 2:
        with open(gtf) as f:
            for l in f:
                t = l.rstrip('\n').split('\t')
                if len(t) == 2 and t[0].startswith('ENSG'):
                    out[t[0].split('.')[0]] = t[1]
        return out
    with open(gtf) as f:
        for l in f:
            if l.startswith('#'):
                continue
            t = l.split('\t', 9)
            if len(t) < 9 or t[2] != 'gene':
                continue
            gid = re.search(r'gene_id "([^".]+)', t[8]).group(1)
            gn = re.search(r'gene_name "([^"]+)"', t[8])
            out[gid] = gn.group(1) if gn else gid
    return out


def load_rna_log2cpm(root, gtf, participants=None, counts_path=None):
    path = counts_path or os.path.join(root, ANSWERALS_COUNTS)
    raw = pd.read_csv(path, encoding='utf-8-sig', low_memory=False)
    gcol = next(c for c in raw.columns if raw[c].astype(str).head(100).str.startswith('ENSG').mean() > 0.9)
    raw = raw.set_index(gcol)
    cols = [c for c in raw.columns if _rx.search(str(c))]
    if participants is not None:
        want = set(participants)
        cols = [c for c in cols if part(c) in want]
    counts = raw[cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    cpm = counts / counts.sum(axis=0) * 1e6
    lg = np.log2(cpm + 1)
    names = gene_id_to_name(gtf)
    lg.index = [names.get(str(i).split('.')[0], str(i)) for i in lg.index]
    lg = lg.groupby(level=0).mean()                  # duplicated symbols (rare)
    lg.columns = [part(c) for c in lg.columns]
    return lg.T.groupby(level=0).mean().T             # average repeated samples per participant
