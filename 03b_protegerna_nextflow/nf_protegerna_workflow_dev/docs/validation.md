# Validation status

## 12 October 2026 — bundle rebuilt from `code_proteogenomic_database_v7`

- v7 test suite: 116 passed under Python 3.13 and 3.11 (the container version). rMATS differential comparison (synthetic SE/A3SS/A5SS/MXE/RI, five option sets) and a standalone run of every stage are identical to the previous v7.
- Clean `pip install` of v7 used from outside the source tree: all step modules import, the workflow runner loads configurations, and an end-to-end run matches.
- `-profile test`: 9 tasks; final FASTA identical to the original pipeline; adapter tests and the no-Nextflow smoke run pass.

## 12 October 2026 — simplification (no profiles in v6, unpatched bundle, adapter entry point)

- v6 test suite: 92 passed; the 1 failure is the pre-existing fusion CDS golden header (`junction_aa=NA`). Producer golden outputs are byte-identical before and after removing profiles, and a standalone TOML run on the smoke fixture produces byte-identical FASTA/TSV/JSON outputs (run configs no longer record `profile`).
- `-profile test`: 9 tasks; fusion 2, rMATS 1, SUPPA 1, final database 4 sequences; final FASTA byte-identical to the original pipeline. Merge tables are identical between repeated runs (apart from work-directory paths).
- `-profile publication` with rescue tiers enabled in the params file: `allow_alt_start`, `include_rescue_tiers` and an explicit `quantms_conservative: false` reach the commands; alternative-start FASTAs are produced and merged.
- 7 adapter tests and `tests/run_python_smoke.py` pass.

## 12 October 2026 — v6 runtime and two-profile configuration

Run on Linux with Nextflow 25.10.4 and Python 3.13 with the pinned dependencies (Apptainer disabled for this check):

- `-profile test`: 9 tasks succeeded; fusion 2, rMATS 1, SUPPA 1, final database 4 sequences. All producer and merge FASTA/TSV outputs are byte-identical to the previous (v5 runtime) pipeline.
- `-profile publication -params-file`: the generated params template (pointed at the smoke fixture) ran to completion; an override (`merge.min_protein_length: 8`) reached the merge command, and a partial `rmats` block kept the remaining publication values.
- A misspelt option (`rmats.max_fdrr`), no profile, and `-profile test,publication` each stop before any task with a clear message.
- 7 adapter tests passed against the v6 runtime.

The Apptainer run on the server (`bash tests/run_server_smoke.sh /absolute/path/protegerna.sif`) is still the acceptance test for container staging.

## 25 September 2026

## Completed checks

- Nextflow **25.10.4** successfully parses the active entry point, workflow, five subworkflows and process modules.
- The same Nextflow engine successfully constructs the complete dataflow graph with the synthetic test configuration. This caught and fixed unsupported `0..1` path arity; optional input lists use `0..*` and callers supply zero or one file.
- All biological Python process templates execute successfully on the synthetic fixture: GTF database creation, GENCODE validation, reference caching, fusion, rMATS, SUPPA, merge and strict QC.
- Synthetic GENCODE validation covers all five required strata with **zero mismatches**. Producer outputs contain **2 fusion**, **1 rMATS** and **1 SUPPA** records. The merged database contains **4 unique protein sequences**.
- All **7 adapter tests** passed, covering real CLI parsers, explicit `false` settings under the publication profile, filename spaces, metadata preservation, empty-file rejection and frozen-policy values.
- The versions-collection template passed too, combining the eight scientific/reference process records. All **9 Python process templates** passed; the native completion hook also wrote its run-provenance JSON during graph validation.
- The original biological regression suite was run against the bundled source: **90 passed; 2 golden byte-comparison tests failed**. QC output matches its fixture after CRLF-to-LF normalization. The producer fixture additionally omits a `junction_aa=NA` header field emitted by the **untouched original source as well**. This is a pre-existing fixture mismatch, not a new translation change.

Python process testing used Python 3.12 on Windows and the pinned scientific dependencies. The supplied Apptainer definition targets Python 3.11.13, matching the original package requirements.

## Linux acceptance test still required

Native Windows Nextflow stops on the unsupported POSIX `HUP` signal before task execution. The compilation/dataflow check therefore used the unmodified Nextflow compiler and graph APIs without starting tasks or signal handlers. It is not a substitute for testing Linux staging, Apptainer mounts and `-resume`.

Run on the local Linux server:

```bash
apptainer build protegerna.sif containers/proteogenomic/Apptainer.def
bash tests/run_server_smoke.sh /absolute/path/protegerna.sif
bash tests/run_server_smoke.sh /absolute/path/protegerna.sif -resume
```

The acceptance script checks all producer record counts, four final sequences, nine traced tasks and the software-versions output. The nf-test pipeline case can also be run with `PROTEGERNA_CONTAINER` set.

## Supplied real-data inventory

The checked `../test_data` contains:

- `test_fusion/fusioninspector/test/test.FusionInspector.fusions.abridged.tsv`: **72,185 bytes**, suitable as a fusion input.
- `test_splice/star_salmon/suppa/generate_events/per_local_event/events.ioe`: **82,949,644 bytes**.
- `test_splice/star_salmon/suppa/psi_per_local_event/suppa_local.psi`: **0 bytes**, rejected by input validation.
- rMATS preparation outputs and `.rmats` files, but no final `*.MATS.JC.txt` event tables.
- No complete genome FASTA, GTF/gffutils database, GENCODE translations or target reference proteome suitable for this workflow's reference inputs. RNA run metadata records matching server genome/GTF paths; see [usage](usage.md).

Consequently, a real-cohort three-producer run and equivalence to an expected production database have not been established. The frozen biological policies were not relaxed to make incomplete inputs pass.
