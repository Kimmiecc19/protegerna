# 03 Cross-layer agreement and evaluation

**Objective:** Objective Four: link SVs, transcriptomic alterations and proteomic evidence within participants and grade the evidence for candidate mechanisms.  
**Dissertation:** Chapter 6, Sections 6.2.13–6.2.15 and 6.3.7–6.3.8; tables and figures: Table 5.11, Table 6.6, Table 6.7, Table 6.12, Table 6.14, Table 6.16, Table 6.17, Figure 6.3  
**Back to:** [objective README](../README.md)

## What this step does

Brings the layers together: a gene-level evidence matrix and RNA–protein concordance, RNA and protein levels in carriers of the
primary SV candidates, fusions whose breakpoints both lie inside a rare SV in the same participant (with WGS confirmation of the
six duplications), and the evaluation table that records each candidate's single-layer conclusion, its integrated conclusion and
its evidence level.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_cross_omics_agreement.py` | Gene evidence matrix, RNA–protein concordance, primary-candidate carrier effects, fusion–peptide chains | Table 6.14 |
| `04_sv_fusion_overlap.py` | Filtered fusions whose breakpoints both lie inside a rare SV in the same participant | Table 6.16 |
| `03_check_duplications_in_wgs.py` | pysam depth, outward-facing pairs and split reads for the six fusion-containing duplications | Table 6.16 |
| `02_evaluation_table.py` | Single-layer vs integrated conclusion, change class and evidence level for every candidate | Table 5.11, Table 6.6, Table 6.7, Table 6.12, Table 6.14, Table 6.17, Figure 6.3 |

## Order of running

1. `01_cross_omics_agreement.py` and `04_sv_fusion_overlap.py` (any order; need `01_single_layer`).
2. `03_check_duplications_in_wgs.py` for each duplication carrier from `04`.
3. `02_evaluation_table.py` (needs `01_single_layer`, including `04ab_spectral_review/spectral_review.tsv`).

## How to run each script

Commands are those used for the dissertation, with paths run from `04_integration/`. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_cross_omics_agreement.py`

Gene evidence matrix, RNA–protein concordance, primary-candidate carrier effects, fusion–peptide chains.

- **Dissertation:** Sections 6.2.13 (Gene- and participant-level agreement; Fusion–peptide concordance), 6.3.7–6.3.8; Table 6.14
- **Inputs:** as in the command (v5 protein path reproduces the saved carrier-effects table)
- **Outputs:** 01_results_cross_omics_agreement/ (gene_evidence_matrix, layer_intersections, rna_protein_concordance*, sv_candidate_carrier_effects, fusion_peptide_chains, summary.json)
- **Run record:** summary.json
- **Run for the dissertation:** 2026-10-22
- **Note:** Saved gene_evidence_matrix predates the EphA3 case fix (one row differs on re-run).

```bash
python 03_cross_layer/01_cross_omics_agreement.py --rna-results 01_single_layer/01a_results_rna_differential_expression/primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv --protein-results 01_single_layer/02a_results_protein_da_consortium/AALS_protein_limma_results.csv --fusion-dir 01_single_layer/01d_results_filter_fusions --peptide-dir 01_single_layer/02b_results_peptide_source_classification --sv-primary ../02_SV_analysis/05_sv_audit/02_results_audited_release/primary_candidates.tsv --sv-support ../02_SV_analysis/05_sv_audit/02_results_audited_release/participant_support.tsv --alsod data/alsod_gene_list.csv --rna-counts data/AnswerALS-1276-T-v1-release7_raw-counts.csv --rna-coldata data/answerals_cohort_coldata.csv --gtf data/ensg_symbol.tsv --protein-matrix 01_single_layer/01b_results_consolidate_proteomic_batches/protein_by_run.log2.tsv --protein-samples 01_single_layer/01b_results_consolidate_proteomic_batches/sample_metadata.tsv --pgdb-metadata ../03_proteogenomic_database/03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_metadata.tsv --outdir 03_cross_layer/01_results_cross_omics_agreement
```

### `04_sv_fusion_overlap.py`

Filtered fusions whose breakpoints both lie inside a rare SV in the same participant; Poisson + permutation.

- **Dissertation:** Sections 6.2.13, 6.3.8; Table 6.16
- **Inputs:** as in the command
- **Outputs:** 04_results_sv_fusion_overlap/ (sv_fusion_overlap*.tsv, summary.json)
- **Run record:** summary.json
- **Run for the dissertation:** 2026-10-22
- **Note:** Re-run on 8 Nov: all four outputs byte-identical to the saved files.

