# 01 SV calling with nf-core/sarek

**Objective:** Objective Two: a reproducible workflow for structural-variant (SV) detection, consolidation, annotation, ALS-informed nomination and interactive exploration.  
**Dissertation:** Chapter 4, Section 4.2.3  
**Back to:** [objective README](../README.md)

## What this step does

Calls germline SVs in the 347 matched Answer ALS genomes with nf-core/sarek 3.5.1, starting from the supplied CRAM files
(`--step prepare_recalibration`). Manta 1.6.0 and TIDDIT 3.6.1 provide the SV calls used downstream; CNVkit also runs but its
output was not used. Sarek was run in 14 batches of participants.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_create_samplesheet_batches_sarek.py` | Pair each CRAM with its CRAI and write 14 Sarek samplesheets | Section 4.2.3 |
| `03_run_aals_sarek.sh` | nf-core/sarek 3.5.1 from prepare_recalibration: Manta + TIDDIT (+ CNVkit, unused) | Section 4.2.3 |
| `02_analyse_resources_sarek.py` | Summarise Sarek CPU/memory/runtime from trace files | — |

## Order of running

1. `01_create_samplesheet_batches_sarek.py` – make the 14 samplesheets.
2. `03_run_aals_sarek.sh` – run Sarek once per samplesheet (server, Apptainer).
3. `02_analyse_resources_sarek.py` – optional; resource summary only.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_create_samplesheet_batches_sarek.py`

Pair each CRAM with its CRAI and write 14 Sarek samplesheets.

- **Dissertation:** Section 4.2.3
- **Inputs:** Answer ALS CRAM/CRAI, 347 participants
- **Outputs:** 01_results_sarek_samplesheet/sarek_samplesheet_part_{1..14}.csv
- **Run for the dissertation:** June 2025
- **Previous name:** `2_SV_analysis/1_sarek/code_sarek/create_samplesheet_batches_June2025.py`

```bash
python 01_create_samplesheet_batches_sarek.py <CRAM_DIR> sarek_samplesheet
```

### `03_run_aals_sarek.sh`

nf-core/sarek 3.5.1 from prepare_recalibration: Manta + TIDDIT (+ CNVkit, unused).

- **Dissertation:** Section 4.2.3
- **Inputs:** sarek samplesheets; GRCh38_full_analysis_set_plus_decoy_hla.fa; dbSNP 138 + known indels; snpEff GRCh38.105; VEP 112
- **Outputs:** per-participant Manta and TIDDIT VCFs under <SAREK>/partN/variant_calling/ (server only)
- **Run record:** aals_sarek.json, aals_sarek.config
- **Run for the dissertation:** 2025
- **Previous name:** `2_SV_analysis/1_sarek/code_sarek/aals_sarek.sh`
- **Before running:** Set the reference paths in `aals_sarek.config` (`fasta`, `fasta_fai`, `dict`, `cacheDir`) and `aals_sarek.json` (dbSNP, known indels, snpEff, VEP), and `SAREK_OUTDIR` (default `/path/to/sarek_results`). The samplesheet defaults to `01_results_sarek_samplesheet/sarek_samplesheet_part_N.csv`. Run once per samplesheet.
- **Note:** Calls are not in the repo (controlled access).

```bash
SAREK_OUTDIR=/path/to/sarek_results bash 03_run_aals_sarek.sh N   # N = 1..14; runs nf-core/sarek -r 3.5.1 with aals_sarek.config + aals_sarek.json
```

### `02_analyse_resources_sarek.py`

Summarise Sarek CPU/memory/runtime from trace files.

- **Dissertation:** not reported in the dissertation
- **Inputs:** execution_trace_* files
- **Outputs:** resource summaries
- **Run for the dissertation:** March 2026
- **Previous name:** `analyse_resources_final_march2026.py`
- **Note:** No dissertation result.

```bash
python 02_analyse_resources_sarek.py -i <SAREK> -p sarek_
```

**Next step:** [`02_sv_consolidation`](../02_sv_consolidation/README.md) reads the per-participant Manta and TIDDIT VCFs from `<SAREK>/partN/variant_calling/`.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
