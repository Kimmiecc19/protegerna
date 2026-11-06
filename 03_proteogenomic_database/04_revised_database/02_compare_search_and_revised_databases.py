#!/usr/bin/env python3
"""
compare_v5_v7_databases.py - v5 vs v7 database overlap and fusion reconstruction consistency (Chapter 5).

Reproduces the Results text under "Effect of additional filtering on database composition":
  * distinct sequences in v5 and v7, how many are shared, new in v7 or dropped from v5;
  * for each source (reference, crap, rmats, suppa, fusioninspector), the distinct v7 sequences
    from that source and how many of them are present anywhere in v5 and in the same v5 source;
  * fusion reconstruction consistency: fusion events (same chrom1, breakpoint1, chrom2, breakpoint2,
    donor transcript and acceptor transcript) observed in more than one sample, and how many of them
    yield more than one distinct reconstructed CDS (cds_sequence_hash) across samples.
Sequences are compared exactly after upper-casing. Sources are read from the source= field of the
final PGDB FASTA headers (a sequence can carry several sources).

Usage:
  python compare_v5_v7_databases.py --v5-dir results_pgdb_publication_rerun_v5 \
      --v7-dir results_protegerna_v7_filtered --fusion-table fusion.biological.tsv --out v5_v7_comparison.tsv
Needs: Python 3, pandas.
"""
import argparse, os, re
import pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--v5-dir", required=True)
ap.add_argument("--v7-dir", required=True)
ap.add_argument("--fusion-table", default="fusion.biological.tsv",
                help="fusion table in each release folder used for the consistency check ('none' to skip)")
ap.add_argument("--out", required=True)
a = ap.parse_args()
SRC = re.compile(r"\|source=([^|]+)")


def fasta_sources(path):
    out, hdr, seq = {}, None, []
    def flush():
        if hdr is not None:
            m = SRC.search(hdr)
            srcs = set(re.split(r"[;,]", m.group(1))) if m else {"NA"}
            out.setdefault("".join(seq).upper(), set()).update(srcs)
    with open(path) as f:
        for line in f:
            if line.startswith(">"):
                flush(); hdr, seq = line, []
            else:
                seq.append(line.strip())
    flush()
    return out


rows = []
def put(metric, v5, v7, note=""):
    rows.append(dict(metric=metric, v5=v5, v7=v7, note=note)); print(metric, v5, v7, note, flush=True)

s5 = fasta_sources(os.path.join(a.v5_dir, "proteogenomic_database.fasta"))
s7 = fasta_sources(os.path.join(a.v7_dir, "proteogenomic_database.fasta"))
k5, k7 = set(s5), set(s7)
put("distinct sequences", len(k5), len(k7), f"v7 = {100 * len(k7) / len(k5):.1f}% of v5")
put("sequences in both releases", len(k5 & k7), len(k5 & k7))
put("sequences only in this release", len(k5 - k7), len(k7 - k5))
for src in ("reference", "crap", "rmats", "suppa", "fusioninspector"):
    a5 = {q for q, s in s5.items() if src in s}
    a7 = {q for q, s in s7.items() if src in s}
    put(f"{src}: distinct sequences", len(a5), len(a7))
    put(f"{src}: v7 sequences present anywhere in v5", "", len(a7 & k5))
    put(f"{src}: v7 sequences present as same source in v5", "", len(a7 & a5))

KEY = ["chrom1", "breakpoint1", "chrom2", "breakpoint2", "donor_tid", "acceptor_tid"]
def fusion_consistency(path):
    samples, cds = {}, {}
    for ch in pd.read_csv(path, sep="\t", usecols=KEY + ["sample_id", "cds_sequence_hash"], dtype=str,
                          chunksize=200_000, keep_default_na=False):
        ch = ch[ch.cds_sequence_hash.str.len() > 0]
        for row in ch.itertuples(index=False):
            k = tuple(getattr(row, c) for c in KEY)
            samples.setdefault(k, set()).add(row.sample_id)
            cds.setdefault(k, set()).add(row.cds_sequence_hash)
    multi = [k for k, s in samples.items() if len(s) > 1]
    return len(samples), len(multi), sum(len(cds[k]) > 1 for k in multi)

if a.fusion_table.lower() == "none":
    pd.DataFrame(rows).to_csv(a.out, sep="\t", index=False); print("wrote", a.out); raise SystemExit
r5 = fusion_consistency(os.path.join(a.v5_dir, a.fusion_table))
r7 = fusion_consistency(os.path.join(a.v7_dir, a.fusion_table))
put("fusion events with a reconstructed CDS", r5[0], r7[0], a.fusion_table)
put("fusion events observed in more than one sample", r5[1], r7[1], a.fusion_table)
put("multi-sample events with more than one distinct CDS", r5[2], r7[2], a.fusion_table)

pd.DataFrame(rows).to_csv(a.out, sep="\t", index=False)
print("wrote", a.out)
