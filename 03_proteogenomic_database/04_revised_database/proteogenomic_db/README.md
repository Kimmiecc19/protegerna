# Proteogenomic database reconstruction

The normalized project/package name is `proteogenomic-database-reconstruction`.
Production entry points use stable, undated module names at the repository root;
historical
dated scripts are archival only and are not part of the installed package.

The source root intentionally exposes only the eight runnable commands:
reference validation, fusion, rMATS, SUPPA, merge, QC, release reporting, and
the workflow facade. Their implementation lives under `proteogenomic/`;
tests and byte-exact fixtures live under `tests/`. Internal modules should be
imported with the `proteogenomic.` package prefix and are not separate workflow
steps.

## Recommended workflow interface

Routine runs no longer require assembling dozens of command-line switches.
Copy `workflow.standard.example.toml`, replace its input paths, and run:

```bash
proteogenomic-workflow workflow.standard.toml --dry-run
proteogenomic-workflow workflow.standard.toml

PYTHONPATH="$PWD" python -m proteogenomic_workflow  ./workflow.publication.suppa.toml --step suppa  --dry-run
```

The dry run prints every resolved production command without executing it. A
step runs when its TOML section exists and `enabled` is not false. Use `--step
rmats` (repeatable) to run only selected configured steps; a requested step
whose
section is missing or disabled is skipped with a warning, exactly as with
`--stage`.

There is one policy: the publication policy. Its choices are the program
defaults: quantms-conservative fusion, rMATS and SUPPA databases, and
conservative
rMATS event thresholds for any threshold left unset. Every boolean option
accepts
`--option` / `--no-option` (or `true` / `false` in the TOML), so any setting can
be
changed explicitly. Earlier named profiles were removed; for example, the former
exploratory behaviour is now `allow_alt_start = true` and `allow_longest_orf =
true`
under `[rmats]`/`[suppa]` (rescue FASTA names are derived from the primary
output)
plus `include_rescue_tiers = true` under `[merge]`. A legacy
`profile = "publication"` line under `[workflow]` is accepted and ignored.

```toml
[workflow]
output_dir = "results"
resume = true
```

`output_dir` supplies conventional filenames for every enabled step, so only
inputs and non-default policy choices need to be listed. `resume` skips a step
only when all declared outputs still exist and both its resolved configuration
and every discovered input checksum match the saved state. Each state/run
manifest records the software version, configuration hash, and input SHA-256
checksums.

Before launching any process, the runner validates every TOML key against the
actual parser for its section. Unknown keys fail with their exact section/key
and a spelling suggestion when one is available. Inspect the fully resolved
policy and its source with:

```bash
proteogenomic-workflow explain workflow.standard.toml
```

The explanation labels each resolved value as explicitly configured, an
output-directory convention, or a program default. A final `[report]` step can
summarize transcript ambiguity, frame
status, NMD, peptide evidence, and stable exclusion-code counts by caller.

Shared references belong under `[common]`; the runner sends each value only to
steps that accept it. Step-specific advanced options may still be written under
`[validate]`, `[fusion]`, `[rmats]`, `[suppa]`, `[merge]`, `[qc]`, or
`[report]`. Existing direct script
commands remain supported.

The TOML file is the recommended run record and should be retained alongside
the generated manifests. The advanced CLIs remain available for method
development and exact reproduction of older commands.

## Reproducible environment

Create the pinned Conda environment:

```bash
conda env create -f environment.yml
conda activate proteogenomic-database-reconstruction
```

Alternatively, install the pinned Python dependencies from `pyproject.toml`:

```bash
python -m pip install .
```

Install the test dependencies (`pip install -e ".[test]"`, or use
`environment.yml`, which includes pytest and Hypothesis), then run the
regression suite. Fixture paths are resolved relative to the test files, so
discovery also works from outside the repository root:

```bash
PYTHONPATH=. python -m unittest discover -s tests -p 'test_*.py' -v
```

