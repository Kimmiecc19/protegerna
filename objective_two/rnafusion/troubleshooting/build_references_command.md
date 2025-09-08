# Creating rnafusion references automatically using nf-core --build_references
### The rnafusion pipeline needs references for the fusion detection tools, so downloading these is a requirement.
### This step was run on a local device to create the references needed to run nf-core/rnafusion
### Reference files were then transferred to hemera (University sever) and CHPC using rsync

```nextflow
nextflow run main.nf \
  --build_references --all \
  --cosmic_username "email" --cosmic_passwd "password" \
  --genomes_base /home/kimmiecc19/nf-core-rnafusion_3.0.1/fusion_references/references \
  --outdir /home/kimmiecc19/nf-core-rnafusion_3.0.1/fusion_references/references
```

# Note:
First register for a free account at COSMIC at https://cancer.sanger.ac.uk/cosmic/register using a university email. The account is only activated upon clicking the link in the registration email.


## Creates the following folders:
- arriba
- convert2bed
- ensembl
- fusion_report_db
- fusioncatcher
- gatk4
- hgnc
- pipeline_info
- rrna
- star

### arriba
- CREDITS
- cytobands_mm39_GRCm39_v2.4.0.tsv
- RefSeq_viral_genomes_v2.4.0.fa.gz
- known_fusions_hg19_hs37d5_GRCh37_v2.4.0.tsv.gz
- blacklist_hg19_hs37d5_GRCh37_v2.4.0.tsv.gz
- known_fusions_hg38_GRCh38_v2.4.0.tsv.gz
- blacklist_hg38_GRCh38_v2.4.0.tsv.gz
- known_fusions_mm10_GRCm38_v2.4.0.tsv.gz
- blacklist_mm10_GRCm38_v2.4.0.tsv.gz
- known_fusions_mm39_GRCm39_v2.4.0.tsv.gz
- blacklist_mm39_GRCm39_v2.4.0.tsv.gz
- protein_domains_hg19_hs37d5_GRCh37_v2.4.0.gff3
- protein_domains_hg38_GRCh38_v2.4.0.gff3
- protein_domains_mm10_GRCm38_v2.4.0.gff3
- protein_domains_mm39_GRCm39_v2.4.0.gff3

### convert2bed
- Homo_sapiens.GRCh38.102.bed

### ensembl
- Homo_sapiens.GRCh38.102.all.fa
- Homo_sapiens.GRCh38.102.chr.gtf
- Homo_sapiens.GRCh38.102.interval_list
- Homo_sapiens.GRCh38.102.all.fa.fai
- Homo_sapiens.GRCh38.102.chr.gtf.refflat
- Homo_sapiens.GRCh38.102.cdna.all.fa.gz
- Homo_sapiens.GRCh38.102.gtf

### fusion_report_db
- DB-timestamp.txt
- cosmic.db
- fusion_report.log
- fusiongdb2.db
- mitelman.db

