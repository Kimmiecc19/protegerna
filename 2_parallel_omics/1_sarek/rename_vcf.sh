#!/bin/bash
"""
This script renames the sample names in nf-core/sarek's structural variant VCF files
to match their respective file names. It reads a list of VCF file paths
from 'sv_vcf_list.txt', extracts the base name (without extension) from each file
path, and uses 'bcftools reheader' to update the sample name in the VCF file. 
This is done to avoid issues when reannotating VCF files.
"""

mkdir -p fixed_vcfs

while read f; do
  name=$(basename "$f" .vcf.gz)
  echo "Fixing sample name for $f → $name"
  
  bcftools reheader -s <(echo "$name") "$f" -o fixed_vcfs/${name}.vcf.gz
done < sv_vcf_list.txt
