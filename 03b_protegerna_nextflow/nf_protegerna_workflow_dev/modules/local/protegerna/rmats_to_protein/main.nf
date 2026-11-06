process RMATS_TO_PROTEIN {
    tag 'rmats'
    label 'process_high'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/rmats", mode: params.publish_dir_mode, saveAs: { it == 'versions.yml' ? null : it }
    input:
    val options
    path runtime, stageAs: 'runtime'
    tuple val(rows), path(event_files, arity: '1..*', stageAs: 'inputs/row????/*')
    path gtf_db, stageAs: 'references/annotation.db'
    path genome, stageAs: 'references/genome.fa'
    path reference_proteome, stageAs: 'references/proteome.fa'
    path peptide_cache, stageAs: 'cache/reference.cache'
    output:
    path "${options.out_prot_fa}", emit: fasta
    path "${options.out_consequence_tsv}", emit: consequences
    path "${options.out_event_summary_tsv}", emit: events
    path "${options.out_alt_start_prot_fa}", emit: alternative_start, optional: true
    path "${options.out_exploratory_orf_fa}", emit: exploratory_orf, optional: true
    path "${options.out_junc_fa}", emit: junctions, optional: true
    path 'versions.yml', emit: versions
    path 'task_inputs.json', emit: provenance
    path 'command.json', emit: command
    path '*.run_config.json', emit: run_config, optional: true
    path '*_metadata.json', emit: event_metadata, optional: true
    path 'sample_metadata.tsv', emit: sample_metadata, optional: true
    script:
    def payload = [options: options, inputs: [gtf_db: gtf_db.toString(), genome: genome.toString(), reference_proteome: reference_proteome.toString(), reference_peptide_cache: peptide_cache.toString()], process: task.process, cpus: task.cpus, rows: rows, files: event_files.collect { it.toString() }]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py rmats
    """
}
