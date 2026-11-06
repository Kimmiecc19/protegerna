#!/usr/bin/env bash
# 01c_collect_diann_summary_tables.sh
#
# Objective Three, Chapter 5 ("Quantmsdiann identification"; "Comparison with a reference-only search";
# Tables 5.5, 5.7, 5.9).
#
# Copies the small DIA-NN summary tables of every quantmsdiann search into one folder, with the names the
# search-assessment scripts expect:
#
#   <out>/small/{ref,v5}_b{N}.stats.tsv                 <- quant_tables/diann_report.stats.tsv
#   <out>/small/{ref,v5}_b{N}.pg_matrix.tsv             <- quant_tables/diann_report.pg_matrix.tsv
#   <out>/small/{ref,v5}_b{N}.gg_matrix.tsv             <- quant_tables/diann_report.gg_matrix.tsv
#   <out>/small/{ref,v5}_b{N}.unique_genes_matrix.tsv   <- quant_tables/diann_report.unique_genes_matrix.tsv
#   <out>/small/sdrf_b{N}.tsv                           <- the SDRF the proteogenomic search used
#
# "ref" is the reference-only search and "v5" the proteogenomic search of the same batch (05_proteomic_search).
# A checksum manifest (small/manifest.tsv) records where every file came from.
#
# Usage:
#   bash 01c_collect_diann_summary_tables.sh --ref-root DIR --pgdb-root DIR --out DIR [--batches "1 2 3 4 5 6"]
#
#   --ref-root DIR    folder with one reference-only quantmsdiann output folder per batch
#   --pgdb-root DIR   folder with one proteogenomic quantmsdiann output folder per batch
#   --ref-pattern P   batch folder name under --ref-root; {b} is replaced by the batch number
#                     (default: batch{b}; batch 1 of the dissertation is batch1_fixed, see below)
#   --pgdb-pattern P  batch folder name under --pgdb-root (default: pgdb_v5_batch{b})
#   --out DIR         the six_batch_assessment folder (the tables go into DIR/small)
#   --batches LIST    batches to collect (default: 1 2 3 4 5 6)
#
# The dissertation's reference-only Batch 1 is the repeat search of 27 October 2026, stored as
# batch1_fixed; give it with, e.g., --ref-override 1=batch1_fixed.
#
# Example (server layout used in the dissertation):
#   bash 01c_collect_diann_summary_tables.sh \
#     --ref-root /home/kcoetzer/nf/nf_results/quantms/reference --ref-override 1=batch1_fixed \
#     --pgdb-root /home/kcoetzer/nf/nf_results/quantms/pgdb \
#     --out results/06_search_assessment

set -euo pipefail

REF_ROOT=""; PGDB_ROOT=""; OUT=""
REF_PATTERN="batch{b}"; PGDB_PATTERN="pgdb_v5_batch{b}"
BATCHES="1 2 3 4 5 6"
declare -A REF_OVERRIDE=()

usage() { sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ref-root)     REF_ROOT="${2:?}"; shift 2 ;;
        --pgdb-root)    PGDB_ROOT="${2:?}"; shift 2 ;;
        --ref-pattern)  REF_PATTERN="${2:?}"; shift 2 ;;
        --pgdb-pattern) PGDB_PATTERN="${2:?}"; shift 2 ;;
        --ref-override) REF_OVERRIDE["${2%%=*}"]="${2#*=}"; shift 2 ;;
        --out)          OUT="${2:?}"; shift 2 ;;
        --batches)      BATCHES="${2:?}"; shift 2 ;;
        -h|--help)      usage; exit 0 ;;
        *) echo "ERROR: unknown option $1" >&2; usage >&2; exit 2 ;;
    esac
done
[[ -n "$REF_ROOT" && -n "$PGDB_ROOT" && -n "$OUT" ]] || { usage >&2; exit 2; }

SMALL="$OUT/small"
mkdir -p "$SMALL"
MANIFEST="$SMALL/manifest.tsv"
printf 'file\tsource\tsha256\n' > "$MANIFEST"

copy() {  # copy SRC DEST, failing loudly if SRC is missing
    local src="$1" dest="$2"
    [[ -s "$src" ]] || { echo "ERROR: missing or empty: $src" >&2; exit 1; }
    cp -- "$src" "$dest"
    printf '%s\t%s\t%s\n' "$(basename -- "$dest")" "$src" "$(sha256sum -- "$dest" | cut -d' ' -f1)" >> "$MANIFEST"
}

for b in $BATCHES; do
    ref_dir="$REF_ROOT/${REF_OVERRIDE[$b]:-${REF_PATTERN//\{b\}/$b}}"
    pgdb_dir="$PGDB_ROOT/${PGDB_PATTERN//\{b\}/$b}"
    for pair in "ref:$ref_dir" "v5:$pgdb_dir"; do
        tag="${pair%%:*}"; dir="${pair#*:}"
        for table in stats pg_matrix gg_matrix unique_genes_matrix; do
            copy "$dir/quant_tables/diann_report.$table.tsv" "$SMALL/${tag}_b$b.$table.tsv"
        done
    done
    # SDRF of the proteogenomic search (both searches of a batch used the same SDRF).
    sdrf="$(find "$pgdb_dir/sdrf" -maxdepth 1 -name '*.sdrf.tsv' 2>/dev/null | head -n 1 || true)"
    if [[ -n "$sdrf" ]]; then
        copy "$sdrf" "$SMALL/sdrf_b$b.tsv"
    else
        echo "WARNING: no SDRF found in $pgdb_dir/sdrf; sdrf_b$b.tsv not written" >&2
    fi
    files="$(awk 'NR > 1' "$SMALL/v5_b$b.stats.tsv" | wc -l)"
    echo "batch $b: copied (proteogenomic search: $files DIA files)"
done

echo "manifest: $MANIFEST"
