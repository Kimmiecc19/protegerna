#!/usr/bin/env python3
"""
02d_summarise_fusion_peptides.py - peptides mapped to fusion-associated sequences in each search (Table 5.5).

Objective Three, Chapter 5 ("Quantmsdiann: peptide evidence for event-derived proteins", Table 5.5).

For each proteogenomic search batch the script counts:
  DIA files                      rows of the DIA-NN stats table (small/v5_b{N}.stats.tsv)
  fusion peptides                distinct peptides whose Protein.Ids include at least one fusion-associated
                                 entry (an entry with a FusionInspector source in v5_id_source.tsv)
  ... also reference-associated  of these, peptides that also map to an entry with a reference or cRAP
                                 source; they give no fusion-specific evidence
  fusion-junction peptides       observed peptides that cross the defining junction of a fusion entry
                                 (crosses_defining_junction == True in proteogenomic_peptides.tsv)
  unique junction peptides       junction peptides that are unique in the complete target database with
                                 leucine and isoleucine treated as equivalent; for each, the number of files
                                 in which it was identified (split by CASE/CTRL file prefix), and the median
                                 spectrum similarity and median PEP over its identifications
It also reports the share of report rows with a fusion-associated identifier that also contain a
reference-associated identifier (Table 5.5 note).

Identifications are the rows passing Q.Value, Global.Q.Value, PG.Q.Value and Global.PG.Q.Value <= 0.01,
as written by 01a_extract_passing_rows.sh: File.Name, Protein.Ids, Stripped.Sequence, Precursor.Id,
Spectrum.Similarity, PEP (headerless).

Inputs (all in the six_batch_assessment folder unless overridden):
  v5_b{N}.pass.tsv.gz        01a_extract_passing_rows.sh
  small/v5_b{N}.stats.tsv    01c_collect_diann_summary_tables.sh
  v5_id_source.tsv           01b_make_sequence_source_table.py
  junction_peptides.tsv.gz   written by this script from proteogenomic_peptides.tsv on the first run
                             (sequence_id, peptide, unique_complete_target_il_equivalent; junction rows only)

Outputs:
  <out_prefix>.tsv                   one row per batch (Table 5.5)
  <out_prefix>.junction_peptides.tsv one row per batch and observed fusion-junction peptide

Usage:
  python 02d_summarise_fusion_peptides.py \
  --six-dir . \
  --batches 1 2 3 4 5 6 \
  --out-prefix 02d_summarise_fusion_peptides/table_5_5_fusion_peptides

Needs: Python 3, pandas, numpy.
"""
import argparse
import gzip
import os
import re
import sys

import numpy as np
import pandas as pd

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


PASS_COLS = ["File.Name", "Protein.Ids", "Stripped.Sequence", "Precursor.Id", "Spectrum.Similarity", "PEP"]
ID_RX = re.compile(r"PGDB_[UC]\d+")
GROUP_RX = re.compile(r"(CASE|CTRL)-NEU")


def read_sources(path):
    src = pd.read_csv(path, sep="\t", header=None, names=["id", "source", "gene"], dtype=str,
                      keep_default_na=False)
    parts = src.source.str.split(";")
    fusion = set(src.id[parts.map(lambda s: "fusioninspector" in s)])
    reference = set(src.id[parts.map(lambda s: bool({"reference", "crap"} & set(s)))])
    gene = dict(zip(src.id, src.gene))
    return fusion, reference, gene


def make_junction_table(pgdb_peptides, out_path):
    """Junction-crossing peptides of the database with their target-wide uniqueness (I/L equivalent)."""
    cols = ["sequence_id", "peptide_sequence", "unique_complete_target_il_equivalent", "crosses_defining_junction"]
    parts = []
    for chunk in pd.read_csv(pgdb_peptides, sep="\t", usecols=cols, dtype=str, chunksize=1_000_000):
        parts.append(chunk.loc[chunk.crosses_defining_junction == "True", cols[:3]])
    table = pd.concat(parts, ignore_index=True)
    with gzip.open(out_path, "wt") as handle:
        table.to_csv(handle, sep="\t", header=False, index=False)
    print(f"wrote {out_path}: {len(table):,} junction peptide rows in {table.sequence_id.nunique():,} entries")


def read_junctions(path):
    jt = pd.read_csv(path, sep="\t", header=None, names=["id", "peptide", "unique_il"], dtype=str)
    unique = set(jt.peptide[jt.unique_il == "True"])
    # a peptide counts as unique only if every junction row for it says so
    unique -= set(jt.peptide[jt.unique_il != "True"])
    ids = jt.groupby("peptide")["id"].agg(lambda x: ";".join(sorted(set(x))))
    return set(jt.peptide), unique, ids


