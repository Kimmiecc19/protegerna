# 01 Single-layer analyses

**Objective:** Objective Four: link SVs, transcriptomic alterations and proteomic evidence within participants and grade the evidence for candidate mechanisms.  
**Dissertation:** Chapter 6, Sections 6.2.7–6.2.12 and 6.3.1–6.3.7; tables and figures: Table 5.11, Table 6.3, Table 6.5, Table 6.8, Table 6.9, Table 6.10, Table 6.11, Table 6.12, Table 6.13, Figure 6.1, Table 6A.1, Table 6A.2, Table 6A.4  
**Back to:** [objective README](../README.md)

## What this step does

Analyses each layer on its own before integration: RNA differential expression (ALS vs healthy controls), consolidation of the
six proteogenomic DIA searches, fusion filtering and recurrence tests, the carrier vs non-carrier SV expression scan with its
dosage positive control, protein differential abundance, peptide-source classification, pathway enrichment with a label
permutation check, and the score-based review of the ten novel peptide candidates.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01a_rna_differential_expression.R` | TMM + dream: ALS vs healthy controls (~ condition + sex + (1\|seq_batch)) and fixed-batch sensitivity | Table 6.3, Table 6.8 |
| `01b_consolidate_proteomic_batches.py` | Consolidate the six v5 DIA-NN batch searches | Table 6.3 |
| `01c_audit_fusion_files.py` | Per-sample catalogue of FusionReport/FusionInspector outputs with checksums | Table 6.3 |
| `01d_filter_fusions.py` | Fusion filters F1–F6, ALS vs HC Fisher tests (BH), ≥ 2-caller sensitivity, Arriba strand check | Table 6.5, Table 6.9, Table 6.10 |
| `01e_sv_carrier_expression_scan.py` | Carrier vs non-carrier RNA scan for every SV event-gene pair | Table 6.13, Figure 6.1 |
| `02a_protein_differential_abundance.R` | limma ~ condition + sex + batch (trend, robust), no imputation | Sections 6.2.11, 6.3.3 |
| `02b_classify_peptide_sources.py` | Reference-explained vs variant-only precursors | Table 5.11, Table 6.11, Table 6.12 |
| `03a_pathway_enrichment.R` | Preranked fgsea (and clusterProfiler) on the moderated t | Table 6A.1, Table 6A.2 |
| `03b_pathway_label_permutation.R` | Within-batch diagnosis-label permutation for the top 15 gene sets (seed 20261014) | Table 6A.4 |
| `04a_extract_spectral_scores.sh` | DIA-NN score columns for the variant-only peptides plus a 1-in-150 background sample | Table 6.12 |
| `04b_review_novel_peptides.py` | Score-based spectral review of the ten novel candidates (fail if ≥ 2 dimensions flagged) | Table 5.11, Table 6.12 |

## Order of running

1. `01a`–`01e` in any order (`01e` needs the Objective Two event tables).
2. `02a` (needs `01b` for the v5 sensitivity run) and `02b`.
3. `03a` (needs `01a` and `02a`), then `03b`.
4. `04a` (needs `02b`), then `04b`.

## How to run each script

Commands are those used for the dissertation, with paths run from `04_integration/`. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01a_rna_differential_expression.R`

TMM + dream: ALS vs healthy controls (~ condition + sex + (1|seq_batch)) and fixed-batch sensitivity; QC and PCA.

- **Dissertation:** Sections 6.2.10, 6.3.1–6.3.2; Table 6.3, Table 6.8
- **Inputs:** data/AnswerALS-1276-T-v1-release7_raw-counts.csv; data/answerals_cohort_coldata.csv
- **Outputs:** 01a_results_rna_differential_expression/ (primary_mixed_seq_batch_random/, sensitivity_fixed_seq_batch/, QC/, AALS_dream_voom_objects.rds)
- **Run record:** 01a_results_rna_differential_expression/sessionInfo.txt
- **Run for the dissertation:** 2026-10
- **Previous name:** `05_ALS_integration/code_ALS_integration/01_rna_dream_answerals.R`
- **Before running:** The script has no command-line options; its **Settings** block holds the input files and `out_dir`, relative to `04_integration/` (it finds its own folder and works from there, whether run with Rscript or sourced in RStudio). The palette is `lib/thesis_palette.R`.

