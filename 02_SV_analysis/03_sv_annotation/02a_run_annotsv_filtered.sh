#!/usr/bin/env bash
set -euo pipefail

# Shared filtered/unfiltered runner (03_run_annotsv_unfiltered.sh calls this with
# --mode unfiltered). The defaults retain the historical run names.
export PATH="${ANNOTSV_BIN_DIR:-/home/kcoetzer/objective_two/AnnotSV/bin}:$PATH"
INPUT_DIR="${INPUT_DIR:-/home/kcoetzer/objective_two/octopusv/octopusv_merged_02092026/merged}"
OUT_DIR="${OUT_DIR:-${OUTPUT_DIR:-/home/kcoetzer/objective_two/run_annotsv/results}}"
GENES="${GENES:-/home/kcoetzer/objective_two/run_annotsv/data/gene_lists/ALS_candidate_gene_list.txt}"
ANNOTATIONS="${ANNOTATIONS:-/home/kcoetzer/objective_two/AnnotSV/share/AnnotSV}"
MODE=filtered
RUN_LABEL=""

usage() {
    echo "Usage: 02_run_annotsv_filtered.sh [--mode filtered|unfiltered] [--input-dir DIR] [--out-dir DIR] [--run-label LABEL]"
    echo "Paths can be supplied through INPUT_DIR, OUT_DIR (or legacy OUTPUT_DIR), GENES, ANNOTATIONS and ANNOTSV_BIN_DIR."
}

while (( $# )); do
    case "$1" in
        --input-dir) INPUT_DIR="${2:?ERROR: --input-dir requires a directory}"; shift 2 ;;
        --out-dir) OUT_DIR="${2:?ERROR: --out-dir requires a directory}"; shift 2 ;;
        --mode) MODE="${2:?ERROR: --mode requires filtered or unfiltered}"; shift 2 ;;
        --run-label) RUN_LABEL="${2:?ERROR: --run-label requires a label}"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done
# Default label matches the final runs in results_annotsv_final.
RUN_LABEL="${RUN_LABEL:-08102026}"
[[ "$MODE" == filtered || "$MODE" == unfiltered ]] || { echo "ERROR: --mode must be filtered or unfiltered" >&2; exit 2; }
[[ "$RUN_LABEL" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo "ERROR: Invalid run label" >&2; exit 2; }
command -v AnnotSV >/dev/null || { echo "ERROR: AnnotSV not found" >&2; exit 127; }
[[ -d "$ANNOTATIONS" ]] || { echo "ERROR: Annotation directory not found: $ANNOTATIONS" >&2; exit 2; }
for callset in intersect union; do
    [[ -s "$INPUT_DIR/manta_tiddit.${callset}.cohort.vcf" ]] || {
        echo "ERROR: Missing/empty $callset input VCF" >&2; exit 2;
    }
done
if [[ "$MODE" == filtered && ! -s "$GENES" ]]; then
    echo "ERROR: Candidate gene file not found or empty: $GENES" >&2; exit 2
fi
mkdir -p "$OUT_DIR"

run_callset() {
    local callset="$1"
    local name="octopusv_${callset}_cohort_${MODE}_${RUN_LABEL}"
    local -a gene_options=(-candidateGenesFiltering 0)
    if [[ "$MODE" == filtered ]]; then
        gene_options=(-candidateGenesFile "$GENES" -candidateGenesFiltering 1)
    fi
    echo "Running AnnotSV: $callset ($MODE)"
    AnnotSV \
        -annotationsDir "$ANNOTATIONS" \
        -SVinputInfo 1 \
        -SVinputFile "$INPUT_DIR/manta_tiddit.${callset}.cohort.vcf" \
        -tx ENSEMBL \
        "${gene_options[@]}" \
        -variantconvertMode fullsplit \
        -vcf 1 \
        -outputDir "$OUT_DIR/$name" \
        > "$OUT_DIR/AnnotSV_${name}.log" 2>&1
}

run_callset intersect
run_callset union
echo "Both AnnotSV runs completed ($MODE)."
