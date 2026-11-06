include { VALIDATE_GENCODE_TRANSLATION } from '../../../modules/local/protegerna/validate_gencode_translation'
include { BUILD_REFERENCE_PEPTIDE_CACHE } from '../../../modules/local/protegerna/build_reference_peptide_cache'
include { CREATE_GENCODE_DB } from '../../../modules/local/protegerna/create_gencode_db'
workflow VALIDATE {
    take:
    options
    cache_options
    runtime
    db
    gtf
    genome
    gencode
    reference
    existing_cache
    main:
    reference_db = db
    db_versions = Channel.empty()
    if (params.gtf) {
        CREATE_GENCODE_DB(runtime, gtf)
        reference_db = CREATE_GENCODE_DB.out.db
        db_versions = CREATE_GENCODE_DB.out.versions
    }
    VALIDATE_GENCODE_TRANSLATION(options, runtime, reference_db, genome, gencode)
    BUILD_REFERENCE_PEPTIDE_CACHE(cache_options, runtime, reference, existing_cache)
    validated_cache = BUILD_REFERENCE_PEPTIDE_CACHE.out.cache.combine(VALIDATE_GENCODE_TRANSLATION.out.summary_json).map { cache, _summary -> cache }
    emit:
    cache = validated_cache
    db = reference_db
    summary = VALIDATE_GENCODE_TRANSLATION.out.summary_json
    versions = VALIDATE_GENCODE_TRANSLATION.out.versions.mix(BUILD_REFERENCE_PEPTIDE_CACHE.out.versions).mix(db_versions)
}
