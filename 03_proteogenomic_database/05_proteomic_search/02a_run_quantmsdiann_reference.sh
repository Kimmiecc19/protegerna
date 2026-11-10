#!/bin/bash
# Run bigbio/quantmsdiann 2.2.0 (DIA-NN 1.8.1): reference search of one DIA batch.
# Usage: bash 02a_run_quantmsdiann_reference.sh <N>     # N = 1..6
# Results are written to 02a_results_quantmsdiann_reference/batch${BATCH} by default (batch 1 of the reference search was saved as batch1_fixed).
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ---- Settings (override with environment variables) --------------------------
BATCH="${1:?Usage: bash 02a_run_quantmsdiann_reference.sh <batch number>}"
QUANTMS_PIPELINE="${QUANTMS_PIPELINE:-bigbio/quantmsdiann}"   # or a local clone's main.nf
QUANTMS_RELEASE="${QUANTMS_RELEASE:-2.2.0}"
SDRF="${SDRF:-/path/to/proteomics/sdrf_batch${BATCH}_flat_paths_fixed.sdrf.tsv}"   # per-batch SDRF (controlled access)
OUTDIR="${OUTDIR:-$SCRIPT_DIR/02a_results_quantmsdiann_reference/batch${BATCH}}"
QUANTMS_CONFIG="${QUANTMS_CONFIG:-$SCRIPT_DIR/02_params/reference.config}"
QUANTMS_PARAMS="${QUANTMS_PARAMS:-$SCRIPT_DIR/02_params/reference.json.json}"
DATABASE="${DATABASE:-$SCRIPT_DIR/01_results_make_reference_database/human_reference_deduplicated.fasta}"
# -------------------------------------------------------------------------------

release_args=()
[[ "$QUANTMS_PIPELINE" == */main.nf ]] || release_args=(-r "$QUANTMS_RELEASE")

nextflow run "$QUANTMS_PIPELINE" "${release_args[@]}" \
  --input "$SDRF" \
  --outdir "$OUTDIR" \
  --database "$DATABASE" \
  -c "$QUANTMS_CONFIG" \
  -params-file "$QUANTMS_PARAMS" \
  -profile apptainer \
  -resume
