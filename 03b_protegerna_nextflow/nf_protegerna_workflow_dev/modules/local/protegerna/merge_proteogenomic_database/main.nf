process MERGE_PROTEOGENOMIC_DATABASE {
    tag 'merge'
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/merge", mode: params.publish_dir_mode, saveAs: { it == 'versions.yml' ? null : it }
    input:
    val options
    path runtime, stageAs: 'runtime'
    path reference_proteome, stageAs: 'references/proteome.fa'
    path variant_fastas, arity: '1..*', stageAs: 'variants/producer????/*'
    path contaminants, arity: '0..*', stageAs: 'references/contaminants/*'
    path concordance
    output:
    path "${options.out_fasta}", emit: fasta
    path "${options.out_metadata}", emit: metadata
    path "${options.out_mapping}", emit: mapping
    path "${options.out_peptide_evidence}", emit: peptide_evidence
    path "${options.out_biological_interpretation}", emit: biological
    path "${options.out_summary_tsv}", emit: summary_tsv
    path "${options.out_summary_json}", emit: summary_json
    path 'versions.yml', emit: versions
    path 'task_inputs.json', emit: provenance
    path 'command.json', emit: command
    path '*.run_config.json', emit: run_config, optional: true
    path '*_metadata.json', emit: event_metadata, optional: true
    path 'sample_metadata.tsv', emit: sample_metadata, optional: true
    script:
    def payload = [options: options, inputs: [inputs: variant_fastas.collect { it.toString() }, reference_fasta: [reference_proteome.toString()], contaminants_fasta: contaminants.collect { it.toString() }, gencode_concordance_summary: concordance.toString()], process: task.process, cpus: task.cpus]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py merge
    """
}
