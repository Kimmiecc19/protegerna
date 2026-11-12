#!/usr/bin/env python3
"""
compare_reference_vs_v5.py - reference-only vs V5 proteogenomic quantmsdiann searches (Chapter 5).

Recomputes every database-comparison metric reported in Chapter 5 (text under "Comparison with a
reference-only search" and Tables 5.10 and 5.12) for Batches 1-6, from files already in
six_batch_assessment/:

  {ref,v5}_b{1..6}.pass.tsv.gz      main-report rows passing Q.Value, Global.Q.Value, PG.Q.Value and
                                    Global.PG.Q.Value <= 0.01 (written by extract.sh from diann_report.tsv)
                                    columns: File.Name, Protein.Ids, Stripped.Sequence, Precursor.Id, ...
  small/{ref,v5}_b{N}.stats.tsv              diann_report.stats.tsv
  small/{ref,v5}_b{N}.pg_matrix.tsv          diann_report.pg_matrix.tsv
  small/{ref,v5}_b{N}.gg_matrix.tsv          diann_report.gg_matrix.tsv
  small/{ref,v5}_b{N}.unique_genes_matrix.tsv diann_report.unique_genes_matrix.tsv
  v5_id_source.tsv                  V5 sequence id -> producer (reference, crap, rmats, suppa, fusioninspector)

Definitions (one rule per metric, applied identically to every batch):
  per-file precursor change   100 * (V5 - ref) / ref of Precursors.Identified in the stats table, paired by
                              file name; median and interquartile range (pandas quantile, linear
                              interpolation) over files present in both searches with ref > 0.
  distinct precursors/peptides  unique Precursor.Id / Stripped.Sequence in the pass table.
  protein groups              rows of the pg_matrix.
  quantified PG per file      non-missing values per file column of the pg_matrix (median over files).
  specific proteins           Proteins.Identified in the stats table: median over all files of each search,
                              and median of the paired % change over files with ref > 0.
  unique genes per file       non-missing values per file column of unique_genes_matrix (median).
  shared gene-group labels    exact label match after removing the "GN=" prefix written by the V5 search.
  per-file correlation        Pearson r of log2 intensities over shared labels quantified in both searches.
  repeated-control CV         CTRL-NEUEU392AE8 files; gene groups with values > 0 in >= 80% of those files;
                              CV = SD / mean * 100 of raw gg_matrix intensities; median over gene groups.
  gained / lost peptides      distinct peptides in V5 only / in reference only; a gained peptide is
                              "custom-only" if none of its V5 protein ids is a reference or cRAP entry.
  cysteine-free (Batch 1)     the same per-file and distinct-peptide metrics restricted to peptides without C.

Usage:  python compare_reference_vs_v5.py [six_batch_assessment_dir] [out.tsv]
Needs:  Python 3, pandas, numpy.
"""
import sys, os, re, gzip
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


D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(D, "reference_vs_v5_metrics.tsv")
S = six_path(D, "small")
CONTROL = "CTRL-NEUEU392AE8"
PASS_COLS = ["File.Name", "Protein.Ids", "Stripped.Sequence", "Precursor.Id"]

src = pd.read_csv(six_path(D, "v5_id_source.tsv"), sep="\t", header=None, names=["id", "source", "gene"])
REF_IDS = set(src.loc[src.source.str.split(";").map(lambda s: any(x in ("reference", "crap") for x in s)), "id"])
idrx = re.compile(r"PGDB_[UC]\d+")


def fkey(name):
    """File key that ignores directory, extension and '.profile' vs '_profile' spelling."""
    b = os.path.basename(str(name))
    b = re.sub(r"\.mzML$", "", b)
    return re.sub(r"[._]profile$", "", b)


def load_pass(tag, b):
    df = pd.read_csv(six_path(D, f"{tag}_b{b}.pass.tsv.gz"), sep="\t", header=None,
                     usecols=[0, 1, 2, 3], names=PASS_COLS, dtype=str)
    return df


def qstats(x):
    x = pd.Series(x).dropna()
    return x.median(), x.quantile(0.25), x.quantile(0.75)


def stats_table(tag, b):
    s = pd.read_csv(os.path.join(S, f"{tag}_b{b}.stats.tsv"), sep="\t")
    s["key"] = s["File.Name"].map(fkey)
    return s


def matrix(tag, b, kind):
    m = pd.read_csv(os.path.join(S, f"{tag}_b{b}.{kind}.tsv"), sep="\t", low_memory=False)
    return m


def file_cols(m):
    return [c for c in m.columns if c.endswith(".mzML") or "profile" in c]


rows = []
def put(b, metric, ref, v5, note=""):
    rows.append(dict(batch=b, metric=metric, reference=ref, v5=v5, note=note))