## Interpretation limits

rMATS coordinates describe local splice alternatives, not complete expressed
transcripts. Each rMATS protein is therefore an event projected onto a selected
annotation model: it is a reconstructable candidate, not proof that the sample
expressed that exact molecule.

Fusion reconstruction has the same transcript-selection limitation. The default
evaluates up to three compatible transcripts for each partner. Producer FASTAs
retain every candidate that passes the DIA policy (all reconstructable
candidates
remain in the interpretation tables); the final merge deduplicates exact
protein products while aggregating their provenance. Setting
`--max_transcripts_per_gene 1` requests a conservative representative-transcript
strategy and must not be described as exhaustive fusion-proteoform recovery.

Missing GTF CDS phase remains missing in audit metadata. Sequence-length frame
classification is retained as an explicit fallback and is labeled
`sequence_length_fallback`, rather than being presented as an annotated phase of
zero.

Primary, alternative-start/rescue, exploratory-ORF, and excluded/audit outputs
must remain separate inputs. Only `merge_proteogenomic_database.py`
may collapse identical protein sequences; it aggregates all provenance headers.
The QC script filters records but deliberately does not deduplicate them.

## GENCODE translation release validation

Validate the shared coordinate/phase implementation against matching GENCODE
annotation, genome, and protein releases before publishing a database:

```bash
PYTHONPATH=. python validate_gencode_translation.py \
  --gtf_db gencode.gtf.db \
  --genome GRCh38.primary_assembly.genome.fa \
  --gencode_protein_fasta gencode.pc_translations.fa \
  --out_tsv gencode_translation_concordance.tsv \
  --out_summary_json gencode_translation_concordance.json \
  --annotation_release GENCODE_46
```

The resulting JSON is now a mandatory input to the authoritative merge via
`--gencode_concordance_summary`. The merge refuses release when any required
strand/CDS/phase stratum is absent or the measured mismatch rate exceeds the
validated threshold. The summary records the annotation release and SHA-256
checksums of the GTF database, genome and GENCODE protein FASTA; the merge
refuses a summary for a different `--annotation_release`, and checks each
producer FASTA's `<fasta>.run_config.json` manifest for the same release and
byte-identical `gtf_db`/`genome` inputs. Proteogenomic producer headers are also
checked against
the versioned `pgdb-merge-input-v1` contract before any final output is written.

Canonical concordance uses annotation-aware translation: GENCODE non-ATG
initiation is normalized to methionine, chrM uses vertebrate mitochondrial
table 2, and mapped Selenocysteine features emit U. Expected leading-residue
differences in partial non-zero-phase CDS models are reported separately.
Stop-codon-readthrough candidates are audited but conservatively excluded from
reconstructed primary FASTAs because the inserted residue is not encoded by the
stop codon alone. Release requires zero unexplained mismatches.

## Architecture and release safety

Workflow runs automatically save terminal output (stdout and stderr) for each
executed step under `<workflow.output_dir>/logs/`, or `./logs/` when no output
directory is configured. For example, `stage_02_suppa.log` records SUPPA output
including PSI loading and filtering messages; rMATS and fusion have separate
logs. Each execution records UTC timestamps, the command, working directory,
resolved configuration, and exit status. Reruns append to existing logs so
earlier
history is preserved, and resume skips are recorded. Output remains visible in
the terminal. Dry runs and explain commands do not create logs. The merge
command
implements both merging and DIA filtering, so those stages share its step log.
These logs are created by the workflow wrapper; running producer scripts
directly
still requires terminal redirection to save their output. Logs cover future runs
and cannot recover terminal output from previous runs.

