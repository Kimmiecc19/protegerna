# 04 Callset statistics and event prioritisation

**Objective:** Objective Two: a reproducible workflow for structural-variant (SV) detection, consolidation, annotation, ALS-informed nomination and interactive exploration.  
**Dissertation:** Chapter 4, Sections 4.2.6–4.2.8 and 4.3.2–4.3.5; tables and figures: Table 4.2, Table 4.3, Table 4.6, Table 4.7, Table 4.8, Table 4.9, Table 4A.3, Table 4A.4, Table 4A.6  
**Back to:** [objective README](../README.md)

## What this step does

Summarises each annotated callset (record counts, size bins, filters, carrier counts and recurrence), consolidates the AnnotSV
rows of each event, nominates events in ALSoD Definitive/Strong/Moderate genes or with an AnnotSV score of at least 0.9, and
assigns manual-review tiers (Table 4.2). The union run reports only events that are not in the intersection (union-only).
`03_build_participant_sv_table.py` writes one row per carrier and intersection event for reference.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_summarise_callset_qc.py` | Per-VCF record statistics, size bins, filter counts, carrier counts and event recurrence | Table 4.3, Table 4.6, Table 4.7, Table 4.8 |
| `02c_prioritise_annotsv_events.py` | Consolidate AnnotSV rows per event, nominate (ALSoD Definitive/Strong/Moderate or AnnotSV score ≥ 0.9), assign review tiers | Table 4.2, Table 4.3, Table 4.9, Table 4A.3, Table 4A.4, Table 4A.6 |
| `03_build_participant_sv_table.py` | One row per carrier and intersection event (reference table only | Section 4.2.6 |
| `02a_extract_alsod.py` | Earlier ALSoD gene-table download (superseded by 03_sv_annotation/01_build_alsod_gene_map.py) | Section 4.2.5 |
| `02b_gene_to_ensembl.py` | Earlier Ensembl ID lookup for the ALSoD genes (superseded by 01_build_alsod_gene_map.py) | Section 4.2.5 |

## Order of running

1. `01_summarise_callset_qc.py` on each of the four annotated VCFs.
2. `02c_prioritise_annotsv_events.py`: intersection, then union-only, for filtered and unfiltered annotations (four runs).
3. `03_build_participant_sv_table.py` (optional reference table).
`02a_extract_alsod.py` and `02b_gene_to_ensembl.py` are the earlier ALSoD scripts and do not need to be run.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_summarise_callset_qc.py`

Per-VCF record statistics, size bins, filter counts, carrier counts and event recurrence.

