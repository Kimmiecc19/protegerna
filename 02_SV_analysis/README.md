# Objective Two: structural-variant workflow (Chapter 4)

**Objective:** develop a reproducible workflow for structural variant (SV) analysis and interactive interpretation with
ALS-informed candidate nomination.

**Research question:** Can SV detection, consolidation, annotation, ALS-informed nomination and interactive exploration be combined
into one reproducible workflow for short-read genomes? How concordant are its calls between callers, and does it recover known
ALS-associated SVs?

**Dissertation:** Chapter 4, *From breakpoints to biological candidates: a reproducible structural-variant interpretation
workflow* (methods 4.2, results 4.3, Appendix 4A). The audited candidates and event tables are inputs to Objective Four.

## What is done

```text
347 matched Answer ALS genomes (CRAM)
  01_sv_calling          nf-core/sarek 3.5.1: Manta + TIDDIT per participant
  02_sv_consolidation    OctopuSV: PASS, 50–100,000 bp; per-participant intersection and union; cohort merge
  03_sv_annotation       ALSoD 154-gene list; AnnotSV 3.5.8, gene-filtered and unfiltered
  04_sv_prioritization   callset statistics; event consolidation, nomination and review tiers
  05_sv_audit            raw-call review of shortlisted events; audited release (24 primary candidates) + verification
  06_dashboard           proteGErna-SV Shiny dashboard
```

## Steps

| Step | What it does | Dissertation |
| --- | --- | --- |
| [`01_sv_calling`](01_sv_calling/README.md) | Sarek samplesheets and SV calling | 4.2.3 |
| [`02_sv_consolidation`](02_sv_consolidation/README.md) | OctopuSV harmonisation and merging; Chapter 4 callset figures | 4.2.4, 4.3.3; Table 4.5; Figures 4.3, 4.4, 4A.1, 4A.2 |
| [`03_sv_annotation`](03_sv_annotation/README.md) | ALS gene list; AnnotSV annotation | 4.2.5 |
| [`04_sv_prioritization`](04_sv_prioritization/README.md) | Callset statistics; prioritisation and tiers | 4.2.6–4.2.8, 4.3.2–4.3.5; Tables 4.3, 4.6–4.9, 4A.3, 4A.4, 4A.6 |
| [`05_sv_audit`](05_sv_audit/README.md) | Raw-call review; audited release; verification | 4.2.9, 4.3.6–4.3.7; Tables 4.10–4.12, 4A.2, 4A.5 |
| [`06_dashboard`](06_dashboard/README.md) | proteGErna-SV dashboard | 4.2.10, 4.3.8, Appendix 4A.6; Figures 4.5–4.7, 4A.3–4A.5 |

Run the steps in order. Each step folder has its own README with the command used for every script, its inputs and outputs, and
what must be edited before running. Results are kept next to the scripts in folders named `NN_results_<script>`.

The cohort (347 participants, Table 4.4) comes from `../00_general/01_filtering_matching_patients/`.

## Data required

| Data | Step | Source / notes |
| --- | --- | --- |
| WGS CRAM + CRAI, 347 participants | 01 | Answer ALS data portal (controlled access). Aligned and duplicate-marked by Answer ALS. |
| `GRCh38_full_analysis_set_plus_decoy_hla.fa` (+ `.fai`) | 01, 05 | 1000 Genomes; the reference the CRAMs were made with |
| dbSNP 138, known indels; snpEff GRCh38.105; VEP 112 caches | 01 | Paths in `01_sv_calling/aals_sarek.json` |
| ALSoD gene table (accessed 24 Feb 2026); Ensembl 112 REST | 03 | Downloaded by `01_build_alsod_gene_map.py`; keep the saved `alsod_gene_list.csv` |
| AnnotSV 3.5.8 annotation folder (GRCh38) | 03 | Installed with AnnotSV |
| STRchive disease loci (hg38 BED) | 05 | `04_sv_prioritization/data/` |
| Per-participant raw Manta/TIDDIT VCFs | 05 | Written by Sarek in step 01 (not in the repository) |

## Software

| Tool | Version | Steps |
| --- | --- | --- |
| Nextflow + nf-core/sarek (Apptainer) | Sarek 3.5.1; Manta 1.6.0; TIDDIT 3.6.1 | 01 |
| OctopuSV, bcftools | OctopuSV 0.3.5 | 02 |
| AnnotSV | 3.5.8 | 03 |
| Python 3 | pandas, numpy, requests, beautifulsoup4 (01, 03); others use the standard library | 01, 03–05 |
| R 4.6.1 | shiny 1.14.0, shinydashboard 0.7.3, DT 0.34.0, vcfR 1.16.0, shinyjs 2.1.1, httr 1.4.8, jsonlite 2.0.0; ggplot2, dplyr, tidyr, stringr, purrr, readr, scales, patchwork, data.table | 02, 06 |

## Script-to-dissertation map

Figures 4.1 and 4.2 are schematics; Table 4.1 is the AnnotSV scoring reference (`03_sv_annotation/data/`); Table 4A.1 comes from
Objective One.

