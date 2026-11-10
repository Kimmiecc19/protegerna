# nf_protegerna pipeline (Nextflow implementation of Objective 3)

**Folder:** [`03b_protegerna_nextflow/nf_protegerna_workflow_dev/`](https://github.com/Kimmiecc19/protegerna/tree/main/03b_protegerna_nextflow/nf_protegerna_workflow_dev)
**Also published at:** [github.com/Kimmiecc19/nf_protegerna](https://github.com/Kimmiecc19/nf_protegerna)
**Dissertation:** Chapter 5, Sections 5.2.10 and 5.3.13; Table 5.12

## Overview

nf_protegerna packages the [Objective 3](Objective-3-Proteogenomic-Database) database workflow as an nf-core-style
Nextflow DSL2 pipeline. It builds a proteogenomic protein database from FusionInspector, rMATS and SUPPA results, on a local
Linux server with Apptainer.

```text
samplesheet + matched reference files
                   |
validate: optional GTF database creation + GENCODE concordance + peptide cache
                   |
       fusion                 splice
   fusiontoprotein     rmatstoprotein + suppatoprotein
                   |
       merge: exact amino-acid sequence deduplication
                   |
       qc: strict proteogenomic FASTA validation
```

> **Note:** no database searched in Chapters 5 or 6 was built with this pipeline. The searched v5 database came from the
> script workflow in `03_proteogenomic_database/03_search_database/`. The pipeline uses the same frozen v5 policy.

## Installation

| Requirement | Version |
| --- | --- |
| Nextflow | ≥ 25.10.4 |
| Java | Compatible with your Nextflow |
| Apptainer | – (Docker also works for the `test` profile) |

Build the dependency image from the pipeline root:

```bash
cd 03b_protegerna_nextflow/nf_protegerna_workflow_dev
apptainer build protegerna.sif containers/proteogenomic/Apptainer.def
```

## Inputs required

### Samplesheet

Each row describes one existing **result file** (not a FASTQ). All columns are required; use `NA` for unknown batch or
condition.

```csv
sample,tool,event_type,path,batch,condition
S1,fusion,FUSION,S1.FusionInspector.fusions.abridged.tsv,batch1,CASE
CASE-CTRL,rmats,SE,SE.MATS.JC.txt,batch1,CASE-CTRL
cohort,suppa,IOE,events.ioe,batch1,NA
cohort,suppa,PSI,events.psi,batch1,NA
```

| Column | Meaning |
| --- | --- |
| `sample` | Fusion sample ID; rMATS comparison ID such as `CASE-CTRL`; SUPPA cohort/file-set label |
| `tool` | `fusion`, `rmats` or `suppa` |
| `event_type` | Fusion: `FUSION`; rMATS: `SE`, `A3SS`, `A5SS`, `MXE`, `RI`; SUPPA: `IOE` or `PSI` |
| `path` | Path to a result file (absolute or relative to the samplesheet). rMATS inputs are final event tables, not `.rmats` files. |
| `batch` | Batch label |
| `condition` | Fusion condition, rMATS comparison conditions, or the condition shared by all samples in a PSI matrix; otherwise `NA` |

Rules: fusion IDs must be unique; repeated paths and empty files are rejected; globs and directories are not accepted; at
least one producer (fusion, rmats or suppa) is required. SUPPA needs both IOE and PSI rows by default. For mixed-condition PSI
matrices, supply an optional `sample_metadata` CSV/TSV with `sample_id,batch,condition`.

### References

Use the same genome and annotation as the upstream RNA workflows:

- uncompressed genome FASTA;
- target reference proteome FASTA;
- **exactly one** of a matching GTF (`gtf`) or gffutils database (`gtf_db`);
- the matching official GENCODE protein translations (`.fa` or `.fa.gz`);
- optional contaminant FASTA (added during merge).

### Parameters

`assets/params.publication.yml` lists every parameter, pre-filled with the publication values. The biological policy is the
frozen `assets/workflow.publication.v5.toml`. `docs/toml_parameter_mapping.tsv` maps every TOML option to its pipeline
parameter. Example overrides:

```yaml
rmats:
  max_fdr: 0.05
  include_failed_filter_proteins: false
suppa:
  min_psi: 0.1
```

Pass parameters with the CLI or `-params-file`, not with `-c` config files.

## Running

The pipeline has exactly two profiles, both using the local executor with Apptainer:

| Profile | Purpose |
| --- | --- |
| `test` | Small synthetic smoke test that checks the installation works |
| `publication` | Production run. Every input and option comes from a params file. |

Running without one of these profiles stops with a usage message.

### 1. Smoke test

```bash
nextflow run . -profile test \
  --proteogenomic_container /absolute/path/protegerna.sif
```

Expected: producer records fusion **2**, rMATS **1**, SUPPA **1**; final database **4** unique sequences (Table 5.12). This
is an integration test, not validation against a real cohort.

### 2. Production run

`assets/params.publication.yml` uses paths relative to the pipeline root. It reads `tests/data_full/`, whose
`samplesheet.csv` points at the CASE-NEUWY079WUH FusionInspector calls and the batch-1 rMATS and SUPPA outputs in
`03_proteogenomic_database/02_event_detection/`. The genome FASTA and GTF are not in the repository, so add them to
`tests/data_full/` or point `genome` and `gtf` at them.

```bash
cp assets/params.publication.yml params.yml     # set genome/gtf; keep exactly one of gtf / gtf_db
nextflow run . -profile publication \
  --proteogenomic_container "$(realpath protegerna.sif)" \
  -params-file params.yml \
  --outdir "$(realpath results)/my_run" \
  -work-dir "$(realpath work)/my_run" \
  -resume
```

Resources: `max_cpus` and `max_memory` bound the executor. The publication profile requests 2 CPUs/8 GB for medium and
4 CPUs/16 GB for high-load processes. Change these per process with `-c custom.config`.

### 3. Tests without Nextflow

```bash
python tests/run_python_smoke.py                                     # every stage through the task adapter
python -m unittest discover -s tests -p 'test_nextflow_adapter.py'   # adapters and options
bash tests/run_server_smoke.sh /absolute/path/protegerna.sif         # Linux acceptance test
```

## Expected outputs

| Folder | Contents |
| --- | --- |
| `merge/` | **`proteogenomic_database.fasta`** (final search database), metadata, original-to-final ID mapping, peptide evidence, biological interpretation, summary TSV/JSON |
| `fusion/`, `rmats/`, `suppa/` | Producer FASTAs and audit tables |
| `validate/` | GENCODE concordance results |
| `cache/` | Reference peptide cache |
| `qc/` | Strict FASTA QC tables |
| `pipeline_info/` | Nextflow report, timeline, trace, DAG, `software_versions.yml`, and a run JSON with parameters, command line, Nextflow version and work directory |

Each biological process also publishes `task_inputs.json`, `command.json` and any run manifests. MultiQC only reports pipeline
information, not biological QC.

## Runs reported in the dissertation

| Run | Command | Result |
| --- | --- | --- |
| 19 Oct 2026 (`tender_poincare`) | `nextflow run main.nf -profile test,docker --outdir results/test_yay` | Table 5.12: 6 synthetic records merged into 4 unique sequences |
| 2 Nov 2026 (`grave_pauling`) | `nextflow run main.nf -profile publication -params-file assets/params.publication.yml --outdir test_publication_woohoo ...` on one participant (CASE-NEUWY079WUH FusionInspector calls with the cohort rMATS and SUPPA outputs) | 61,800 unique sequences |

## Updating the reconstruction code

The pipeline's Python code is copied from the database workflow. After changing that code, run
`python scripts/build_runtime.py` (Python ≥ 3.11) from the pipeline root to refresh the runtime and
`assets/resolved_publication_defaults.json`.

## Known issues

- Some files and README sections are still from the nf-core template (marked `TODO nf-core`).