```bash
Rscript 01_single_layer/01a_rna_differential_expression.R   # Settings block: counts_file, coldata_file, out_dir
```

### `01b_consolidate_proteomic_batches.py`

Consolidate the six v5 DIA-NN batch searches; 1% q-value filters; drop the 4 failed runs.

- **Dissertation:** Sections 6.2.11–6.2.12, 6.3.1; Table 6.3
- **Inputs:** pgdb_v5_batch{1..6} quant tables (O3-12); cohort manifests in data/
- **Outputs:** 01b_results_consolidate_proteomic_batches/ (protein_by_run.log2.tsv, protein_by_participant.log2.tsv, sample_metadata.tsv, excluded_runs.tsv, run_stats.tsv)
- **Run record:** 01b_results_consolidate_proteomic_batches/SUCCESS.json (inputs with SHA-256, version 1.4.0)
- **Run for the dissertation:** 2026-10-22
- **Previous name:** `05_consolidate_cohort.py`

```bash
python 01_single_layer/01b_consolidate_proteomic_batches.py --batches data/cohort_batches_1-6.tsv --samples data/cohort_samples_1-6.tsv --exclude-runs data/cohort_exclude_runs_1-6.tsv --msstats-run-aliases data/cohort_msstats_run_aliases_1-6.tsv --expected-batches 6 --expected-participants 346 --outdir 01_single_layer/01b_results_consolidate_proteomic_batches
```

### `01c_audit_fusion_files.py`

Per-sample catalogue of FusionReport/FusionInspector outputs with checksums.

- **Dissertation:** Sections 6.2.9, 6.3.1; Table 6.3
- **Inputs:** nf-core/rnafusion outputs (O3-04)
- **Outputs:** 01c_results_audit_fusion_files/ (combined_fusion_catalogue.tsv, per_sample_summary.tsv, file_audit.tsv)
- **Run record:** 01c_results_audit_fusion_files/provenance_manifest.json
- **Run for the dissertation:** 2026-10-22
- **Previous name:** `11_combine_fusion_reports.py`

```bash
python 01_single_layer/01c_audit_fusion_files.py --input ../03_proteogenomic_database/02_event_detection/02_results_rnafusion_final --output 01_single_layer/01c_results_audit_fusion_files
```

### `01d_filter_fusions.py`

Fusion filters F1–F6, ALS vs HC Fisher tests (BH), ≥ 2-caller sensitivity, Arriba strand check.

- **Dissertation:** Sections 6.2.9, 6.3.4; Table 6.5, Table 6.9, Table 6.10
- **Inputs:** FusionInspector abridged TSVs, fusion-report CSVs, arriba TSVs (batches 1–6); covariates; coldata
- **Outputs:** 01d_results_filter_fusions/ (fusion_calls_all/pass, fusion_recurrence_tests*, fusion_gene_tests, arriba_strand_check, sample_manifest, summary.json)
- **Run record:** 01d_results_filter_fusions/summary.json (settings), log_12_fusions.txt
- **Run for the dissertation:** 2026-10-22
- **Previous name:** `12_fusion_filter_als_test.py`
- **Note:** BH step moved to lib/common.bh on 8 Nov 2026 (bit-identical).

```bash
python 01_single_layer/01d_filter_fusions.py --rnafusion-root ../03_proteogenomic_database/02_event_detection/02_results_rnafusion_final --covariates data/transcriptomic_batches_covariate_info.csv --coldata data/remove_btc_coldata_filtered.csv --outdir 01_single_layer/01d_results_filter_fusions
```

### `01e_sv_carrier_expression_scan.py`

Carrier vs non-carrier RNA scan for every SV event-gene pair; positive control by SV type and length.

