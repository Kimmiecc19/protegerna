#!/usr/bin/env python3
"""
table_5_10_peptide_lengths.py - search-space inflation and Table 5.10 (Chapter 5).

Reproduces the Results text under "Search-space inflation" and Table 5.10:
  * entries in the reference-only and V5 search databases;
  * distinct in-silico tryptic peptides of each database, the overlap between them, and their
    length distribution (median, mean, % of 30 residues or longer);
  * distinct peptides identified in the six reference-only and six V5 searches (rows passing
    Q.Value, Global.Q.Value, PG.Q.Value and Global.PG.Q.Value <= 0.01, i.e. the *.pass.tsv.gz
    tables written by six_batch_assessment/extract.sh), their overlap and length distribution,
    the same for the reference-only searches without Batch 1 (which lacked fixed
    carbamidomethylation of cysteine), and the % of theoretical peptides that were identified.

Digestion uses the same cleavage rule as the workflow (proteogenomic.proteogenomic_digestion) with the
search settings: cleavage after K or R except before P, up to 3 missed cleavages, 7-40 residues.
Unlike the workflow digest, peptides containing X are KEPT, which reproduces the counts reported in the
chapter (3,175,822 and 3,414,274); the number of such peptides is reported on its own row (22 and 129),
so subtracting it gives the workflow-digest counts.
Sequences are compared exactly (no I/L merging). Precursor m/z and charge limits and N-terminal
methionine excision are not modelled.

Usage:
  python table_5_10_peptide_lengths.py --ref-fasta human_reference_deduplicated.fasta \
      --v5-fasta proteogenomic_database.fasta --six-dir six_batch_assessment --out table_5_10.tsv
Needs: Python 3, pandas, numpy.
"""
import argparse, os, re
import numpy as np, pandas as pd

# The "six-batch" folder may hold the 01a/01b/01c outputs side by side, or be this step's folder,
# where they sit in their own result subfolders. Look in the folder first, then in those subfolders.
SIX_SUBDIRS = ("01a_extract_passing_rows", "01b_make_sequence_source_table",
               "01c_collect_diann_summary_tables", "02d_summarise_fusion_peptides")


def six_path(root, *parts):
    flat = os.path.join(root, *parts)
    if os.path.exists(flat):
        return flat
    for sub in SIX_SUBDIRS:
        candidate = os.path.join(root, sub, *parts)
        if os.path.exists(candidate):
            return candidate
    return flat


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--ref-fasta", required=True)
ap.add_argument("--v5-fasta", required=True)
ap.add_argument("--six-dir", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
MIN_LEN, MAX_LEN, MISSED = 7, 40, 3


def digest_sequences(sequence):
    """Trypsin (K/R not before P), <= MISSED missed cleavages, MIN_LEN-MAX_LEN residues; X kept."""
    out = set()
    for seg in (p for p in re.sub(r"[^A-Za-z*]", "", sequence.upper()).split("*") if p):
        cuts = [0] + [i + 1 for i, aa in enumerate(seg) if aa in "KR" and (i + 1 == len(seg) or seg[i + 1] != "P")]
        if cuts[-1] != len(seg):
            cuts.append(len(seg))
        for s in range(len(cuts) - 1):
            for e in range(s + 1, min(len(cuts) - 1, s + MISSED + 1) + 1):
                p = seg[cuts[s]:cuts[e]]
                if MIN_LEN <= len(p) <= MAX_LEN:
                    out.add(p)
    return out


def read_fasta(path):
    seq = []
    with open(path) as f:
        for line in f:
            if line.startswith(">"):
                if seq: yield "".join(seq)
                seq = []
            else:
                seq.append(line.strip())
    if seq: yield "".join(seq)


def digest_db(path):
    n, peps = 0, set()
    for s in read_fasta(path):
        n += 1
        peps |= digest_sequences(s)
    return n, peps


def observed(tag, batches):
    peps = set()
    for b in batches:
        p = pd.read_csv(six_path(a.six_dir, f"{tag}_b{b}.pass.tsv.gz"), sep="\t", header=None,
                        usecols=[2], names=["pep"], dtype=str)
        peps |= set(p.pep.unique())
    return peps


def lengths(peps):
    L = np.fromiter((len(p) for p in peps), dtype=np.int32, count=len(peps))
    return dict(n=len(peps), median=float(np.median(L)), mean=round(float(L.mean()), 2),
                min=int(L.min()), max=int(L.max()), n_ge30=int((L >= 30).sum()),
                pct_ge30=round(100 * float((L >= 30).mean()), 2),
                n_cys=sum("C" in p for p in peps))


rows = []
def put(metric, ref, v5, note=""):
    rows.append(dict(metric=metric, reference=ref, v5=v5, note=note)); print(metric, ref, v5, note, flush=True)

n_ref, th_ref = digest_db(a.ref_fasta)
n_v5, th_v5 = digest_db(a.v5_fasta)
put("database entries", n_ref, n_v5)
put("distinct theoretical tryptic peptides", len(th_ref), len(th_v5),
    f"+{100 * (len(th_v5) - len(th_ref)) / len(th_ref):.1f}%")
put("theoretical peptides only in this database", len(th_ref - th_v5), len(th_v5 - th_ref))
put("theoretical peptides shared", len(th_ref & th_v5), len(th_ref & th_v5))
put("theoretical peptides containing X", sum("X" in p for p in th_ref), sum("X" in p for p in th_v5),
    "excluded by the workflow digest; subtract for workflow-digest counts")
lr, lv = lengths(th_ref), lengths(th_v5)
for k in ("median", "mean", "min", "max", "n_ge30", "pct_ge30"):
    put(f"theoretical length {k}", lr[k], lv[k])
del th_ref, th_v5

ob_ref = observed("ref", range(1, 7))
ob_v5 = observed("v5", range(1, 7))
ob_ref26 = observed("ref", range(2, 7))
put("distinct identified peptides (B1-6)", len(ob_ref), len(ob_v5))
put("identified peptides shared", len(ob_ref & ob_v5), len(ob_ref & ob_v5))
orf, ov5, o26 = lengths(ob_ref), lengths(ob_v5), lengths(ob_ref26)
for k in ("median", "mean", "min", "max", "n_ge30", "pct_ge30", "n_cys"):
    put(f"identified length {k}", orf[k], ov5[k])
for k in ("n", "median", "mean", "n_cys"):
    put(f"reference-only searches B2-6: {k}", o26[k], "", "Batch 1 reference search lacked fixed Cys carbamidomethylation")
put("% of theoretical peptides identified", round(100 * orf["n"] / lr["n"], 2), round(100 * ov5["n"] / lv["n"], 2))

pd.DataFrame(rows).to_csv(a.out, sep="\t", index=False)
print("wrote", a.out)
