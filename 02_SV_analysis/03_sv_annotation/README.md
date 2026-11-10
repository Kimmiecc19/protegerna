# 03 ALS gene list and AnnotSV annotation

**Objective:** Objective Two: a reproducible workflow for structural-variant (SV) detection, consolidation, annotation, ALS-informed nomination and interactive exploration.  
**Dissertation:** Chapter 4, Section 4.2.5; tables and figures: Table 4.1  
**Back to:** [objective README](../README.md)

## What this step does

Builds the 154-gene ALS candidate list from ALSoD (accessed 24 February 2026) with Ensembl 112 identifiers, then annotates the
intersection and union cohort VCFs with AnnotSV 3.5.8 twice: restricted to the candidate genes (filtered, run label 05102026) and
without the gene filter (unfiltered, run label 03102026). The unfiltered tables are also used in Chapter 6.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_build_alsod_gene_map.py` | Download the ALSoD gene table and look up Ensembl 112 gene/transcript IDs | Section 4.2.5 |
| `02a_run_annotsv_filtered.sh` | AnnotSV 3.5.8 on the intersection and union cohort VCFs, restricted to the 154 ALS candidate genes (no HPO) | Table 4.1 |
| `02b_run_annotsv_unfiltered.sh` | AnnotSV 3.5.8 without the gene filter | Sections 4.2.5; 6.2.7 |

## Order of running

1. `01_build_alsod_gene_map.py`.
2. `02a_run_annotsv_filtered.sh` and `02b_run_annotsv_unfiltered.sh` (either order).

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_build_alsod_gene_map.py`

Download the ALSoD gene table and look up Ensembl 112 gene/transcript IDs.

- **Dissertation:** Section 4.2.5
- **Inputs:** https://alsod.ac.uk (accessed 24 Feb 2026); Ensembl REST (release 112)
- **Outputs:** 01_results_build_alsod_gene_map/alsod_gene_list.csv, alsod_gene_transcript_map_gencode_v46.csv, ALS_candidate_gene_list.txt
- **Run for the dissertation:** 2026-02-24
- **Previous name:** `extract_alsod.py + gene_to_ensembl.py (also kept as 04_sv_prioritization/02a_extract_alsod.py, 02b_gene_to_ensembl.py)`
- **Note:** ALSoD changes over time; keep the saved alsod_gene_list.csv.

```bash
python 01_build_alsod_gene_map.py --out-dir 01_results_build_alsod_gene_map
```

### `02a_run_annotsv_filtered.sh`

AnnotSV 3.5.8 on the intersection and union cohort VCFs, restricted to the 154 ALS candidate genes (no HPO).

- **Dissertation:** Section 4.2.5; Table 4.1
- **Inputs:** manta_tiddit.{intersect,union}.cohort.vcf; ALS_candidate_gene_list.txt; AnnotSV annotation directory
- **Outputs:** 02a_results_annotsv_filtered/octopusv_{intersect,union}_cohort_filtered_05102026/*.annotated.{tsv,vcf}
- **Run record:** 02a_results_annotsv_filtered/AnnotSV_octopusv_*_cohort_filtered_05102026.log
- **Run for the dissertation:** 2026-10-05
- **Previous name:** `2_SV_analysis/3_annotsv/code_annotsv/run_annotsv.sh`
- **Before running:** Set `ANNOTSV_BIN_DIR` and `ANNOTATIONS` (the AnnotSV 3.5.8 install and its GRCh38 annotation folder; not in the repository). Defaults: input `../02_sv_consolidation/01_results_octopusv/merged`, gene list `../04_sv_prioritization/data/ALS_candidate_gene_list.txt`, output `02a_results_annotsv_filtered/` with run label `05102026` (unfiltered mode: `02b_results_annotsv_unfiltered/`, `03102026`).
- **Note:** The log lists every AnnotSV argument (-candidateGenesFiltering 1, -SVminSize 50).

```bash
ANNOTSV_BIN_DIR=/path/to/AnnotSV/bin ANNOTATIONS=/path/to/AnnotSV/share/AnnotSV bash 02a_run_annotsv_filtered.sh
```

### `02b_run_annotsv_unfiltered.sh`

AnnotSV 3.5.8 without the gene filter.

- **Dissertation:** Sections 4.2.5; 6.2.7
- **Inputs:** as O2-08, no gene list
- **Outputs:** 02b_results_annotsv_unfiltered/octopusv_{intersect,union}_cohort_unfiltered_03102026/*.annotated.{tsv,vcf}
- **Run record:** 02b_results_annotsv_unfiltered/AnnotSV_octopusv_*_cohort_unfiltered_03102026.log
- **Run for the dissertation:** 2026-10-03
- **Previous name:** `2_SV_analysis/3_annotsv/code_annotsv/run_annotsv_unfiltered.sh`
- **Before running:** Same environment variables as `02a`; this wrapper calls `02a_run_annotsv_filtered.sh --mode unfiltered`.

```bash
ANNOTSV_BIN_DIR=/path/to/AnnotSV/bin ANNOTATIONS=/path/to/AnnotSV/share/AnnotSV bash 02b_run_annotsv_unfiltered.sh
```

### Data in this folder

- `data/Scoring_Criteria_AnnotSV_v3.4.xlsx` – AnnotSV ranking criteria (Table 4.1).
- `data/configfile.txt` – AnnotSV configuration used.

The AnnotSV log files (`AnnotSV_octopusv_*.log`) in each results folder list every argument used.

**Next step:** [`04_sv_prioritization`](../04_sv_prioritization/README.md).

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
