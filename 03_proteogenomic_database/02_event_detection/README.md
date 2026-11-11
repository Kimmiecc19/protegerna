# 02 Splice and fusion event detection

**Objective:** Objective Three: translate gene-fusion and alternative-splicing events detected in RNA-seq into a protein search database for DIA proteomics.  
**Dissertation:** Chapter 5, Section 5.2.5; tables and figures: Figure 6.2  
**Back to:** [objective README](../README.md)

## What this step does

Runs nf-core/rnafusion 4.0.0 (Arriba, STAR-Fusion, FusionCatcher, fusion-report and FusionInspector) and nf-core/rnasplice
1.0.3 (rMATS, SUPPA) on the RNA-seq FASTQ files of each batch. Only the FusionInspector predictions, the rMATS junction-count
tables and the SUPPA event definitions enter the search database; the rnasplice quantitative outputs are invalid because the
libraries were processed as forward-stranded.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_build_rnafusion_references.sh` | Build the nf-core/rnafusion references (Arriba, STAR-Fusion, FusionCatcher) | Section 5.2.5 |
| `02a_create_rnafusion_samplesheet.py` | Write an nf-core/rnafusion samplesheet from a folder of paired FASTQ files | Section 5.2.5 |
| `02b_run_rnafusion.sh` | nf-core/rnafusion 4.0.0 (--tools all) per batch | Figure 6.2 |
| `03a_create_rnasplice_samplesheet.py` | Write an nf-core/rnasplice samplesheet (sample, fastq_1, fastq_2, strandedness, condition) | Section 5.2.5 |
| `03b_run_rnasplice.sh` | nf-core/rnasplice 1.0.3 per batch (rMATS JC tables and SUPPA events used | Section 5.2.5 |

## Order of running

1. `01_build_rnafusion_references.sh` (once).
2. `02a_create_rnafusion_samplesheet.py`, then `02b_run_rnafusion.sh` per batch.
3. `03a_create_rnasplice_samplesheet.py`, then `03b_run_rnasplice.sh` per batch.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_build_rnafusion_references.sh`

Build the nf-core/rnafusion references (Arriba, STAR-Fusion, FusionCatcher).

- **Dissertation:** Section 5.2.5
- **Inputs:** GRCh38 genome and GTF; COSMIC account (for the COSMIC fusion database)
- **Outputs:** rnafusion reference folders (server only)
- **Run record:** 02_03_params/rnafusion_build.config
- **Run for the dissertation:** 2025-09
- **Before running:** Export `COSMIC_USERNAME` and `COSMIC_PASSWD` (never write them in the script or in `02_03_params/rnafusion.json`) and set `FUSION_REF_DIR` (reference output folder). Uses `02_03_params/rnafusion_build.config`.
- **Note:** Never store the COSMIC user name or password in this script; pass them at run time.

```bash
COSMIC_USERNAME=... COSMIC_PASSWD=... FUSION_REF_DIR=/path/to/references/fusion_ref bash 01_build_rnafusion_references.sh
```

### `02a_create_rnafusion_samplesheet.py`

Write an nf-core/rnafusion samplesheet from a folder of paired FASTQ files.

- **Dissertation:** Section 5.2.5
- **Inputs:** per-batch FASTQ folders
- **Outputs:** samplesheet_batchN_rnaseqfusion.csv
- **Run for the dissertation:** 2025

```bash
python 02a_create_rnafusion_samplesheet.py <FASTQ batch folder> samplesheet_batchN_rnaseqfusion.csv
```

### `02b_run_rnafusion.sh`

nf-core/rnafusion 4.0.0 (--tools all) per batch.

- **Dissertation:** Sections 5.2.5; 6.2.9; Figure 6.2
- **Inputs:** RNA-seq FASTQ (412 samples); rnafusion references
- **Outputs:** 02_results_rnafusion_final/ (fusioninspector, fusionreport, arriba per batch)
- **Run record:** 02_03_params/rnafusion.json, rnafusion.config
- **Run for the dissertation:** 2026
- **Before running:** Set the reference paths in `02_03_params/rnafusion.config` and `rnafusion.json`, and `GENOMES_BASE`, `SAMPLESHEET` and `RNAFUSION_OUTDIR` in the Settings block (or as environment variables). Run once per batch.

```bash
GENOMES_BASE=/path/to/references/GRCh38 SAMPLESHEET=samplesheet_batchN_rnaseqfusion.csv RNAFUSION_OUTDIR=/path/to/nf_results/rnafusion bash 02b_run_rnafusion.sh N   # nf-core/rnafusion -r 4.0.0 --tools all with 02_03_params/rnafusion.{config,json}
```

### `03a_create_rnasplice_samplesheet.py`

Write an nf-core/rnasplice samplesheet (sample, fastq_1, fastq_2, strandedness, condition).

- **Dissertation:** Section 5.2.5
- **Inputs:** per-batch FASTQ folders
- **Outputs:** samplesheet_batchN_rnasplice.csv
- **Run for the dissertation:** 2025
- **Note:** Writes strandedness = forward. The Answer ALS libraries are reverse-stranded, which is why the rnasplice quantitative outputs were not used (Section 5.2.5).

```bash
python 03a_create_rnasplice_samplesheet.py <FASTQ batch folder> samplesheet_batchN_rnasplice.csv
```

### `03b_run_rnasplice.sh`

nf-core/rnasplice 1.0.3 per batch (rMATS JC tables and SUPPA events used; quantitative outputs invalid).

- **Dissertation:** Section 5.2.5
- **Inputs:** RNA-seq FASTQ; rnasplice_contrast.csv (not in repo)
- **Outputs:** 03_results_rnasplice_final/
- **Run record:** 02_03_params/rnasplice.json
- **Run for the dissertation:** 2026
- **Before running:** Set the reference paths in `02_03_params/rnasplice.config`, and `SAMPLESHEET`, `RNASPLICE_OUTDIR` and `CONTRASTS` (default `02_03_params/rnasplice_contrast.csv`, not in the repository) in the Settings block. Run once per batch.
- **Note:** Run with forward strandedness on reverse-stranded libraries; splice entries lack valid RNA support.

```bash
SAMPLESHEET=samplesheet_batchN_rnasplice.csv RNASPLICE_OUTDIR=/path/to/nf_results/rnasplice bash 03b_run_rnasplice.sh N   # nf-core/rnasplice -r 1.0.3 with 02_03_params/rnasplice.{config,json}
```

Parameter files: `02_03_params/` (`rnafusion.json`, `rnafusion.config`, `rnafusion_build.config`, `rnasplice.json`, `rnasplice.config`). `rnasplice_contrast.csv` is not in the repository.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