```bash
python 03_cross_layer/04_sv_fusion_overlap.py --fusions 01_single_layer/01d_results_filter_fusions/fusion_calls_pass.tsv --sv-tests 01_single_layer/01e_results_sv_carrier_expression_scan_unfiltered/{intersection,union_only}_sv_gene_expression_tests.tsv --coldata data/answerals_cohort_coldata.csv --protein 01_single_layer/01b_results_consolidate_proteomic_batches/protein_by_participant.log2.tsv --pgdb-metadata ../03_proteogenomic_database/03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_metadata.tsv --outdir 03_cross_layer/04_results_sv_fusion_overlap
```

### `03_check_duplications_in_wgs.py`

pysam depth, outward-facing pairs and split reads for the six fusion-containing duplications.

- **Dissertation:** Sections 6.2.13 (WGS confirmation of duplications), 6.3.8; Table 6.16
- **Inputs:** re-obtained CRAMs of six carriers; GRCh38_full_analysis_set_plus_decoy_hla.fa
- **Outputs:** 03_check_duplication_in_wgs/wgs_duplication_check_results.tsv; igv_wgs_duplications/<participant>/igv_snapshot.png
- **Run for the dissertation:** 2026-11
- **Before running:** Needs the CRAM files of the six carriers (controlled access) and pysam. Set `CRAM_DIR` (CRAMs found as `$CRAM_DIR/<participant>/*/*.cram`) and `WGS_REFERENCE`.
- **Note:** Duplicate dupcheck.py removed 8 Nov 2026.

```bash
WGS_REFERENCE=/path/to/GRCh38_full_analysis_set_plus_decoy_hla.fa CRAM_DIR=/path/to/cram python 03_cross_layer/03_check_duplications_in_wgs.py <participant ID>   # once per carrier
```

### `02_evaluation_table.py`

Single-layer vs integrated conclusion, change class and evidence level for every candidate.

- **Dissertation:** Sections 6.2.14–6.2.15, 6.3.8; Table 5.11, Table 6.6, Table 6.7, Table 6.12, Table 6.14, Table 6.17, Figure 6.3
- **Inputs:** exact inputs recorded in summary.json → inputs
- **Outputs:** 02_results_evaluation_table/ (evaluation_full, evaluation_main_table, evaluation_summary, summary.json)
- **Run record:** 02_results_evaluation_table/summary.json (inputs)
- **Run for the dissertation:** 2026-11-07 (EphA3 fix, spectral review)
- **Note:** Seed 1. Re-run on 8 Nov: all three tables byte-identical to the saved files.

```bash
python 03_cross_layer/02_evaluation_table.py --rna-counts data/AnswerALS-1276-T-v1-release7_raw-counts.csv --rna-coldata data/answerals_cohort_coldata.csv --gene-map data/ensg_symbol.tsv --sv-primary ../02_SV_analysis/05_sv_audit/02_results_audited_release/primary_candidates.tsv --sv-support ../02_SV_analysis/05_sv_audit/02_results_audited_release/participant_support.tsv --sv-scan 01_single_layer/01e_results_sv_carrier_expression_scan/{intersection,union_only}_sv_gene_expression_tests.tsv --sv-tables ../02_SV_analysis/04_sv_prioritization/02c_results_prioritise_annotsv_events/intersection_filtered/Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv ../02_SV_analysis/04_sv_prioritization/02c_results_prioritise_annotsv_events/union_only_filtered/Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv --peptides 01_single_layer/02b_results_peptide_source_classification/variant_only_peptides.tsv --protein-cohort data/cohort_samples_1-6.tsv --fusion-dir 01_single_layer/01d_results_filter_fusions --spectral-review 01_single_layer/04ab_spectral_review/spectral_review.tsv --protein-matrix 01_single_layer/01b_results_consolidate_proteomic_batches/protein_by_run.log2.tsv --protein-samples 01_single_layer/01b_results_consolidate_proteomic_batches/sample_metadata.tsv --pgdb-metadata ../03_proteogenomic_database/03_search_database/results_pgdb_publication_rerun_v5/proteogenomic_metadata.tsv --rna-results 01_single_layer/01a_results_rna_differential_expression/primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv --protein-results 01_single_layer/02a_results_protein_da_consortium/AALS_protein_limma_results.csv --outdir 03_cross_layer/02_results_evaluation_table
```

`03_check_duplication_in_wgs/igv_wgs_duplications/` holds the IGV snapshots of the six duplications.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
