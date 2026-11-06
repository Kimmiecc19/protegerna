Markdown · README.md

# Objective Three: proteogenomic search database (Chapter 5)

This folder contains the code for **Objective Three** of the dissertation, reported in **Chapter 5: Beyond the reference proteome: translating RNA events into a proteogenomic search database**.

It covers four things:

1. **Detect splice and fusion events** in Answer ALS RNA-seq: rMATS and SUPPA (nf-core/rnasplice) and FusionInspector (nf-core/rnafusion).
2. **Build a cohort-level proteogenomic search database.** A configuration-driven Python workflow turns the events into protein sequences and merges them with the UniProt reference proteome and cRAP.
3. **Search the Answer ALS DIA proteomes** with quantmsdiann (DIA-NN). Each batch is searched once against the proteogenomic database and once against a reference-only database.
4. **Compare the two searches** and identify candidate non-reference peptides.

The search database and its DIA-NN searches are inputs to Objective Four (`../objective4_integration`, Chapter 6).

> **Status of the database builds (Figure 5.4).**
>
> - Every peptide-level result in Chapters 5 and 6 comes from the **search database** (v5, `03_search_database`).
> - The **revised database** (v7, `04_revised_database`) was built with corrected code only to describe how stricter filters change database composition. **It was never searched.**
> - The splice events behind the database come from nf-core/rnasplice outputs that were run with the wrong library strandedness (reverse-stranded libraries processed as forward). Splice-derived entries therefore lack valid RNA support (Chapter 7, Section 7.3.3).
> - A database entry is a candidate sequence, not evidence that the protein is expressed.

## Contents

