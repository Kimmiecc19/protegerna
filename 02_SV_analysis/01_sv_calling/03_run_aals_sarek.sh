#!/bin/bash
# Run nf-core/sarek 3.5.1 (Manta + TIDDIT) for one samplesheet batch.
# Usage: bash 03_run_aals_sarek.sh <N>        # N = 1..14 (01_results_sarek_samplesheet/sarek_samplesheet_part_N.csv)
#
# Before running, set the reference paths in aals_sarek.config (fasta, fasta_fai, dict, cacheDir)
# and aals_sarek.json (known_snps, known_indels, snpeff_cache, vep_cache, ...).
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Load apptainer if your system uses modules or spack, e.g.
#spack load apptainer

# ---- Settings (override with environment variables) --------------------------
PART="${1:?Usage: bash 03_run_aals_sarek.sh <samplesheet part number>}"
SAREK_PIPELINE="${SAREK_PIPELINE:-nf-core/sarek}"      # or a local clone, e.g. /path/to/sarek-3.5.1/main.nf
SAREK_RELEASE="${SAREK_RELEASE:-3.5.1}"
SAMPLESHEET="${SAMPLESHEET:-$SCRIPT_DIR/01_results_sarek_samplesheet/sarek_samplesheet_part_${PART}.csv}"
SAREK_OUTDIR="${SAREK_OUTDIR:-/path/to/sarek_results}" # per-participant VCFs (controlled access, outside the repository)
SAREK_CONFIG="${SAREK_CONFIG:-$SCRIPT_DIR/aals_sarek.config}"
SAREK_PARAMS="${SAREK_PARAMS:-$SCRIPT_DIR/aals_sarek.json}"
# -------------------------------------------------------------------------------

release_args=()
[[ "$SAREK_PIPELINE" == */main.nf ]] || release_args=(-r "$SAREK_RELEASE")

#NXF_VER=24.04.4
nextflow run "$SAREK_PIPELINE" "${release_args[@]}" \
  -profile apptainer \
  -c "$SAREK_CONFIG" \
  -params-file "$SAREK_PARAMS" \
  --input "$SAMPLESHEET" \
  --outdir "$SAREK_OUTDIR/part${PART}" \
  -resume

# nextflow clean -f -before $(nextflow log -q | tail -n 1)