### fusioncatcher
- human_v102/
- 1000genomes.txt
- 18cancers.txt
- 7skrnas.txt
- adjacent_genes.txt
- banned.txt
- banned_seq.fa
- biotypes.txt
- biotypes_header.txt
- bodymap2.txt
- cacg.txt
- cancer_genes.txt
- ccle.txt
- ccle2.txt
- ccle3.txt
- cgp.txt
- chimerdb2.txt
- chimerdb4kb.txt
- chimerdb4pub.txt
- chimerdb4seq.txt
- chromosomes_lengths.txt
- conjoing.txt
- cortex.txt
- cosmic.txt
- custom_genes.bed
- custom_genes.txt
- custom_genes_mark.txt
- custom_transcripts_mark.txt
- descriptions.txt
- descriptions_header.txt
- dgd.txt
- enlarge.txt
- enlarged_genes.bed
- ensembl_fully_overlapping_genes.txt
- ensembl_overlapping_genes.txt
- ensembl_partially_overlapping_genes.txt
- ensembl_removed-overlapping-genes.txt
- ensembl_same_strand_overlapping_genes.txt
- exons.fa
- exons.txt
- exons_header.txt
- exons_original.txt
- exons_removed.txt
- final-list_candidate-fusion-genes.caption.md.txt
- gap_fusions.txt
- gencode_fully_overlapping_genes.txt
- gencode_genes.txt
- gencode_genes_header.txt
- gencode_partially_overlapping_genes.txt
- gencode_same_strand_overlapping_genes.txt
- genes.fa
- genes.txt
- genes_backup.txt
- genes_header.txt
- genes_original.txt
- genes_removed.txt
- genes_symbols.txt
- genes_with_no_proteins.txt
- genome_index2
- genome_information.txt
- gliomas.txt
- gtex.txt
- gtex_removed.txt
- healthy.txt
- hg38ToHg19.over.chain.gz
- hla.txt
- hla2.fa
- hla2.txt
- hpa.txt
- ig_loci.txt
- known.txt
- known_genes.txt
- lncrnas.txt
- metastasis.txt
- metazoa.txt
- mirnas.txt
- mitelman.txt
- mt.txt
- non-cancer_tissues.txt
- non-tumor_cells.txt
- oesophagus.txt
- oncogenes.txt
- oncogenes_more.txt
- oncokb.txt
- organism.gtf
- organism.txt
- pairs_pseudogenes.txt
- pancreases.txt
- paralogs.txt
- paralogs_header.txt
- pcawg.txt
- prostate_cancer.txt
- pseudogenes.bed
- pseudogenes.txt
- readthroughs.txt
- refseq_fully_overlapping_genes.txt
- refseq_genes.txt
- refseq_genes_header.txt
- refseq_ids.txt
- refseq_ids_header.txt
- refseq_partially_overlapping_genes.txt
- refseq_same_strand_overlapping_genes.txt
- removed_features.txt
- ribosomal_proteins.txt
- rnas_y.txt
- rrnas.txt
- rtcircrnas.txt
- rtrna_hla_mt.fa
- rtrna_hla_mt_index
- rtrna_index
- shield__report.txt
- shield_against_pseudo-genes.bed
- shield_against_pseudo-genes.txt
- shield_against_pseudo-genes_not-found.txt
- shield_erase-regions.bed
- shield_pseudogenes-predicted-to-be-erased.bed
- shield_pseudogenes-predicted-to-be-erased.txt
- shielded_genes.bed
- shielded_genes.txt
- shielded_reads_similarity.bed
- snornas.txt
- snrnas.txt
- synonyms.txt
- tcga-cancer.txt
- tcga-normal.txt
- tcga.txt
- tcga2.txt
- tcga3.txt
- ticdb.txt
- transcripts.fa
- transcripts.txt
- transcripts_index
- trnas.txt
- tumor_genes.txt
- ucsc_fully_overlapping_genes.txt
- ucsc_genes.txt
- ucsc_genes_header.txt
- ucsc_partially_overlapping_genes.txt
- ucsc_same_strand_overlapping_genes.txt
- version.txt
- viruses_index


### gatk4
- Homo_sapiens.GRCh38.102.all.dict

### hgnc
- HGNC-DB-timestamp.txt
- hgnc_complete_set.txt

### pipeline_info
- Created by running the pipeline

### rrna
- Homo_sapiens.GRCh38.102_rrna_intervals.gtf

### star
- Genome
- SAindex
- chrNameLength.txt
- exonInfo.tab
- sjdbInfo.txt
- transcriptInfo.tab
- Log.out
- chrLength.txt
- chrStart.txt
- geneInfo.tab
- sjdbList.fromGTF.out.tab
- SA
- chrName.txt
- exonGeTrInfo.tab
- genomeParameters.txt
- sjdbList.out.tab

# Troubleshooting

See rnafusion_troublshooting.md
