# Objective Four: multi-omics integration in Answer ALS (Chapter 6)

This folder contains the code for **Objective Four** of the dissertation, reported in
**Chapter 6: From disruption to consequence: a framework to trace structural variants across the
transcriptome and proteome**.

Each molecular layer is first analysed on its own:

- RNA expression and pathways;
- protein abundance and pathways;
- fusion transcripts;
- peptides from the proteogenomic search.

The layers are then linked within participants to the structural variants (SVs) from Objective Two. The
single-layer and integrated conclusions are compared for every candidate under fixed rules.

It uses outputs from:

- **Objective Two** (`../objective2_sv_analysis`, Chapter 4): SV calls, AnnotSV event tables and the audited release;
- **Objective Three** (Chapter 5): the proteogenomic search database (v5) and its DIA-NN searches.

> The evidence levels support claims of mechanistic plausibility only, not of pathogenicity or disease
> contribution (Section 6.2.14).

## Contents

- [Workflow at a glance](#workflow-at-a-glance)
- [Data required](#data-required)
- [Software](#software)
- [Setting up paths](#setting-up-paths)
- [How to run each step](#how-to-run-each-step)
- [Script-to-dissertation map](#script-to-dissertation-map)
- [Reproducibility notes](#reproducibility-notes)
- [Previous file names](#previous-file-names)

## Workflow at a glance

```text
                Objective Two (SVs)        Objective Three (search database)    Answer ALS RNA / protein
                        │                              │                                │
01_single_layer   step 1  RNA DE · consolidate proteomic batches · fusion audit + filter · SV carrier scan
                  step 2  protein DA · peptide-source classification · pathway enrichment
                  step 3  pathway label permutation · spectral review of novel peptides
                        │
02_participant_linking    Stage 1 peptide→event · Stage 2 SV→event · Stage 3 rare-SV RNA/protein scan · permutation null
                        │
03_cross_layer            cross-omics agreement · SV–fusion overlap · WGS duplication check → evaluation table
                        │
figures                   Figures 6.1 and 6.3
```

Numbers give the run order. Scripts in the same folder that share a number with different letters
(`01a`, `01b`) don't depend on each other.

## Data required

| Data | File(s) | Used by |
| --- | --- | --- |
| Answer ALS RNA-seq gene counts, release 7 | `AnswerALS-1276-T-v1-release7_raw-counts.csv` | 01a, 01e, 02, 03a, 03c |
| RNA sample metadata (336 samples: 286 ALS, 50 healthy controls; `condition`, `seq_batch`, `sex`, `diagnosis`) | `answerals_cohort_coldata.csv` | 01a, 01e, 03a–03c |
| RNA batch covariates and sample sheet for fusions | `transcriptomic_batches_covariate_info.csv`, `remove_btc_coldata_filtered.csv` | 01d |
| Answer ALS consortium protein matrix (pre-batch-corrected) | `AnswerALS-447-P_proteomics-protein-matrix_prebatchcorrected.txt` | 02a |
| Proteomic sample manifest (sample-preparation batch per participant) | `cohort_samples.tsv` | 02a, 03c |
| quantmsdiann (DIA-NN 1.8.1) search outputs for batches 1–6 against the v5 database | `pgdb_v5_batch{1..6}/quant_tables/diann_report.tsv`, `diann_report.pr_matrix.tsv`, `diann_report.pg_matrix.tsv`, `diann_report.stats.tsv`, `diann_design_msstats_in.csv` | 01b, 02b, 02, 03b |
| Proteomic cohort manifests | `cohort_batches_1-6.tsv`, `cohort_samples_1-6.tsv`, `cohort_exclude_runs_1-6.tsv` (the 4 failed runs), `cohort_msstats_run_aliases_1-6.tsv` | 01b, 02 |
| Proteogenomic search database v5 (Objective Three) | `pgdb_publication_rerun_v5/`: `proteogenomic_database.fasta` (MD5 `3f8ed11769fcd5a62587b528cd2eb52a`), `proteogenomic_mapping.tsv`, `proteogenomic_metadata.tsv` | 02a, 02b, 02, 03 |
| nf-core/rnafusion v4.0.0 outputs, batches 1–6 | `fusioninspector/`, `fusionreport/`, `arriba/`, `fusioncatcher/` per batch | 01c, 01d, 02 |
| UniProt human reference proteome UP000005640 (downloaded 15 Sep 2026) | `UP000005640_9606.fasta.gz`, `UP000005640_9606_additional.fasta.gz` | 02b, 02 |
| GENCODE v46 annotation | `Homo_sapiens_GRCh38_46.gtf`; protein-coding translations FASTA; `ensg_symbol.tsv` (ENSG → symbol) | 01e, 02b, 02, 03 |
| MSigDB v2026.1 gene sets | `data/gene_sets/{broad,disease,targeted}_sets/*.gmt` (Appendix Tables 6A.1–6A.2) | 02c, 03a |
| **From Objective Two** | `manta_tiddit.intersect.cohort.vcf`; `Supplementary_Table_AnnotSV_{intersection,union_only}_event_prioritisation.tsv` (filtered and unfiltered); `primary_candidates.tsv`; `participant_support.tsv`; `alsod_gene_list.csv` | 01e, 02, 03 |
| Answer ALS WGS CRAM files of the duplication carriers | CRAM + CRAI | 03 (duplication check) |

Answer ALS data are available under the consortium's data-use terms. Do not commit them, or
participant-level outputs, to a public repository.

## Software

| Tool | Version |
| --- | --- |
| R | 4.6.1 with edgeR 4.10.6, limma 3.68.5, variancePartition 1.42.0, fgsea 1.38.0, clusterProfiler, enrichplot, org.Hs.eg.db, AnnotationDbi, BiocParallel, dplyr, tidyr, readr, stringr, purrr, ggplot2 |
| Python | 3.11.13 with pandas, NumPy, SciPy (pysam 0.24.1 for the duplication check) |
| Upstream workflows (run before this folder) | nf-core/rnafusion 4.0.0; nf-core/rnasplice 1.0.3 (its quantitative outputs are **not** used); quantmsdiann 2.2.0 with DIA-NN 1.8.1 |

## Setting up paths

- **Run every command from the root of this folder.** The R scripts `source("lib/thesis_palette.R")` relative to it.
- **R scripts** have no command-line options. Each has a **Settings** block near the top (input files,
  `out_dir`, and the `mode` or `source_mode` switch). Edit it before each run.
- **Integration pipeline (step 02)** reads every input path from `lib/paths.py`. Edit that file, or override a
  single path with an environment variable `OBJ4_<NAME>`, e.g. `OBJ4_GTF=/path/genes.gtf`.
  `BATCHES` defaults to all six batches.
- **Python scripts** print their options with `--help`, and **none overwrites an existing output folder**.
  To re-run, rename or delete the old folder first.

The commands below write each script's output to `results/<script name>/`, so any result file can be traced
back to the script that made it. They use these variables:

```bash
DATA=data                                   # inputs listed above
R=results                                   # outputs
SV=/path/to/objective2_sv_analysis/results  # Objective Two outputs
PGDB=/path/to/pgdb_publication_rerun_v5     # Objective Three database
COUNTS=$DATA/AnswerALS-1276-T-v1-release7_raw-counts.csv
COLDATA=$DATA/answerals_cohort_coldata.csv
```

## How to run each step

### 01_single_layer: one layer at a time

#### Step 1 (scripts 01a–01e can run in any order)

**01a_rna_differential_expression.R** filters genes (≥ 10 counts in ≥ 20 samples), applies TMM normalisation
(edgeR) and fits dream (variancePartition), comparing ALS with healthy controls using
`~ diagnosis + sex + (1 | sequencing batch)` with voomWithDreamWeights. It also fits a fixed-batch
sensitivity model, and computes library-size QC and PCA.

```bash
# Settings: project_dir, counts_file, coldata_file, out_dir = "results/01a_rna_differential_expression"
Rscript 01_single_layer/01a_rna_differential_expression.R
```

- *Output:* `primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv`,
  `sensitivity_fixed_seq_batch/`, `QC/`, `AALS_dream_voom_objects.rds`, `sessionInfo.txt`.

**01b_consolidate_proteomic_batches.py** combines the six DIA-NN batch searches into one cohort. It applies
the 1% q-value filters and drops the four failed runs.

```bash
python 01_single_layer/01b_consolidate_proteomic_batches.py \
  --batches $DATA/cohort_batches_1-6.tsv --samples $DATA/cohort_samples_1-6.tsv \
  --exclude-runs $DATA/cohort_exclude_runs_1-6.tsv --msstats-run-aliases $DATA/cohort_msstats_run_aliases_1-6.tsv \
  --expected-batches 6 --expected-participants 346 --outdir $R/01b_consolidate_proteomic_batches
```

- *Output:* `protein_by_run.log2.tsv`, `protein_by_participant.log2.tsv`, `sample_metadata.tsv`,
  `excluded_runs.tsv`, `run_stats.tsv`, `SUCCESS.json`.

**01c_audit_fusion_files.py** records, for every sample, which nf-core/rnafusion outputs exist
(FusionInspector, fusion-report), with checksums. It does not re-score calls.

```bash
python 01_single_layer/01c_audit_fusion_files.py --input /path/to/rnafusion_analysis --output $R/01c_audit_fusion_files
```

**01d_filter_fusions.py** applies filters F1–F6 to the FusionInspector calls:

- F1: ≥ 2 junction reads;
- F2: FFPM ≥ 0.1;
- F3: large anchor support;
- F4: not neighbouring genes;
- F5: not on the artefact or normal-tissue lists;
- F6: not seen in the recurring control line.

It then tests each fusion pair and partner gene with ≥ 3 carriers (ALS vs controls, Fisher with BH correction). It
also runs the ≥ 2-caller sensitivity tier and the Arriba strand check.

```bash
python 01_single_layer/01d_filter_fusions.py --rnafusion-root /path/to/rnafusion_analysis \
  --covariates $DATA/transcriptomic_batches_covariate_info.csv --coldata $DATA/remove_btc_coldata_filtered.csv \
  --outdir $R/01d_filter_fusions
```

- *Output:* `fusion_calls_all.tsv`, `fusion_calls_pass.tsv` (351 calls), `fusion_recurrence_tests.tsv`,
  `fusion_recurrence_tests_multicaller_sensitivity.tsv`, `fusion_gene_tests.tsv`, `arriba_strand_check.tsv`.

**01e_sv_carrier_expression_scan.py** compares carriers with non-carriers for every SV event and every gene it
overlaps. Expression is log2(CPM+1), residualised on sequencing batch, sex and diagnosis and z-scored.
The statistic is the mean carrier z × √k. P-values come from an empirical null of 20 random genes per pair
(seed 1). The script also runs the positive control: does expression change in the expected direction
by SV type and length? **Run it twice:**

```bash
# genome-wide scan and positive control: UNFILTERED AnnotSV event tables
python 01_single_layer/01e_sv_carrier_expression_scan.py \
  --tables $SV/annotsv_prioritization/intersection_unfiltered/Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv \
           $SV/annotsv_prioritization/union_only_unfiltered/Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv \
  --labels intersection union_only --counts $COUNTS --coldata $COLDATA \
  --gene-map $DATA/ensg_symbol.tsv --alsod $SV/alsod_gene_list.csv \
  --outdir $R/01e_sv_carrier_expression_scan_unfiltered
# SVs in ALS genes: FILTERED tables (intersection_filtered, union_only_filtered) -> $R/01e_sv_carrier_expression_scan_filtered
```

- *Output:* `<label>_sv_gene_expression_tests.tsv`, `<label>_positive_control_by_length.tsv`, `summary.json`.

#### Step 2 (needs step 1)

**02a_protein_differential_abundance.R** runs limma with `~ diagnosis + sex + batch`, trend and robust eBayes,
and no imputation. A protein is tested if it is quantified in ≥ 70% of each group. **Run it twice:**

| `source_mode` | Input | Batch covariate | Role |
| --- | --- | --- | --- |
| `"consortium"` | consortium protein matrix + `cohort_samples.tsv` | sample-preparation batch | Primary (286 ALS vs 50 controls) |
| `"v5"` | `01b` output + `proteogenomic_metadata.tsv` | search batch | Sensitivity (282 vs 50) |

```bash
Rscript 01_single_layer/02a_protein_differential_abundance.R
```

- *Output:* `AALS_protein_limma_results.csv`, `..._for_fgsea.csv`, `protein_objects.rds`,
  `protein_by_participant_gene.log2.tsv`, `QC/`, `summary.txt`.

**02b_classify_peptide_sources.py** marks each precursor as reference-explained or variant-only. It then
classifies every variant-only peptide as known UniProt isoform, GENCODE-only, or novel candidate, treating
I and L as the same residue.

```bash
python 01_single_layer/02b_classify_peptide_sources.py \
  --pr-matrix /path/pgdb_v5_batch{1,2,3,4,5,6}/quant_tables/diann_report.pr_matrix.tsv \
  --batch-names batch1 batch2 batch3 batch4 batch5 batch6 \
  --mapping $PGDB/proteogenomic_mapping.tsv \
  --uniprot $DATA/UP000005640_9606.fasta.gz $DATA/UP000005640_9606_additional.fasta.gz \
  --gencode $DATA/gencode.v46.pc_translations.fa.gz --outdir $R/02b_classify_peptide_sources
```

- *Output:* `precursor_sources.tsv`, `variant_only_peptides.tsv` (649 peptides, 10 novel), `summary.json`.

**02c_pathway_enrichment.R** runs preranked fgsea on the moderated t-statistic in three
gene-set categories: broad, disease and targeted. **Run it four times:**

| `mode` | `max_gs_size` | Input |
| --- | --- | --- |
| `"rna"` | 300 | 01a results |
| `"protein"` | 300 | 02a consortium results |
| `"rna"` | 500 | 01a results (sensitivity) |
| `"protein"` | 500 | 02a consortium results (sensitivity) |

```bash
# Settings: mode, max_gs_size, input results file, base_out_dir
Rscript 01_single_layer/02c_pathway_enrichment.R
```

- *Output:* `gsea_validation/fgsea_ALL_categories_DREAM_t_nonredundant_combined.csv` and per-category plots.

#### Step 3 (needs step 2)

**03a_pathway_label_permutation.R** retests the 15 top gene sets. It permutes diagnosis labels within
sequencing batch 1,000 times (seed 20261014), refits the model and recomputes NES. A gene set counts as
robust only if its empirical FDR is below 0.05. **Run it four times**, matching the 02c runs
(`mode`, `max_gs_size`, `fgsea_results`, and `rna_rds` or `protein_rds`).

```bash
Rscript 01_single_layer/03a_pathway_label_permutation.R
```

- *Output:* `results_pathway_permutation_1000[_maxsize500]_<mode>.csv`.

**03b_extract_spectral_scores.sh** writes the DIA-NN score columns for every identification of the
variant-only peptides, plus a systematic 1-in-150 background sample. Run it once per batch:

```bash
mkdir -p $R/03c_review_novel_peptides
for b in 1 2 3 4 5 6; do
  bash 01_single_layer/03b_extract_spectral_scores.sh /path/pgdb_v5_batch$b/quant_tables/diann_report.tsv batch$b \
       $R/02b_classify_peptide_sources/variant_only_peptides.tsv $R/03c_review_novel_peptides/scores_b$b.tsv
done
cp $R/02b_classify_peptide_sources/variant_only_peptides.tsv $R/03c_review_novel_peptides/variant_only_peptide_classes.tsv
```

**03c_review_novel_peptides.py** reviews the score evidence for the ten novel candidates. It covers
five dimensions: CScore, spectrum similarity, fragment co-elution, RT error and RT reproducibility. A
dimension is flagged when the candidate is in the worst 10% of length- and intensity-matched reference
identifications, and a candidate fails if two or more dimensions are flagged.

```bash
python 01_single_layer/03c_review_novel_peptides.py $R/03c_review_novel_peptides $R/03c_review_novel_peptides/novel_score_review
```

- *Output:* `novel_score_review_{summary,by_batch,reference_medians}.tsv` and `spectral_review.tsv`
  (`peptide`, `verdict`), which is needed by `03_cross_layer/02`.

### 02_participant_linking: integration pipeline (Stages 1–3)

**00_run_linking_pipeline.py** runs scripts 01–05 in order and writes a run manifest with the
Python version and SHA-256 checksums of each script. Check the inputs first:

```bash
python 02_participant_linking/00_run_linking_pipeline.py --check
python 02_participant_linking/00_run_linking_pipeline.py --nperm 600 --out $R/02_participant_linking
# resume: --from-stage 2 --out <same folder>
```

| Script | Stage | What it does | Main output |
| --- | --- | --- | --- |
| `01_link_peptides_to_events.py` | 1 | Links each variant-only peptide to the annotated isoform or fusion event of its database entry and records gene RNA in the same participant | `links_peptide_event.tsv`, `novel_peptides_detected.tsv` |
| `02_extract_sv_carriers.py` | 1b | Extracts carriers and cohort carrier counts from the Objective Two intersection VCF | `sv_carriers.tsv` |
| `03_link_svs_to_events.py` | 2 | Links each SV in a participant to an isoform event within 5 kb or a fusion breakpoint within 100 kb; builds variant→event→peptide chains | `links_variant_event.tsv`, `chains_variant_event_peptide.tsv`, `summary.json` |
| `04_test_rare_sv_rna_protein.py` | 3 | Tests rare SVs (≤ 17 carriers) against each gene ± 5 kb. An effect needs \|log2FC\| ≥ 0.5 plus \|z\| ≥ 2.5 (one carrier) or Mann–Whitney p < 0.05. Tier A = RNA and protein effect; tier B = either | `variant_gene_rna_protein.tsv`, `..._summary.json` |
| `05_permutation_null.py` | 3 | Reassigns carrier labels 600 times and compares the number of effects with the observed number | `permutation_null_summary.json` |

Shared helpers: `lib/paths.py` (inputs and batches) and `lib/rna_answerals.py` (participant × gene
log2(CPM+1) from the release 7 counts).

### 03_cross_layer: agreement between layers and evaluation

#### Step 1 (scripts 01a–01c can run in any order)

**01a_cross_omics_agreement.py** builds the gene evidence matrix (prioritised SV, RNA, protein, fusion,
isoform and novel peptide, ALSoD category) and the RNA–protein agreement of ALS-vs-control effects. It runs
the carrier tests (robust z, Mann–Whitney) for each primary SV candidate and builds fusion→peptide chains.

```bash
python 03_cross_layer/01a_cross_omics_agreement.py \
  --rna-results $R/01a_rna_differential_expression/primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv \
  --protein-results $R/02a_protein_differential_abundance_consortium/AALS_protein_limma_results.csv \
  --fusion-dir $R/01d_filter_fusions --peptide-dir $R/02b_classify_peptide_sources \
  --sv-primary $SV/sv_audited_release/primary_candidates.tsv --sv-support $SV/sv_audited_release/participant_support.tsv \
  --alsod $SV/alsod_gene_list.csv --rna-counts $COUNTS --rna-coldata $COLDATA --gtf $DATA/ensg_symbol.tsv \
  --protein-matrix $R/01b_consolidate_proteomic_batches/protein_by_run.log2.tsv \
  --protein-samples $R/01b_consolidate_proteomic_batches/sample_metadata.tsv \
  --pgdb-metadata $PGDB/proteogenomic_metadata.tsv --outdir $R/01a_cross_omics_agreement
```

- *Output:* `gene_evidence_matrix.tsv`, `layer_intersections.tsv`, `rna_protein_concordance.tsv`,
  `sv_candidate_carrier_effects.tsv`, `fusion_peptide_chains.tsv`, `summary.json`.

**01b_sv_fusion_overlap.py** counts filtered fusion calls whose two breakpoints both lie inside a rare SV
(≤ 17 carriers) in the same participant. It computes the expected count by assigning each call to a
random participant (Poisson, plus 1,000 label permutations), and reports RNA and protein in the carriers.

```bash
python 03_cross_layer/01b_sv_fusion_overlap.py --fusions $R/01d_filter_fusions/fusion_calls_pass.tsv \
  --sv-tests $R/01e_sv_carrier_expression_scan_unfiltered/{intersection,union_only}_sv_gene_expression_tests.tsv \
  --coldata $COLDATA --protein $R/01b_consolidate_proteomic_batches/protein_by_participant.log2.tsv \
  --pgdb-metadata $PGDB/proteogenomic_metadata.tsv --outdir $R/01b_sv_fusion_overlap
```

- *Output:* `sv_fusion_overlap.tsv`, `sv_fusion_overlap_rna_effects.tsv`, `sv_fusion_overlap_protein_in_carriers.tsv`, `summary.json`.

**01c_check_duplications_in_wgs.py** counts reads in the six fusion-containing duplications with pysam.
It reports depth inside versus flanking windows (MAPQ ≥ 20, primary, non-duplicate reads), plus
outward-facing pairs and split reads for tandem orientation, against shifted control windows.
*TODO: add this script (`dupcheck.py`, currently stored with the alignments) and its usage.*

#### Step 2 (needs step 1 and `01_single_layer/03c`)

**02_evaluation_table.py** records, for each candidate (primary SVs, SVs in ALS genes, novel peptides,
isoform peptides, recurrent fusions), the conclusion from its own layer, the matched evidence from the other
layers, the integrated conclusion and the change class (Table 6.7 rules).

```bash
python 03_cross_layer/02_evaluation_table.py --rna-counts $COUNTS --rna-coldata $COLDATA --gene-map $DATA/ensg_symbol.tsv \
  --sv-primary $SV/sv_audited_release/primary_candidates.tsv --sv-support $SV/sv_audited_release/participant_support.tsv \
  --sv-scan $R/01e_sv_carrier_expression_scan_filtered/{intersection,union_only}_sv_gene_expression_tests.tsv \
  --sv-tables $SV/annotsv_prioritization/intersection_filtered/Supplementary_Table_AnnotSV_intersection_event_prioritisation.tsv \
              $SV/annotsv_prioritization/union_only_filtered/Supplementary_Table_AnnotSV_union_only_event_prioritisation.tsv \
  --peptides $R/02b_classify_peptide_sources/variant_only_peptides.tsv --protein-cohort $DATA/cohort_samples_1-6.tsv \
  --fusion-dir $R/01d_filter_fusions --spectral-review $R/03c_review_novel_peptides/spectral_review.tsv \
  --protein-matrix $R/01b_consolidate_proteomic_batches/protein_by_run.log2.tsv \
  --protein-samples $R/01b_consolidate_proteomic_batches/sample_metadata.tsv --pgdb-metadata $PGDB/proteogenomic_metadata.tsv \
  --rna-results $R/01a_rna_differential_expression/primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv \
  --protein-results $R/02a_protein_differential_abundance_consortium/AALS_protein_limma_results.csv \
  --outdir $R/02_evaluation_table
```

- *Output:* `evaluation_main_table.tsv`, `evaluation_full.tsv`, `evaluation_summary.tsv`, `summary.json`.

### figures: Chapter 6 figures

**make_chapter6_figures.R** draws Figure 6.1 (positive control, from `01e` unfiltered) and Figure 6.3
(change in conclusion, from `02_evaluation_table`) using the saved tables. It does not refit any model.

```bash
Rscript figures/make_chapter6_figures.R
```

Figure 6.2 shows FusionInspector views exported from the nf-core/rnafusion output; no script draws it.

## Script-to-dissertation map

| Script | Chapter 6 methods | Results, tables and figures |
| --- | --- | --- |
| 01_single_layer/01a | 6.2.5 Quality control (RNA); 6.2.10 Transcriptomic DE and pathway analysis | Single layer: gene expression in ALS vs healthy controls |
| 01_single_layer/01b | 6.2.5 Failed proteomic runs; Table 6.3 | Cohort and data quality |
| 01_single_layer/01c | Table 6.3 (fusion samples processed) | Cohort and data quality |
| 01_single_layer/01d | 6.2.9 Fusion analysis; Table 6.5 | Single layer: fusions |
| 01_single_layer/01e (unfiltered) | 6.2.7 Carrier vs non-carrier expression scan; Positive control | Consequences of SVs for RNA: Positive control, Genome-wide scan; Figure 6.1 |
| 01_single_layer/01e (filtered) | 6.2.7 Structural variant analysis | SVs in ALS genes |
| 01_single_layer/02a | 6.2.11 Conventional proteomic analysis | Single-layer protein results and the batches 1–6 sensitivity analysis |
| 01_single_layer/02b | 6.2.12 Proteogenomic search and peptide-source classification | Contribution of the proteogenomic database; Table 6.11 |
| 01_single_layer/02c | 6.2.10 (pathways); Appendix Tables 6A.1–6A.2 | Gene-set results, RNA and protein (300 and 500 genes) |
| 01_single_layer/03a | 6.2.10 (label permutation); 6.2.15 sensitivity analyses | Appendix Table 6A.4 |
| 01_single_layer/03b–03c | 6.2.12 (score-based spectral review) | Novel peptide candidates checked against RNA; Table 6.12 |
| 02_participant_linking (Stages 1–2) | 6.2.13 Participant-level event linking; Event-linking windows | Contribution of the proteogenomic database (peptide links); Linking variants to isoform events and fusions |
| 02_participant_linking (Stage 3, null) | 6.2.13; 6.2.6 statistical principles | RNA and protein levels in carriers of rare SVs; Table 6.15 |
| 03_cross_layer/01a | 6.2.7 Primary candidates; 6.2.13 Gene- and participant-level agreement; Fusion–peptide concordance | Primary candidates; Agreement between layers at the gene level |
| 03_cross_layer/01b | 6.2.13 Event-linking windows (containment rule) | Fusion transcripts coinciding with rare duplications; Table 6.16 |
| 03_cross_layer/01c | 6.2.13 WGS confirmation of duplications | Fusion transcripts coinciding with rare duplications |
| 03_cross_layer/02 | 6.2.14 Candidate evidence grading; 6.2.15 Evaluation of integration; Tables 6.6, 6.7 | Evaluation of the integrated interpretation; Table 6.17; Figure 6.3 |
| figures/make_chapter6_figures.R | none | Figures 6.1, 6.3 |

Table 6.2 (design), Table 6.4 (comparisons) and Appendix Table 6A.3 (counting units) describe the study
design; no script produces them. The Discussion (Chapter 7) draws on these results but adds no new analysis.

## Reproducibility notes

These match Section 6.2 (Reproducibility) and Appendix Table 6A.5.

- **Seeds:**
  - pathway label permutation: 20261014;
  - SV-scan empirical null and evaluation table: 1;
  - Stage 3 carrier permutation (600) and fusion label permutation (1,000): not saved, so those two results reproduce only up to Monte Carlo variation.
- **Software records:** R `sessionInfo.txt` is saved with the DE and DA outputs. The linking pipeline writes
  the Python version and script SHA-256 checksums to `run_manifest.json`.
- **Not used:** the nf-core/rnasplice quantitative outputs (Salmon, SUPPA, rMATS) were invalidated by a
  library-strandedness error. Splice events enter only as search-database entries (Section 6.2.8).
- **Superseded database:** every peptide-level result uses the v5 search database from Chapter 5, which was later superseded. No result uses v7.
- **Upstream parameter files:** *TODO: add the nf-core/rnafusion, nf-core/rnasplice and quantmsdiann
  parameter files to `workflows/`, since the chapter states they are kept with the code.*

## Licence and citation
