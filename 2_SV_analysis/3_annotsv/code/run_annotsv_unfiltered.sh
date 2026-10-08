#!/usr/bin/env bash
set -euo pipefail

export PATH="/AnnotSV/bin:$PATH"

INPUT_DIR="/octopusv/octopusv_merged_02092026/merged"
OUTPUT_DIR="/run_annotsv/results"
#GENES="/gene_lists/ALS_candidate_gene_list.txt"
ANNOTATIONS="/AnnotSV/share/AnnotSV"

mkdir -p "$OUTPUT_DIR"

AnnotSV \
    -annotationsDir "$ANNOTATIONS" \
    -SVinputInfo 1 \
    -SVinputFile "$INPUT_DIR/manta_tiddit.intersect.cohort.vcf" \
    -candidateGenesFiltering 0 \
    -variantconvertMode fullsplit \
    -vcf 1 \
    -outputDir "$OUTPUT_DIR/octopusv_intersect_cohort_unfiltered_02092026" \
    > "$OUTPUT_DIR/AnnotSV_octopusv_intersect_cohort_unfiltered_02092026.log" 2>&1 &

pid_intersect=$!

AnnotSV \
    -annotationsDir "$ANNOTATIONS" \
    -SVinputInfo 1 \
    -SVinputFile "$INPUT_DIR/manta_tiddit.union.cohort.vcf" \
    -candidateGenesFiltering 0 \
    -variantconvertMode fullsplit \
    -vcf 1 \
    -outputDir "$OUTPUT_DIR/octopusv_union_cohort_unfiltered_02092026" \
    > "$OUTPUT_DIR/AnnotSV_octopusv_union_cohort_unfiltered_02092026.log" 2>&1 &

pid_union=$!

wait "$pid_intersect"
wait "$pid_union"

echo "Both AnnotSV runs completed."
