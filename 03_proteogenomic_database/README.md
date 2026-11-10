# Objective Three: proteogenomic search database for DIA (Chapter 5)

**Objective:** develop a proteogenomic workflow that translates gene-fusion and alternative-splicing events into a searchable
protein database for peptide identification and protein inference.

**Research question:** Can splice junctions and fusion transcripts detected from RNA-seq be translated into sample-specific
databases that identify junction and fusion peptides in matched DIA proteomes, with novel identifications controlled separately from
canonical ones? What protein-level conclusions can those peptides support?

**Dissertation:** Chapter 5, *Beyond the reference proteome: translating RNA events into protein hypotheses* (methods 5.2, results
5.3, Appendix 5A). The searches and the database are inputs to Objective Four.

## What is done

```text
RNA-seq FASTQ (412 samples, 6 batches)            DIA mzML (6 batches)
  02_event_detection: rnafusion 4.0.0, rnasplice 1.0.3       |
  03_search_database: v5 database (80,657 entries) ----------+
  04_revised_database: v7 (comparison only, not searched)    |
  05_proteomic_search: quantmsdiann 2.2.0, reference-only and proteogenomic searches
  06_search_assessment: compare the two searches
01_sample_batches: six matched RNA/proteomic batches (run first)
```

The Nextflow implementation (nf-core/protegerna) is in [`../03b_protegerna_nextflow`](../03b_protegerna_nextflow/README.md).

## Steps

| Step | What it does | Dissertation |
| --- | --- | --- |
| [`01_sample_batches`](01_sample_batches/README.md) | Stratified batches; DIA acquisition check | 5.2.2–5.2.4; Table 5.6 |
| [`02_event_detection`](02_event_detection/README.md) | nf-core/rnafusion and nf-core/rnasplice | 5.2.5 |
| [`03_search_database`](03_search_database/README.md) | Build and QC the v5 search database; fusion concordance | 5.2.6–5.2.7, 5.3.1–5.3.7; Tables 5.1–5.4, 5A.2–5A.5; Figures 5.1–5.3 |
| [`04_revised_database`](04_revised_database/README.md) | Revised v7 build for comparison | 5.2.8, 5.3.8 |
| [`05_proteomic_search`](05_proteomic_search/README.md) | Reference database; quantmsdiann searches | 5.2.9 |
| [`06_search_assessment`](06_search_assessment/README.md) | Reference vs proteogenomic comparison | 5.3.8–5.3.12; Tables 5.5, 5.7–5.11 |

Each step folder has its own README with the command used for every script, its inputs and outputs, and what to edit first.

## Data required

| Data | Step | Notes |
| --- | --- | --- |
| Answer ALS RNA-seq FASTQ (346 participants + 66 recurring controls) | 02 | Controlled access |
| Answer ALS DIA runs (SCIEX TripleTOF 6600; 346 participants + 71 recurring controls), per-batch SDRF | 01, 05 | Controlled access |
| Sample mapping and metadata | 01 | via `../00_general/01_filtering_matching_patients/` |
| GRCh38 primary assembly (Ensembl 112); GENCODE v46 GTF and protein translations | 03, 04, 06 | |
| UniProt UP000005640 (2026_01), canonical + isoforms; reviewed human UniProt with isoforms | 03, 05, 06 | |
| cRAP contaminants (116 entries) | 03, 05 | |
| rnafusion and rnasplice references | 02 | Built by `02_event_detection/01_build_rnafusion_references.sh` |

## Software

| Tool | Version | Step |
| --- | --- | --- |
| Nextflow + Apptainer | | 02, 05 |
| nf-core/rnasplice | 1.0.3 | 02 |
| nf-core/rnafusion | 4.0.0 | 02 |
| bigbio/quantmsdiann | 2.2.0 (DIA-NN 1.8.1) | 05 |
| Python (database workflow) | 3.11 with biopython 1.88, gffutils 0.14, pandas, pyfaidx 0.9.0.4, tqdm; `03_search_database/proteogenomic_db/environment.yml` | 03, 04 |
| Python (other scripts) | pandas, numpy, scikit-learn (01), pyteomics + matplotlib (01, acquisition mode) | 01, 06 |

```bash
conda env create -f 03_search_database/proteogenomic_db/environment.yml
conda activate proteogenomic-database-reconstruction
pip install -e 03_search_database/proteogenomic_db
```

## Script-to-dissertation map

Figure 5.4 is a schematic; Tables 5.13 and 5A.1 come from the literature and the Objective One records.

