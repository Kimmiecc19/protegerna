# Final shorter version with less terms - September 2025

# This script indicated which tools must be fetched from the bio.tools database based on specific search terms related to genomics, transcriptomics, proteomics, and multi-omics.

# Genomics
python fetch_biotools_final2025.py "genomic,genome,dna,gene,variant calling,variant,assembly,assemblies,annotation,sequencing,read alignment,vcf,snp,indel,reference genome,sequence analysis,sequence alignment" genomics_september2025.tsv --tsv

# Transcriptomics
python fetch_biotools_final2025.py "transcriptomic,transcriptome,rna-seq,RNAseq,rna seq,gene expression,fusion gene,transcript,rna sequencing,splicing,splice,expression analysis" transcriptomics_september2025.tsv --tsv

# Proteomics
python fetch_biotools_final2025.py "proteomic,protein,peptide,mass spectrometry,MS,MS/MS,quantitative proteomics,peptide identification,protein identification,protein inference,protein annotation" proteomics_september2025.tsv --tsv

# Multi-omics
python fetch_biotools_final2025.py "multi-omic,multiomic,proteogenomic,integration,integrative,cross-omic,pan-omic,pathway or network" multiomics_september2025.tsv --tsv
