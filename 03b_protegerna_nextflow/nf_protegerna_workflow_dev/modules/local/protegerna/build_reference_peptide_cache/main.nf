process BUILD_REFERENCE_PEPTIDE_CACHE {
    tag 'cache'
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/cache", mode: params.publish_dir_mode, saveAs: { it == 'versions.yml' ? null : it }
    input:
    val options
    path runtime, stageAs: 'runtime'
    path reference_proteome, stageAs: 'references/proteome.fa'
    path existing_cache, arity: '0..*', stageAs: 'cache/existing.cache'
    output:
    path 'reference_tryptic_peptides.cache', emit: cache
    path 'versions.yml', emit: versions
    path 'task_inputs.json', emit: provenance
    script:
    def payload = [options: options, inputs: [reference_proteome: reference_proteome.toString()], process: task.process, cpus: task.cpus, existing_cache: existing_cache ? existing_cache[0].toString() : null]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py cache
    """
}
