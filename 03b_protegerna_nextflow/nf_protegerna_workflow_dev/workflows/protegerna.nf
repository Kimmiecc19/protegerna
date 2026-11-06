/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { MULTIQC                } from '../modules/nf-core/multiqc/main'
include { paramsSummaryMap       } from 'plugin/nf-schema'
include { paramsSummaryMultiqc   } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { softwareVersionsToYAML } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText } from '../subworkflows/local/utils_nfcore_protegerna_pipeline'

include { VALIDATE } from '../subworkflows/local/validate'
include { SPLICE } from '../subworkflows/local/splice'
include { FUSIONINSPECTOR_TO_PROTEIN } from '../modules/local/protegerna/fusioninspector_to_protein'
include { MERGE_PROTEOGENOMIC_DATABASE } from '../modules/local/protegerna/merge_proteogenomic_database'
include { PROTEOGENOMIC_FASTA_QC } from '../modules/local/protegerna/proteogenomic_fasta_qc'
include { COLLECT_PROTEOGENOMIC_VERSIONS } from '../modules/local/protegerna/collect_versions'

def publicationDefaults() {
    new groovy.json.JsonSlurper().parse(file("${projectDir}/assets/resolved_publication_defaults.json").toFile())
}

// Publication defaults for one stage, overlaid with the user's params-file/CLI values.
def stageOptions(stage) {
    def defaults = publicationDefaults()[stage]
    def overrides = params[stage] ?: [:]
    if (!(overrides instanceof Map)) error "Parameter '${stage}' must be a map of options, e.g. ${stage}: { <option>: <value> }"
    def unknown = overrides.keySet().findAll { !defaults.containsKey(it) }
    if (unknown) error "Unknown ${stage} option(s): ${unknown.join(', ')}. Valid options are listed in assets/params.publication.yml"
    def options = [:] + defaults + overrides
    if (stage in ['fusion','rmats','suppa','merge']) {
        options.annotation_release = params.annotation_release
        options.organism = params.organism
    }
    options.each { key, value ->
        if (value && (key.startsWith('out_') || key in ['filtered_protein_fasta','filtered_cds_fasta','biological_interpretation_tsv','dia_database_metadata_tsv','digested_peptide_tsv','outdir'])) {
            if (!(value.toString() ==~ /[A-Za-z0-9][A-Za-z0-9._-]*/)) error "${stage}.${key} must be a task-local filename: ${value}"
        }
    }
    return options
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow PROTEGERNA {

    take:
    ch_samplesheet // channel: samplesheet read in from --input
    multiqc_config
    multiqc_logo
    multiqc_methods_description
    outdir

    main:

    def ch_versions = channel.empty()
    def ch_multiqc_files = channel.empty()

    //
    // Collate and save software versions
    //
    def topic_versions = channel.topic("versions")
        .distinct()
        .branch { entry ->
            versions_file: entry instanceof Path
            versions_tuple: true
        }

    def topic_versions_string = topic_versions.versions_tuple
        .map { process, tool, version ->
            [ process[process.lastIndexOf(':')+1..-1], "  ${tool}: ${version}" ]
        }
        .groupTuple(by:0)
        .map { process, tool_versions ->
            tool_versions.unique().sort()
            "${process}:\n${tool_versions.join('\n')}"
        }

    def ch_collated_versions = softwareVersionsToYAML(ch_versions.mix(topic_versions.versions_file))
        .mix(topic_versions_string)
        .collectFile(
            storeDir: "${outdir}/pipeline_info",
            name: 'nf_core_'  +  'protegerna_software_'  + 'mqc_'  + 'versions.yml',
            sort: true,
            newLine: true
        )
    def options = ['validate','fusion','rmats','suppa','merge','qc'].collectEntries { [(it): stageOptions(it)] }
    def info = file("${params.outdir}/pipeline_info")
    info.mkdirs()
    info.resolve('resolved_stage_options.json').text = groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(options)) + '\n'
    def samplesheet_parent = file(params.input, checkIfExists: true).parent
    def runtime = Channel.value(file(params.runtime_source, checkIfExists: true))
    def genome = Channel.value(file(params.genome, checkIfExists: true))
    def db = Channel.value(params.gtf_db ? file(params.gtf_db, checkIfExists: true) : [])
    def gtf = Channel.value(params.gtf ? file(params.gtf, checkIfExists: true) : [])
    def reference = Channel.value(file(params.reference_proteome, checkIfExists: true))
    def gencode = Channel.value(file(params.gencode_protein_fasta, checkIfExists: true))
    def contaminants = Channel.value(params.contaminants ? [file(params.contaminants, checkIfExists: true)] : [])
    def existing_cache = Channel.value(params.reference_peptide_cache ? [file(params.reference_peptide_cache, checkIfExists: true)] : [])
    def sample_metadata = Channel.value(params.sample_metadata ? [file(params.sample_metadata, checkIfExists: true)] : [])    
    rows = ch_samplesheet.splitCsv(header: true, strip: true).map { row ->
        ['sample','tool','event_type','path','batch','condition'].each { key ->
            if (!row.containsKey(key) || !row[key]?.trim()) error "Samplesheet requires non-empty ${key}; use NA for unknown metadata"
        }
        def allowed = [fusion: ['FUSION'], rmats: ['SE','A3SS','A5SS','MXE','RI'], suppa: ['IOE','PSI']]
        if (!allowed.containsKey(row.tool)) error "Unknown samplesheet tool: ${row.tool}"
        if (!(row.event_type in allowed[row.tool])) error "Invalid ${row.tool} event_type: ${row.event_type}"
        ['sample','batch'].each { key ->
            if (!(row[key] ==~ /[A-Za-z0-9][A-Za-z0-9_.-]*/)) error "Invalid samplesheet ${key}: ${row[key]}"
        }
        def inputPath = row.path.startsWith('/') || row.path ==~ /^[A-Za-z]:.*/ || row.path.contains('://') ? row.path : samplesheet_parent.resolve(row.path).toString()
        def inputFile = file(inputPath, checkIfExists: true)
        if (!inputFile.isFile() || inputFile.size() == 0) error "Input must be a non-empty file: ${inputFile}"
        tuple(row, inputFile)
    }.collect(flat: false).ifEmpty { [] }.map { entries ->
        if (!entries) error 'Samplesheet has no inputs'
        def paths = entries.collect { it[1].toString() }
        if (paths.unique(false).size() != paths.size()) error 'Samplesheet contains duplicate input files'
        def samples = entries.findAll { it[0].tool == 'fusion' }.collect { it[0].sample }
        if (samples.unique(false).size() != samples.size()) error 'Fusion sample identifiers must be unique across batches'
        def suppa = entries.findAll { it[0].tool == 'suppa' }
        if (suppa && !suppa.any { it[0].event_type == 'IOE' }) error 'SUPPA requires an IOE row'
        if (suppa && params.suppa_require_psi && !suppa.any { it[0].event_type == 'PSI' }) error 'SUPPA requires PSI evidence; use --suppa_require_psi false only for an explicitly unfiltered run'
        entries
    }
    fusion_inputs = rows.map { it.findAll { pair -> pair[0].tool == 'fusion' } }.filter { it }.map { tuple(it.collect { pair -> pair[0] }, it.collect { pair -> pair[1] }) }
    rmats_inputs = rows.map { it.findAll { pair -> pair[0].tool == 'rmats' } }.filter { it }.map { tuple(it.collect { pair -> pair[0] }, it.collect { pair -> pair[1] }) }
    suppa_inputs = rows.map { it.findAll { pair -> pair[0].tool == 'suppa' } }.filter { it }.map { tuple(it.collect { pair -> pair[0] }, it.collect { pair -> pair[1] }) }
    VALIDATE(options.validate, [min_peptide_length: params.min_peptide_length, max_peptide_length: params.max_peptide_length, max_missed_cleavages: params.max_missed_cleavages], runtime, db, gtf, genome, gencode, reference, existing_cache)
    FUSIONINSPECTOR_TO_PROTEIN(options.fusion, runtime, fusion_inputs, VALIDATE.out.db, genome, reference, VALIDATE.out.cache, sample_metadata)
    SPLICE(options.rmats, options.suppa, runtime, rmats_inputs, suppa_inputs, VALIDATE.out.db, genome, reference, VALIDATE.out.cache, sample_metadata)
    producer_fastas = FUSIONINSPECTOR_TO_PROTEIN.out.fasta.mix(SPLICE.out.fastas)
    if (options.merge.include_rescue_tiers) producer_fastas = producer_fastas.mix(SPLICE.out.rescue)
    // Sorted by name so merge sees inputs in a fixed order, independent of task completion order.
    fastas = producer_fastas.collect(sort: { it.name }).ifEmpty { [] }.map { files ->
        if (!files) error 'No reconstruction inputs were selected'
        files
    }
    MERGE_PROTEOGENOMIC_DATABASE(options.merge, runtime, reference, fastas, contaminants, VALIDATE.out.summary)
    PROTEOGENOMIC_FASTA_QC(options.qc, runtime, reference, MERGE_PROTEOGENOMIC_DATABASE.out.fasta, MERGE_PROTEOGENOMIC_DATABASE.out.metadata)
    all_versions = VALIDATE.out.versions.mix(FUSIONINSPECTOR_TO_PROTEIN.out.versions, SPLICE.out.versions, MERGE_PROTEOGENOMIC_DATABASE.out.versions, PROTEOGENOMIC_FASTA_QC.out.versions)
    COLLECT_PROTEOGENOMIC_VERSIONS(runtime, all_versions.collect())

    //
    // MODULE: MultiQC
    //
    ch_multiqc_files = ch_multiqc_files.mix(ch_collated_versions)
    def ch_summary_params = paramsSummaryMap(workflow, parameters_schema: "nextflow_schema.json")
    def ch_workflow_summary = channel.value(paramsSummaryMultiqc(ch_summary_params))
    ch_multiqc_files = ch_multiqc_files.mix(ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    def ch_multiqc_custom_methods_description = multiqc_methods_description
        ? file(multiqc_methods_description, checkIfExists: true)
        : file("${projectDir}/assets/methods_description_template.yml", checkIfExists: true)
    def ch_methods_description = channel.value(methodsDescriptionText(ch_multiqc_custom_methods_description))
    ch_multiqc_files = ch_multiqc_files.mix(ch_methods_description.collectFile(name: 'methods_description_mqc.yaml', sort: true))
    MULTIQC(
        ch_multiqc_files.flatten().collect().map { files ->
            [
                [id: 'protegerna'],
                files,
                multiqc_config
                    ? file(multiqc_config, checkIfExists: true)
                    : file("${projectDir}/assets/multiqc_config.yml", checkIfExists: true),
                multiqc_logo ? file(multiqc_logo, checkIfExists: true) : [],
                [],
                [],
            ]
        }
    )
    emit:
    fasta = MERGE_PROTEOGENOMIC_DATABASE.out.fasta
    metadata = MERGE_PROTEOGENOMIC_DATABASE.out.metadata
    qc = PROTEOGENOMIC_FASTA_QC.out.qc
    versions = COLLECT_PROTEOGENOMIC_VERSIONS.out.yml
    multiqc_report = MULTIQC.out.report.map { _meta, report -> [report] }.toList() // channel: /path/to/multiqc_report.html
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
