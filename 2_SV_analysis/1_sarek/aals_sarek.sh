#!/bin/bash

# Load apptainer (to use hemera instead of miniconda)
#spack load apptainer

# Change to the directory containing the script
cd /sarek-3.5.1/3_5_1/

#NXF_VER=24.04.4 
nextflow run main.nf \
  -profile apptainer \
  -c sarek.config \
  --input sarek_samplesheet.csv \
  --outdir /results/sarek/batch \
  -params-file sarek.json \
  -resume


# nextflow clean -f -before $(nextflow log -q | tail -n 1)