Fusion parsing, reconstruction, biological eligibility, and output are isolated
in dedicated modules for transcript modelling, coordinate mapping, candidate
evaluation, filtering, orchestration, and reporting. Scalar caller-value
normalization has one owner, and compatibility facades contain no wildcard
imports. Internally, CLI values are immutable configuration
snapshots rather than mutable `argparse.Namespace` objects. rMATS projection,
frame resolution, and output-tier selection are pure stages in `rmats_stages`.
The merge aggregates retained records directly while reading, avoiding a second
full in-memory record list. Unreadable fusion inputs are release-fatal rather
than silently producing a partial database.

Closely coupled infrastructure has been consolidated without merging biological
algorithms: `audit.py` owns decision codes and failure accounting;
`release_validation.py` owns producer-header contracts and GENCODE release
gates; fusion FASTA serialization is part of `fusion_reporting.py`; and producer
fixture generation is kept with its test rather than shipped as production code.

All producer audit tables include stable `PGDB_EXCL_*` exclusion codes and keep
biological observations separate from policy decisions. Producer headers are
validated against the merge contract during serialization, with a startup
preflight before expensive reconstruction. Byte-exact producer golden fixtures
cover FASTAs, headers, exclusions, and audit tables.

The default release criterion is zero mismatches. Results are stratified by
positive/negative strand, complete/partial CDS, single/multi-exon CDS, and
zero/non-zero/missing leading phase. Any mismatch must be investigated rather
than silently accepted; `--max_mismatch_rate` changes the failure threshold only
when a documented release policy explicitly permits it.
# Workflow architecture

The public workflow has six stages:

1. Validate reference annotation.
2. Reconstruct proteins with rMATS, SUPPA, and FusionInspector.
3. Merge proteins.
4. Filter for DIA suitability.
5. Validate the database.
6. Generate the release.

Caller-specific reconstruction, exact-sequence aggregation, benchmarking, QC,
and report generation are implementation details within these stages. Select a
stage with `--stage`, for example `--stage reconstruct_proteins`. The legacy
internal `--step` switch remains accepted for reproducibility but is hidden from
normal command help.

---

## Detailed QC Summary

Run from proteogenomic_database root with the following command to generate a
detailed QC summary of the proteogenomic database:

python proteogenomic_fasta_qc.py \
  --fasta results/pgdb_publication_rerun_v5/proteogenomic_database.fasta \
  --labels proteogenomic_database \
  --metadata \
    results/pgdb_publication_rerun_v5/suppa.consequences.tsv \
    results/pgdb_publication_rerun_v5/rmats.consequences.tsv \
    results/pgdb_publication_rerun_v5/fusion.metadata.tsv \
  --outdir results/pgdb_publication_rerun_v5/qc_detailed \
  --prefix proteogenomic_database

---

Run V5

```bash
2026-10-06 14:11:13,855 [INFO] root: QC complete: 80,657 FASTA records processed
2026-10-06 14:11:13,856 [INFO] root: Total residues: 45,186,038
2026-10-06 14:11:13,856 [INFO] root: Unique protein sequences: 80,657
2026-10-06 14:11:13,856 [INFO] root: Proteins with eligible peptide: 80,653 (99.995%)
2026-10-06 14:11:13,856 [INFO] root: Proteins without eligible peptide: 4
2026-10-06 14:11:13,856 [INFO] root: Output directory: results/pgdb_publication_rerun_v5/qc_detailed
2026-10-06 14:11:13,891 [INFO] root: quantms/DIA-NN validation failures: 0
2026-10-06 14:11:13,891 [INFO] root: quantms/DIA-NN annotation warnings: 237
```

Fusion concordance:

```bash
python summarize_fusion_concordance.py \
  results/pgdb_publication_rerun_v5/fusion.biological.tsv \
  --output results/pgdb_publication_rerun_v5/qc/fusion_prediction_concordance.md
```

---

Run v6

```bash
PYTHONPATH="$PWD" python -m proteogenomic_workflow  ./workflow.publication.v6_nopsi.toml --dry-run

PYTHONPATH="$PWD" python -m proteogenomic_workflow  ./workflow.publication.v6_psi.toml --dry-run
```