#!/bin/bash

# Load apptainer (to use hemera instead of miniconda)
#spack load apptainer

# Change to the directory containing the script
cd /home/kcoetzer/nf/nf_pipelines/sarek-3.5.1/3_5_1/

#NXF_VER=24.04.4 
nextflow run main.nf \
  -profile apptainer \
  -c /home/kcoetzer/nf/nf_params/sarek/sarek.config \
  --input /home/kcoetzer/DATA/genomics/2_cram/sarek_samplesheet_part_4.csv \
  --outdir /home/kcoetzer/nf/nf_results/sarek/batch4 \
  -params-file /home/kcoetzer/nf/nf_params/sarek/sarek.json \
  -resume


# nextflow clean -f -before $(nextflow log -q | tail -n 1)