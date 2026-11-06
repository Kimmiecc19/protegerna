# Changelog

## Unreleased

Workflow-runner fixes (2026-10-13).

- FIX steps no longer depend on the working directory: each step process gets
  this
  code tree first on `PYTHONPATH`, so `python -m <step>` works without
installing
  the package or running from the code folder.
- FIX a configured `out_junc_fa` without `short_junction_peptides` (rMATS/SUPPA)
  is
  no longer an expected output, so such a successful step is not reported as
failed.
- FIX fusion: zero proteins passing the policy is a valid (empty) result and
  exits 0
  with a warning, instead of failing the workflow and quarantining the outputs.
- FIX steps always run in pipeline order (stage 1 -> 6), whatever order
  `--stage` or
  `--step` options are given in; `benchmark` (stage 5) now runs after `merge`.
- NEW configuration values are type-checked against each enabled step's options
  when
  the config is loaded (booleans, numbers, choices, single value vs list, empty
  required lists), instead of failing when the step starts.
- FIX a failed `validate` (release gate) or `qc` (`--strict_quantms`) keeps its
  reports under their normal names for inspection; the step is still not marked
  complete, so resume re-runs it.
- NEW output-directory lock (`.proteogenomic_state/workflow.lock`): a second run
  on
  the same output directory is refused. A lock left by a dead process on the
same
  POSIX host is recovered automatically; otherwise delete it by hand.

## PSI validation and checksum-cache hardening (2026-10-13)

- FIX SUPPA PSI values are validated instead of silently coerced: a cell that is
  not a number or a declared missing token (empty, nan, NA, N/A, NULL, None,
#N/A,
  <NA>; any case, surrounding spaces allowed) is an error, as are infinities and
  values outside 0-1. The error names the file, event, sample and value.
Previously
  a malformed cell became "missing" and could change whether an event passed the
  PSI filter. Valid matrices load as before (identical results, same speed).
- PERF duplicate PSI sample-header check uses a counter (linear, not quadratic
  in
  the number of samples).
- FIX checksum cache: digests are memoised per file identity (device, inode,
  size,
  mtime and ctime), and only when the file did not change while being read, so a
  same-size, same-mtime replacement is re-hashed. Workflow output checksums are
  never taken from the cache, and cached digests of a step's outputs are dropped
  after the step runs.
- FIX `provenance.py` type annotations (the CI mypy check failed on yesterday's
  `as_path_list`/`open_text` additions).

## Release-integrity fixes (2026-10-13 review)

- FIX (high) workflow resume after a failed rerun: the success record of a step
  is
  deleted before the step runs and rewritten atomically only after it succeeds
and
  all expected outputs exist. The record now also stores SHA-256 checksums of
those
  outputs, and `--resume` skips a step only if the outputs are byte-identical to
the
  recorded ones. Outputs left by a failed or interrupted run are renamed
  `*.incomplete`. State files from earlier versions are not trusted (the step
re-runs).
- FIX (high) SUPPA PSI duplicate samples: duplicate sample names are now checked
  in
  the raw PSI header; pandas had renamed `sampleA, sampleA` to `sampleA,
sampleA.1`,
  so one sample counted twice towards `--min_psi_samples`.
- FIX (medium) merge resume fingerprint now includes each input FASTA's
  `.run_config.json` (or its absence), which merge reads for reference binding.
- FIX (medium) release binding: a producer manifest that does not record both
  `gtf_db` and `genome`, with checksums matching the GENCODE validation, now
fails
  instead of being reported as verified.
- FIX producers (rMATS, SUPPA, fusion) remove any old `<FASTA>.run_config.json`
  at
  start and publish the new one only after their outputs are written, so a
failed
  run never leaves a manifest vouching for partial output. The recorded
arguments
  are a startup snapshot (run-time objects are no longer serialised).
- NEW merge `--require_producer_manifests`: fail instead of warning when an
  input
  FASTA has no producer manifest. Enabled in `workflow.publication.frozen.toml`.

## Pre-release configuration fixes (2026-10-12)

