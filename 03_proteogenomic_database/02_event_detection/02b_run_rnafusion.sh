#!/bin/bash

# Change to the directory containing the script
cd /home/kcoetzer/nf/nf_pipelines/rnafusion_4.0.0/4_0_0/

#Add STAR path variable
export PATH="/home/kcoetzer/STAR/source:$PATH"
export PATH="/home/kcoetzer/nf/nf_references/fusion_ref/starfusion/STAR-Fusion:$PATH"

# Run the Nextflow command
nextflow run main.nf \
  --genomes_base /home/kcoetzer/nf/nf_references/GRCh38 \
  --input /home/kcoetzer/DATA/transcriptomics/1_fastq/rna_batches/samplesheet_batch3_rnaseqfusion.csv \
  --outdir /home/kcoetzer/nf/nf_results/rnafusion/batch3/ \
  -c /home/kcoetzer/nf/nf_params/rnafusion/rnafusion.config \
  --tools all \
  -params-file /home/kcoetzer/nf/nf_params/rnafusion/rnafusion.json \
  -profile apptainer \
  -resume

