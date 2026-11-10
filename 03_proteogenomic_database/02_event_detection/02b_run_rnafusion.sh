#!/bin/bash
# Run nf-core/rnafusion 4.0.0 for one RNA-seq batch.
# Usage: bash 02b_run_rnafusion.sh <N>     # N = 1..6
# Samplesheets come from 02a_create_rnafusion_samplesheet.py; references from 01_build_rnafusion_references.sh.
# Before running, set the reference paths in 02_03_params/rnafusion.config and rnafusion.json.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ---- Settings (override with environment variables) --------------------------
BATCH="${1:?Usage: bash 02b_run_rnafusion.sh <batch number>}"
RNAFUSION_PIPELINE="${RNAFUSION_PIPELINE:-nf-core/rnafusion}"   # or a local clone's main.nf
RNAFUSION_RELEASE="${RNAFUSION_RELEASE:-4.0.0}"
GENOMES_BASE="${GENOMES_BASE:-/path/to/references/GRCh38}"      # external: rnafusion references
SAMPLESHEET="${SAMPLESHEET:-/path/to/rna_batches/samplesheet_batch${BATCH}_rnaseqfusion.csv}"
RNAFUSION_OUTDIR="${RNAFUSION_OUTDIR:-/path/to/nf_results/rnafusion}"
RNAFUSION_CONFIG="${RNAFUSION_CONFIG:-$SCRIPT_DIR/02_03_params/rnafusion.config}"
RNAFUSION_PARAMS="${RNAFUSION_PARAMS:-$SCRIPT_DIR/02_03_params/rnafusion.json}"
# Optional: folders holding STAR and STAR-Fusion binaries, if they are not already on PATH
[[ -n "${STAR_DIR:-}" ]] && export PATH="$STAR_DIR:$PATH"
[[ -n "${STARFUSION_DIR:-}" ]] && export PATH="$STARFUSION_DIR:$PATH"
# -------------------------------------------------------------------------------

release_args=()
[[ "$RNAFUSION_PIPELINE" == */main.nf ]] || release_args=(-r "$RNAFUSION_RELEASE")

nextflow run "$RNAFUSION_PIPELINE" "${release_args[@]}" \
  --genomes_base "$GENOMES_BASE" \
  --input "$SAMPLESHEET" \
  --outdir "$RNAFUSION_OUTDIR/batch${BATCH}/" \
  -c "$RNAFUSION_CONFIG" \
  --tools all \
  -params-file "$RNAFUSION_PARAMS" \
  -profile apptainer \
  -resume
