# Shared cohort preparation and utilities

**Objective:** prepare the matched Answer ALS cohort used by Objectives Two to Four, and keep shared figures and utilities.

**Dissertation:** Chapter 4, Section 4.2.1 and Table 4.4 (347 participants); Chapter 5, Sections 5.2.2–5.2.4; Chapter 6,
Sections 6.2.2–6.2.4. The schematic figures for Chapters 3–5 are in `04_miscellaneous/figures/`.

## What is done

1. **Filter and match participants** (`01_filtering_matching_patients/`): keep participants with genomic, transcriptomic and
   proteomic data, remove the 52 proteomic samples with strong batch effects, map the remaining 347 participants to their sample
   records and released files, and separate the recurring technical-control samples (BTC/BDC) for batching.
2. **Describe the cohort** (`02_demographic_plots/`): cohort and variant-carrier summaries for the literature review.
3. **Review resource use** (`03_resource_optimization/`): summarise Nextflow trace files and suggest resource settings.
4. **Utilities and figures** (`04_miscellaneous/`, `00_nf_syntax/`).

Batching (six matched RNA/proteomic batches) is in `../03_proteogenomic_database/01_sample_batches/`.

## Scripts

| Script | What it does | Dissertation |
| --- | --- | --- |
| `01_filtering_matching_patients/01_participant_filtering.R` | Keep participants with all three omics; remove the 52 batch-effect samples | Table 4.4; 4.2.1 |
| `01_filtering_matching_patients/02_merged_tp_mapping.R` | Map transcriptomic and proteomic files to participants | 5.2.4 |
| `01_filtering_matching_patients/03_split_bcd_btc.R` | Split BTC/BDC records before batching | 5.2.3 |
| `01_filtering_matching_patients/04_aals_full_merge.R` | Merge metadata with released-file paths | Table 4.4 |
| `02_demographic_plots/01_literature_review.R` | Cohort, sex, ancestry, C9orf72/ATXN2 repeat and omics-availability summaries | cohort description; no numbered table or figure |
| `03_resource_optimization/01_optimize_resources.py` | Resource summaries from Nextflow traces | not reported |
| `04_miscellaneous/move_participants_by_batch.sh`, `unpack_dir.py` | Move files into batch folders; flatten download folders | not reported |
| `00_nf_syntax/extract_nf_syntax.py` | Build a searchable Nextflow syntax reference | not reported |

## How to run

### Cohort matching

Run from `01_filtering_matching_patients/`; file names are set inside each script. Place the Answer ALS portal tables in
`data/aals_metadata_neuromine/` (`aals_dataportal_datatable.csv`, `aals_released_files.csv`,
`Proteomics_Batch_Effect_Samples_52.csv`, `Sample-Mapping-File-Feb-2024.csv`). The first and third are saved there; the other
two are controlled-access portal downloads you add yourself. The scripts read the portal tables from that folder and write
their outputs to `01_filtering_matching_patients/`.

```bash
cd 00_general/01_filtering_matching_patients
Rscript 01_participant_filtering.R   # -> filtered_matched_aals.csv (347 participants)
Rscript 04_aals_full_merge.R         # -> merged_aals_data.csv
Rscript 02_merged_tp_mapping.R       # -> filtered_mapping_data.csv
Rscript 03_split_bcd_btc.R           # -> samples_with_paths.csv, stratify_bdc.csv, stratify_btc.csv, stratify_bdc_ctrl.csv
```

`AALS_sample_filtering_matching.md` records the selection steps and counts; `data/aals_metadata_neuromine/downloading_aals_data.md`
records how the portal tables were downloaded (Feb 2024 snapshot). `filtered_aals_cleaned.csv` is a cleaned copy of
`filtered_matched_aals.csv`; check which one a downstream script reads.

### Cohort description

```bash
cd 00_general/02_demographic_plots
Rscript 01_literature_review.R   # -> figures_literature_review/*.pdf and *_counts.csv
```

Run it from its own folder: it sources `plot_helpers.R` and `thesis_palette.R` from there and reads
`../01_filtering_matching_patients/data/aals_metadata_neuromine/aals_dataportal_datatable.csv`.

### Nextflow resource review

```bash
python 03_resource_optimization/01_optimize_resources.py --input-dir /path/to/nf-results --output-prefix rnasplice_
```

Writes CPU and memory waste rankings, a process summary and a suggested resource config (`results_resource_optimization/`).

### Nextflow syntax reference

```bash
python 00_nf_syntax/extract_nf_syntax.py   # needs network access, requests and beautifulsoup4
```

## Figures and notes

- `04_miscellaneous/figures/`: `objective1_methods_flowchart.png` (Figure 3.1), `objective2_workflow.png` (Figure 4.1),
  `proteogenomic_database_v5_03102026-{workflow,splice,fusion}.png` (Figures 5.1–5.3).
- `04_miscellaneous/DMP.md` (data management plan) and `metadata.md`.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
