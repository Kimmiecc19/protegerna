#!/bin/bash
# Build the nf-core/rnafusion references (arriba, STAR-Fusion, FusionCatcher; fusion-report database).
# Usage:
#   export COSMIC_USERNAME='you@example.org'
#   export COSMIC_PASSWD='...'          # never write credentials in this file or in a params file
#   bash 01_build_rnafusion_references.sh
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ---- Settings (override with environment variables) --------------------------
RNAFUSION_BUILD_PIPELINE="${RNAFUSION_BUILD_PIPELINE:-nf-core/rnafusion}"  # or a local clone's main.nf
RNAFUSION_BUILD_RELEASE="${RNAFUSION_BUILD_RELEASE:-3.0.2}"                # release used to build the references
BUILD_CONFIG="${BUILD_CONFIG:-$SCRIPT_DIR/02_03_params/rnafusion_build.config}"
FUSION_REF_DIR="${FUSION_REF_DIR:-/path/to/references/fusion_ref}"         # external: reference output folder
: "${COSMIC_USERNAME:?Set COSMIC_USERNAME}"
: "${COSMIC_PASSWD:?Set COSMIC_PASSWD}"
# -------------------------------------------------------------------------------

release_args=()
[[ "$RNAFUSION_BUILD_PIPELINE" == */main.nf ]] || release_args=(-r "$RNAFUSION_BUILD_RELEASE")

nextflow run "$RNAFUSION_BUILD_PIPELINE" "${release_args[@]}" \
  --build_references \
  --arriba --starfusion --fusioncatcher \
  -c "$BUILD_CONFIG" \
  --cosmic_username "$COSMIC_USERNAME" \
  --cosmic_passwd "$COSMIC_PASSWD" \
  --genomes_base "$FUSION_REF_DIR" \
  --outdir "$FUSION_REF_DIR" \
  -profile apptainer \
  -resume

# The fusion-report database for rnafusion 4.0.0 was built separately with:
# nextflow run nf-core/rnafusion -r 4.0.0 \
#   -profile apptainer \
#   --references_only --tools fusionreport \
#   --cosmic_username "$COSMIC_USERNAME" \
#   --cosmic_passwd "$COSMIC_PASSWD" \
#   --outdir /path/to/references/GRCh38