- FIX mitochondrial sequence lookup: chromosome names now resolve
  chrM/chrMT/M/MT
  as well as chr1/1, so GENCODE `chrM` transcripts are found in an Ensembl-style
  genome FASTA (`MT`). Previously they were unreconstructable and failed the
  zero-mismatch GENCODE validation gate.
- FIX peptide uniqueness reference: `--reference_proteome` (fusion, rMATS,
  SUPPA,
  QC) accepts several FASTAs, plain or `.gz`, e.g. UniProt canonical plus the
  `_additional` isoform FASTA, so known isoforms no longer count as novel. The
  fusion "identical to reference" check uses all files. The peptide-cache key
  covers every file, so an existing cache is rebuilt once.
- FIX rMATS `--include_failed_filter_proteins` now does what its help says: a
  reconstructable, non-canonical protein that fails DIA policy rules
(consequence
  filters, retained-intron rules, unique-peptide requirements) stays in the
  primary FASTA, with the failed rules in `fasta_exclusion_reasons` and
  `passed_dia_filters = false`. Previously only the opposite-isoform peptide
check
  was bypassed. Proteins with no ORF or identical to the canonical protein are
still
  excluded.
- CONFIG `workflow.publication.frozen.toml`: rMATS now uses the same database
  rules
  as SUPPA (`quantms_conservative`, `exclude_incomplete_cds` and
  `exclude_nmd_from_dia` set to true), while keeping
`include_failed_filter_proteins
  = true`; SUPPA reads one `events.ioe`; `reference_proteome` lists the
canonical
  and `_additional` UniProt FASTAs (common and QC sections).

## Follow-up to the code-quality review (2026-10-12)

- FEATURE SUPPA rescue: `--allow_alt_start` and `--allow_longest_orf` now work
  in
  SUPPA with the rMATS rules, from one shared module
(`proteogenomic/splice_rescue.py`):
  the same `--alternative_start_codons`, `--min_alt_start_kozak_strength` (now
  accepted by SUPPA too) and `--min_alt_orf_aa`, `exploratory` tier, separate
  alternative-start / exploratory-ORF FASTAs, the same bypass of primary DIA
filters
  (unless identical to the opposite isoform), and the unique-peptide requirement
  applied to primary products only. Because SUPPA translates complete annotated
  transcripts, an alternative start is used when the transcript has no annotated
  start codon (`cds_start_NF`) or its annotated CDS yields no protein;
longest-ORF
  rescue applies only when nothing else translates. With the flags off, SUPPA
  products are unchanged; the consequence TSV gains the rMATS `alt_start*`
columns.
  Longest-ORF rescue (both callers) now uses the mitochondrial code on chrM/MT.
- FIX fusion breakpoints outside the transcript span: the resolver snapped them
  to
  the nearest transcript boundary itself, so the low-confidence fallback in
  `create_fusion_cds` was unreachable and a snap of <= 25 nt was not flagged.
These
  products are now always `low_confidence` (excluded from the DIA FASTA, kept in
the
  biological TSV). `resolve_breakpoint_on_exon_chain` keeps snapping by default
  (`snap_outside=False` leaves such breakpoints to the caller).
- FIX fusion `pair_token` / FASTA `event_id` is now
  `<sample>:<event>_<donor>_<acceptor>`;
  the old `<event>_<donor>_<acceptor>` restarted at 0 in every sample, so
unrelated
  fusions in different samples shared an event_id.

## Code-quality review (2026-10-12)

Code-quality review (2026-10-12, fourth pass). Verified with the full test suite
(148 tests), the rMATS differential harness (4 seeds x 5 option sets) and new
end-to-end old-vs-new comparisons for SUPPA, fusion, merge, QC and GENCODE
validation on synthetic inputs. Unless listed under FIX, outputs are
byte-identical.

- FIX confidence rubric: producers write `frame_status = "INFRAME"` but the
  rubric
  compared against lowercase `"inframe"`, so the +20 `frame_preserved` credit
was
  never awarded. On the synthetic data ~45% of rMATS rows change score and many
  move from Moderate to High confidence.
- FIX rMATS `consequence_class`/`ri_orf_preserved` were derived from a private
  frame
  calculation while `frame_status`, `frameshift`, stop and NMD columns came from
the
  shared caller-neutral calculation, so a row could report
