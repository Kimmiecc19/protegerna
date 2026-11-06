process COLLECT_PROTEOGENOMIC_VERSIONS {
    container "${params.proteogenomic_container}"
    conda "${moduleDir}/environment.yml"
    publishDir "${params.outdir}/pipeline_info", mode: params.publish_dir_mode
    input:
    path runtime, stageAs: 'runtime'
    path versions, stageAs: 'versions????/*'
    output:
    path 'software_versions.yml', emit: yml
    script:
    def payload = [:]
    """
    printf '%s' '${groovy.json.JsonOutput.toJson(payload).getBytes('UTF-8').encodeBase64()}' | python3 -B runtime/nextflow_adapter.py versions
    """
}
