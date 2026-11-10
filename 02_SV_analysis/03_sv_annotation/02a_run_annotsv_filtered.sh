#!/usr/bin/env bash
set -euo pipefail

# Shared filtered/unfiltered runner (02b_run_annotsv_unfiltered.sh calls this with
# --mode unfiltered). Defaults follow this repository; the AnnotSV install is external.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SV_DIR="$(dirname "$SCRIPT_DIR")"

# ---- Settings (override with environment variables) --------------------------
ANNOTSV_BIN_DIR="${ANNOTSV_BIN_DIR:-/path/to/AnnotSV/bin}"                 # AnnotSV 3.5.8 install (external)
ANNOTATIONS="${ANNOTATIONS:-/path/to/AnnotSV/share/AnnotSV}"              # AnnotSV GRCh38 annotations (external)
INPUT_DIR="${INPUT_DIR:-$SV_DIR/02_sv_consolidation/01_results_octopusv/merged}"
GENES="${GENES:-$SV_DIR/04_sv_prioritization/data/ALS_candidate_gene_list.txt}"
OUT_DIR="${OUT_DIR:-${OUTPUT_DIR:-}}"   # default set below from --mode
# -------------------------------------------------------------------------------
export PATH="$ANNOTSV_BIN_DIR:$PATH"
MODE=filtered
RUN_LABEL=""

usage() {
    echo "Usage: 02a_run_annotsv_filtered.sh [--mode filtered|unfiltered] [--input-dir DIR] [--out-dir DIR] [--run-label LABEL]"
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
# Default labels and output folders match the saved runs:
#   filtered   -> 02a_results_annotsv_filtered/octopusv_*_cohort_filtered_05102026
#   unfiltered -> 02b_results_annotsv_unfiltered/octopusv_*_cohort_unfiltered_03102026
if [[ "$MODE" == filtered ]]; then
    RUN_LABEL="${RUN_LABEL:-05102026}"
    OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/02a_results_annotsv_filtered}"
else
    RUN_LABEL="${RUN_LABEL:-03102026}"
    OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/02b_results_annotsv_unfiltered}"
fi
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
