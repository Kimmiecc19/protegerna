# Objective 2: Structural-variant workflow

**Folder:** [`02_SV_analysis/`](https://github.com/Kimmiecc19/protegerna/tree/main/02_SV_analysis)
**Dissertation:** Chapter 4, *From breakpoints to biological candidates: a reproducible structural-variant interpretation
workflow* (methods 4.2, results 4.3, Appendix 4A)

## Overview

**Objective:** develop a reproducible workflow for structural variant (SV) analysis and interactive interpretation, with
ALS-informed candidate nomination.

**Research question:** Can SV detection, consolidation, annotation, ALS-informed nomination and interactive exploration be
combined into one reproducible workflow for short-read genomes? How concordant are the calls of different callers, and does
the workflow recover known ALS-associated SVs?

```text
347 matched Answer ALS genomes (CRAM)
  01_sv_calling          nf-core/sarek 3.5.1: Manta + TIDDIT per participant
  02_sv_consolidation    OctopuSV: PASS, 50–100,000 bp; per-participant intersection and union; cohort merge
  03_sv_annotation       ALSoD 154-gene list; AnnotSV 3.5.8, gene-filtered and unfiltered
  04_sv_prioritization   callset statistics; event consolidation, nomination and review tiers
  05_sv_audit            raw-call review of shortlisted events; audited release (24 primary candidates) + verification
  06_dashboard           proteGErna-SV Shiny dashboard
```

The audited candidates and event tables feed into [Objective 4](Objective-4-Multi-Omics-Integration).

> **Read [Structural-variant workflow: design logic](SV-Workflow-Design-Logic) first** if you want to understand why the
> workflow calls, consolidates, nominates and audits SVs as it does, what it deliberately leaves out, and how to read its
> candidates.

## Installation

| Tool | Version | Steps |
| --- | --- | --- |
| Nextflow + nf-core/sarek (Apptainer) | Sarek 3.5.1; Manta 1.6.0; TIDDIT 3.6.1 | 01 |
| OctopuSV, bcftools | OctopuSV 0.3.5 | 02 |
| AnnotSV | 3.5.8 with GRCh38 annotations | 03 |
| Python 3 | pandas, numpy, requests, beautifulsoup4 (01, 03); the rest use the standard library | 01, 03–05 |
| R 4.6.1 | shiny, shinydashboard, DT, vcfR, shinyjs, httr, jsonlite, ggplot2, dplyr, tidyr, stringr, purrr, readr, scales, patchwork, data.table | 02, 06 |

See [Installation](Installation) for install commands and exact R package versions.

## Inputs required

| Data | Step | Source / notes |
| --- | --- | --- |
| WGS CRAM + CRAI, 347 participants | 01 | Answer ALS portal (controlled access). Cohort list from [Cohort preparation](Cohort-Preparation). |
| `GRCh38_full_analysis_set_plus_decoy_hla.fa` (+ `.fai`) | 01, 05 | 1000 Genomes; the reference the CRAMs were made with |
| dbSNP 138, known indels; snpEff GRCh38.105; VEP 112 caches | 01 | Paths in `01_sv_calling/aals_sarek.json` |
| ALSoD gene table (accessed 24 Feb 2026); Ensembl 112 REST | 03 | Downloaded by `01_build_alsod_gene_map.py`. Keep the saved `alsod_gene_list.csv`. |
| AnnotSV 3.5.8 annotation folder (GRCh38) | 03 | Installed with AnnotSV |
| `data/sarek_metadata_stats.tsv` | 04 | `04_sv_prioritization/data/` |
| STRchive disease loci (hg38 BED) | 05 | `04_sv_prioritization/data/` |
| Per-participant raw Manta/TIDDIT VCFs | 05 | Written by Sarek in step 01 (not in the repository) |

## Running

Run the steps in order. Commands are run from the step folder. Repository inputs and outputs are found automatically.
Data and tools outside the repository are set as environment variables (shown below with `/path/to/...` values).
`$FI` and `$FU` are shorthand for the saved filtered AnnotSV tables:

```bash
A=../03_sv_annotation/02a_results_annotsv_filtered
FI=$A/octopusv_intersect_cohort_filtered_05102026/manta_tiddit.intersect.cohort.annotated
FU=$A/octopusv_union_cohort_filtered_05102026/manta_tiddit.union.cohort.annotated
```

### Step 01: SV calling with nf-core/sarek

```bash
cd 02_SV_analysis/01_sv_calling

# 1. Split the 347 participants into 14 samplesheets -> 01_results_sarek_samplesheet/
python 01_create_samplesheet_batches_sarek.py /path/to/cram sarek_samplesheet

# 2. Set the reference paths in aals_sarek.config and aals_sarek.json first. Then, once per samplesheet (N = 1..14):
SAREK_OUTDIR=/path/to/sarek_results bash 03_run_aals_sarek.sh N

# 3. Optional: summarise resource use
python 02_analyse_resources_sarek.py -i /path/to/sarek_results -p sarek_
```

### Step 02: Caller harmonisation and cohort consolidation (OctopuSV)

```bash
cd 02_SV_analysis/02_sv_consolidation
bash 01_octopusv_manta_tiddit.sh --input-dir /path/to/sarek_results --out-dir 01_results_octopusv \
  --min-svlen 50 --max-svlen 100000

GRCH38_FAI=/path/to/GRCh38_full_analysis_set_plus_decoy_hla.fa.fai Rscript 02a_octopusv_stats_plots.R
Rscript 02b_sv_workflow_figures.R    # run after steps 04 and 05
```

The dissertation palette is found automatically in `01_biotools_landscape/03_helpers/`.

### Step 03: ALS gene list and AnnotSV annotation

```bash
cd 02_SV_analysis/03_sv_annotation
python 01_build_alsod_gene_map.py --out-dir 01_results_build_alsod_gene_map

export ANNOTSV_BIN_DIR=/path/to/AnnotSV/bin
export ANNOTATIONS=/path/to/AnnotSV/share/AnnotSV
bash 02a_run_annotsv_filtered.sh     # -> 02a_results_annotsv_filtered/*_05102026
bash 02b_run_annotsv_unfiltered.sh   # -> 02b_results_annotsv_unfiltered/*_03102026
```

Defaults: input `../02_sv_consolidation/01_results_octopusv/merged`, gene list
`../04_sv_prioritization/data/ALS_candidate_gene_list.txt`.

### Step 04: Callset statistics and event prioritisation

```bash
cd 02_SV_analysis/04_sv_prioritization

# Callset QC: run four times (intersect/union × filtered/unfiltered)
python 01_summarise_callset_qc.py -v $FI.vcf \
  -o 01_results_summarise_callset_qc/intersect_filtered_annotated/intersect_filtered_annotated \
  --caller manta_tiddit --callset intersect_filtered_annotsv --filter-policy all --genotypes caller-reported

# Prioritisation
ALSOD=../03_sv_annotation/01_results_build_alsod_gene_map/alsod_gene_list.csv
python 02c_prioritise_annotsv_events.py --mode intersection --intersection-vcf $FI.vcf \
  --alsod-csv $ALSOD --out-dir 02c_results_prioritise_annotsv_events/intersection_filtered
python 02c_prioritise_annotsv_events.py --mode union-only --intersection-vcf $FI.vcf --union-vcf $FU.vcf \
  --alsod-csv $ALSOD --out-dir 02c_results_prioritise_annotsv_events/union_only_filtered
# Repeat both with the unfiltered tables (../03_sv_annotation/02b_results_annotsv_unfiltered/*_03102026)

# Participant-level SV table (defaults read the saved AnnotSV tables)
python 03_build_participant_sv_table.py --mode all
python 03_build_participant_sv_table.py --mode filtered
```

`02a_extract_alsod.py` and `02b_gene_to_ensembl.py` rebuild the ALSoD gene list. Use the saved list to reproduce the
dissertation.

### Step 05: Raw-call review and audited release

```bash
cd 02_SV_analysis/05_sv_audit

# Reheader the per-participant Sarek VCFs -> 01a_fixed_vcf_names/fixed_vcf_names/ (participant data: do not commit)
bash 01a_prep_sarek_for_review.sh /path/to/sarek_results/part*/variant_calling

# One run per set: intersection/union_only × filtered/unfiltered (union runs use --union-tsv)
python 01b_extract_raw_calls.py \
  --intersection-tsv ../04_sv_prioritization/02c_results_prioritise_annotsv_events/intersection_filtered/Supplementary_Table_intersection_manual_review_shortlist.tsv \
  --input-dir 01a_fixed_vcf_names/fixed_vcf_names --vcf-glob '*.vcf.gz' \
  --out-dir 01bc_results_raw_call_review/intersection_filtered --padding 500 --min-ro 0.5

python 01c_score_raw_call_evidence.py --input-dir 01bc_results_raw_call_review/intersection_filtered \
  --str-bed ../04_sv_prioritization/data/STRchive-disease-loci.hg38.general.bed \
  --intersection-annotsv-files $FI.tsv
# defaults: --min-split 3 --min-pairs 3 --del-max-ratio 0.75 --dup-min-ratio 1.25 --max-lq 0.3 --case-n 296 --control-n 51

python 02a_build_audited_release.py --input-dir 01bc_results_raw_call_review/intersection_filtered \
  --intersection-annotations $FI.tsv --union-annotations $FU.tsv --out-dir 02_results_audited_release

python 02b_verify_audited_release.py --out-dir 02_results_audited_release \
  --input-dir 01bc_results_raw_call_review/intersection_filtered
```

### Step 06: proteGErna-SV dashboard

```bash
Rscript -e 'shiny::runApp("02_SV_analysis/06_dashboard/proteGErna-SV.R", launch.browser = TRUE)'
```

Then upload the filtered intersection annotated VCF (`manta_tiddit.intersect.cohort.annotated.vcf`). The dashboard lets you
filter SVs, look up genes in external resources, read column descriptions and export the filtered table as HTML, CSV or XLSX.

## Expected outputs

| Step | Output | Description |
| --- | --- | --- |
| 01 | `01_results_sarek_samplesheet/sarek_samplesheet_part_{1..14}.csv` | Sarek samplesheets |
| 01 | `<SAREK>/partN/variant_calling/` | Per-participant Manta and TIDDIT VCFs (server only) |
| 02 | `01_results_octopusv/{merged,stats,plots,circos}/` | Cohort `manta_tiddit.{intersect,union}.cohort.vcf` and caller-specific callsets; SV-type counts (Table 4.5) |
| 02 | `02b_sv_workflow_figures/{figures,tables,cache}/` | Figures 4.3, 4.4, 4A.2 |
| 03 | `01_results_build_alsod_gene_map/` | `alsod_gene_list.csv`, `alsod_gene_transcript_map_gencode_v46.csv`, `ALS_candidate_gene_list.txt` |
| 03 | `02a_results_annotsv_filtered/`, `02b_results_annotsv_unfiltered/` | `*.annotated.{tsv,vcf}` for intersect and union callsets |
| 04 | `01_results_summarise_callset_qc/` | Callset statistics (Tables 4.6–4.8) and `*.manifest.json` |
| 04 | `02c_results_prioritise_annotsv_events/{intersection,union_only}_{filtered,unfiltered}/` | Event prioritisation tables, manual-review shortlists, review tiers (Tables 4.2, 4.9, 4A.3, 4A.4, 4A.6), `*_prioritisation_summary.json` |
| 04 | `03_results_build_participant_sv_table/` | `intersection_SVs_347_participants[_filtered].{tsv,README.md,validation.json}` |
| 05 | `01bc_results_raw_call_review/<set>/` | `review_events.tsv`, `raw_record_matches.tsv`, `carrier_status.tsv`, `evidence_per_{record,carrier,event}.tsv`, `evidence_summary.tsv`, `run_log.json`, `evidence_thresholds.json` |
| 05 | `02_results_audited_release/` | `audited_candidates`, **`primary_candidates`** (24), **`participant_support`**, `integration_pairs`, `matching_sensitivity`, `summary.json`, `verification.json` (Tables 4.10–4.12, 4A.2, 4A.5) |
| 06 | `results_dashboard_final/` | Screenshots and HTML/CSV/XLSX exports (Figures 4.5–4.10) |

**Handed to Objective 4:** `manta_tiddit.intersect.cohort.vcf`, the four AnnotSV event-prioritisation tables,
`primary_candidates.tsv` and `participant_support.tsv`.

## Before you run / known issues

- Values to set before running (everything else defaults to the repository):

  | Script | Setting | What it is |
  | --- | --- | --- |
  | `aals_sarek.config`, `aals_sarek.json` | `fasta`, `fasta_fai`, `dict`, `cacheDir`, `known_snps`, `known_indels`, `snpeff_cache`, `vep_cache`, … | Reference files and container cache |
  | `03_run_aals_sarek.sh` | `SAREK_OUTDIR` (optional `SAREK_PIPELINE`, `SAMPLESHEET`) | Where Sarek writes the per-participant VCFs |
  | `02a_octopusv_stats_plots.R` | `GRCH38_FAI` or second argument | Reference FASTA index |
  | `02a/02b_run_annotsv_*.sh` | `ANNOTSV_BIN_DIR`, `ANNOTATIONS` | AnnotSV 3.5.8 install and annotations |
  | `01a_prep_sarek_for_review.sh` | VCF folders as arguments, or `INPUT_DIR_GLOB` | Raw per-participant Sarek VCFs |

- `figures/make_chapter4_figures.R` and `figures/sv_thesis_style.R` are copies of `02b_sv_workflow_figures.R` and
  `02_sv_thesis_style.R`, and both work from either location.
- The prioritisation tables were re-run on 7 Nov 2026 after a gene-symbol case fix (EphA3). The release and dashboard were not
  affected.

## Dissertation map

| Item | Script(s) |
| --- | --- |
| Table 4.1 (AnnotSV score classes) | `03_sv_annotation/02a_run_annotsv_filtered.sh` |
| Table 4.2 (review tiers) | `04_sv_prioritization/02c_prioritise_annotsv_events.py` |
| Table 4.3 | `04/01_summarise_callset_qc.py`, `04/02c_...`, `05/02a_build_audited_release.py` |
| Table 4.4 (cohort) | `00_general/01_filtering_matching_patients/*.R` |
| Table 4.5 | `02_sv_consolidation/01_octopusv_manta_tiddit.sh` |
| Tables 4.6–4.8 | `04_sv_prioritization/01_summarise_callset_qc.py` |
| Table 4.9 | `04_sv_prioritization/02c_prioritise_annotsv_events.py` |
| Table 4.10 | `05_sv_audit/01b_extract_raw_calls.py`, `01c_score_raw_call_evidence.py` |
| Tables 4.11–4.12 | `05_sv_audit/02a_build_audited_release.py`, `02b_verify_audited_release.py` |
| Figures 4.3, 4.4, 4A.2 | `02_sv_consolidation/02b_sv_workflow_figures.R` |
| Figures 4.5–4.10 | `06_dashboard/proteGErna-SV.R` |
| Appendix 4A tables | See the [folder README](https://github.com/Kimmiecc19/protegerna/blob/main/02_SV_analysis/README.md#script-to-dissertation-map) |

Each step folder README lists inputs, outputs and run records for every script.

## Key literature

The published work behind this method, and what each work justifies, is listed in
[Literature and method justification](Literature-and-Method-Justification#objective-2-structural-variants).
