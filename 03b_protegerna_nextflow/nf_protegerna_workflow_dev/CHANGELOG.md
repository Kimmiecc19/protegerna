# nf-core/protegerna: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.0.0dev - [date]

Initial release of nf-core/protegerna, created with the [nf-core](https://nf-co.re/) template.

### `Changed`

- Profiles reduced to `publication` (params-file driven production run) and `test` (synthetic smoke test). The `apptainer` profile is now the base configuration and `reconstruction_profile` was removed; the pipeline always uses the publication policy.
- Stage defaults are defined once, in `assets/resolved_publication_defaults.json`; `nextflow.config` no longer duplicates them. Params files may override any subset of options; unknown options stop the run.
- Bundled reconstruction code updated to `code_proteogenomic_database_v6` (fork-safe genome/annotation handles in multi-worker fusion reconstruction). The former integration patches are now part of v6 itself, so the bundle is an unmodified copy, limited to the 50 modules the pipeline imports.
- Every process runs `nextflow_adapter.py <stage>` directly; the nine per-module `templates/run.py` files were removed. The single-module `FUSION`, `MERGE` and `QC` subworkflows were inlined into `workflows/protegerna.nf`. Unused `benchmark_variant_reconstruction` and `release_report` module stubs were removed.
- Producer FASTAs reach merge in a fixed (name-sorted) order, so merge tables no longer depend on task completion order.
- Removed nf-core template leftovers (`tower.yml`, MultiQC config, methods template, FASTQ `schema_input.json`, `ro-crate-metadata.json`), `linting_todo`, `.history/` and retired generators in `testing/`. `test-datasets/` and `*.sif` are git-ignored.

- Removed the `fusion_transcript_model_cache` parameter and the matching fusion module input/output and adapter code: the fusion program accepted `--transcript_model_cache` but never read or wrote the cache, so the parameter had no effect.

- Bundled reconstruction code now comes from `code_proteogenomic_database_v7` (the build script's default source): includes the rMATS `--require_unique_event_peptide` fix, the unresolved-reading-frame audit rows and the review fixes. Reconstruction outputs on the test data are unchanged.

### `Added`

- `assets/params.publication.yml`: complete parameter template generated from the defaults.
- `pipeline_info/resolved_stage_options.json`: options actually used by each stage.
- `scripts/build_runtime.py` (replaces `testing/build_runtime_v5.py`) also regenerates the params template.

### `Fixed`

### `Dependencies`

### `Deprecated`
