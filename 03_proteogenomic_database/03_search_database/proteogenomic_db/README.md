# Proteogenomic database reconstruction

The normalized project/package name is `proteogenomic-database-reconstruction`.
Production entry points use stable, undated module names in `code/`; historical
dated scripts are archival only and are not part of the installed package.

The source root intentionally exposes only the eight runnable commands:
reference validation, fusion, rMATS, SUPPA, merge, QC, release reporting, and
the workflow facade. Their implementation lives under `code/proteogenomic/`;
tests and byte-exact fixtures live under `tests/`. Internal modules should be
imported with the `proteogenomic.` package prefix and are not separate workflow
steps.

## Recommended workflow interface

The workflow reads one TOML configuration; there is no profile selector. Policy
choices, inputs, and output paths belong in the relevant TOML sections. Start
with one of these templates:

- `workflow.standard.example.toml` is a practical starting configuration. Replace
  its example input paths and enable only the steps you want to run.
- `workflow.minimum.example.toml` shows the minimum inputs for the complete
  production path: validation, fusion, rMATS, SUPPA, merge, QC, and release
  reporting. It uses `output_dir` to generate the conventional output filenames
  and connects each step to the files produced by earlier steps. Benchmarking is
  omitted because it requires separate actual and truth files.
- `workflow.full.example.toml` is a reference template listing all available
  workflow and step parameters, including optional outputs and the benchmark
  step. Replace every placeholder path and adjust the settings before execution.

For example, copy a template to a new configuration, edit its paths, and inspect
the commands before running:

```bash
cp workflow.minimum.example.toml my_workflow.toml
# Edit my_workflow.toml with your real paths and settings.
proteogenomic-workflow my_workflow.toml --dry-run
proteogenomic-workflow my_workflow.toml
```

The dry run prints the resolved commands without executing them. A step runs
when its TOML section exists and `enabled` is not false. Use `--step rmats`
(repeatable) or `--stage reconstruct_proteins` to select configured work. The
`--resume` option can be set in TOML under `[workflow]` or passed on the command
line.

Policy choices are ordinary step options. For example, set
`quantms_conservative = true` under `[fusion]`, `[rmats]`, or `[suppa]` to enable
the recommended primary quantMS policy; rMATS also accepts
`rmats_conservative_event_filter = true`. Exploratory reconstruction is
controlled explicitly with `allow_alt_start` and `allow_longest_orf`; configure
`out_alt_start_prot_fa` and `out_exploratory_orf_fa` when those outputs are
enabled. No policy is inferred from a profile name.

```toml
[workflow]
output_dir = "results"
resume = true

[fusion]
quantms_conservative = true

[rmats]
quantms_conservative = true
rmats_conservative_event_filter = true
allow_alt_start = false
allow_longest_orf = false
```

`output_dir` supplies conventional filenames for step outputs unless those
outputs are explicitly configured. `resume` skips a step only when its declared
outputs still exist and the resolved configuration and discovered input
checksums match the saved state. Each state/run manifest records the software
version, configuration hash, and input SHA-256 checksums.

Before launching a process, the runner validates each TOML key against the
current parser for that step. Unknown keys fail with their section/key and a
spelling suggestion when available. Inspect resolved settings with:

```bash
proteogenomic-workflow explain my_workflow.toml
```

The explanation labels each value as configured or supplied by an output-directory
convention. A `[report]` step can summarize transcript ambiguity, frame status,
NMD, peptide evidence, and stable exclusion-code counts by caller.

Shared references belong under `[common]`; the runner passes each shared value
only to steps that accept it. Step-specific options belong under `[validate]`,
`[fusion]`, `[rmats]`, `[suppa]`, `[benchmark]`, `[merge]`, `[qc]`, or `[report]`.
The direct command-line tools remain available for advanced use. Keep the TOML
configuration alongside the generated manifests as the run record.

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

Run the regression suite from the repository root:

```bash
PYTHONPATH=code python -m unittest discover -s tests -p 'test_*.py' -v
```

## Interpretation limits

rMATS coordinates describe local splice alternatives, not complete expressed
transcripts. Each rMATS protein is therefore an event projected onto a selected
annotation model: it is a reconstructable candidate, not proof that the sample
expressed that exact molecule.

Fusion reconstruction has the same transcript-selection limitation. The default
evaluates up to three compatible transcripts for each partner. Producer FASTAs
retain every reconstructable candidate; the final merge deduplicates exact
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
PYTHONPATH=code python code/validate_gencode_translation.py \
  --gtf_db gencode.gtf.db \
  --genome GRCh38.primary_assembly.genome.fa \
  --gencode_protein_fasta gencode.pc_translations.fa \
  --out_tsv gencode_translation_concordance.tsv \
  --out_summary_json gencode_translation_concordance.json
```

The resulting JSON is now a mandatory input to the authoritative merge via
`--gencode_concordance_summary`. The merge refuses release when any required
strand/CDS/phase stratum is absent or the measured mismatch rate exceeds the
validated threshold. Proteogenomic producer headers are also checked against
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
