# 04 Revised database (v7, comparison only)

**Objective:** Objective Three: translate gene-fusion and alternative-splicing events detected in RNA-seq into a protein search database for DIA proteomics.  
**Dissertation:** Chapter 5, Sections 5.2.8 and 5.3.8  
**Back to:** [objective README](../README.md)

## What this step does

Rebuilds the database with the corrected code and stricter settings (30,031 sequences). It was never searched; it is compared
with the searched v5 build to show the effect of the additional filtering (Figure 5.4).

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_build_revised_database.sh` | Revised (v7) build with corrected code | Sections 5.2.8, 5.3.8 |

## Order of running

1. `01_build_revised_database.sh`.
2. `../06_search_assessment/02_compare_search_and_revised_databases.py` (comparison table).

## How to run each script

Commands are those used for the dissertation, with paths run from `03_proteogenomic_database/`. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_build_revised_database.sh`

Revised (v7) build with corrected code; comparison only, never searched.

- **Dissertation:** Sections 5.2.8, 5.3.8
- **Inputs:** as O3-06
- **Outputs:** results_revised_database/ (30,031 sequences, MD5 e6b4632b…)
- **Run record:** results_revised_database/.proteogenomic_state/*.json, logs/
- **Run for the dissertation:** 2026-10
- **Previous name:** `code_proteogenomic_database_v7`
- **Before running:** As for `03_search_database/02_build_search_database.sh`, with `config/workflow.publication.frozen.toml`; outputs go to `04_revised_database/results_revised_database/`.

```bash
bash 04_revised_database/01_build_revised_database.sh   # config/workflow.publication.frozen.toml
```

`02_compare_search_and_revised_databases.py` in this folder is an identical copy of the script in `06_search_assessment/`. Configurations: `config/workflow.publication.frozen.toml`, `config/workflow.standard.example.toml`.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
