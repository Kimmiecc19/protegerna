#!/bin/bash

# Change to the directory containing the script
cd /home/kcoetzer/nf/nf_pipelines/rnafusion-3.0.2/3_0_2/

# command to build reference
nextflow run main.nf \
  --build_references \
  --arriba --starfusion --fusioncatcher \
  -c /home/kcoetzer/nf/nf_params/rnafusion/rnafusion_build.config \
  --cosmic_username "kcoetzer@sun.ac.za" \
  --cosmic_passwd "Kimmiecc-19" \
  --genomes_base /home/kcoetzer/nf/nf_references/fusion_ref_092025 \
  --outdir /home/kcoetzer/nf/nf_references/fusion_ref_092025 \
  -profile apptainer \
  -resume

"""
nextflow run /home/kcoetzer/nf/nf_pipelines/rnafusion_4.0.0/4_0_0/main.nf \
  -profile apptainer \
  --references_only --tools fusionreport \
  --cosmic_username "kcoetzer@sun.ac.za" \
  --cosmic_passwd "Kimmiecc-19" \
  --outdir /home/kcoetzer/nf/nf_references/GRCh38
"""