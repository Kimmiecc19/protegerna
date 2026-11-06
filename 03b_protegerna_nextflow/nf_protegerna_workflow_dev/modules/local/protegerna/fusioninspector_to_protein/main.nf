process FUSIONINSPECTOR_TO_PROTEIN {
    tag 'fusion'
    label 'process_high'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/fusion", mode: params.publish_dir_mode, saveAs: { it == 'versions.yml' ? null : it }
    input:
    val options
    path runtime, stageAs: 'runtime'
    tuple val(rows), path(event_files, arity: '1..*', stageAs: 'inputs/row????/*')
    path gtf_db, stageAs: 'references/annotation.db'
    path genome, stageAs: 'references/genome.fa'
    path reference_proteome, stageAs: 'references/proteome.fa'
    path peptide_cache, stageAs: 'cache/reference.cache'
    path sample_metadata, arity: '0..*', stageAs: 'metadata/*'
    output:
    path "${options.filtered_protein_fasta}", emit: fasta
    path "${options.filtered_cds_fasta}", emit: cds
    path "${options.biological_interpretation_tsv}", emit: biological
    path "${options.dia_database_metadata_tsv}", emit: metadata
    path "${options.out_sequence_sample_tsv}", emit: sequence_samples
    path "${options.digested_peptide_tsv}", emit: peptides, optional: true
    path 'versions.yml', emit: versions
    path 'task_inputs.json', emit: provenance
    path 'command.json', emit: command
    path '*.run_config.json', emit: run_config, optional: true
    path '*_metadata.json', emit: event_metadata, optional: true
    path 'sample_metadata.tsv', emit: sample_metadata, optional: true
    script:
    def payload = [options: options, inputs: [gtf_db: gtf_db.toString(), genome: genome.toString(), reference_proteome: reference_proteome.toString(), reference_peptide_cache: peptide_cache.toString()], process: task.process, cpus: task.cpus, rows: rows, files: event_files.collect { it.toString() }]
    payload.sample_metadata = sample_metadata ? sample_metadata[0].toString() : null
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py fusion
    """
}