| Item | Caption | Script(s) | Status |
| --- | --- | --- | --- |
| Table 4.1 | AnnotSV ranking-score classes, adapted from the ACMG/ClinGen CNV scoring framework | `03_sv_annotation/02a_run_annotsv_filtered.sh` | Saved |
| Table 4.2 | Manual-review tiers assigned to nominated events | `04_sv_prioritization/02c_prioritise_annotsv_events.py` | Saved |
| Table 4.3 | Accounting chain from eligible callset records to exported participant–candidate pairs | `04_sv_prioritization/01_summarise_callset_qc.py`, `04_sv_prioritization/02c_prioritise_annotsv_events.py`, `05_sv_audit/02a_build_audited_release.py` | Saved |
| Table 4.4 | Participants in the Answer ALS cohort before and after omics matching and filtering | `00_general/01_filtering_matching_patients/04_aals_full_merge.R`, `00_general/01_filtering_matching_patients/01_participant_filtering.R`, `00_general/01_filtering_matching_patients/02_merged_tp_mapping.R` | Saved |
| Table 4.5 | Structural variant type counts reported in OctopuSV results | `02_sv_consolidation/01_octopusv_manta_tiddit.sh` | Saved |
| Table 4.6 | Filtering of OctopuSV cohort records | `04_sv_prioritization/01_summarise_callset_qc.py` | Saved |
| Table 4.7 | Comparison of structural variant statistics for the unfiltered and filtered Manta–TIDDIT union and intersection callsets | `04_sv_prioritization/01_summarise_callset_qc.py` | Saved |
| Table 4.8 | High-frequency events in the filtered union callset | `04_sv_prioritization/01_summarise_callset_qc.py` | Saved |
| Table 4.9 | AnnotSV classes for filtered callsets | `04_sv_prioritization/02c_prioritise_annotsv_events.py` | Saved |
| Table 4.10 | Nominations moved to tier 4 after recounting carriers from raw calls | `05_sv_audit/01b_extract_raw_calls.py`, `05_sv_audit/01c_score_raw_call_evidence.py` | Saved |
| Table 4.11 | Primary research candidates in the audited release | `05_sv_audit/02a_build_audited_release.py` | Saved |
| Table 4.12 | Final decisions for the 50 original intersection nominations | `05_sv_audit/02a_build_audited_release.py`, `05_sv_audit/02b_verify_audited_release.py` | Saved |
| Figure 4.1 | Overview of the structural-variant workflow | Schematic | Saved |
| Figure 4.2 | OctopuSV workflow for caller-specific and integrated cohort structural variant callsets | `02_sv_consolidation/01_octopusv_manta_tiddit.sh` | Schematic |
| Figure 4.3 | Agreement between each caller and the caller intersection by SV type and length | `02_sv_consolidation/02b_sv_workflow_figures.R` | Saved |
| Figure 4.4 | Final audit decisions for the 50 prioritised structural variants | `02_sv_consolidation/02b_sv_workflow_figures.R`, `05_sv_audit/02a_build_audited_release.py` | Saved |
| Figure 4.5 | proteGErna-SV dashboard before data import | `06_dashboard/proteGErna-SV.R` | Saved |
| Figure 4.6 | Overview of the dashboard after importing the candidate-gene-filtered AnnotSV intersection VCF | `06_dashboard/proteGErna-SV.R` | Saved |
| Figure 4.7 | Structural variants view with an example filter applied | `06_dashboard/proteGErna-SV.R` | Partly saved |
| Table 4A.1 | Tools used in the structural-variant workflow and their outcome in the Objective One screen | `01_biotools_landscape/02a_filter_biotools.R` | Saved |
| Table 4A.2 | Raw-call review outcomes for intersection and union-only nominations under the review-stage evidence rule | `05_sv_audit/01b_extract_raw_calls.py`, `05_sv_audit/01c_score_raw_call_evidence.py` | Saved |
| Table 4A.3 | Illustrative filtered intersection nominations before the raw-call audit | `04_sv_prioritization/02c_prioritise_annotsv_events.py` | Saved |
| Table 4A.4 | Illustrative filtered union-only nominations after AnnotSV prioritisation | `04_sv_prioritization/02c_prioritise_annotsv_events.py` | Saved |
| Table 4A.5 | Matching sensitivity of the audited release for the 50 filtered intersection nominations | `05_sv_audit/02a_build_audited_release.py` | Saved |
| Table 4A.6 | Nominations by callset and annotation run before technical review | `04_sv_prioritization/02c_prioritise_annotsv_events.py` | Saved |
| Figure 4A.1 | Structural variant type counts reported in OctopuSV results | `02_sv_consolidation/01_octopusv_manta_tiddit.sh` | Saved |
| Figure 4A.2 | Length distribution of structural variants by callset and SV type | `02_sv_consolidation/02b_sv_workflow_figures.R` | Saved |
| Figure 4A.3 | HTML export of the filtered structural variant table | `06_dashboard/proteGErna-SV.R` | Saved |
| Figure 4A.4 | Resource search view for the gene SOD1 | `06_dashboard/proteGErna-SV.R` | Saved |
| Figure 4A.5 | Column descriptions view | `06_dashboard/proteGErna-SV.R` | Saved |

## Reproducibility notes

- Each run writes a record next to its results: AnnotSV logs, `*.manifest.json` (callset QC), `*_prioritisation_summary.json`
  (inputs with SHA-256), `run_log.json` and `evidence_thresholds.json` (raw-call review), `input_checksums.json`,
  `release_parameters.json` and `verification.json` (audited release).
- The prioritisation tables were re-run on 7 Nov 2026 after a gene-symbol case fix (EphA3); the release and dashboard were not
  affected.
- Scripts resolve repository files from their own location. Data and tools that are not in the repository (CRAMs, raw
  VCFs, reference files, the AnnotSV install, container caches) are set in a **Settings** block at the top of each launcher,
  each overridable with an environment variable and shown as a `/path/to/...` placeholder until you set it.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
