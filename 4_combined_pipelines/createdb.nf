#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*

// This script takes the output from rnaseq, raredisease, rnasplice, and rnafusion to convert to protein FASTA files for creating a protein database of splice, fusion, and genetic variants as input for quantms.
// Files need to be converted to a nucleotide fasta and then translated (3 or 6 frame) into a protein fasta file.
// The output then needs to be concatenated with user-defined variant protein databases of their choosing.

========================================================================================
    IMPORT LOCAL MODULES/SUBWORKFLOWS
========================================================================================
*/

//TODO: Create containers for the tools used in these scripts for example EMBL TranSeq tool for nucleotide translation
// See if I can edit the vcf2prot pipeline to be able to use the raredisease vcf as input instead of a bcf generated file
include { JUNCTION_TO_BED }              from '../modules/local/createdb/main'
include { SPLICE_TO_BED }                from '../modules/local/createdb/main'
include { FUSION_TO_BED }                from '../modules/local/createdb/main'
include { VCF_TO_BED }                   from '../modules/local/createdb/main' 
include { COMBINE_BED }                  from '../modules/local/createdb/main'

include { PREPDATA_TO_BED }              from ''./subworkflows/local/createdb/prepdatatobed' // This is created using the _TO_BED modules. This will also combine the bed files
include { BED_TO_FASTA }                 from './subworkflows/local/createdb/bedtofasta' // convertes combined bed file to nucleotide fasta 
include { TRANSLATE_FASTA }              from './subworkflows/local/createdb/translatefasta' // Three/Six- frame translation of nucleotide sequences
include { COMBINE_FASTA }                from './subworkflows/local/createdb/combinefasta' // combine created database with other databases added (user specified and variant proteins)


// TODO: Quality checks?? 

/*
========================================================================================
    IMPORT NF-CORE MODULES/SUBWORKFLOWS
========================================================================================
*/

// include { }                  from '../modules/nf-core/' Check samplesheet? 


/*
========================================================================================
    RUN MAIN WORKFLOW
========================================================================================
*/

//Run subworkflows and modules
workflow NFCORE_CREATEDB {

    PREPDATA_TO_BED (
        ch_reads_all,
        COMBINE_BED.out.bed
    )
    ch_versions = ch_versions.mix(PREPDATA_TO_BED.out.versions)

    BED_TO_FASTA (
        ch_reads_all,
        NUCELOTIDE_FASTA.out.fasta,
        ch_chrgtf
    )
    ch_versions = ch_versions.mix(BED_TO_FASTA.out.versions)  

    TRANSLATE_FASTA (
        ch_reads_all,
        PROTEIN_FASTA.out.fasta
    )
    ch_versions = ch_versions.mix(TRANSLATE_FASTA.out.versions)

    COMBINE_FASTA (
        ch_reads_all,
        ch_fusionreport_ref,
        PROTEINDB.out.fasta
    )
    ch_versions = ch_versions.mix(COMBINE_FASTA.out.versions)

}


/*
========================================================================================
    THE END
========================================================================================
*/