`frame_status=INFRAME`
  with class `...;frameshift` (122 rows on the synthetic data, all start-lost).
Both
  are now derived from the reported values; SUPPA uses the same pattern (no
change).
- FIX shared consequence: an isoform with no altered CDS now reports
  `frame_status=NA` and `cds_delta_nt=NA` instead of a vacuous `INFRAME`.
- FIX rMATS junction peptides: rMATS and SUPPA now share one generator (the
  SUPPA
  implementation). The rMATS copy emitted stop-truncated "junction peptides" of
  1-4 residues; peptides shorter than `2 x --junction_min_flank` are now dropped
and
  headers gain `window_nt`/`coords`. Junction peptides of proteins removed by
the
  final opposite-isoform peptide check are no longer written.
- FIX rMATS A3SS/A5SS: the short-exon coordinates no longer fall back to the
  `flankingES/flankingEE` (different exon) columns.
- FIX fusion determinism: with `--workers > 1` results were collected with
  `imap_unordered`, and rows were only sorted when
`--biological_interpretation_tsv`
  was requested; FASTA record IDs (which hash the row index) therefore depended
on
  worker timing and on an optional output. Rows are now always in sample order
and
  sorted the same way (identical to the previous output whenever the TSV was
set).
- FIX QC: peptide eligibility was keyed by (label, ordinal); files sharing a
  label
  overwrote each other's counts. Rows are now aligned by position.
- FIX workflow resume: the SUPPA PSI summary is only expected when PSI files are
  configured (without PSI the step was always re-run).
- FIX Windows portability: gzip FASTA input is read as UTF-8 and the junction
  FASTA
  is written with `\n` line endings like every other output.
- FIX merge: concordance/release-gate failures (`RuntimeError`) are reported as
  a
  clean error instead of a traceback; missing typing imports in merge/QC
modules.
- FIX `validate_gencode_translation`: `translation_table` uses the same
  mitochondrial rule as translation (also covers `chrMT`).
- PERF GTF loading: exon/CDS/start/stop/Selenocysteine children are fetched with
  one
  SQL query instead of up to five queries per transcript (splice and fusion
loaders;
  ~2x faster on a 2,500-transcript test DB, identical models).
- PERF checksums: file SHA-256s are memoised per path/size/mtime, so the genome
  and
  annotation DB are hashed once per process instead of once per step; a plain
  `--dry-run` hashes nothing; the reference proteome is only hashed when a
peptide
  cache is used.
- PERF rMATS: one consequence classification per isoform (was two); canonical
  CDS
  reads go through the sequence cache; transcript chains are no longer rebuilt
only
  to populate the unused `SpliceProteinResult.candidates`.
- PERF SUPPA PSI loading iterates a float matrix instead of
  `DataFrame.iterrows()`;
  merge streams FASTA, metadata and mapping rows instead of holding them in
memory.
- CLEANUP removed dead/duplicate code: the unused `candidates` field and
  `SpliceCandidate`, `compute_frame_at_genomic_pos`, a duplicate
  `summarize_junction_codon_state`, pass-through wrappers in fusion coordinates
and
  merge models, unused workflow table aliases, empty section banners, a
duplicated
  serial/parallel aggregation path in fusion orchestration, the never-used
non-pyfaidx
  genome fallback, and stale docstring examples with personal paths. Shared
helpers
  replace duplicated hashing, glob expansion and confidence selection.

## Previous unreleased changes

- PERF final peptide evidence (merge): peptide ownership is tracked as a single
  owner
  index per peptide instead of sets of SHA-256 strings; fragment-ion uniqueness
is
  computed exactly from neighbouring sequences in sorted order instead of
  materialising every b/y prefix/suffix string (O(L^2) per peptide); proteins
are
  re-digested in a second pass instead of holding all digests; rows are streamed
to
  the TSV. On a synthetic ~6,000-protein / 848,000-row database peak memory for
this
  step fell from 1.6 GB to 65 MB with slightly lower runtime. All merge outputs
are
  byte-identical to the previous implementation (randomised and end-to-end
checks).
  `final_database_peptide_rows` still returns a list for existing callers.

