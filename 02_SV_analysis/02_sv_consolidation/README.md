# 02 Caller harmonisation and cohort consolidation (OctopuSV)

**Objective:** Objective Two: a reproducible workflow for structural-variant (SV) detection, consolidation, annotation, ALS-informed nomination and interactive exploration.  
**Dissertation:** Chapter 4, Sections 4.2.4 and 4.3.3; tables and figures: Table 4.5, Figure 4.2, Figure 4.3, Figure 4.4, Figure 4A.1, Figure 4A.2  
**Back to:** [objective README](../README.md)

## What this step does

Converts Manta and TIDDIT calls to a common format with OctopuSV 0.3.5 (PASS records, 50–100,000 bp), builds a per-participant
intersection (called by both callers) and union, merges participants into cohort VCFs, and writes OctopuSV statistics. The R
scripts draw the Chapter 4 callset figures.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_octopusv_manta_tiddit.sh` | OctopuSV clean/correct (PASS, 50–100,000 bp), per-participant caller intersection/union, cohort merge, stats | Table 4.5, Figure 4.2, Figure 4A.1 |
| `02a_octopusv_stats_plots.R` | OctopuSV callset figures (SV types) | Sections 4.2.4, 4.3.3 |
| `02b_sv_workflow_figures.R` | Chapter 4 figures: length spectrum, caller concordance, audit disposition | Figure 4.3, Figure 4.4, Figure 4A.2 |

## Order of running

1. `01_octopusv_manta_tiddit.sh` (writes `01_results_octopusv/merged/manta_tiddit.{intersect,union}.cohort.vcf`).
2. `02b_sv_workflow_figures.R` after steps 04 and 05 have finished (it also reads the prioritisation and audit outputs).
3. `02a_octopusv_stats_plots.R` is optional; the dissertation uses the OctopuSV `stat` panels for Figure 4A.1.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_octopusv_manta_tiddit.sh`

OctopuSV clean/correct (PASS, 50–100,000 bp), per-participant caller intersection/union, cohort merge, stats.

- **Dissertation:** Section 4.2.4; Table 4.5, Figure 4.2, Figure 4A.1
- **Inputs:** per-participant Manta and TIDDIT VCFs (O2-02)
- **Outputs:** 01_results_octopusv/{merged,stats,plots,circos}/
- **Run record:** none (merged VCFs dated 02 Sep 2026 on the server: octopusv_merged_02092026)
- **Run for the dissertation:** 2026-09-02
- **Note:** A dated copy (octopusv_manta_tiddit_27082026.sh) was a duplicate.

```bash
bash 01_octopusv_manta_tiddit.sh --input-dir <SAREK> --out-dir 01_results_octopusv --min-svlen 50 --max-svlen 100000
```

### `02a_octopusv_stats_plots.R`

OctopuSV callset figures (SV types).

- **Dissertation:** Sections 4.2.4, 4.3.3
- **Inputs:** 01_results_octopusv/stats/*.stats.txt; reference .fai
- **Outputs:** <out_dir>/figures, <out_dir>/tables (default 01_results_octopusv/thesis_figures)
- **Before running:** Defaults: `stats_dir` = `01_results_octopusv/stats`, `out_dir` = `01_results_octopusv/thesis_figures`. The reference index is not in the repository: pass it as the second argument or set `GRCH38_FAI`. The palette is found automatically in `01_biotools_landscape/03_helpers/` (or set `THESIS_PALETTE`).
- **Note:** Figure 4A.1 panels in the repo come from octopusv stat (01_results_octopusv/stats/*_sv_types.png).

```bash
GRCH38_FAI=/path/to/GRCh38_full_analysis_set_plus_decoy_hla.fa.fai Rscript 02a_octopusv_stats_plots.R   # or: Rscript 02a_octopusv_stats_plots.R [stats_dir] [fai] [out_dir]
```

### `02b_sv_workflow_figures.R`

Chapter 4 figures: length spectrum, caller concordance, audit disposition.

- **Dissertation:** Sections 4.2.4, 4.3.3, 4.3.7; Figure 4.3, Figure 4.4, Figure 4A.2
- **Inputs:** 01_results_octopusv/merged/*.vcf; 02c prioritisation summaries; 05_sv_audit/02_results_audited_release
- **Outputs:** 02b_sv_workflow_figures/{figures,tables,cache}/
- **Before running:** Run after steps 04 and 05. Reads `01_results_octopusv/`, `../04_sv_prioritization/02c_results_prioritise_annotsv_events/` and `../05_sv_audit/02_results_audited_release/` and writes to `02b_sv_workflow_figures/` by default; the palette is found automatically.
- **Note:** figures/make_chapter4_figures.R is a copy of this script; 02_sv_thesis_style.R is its style helper.

```bash
Rscript 02b_sv_workflow_figures.R   # or: Rscript 02b_sv_workflow_figures.R [sv_dir] [out_dir]
```

### Helper files

- `02_sv_thesis_style.R` – figure theme; loads the dissertation palette from `01_biotools_landscape/03_helpers/thesis_palette.R` (override with `THESIS_PALETTE`).
- `figures/make_chapter4_figures.R` and `figures/sv_thesis_style.R` are copies of `02b_sv_workflow_figures.R` and `02_sv_thesis_style.R` and can be deleted.

**Next step:** [`03_sv_annotation`](../03_sv_annotation/README.md) annotates the two cohort VCFs.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
