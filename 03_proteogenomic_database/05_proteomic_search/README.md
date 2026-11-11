# 05 DIA searches with quantmsdiann

**Objective:** Objective Three: translate gene-fusion and alternative-splicing events detected in RNA-seq into a protein search database for DIA proteomics.  
**Dissertation:** Chapter 5, Section 5.2.9  
**Back to:** [objective README](../README.md)

## What this step does

Builds the reference-only database (reviewed human UniProt with isoforms plus cRAP, 42,562 sequences) and searches each of the
six DIA batches twice with bigbio/quantmsdiann 2.2.0 (DIA-NN 1.8.1): against the reference-only database and against the v5
proteogenomic database.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_make_reference_database.py` | Reviewed human UniProt + isoforms + cRAP, deduplicated (42,562 sequences) | Section 5.2.9 |
| `02a_run_quantmsdiann_reference.sh` | bigbio/quantmsdiann 2.2.0 (DIA-NN 1.8.1), reference-only database, per batch | Section 5.2.9 |
| `02b_run_quantmsdiann_proteogenomic.sh` | quantmsdiann against the v5 proteogenomic database, per batch | Sections 5.2.9; 6.2.12 |

## Order of running

1. `01_make_reference_database.py`.
2. `02a_run_quantmsdiann_reference.sh` and `02b_run_quantmsdiann_proteogenomic.sh`, once per batch.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_make_reference_database.py`

Reviewed human UniProt + isoforms + cRAP, deduplicated (42,562 sequences).

- **Dissertation:** Section 5.2.9
- **Inputs:** UniProt REST download; cRAP (thegpm.org)
- **Outputs:** 01_results_make_reference_database/human_reference_deduplicated.fasta, crap.fasta
- **Run record:** 01_results_make_reference_database/database_build_log.txt
- **Run for the dissertation:** 2026-02
- **Before running:** Writes to `01_results_make_reference_database/` (where `02_params/reference.json.json` and `02a` expect it). Needs network access to UniProt and the GPM FTP site.

```bash
python 01_make_reference_database.py
```

### `02a_run_quantmsdiann_reference.sh`

bigbio/quantmsdiann 2.2.0 (DIA-NN 1.8.1), reference-only database, per batch.

- **Dissertation:** Section 5.2.9
- **Inputs:** per-batch SDRF; mzML; human_reference_deduplicated.fasta
- **Outputs:** 02a_results_quantmsdiann_reference/batch{1_fixed,2..6}/quant_tables/
- **Run record:** 02_params/reference.json.json
- **Run for the dissertation:** 2026-08-14 to 09-03; batch 1 repeated 2026-10-27
- **Before running:** Set `SDRF` (per-batch SDRF, controlled access) and the container `cacheDir` in `02_params/reference.config`. Defaults: database `01_results_make_reference_database/human_reference_deduplicated.fasta`, output `02a_results_quantmsdiann_reference/batchN`. Run once per batch.
- **Note:** Batch 1 used is batch1_fixed (27 Oct); the earlier run without carbamidomethyl is superseded.

```bash
SDRF=/path/to/sdrf_batchN.sdrf.tsv bash 02a_run_quantmsdiann_reference.sh N   # bigbio/quantmsdiann -r 2.2.0 with 02_params/reference.json.json + reference.config
```

### `02b_run_quantmsdiann_proteogenomic.sh`

quantmsdiann against the v5 proteogenomic database, per batch.

- **Dissertation:** Sections 5.2.9; 6.2.12
- **Inputs:** per-batch SDRF; mzML; proteogenomic_database.fasta (v5)
- **Outputs:** 02b_results_quantmsdiann_pgdb/pgdb_v5_batch{1..6}/quant_tables/
- **Run record:** 02_params/proteogenomic_v5.json (copied from pipeline_info/params_*.json)
- **Run for the dissertation:** 2026-09
- **Before running:** As for `02a`. The database defaults to `../03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_database.fasta` and the output to `02b_results_quantmsdiann_pgdb/pgdb_v5_batchN`. Run once per batch.
- **Note:** Inputs to Chapter 6 (01b, 02b, linking).

```bash
SDRF=/path/to/sdrf_batchN.sdrf.tsv bash 02b_run_quantmsdiann_proteogenomic.sh N   # bigbio/quantmsdiann -r 2.2.0 with 02_params/proteogenomic_v5.json + reference.config
```

Parameter files: `02_params/reference.json.json`, `02_params/reference.config`, `02_params/proteogenomic_v5.json`. Batch 1 of the reference search was repeated on 27 October 2026 (`batch1_fixed`); the earlier run without carbamidomethylation is not used.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