- REFACTOR workflow runner: the six parallel per-step tables in
  `proteogenomic_workflow.py` (`STEP_MODULES`, `PARSERS`, `STEP_COMMON`,
`INPUT_KEYS`,
  `OUTPUT_KEYS`, `OUTPUT_DEFAULTS`) and the step-specific branches for
rescue-tier
  names and fusion/QC outputs are replaced by one `StepSpec` per step in
`STEPS`. The
  old names remain as read-only views. Each CLI parser is now built once per
run. A
  test checks that every option named in a spec is accepted by that step's
parser.
  Commands, resolved configuration, `explain` output, expected outputs and
resume
  manifests are byte-identical to before for both shipped configurations.

Correctness fixes from the third review (2026-10-12). Reconstruction algorithms
are
unchanged; these change sample identity, evidence gating, resume and release
checks.

- FIX fusion sample identity: `-T`/`-N`/`tumor`/`normal` suffixes are no longer
  stripped, so tumour and normal files stay separate samples. One shared suffix
  grammar (`.fusioninspector.fusions[.abridged][.filtered].tsv`) drives both
  discovery and sample naming, so `.filtered` files map to the right sample.
  Sample-metadata `sample_id` values must now match the full file sample ID.
- FIX SUPPA PSI fails closed: an unmatched `--psi_files` pattern, a missing,
  unreadable or empty matrix, or a matrix with no samples is an error. `None`
now
  only means PSI filtering was deliberately not requested.
- FIX PSI support counts distinct samples: values are pooled per event and per
  canonical sample ID; identical duplicates count once, conflicting ones are an
error.
- FIX resume and producer manifests expand glob patterns and hash every matched
  file, so changed, added or removed inputs invalidate resume.
- FIX resume checks outputs written under parser defaults (for example the merge
  metadata, mapping and peptide tables when only `out_fasta` is configured).
- FIX resume fingerprint (`pgdb-workflow-run-v2`) includes a digest of the
  step's
  Python source and its effective parser defaults. Existing state files will not
  match once, so the first `--resume` after upgrading reruns every step.
- FIX release binding: `validate_gencode_translation.py` takes a required
  `--annotation_release` and records it plus SHA-256 checksums of the GTF
database,
  genome and GENCODE protein FASTA. The merge rejects a summary for another
release
  or without this identity, and checks producer `<fasta>.run_config.json`
manifests
  for the same release and byte-identical `gtf_db`/`genome`. Rerun validation
once.
- FIX `--dry-run` no longer creates the output directory.
- `explain` also lists ordinary parser defaults.
- Merge aggregates records as they are read (connects the existing
  `record_sink`)
  instead of first building a full record list; output is unchanged.
- Removed empty section banners in `merge_proteogenomic_database.py`; documented
  `PipelineConfig` as a shallow snapshot.

### Cross-platform and runner fixes (2026-10-12, second review)

- FIX byte-reproducibility on Windows: every FASTA, TSV and JSON artifact writer
  now
  writes LF line endings explicitly (`lineterminator="\n"` for pandas/csv,
  `newline="\n"` for text files). Previously Windows produced CRLF and failed
the
  golden release tests. `release_report.py` TSVs switch from csv's default CRLF
to LF.
- FIX `--step`: an explicitly requested step is now filtered by `enabled`
  exactly like
  `--stage`; a missing or disabled section is skipped with a warning instead of
run.
- FIX test environment: `pytest` and `hypothesis` are declared (`.[test]` extra
  and
  `environment.yml`).
- FIX test fragility: golden tests resolve fixtures from the test file location,
  so
  discovery works from any working directory.
- Tidy: unused unpacked locals in `rmatstoprotein.py` are underscore-prefixed.

### Earlier review fixes

Review fixes (2026-10-12). None of these change reconstruction outputs; they
affect
installation, CI and the TOML runner (`proteogenomic_workflow.py`) only.

- FIX packaging: `pyproject.toml` pointed `package-dir` at a non-existent
  `code/`
  directory, so `pip install .` failed. The source root is now the package root,
  `benchmark_variant_reconstruction` (needed by the workflow runner, which
imports every
  step parser) and `summarize_fusion_concordance` are distributed, and
  `requires-python` is `>=3.11` to match `environment.yml` and the pipeline
