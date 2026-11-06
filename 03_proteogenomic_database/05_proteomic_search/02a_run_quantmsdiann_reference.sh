#!/bin/bash

# Change to the directory containing the script
#cd /home/kcoetzer/nf/nf_pipelines/quantms-1.2.0/
#cd /home/kcoetzer/nf/nf_pipelines/quantms
cd /home/kcoetzer/nf/nf_pipelines/bigbio-quantmsdiann_v2.2.0/v2_2_0

# Run the Nextflow command
nextflow run main.nf \
  --input /home/kcoetzer/DATA/proteomics/sdrf_batch1_flat_paths_fixed.sdrf.tsv \
  --outdir /home/kcoetzer/nf/nf_results/quantms/reference/batch1_fixed \
  -c /home/kcoetzer/nf/nf_params/quantms/aals_quantms_diann.config \
  -params-file /home/kcoetzer/nf/nf_params/quantms/aals_quantms_diann.json \
  -profile apptainer \
  -resume


#export SINGULARITY_DOCKER_USERNAME="Kimmiecc19"
#export SINGULARITY_DOCKER_PASSWORD="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"
#singularity pull diann-2.2.0.sif docker://ghcr.io/bigbio/diann:2.2.0