| Item | Caption | Script(s) | Status |
| --- | --- | --- | --- |
| Table 5.1 | Reproduction of GENCODE translations by the coordinate, CDS-phase and translation implementation | `03_search_database/02_build_search_database.sh` | Saved |
| Table 5.2 | Candidate generation by caller, from input events to the final database | `03_search_database/02_build_search_database.sh` | Saved |
| Table 5.3 | Reconstructed fusion proteins compared with FusionInspector peptide sequences and reading frames | `03_search_database/03_summarise_fusion_concordance.py` | Saved |
| Table 5.4 | Fusion concordance within the DIA-eligible subset | `03_search_database/03_summarise_fusion_concordance.py` | Saved |
| Table 5.5 | Peptides mapped to fusion-associated sequences | `06_search_assessment/02d_summarise_fusion_peptides.py` | Partly saved |
| Table 5.6 | Composition of DIA Batches 1–6 | `01_sample_batches/01a_make_stratified_batches.py`, `01_sample_batches/01b_validation.py`, `06_search_assessment/01c_collect_diann_summary_tables.sh` | Saved |
| Table 5.7 | Identification coverage and quantitative quality of reference-only (Ref) and proteogenomic (PG) searches of Batches 1 (B1), 2 (B2) and 3 (B3) | `06_search_assessment/01a_extract_passing_rows.sh`, `06_search_assessment/01b_make_sequence_source_table.py`, `06_search_assessment/01c_collect_diann_summary_tables.sh`, `06_search_assessment/02a_compare_reference_and_proteogenomic.py` | Saved |
| Table 5.8 | Peptide lengths in the two search databases vs identified peptides | `06_search_assessment/02c_compare_peptide_lengths.py` | Saved |
| Table 5.9 | Peptide and precursor overlap between the reference-only and proteogenomic searches | `06_search_assessment/02a_compare_reference_and_proteogenomic.py` | Saved |
| Table 5.10 | Proteogenomic-search peptides absent from the reference-only searches and UniProt (first six rows) | `06_search_assessment/02b_find_novel_candidate_peptides.py` | Saved |
| Table 5.11 | Candidate-level evidence for the six peptides across Chapters 5 and 6 | `06_search_assessment/02b_find_novel_candidate_peptides.py`, `04_integration/01_single_layer/02b_classify_peptide_sources.py`, `04_integration/01_single_layer/04b_review_novel_peptides.py`, `04_integration/03_cross_layer/02_evaluation_table.py` | Saved |
| Table 5.12 | End-to-end smoke test of protegerna on the synthetic test dataset | `03b_protegerna_nextflow/nf_protegerna_workflow_dev/main.nf` | Saved |
| Table 5.13 | Existing proteogenomic database strategies and their influence on workflow design | Literature review | No script |
| Figure 5.1 | Overview of the proteogenomic database reconstruction workflow | `03_search_database/02_build_search_database.sh` | Saved |
| Figure 5.2 | Overview of the splice-derived protein reconstruction workflow | `03_search_database/02_build_search_database.sh` | Saved |
| Figure 5.3 | Overview of the fusion-derived protein reconstruction workflow | `03_search_database/02_build_search_database.sh` | Saved |
| Figure 5.4 | Database builds used in this dissertation and their status | Schematic | Schematic |
| Table 5A.1 | Proteogenomic tools identified in the proteomics and multi-omics records from Chapter 3 | `01_biotools_landscape/02a_filter_biotools.R` | Saved |
| Table 5A.2 | Quality-control and inclusion measures applied during database construction | `03_search_database/02_build_search_database.sh` | Saved |
| Table 5A.3 | Reasons for excluding candidates from the search database | `03_search_database/02_build_search_database.sh` | Saved |
| Table 5A.4 | Quality-control assessment of the final proteogenomic search database | `03_search_database/02_build_search_database.sh` | Saved |
| Table 5A.5 | Final merged proteogenomic database composition | `03_search_database/02_build_search_database.sh` | Saved |

## Reproducibility notes

- Frozen configurations: `03_search_database/config/workflow.publication.v5.toml` and
  `04_revised_database/config/workflow.publication.frozen.toml`; every stage records its configuration hash and input checksums.
- Search database: `proteogenomic_database.fasta`, 80,657 entries, MD5 `3f8ed11769fcd5a62587b528cd2eb52a`.
- Class-specific FDR and entrapment searches were not implemented; non-canonical peptides are reported at DIA-NN's whole-search FDR.
- The nf-core/rnasplice quantitative outputs are not used (strandedness error); only event definitions enter the database.
- The Nextflow launchers in `02_event_detection/` and `05_proteomic_search/` take the batch number as their argument and
  read data, references and output folders from a **Settings** block at the top (environment variables with `/path/to/...`
  placeholders). Their params and config files are the copies in `02_03_params/` and `02_params/`.
- The database TOMLs read the saved rnafusion/rnasplice results in `02_event_detection/`; reference files go in
  `03_proteogenomic_database/data/`. The configuration exactly as run is saved with each database's results.
- COSMIC credentials are read from `COSMIC_USERNAME` / `COSMIC_PASSWD`; never write them in a script or params file.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