for b in range(1, 7):
    # --- per-file precursors and specific proteins (stats tables)
    sv, sr = stats_table("v5", b), stats_table("ref", b)
    m = sv[["key", "Precursors.Identified", "Proteins.Identified"]].merge(
        sr[["key", "Precursors.Identified", "Proteins.Identified"]], on="key", suffixes=("_v5", "_ref"))
    mp = m[m["Precursors.Identified_ref"] > 0]
    ch = 100 * (mp["Precursors.Identified_v5"] - mp["Precursors.Identified_ref"]) / mp["Precursors.Identified_ref"]
    med, q1, q3 = qstats(ch)
    put(b, "per-file precursor change, median % (IQR)", "", f"{med:+.2f} ({q1:+.2f} to {q3:+.2f})", f"{len(mp)} paired files")
    ms = m[m["Proteins.Identified_ref"] > 0]
    chp = 100 * (ms["Proteins.Identified_v5"] - ms["Proteins.Identified_ref"]) / ms["Proteins.Identified_ref"]
    put(b, "specific proteins per file, median (all files)", sr["Proteins.Identified"].median(), sv["Proteins.Identified"].median())
    put(b, "specific proteins per file, median paired change %", "", f"{chp.median():+.1f}", f"{len(ms)} paired files")

    # --- distinct precursors / peptides, gained / lost
    pv, pr = load_pass("v5", b), load_pass("ref", b)
    put(b, "distinct precursors (4 x 1% q)", pr["Precursor.Id"].nunique(), pv["Precursor.Id"].nunique())
    pepv, pepr = set(pv["Stripped.Sequence"]), set(pr["Stripped.Sequence"])
    put(b, "distinct peptides (4 x 1% q)", len(pepr), len(pepv))
    pep_ids = pv.drop_duplicates(["Stripped.Sequence", "Protein.Ids"]).groupby("Stripped.Sequence")["Protein.Ids"].apply(
        lambda s: set(idrx.findall(";".join(s))))
    custom_only = {p for p, ids in pep_ids.items() if ids and not (ids & REF_IDS)}
    gained, lost = pepv - pepr, pepr - pepv
    put(b, "peptides gained in V5 / lost", "", f"{len(gained)} / {len(lost)}")
    put(b, "gained peptides mapping only to splice/fusion entries", "", len(gained & custom_only))
    put(b, "V5 peptides mapping only to splice/fusion entries", "", len(pepv & custom_only))
    if b == 1:
        cf = lambda s: {p for p in s if "C" not in p}
        put(b, "distinct cysteine-free peptides", len(cf(pepr)), len(cf(pepv)))
        g, l = cf(pepv) - cf(pepr), cf(pepr) - cf(pepv)
        put(b, "cysteine-free peptides gained / lost", "", f"{len(g)} / {len(l)}",
            f"{len(g & custom_only)} gained map only to splice/fusion entries")
        # per-file cysteine-free peptide change
        cv = pv[~pv["Stripped.Sequence"].str.contains("C")].groupby(pv["File.Name"].map(fkey))["Stripped.Sequence"].nunique()
        cr = pr[~pr["Stripped.Sequence"].str.contains("C")].groupby(pr["File.Name"].map(fkey))["Stripped.Sequence"].nunique()
        j = pd.concat([cv.rename("v5"), cr.rename("ref")], axis=1).dropna()
        j = j[j.ref > 0]
        med, q1, q3 = qstats(100 * (j.v5 - j.ref) / j.ref)
        put(b, "per-file cysteine-free peptide change, median % (IQR)", "", f"{med:+.2f} ({q1:+.2f} to {q3:+.2f})", f"{len(j)} files")
    del pv, pr

    # --- protein groups and unique genes
    for kind, label in (("pg_matrix", "protein groups"), ("unique_genes_matrix", "unique genes")):
        mr, mv = matrix("ref", b, kind), matrix("v5", b, kind)
        if kind == "pg_matrix":
            put(b, "protein groups (pg_matrix rows)", len(mr), len(mv))
        put(b, f"quantified {label} per file, median", mr[file_cols(mr)].notna().sum().median(), mv[file_cols(mv)].notna().sum().median())

    # --- gene-group labels, correlation, repeated-control CV
    gr, gv = matrix("ref", b, "gg_matrix"), matrix("v5", b, "gg_matrix")
    gr["Genes"] = gr["Genes"].astype(str)
    gv["Genes"] = gv["Genes"].astype(str).str.replace(r"(^|;)GN=", r"\1", regex=True)
    gr, gv = gr.set_index("Genes"), gv.set_index("Genes")
    shared = gr.index.intersection(gv.index)
    put(b, "shared gene-group labels", len(gr), len(gv), f"{len(shared)} shared")
    fr = {fkey(c): c for c in file_cols(gr.reset_index())}
    fv = {fkey(c): c for c in file_cols(gv.reset_index())}
    rs = []
    for k in sorted(set(fr) & set(fv)):
        x, y = gr.loc[shared, fr[k]], gv.loc[shared, fv[k]]
        ok = x.notna() & y.notna() & (x > 0) & (y > 0)
        if ok.sum() > 10:
            rs.append(np.corrcoef(np.log2(x[ok]), np.log2(y[ok]))[0, 1])
    put(b, "median per-file Pearson r (log2, shared labels)", "", f"{np.median(rs):.3f}", f"{len(rs)} files")
    for tag, g in (("reference", gr), ("v5", gv)):
        cols = [c for c in file_cols(g.reset_index()) if CONTROL in c]
        x = g[cols].astype(float)
        keep = (x > 0).sum(axis=1) >= np.ceil(0.8 * len(cols))
        cv = (x[keep].std(axis=1, ddof=1) / x[keep].mean(axis=1) * 100)
        put(b, f"repeated-control CV % ({tag})", "", f"{cv.median():.2f}", f"{len(cols)} control files; {int(keep.sum())} gene groups")
    print(f"batch {b} done", file=sys.stderr)

res = pd.DataFrame(rows)
res.to_csv(OUT, sep="\t", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 500)
print(res.to_string(index=False))
