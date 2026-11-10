# 06 proteGErna-SV dashboard

**Objective:** Objective Two: a reproducible workflow for structural-variant (SV) detection, consolidation, annotation, ALS-informed nomination and interactive exploration.  
**Dissertation:** Chapter 4, Sections 4.2.10 and 4.3.8; tables and figures: Figure 4.5, Figure 4.6, Figure 4.7, Figure 4.8, Figure 4.9, Figure 4.10  
**Back to:** [objective README](../README.md)

## What this step does

An R Shiny app for exploring any AnnotSV-annotated VCF (upload limit 60 MiB). Views: Overview, Structural variants (filters and
HTML/CSV/XLSX export), Column descriptions and Resource search (gene look-ups in external resources). The dissertation demonstrates
it with the filtered AnnotSV intersection VCF.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `proteGErna-SV.R` | Shiny dashboard for AnnotSV-annotated VCFs (Overview, Structural variants, Column descriptions, Resource search) | Figure 4.5, Figure 4.6, Figure 4.7, Figure 4.8, Figure 4.9, Figure 4.10 |

## Order of running

Start the app and upload an annotated VCF. Keep `sv_dashboard_helpers.R`, `annotsv_column_descriptions.tsv` and `www/` in the
same folder as `proteGErna-SV.R`.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `proteGErna-SV.R`

Shiny dashboard for AnnotSV-annotated VCFs (Overview, Structural variants, Column descriptions, Resource search).

- **Dissertation:** Sections 4.2.10, 4.3.8; Figure 4.5, Figure 4.6, Figure 4.7, Figure 4.8, Figure 4.9, Figure 4.10
- **Inputs:** manta_tiddit.intersect.cohort.annotated.vcf (filtered); sv_dashboard_helpers.R; annotsv_column_descriptions.tsv; www/
- **Outputs:** results_dashboard_final/ (screenshots, HTML/CSV/XLSX exports)
- **Run record:** none (no sessionInfo saved)
- **Run for the dissertation:** 2026-10-08
- **Previous name:** `protegerna_github_code_oct2026/02_sv_analysis/05_dashboard/proteGErna-SV.R`

```bash
Rscript -e 'shiny::runApp("06_dashboard/proteGErna-SV.R", launch.browser = TRUE)'   # then upload the filtered intersection annotated VCF
```

Requires R ≥ 4.6 with shiny 1.14.0, shinydashboard 0.7.3, DT 0.34.0, vcfR 1.16.0, shinyjs 2.1.1, httr 1.4.8 and jsonlite 2.0.0.

`results_dashboard_final/` holds the screenshots and exports used for Figures 4.5–4.10. The four `127.0.0.1_4919_*.png` files are
unnamed screenshots; the cropped panel in Figure 4.7 is not saved.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
