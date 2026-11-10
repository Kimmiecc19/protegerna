#!/bin/bash

# Change to the directory containing the script
cd /home/kcoetzer/nf/nf_pipelines/rnasplice-1.0.3/1_0_3/

# Remember to use fix name script for samplesheet because of DRIMSEQ

nextflow run main.nf \
  --input /home/kcoetzer/DATA/transcriptomics/1_fastq/rna_batches/samplesheet_batch1_rnasplice.csv \
  --outdir /home/kcoetzer/nf/nf_results/rnasplice/batch1 \
  -c /home/kcoetzer/nf/nf_params/rnasplice/rnasplice.config \
  -params-file /home/kcoetzer/nf/nf_params/rnasplice/rnasplice.json \
  --contrasts /home/kcoetzer/nf/nf_params/rnasplice/rnasplice_contrast.csv \
  -profile apptainer \
  -resume


#"min_samps_gene_expr": 3,
#"min_gene_expr": 10,
#"min_samps_feature_expr": 3,
#"min_feature_expr": 10,
#"min_samps_feature_prop": 3,
#"min_feature_prop": 0.1,