container
  (Python 3.11.13); it previously required 3.12 only. Verified by a clean
install used
  from outside the source tree. A packaging test now guards the layout.
- FIX CI and README: removed the stale `code/` paths; CI uses Python 3.11. A
  too-narrow
  type hint in `splice_reconstruction_core._interval_intersection_length` (CDS
  intervals carry a phase field) made the CI type-check fail; the hint now
matches the data.
- FIX resume: the rMATS `event_metadata` file is part of the input checksum, so
  editing
  it re-runs rMATS. Resume now checks the files a step must have written: every
QC
  report (plus conditional ones) rather than the QC directory, and fusion's
  sequence-sample and (when digesting) peptide TSVs.
- FIX section selection: a present but empty TOML section now runs, as
  documented
  ("runs when its section exists and `enabled` is not false").
- Removed `SpliceProteinResult.merge_into` (broken import, no callers) and
  unused
  definitions: `translate_canonical_protein`, `confidence_rank_value`, `Strand`,
  `ConsequenceRecord`, `OutputBundle`, `CDSSegmentModel`,
  `exon_junction_positions_from_cds_segments`,
`digest_tryptic_peptides_with_positions`.
- Fusion `--filtered_protein_fasta`/`--filtered_cds_fasta` help and the README
  now say
  what the code does: every candidate passing the DIA policy is written, without
  deduplication (merge collapses identical sequences).

- FIX: removed the fusion option `--transcript_model_cache`. It was accepted
  (and set
  by the Nextflow pipeline and the frozen TOML) but no code read or wrote the
cache, so
  it had no effect. The line is commented out in
`workflow.publication.frozen.toml`.
- FIX: rMATS isoforms whose reading frame cannot be resolved now get an audit
  row
  (`region_class` and reason `unresolved_reading_frame`) instead of disappearing
from
  `rmats.consequences.tsv`. They never reached a FASTA, so FASTAs are unchanged.
- FIX: the confidence rubric (`biological_evidence.py`) caps alternative-start
  and
  alternative-ORF products by `translation_strategy`; it previously matched tier
names
  that rMATS never writes ("exploratory" is the rMATS rescue tier). Only affects
runs
  with rescue tiers enabled; not the publication policy.
- FIX: regenerated the producer golden fixtures; they predated the
  `junction_aa`,
  `passed_dia_filters` and `fasta_exclusion_reasons` header fields, which is why
  `test_producer_equivalence` failed. The test suite now passes in full.
- Removed dead code: an unreachable schema check in `build_ranking_record`
  (covered by
  `test_fusiontoprotein_refactor`), six functions with no callers
  (`map_genomic_to_transcript_offset`, `rank_filtered_isoform_row`,
  `add_breakpoint_fields`, `sequence_aggregate_sink`,
`FailureLedger.assert_release_safe`,
  `pgdb_header` `serialize`) and unused imports. Names other code imports from
the
  compatibility facades are kept and marked `# noqa: F401`.
- Removed `fusion_policy_filter.py`: fusion already applies the DIA policy to
  its FASTA
  (verified on the v5 run: all 4,211 `fusion.primary.fasta` proteins have a
  `dia_fasta_include = True` row).

- Split `rmatstoprotein._evaluate_rmats_variant_projections` (previously one
  315-line
  loop) into seven named steps: `_base_audit_row`, `_variant_cds`,
  `_resolve_frame_and_trim`, `_annotated_start_offset`, `_translate_variant`,
  `_fasta_decision` (the inclusion/tier policy) and `_record_variant`. Behaviour
is
  unchanged: `tests/differential/compare_rmats.py` reproduces every rMATS output
  byte-for-byte against the unsplit code (5 synthetic annotations x 5 option
sets,
  SE/A3SS/A5SS/MXE/RI). New unit tests: `tests/test_rmats_variant_steps.py`.
- FIX (changes rMATS output): `--require_unique_event_peptide` now removes rMATS
  proteins
  that have no tryptic peptide unique against the reference proteome. The
per-isoform
  check compared the output tier with "primary", but `choose_output_tier`
returns
  "primary_dia", so the check never ran; only the separate opposite-isoform
check applied,
  and with `include_failed_filter_proteins` that one only records a reason.
