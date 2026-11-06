process VALIDATE_GENCODE_TRANSLATION {
    tag 'validate'
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/validate", mode: params.publish_dir_mode, saveAs: { it == 'versions.yml' ? null : it }
    input:
    val options
    path runtime, stageAs: 'runtime'
    path gtf_db, stageAs: 'references/annotation.db'
    path genome, stageAs: 'references/genome.fa'
    path gencode_protein_fasta, stageAs: 'references/gencode/*'
    output:
    path "${options.out_tsv}", emit: concordance
    path "${options.out_summary_json}", emit: summary_json
    path 'versions.yml', emit: versions
    path 'task_inputs.json', emit: provenance
    path 'command.json', emit: command
    path '*.run_config.json', emit: run_config, optional: true
    path '*_metadata.json', emit: event_metadata, optional: true
    path 'sample_metadata.tsv', emit: sample_metadata, optional: true
    script:
    def payload = [options: options, inputs: [gtf_db: gtf_db.toString(), genome: genome.toString(), gencode_protein_fasta: gencode_protein_fasta.toString()], process: task.process, cpus: task.cpus]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py validate
    """
}
