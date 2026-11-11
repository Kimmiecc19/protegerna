# 06 Reference vs proteogenomic search assessment

**Objective:** Objective Three: translate gene-fusion and alternative-splicing events detected in RNA-seq into a protein search database for DIA proteomics.  
**Dissertation:** Chapter 5, Sections 5.3.8–5.3.12; tables and figures: Table 5.5, Table 5.6, Table 5.7, Table 5.8, Table 5.9, Table 5.10, Table 5.11  
**Back to:** [objective README](../README.md)

## What this step does

Compares the two searches of all six batches: identification coverage and quantitative quality, peptide and precursor overlap,
peptides found only through splice- or fusion-derived entries, search-space inflation, fusion-associated peptides and the
composition of the v5 and v7 databases.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01a_extract_passing_rows.sh` | Keep report rows passing all four q-value filters (≤ 0.01) | Table 5.7 |
| `01b_make_sequence_source_table.py` | Map each v5 entry to its producers (reference, crap, rmats, suppa, fusioninspector) | Table 5.7 |
| `01c_collect_diann_summary_tables.sh` | Copy stats/pg/gg/unique-gene matrices and SDRFs per batch into small/ | Table 5.6, Table 5.7 |
| `02a_compare_reference_and_proteogenomic.py` | All reference-vs-proteogenomic search metrics (Tables 5.7, 5.9) | Table 5.7, Table 5.9 |
| `02b_find_novel_candidate_peptides.py` | Peptides only in splice/fusion entries and absent from reference DB, UniProt and GENCODE (I=L) | Table 5.10, Table 5.11 |
| `02c_compare_peptide_lengths.py` | In-silico digest of both databases vs observed peptide lengths (Table 5.8, search-space inflation) | Table 5.8 |
| `02d_summarise_fusion_peptides.py` | Peptides mapped to fusion-associated sequences per batch (Table 5.5) | Table 5.5 |
| `02_compare_search_and_revised_databases.py` | Composition of v5 vs v7 and fusion consistency across samples | Section 5.3.8 |

## Order of running

Step 1 builds one working folder (`<six-batch dir>`) that the step-2 scripts read:
1. `01a_extract_passing_rows.sh` (each batch and search), `01b_make_sequence_source_table.py`, `01c_collect_diann_summary_tables.sh`.
2. `02a`, `02b`, `02c`, `02d` in any order; `02_compare_search_and_revised_databases.py` needs the v5 and v7 database folders only.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01a_extract_passing_rows.sh`

Keep report rows passing all four q-value filters (≤ 0.01).

- **Dissertation:** Section 5.2.9; Table 5.7
- **Inputs:** diann_report.tsv per batch and search
- **Outputs:** 01a_extract_passing_rows/{v5,ref}_b{1..6}.pass.tsv.gz, .counts.txt
- **Run record:** *.counts.txt
- **Run for the dissertation:** 2026-10-27

```bash
for b in 1 2 3 4 5 6; do
  bash 01a_extract_passing_rows.sh ../05_proteomic_search/02b_results_quantmsdiann_pgdb/pgdb_v5_batch$b/quant_tables/diann_report.tsv 01a_extract_passing_rows/v5_b$b
  ref=batch$b; [ $b = 1 ] && ref=batch1_fixed
  bash 01a_extract_passing_rows.sh ../05_proteomic_search/02a_results_quantmsdiann_reference/$ref/quant_tables/diann_report.tsv 01a_extract_passing_rows/ref_b$b
done
```

### `01b_make_sequence_source_table.py`

Map each v5 entry to its producers (reference, crap, rmats, suppa, fusioninspector).

- **Dissertation:** Section 5.2.9; Table 5.7
- **Inputs:** proteogenomic_mapping.tsv, proteogenomic_metadata.tsv
- **Outputs:** 01b_make_sequence_source_table/v5_id_source.tsv
- **Run for the dissertation:** 2026-10
- **Note:** Rebuilt file is identical to the one used in the dissertation.

```bash
python 01b_make_sequence_source_table.py --pgdb-dir ../03_search_database/results_pgdb_publication_rerun_v5 --out 01b_make_sequence_source_table/v5_id_source.tsv
```

### `01c_collect_diann_summary_tables.sh`

Copy stats/pg/gg/unique-gene matrices and SDRFs per batch into small/.

- **Dissertation:** Section 5.2.9; Table 5.6, Table 5.7
- **Inputs:** quantmsdiann quant_tables; SDRFs
- **Outputs:** 01c_collect_diann_summary_tables/small/{ref,v5}_bN.*.tsv, sdrf_bN.tsv
- **Run record:** checksum manifest in the output folder
- **Run for the dissertation:** 2026-10
- **Note:** All 54 tables identical to those used.

