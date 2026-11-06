include { RMATS_TO_PROTEIN } from '../../../modules/local/protegerna/rmats_to_protein'
include { SUPPA_TO_PROTEIN } from '../../../modules/local/protegerna/suppa_to_protein'
workflow SPLICE {
    take:
    rmats_options
    suppa_options
    runtime
    rmats_events
    suppa_events
    db
    genome
    reference
    cache
    sample_metadata
    main:
    RMATS_TO_PROTEIN(rmats_options, runtime, rmats_events, db, genome, reference, cache)
    SUPPA_TO_PROTEIN(suppa_options, runtime, suppa_events, db, genome, reference, cache, sample_metadata)
    emit:
    fastas = RMATS_TO_PROTEIN.out.fasta.mix(SUPPA_TO_PROTEIN.out.fasta)
    rescue = RMATS_TO_PROTEIN.out.alternative_start.mix(RMATS_TO_PROTEIN.out.exploratory_orf, SUPPA_TO_PROTEIN.out.alternative_start, SUPPA_TO_PROTEIN.out.exploratory_orf)
    versions = RMATS_TO_PROTEIN.out.versions.mix(SUPPA_TO_PROTEIN.out.versions)
}
