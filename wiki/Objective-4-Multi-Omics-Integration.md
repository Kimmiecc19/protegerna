# Objective 4: Multi-omics integration in Answer ALS

**Folder:** [`04_integration/`](https://github.com/Kimmiecc19/protegerna/tree/main/04_integration)
**Dissertation:** Chapter 6, *From disruption to consequence: a framework to trace structural variants across the
transcriptome and proteome* (methods 6.2, results 6.3, Appendix 6A). Appendix Table 6A.5 is the reproducibility locator.

## Overview

**Objective:** develop and demonstrate a reproducible framework that integrates structural variants, transcriptomic alterations
and proteomic evidence within individuals, and grades the resulting evidence for candidate mechanisms. ALS is the
demonstration setting.

**Research question:** Can SVs and RNA-level events from the same individual be linked in both directions? Can the resulting
evidence for candidate mechanisms be graded in ordered levels with traceable provenance? Does the approach recover a positive
control?

```text
Objective 2: SV event tables, audited candidates       Objective 3: v5 database + six DIA searches
                         |                                              |
01_single_layer        RNA DE, fusions, SV expression scan, protein DA, peptide sources, pathways, spectral review
02_participant_linking peptides <-> events <-> SVs within participants; rare SVs vs RNA and protein (+ permutation null)
03_cross_layer         gene-level agreement, SV–fusion overlap (+ WGS check), evaluation table and evidence levels
04_figures             Figures 6.1 and 6.3
```

> **Read [Multi-omics integration: design logic](Integration-Design-Logic) first** if you want to understand how the
> layers are linked, how evidence is graded and calibrated, and what the integrated results can and cannot support.

## Installation

| Tool | Version |
| --- | --- |
| R | 4.6.1 with edgeR 4.10.6, limma 3.68.5, variancePartition 1.42.0, fgsea 1.38.0, clusterProfiler, enrichplot, org.Hs.eg.db, BiocParallel, dplyr, tidyr, readr, stringr, ggplot2 |
| Python | 3.11 with pandas, NumPy, SciPy; pysam 0.24.1 (duplication check only) |

See [Installation](Installation) for install commands.

Shared code in `04_integration/lib/`:

| File | Purpose |
| --- | --- |
| `paths.py` | Input paths for `02_participant_linking`. Override any path with `OBJ4_<NAME>` environment variables. |
| `rna_answerals.py` | RNA log2 CPM loader |
| `common.py` | Participant IDs, Benjamini–Hochberg, FASTA and v5 protein loaders |
| `thesis_palette.R` | Dissertation colour palette |

## Inputs required

### From Answer ALS (place in `04_integration/data/`; controlled access)

| Data | Used by |
| --- | --- |
| RNA counts release 7 (`AnswerALS-1276-T-v1-release7_raw-counts.csv`) and `answerals_cohort_coldata.csv` (336 samples: 286 ALS, 50 controls) | 01a, 01e, 03_cross_layer |
| Consortium protein matrix (`AnswerALS-447-P_proteomics-protein-matrix_prebatchcorrected.txt`) and `cohort_samples.tsv` | 02a |
| Proteomic cohort manifests: `cohort_batches_1-6.tsv`, `cohort_samples_1-6.tsv`, `cohort_exclude_runs_1-6.tsv`, `cohort_msstats_run_aliases_1-6.tsv` | 01b, linking |
| `transcriptomic_batches_covariate_info.csv`, `remove_btc_coldata_filtered.csv` | 01d |
| CRAM files of the six duplication carriers | 03_cross_layer/03 |

### Public files (also in `data/`)

`UP000005640_9606.fasta.gz` and `_additional.fasta.gz` (UniProt), `ensg_symbol.tsv`, `alsod_gene_list.csv`, and
`gene_sets/` (MSigDB v2026.1 GMTs; Tables 6A.1–6A.2). GENCODE v46 GTF and translations.

### From earlier objectives

| From | Files |
| --- | --- |
| [Objective 2](Objective-2-Structural-Variants) | `manta_tiddit.intersect.cohort.vcf`; the four AnnotSV event-prioritisation tables (`02c_results_prioritise_annotsv_events/`); `primary_candidates.tsv`; `participant_support.tsv` |
| [Objective 3](Objective-3-Proteogenomic-Database) | v5 database folder (`proteogenomic_database.fasta`, mapping, metadata); quantmsdiann v5 searches, batches 1–6; nf-core/rnafusion 4.0.0 outputs, batches 1–6 |

## Running

Run the steps in order from `04_integration/`. The shorthands below point at the saved results of Objectives 2 and 3 in
this repository:

```bash
S=01_single_layer
C2=../02_SV_analysis/04_sv_prioritization/02c_results_prioritise_annotsv_events
REL=../02_SV_analysis/05_sv_audit/02_results_audited_release
PG=../03_proteogenomic_database/05_proteomic_search/02b_results_quantmsdiann_pgdb
DB=../03_proteogenomic_database/03_search_database/results_pgdb_publication_rerun_v5
FUS=../03_proteogenomic_database/02_event_detection/02_results_rnafusion_final
```

> The R scripts have no command-line options. Their **Settings** block holds input files and `out_dir`, relative to
> `04_integration/`. Each script finds its own folder and works from there, whether run with Rscript or sourced in RStudio.

### Step 01: Single-layer analyses

```bash
# RNA differential expression (dream/voom; Table 6.8)
Rscript $S/01a_rna_differential_expression.R

# Consolidate the six proteogenomic DIA batches
python $S/01b_consolidate_proteomic_batches.py \
  --batches data/cohort_batches_1-6.tsv --samples data/cohort_samples_1-6.tsv \
  --exclude-runs data/cohort_exclude_runs_1-6.tsv \
  --msstats-run-aliases data/cohort_msstats_run_aliases_1-6.tsv \
  --expected-batches 6 --expected-participants 346 \
  --outdir $S/01b_results_consolidate_proteomic_batches

# Fusions: audit files, then filter (Tables 6.5, 6.9, 6.10)
python $S/01c_audit_fusion_files.py --input $FUS --output $S/01c_results_audit_fusion_files
python $S/01d_filter_fusions.py --rnafusion-root $FUS \
  --covariates data/transcriptomic_batches_covariate_info.csv \
  --coldata data/remove_btc_coldata_filtered.csv --outdir $S/01d_results_filter_fusions

# SV-carrier expression scan (Table 6.13; positive control, Figure 6.1)
export PYTHONHASHSEED=0
python $S/01e_sv_carrier_expression_scan.py \
  --tables $C2/intersection_unfiltered/Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv \
           $C2/union_only_unfiltered/Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv \
  --labels intersection union_only \
  --counts data/AnswerALS-1276-T-v1-release7_raw-counts.csv --coldata data/answerals_cohort_coldata.csv \
  --gene-map data/ensg_symbol.tsv --alsod data/alsod_gene_list.csv \
  --outdir $S/01e_results_sv_carrier_expression_scan_unfiltered
# Repeat with the *_filtered tables and --outdir $S/01e_results_sv_carrier_expression_scan

# Protein differential abundance: run twice, source_mode = "consortium" then "v5" (Settings block)
Rscript $S/02a_protein_differential_abundance.R

# Peptide-source classification (Table 6.11)
python $S/02b_classify_peptide_sources.py \
  --pr-matrix $PG/pgdb_v5_batch{1..6}/quant_tables/diann_report.pr_matrix.tsv \
  --batch-names batch1 batch2 batch3 batch4 batch5 batch6 \
  --mapping $DB/proteogenomic_mapping.tsv \
  --uniprot data/UP000005640_9606.fasta.gz data/UP000005640_9606_additional.fasta.gz \
  --gencode /path/to/gencode.v46.pc_translations.fa.gz \
  --outdir $S/02b_results_peptide_source_classification

# Pathway enrichment: four runs (mode = rna/protein × max_gs_size = 300/500, Settings block)
Rscript $S/03a_pathway_enrichment.R
# Label permutation: four matching runs (Table 6A.4; the saved results used n_perm = 1000)
Rscript $S/03b_pathway_label_permutation.R

# Spectral review of novel peptides (Table 6.12)
for b in 1 2 3 4 5 6; do
  bash $S/04a_extract_spectral_scores.sh $PG/pgdb_v5_batch$b/quant_tables/diann_report.tsv batch$b \
    $S/02b_results_peptide_source_classification/variant_only_peptides.tsv $S/04ab_spectral_review/scores_b$b.tsv
done
python $S/04b_review_novel_peptides.py $S/04ab_spectral_review $S/04ab_spectral_review/novel_score_review
```

### Step 02: Participant-level linking (Stages 1–3)

`lib/paths.py` resolves every input from this repository except the GENCODE v46 GTF. Override any path with an
`OBJ4_<NAME>` environment variable:

```bash
export OBJ4_GTF=/path/to/Homo_sapiens_GRCh38_46.gtf
python 02_participant_linking/00_run_linking_pipeline.py --check
python 02_participant_linking/00_run_linking_pipeline.py --nperm 600
# -> 02_participant_linking/02_results_participant_linking/b1to6_<date>/
```

The runner calls, in order:

| Script | Stage |
| --- | --- |
| `01_link_peptides_to_events.py` | Stage 1: peptides ↔ RNA events (feasibility) |
| `02_extract_sv_carriers.py` | SV carriers from the intersection VCF |
| `03_link_svs_to_events.py` | Stage 2: SVs ↔ events ↔ peptides chains |
| `04_test_rare_sv_rna_protein.py` | Stage 3: rare SVs vs RNA and protein in carriers |
| `05_permutation_null.py` | Permutation null (600 permutations of carrier labels) |

### Step 03: Cross-layer agreement and evaluation

```bash
RNA=$S/01a_results_rna_differential_expression/primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv
PROT=$S/02a_results_protein_da_consortium/AALS_protein_limma_results.csv

# Gene-level agreement and SV-candidate carrier effects (Table 6.14)
python 03_cross_layer/01_cross_omics_agreement.py --rna-results $RNA --protein-results $PROT \
  --fusion-dir $S/01d_results_filter_fusions --peptide-dir $S/02b_results_peptide_source_classification \
  --sv-primary $REL/primary_candidates.tsv --sv-support $REL/participant_support.tsv \
  --alsod data/alsod_gene_list.csv --rna-counts data/AnswerALS-1276-T-v1-release7_raw-counts.csv \
  --rna-coldata data/answerals_cohort_coldata.csv --gtf data/ensg_symbol.tsv \
  --protein-matrix $S/01b_results_consolidate_proteomic_batches/protein_by_run.log2.tsv \
  --protein-samples $S/01b_results_consolidate_proteomic_batches/sample_metadata.tsv \
  --pgdb-metadata $DB/proteogenomic_metadata.tsv --outdir 03_cross_layer/01_results_cross_omics_agreement

# Fusions inside rare duplications (Table 6.16)
python 03_cross_layer/04_sv_fusion_overlap.py --fusions $S/01d_results_filter_fusions/fusion_calls_pass.tsv \
  --sv-tests $S/01e_results_sv_carrier_expression_scan_unfiltered/{intersection,union_only}_sv_gene_expression_tests.tsv \
  --coldata data/answerals_cohort_coldata.csv \
  --protein $S/01b_results_consolidate_proteomic_batches/protein_by_participant.log2.tsv \
  --pgdb-metadata $DB/proteogenomic_metadata.tsv --outdir 03_cross_layer/04_results_sv_fusion_overlap

# Confirm the duplications in WGS: once per carrier (needs the carriers' CRAMs + pysam)
WGS_REFERENCE=/path/to/GRCh38_full_analysis_set_plus_decoy_hla.fa CRAM_DIR=/path/to/cram \
  python 03_cross_layer/03_check_duplications_in_wgs.py <participant ID>

# Evaluation table and evidence levels (Tables 6.6, 6.7, 6.17); full argument list in the step README
python 03_cross_layer/02_evaluation_table.py \
  --rna-counts data/AnswerALS-1276-T-v1-release7_raw-counts.csv \
  --rna-coldata data/answerals_cohort_coldata.csv --gene-map data/ensg_symbol.tsv \
  --sv-primary $REL/primary_candidates.tsv --sv-support $REL/participant_support.tsv \
  --sv-scan $S/01e_results_sv_carrier_expression_scan/{intersection,union_only}_sv_gene_expression_tests.tsv \
  --sv-tables $C2/intersection_filtered/Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv \
              $C2/union_only_filtered/Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv \
  --peptides $S/02b_results_peptide_source_classification/variant_only_peptides.tsv \
  --protein-cohort data/cohort_samples_1-6.tsv --fusion-dir $S/01d_results_filter_fusions \
  --spectral-review $S/04ab_spectral_review/spectral_review.tsv \
  --protein-matrix $S/01b_results_consolidate_proteomic_batches/protein_by_run.log2.tsv \
  --protein-samples $S/01b_results_consolidate_proteomic_batches/sample_metadata.tsv \
  --pgdb-metadata $DB/proteogenomic_metadata.tsv --rna-results $RNA --protein-results $PROT \
  --outdir 03_cross_layer/02_results_evaluation_table
```

The exact inputs of the saved evaluation run are in `03_cross_layer/02_results_evaluation_table/summary.json` → `inputs`.

### Step 04: Figures

```bash
Rscript 04_figures/01_combined_chapter6_figures.R   # -> 04_figures/01_results_combined_chapter6_figures/
```

## Expected outputs

| Step | Output folder | Key files |
| --- | --- | --- |
| 01a | `01a_results_rna_differential_expression/` | `primary_mixed_seq_batch_random/`, `sensitivity_fixed_seq_batch/`, `QC/`, `AALS_dream_voom_objects.rds`, `sessionInfo.txt` |
| 01b | `01b_results_consolidate_proteomic_batches/` | `protein_by_run.log2.tsv`, `protein_by_participant.log2.tsv`, `sample_metadata.tsv`, `excluded_runs.tsv`, `run_stats.tsv` |
| 01c | `01c_results_audit_fusion_files/` | `combined_fusion_catalogue.tsv`, `per_sample_summary.tsv`, `file_audit.tsv` |
| 01d | `01d_results_filter_fusions/` | `fusion_calls_all/pass`, `fusion_recurrence_tests*`, `fusion_gene_tests`, `arriba_strand_check`, `summary.json` |
| 01e | `01e_results_sv_carrier_expression_scan[_unfiltered]/` | `<label>_sv_gene_expression_tests.tsv`, `<label>_positive_control_by_length.tsv`, `summary.json` |
| 02a | `02a_results_protein_da_{consortium,v5}/` | `AALS_protein_limma_results.csv`, `_for_fgsea.csv`, `protein_by_participant_gene.log2.tsv`, `QC/` |
| 02b | `02b_results_peptide_source_classification/` | `precursor_sources.tsv`, `variant_only_peptides.tsv`, `summary.json` |
| 03a/b | `03a_results_pathway_enrichment_{rna,protein}/`, `03b_results_pathway_label_permutation_rna_protein/` | fgsea results and plots; permutation results |
| 04a/b | `04ab_spectral_review/` | `scores_b{1..6}.tsv`, `novel_score_review_*.tsv`, `spectral_review.tsv` |
| 02 linking | `02_results_participant_linking/` | `links_peptide_event.tsv`, `novel_peptides_detected.tsv`, `sv_carriers.tsv`, `links_variant_event.tsv`, `chains_variant_event_peptide.tsv`, `variant_gene_rna_protein.tsv`, `permutation_null_summary.json`, `run.log`, `run_manifest.json` |
| 03 cross-layer | `01_results_cross_omics_agreement/` | `gene_evidence_matrix`, `layer_intersections`, `rna_protein_concordance*`, `sv_candidate_carrier_effects`, `fusion_peptide_chains` |
| | `04_results_sv_fusion_overlap/` | `sv_fusion_overlap*.tsv` |
| | `03_check_duplication_in_wgs/` | `wgs_duplication_check_results.tsv`, `igv_wgs_duplications/<participant>/igv_snapshot.png` |
| | `02_results_evaluation_table/` | **`evaluation_full`**, `evaluation_main_table`, `evaluation_summary`, `summary.json` |
| 04 | `04_figures/01_results_combined_chapter6_figures/` | `Figure_6.1_*.png/.pdf`, `Figure_6.3_*.png/.pdf` (not saved in the repository) |

## Before you run / known issues

- **External inputs.** Everything is read from this repository except the GENCODE v46 GTF (`OBJ4_GTF`), the GENCODE
  translations (`--gencode`), and the six carriers' CRAMs with their reference (`CRAM_DIR`, `WGS_REFERENCE`).
- **Seeds:** pathway label permutation 20261014; SV-scan null and evaluation table 1; Stage 3 carrier permutation
  `default_rng(1)`. The fusion label-permutation seed was not saved.
- **`PYTHONHASHSEED=0`** is needed when re-running `01e`; otherwise the row order among tied p-values depends on the hash seed.
- Every peptide-level result uses the **v5** search database. The rnasplice quantitative outputs are not used.

## Dissertation map

| Item | Script(s) |
| --- | --- |
| Table 6.3 | `01a`, `01b`, `01c` |
| Tables 6.5, 6.9, 6.10 | `01d_filter_fusions.py` |
| Tables 6.6, 6.7, 6.17; Figure 6.3 | `03_cross_layer/02_evaluation_table.py` (+ `04_figures`) |
| Table 6.8 | `01a_rna_differential_expression.R` |
| Table 6.11 | `02b_classify_peptide_sources.py` |
| Table 6.12 | `02b`, `04a`, `04b`, `03_cross_layer/02_evaluation_table.py` |
| Table 6.13; Figure 6.1 | `01e_sv_carrier_expression_scan.py` (+ `04_figures`) |
| Table 6.14 | `03_cross_layer/01_cross_omics_agreement.py`, `02_evaluation_table.py` |
| Table 6.15 | `02_participant_linking/00`, `04`, `05` |
| Table 6.16 | `03_cross_layer/04_sv_fusion_overlap.py`, `03_check_duplications_in_wgs.py` |
| Tables 6A.1, 6A.2 | `03a_pathway_enrichment.R` |
| Table 6A.4 | `03b_pathway_label_permutation.R` |

## Key literature

The published work behind this method, and what each work justifies, is listed in
[Literature and method justification](Literature-and-Method-Justification#objective-4-multi-omics-integration).