- **Dissertation:** Sections 6.2.7, 6.3.7; Table 6.13, Figure 6.1
- **Inputs:** 02c event tables (unfiltered: scan + positive control; filtered: ALS-gene SVs); RNA counts; coldata; ensg_symbol.tsv; alsod_gene_list.csv
- **Outputs:** 01e_results_sv_carrier_expression_scan_unfiltered/ and 01e_results_sv_carrier_expression_scan/ (<label>_sv_gene_expression_tests.tsv, <label>_positive_control_by_length.tsv, summary.json)
- **Run record:** summary.json (no input paths recorded)
- **Run for the dissertation:** 2026-11-07 (EphA3 fix)
- **Previous name:** `15_sv_carrier_expression_scan.py`
- **Note:** Seed 1. Set PYTHONHASHSEED=0 for identical row order. Re-run on 8 Nov: summary.json identical to the saved file.

```bash
python 01_single_layer/01e_sv_carrier_expression_scan.py --tables ../02_SV_analysis/04_sv_prioritization/02c_results_prioritise_annotsv_events/intersection_unfiltered/Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv ../02_SV_analysis/04_sv_prioritization/02c_results_prioritise_annotsv_events/union_only_unfiltered/Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv --labels intersection union_only --counts data/AnswerALS-1276-T-v1-release7_raw-counts.csv --coldata data/answerals_cohort_coldata.csv --gene-map data/ensg_symbol.tsv --alsod data/alsod_gene_list.csv --outdir 01_single_layer/01e_results_sv_carrier_expression_scan_unfiltered
# filtered run: same with the *_filtered tables and --outdir 01_single_layer/01e_results_sv_carrier_expression_scan
```

### `02a_protein_differential_abundance.R`

limma ~ condition + sex + batch (trend, robust), no imputation; consortium (primary) and v5 (sensitivity).

- **Dissertation:** Sections 6.2.11, 6.3.3
- **Inputs:** consortium: data/AnswerALS-447-P_proteomics-protein-matrix_prebatchcorrected.txt + data/cohort_samples.tsv; v5: 01b protein_by_run.log2.tsv + sample_metadata.tsv + proteogenomic_metadata.tsv; data/answerals_cohort_coldata.csv
- **Outputs:** 02a_results_protein_da_consortium/ and 02a_results_protein_da_v5/ (AALS_protein_limma_results.csv, _for_fgsea.csv, protein_by_participant_gene.log2.tsv, protein_objects.rds, QC/)
- **Run record:** sessionInfo.txt, summary.txt in each output folder
- **Run for the dissertation:** 2026-10-23
- **Previous name:** `07_protein_differential_abundance.R`
- **Before running:** The script has no command-line options; its **Settings** block holds the input files and `out_dir`, relative to `04_integration/` (it finds its own folder and works from there, whether run with Rscript or sourced in RStudio). The palette is `lib/thesis_palette.R`. Set `source_mode` to "consortium", then "v5".

```bash
Rscript 01_single_layer/02a_protein_differential_abundance.R   # set source_mode = "consortium" then "v5" in the Settings block
```

### `02b_classify_peptide_sources.py`

Reference-explained vs variant-only precursors; known isoform / GENCODE-only / novel candidate (I=L).

- **Dissertation:** Sections 6.2.12, 6.3.5; Table 5.11, Table 6.11, Table 6.12
- **Inputs:** v5 pr_matrix per batch; proteogenomic_mapping.tsv; UniProt canonical + isoforms; GENCODE v46 translations
- **Outputs:** 02b_results_peptide_source_classification/ (precursor_sources.tsv, variant_only_peptides.tsv, summary.json)
- **Run record:** summary.json
- **Run for the dissertation:** 2026-10-22
- **Previous name:** `06_peptide_source_classification.py`

```bash
python 01_single_layer/02b_classify_peptide_sources.py --pr-matrix ../03_proteogenomic_database/05_proteomic_search/02b_results_quantmsdiann_pgdb/pgdb_v5_batch{1..6}/quant_tables/diann_report.pr_matrix.tsv --batch-names batch1 batch2 batch3 batch4 batch5 batch6 --mapping ../03_proteogenomic_database/03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_mapping.tsv --uniprot data/UP000005640_9606.fasta.gz data/UP000005640_9606_additional.fasta.gz --gencode /path/to/gencode.v46.pc_translations.fa.gz --outdir 01_single_layer/02b_results_peptide_source_classification
```

### `03a_pathway_enrichment.R`

Preranked fgsea (and clusterProfiler) on the moderated t; broad, disease, targeted gene sets.

