process PROTEOGENOMIC_FASTA_QC {
    tag 'qc'
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/qc", mode: params.publish_dir_mode, saveAs: { it == 'versions.yml' ? null : it }
    input:
    val options
    path runtime, stageAs: 'runtime'
    path reference_proteome, stageAs: 'references/proteome.fa'
    path fasta
    path metadata
    output:
    path "${options.outdir}", emit: qc
    path 'versions.yml', emit: versions
    path 'task_inputs.json', emit: provenance
    path 'command.json', emit: command
    path '*.run_config.json', emit: run_config, optional: true
    path '*_metadata.json', emit: event_metadata, optional: true
    path 'sample_metadata.tsv', emit: sample_metadata, optional: true
    script:
    def payload = [options: options, inputs: [reference_proteome: reference_proteome.toString(), fasta: [fasta.toString()], metadata: [metadata.toString()]], process: task.process, cpus: task.cpus]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py qc
    """
}
