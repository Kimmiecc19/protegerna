"""Small helpers shared by the Objective 4 Python scripts.

Each function here replaces identical copies that used to live in several scripts; behaviour is unchanged.
"""
import gzip, re
import numpy as np, pandas as pd

PART_RX = re.compile(r'(CASE|CTRL)[-_](NEU[A-Z0-9]+)')


def part(s):
    """Participant ID (CASE-NEUxxxx / CTRL-NEUxxxx) from a sample, run or column name; None if absent."""
    m = PART_RX.search(str(s))
    return f'{m.group(1)}-{m.group(2)}' if m else None


def bh(p):
    """Benjamini-Hochberg adjusted p-values, in input order; NaN p-values stay NaN."""
    p = np.asarray(p, float); out = np.full(len(p), np.nan); ok = ~np.isnan(p)
    if ok.sum() == 0: return out
    q = p[ok]; o = np.argsort(q); n = len(q)
    r = q[o] * n / np.arange(1, n + 1); r = np.minimum.accumulate(r[::-1])[::-1]
    tmp = np.empty(n); tmp[o] = np.minimum(r, 1); out[ok] = tmp; return out


def read_fasta_seqs(paths):
    """Protein sequences from one or more FASTA files (.gz allowed), in file order."""
    seqs = []
    for p in paths:
        op = gzip.open if p.endswith('.gz') else open
        buf = []
        with op(p, 'rt') as fh:
            for line in fh:
                if line.startswith('>'):
                    if buf: seqs.append(''.join(buf)); buf = []
                else:
                    buf.append(line.strip())
        if buf: seqs.append(''.join(buf))
    return seqs


def pgdb_gene_mapper(id2gene):
    """Return pg_gene(protein_group): the single gene of the PGDB_U ids in a protein group, or None."""
    def pg_gene(pg):
        g = {id2gene.get(i) for i in re.findall(r'PGDB_U\d+', str(pg))} - {None, 'NA', ''}
        return g.pop() if len(g) == 1 else None
    return pg_gene


def load_v5_protein_by_gene(matrix, samples, pgdb_meta):
    """Gene x participant log2 protein matrix from the 01b consolidation outputs (v5 search).
    Participant runs only, median-centred per run, protein groups mapped to a unique gene through the
    PGDB metadata, groups of one gene averaged, runs of one participant averaged."""
    pm = pd.read_csv(matrix, sep='\t', index_col=0, na_values=['NA', ''])
    ps = pd.read_csv(samples, sep='\t')
    ps = ps[(ps.sample_type == 'participant') & ps.cohort_run.isin(pm.columns)]
    pm = pm[ps.cohort_run]
    pm = pm - pm.median()                                       # per-run median centring
    meta = pd.read_csv(pgdb_meta, sep='\t', dtype=str)
    pg_gene = pgdb_gene_mapper(dict(zip(meta.sequence_id, meta.gene)))
    pm.index = [pg_gene(i) for i in pm.index]
    pm = pm[pm.index.notna()].groupby(level=0).mean()
    pm.columns = [part(p) for p in ps.participant_id]
    return pm.T.groupby(level=0).mean().T
