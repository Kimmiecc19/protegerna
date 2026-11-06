#!/usr/bin/env python3
"""
01b_make_sequence_source_table.py - map every search-database entry to the sources that produced it.

Objective Three, Chapter 5 ("Comparison with a reference-only search"; Tables 5.5, 5.7, 5.9, 5.10).

The search database (v5) collapses identical sequences, so one entry (PGDB_U...) can come from several
producers: the UniProt reference proteome, cRAP, rMATS, SUPPA and/or FusionInspector. This script writes one
row per entry with all of its producers, which the search-assessment scripts use to decide whether an
identified peptide maps to a reference sequence or only to splice- or fusion-derived sequences.

Input (from the database build, 03_search_database):
  proteogenomic_mapping.tsv    one row per input record: sequence_id, source, ... (157,726 rows for v5)
  proteogenomic_metadata.tsv   one row per entry: sequence_id, gene, ...         (80,657 rows for v5)

Output: a headerless, tab-separated file with three columns, in database order
  sequence_id   sources                                   gene
  PGDB_U0001630 reference                                 ADARB1
  PGDB_U0002649 rmats;suppa                               ...
  PGDB_U0034249 fusioninspector;fusioninspector           JAK3-INSL3
`sources` lists the source of every contributing input record, in the order of the mapping table, so a
fusion entry built from three participants' FusionInspector calls reads fusioninspector;fusioninspector;
fusioninspector. Downstream scripts split this field on ';'.

`gene` is informational only (no downstream count uses it). By default it is the gene_symbols value of the
LAST mapping record of the entry, which reproduces the v5_id_source.tsv used in the dissertation exactly;
entries whose last record is a cRAP sequence therefore read NA. Use --gene-from metadata to take the gene
symbol(s) from proteogenomic_metadata.tsv instead.

Usage:
  python 01b_make_sequence_source_table.py --pgdb-dir results/pgdb_publication_rerun_v5 \
      --out results/06_search_assessment/v5_id_source.tsv

Needs: Python 3, pandas.
"""
import argparse
import os
import sys

import pandas as pd

KNOWN_SOURCES = {"reference", "crap", "rmats", "suppa", "fusioninspector"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pgdb-dir", required=True,
                    help="database build folder containing proteogenomic_mapping.tsv and proteogenomic_metadata.tsv")
    ap.add_argument("--mapping", help="override path to proteogenomic_mapping.tsv")
    ap.add_argument("--metadata", help="override path to proteogenomic_metadata.tsv")
    ap.add_argument("--gene-from", choices=["last-record", "metadata"], default="last-record",
                    help="where the informational gene column comes from (default reproduces the dissertation file)")
    ap.add_argument("--out", required=True, help="output TSV (headerless: sequence_id, sources, gene)")
    a = ap.parse_args(argv)

    mapping_path = a.mapping or os.path.join(a.pgdb_dir, "proteogenomic_mapping.tsv")
    metadata_path = a.metadata or os.path.join(a.pgdb_dir, "proteogenomic_metadata.tsv")

    mapping = pd.read_csv(mapping_path, sep="\t", dtype=str, usecols=["sequence_id", "source", "gene_symbols"],
                          keep_default_na=False)
    metadata = pd.read_csv(metadata_path, sep="\t", dtype=str, usecols=["sequence_id", "gene"],
                           keep_default_na=False)

    unknown = sorted(set(mapping.source) - KNOWN_SOURCES)
    if unknown:
        sys.exit(f"Unexpected source values in {mapping_path}: {unknown}")

    # Join the source of every contributing record, keeping the order of the mapping table.
    sources = mapping.groupby("sequence_id", sort=False)["source"].agg(";".join)

    missing = sorted(set(metadata.sequence_id) - set(sources.index))
    extra = sorted(set(sources.index) - set(metadata.sequence_id))
    if missing or extra:
        sys.exit(f"Mapping and metadata disagree: {len(missing)} entries without a mapping row, "
                 f"{len(extra)} mapping entries not in the metadata (e.g. {(missing or extra)[:3]})")

    if a.gene_from == "last-record":
        last_gene = mapping.groupby("sequence_id", sort=False)["gene_symbols"].last()
        metadata["gene"] = metadata.sequence_id.map(last_gene)
    out = metadata.assign(sources=metadata.sequence_id.map(sources))[["sequence_id", "sources", "gene"]]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out.to_csv(a.out, sep="\t", header=False, index=False)

    # Short summary for the log.
    first = out.sources.str.split(";")
    summary = {
        "entries": len(out),
        "with a reference or cRAP source": int(first.map(lambda s: bool({"reference", "crap"} & set(s))).sum()),
        "splice/fusion only": int(first.map(lambda s: set(s) <= {"rmats", "suppa", "fusioninspector"}).sum()),
        "with a FusionInspector source": int(first.map(lambda s: "fusioninspector" in s).sum()),
    }
    for key, value in summary.items():
        print(f"{key}: {value:,}")
    print(f"written: {a.out}")


if __name__ == "__main__":
    main()
