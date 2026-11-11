# 04 Chapter 6 figures

**Objective:** Objective Four: link SVs, transcriptomic alterations and proteomic evidence within participants and grade the evidence for candidate mechanisms.  
**Dissertation:** Chapter 6, Sections 6.3.7–6.3.8; tables and figures: Figure 6.1, Figure 6.3  
**Back to:** [objective README](../README.md)

## What this step does

Draws Figure 6.1 (positive control for the SV expression scan) and Figure 6.3 (change in conclusion after integration) from
saved result tables, and re-themes the QC, concordance and pathway plots with the dissertation palette.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_combined_chapter6_figures.R` | Figures 6.1 and 6.3 (base R) from saved tables | Figure 6.1, Figure 6.3 |

## Order of running

Run after `01_single_layer` and `03_cross_layer`.

## How to run each script

Commands are those used for the dissertation, with paths run from `04_integration/`. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_combined_chapter6_figures.R`

Figures 6.1 and 6.3 (base R) from saved tables; re-themes QC, concordance and pathway plots.

- **Dissertation:** Sections 6.3.7–6.3.8; Figure 6.1, Figure 6.3
- **Inputs:** 01_single_layer/01e_results_sv_carrier_expression_scan_unfiltered/*_positive_control_by_length.tsv; 03_cross_layer/02_results_evaluation_table/evaluation_summary.tsv; QC rds/csv from 01_single_layer/01a_results_rna_differential_expression and 02a_results_protein_da_consortium; fgsea tables in 01_single_layer/03a_results_pathway_enrichment_{rna,protein}/results_fgsea_*_500
- **Outputs:** 04_figures/01_results_combined_chapter6_figures/Figure_6.1_*.png/.pdf, Figure_6.3_*.png/.pdf (not saved in the repo)
- **Before running:** Reads the saved results of `01_single_layer/` (01a, 01e unfiltered, 02a consortium, 03a `*_500`) and `03_cross_layer/` (01, 02) from this repository; run from anywhere. The palette is `lib/thesis_palette.R`.
- **Note:** Missing save_png/clean_pathway_label fixed 8 Nov 2026; Figures 6.1/6.3 PNGs regenerated identically before and after the fix.

```bash
Rscript 04_figures/01_combined_chapter6_figures.R
```

The output folder (`results_interpretation/`) is not in the repository; the figures can be regenerated from the saved tables. Figure 6.2 (FusionInspector views) was captured from the rnafusion igv-reports and is not saved.
Only a few examples of this script's outputs are shown.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