- **Dissertation:** Sections 6.2.10, 6.3.2–6.3.3; Table 6A.1, Table 6A.2
- **Inputs:** 01a primary dream results; 02a consortium _for_fgsea.csv; data/gene_sets/{broad,disease,targeted}_sets/*.gmt (MSigDB v2026.1)
- **Outputs:** 03a_results_pathway_enrichment_rna/ and _protein/ (gsea_validation/, gsea_plots/; results_fgsea_*_500 subfolders)
- **Run for the dissertation:** 2026-10
- **Previous name:** `02_08_dream_fgsea.R`
- **Before running:** The script has no command-line options; its **Settings** block holds the input files and `out_dir`, relative to `04_integration/` (it finds its own folder and works from there, whether run with Rscript or sourced in RStudio). The palette is `lib/thesis_palette.R`. Set `mode` and `max_gs_size` (300 writes to `03a_results_pathway_enrichment_<mode>/`, 500 to its `results_fgsea_<mode>_500/` subfolder).

```bash
Rscript 01_single_layer/03a_pathway_enrichment.R   # four runs: mode = rna/protein x max_gs_size = 300/500 (Settings block)
```

### `03b_pathway_label_permutation.R`

Within-batch diagnosis-label permutation for the top 15 gene sets (seed 20261014).

- **Dissertation:** Section 6.2.10; Table 6A.4
- **Inputs:** AALS_dream_voom_objects.rds or protein_objects.rds; fgsea_ALL_categories_DREAM_t_nonredundant_combined.csv; GMT files
- **Outputs:** 03b_results_pathway_label_permutation_rna_protein/results_pathway_permutation_{1000,1000_maxsize500}_{rna,protein}.csv
- **Run for the dissertation:** 2026-10
- **Previous name:** `03_09_pathway_label_permutation.R`
- **Before running:** The script has no command-line options; its **Settings** block holds the input files and `out_dir`, relative to `04_integration/` (it finds its own folder and works from there, whether run with Rscript or sourced in RStudio). The palette is `lib/thesis_palette.R`. Set `mode`, `n_perm` and `max_gs_size` to match the 03a run; the output name records them. The saved results used `n_perm = 1000` (the script currently says 5000).
- **Note:** Folder also holds 200- and 5000-permutation runs that the chapter does not report.

```bash
Rscript 01_single_layer/03b_pathway_label_permutation.R   # set mode, n_perm = 1000, max_gs_size; four runs matching 03a
```

### `04a_extract_spectral_scores.sh`

DIA-NN score columns for the variant-only peptides plus a 1-in-150 background sample.

- **Dissertation:** Sections 6.2.12, 6.3.6; Table 6.12
- **Inputs:** v5 diann_report.tsv per batch; variant_only_peptides.tsv
- **Outputs:** 04ab_spectral_review/scores_b{1..6}.tsv
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `extract_scores.sh`

```bash
for b in 1 2 3 4 5 6; do
  bash 01_single_layer/04a_extract_spectral_scores.sh ../03_proteogenomic_database/05_proteomic_search/02b_results_quantmsdiann_pgdb/pgdb_v5_batch$b/quant_tables/diann_report.tsv batch$b 01_single_layer/02b_results_peptide_source_classification/variant_only_peptides.tsv 01_single_layer/04ab_spectral_review/scores_b$b.tsv
done
```

### `04b_review_novel_peptides.py`

Score-based spectral review of the ten novel candidates (fail if ≥ 2 dimensions flagged).

- **Dissertation:** Sections 6.2.12, 6.3.6; Table 5.11, Table 6.12
- **Inputs:** scores_b{1..6}.tsv; variant_only_peptide_classes.tsv (copy of variant_only_peptides.tsv)
- **Outputs:** 04ab_spectral_review/novel_score_review_{summary,by_batch,reference_medians}.tsv, spectral_review.tsv
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `score_review.py`
- **Note:** Re-run on 8 Nov: all four outputs identical to the saved files.

```bash
python 01_single_layer/04b_review_novel_peptides.py 01_single_layer/04ab_spectral_review 01_single_layer/04ab_spectral_review/novel_score_review
```

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
