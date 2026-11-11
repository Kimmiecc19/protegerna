# 01 Sample batches and acquisition mode

**Objective:** Objective Three: translate gene-fusion and alternative-splicing events detected in RNA-seq into a protein search database for DIA proteomics.  
**Dissertation:** Chapter 5, Sections 5.2.2–5.2.4 and 5.2.9; tables and figures: Table 5.6  
**Back to:** [objective README](../README.md)

## What this step does

Splits the matched participants into six artificial batches with StratifiedKFold on sex, diagnosis, sequencing batch and
shipment batch, and adds the recurring technical-control samples (BTC) round-robin, so that RNA batch N and proteomic batch N hold
the same participants. A second script confirms from the mzML isolation windows that every run is DIA (153 files checked).

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01a_make_stratified_batches.py` | Six artificial batches (StratifiedKFold on sex, diagnosis, sequencing and shipment batch) | Table 5.6 |
| `01b_validation.py` | Batch balance statistics | Table 5.6 |
| `02_detect_acquisition_mode.py` | Confirm DIA acquisition from mzML isolation windows (153 files, all DIA) | Section 5.2.9 |

## Order of running

1. `01a_make_stratified_batches.py` (needs `00_general/01_filtering_matching_patients/stratify_{bdc,btc}.csv`).
2. `01b_validation.py`.
3. `02_detect_acquisition_mode.py` (independent).

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01a_make_stratified_batches.py`

Six artificial batches (StratifiedKFold on sex, diagnosis, sequencing and shipment batch); BTC/BDC added round-robin.

- **Dissertation:** Sections 5.2.2–5.2.4, 5.2.9; Table 5.6
- **Inputs:** 00_general/01_filtering_matching_patients/stratify_bdc.csv, stratify_btc.csv
- **Outputs:** 01_results_stratified_batches/batch_files/ (proteomic_batches.csv, transcriptomic_batches.csv, artificial_*_batch_N.csv, batch_summary_report_17062025.csv)
- **Run record:** batch_summary_report_17062025.csv
- **Run for the dissertation:** 2025-06-17
- **Before running:** Reads `stratify_bdc.csv` and `stratify_btc.csv` from `00_general/01_filtering_matching_patients/` and writes tables to `01_results_stratified_batches/batch_files/` and figures to `01_results_stratified_batches/batch_figures/` (paths in the CONFIG block at the top).
- **Note:** Earlier map: three versions of the stratification script existed; confirm this copy reproduces batch_files/ and record its seed.

```bash
python 01a_make_stratified_batches.py
```

### `01b_validation.py`

Batch balance statistics.

- **Dissertation:** Section 5.2.9; Table 5.6
- **Inputs:** proteomic_batches.csv, transcriptomic_batches.csv
- **Outputs:** 01_results_stratified_batches/batch_files/*_batch_stats_*.csv, batch_figures/
- **Run for the dissertation:** 2025-06
- **Before running:** Reads and writes `01_results_stratified_batches/batch_files/`.

```bash
python 01b_validation.py
```

### `02_detect_acquisition_mode.py`

Confirm DIA acquisition from mzML isolation windows (153 files, all DIA).

- **Dissertation:** Section 5.2.9
- **Inputs:** Answer ALS mzML files
- **Outputs:** 02_results_detect_acquisition_mode/mzML_mode_summary*.csv
- **Note:** Notes: answerals_proteomics_mode_detection.md.

```bash
python 02_detect_acquisition_mode.py /path/to/mzML --outdir 02_results_detect_acquisition_mode --max-scans 5000 --dia-threshold 5
```

Notes: `sample_stratification_batches.md` (batching logic) and `answerals_proteomics_mode_detection.md` (acquisition-mode check).

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
