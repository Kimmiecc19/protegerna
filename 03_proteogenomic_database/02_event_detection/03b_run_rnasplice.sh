#!/bin/bash
# Run nf-core/rnasplice 1.0.3 for one RNA-seq batch.
# Usage: bash 03b_run_rnasplice.sh <N>     # N = 1..6
# Samplesheets come from 03a_create_rnasplice_samplesheet.py.
# Remember to use the fixed-name samplesheet because of DRIMSEQ.
# Before running, set the reference paths in 02_03_params/rnasplice.config.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ---- Settings (override with environment variables) --------------------------
BATCH="${1:?Usage: bash 03b_run_rnasplice.sh <batch number>}"
RNASPLICE_PIPELINE="${RNASPLICE_PIPELINE:-nf-core/rnasplice}"   # or a local clone's main.nf
RNASPLICE_RELEASE="${RNASPLICE_RELEASE:-1.0.3}"
SAMPLESHEET="${SAMPLESHEET:-/path/to/rna_batches/samplesheet_batch${BATCH}_rnasplice.csv}"
RNASPLICE_OUTDIR="${RNASPLICE_OUTDIR:-/path/to/nf_results/rnasplice}"
RNASPLICE_CONFIG="${RNASPLICE_CONFIG:-$SCRIPT_DIR/02_03_params/rnasplice.config}"
RNASPLICE_PARAMS="${RNASPLICE_PARAMS:-$SCRIPT_DIR/02_03_params/rnasplice.json}"
CONTRASTS="${CONTRASTS:-$SCRIPT_DIR/02_03_params/rnasplice_contrast.csv}"   # not in the repository; create it
# -------------------------------------------------------------------------------

release_args=()
[[ "$RNASPLICE_PIPELINE" == */main.nf ]] || release_args=(-r "$RNASPLICE_RELEASE")

nextflow run "$RNASPLICE_PIPELINE" "${release_args[@]}" \
  --input "$SAMPLESHEET" \
  --outdir "$RNASPLICE_OUTDIR/batch${BATCH}" \
  -c "$RNASPLICE_CONFIG" \
  -params-file "$RNASPLICE_PARAMS" \
  --contrasts "$CONTRASTS" \
  -profile apptainer \
  -resume

#"min_samps_gene_expr": 3,
#"min_gene_expr": 10,
#"min_samps_feature_expr": 3,
#"min_feature_expr": 10,
#"min_samps_feature_prop": 3,
#"min_feature_prop": 0.1,