- [Workflow at a glance](#workflow-at-a-glance)
- [Data required](#data-required)
- [Software](#software)
- [How to run each step](#how-to-run-each-step)
- [Script-to-dissertation map](#script-to-dissertation-map)
- [Reproducibility notes](#reproducibility-notes)
- [Previous file names](#previous-file-names)

## Workflow at a glance

```text
Answer ALS RNA-seq FASTQ (412 samples)         Answer ALS DIA mzML (417 runs)
            │                                              │
01_sample_batches        six stratified batches · confirm DIA acquisition mode
            │                                              │
02_event_detection       nf-core/rnasplice (rMATS, SUPPA) · nf-core/rnafusion (FusionInspector)
            │                                              │
03_search_database       GENCODE validation → fusion / rMATS / SUPPA reconstruction → merge → QC → release report
            │                         └── 04_revised_database (v7, comparison only, not searched)
            │                                              │
05_proteomic_search      reference-only database · quantmsdiann: reference-only and proteogenomic searches
            │
06_search_assessment     search comparison · candidate peptides · peptide lengths · fusion peptides
```

Numbers give the run order. Scripts in the same folder that share a number with different letters (`02a`, `02b`) don't depend on each other.

The Nextflow version of the database workflow, **nf-core/protegerna** (1.0.0dev), is kept in its own repository, [github.com/Kimmiecc19/nf_protegerna](https://github.com/Kimmiecc19/nf_protegerna). It was tested on synthetic data (Table 5.12) and on one Answer ALS participant, but no searched database was built with it; see [nf-core/protegerna](#nf-coreprotegerna-nextflow-implementation) below.

## Data required

| Data | File(s) | Used in |
| --- | --- | --- |
| Answer ALS RNA-seq FASTQ files, 346 participant samples + 66 recurring-control samples | per-batch samplesheets | 02 |
| Answer ALS DIA proteomic runs (SCIEX TripleTOF 6600, SWATH-MS), 346 participant runs + 71 recurring-control runs | `.mzML` files; per-batch SDRF files | 01, 05 |
| Answer ALS sample mapping and metadata | `Sample Mapping File Feb 2024.csv`, `Sample Mapping README.txt`; sex, diagnosis, sequencing and shipment batch | 01 |
| GRCh38 primary assembly (Ensembl 112) | `Homo_sapiens_GRCh38_46_dna_primary_assembly.fa` (+ `.fai`) | 03, 04 |
| GENCODE v46 annotation | `Homo_sapiens_GRCh38_46.gtf` → `gencode_v46.gtf.db`; `gencode.v46.pc_translations.fa` | 03, 04, 06 |
| UniProt human reference proteome UP000005640, release 2026_01 | `UP000005640_9606.fasta` (canonical); `UP000005640_9606_additional.fasta.gz` (isoforms) | 03, 04, 06 |
| Reviewed (Swiss-Prot) human UniProt entries including isoforms | `uniprot_human_reviewed_isoforms.fasta`, downloaded by `05/01` | 05 |
| cRAP contaminants (downloaded 2023-07-04; 116 entries) | `crap.fasta` | 03, 05 |
| nf-core/rnasplice and nf-core/rnafusion references | GRCh38 genome, GTF, STAR, Salmon and STAR-Fusion / FusionCatcher / Arriba indices | 02 |

Answer ALS data are available under the consortium's data-use terms. Do not commit them, or the FASTA databases and search results, to a public repository.

## Software

| Tool | Version | Step |
| --- | --- | --- |
| Nextflow + Apptainer | Nextflow ≥ 25.10.4 for nf-core/protegerna | 02, 05 |
| nf-core/rnasplice | 1.0.3 | 02 |
| nf-core/rnafusion | 4.0.0 (Arriba, STAR-Fusion, FusionCatcher, fusion-report, FusionInspector) | 02 |
| bigbio/quantmsdiann | 2.2.0 with DIA-NN 1.8.1 | 05 |
| Python (database workflow) | 3.11.13 with biopython 1.88, gffutils 0.14, pandas 3.0.1, pyfaidx 0.9.0.4, tqdm. Environment: `environment.yml`; software version 0.1.0 | 03, 04 |
| Python (other scripts) | pandas, numpy, scikit-learn (batches), pyteomics + matplotlib (acquisition mode) | 01, 06 |

Install the database workflow from inside its package folder. This gives the commands `proteogenomic-workflow`, `proteogenomic-validate-reference`, `proteogenomic-fusion`, `proteogenomic-rmats`, `proteogenomic-suppa`, `proteogenomic-merge`, `proteogenomic-qc` and `proteogenomic-release-report`:

```bash
conda env create -f 03_search_database/proteogenomic_db/environment.yml
conda activate proteogenomic-database-reconstruction
pip install -e 03_search_database/proteogenomic_db
```

## How to run each step

### 01_sample_batches: batches and acquisition mode

**01_make_stratified_batches.py** splits the 347 participants into six artificial batches with scikit-learn `StratifiedKFold`, stratified on sex, diagnosis, original sequencing batch and shipment batch. The recurring-control samples (BTC and BDC) are set aside first and then added back in round-robin order. Each participant gets the same batch number in the RNA and proteomic layers.

> **TODO:** this script is not yet in the repository. Add it with its random seed and the output samplesheets.

**02_detect_acquisition_mode.py** reads the precursor isolation windows of the first 5,000 MS2 spectra of each mzML file. It classes a file as DIA when the mean isolation width is above 5 m/z and the number of distinct widths is less than half the spectra read.

```bash
python 01_sample_batches/02_detect_acquisition_mode.py /path/to/mzML --outdir results/01_acquisition_mode \
  --max-scans 5000 --dia-threshold 5
```

- *Output:* a summary CSV, plus plots unless `--no-plot` is given.
- *Result:* all 153 files checked were DIA, with mean isolation width 9.49 m/z and 19 distinct widths.

### 02_event_detection: splice and fusion events

Edit the paths in each launch script and parameter file, then run once per batch.

**01_build_rnafusion_references.sh** builds the nf-core/rnafusion references (`rnafusion_build.config`).

**02a_run_rnasplice.sh** runs nf-core/rnasplice 1.0.3 with `params/rnasplice.json`, `params/rnasplice.config` and the CASE-vs-CTRL contrast file:

```bash
bash 02_event_detection/02a_run_rnasplice.sh     # nextflow run nf-core/rnasplice -r 1.0.3 --input samplesheet_batchN_rnasplice.csv --contrasts rnasplice_contrast.csv -params-file ... -profile apptainer
```

- *Used later:* the rMATS JC tables `rmats_post/{SE,A3SS,A5SS,MXE,RI}.MATS.JC.txt` and the SUPPA event file `suppa/generate_events/per_local_event/events.ioe` from each batch.
- *Not used:* the Salmon, SUPPA PSI and rMATS differential-splicing values.

> **TODO:** add `rnasplice_contrast.csv`. The launch script references it, but it is not in the repository.

**02b_run_rnafusion.sh** runs nf-core/rnafusion 4.0.0 (`--tools all`) with `params/rnafusion.json` and `params/rnafusion.config`:

```bash
bash 02_event_detection/02b_run_rnafusion.sh     # nextflow run nf-core/rnafusion -r 4.0.0 --input samplesheet_batchN_rnaseqfusion.csv --tools all -params-file ... -profile apptainer
```

- *Used later:* `fusioninspector/<sample>.FusionInspector.fusions.abridged.tsv` for every sample (FusionInspector output for 411 of the 412 samples).

### 03_search_database: build the search database (v5)

**01_build_gtf_database.py** converts the GENCODE v46 GTF into the gffutils database that the workflow reads.

```bash
python 03_search_database/01_build_gtf_database.py      # edit gtf_file / db_file at the top
```

**02_build_search_database.sh** runs the workflow with the frozen search-database configuration. `config/workflow.publication.v5.toml` (profile `publication`) sets every input path and parameter; its paths are relative to the folder that holds `data/` and `results/`. First edit the absolute rnasplice and rnafusion input paths in the TOML. The script always runs the bundled v5 code in `proteogenomic_db/` (never an installed command) and needs Python ≥ 3.11:

```bash
bash 03_search_database/02_build_search_database.sh --project-dir . --dry-run   # print every resolved command
bash 03_search_database/02_build_search_database.sh --project-dir . --explain   # show each resolved setting and its source
bash 03_search_database/02_build_search_database.sh --project-dir .             # build; --stage NAME runs one stage
```

After a full build, the script compares the FASTA with the dissertation's search database (80,657 entries, MD5 `3f8ed11769fcd5a62587b528cd2eb52a`) and warns if they differ. A timestamped log is written to the output folder.

The workflow runs these stages in order, and the merge cannot run unless the GENCODE validation passed:

| Stage | Module (inside `proteogenomic_db/`) | Main output in `results/pgdb_publication_rerun_v5/` |
| --- | --- | --- |
| 1. Validate GENCODE translation | `validate_gencode_translation.py` | `gencode_translation_concordance.{tsv,json}` |
| 2a. Reconstruct fusion proteins | `fusiontoprotein.py` | `fusion.primary.fasta`, `fusion.biological.tsv`, `fusion.metadata.tsv` |
| 2b. Reconstruct rMATS proteins | `rmatstoprotein.py` | `rmats.primary.fasta`, `rmats.consequences.tsv`, `rmats.events.tsv` |
| 2c. Reconstruct SUPPA proteins | `suppatoprotein.py` | `suppa.primary.fasta`, `suppa.consequences.tsv` |
| 3–4. Merge with UniProt + cRAP; DIA-suitability filter; exact-sequence deduplication | `merge_proteogenomic_database.py` | **`proteogenomic_database.fasta`** (80,657 entries; MD5 `3f8ed11769fcd5a62587b528cd2eb52a`), `proteogenomic_metadata.tsv`, `proteogenomic_mapping.tsv`, `proteogenomic_summary.{tsv,json}` |
| 5. FASTA QC and quantmsdiann validation | `proteogenomic_fasta_qc.py` | `qc/` |
| 6. Caller-stratified release report | `release_report.py` | `release_report.{tsv,json}` |

Settings, from the TOML:

- **rMATS:** ≥ 3 inclusion and ≥ 3 skipping junction reads summed across samples. No FDR, ΔPSI or SUPPA PSI threshold.
- **Fusions:** ≤ 3 transcripts per partner, breakpoint snap ≤ 25 nt, ≥ 30 retained coding nt per partner.
- **Digestion:** trypsin, 7–40 aa, ≤ 3 missed cleavages; minimum protein length 6 aa.
- **Reference-unique peptides:** required for SUPPA products and fusion junctions, but not for rMATS products.
- **Excluded for every source:** incomplete-CDS and predicted-NMD products. Rescue tiers are off.

Each stage saves its resolved configuration hash, software version and input checksums in `.proteogenomic_state/`. With `resume = true`, a stage is rerun only when its configuration or inputs change.

**03_summarise_fusion_concordance.py** compares the reconstructed fusion proteins with FusionInspector's predicted peptides and frames.

```bash
python 03_search_database/03_summarise_fusion_concordance.py results/pgdb_publication_rerun_v5/fusion.biological.tsv \
  --output results/pgdb_publication_rerun_v5/qc/fusion_prediction_concordance.md
```

### 04_revised_database: comparison build (v7, not searched)

**01_build_revised_database.sh** runs the corrected code (`04_revised_database/proteogenomic_db/`) with `config/workflow.publication.v7.filtered.toml`. The genome, annotation, translation check, digestion, fusion parameters and merge rules are the same as the search database. The corrections are:

- fusion processing gives the same result whatever order the parallel workers finish in;
- failing rMATS products are excluded rather than flagged;
- rMATS products need a reference-unique peptide;
- peptide uniqueness is checked against the UniProt isoforms too;
- SUPPA events are read once, not six times.

```bash
bash 04_revised_database/01_build_revised_database.sh --project-dir . --dry-run
bash 04_revised_database/01_build_revised_database.sh --project-dir .
```

- *Output:* `results/protegerna_v7_filtered/` (30,031 sequences). The script checks the FASTA against the reported build (MD5 `e6b4632bafd6a6a026fc4c18fff06ca6`).
- Install the v5 and v7 code in separate environments if you install them at all: both provide `proteogenomic-workflow`. The two build scripts avoid the clash by always running their own bundled copy.

**02_compare_search_and_revised_databases.py** compares the composition of the two builds and checks fusion consistency across samples.

```bash
python 04_revised_database/02_compare_search_and_revised_databases.py \
  --v5-dir results/pgdb_publication_rerun_v5 --v7-dir results/protegerna_v7_filtered \
  --fusion-table fusion.biological.tsv --out results/04_v5_v7_comparison.tsv
```

### 05_proteomic_search: quantmsdiann searches

**01_make_reference_database.py** downloads the reviewed human UniProt entries with isoforms and cRAP, then deduplicates them by exact sequence into `human_reference_deduplicated.fasta` (42,562 sequences). It was built in February 2026, before the proteogenomic workflow existed.

```bash
python 05_proteomic_search/01_make_reference_database.py     # writes protein_databases/ and database_build_log.txt
```

**02a_run_quantmsdiann_reference.sh** and **02b_run_quantmsdiann_proteogenomic.sh** run bigbio/quantmsdiann 2.2.0 once per batch, using the per-batch SDRF files. Both use library-free DIA-NN 1.8.1, ≤ 3 missed cleavages, peptides of 7–40 aa, precursor m/z 400–2,400 and 1% precursor and protein-group FDR. The only difference is the database: `params/reference.json` (`human_reference_deduplicated.fasta`) versus `params/proteogenomic_v5.json` (`proteogenomic_database.fasta`).

```bash
nextflow run bigbio/quantmsdiann -r 2.2.0 -profile apptainer \
  --input sdrf_batchN.sdrf.tsv --outdir results/quantms/reference/batchN \
  -params-file 05_proteomic_search/params/reference.json -c 05_proteomic_search/params/reference.config
nextflow run bigbio/quantmsdiann -r 2.2.0 -profile apptainer \
  --input sdrf_batchN.sdrf.tsv --outdir results/quantms/pgdb/pgdb_v5_batchN \
  -params-file 05_proteomic_search/params/proteogenomic_v5.json -c 05_proteomic_search/params/reference.config
```

- *Output (per batch):* `quant_tables/diann_report.tsv`, `diann_report.stats.tsv`, `diann_report.pr_matrix.tsv`, `diann_report.pg_matrix.tsv`, `diann_report.gg_matrix.tsv`, `diann_report.unique_genes_matrix.tsv`, `pipeline_info/`.
- *Failed runs:* a run is classed as failed when it has fewer than 1,000 precursors in `diann_report.stats.tsv`.

`params/proteogenomic_v5.json` is the parameter file recorded by the v5 searches themselves (copied from `pgdb_v5_batch*/pipeline_info/params_*.json`).

### 06_search_assessment: compare the two searches

**01a_extract_passing_rows.sh** keeps the main-report rows that pass Q.Value, Global.Q.Value, PG.Q.Value and Global.PG.Q.Value ≤ 0.01. Run it for each batch and each search:

```bash
for b in 1 2 3 4 5 6; do
  bash 06_search_assessment/01a_extract_passing_rows.sh results/quantms/pgdb/pgdb_v5_batch$b/quant_tables/diann_report.tsv results/06/v5_b$b
  bash 06_search_assessment/01a_extract_passing_rows.sh results/quantms/reference/batch$b/quant_tables/diann_report.tsv results/06/ref_b$b
done
```

- *Output:* `{v5,ref}_b{1..6}.pass.tsv.gz` and `.counts.txt`.

**01b_make_sequence_source_table.py** writes `v5_id_source.tsv` (headerless: `sequence_id`, `sources`, `gene`). It maps each search-database entry to every producer that contributed to it (reference, crap, rmats, suppa, fusioninspector; joined with `;`):

```bash
python 06_search_assessment/01b_make_sequence_source_table.py --pgdb-dir results/pgdb_publication_rerun_v5 \
  --out results/06/v5_id_source.tsv
```

The gene column is informational. By default it is taken from each entry's last mapping record, which reproduces the dissertation file exactly; `--gene-from metadata` uses the database metadata instead.

**01c_collect_diann_summary_tables.sh** copies each search's `stats`, `pg_matrix`, `gg_matrix` and `unique_genes_matrix` tables, and the SDRF of each batch, into `results/06/small/` as `{ref,v5}_b{N}.*.tsv` and `sdrf_b{N}.tsv`, with a checksum manifest. The dissertation's reference-only Batch 1 is the 27 October repeat (`batch1_fixed`):

```bash
bash 06_search_assessment/01c_collect_diann_summary_tables.sh \
  --ref-root results/quantms/reference --ref-override 1=batch1_fixed \
  --pgdb-root results/quantms/pgdb --out results/06
```

Both outputs were checked against the files used in the dissertation: `v5_id_source.tsv` and all 54 `small/` tables are identical.

**02a_compare_reference_and_proteogenomic.py** computes every comparison metric with one rule per metric:

- per-file precursor change;
- distinct precursors and peptides;
- protein groups;
- specific proteins per file;
- shared gene-group labels and per-file correlation;
- repeated-control CV;
- gained and lost peptides.

```bash
python 06_search_assessment/02a_compare_reference_and_proteogenomic.py results/06 results/06/reference_vs_v5_metrics.tsv
```

**02b_find_novel_candidate_peptides.py** finds peptides that map only to splice- or fusion-derived entries and are absent, with I and L treated as identical, from the reference-only database, UniProt canonical and additional sequences, and GENCODE v46 translations.

```bash
python 06_search_assessment/02b_find_novel_candidate_peptides.py results/06 \
  human_reference_deduplicated.fasta data/UP000005640_9606.fasta.gz data/UP000005640_9606_additional.fasta.gz \
  data/gencode.v46.pc_translations.fa.gz results/06/custom_only_peptides_b1to6.tsv
```

**02c_compare_peptide_lengths.py** digests both databases in silico (same rule as the searches) and compares theoretical with observed peptide lengths.

```bash
python 06_search_assessment/02c_compare_peptide_lengths.py --ref-fasta human_reference_deduplicated.fasta \
  --v5-fasta results/pgdb_publication_rerun_v5/proteogenomic_database.fasta --six-dir results/06 \
  --out results/06/peptide_lengths.tsv
```

**02d_summarise_fusion_peptides.py** counts the peptides mapped to fusion-associated sequences in each batch. It reports:

- how many are also mapped to a reference or cRAP sequence;
- how many cross a fusion junction;
- which junction peptides are unique in the target database (I/L equivalent), with their files (CASE/CTRL), median spectrum similarity and median PEP.

On its first run it writes `junction_peptides.tsv.gz` from the database's `proteogenomic_peptides.tsv`:

```bash
python 06_search_assessment/02d_summarise_fusion_peptides.py --six-dir results/06 \
  --pgdb-peptides results/pgdb_publication_rerun_v5/proteogenomic_peptides.tsv \
  --out-prefix results/06/table_5_5_fusion_peptides
```

- *Output:* `table_5_5_fusion_peptides.tsv` (one row per batch) and `table_5_5_fusion_peptides.junction_peptides.tsv` (one row per batch and observed junction peptide).
- *Check:* every Table 5.5 value is reproduced for all six batches, and the rebuilt `junction_peptides.tsv.gz` is identical to the one used in the dissertation.

### nf-core/protegerna: Nextflow implementation

The pipeline lives in its own repository, [github.com/Kimmiecc19/nf_protegerna](https://github.com/Kimmiecc19/nf_protegerna), whose README explains how to run it. It bundles the revised (v7) code as of 17 October 2026, with the search-database settings. It runs the same stages as `03_search_database`, without the release report.

The dissertation reports two runs:

| Run | Inputs | Reported in |
| --- | --- | --- |
| 19 Oct 2026, `-profile test` (`tender_poincare`) | synthetic fixture: 6 records merged into 4 unique sequences | Table 5.12 |
| 2 Nov 2026, `-profile publication` (`grave_pauling`) | FusionInspector calls of CASE-NEUWY079WUH plus the cohort rMATS and SUPPA outputs, full GRCh38 and GENCODE v46: 61,800 unique sequences | Text after Table 5.12; Figure 5.4 |

The pipeline README lists the repository files that these runs did not use: the nf-core template configurations, CI workflows and nf-test files, and old copies. No database searched in Chapters 5 or 6 was built with the pipeline.

## Script-to-dissertation map

Chapter 5 section names are given as they appear in the chapter.

| Step / script | Chapter 5 methods | Results, tables and figures |
| --- | --- | --- |
| 01_sample_batches/01 | Cohort and experimental material; Appendix 5A.1 | Batch composition (Table 5.6) |
| 01_sample_batches/02 | Appendix 5A.4.3 Confirmation of proteomic data mode | 153 files classed as DIA |
| 02_event_detection | Alternative splicing and gene fusion event detection; Appendix 5A.3 | Inputs to the database; fusion calls also used in Chapter 6 |
| 03_search_database/01–02 (stage 1) | Proteogenomic database reconstruction workflow; Key design choices | Validation of reference protein reconstruction (Table 5.1) |
| 03_search_database/02 (stages 2–4) | Splice- and fusion-derived reconstruction workflows (Figures 5.1–5.3); Appendix 5A.4 | Candidate reconstruction and biological filtering (Table 5.2; Appendix Table 5A.3); Final database composition (Appendix Table 5A.5) |
| 03_search_database/02 (stages 5–6) | Database quality assurance and validation | Theoretical peptide uniqueness; Quality-control assessment (Appendix Tables 5A.2, 5A.4); release report |
| 03_search_database/03 | Database quality assurance and validation | Concordance with FusionInspector predictions (Tables 5.3, 5.4) |
| 04_revised_database | Revised database (comparison release); Figure 5.4 | Effect of additional filtering on database composition; Appendix 5A |
| 05_proteomic_search/01 | DIA proteomics using a proteogenomic database; Appendix 5A | Reference-only database (42,562 sequences) |
| 05_proteomic_search/02a–02b | DIA proteomics using a proteogenomic database; Appendix 5A.4.4 | Quantmsdiann identification: coverage and quantitative quality |
| 06_search_assessment/01a–02a | DIA proteomics using a proteogenomic database; Appendix 5A (calculation of comparison metrics) | Comparison with a reference-only search (Tables 5.7, 5.9); failed runs |
| 06_search_assessment/02b | DIA proteomics (novel peptide definition) | Candidate peptides (Table 5.10) |
| 06_search_assessment/02c | none | Search-space inflation (Table 5.8) |
| 06_search_assessment/02d | none | Quantmsdiann: peptide evidence for event-derived proteins (Table 5.5) |
| nf-core/protegerna (separate repository) | Implementation as a Nextflow pipeline | End-to-end test of the Nextflow pipeline (Table 5.12); one-participant run (Figure 5.4) |

**No script here produces these:**

- **Table 5.11** (candidate-level evidence) combines Table 5.10 with Chapter 6 results: the spectral review and the RNA checks in `objective4_integration`.
- **Table 5.13 and Appendix Table 5A.1** (review of existing proteogenomic tools) come from manual review of the bio.tools records retrieved in Objective One.

**Used later:** `proteogenomic_database.fasta`, `proteogenomic_mapping.tsv`, `proteogenomic_metadata.tsv` and the six `pgdb_v5_batch*` quantmsdiann outputs are inputs to Objective Four (Chapter 6, Sections 6.2.11–6.2.13).

## Reproducibility notes

- **Frozen configurations:** `workflow.publication.v5.toml` (search database) and `workflow.publication.v7.filtered.toml` (revised database). Each stage records a configuration hash, software version 0.1.0 and input SHA-256 checksums in `.proteogenomic_state/`.
- **Search database:** `proteogenomic_database.fasta`, 80,657 entries, MD5 `3f8ed11769fcd5a62587b528cd2eb52a`.
- **Reference-only searches:** these ran from 14 August to 3 September 2026, and Batch 1 was repeated on 27 October 2026. The earlier Batch 1 search (`superseded_ref_b1_without_carbamidomethyl`) is not used.
- **Not implemented:** class-specific FDR and entrapment searches. Non-canonical peptides are reported with DIA-NN's whole-search FDR, as candidates for validation.
- **Nextflow pipeline:** nf-core/protegerna bundles the revised code as it stood on 17 October 2026. It has been tested on synthetic data and one Answer ALS participant, and must be regenerated from the current revised code before a cohort run.

## Licence and citation