- **Dissertation:** Section 4.2.6; Table 4.3, Table 4.6, Table 4.7, Table 4.8
- **Inputs:** the four AnnotSV-annotated VCFs (O2-08, O2-09); data/sarek_metadata_stats.tsv
- **Outputs:** 01_results_summarise_callset_qc/{intersect,union}_{filtered,unfiltered}_annotated/
- **Run record:** 01_results_summarise_callset_qc/*/*.manifest.json (settings and inputs)
- **Run for the dissertation:** 2026-10
- **Previous name:** `01_sv_qc_analysis.py / sv_qc_analysis.py`
- **Note:** Manifests show the server version also took --metadata and --rarity options that the current script no longer has.

```bash
# run once per callset: <set> = intersect_filtered / union_filtered / intersect_unfiltered / union_unfiltered
python 01_summarise_callset_qc.py -v ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_intersect_cohort_filtered_05102026/manta_tiddit.intersect.cohort.annotated.vcf -o 01_results_summarise_callset_qc/intersect_filtered_annotated/intersect_filtered_annotated --caller manta_tiddit --callset intersect_filtered_annotsv --filter-policy all --genotypes caller-reported
```

### `02c_prioritise_annotsv_events.py`

Consolidate AnnotSV rows per event, nominate (ALSoD Definitive/Strong/Moderate or AnnotSV score ≥ 0.9), assign review tiers.

- **Dissertation:** Sections 4.2.7–4.2.8; 6.2.7; Table 4.2, Table 4.3, Table 4.9, Table 4A.3, Table 4A.4, Table 4A.6
- **Inputs:** annotated VCFs (05102026 filtered, 03102026 unfiltered); alsod_gene_list.csv
- **Outputs:** 02c_results_prioritise_annotsv_events/{intersection,union_only}_{filtered,unfiltered}/
- **Run record:** *_prioritisation_summary.json (inputs with SHA-256)
- **Run for the dissertation:** 2026-11-07 (EphA3 case fix re-run)
- **Previous name:** `02_annotsv_prioritization.py / build_annotsv_prioritization.py`
- **Note:** Event tables are inputs to Chapter 6 (01e scan, evaluation table).

```bash
python 02c_prioritise_annotsv_events.py --mode intersection --intersection-vcf ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_intersect_cohort_filtered_05102026/manta_tiddit.intersect.cohort.annotated.vcf --alsod-csv ../03_sv_annotation/01_results_build_alsod_gene_map/alsod_gene_list.csv --out-dir 02c_results_prioritise_annotsv_events/intersection_filtered
python 02c_prioritise_annotsv_events.py --mode union-only --intersection-vcf ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_intersect_cohort_filtered_05102026/manta_tiddit.intersect.cohort.annotated.vcf --union-vcf ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_union_cohort_filtered_05102026/manta_tiddit.union.cohort.annotated.vcf --alsod-csv ../03_sv_annotation/01_results_build_alsod_gene_map/alsod_gene_list.csv --out-dir 02c_results_prioritise_annotsv_events/union_only_filtered
# repeat both with the unfiltered VCFs (../03_sv_annotation/02b_results_annotsv_unfiltered/...03102026) -> intersection_unfiltered, union_only_unfiltered
```

### `03_build_participant_sv_table.py`

One row per carrier and intersection event (reference table only; 6,707 carrier calls for 185 filtered records).

- **Dissertation:** Section 4.2.6
- **Inputs:** intersection annotated TSVs (05102026 filtered, 03102026 unfiltered); ALS_candidate_gene_list.txt
- **Outputs:** 03_results_build_participant_sv_table/intersection_SVs_347_participants[_filtered].{tsv,README.md,validation.json}
- **Run record:** *.validation.json (sources with SHA-256)
- **Run for the dissertation:** 2026-10
- **Previous name:** `02_build_participant_sv_table.py / build_participant_intersection_table.py`
- **Before running:** Defaults read the saved AnnotSV tables (`../03_sv_annotation/02a_results_annotsv_filtered/...05102026`, `../03_sv_annotation/02b_results_annotsv_unfiltered/...03102026`) and `data/ALS_candidate_gene_list.txt`, and write to `03_results_build_participant_sv_table/`.
- **Note:** Import fixed on 8 Nov 2026 (now imports 02c_prioritise_annotsv_events); filtered output re-run and matched the saved TSV.

```bash
python 03_build_participant_sv_table.py --mode all
python 03_build_participant_sv_table.py --mode filtered
```

### `02a_extract_alsod.py`

Earlier ALSoD gene-table download (superseded by 03_sv_annotation/01_build_alsod_gene_map.py).

- **Dissertation:** Section 4.2.5
- **Inputs:** https://alsod.ac.uk
- **Outputs:** 02ab_results_alsod_gene_list/
- **Run for the dissertation:** 2026-02-24
- **Previous name:** `extract_alsod.py`
- **Note:** Kept because 02ab_results_alsod_gene_list/ came from it; the combined script gives the same gene list.

```bash
python 02a_extract_alsod.py
```

### `02b_gene_to_ensembl.py`

Earlier Ensembl ID lookup for the ALSoD genes (superseded by 01_build_alsod_gene_map.py).

- **Dissertation:** Section 4.2.5
- **Inputs:** alsod_gene_list.csv; Ensembl REST
- **Outputs:** 02ab_results_alsod_gene_list/
- **Run for the dissertation:** 2026-02-24
- **Previous name:** `gene_to_ensembl.py`

```bash
python 02b_gene_to_ensembl.py
```

### Data in this folder

`data/` holds `ALS_candidate_gene_list.txt`, `alsod_gene_transcript_map_gencode_v46.csv`, `STRchive-disease-loci.hg38.general.bed`
(used in step 05), `Scoring_Criteria_AnnotSV_v3.4.xlsx` and `sarek_metadata_stats.tsv` (participant metadata for step 1).

**Used later:** the four `02c_results_prioritise_annotsv_events/*/Supplementary_Table_AnnotSV_*_event_prioritisation.tsv` tables
are inputs to Objective Four (`04_integration/01_single_layer/01e`, `03_cross_layer/02`).

**Next step:** [`05_sv_audit`](../05_sv_audit/README.md) reviews the manual-review shortlists against the raw calls.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
