#!/usr/bin/env nextflow
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    nf-core/protegerna
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Github : https://github.com/nf-core/protegerna
    Website: https://nf-co.re/protegerna
    Slack  : https://nfcore.slack.com/channels/protegerna
----------------------------------------------------------------------------------------
*/
nextflow.enable.dsl = 2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS / WORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PROTEGERNA              } from './workflows/protegerna'
include { PIPELINE_INITIALISATION } from './subworkflows/local/utils_nfcore_protegerna_pipeline'
include { PIPELINE_COMPLETION     } from './subworkflows/local/utils_nfcore_protegerna_pipeline'
include { getGenomeAttribute      } from './subworkflows/local/utils_nfcore_protegerna_pipeline'

params.fasta = getGenomeAttribute('fasta')

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow {

    PIPELINE_INITIALISATION(
        params.get('version'),
        params.get('validate_params'),
        params.get('monochrome_logs'),
        args,
        params.get('outdir'),
        params.get('input'),
        params.get('help'),
        params.get('help_full'),
        params.get('show_hidden')
    )

    if (params.get('help')) {
        log.info 'nextflow run . -profile apptainer --input samplesheet.csv --genome genome.fa --gtf_db annotation.db --reference_proteome reference.fa --gencode_protein_fasta gencode.fa --proteogenomic_container /path/runtime.sif --outdir results'
    } else {
        def profiles = workflow.profile.tokenize(',')
        if (!profiles.any { it in ['publication', 'test'] }) {
            error '''Select -profile publication or -profile test

Publication run:
  nextflow run . -profile publication -params-file params.yml -resume
  (start from assets/params.publication.yml)

Smoke test:
  nextflow run . -profile test --proteogenomic_container /abs/path/protegerna.sif'''
        }
        if (profiles.containsAll(['publication', 'test'])) {
            error 'Use either -profile publication or -profile test, not both'
        }
        ['input', 'genome', 'reference_proteome', 'gencode_protein_fasta', 'annotation_release', 'organism', 'outdir', 'proteogenomic_container'].each { key ->
            if (!params.get(key)) {
                error "Required parameter: --${key}"
            }
        }
        if ((!params.get('gtf') && !params.get('gtf_db')) || (params.get('gtf') && params.get('gtf_db'))) {
            error 'Provide exactly one of --gtf or --gtf_db'
        }
        ['genome', 'reference_proteome'].each { key ->
            if (params.get(key).toString().endsWith('.gz')) {
                error "--${key} must be an uncompressed FASTA"
            }
        }

        PROTEGERNA(
            PIPELINE_INITIALISATION.out.samplesheet,
            params.get('multiqc_config'),
            params.get('multiqc_logo'),
            params.get('multiqc_methods_description'),
            params.get('outdir')
        )

        PIPELINE_COMPLETION(
            params.get('email'),
            params.get('email_on_fail'),
            params.get('plaintext_email'),
            params.get('outdir'),
            params.get('monochrome_logs'),
            PROTEGERNA.out.multiqc_report
        )
    }

    def pipeline_help = params.get('help')
    def pipeline_outdir = params.get('outdir')
    def pipeline_params = params
    def pipeline_workflow = workflow

    workflow.onComplete {
        if (!pipeline_help && pipeline_outdir) {
            def info = file("${pipeline_outdir}/pipeline_info")
            info.mkdirs()
            def provenance = [
                run_name: pipeline_workflow.runName,
                session_id: pipeline_workflow.sessionId.toString(),
                nextflow_version: pipeline_workflow.nextflow.version.toString(),
                success: pipeline_workflow.success,
                command_line: pipeline_workflow.commandLine,
                work_directory: pipeline_workflow.workDir.toString(),
                parameters: pipeline_params
            ]
            info.resolve("run_${pipeline_workflow.runName}.json").text =
                groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(provenance)) + '\n'
        }
    }
}
