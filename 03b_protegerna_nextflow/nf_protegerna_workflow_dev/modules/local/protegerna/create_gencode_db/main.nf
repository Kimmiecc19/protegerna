process CREATE_GENCODE_DB {
    label 'process_medium'
    conda "${moduleDir}/environment.yml"
    container "${params.proteogenomic_container}"
    publishDir "${params.outdir}/validate", mode: params.publish_dir_mode, pattern: '*.db'
    input:
    path runtime, stageAs: 'runtime'
    path gtf, stageAs: 'annotation/*'
    output:
    path 'gencode.gtf.db', emit: db
    path 'versions.yml', emit: versions
    script:
    def payload = [options: [:], inputs: [gtf: gtf.toString()], process: task.process]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py gtfdb
    """
}
