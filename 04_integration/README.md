# Objective Four: multi-omics integration in Answer ALS (Chapter 6)

**Objective:** develop and demonstrate a reproducible framework for multi-omics integration of structural variants, transcriptomic
alterations and proteomic evidence within individuals, and grade the resulting evidence for candidate mechanisms, using ALS as the
demonstration setting.

**Research question:** Can SVs and RNA-level events from the same individual be linked in both directions, can the resulting
evidence for candidate mechanisms be graded in ordered levels with traceable provenance, and does the approach recover a positive
control?

**Dissertation:** Chapter 6, *From disruption to consequence: a framework to trace structural variants across the transcriptome
and proteome* (methods 6.2, results 6.3, Appendix 6A). Appendix Table 6A.5 is the reproducibility locator for this folder.

## What is done

```text
Objective Two: SV event tables, audited candidates      Objective Three: v5 database + six DIA searches
                         |                                              |
01_single_layer     RNA DE, fusions, SV expression scan, protein DA, peptide sources, pathways, spectral review
02_participant_linking   peptides <-> events <-> SVs within participants; rare SVs vs RNA and protein (+ permutation null)
03_cross_layer      gene-level agreement, SV-fusion overlap (+ WGS check), evaluation table and evidence levels
04_figures          Figures 6.1 and 6.3
```

## Steps

| Step | What it does | Dissertation |
| --- | --- | --- |
| [`01_single_layer`](01_single_layer/README.md) | One layer at a time | 6.2.7–6.2.12, 6.3.1–6.3.7; Tables 6.3, 6.8–6.13, 6A.4 |
| [`02_participant_linking`](02_participant_linking/README.md) | Within-participant linking, Stages 1–3 | 6.2.13, 6.3.8; Table 6.15 |
| [`03_cross_layer`](03_cross_layer/README.md) | Cross-layer agreement and evaluation | 6.2.13–6.2.15, 6.3.8; Tables 6.14, 6.16, 6.17 |
| [`04_figures`](04_figures/README.md) | Figures 6.1 and 6.3 | 6.3.7–6.3.8 |

Run the steps in order. Each step folder has its own README with the command used for every script, its inputs and outputs, and
what to edit first.

## Shared folders

| Folder | Contents |
| --- | --- |
| `lib/` | `paths.py` (input paths for `02_participant_linking`; override with `OBJ4_<NAME>` environment variables), `rna_answerals.py` (RNA log2 CPM loader), `common.py` (participant IDs, Benjamini–Hochberg, FASTA and v5 protein loaders), `thesis_palette.R` |
| `data/` | RNA counts (release 7) and sample metadata, consortium protein matrix, proteomic cohort manifests, UniProt FASTA, `ensg_symbol.tsv`, `alsod_gene_list.csv`, and `gene_sets/` (MSigDB v2026.1 GMTs; Tables 6A.1–6A.2) |

## Data required

| Data | Used by |
| --- | --- |
| Answer ALS RNA counts release 7; `answerals_cohort_coldata.csv` (336 samples: 286 ALS, 50 controls) | 01a, 01e, 03_cross_layer |
| Consortium protein matrix (pre-batch-corrected); `cohort_samples.tsv` | 02a |
| quantmsdiann v5 searches, batches 1–6 (Objective Three) and cohort manifests in `data/` | 01b, 02b, 04a, 02_participant_linking |
| v5 database folder (`proteogenomic_database.fasta`, mapping, metadata) | 02a, 02b, 02_participant_linking, 03_cross_layer |
| nf-core/rnafusion 4.0.0 outputs, batches 1–6 | 01c, 01d, 02_participant_linking |
| UniProt UP000005640 (canonical + isoforms); GENCODE v46 GTF and translations | 02b, 02_participant_linking |
| Objective Two: `manta_tiddit.intersect.cohort.vcf`, the four AnnotSV event-prioritisation tables, `primary_candidates.tsv`, `participant_support.tsv` | 01e, 02_participant_linking, 03_cross_layer |
| CRAM files of the six duplication carriers | 03_cross_layer/03 |

## Software

| Tool | Version |
| --- | --- |
| R | 4.6.1 with edgeR 4.10.6, limma 3.68.5, variancePartition 1.42.0, fgsea 1.38.0, clusterProfiler, enrichplot, org.Hs.eg.db, BiocParallel, dplyr, tidyr, readr, stringr, ggplot2 |
| Python | 3.11 with pandas, NumPy, SciPy; pysam 0.24.1 (duplication check) |

## Script-to-dissertation map

Tables 6.1, 6.2, 6.4 and 6.6–6.7 and Appendix Table 6A.3 describe the design; Table 6.5 lists the filters coded in `01d`.
Figure 6.2 (FusionInspector views) is not saved.