```bash
bash 01c_collect_diann_summary_tables.sh --ref-root ../05_proteomic_search/02a_results_quantmsdiann_reference --ref-override 1=batch1_fixed --pgdb-root ../05_proteomic_search/02b_results_quantmsdiann_pgdb --out 01c_collect_diann_summary_tables
```

### `02a_compare_reference_and_proteogenomic.py`

All reference-vs-proteogenomic search metrics (Tables 5.7, 5.9).

- **Dissertation:** Sections 5.3.10–5.3.12; Table 5.7, Table 5.9
- **Inputs:** {v5,ref}_bN.pass.tsv.gz; v5_id_source.tsv; small/ tables
- **Outputs:** 02a_compare_reference_and_proteogenomic/reference_vs_v5_metrics.tsv
- **Run for the dissertation:** 2026-10-28

```bash
python 02a_compare_reference_and_proteogenomic.py . 02a_compare_reference_and_proteogenomic/reference_vs_v5_metrics.tsv   # "." = this folder; the 01a/01b/01c subfolders are found automatically
```

### `02b_find_novel_candidate_peptides.py`

Peptides only in splice/fusion entries and absent from reference DB, UniProt and GENCODE (I=L).

- **Dissertation:** Sections 5.3.10, 5.3.12; Table 5.10, Table 5.11
- **Inputs:** pass tables; v5_id_source.tsv; reference FASTAs
- **Outputs:** 02b_find_novel_candidate_peptides/custom_only_peptides_b1to6.tsv
- **Run for the dissertation:** 2026-10

```bash
python 02b_find_novel_candidate_peptides.py . ../05_proteomic_search/01_results_make_reference_database/human_reference_deduplicated.fasta ../../04_integration/data/UP000005640_9606.fasta.gz ../../04_integration/data/UP000005640_9606_additional.fasta.gz /path/to/gencode.v46.pc_translations.fa.gz 02b_find_novel_candidate_peptides/custom_only_peptides_b1to6.tsv
```

### `02c_compare_peptide_lengths.py`

In-silico digest of both databases vs observed peptide lengths (Table 5.8, search-space inflation).

- **Dissertation:** Section 5.3.9; Table 5.8
- **Inputs:** both FASTAs; pass tables
- **Outputs:** 02c_compare_peptide_lengths/table_5_10_peptide_lengths.tsv
- **Run for the dissertation:** 2026-10-28
- **Note:** File name keeps the old table number (5.10); the table is now Table 5.8.

```bash
python 02c_compare_peptide_lengths.py --ref-fasta ../05_proteomic_search/01_results_make_reference_database/human_reference_deduplicated.fasta --v5-fasta ../03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_database.fasta --six-dir . --out 02c_compare_peptide_lengths/table_5_10_peptide_lengths.tsv
```

### `02d_summarise_fusion_peptides.py`

Peptides mapped to fusion-associated sequences per batch (Table 5.5).

- **Dissertation:** Section 5.3.4; Table 5.5
- **Inputs:** pass tables; v5_id_source.tsv; proteogenomic_peptides.tsv
- **Outputs:** 02d_summarise_fusion_peptides/junction_peptides.tsv.gz (table_5_5_fusion_peptides.tsv not saved)
- **Run for the dissertation:** 2026-11
- **Note:** Reproduces every Table 5.5 value; save the table output.

```bash
python 02d_summarise_fusion_peptides.py --six-dir . --pgdb-peptides ../03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_peptides.tsv --out-prefix 02d_summarise_fusion_peptides/table_5_5_fusion_peptides
```

### `02_compare_search_and_revised_databases.py`

Composition of v5 vs v7 and fusion consistency across samples.

- **Dissertation:** Section 5.3.8
- **Inputs:** v5 and v7 database folders
- **Outputs:** 02_compare_search_and_revised_databases/v5_v7_comparison.tsv
- **Run for the dissertation:** 2026-10-28
- **Note:** An identical copy sits in 04_revised_database/02_compare_search_and_revised_databases.py.

```bash
python 02_compare_search_and_revised_databases.py --v5-dir ../03_search_database/results_pgdb_publication_rerun_v5 --v7-dir ../04_revised_database/results_revised_database --fusion-table ../03_search_database/results_pgdb_publication_rerun_v5/fusion.biological.tsv --out 02_compare_search_and_revised_databases/v5_v7_comparison.tsv
```

Python 3 with pandas and numpy. `table_5_10_peptide_lengths.tsv` keeps the table number of an earlier draft; it is now Table 5.8.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