def summarise_batch(batch, six, fusion_ids, ref_ids, gene, junctions, unique_junctions, junction_ids):
    pass_path = six_path(six, f"v5_b{batch}.pass.tsv.gz")
    stats_path = six_path(six, "small", f"v5_b{batch}.stats.tsv")
    stats = pd.read_csv(stats_path, sep="\t", usecols=["File.Name"])

    fusion_rows = []
    rows_total = rows_fusion = rows_fusion_ref = 0
    for chunk in pd.read_csv(pass_path, sep="\t", header=None, names=PASS_COLS, chunksize=500_000,
                             dtype={"File.Name": str, "Protein.Ids": str, "Stripped.Sequence": str}):
        rows_total += len(chunk)
        ids = chunk["Protein.Ids"].map(lambda s: set(ID_RX.findall(s)))
        has_fusion = ids.map(lambda s: bool(s & fusion_ids))
        has_ref = ids.map(lambda s: bool(s & ref_ids))
        rows_fusion += int(has_fusion.sum())
        rows_fusion_ref += int((has_fusion & has_ref).sum())
        sub = chunk.loc[has_fusion].assign(has_ref=has_ref[has_fusion].values)
        fusion_rows.append(sub)
    fr = pd.concat(fusion_rows, ignore_index=True)

    by_peptide = fr.groupby("Stripped.Sequence")["has_ref"].any()
    observed_junctions = sorted(set(by_peptide.index) & junctions)

    detail = []
    for pep in observed_junctions:
        rows = fr[fr["Stripped.Sequence"] == pep]
        files = rows["File.Name"].drop_duplicates()
        group = files.map(lambda f: (GROUP_RX.search(f) or [None, "other"])[1])
        detail.append({
            "batch": batch, "peptide": pep, "fusion_entries": junction_ids.get(pep, ""),
            "fusions": ";".join(sorted({gene.get(i, "") for i in junction_ids.get(pep, "").split(";") if i})),
            "unique_in_target_il": pep in unique_junctions,
            "also_maps_to_reference": bool(by_peptide[pep]),
            "files": len(files), "case_files": int((group == "CASE").sum()), "ctrl_files": int((group == "CTRL").sum()),
            "identifications": len(rows),
            "median_spectrum_similarity": float(np.median(rows["Spectrum.Similarity"].astype(float))),
            "median_pep": float(np.median(rows["PEP"].astype(float))),
        })
    detail = pd.DataFrame(detail)

    uniq = detail[detail.unique_in_target_il] if len(detail) else detail
    n_fusion = int(len(by_peptide))
    n_ref = int(by_peptide.sum())
    row = {
        "batch": batch,
        "dia_files": int(stats["File.Name"].nunique()),
        "peptides_mapped_to_fusion_sequences": n_fusion,
        "also_mapped_to_reference_sequence": n_ref,
        "also_mapped_to_reference_pct": round(100 * n_ref / n_fusion, 2) if n_fusion else np.nan,
        "fusion_junction_peptides_observed": len(observed_junctions),
        "unique_junction_peptides": ";".join(uniq.peptide) if len(uniq) else "",
        "unique_junction_files": ";".join(f"{r.files} ({r.case_files}/{r.ctrl_files})" for r in uniq.itertuples()),
        "unique_junction_median_spectrum_similarity": ";".join(f"{v:.3f}" for v in uniq.median_spectrum_similarity),
        "unique_junction_median_pep": ";".join(f"{v:.4f}" for v in uniq.median_pep),
        "report_rows_with_fusion_id": rows_fusion,
        "of_which_also_reference_id_pct": round(100 * rows_fusion_ref / rows_fusion, 2) if rows_fusion else np.nan,
        "passing_report_rows": rows_total,
    }
    return row, detail


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--six-dir", required=True, help="six_batch_assessment folder")
    ap.add_argument("--pgdb-peptides", help="proteogenomic_peptides.tsv of the search database; needed only if "
                                            "junction_peptides.tsv.gz does not exist yet")
    ap.add_argument("--id-source", help="default: <six-dir>/v5_id_source.tsv")
    ap.add_argument("--junctions", help="default: <six-dir>/junction_peptides.tsv.gz")
    ap.add_argument("--batches", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--out-prefix", required=True)
    a = ap.parse_args(argv)

    id_source = a.id_source or six_path(a.six_dir, "v5_id_source.tsv")
    junction_path = a.junctions or six_path(a.six_dir, "junction_peptides.tsv.gz")
    if not os.path.exists(junction_path):
        if not a.pgdb_peptides:
            sys.exit(f"{junction_path} not found: give --pgdb-peptides to build it")
        make_junction_table(a.pgdb_peptides, junction_path)

    fusion_ids, ref_ids, gene = read_sources(id_source)
    junctions, unique_junctions, junction_ids = read_junctions(junction_path)
    print(f"{len(fusion_ids):,} fusion-associated entries; {len(junctions):,} junction peptides "
          f"({len(unique_junctions):,} unique in the target database, I/L equivalent)")

    rows, details = [], []
    for b in a.batches:
        row, detail = summarise_batch(b, a.six_dir, fusion_ids, ref_ids, gene, junctions, unique_junctions,
                                      junction_ids)
        rows.append(row); details.append(detail)
        print(f"batch {b}: {row['dia_files']} files, {row['peptides_mapped_to_fusion_sequences']:,} fusion peptides, "
              f"{row['also_mapped_to_reference_sequence']:,} ({row['also_mapped_to_reference_pct']}%) also reference, "
              f"{row['fusion_junction_peptides_observed']} junction peptides; unique: {row['unique_junction_peptides']} "
              f"{row['unique_junction_files']}")

    os.makedirs(os.path.dirname(os.path.abspath(a.out_prefix)), exist_ok=True)
    pd.DataFrame(rows).to_csv(a.out_prefix + ".tsv", sep="\t", index=False)
    pd.concat(details, ignore_index=True).to_csv(a.out_prefix + ".junction_peptides.tsv", sep="\t", index=False)
    print(f"written: {a.out_prefix}.tsv and {a.out_prefix}.junction_peptides.tsv")


if __name__ == "__main__":
    main()