| Item | Caption | Script(s) | Status |
| --- | --- | --- | --- |
| Table 6.1 | Complementary information contributed by each molecular layer | Method design | No script |
| Table 6.2 | Analyses performed for each molecular layer | Method design | No script |
| Table 6.3 | Participants and samples available for each layer | `01_single_layer/01a_rna_differential_expression.R`, `01_single_layer/01b_consolidate_proteomic_batches.py`, `01_single_layer/01c_audit_fusion_files.py` | Saved |
| Table 6.4 | Comparisons performed, the participants included in each and the role of each comparison in the chapter | Method design | No script |
| Table 6.5 | Criteria for filtering fusion events | `01_single_layer/01d_filter_fusions.py` | Saved |
| Table 6.6 | Evidence dimensions and mechanistic levels | `03_cross_layer/02_evaluation_table.py` | Saved |
| Table 6.7 | Rules used to reclassify candidates after integration | `03_cross_layer/02_evaluation_table.py` | Saved |
| Table 6.8 | Proportion of variance in the first five principal components explained by each covariate | `01_single_layer/01a_rna_differential_expression.R` | Saved |
| Table 6.9 | Fusion-call filtering (a call can fail more than one filter) | `01_single_layer/01d_filter_fusions.py` | Saved |
| Table 6.10 | The most recurrent fusions passing all filters | `01_single_layer/01d_filter_fusions.py` | Saved |
| Table 6.11 | Peptide-source classification in the proteogenomic searches of batches 1–6 | `01_single_layer/02b_classify_peptide_sources.py` | Saved |
| Table 6.12 | Novel peptide candidates and their support in matched RNA data | `01_single_layer/02b_classify_peptide_sources.py`, `01_single_layer/04a_extract_spectral_scores.sh`, `01_single_layer/04b_review_novel_peptides.py`, `03_cross_layer/02_evaluation_table.py` | Saved |
| Table 6.13 | Selected SV–expression associations significant at FDR below 0.05 (intersection table) | `01_single_layer/01e_sv_carrier_expression_scan.py` | Saved |
| Table 6.14 | RNA and protein levels in carriers of the primary SV candidates from Objective Two | `03_cross_layer/01_cross_omics_agreement.py`, `03_cross_layer/02_evaluation_table.py` | Saved |
| Table 6.15 | Effects of rare SVs on RNA and protein in carriers, compared with a permutation null (600 permutations of carrier labels) | `02_participant_linking/00_run_linking_pipeline.py`, `02_participant_linking/04_test_rare_sv_rna_protein.py`, `02_participant_linking/05_permutation_null.py` | Saved |
| Table 6.16 | Fusion transcripts with both breakpoints inside a rare duplication carried by the same participant | `03_cross_layer/04_sv_fusion_overlap.py`, `03_cross_layer/03_check_duplications_in_wgs.py` | Saved |
| Table 6.17 | Change in each candidate's single-layer conclusion after integration | `03_cross_layer/02_evaluation_table.py` | Saved |
| Figure 6.1 | Positive control for the SV expression scan | `01_single_layer/01e_sv_carrier_expression_scan.py`, `04_figures/01_combined_chapter6_figures.R` | Data saved; figure file missing |
| Figure 6.2 | FusionInspector views of fusions coinciding with private duplications | `03_proteogenomic_database/02_event_detection/02b_run_rnafusion.sh` | Missing |
| Figure 6.3 | Change in the conclusion for each candidate category after integration | `03_cross_layer/02_evaluation_table.py`, `04_figures/01_combined_chapter6_figures.R` | Data saved; figure file missing |
| Table 6A.1 | Broad gene-set collections used for preranked gene-set enrichment analysis | `01_single_layer/03a_pathway_enrichment.R` | Saved |
| Table 6A.2 | Disease and targeted gene sets used for preranked gene-set enrichment analysis | `01_single_layer/03a_pathway_enrichment.R` | Saved |
| Table 6A.3 | Units of analysis and how they are counted | Method design | No script |
| Table 6A.4 | Gene sets retested by permutation of diagnosis labels within batch (1,000 permutations; the 15 gene sets with the smallest gene-set-permutation p-values in each layer) | `01_single_layer/03b_pathway_label_permutation.R` | Saved |
| Table 6A.5 | Reproducibility locator for the Chapter 6 analyses | Locator | Saved |

## Reproducibility notes

- Seeds: pathway label permutation 20261014; SV-scan null and evaluation table 1; Stage 3 carrier permutation `default_rng(1)`;
  the fusion label permutation seed was not saved.
- Set `PYTHONHASHSEED=0` when re-running `01e`: the row order among tied p-values otherwise depends on the hash seed.
- R `sessionInfo.txt` is saved with the DE and DA results; the linking pipeline writes `run_manifest.json`; most Python scripts
  write `summary.json` with their settings.
- Every peptide-level result uses the v5 search database from Chapter 5. The rnasplice quantitative outputs are not used.
- Every script resolves its inputs from this repository (R scripts work from `04_integration/`; `lib/paths.py` for the
  linking pipeline). External inputs are the GENCODE v46 GTF and translations, and the CRAMs for the duplication check.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