SUPPA always
  applied both checks. Impact on the v5 publication run
  (`results_pgdb_publication_rerun_v5`): 1,514 of 18,809 distinct rMATS primary
proteins
  lacked a reference-unique peptide; 637 were identical to a reference protein
(merged
  into the reference entry), 854 remained as separate `source=rmats` entries
(1.1% of
  80,657 final entries) and 23 were removed later by merge. These proteins add
no
  peptide absent from the reference proteome, so they cannot be identified on
their own
  evidence and only add protein-inference ambiguity. Excluded rows stay in the
  consequence table with reason `no_reference_unique_tryptic_peptide`.
Regression test:
  `test_require_unique_event_peptide_excludes_primary_without_reference_unique_peptide`.

- Remove named workflow profiles (`workflow_profiles.py`, `--profile`). The
  publication policy is now the program default (`quantms_conservative` for
  fusion/rMATS/SUPPA, `rmats_conservative_event_filter`); producer outputs are
  unchanged. Every boolean option accepts `--option`/`--no-option`, so explicit
  `false` settings are honoured. Rescue-tier FASTA names are derived whenever
  `allow_alt_start`/`allow_longest_orf` is enabled.
- rMATS accepts `--event_metadata` (JSON keyed by event-file path) so batch,
  comparison and condition can be supplied explicitly, as the Nextflow pipeline
does.

- Move all internal implementation modules into the `proteogenomic` package and
  move tests/fixtures into `tests`, leaving only eight executable entry points
  at the source root.
- Consolidate audit codes with failure accounting, release gates with producer
  header contracts, fusion FASTA serialization with fusion reporting, and
  producer fixture generation with its owning golden test.
- Add installed console commands for every production workflow step.

- Add a configuration-driven `proteogenomic-workflow` command and standard,
  conservative, and exploratory profiles while preserving advanced CLIs.
- Centralize the shared rMATS/SUPPA CLI policy and GENCODE transcript-model
  loader so CDS phase, completeness, and special-feature handling cannot drift.
- Separate rMATS coordinate/file parsing and statistical, retained-intron, and
  peptide evidence into `rmats_parsing` and `rmats_evidence`.
- Separate SUPPA event-coordinate parsing and PSI evidence into `suppa_parsing`
  and `suppa_psi` while preserving producer compatibility exports.
- Split merge responsibilities into domain models, FASTA parsing, exact-sequence
  aggregation, peptide evidence, and reporting modules.
- Extract fusion domain models, transcript selection/model construction, and
  strand-aware coordinate/breakpoint mapping into dedicated modules.
- Separate FASTA QC models, calculations, I/O, diagnostic reporting, CLI, and
  application orchestration, with byte-exact golden output fixtures.
- Clarify that the merged search database includes the canonical reference plus
  cRAP contaminants only; AnswerALS iRT standards are not included.
- Flag GENCODE `cds_start_NF` and `cds_end_NF` transcripts and exclude their
  products from primary DIA FASTAs by default while retaining auditable
  metadata.
- Standardize SUPPA and rMATS consequence TSV schemas.
- Record resolved command-line configuration beside generated FASTAs.
- Make fusion multiprocessing use worker-local genome and SQLite handles under
  the portable `spawn` context.
- Expose `--max_transcripts_per_gene` and report the alternative transcript
  combinations omitted at the configured limit.
- Consolidate tryptic cleavage logic in the shared translation module.
- Add synthetic coordinate, translation, NMD, rMATS-event, fusion, and
  output-schema regression tests.
- Finish fusion separation into transcript modelling, coordinate mapping,
  candidate evaluation, filtering, orchestration, reporting, and CLI modules;
  centralize scalar normalization and remove wildcard compatibility imports.
- Add strict per-step TOML validation, policy-source explanations, conventional
  output names, and checksum/configuration-safe resume manifests.
- Add stable exclusion codes, separate biological-observation and
  policy-decision
  audit fields, producer header preflight, and byte-exact producer goldens.
- Add a caller-stratified release report for transcript ambiguity, frame status,
  NMD, peptide evidence, and exclusions.

The exact thesis database release should be identified by a Git commit and
annotated tag after final validation.
