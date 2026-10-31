#!/bin/bash

# Change to the directory containing the script
#cd /home/kcoetzer/nf/nf_pipelines/quantms-1.2.0/
cd /home/kcoetzer/nf/nf_pipelines/bigbio-quantmsdiann_v2.2.0/v2_2_0

# Run the Nextflow command
#nextflow run main.nf \
NXF_OFFLINE=true nextflow run main.nf \
  --input /home/kcoetzer/DATA/proteomics/sdrf_batch3_flat_paths_fixed.sdrf.tsv \
  --outdir /home/kcoetzer/nf/nf_results/quantms/pgdb/pgdb_v5_batch3 \
  -c /home/kcoetzer/nf/nf_params/quantms/aals_quantms.config \
  -params-file /home/kcoetzer/nf/nf_params/quantms/aals_quantms_pgdb.json \
  -profile apptainer \
  -resume