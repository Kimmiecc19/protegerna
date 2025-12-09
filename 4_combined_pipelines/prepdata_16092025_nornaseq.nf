#!/usr/bin/env nextflow

// Credit: https://github.com/mahesh-panchal/nf-cascade

nextflow.enable.dsl = 2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { NFCORE_RNASPLICE} from './modules/prepdata/rnasplice/' addParams(options: params.nfcore_rnasplice_opts)
include { NFCORE_RNAFUSION} from './modules/prepdata/rnafusion/' addParams(options: params.nfcore_rnafusion_opts)
include { NFCORE_SAREK} from './modules/prepdata/sarek/' addParams(options: params.nfcore_sarek_opts)

include { OUTPUT_ORGANIZER } from './modules/local/output_organizer'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NFCORE MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// include { MODULE } from './modules/nfcore/'


// Parameter validation
// Define a list of valid module names that can be selected by the user

def valid_modules = ['rnasplice', 'rnafusion', 'sarek']

// Check if any modules are specified by the user
if (!params.modules) {
    // If no modules are specified, throw an error with instructions
    error "No modules specified. Please specify at least one of 'rnasplice' or 'rnafusion'."
}
// // Check that at least one of 'rnasplice' or 'rnafusion' is included in the user's selection
if (!params.modules.contains('rnasplice') && !params.modules.contains('rnafusion')) {
    // If 'rnasplice' and 'rnafusion' are not included, throw an error reminding the user they're compulsory
    error "The 'rnasplice' or 'rnafusion' modules are compulsory. Please include at least one of them in your module selection."
}

// This uses the every method to check if all specified modules are valid (i.e., they exist in the valid_modules list above) (https://dzone.com/articles/groovy-gotcha-with-the-every-collection-method and https://www.tutorialspoint.com/groovy/groovy_any_every.html).
if (!params.modules.every { it in valid_modules }) {
    // If any invalid module is specified, throw an error listing the valid options
    error "Invalid module specified. Valid options are: ${valid_modules.join(', ')}"
}

/*
========================================================================================
    RUN MAIN WORKFLOW
========================================================================================
*/

workflow {
    // Input validation and channel creation
    // Check if modules are specified, if not, throw an error
    def modules = params.modules ?: error("No modules specified. Please specify at least one of 'rnasplice', 'rnafusion', and optionally 'sarek'.")
    
    // Channels for samplesheets
    // At least rnasplice or rnafusion samplesheet is required, sarek is optional
    ch_rnasplice_samplesheet = params.rnasplice_samplesheet ? Channel.fromPath(params.rnasplice_samplesheet) : Channel.empty()
    ch_rnafusion_samplesheet = params.rnafusion_samplesheet ? Channel.fromPath(params.rnafusion_samplesheet) : Channel.empty() // TODO: Strip column from rnasplice samplesheet
    ch_sarek_samplesheet = params.sarek_samplesheet ? Channel.fromPath(params.sarek_samplesheet) : Channel.empty()

    // Initialize result channels to store the outputs from each workflow
    ch_rnasplice_results = Channel.empty()
    ch_rnafusion_results = Channel.empty()
    ch_sarek_results = Channel.empty()

    // Run RNASPLICE if selected
    if (modules.contains('rnasplice')) {
        // Check if samplesheet is provided when module is selected
        if (ch_rnasplice_samplesheet.isEmpty()) {
            error("RNASPLICE module selected but no samplesheet provided")
        }
        // Execute RNASPLICE workflow
        NFCORE_RNASPLICE(
            Channel.value('nf-core/rnasplice'),  // Workflow name
            params.rnasplice_params ? file(params.rnasplice_params) : [],  // Optional parameters file
            ch_rnasplice_samplesheet,  // Input samplesheet
            params.rnasplice_config ? file(params.rnasplice_config) : []  // Optional config file
        )
        // Store the results, throw an error if no results are produced
        ch_rnasplice_results = NFCORE_RNASPLICE.out.results.ifEmpty { error("RNASPLICE workflow did not produce any results") }
    }

    // Run RNAFUSION if selected
    if (modules.contains('rnafusion')) {
        // Check if samplesheet is provided when module is selected
        if (ch_rnafusion_samplesheet.isEmpty()) {
            error("RNAFUSION module selected but no samplesheet provided")
        }
        // Execute RNAFUSION workflow
        NFCORE_RNAFUSION(
            Channel.value('nf-core/rnafusion'),  // Workflow name
            params.rnafusion_params ? file(params.rnafusion_params) : [],  // Optional parameters file
            ch_rnafusion_samplesheet,  // Input samplesheet
            params.rnafusion_config ? file(params.rnafusion_config) : []  // Optional config file
        )
        // Store the results, throw an error if no results are produced
        ch_rnafusion_results = NFCORE_RNAFUSION.out.results.ifEmpty { error("RNAFUSION workflow did not produce any results") }
    }

    // Run SAREK if selected
    if (modules.contains('sarek')) {
        // Check if samplesheet is provided when module is selected
        if (ch_sarek_samplesheet.isEmpty()) {
            error("SAREK module selected but no samplesheet provided")
        }
        // Execute SAREK workflow
        NFCORE_SAREK(
            Channel.value('nf-core/sarek'),  // Workflow name
            params.sarek_params ? file(params.sarek_params) : [],  // Optional parameters file
            ch_sarek_samplesheet,  // Input samplesheet
            params.sarek_config ? file(params.sarek_config) : []  // Optional config file
        )
        // Store the results, throw an error if no results are produced
        ch_sarek_results = NFCORE_SAREK.out.results.ifEmpty { error("SAREK workflow did not produce any results") }
    }

    // Organize output
    def organizer_inputs = []

    // Add results from other modules if they were run
    if (modules.contains('rnasplice')) {
        organizer_inputs.add(ch_rnasplice_results)
    }
    if (modules.contains('rnafusion')) {
        organizer_inputs.add(ch_rnafusion_results)
    }
    if (modules.contains('sarek')) {
        organizer_inputs.add(ch_sarek_results)
    }
// TODO: soft links/pseudo directory to link pipeline output to input for the rest vs. hard links

    // Run the output organizer with all collected results and emit a single combined results channel
        ch_combined_results = OUTPUT_ORGANIZER(organizer_inputs).out.combined_results
        // ch_combined_results now contains all results from selected modules
        // ch_combined_results will be used as input for the next pipeline step (createdb.nf)
        // Example usage:
        // CREATE_DB(ch_combined_results)