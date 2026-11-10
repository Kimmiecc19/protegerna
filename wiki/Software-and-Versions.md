# Software and versions

Every tool, library and reference resource used in the four objectives, with the version used for the dissertation.

**Source column**, in order of preference:

| Code | Meaning |
| --- | --- |
| **Run** | Recorded by the run itself: `sessionInfo.txt`, a run manifest, an AnnotSV log, a pipeline `software_versions.yml` or pmultiqc version table |
| **Env** | Pinned in an environment, config or container file in the repository |
| **Diss** | Stated in the dissertation (methods, Appendix Table 4A.1 or 6A.5) |
| **n.r.** | Used, but the exact version was **not recorded** in the repository or the dissertation |

Where a recorded version differs from a stated one, both are shown.

---

## 1. Workflow managers, containers and languages

| Tool | Version | Used for | Objective | Source |
| --- | --- | --- | --- | --- |
| Nextflow | 25.10.4 | bigbio/quantmsdiann searches | 3 | Run (pmultiqc) |
| Nextflow | 25.04.7 | nf-core/rnafusion run | 3 | Diss (App. 5A.2.1) |
| Nextflow | 26.10.2 | nf-core/protegerna test run (Table 5.12) | 3 | Diss |
| Nextflow | ≥ 25.10.4 (required) | nf-core/protegerna | 3 | Env (README, `nextflow.config`) |
| Nextflow | n.r. | nf-core/sarek and nf-core/rnasplice runs | 2, 3 | n.r. (the Sarek launcher has a commented-out `NXF_VER=24.04.4`) |
| Apptainer | n.r. | Container runtime for all nf-core pipelines | 2, 3 | n.r. |
| Docker | n.r. | nf-core/protegerna `test` profile run (19 Oct 2026) | 3 | n.r. |
| nf-core template | 4.1.0 | nf-core/protegerna scaffold | 3 | Env (README badge) |
| Python | 3.11.13 | SV audit, fusion audit, linking pipeline, Objective 4 scripts | 2, 4 | Run (run logs, manifests); Diss |
| Python | 3.11.13 | Proteogenomic database workflow (standalone) | 3 | Env (`environment.yml`) |
| Python | 3.11.17 | Proteogenomic code inside the nf-core/protegerna container | 3 | Run (`software_versions.yml`); Env (`conda.yml` pins `python=3.11`) |
| Python | ≥ 3.10 | bio.tools fetch and EDAM mapping | 1 | Diss/README (exact version n.r.; run on Linux 6.8.0) |
| R | 4.6.1 (2026-06-24 ucrt, Windows) | Objective 1 analyses, Objective 4 DE/DA/pathways, dashboard | 1, 2, 4 | Run (manifests, `sessionInfo.txt`) |
| pip | 26.2.1 | nf-core/protegerna environment | 3 | Env |

## 2. Objective 1: bio.tools landscape

| Tool / package | Version | Used for | Source |
| --- | --- | --- | --- |
| bio.tools API | `https://bio.tools/api/tool/` (queried 29 Sep 2026) | Tool retrieval | Run (fetch manifests) |
| Dimensions Metrics API | queried once (Sep 2026) | Citation counts | Diss |
| Europe PMC; Crossref REST API | Crossref API v1 | Publication metadata enrichment | Diss |
| GitHub REST API | frozen cache `github_commit_cache_final.csv` | Commit recency, engagement | Diss; config |
| EDAM ontology | **1.25** (`1.25-20260626T1230Z`) | Operation mapping (`EDAM.owl`, 806 operation classes) | Run (`owl:versionInfo`, EDAM manifest) |
| requests (Python) | 2.32.4 | bio.tools API client | Run (fetch manifests) |
| dplyr | 1.2.1 | Filtering and analysis | Run |
| readr | 2.2.0 | | Run |
| tidyr | 1.3.2 | | Run |
| purrr | 1.2.2 | | Run |
| stringr | 1.6.0 | Filtering | Run (02a manifest) |
| janitor | 2.2.1 | Filtering | Run (02a manifest) |
| curl | 7.1.0 | URL audit | Run (02a manifest) |
| jsonlite | 2.0.0 | | Run |
| httr | 1.4.8 | GitHub queries | Run (03a manifest) |
| yaml | 2.3.12 | Config | Run |
| lubridate | 1.9.5 | Dates | Run |
| glue | 1.8.1 | | Run |
| ggplot2 | 4.0.3 | Figures | Run |
| scales | 1.4.0 | | Run |
| ggrepel | 0.9.8 | | Run |
| patchwork | 1.3.2 | | Run |
| ggridges | 0.5.7 | Ridge plots | Run (03a manifest) |
| rstatix | 1.1.0 | Kruskal–Wallis / Dunn tests | Run (03a manifest) |

## 3. Objective 2: structural-variant workflow

| Tool / package | Version | Used for | Source |
| --- | --- | --- | --- |
| nf-core/sarek | **3.5.1** | Germline SV calling (from `prepare_recalibration`) | Diss (App. Table 4A.1) |
| GATK4 | as supplied by Sarek 3.5.1 | Base-quality score recalibration | Diss |
| Manta | **1.6.0** | SV calling (split-read / read-pair assembly) | Diss |
| TIDDIT | **3.6.1** | SV calling (pairs, split reads, coverage) | Diss |
| CNVkit | as supplied by Sarek 3.5.1 | Run, output **not used** | Diss |
| tabix (htslib) | 1.20 | Sarek VCF concatenation/indexing | Run (Sarek `versions.yml`) |
| snpEff | 5.1 (cache GRCh38.105) | Sarek annotation of raw VCFs | Diss |
| Ensembl VEP | 112 | Sarek annotation of raw VCFs | Diss |
| OctopuSV | **0.3.5** (pre-release) | Clean, correct, caller ∩/∪, cohort merge | Diss |
| bcftools | n.r. | VCF reheadering (`01a_prep_sarek_for_review.sh`); AnnotSV dependency | n.r. |
| AnnotSV | **3.5.8** | Annotation and ACMG/ClinGen ranking | Run (AnnotSV log); Diss |
| Tcl/Tk | 8.6 | AnnotSV runtime | Run (AnnotSV log) |
| bedtools | n.r. | AnnotSV dependency | n.r. |
| variantconvert | bundled with AnnotSV 3.5.8 | AnnotSV TSV → VCF | Run (VCF header) |
| Python | 3.11.13 | Callset QC, prioritisation, raw-call audit, release | Run (`run_log.json`) |
| R | 4.6.1 | proteGErna-SV and Chapter 4 figures | Diss |
| shiny | 1.14.0 | Dashboard | Diss (App. Table 4A.1) |
| shinydashboard | 0.7.3 | Dashboard | Diss |
| DT | 0.34.0 | Dashboard tables | Diss |
| vcfR | 1.16.0 | VCF parsing | Diss |
| shinyjs | 2.1.1 | Dashboard | Diss |
| httr | 1.4.8 | Gene-ID lookup for resource links | Diss |
| jsonlite | 2.0.0 | Gene-ID lookup | Diss |
| ggplot2, dplyr, tidyr, stringr, purrr, readr, scales, patchwork, data.table, stringi | n.r. for these scripts | Chapter 4 figures (`02a`/`02b` R scripts) | n.r. (see Objective 1/4 for the versions used elsewhere) |

## 4. Objective 3: proteogenomic database and DIA searches

### 4.1 Event detection

| Tool | Version | Used for | Source |
| --- | --- | --- | --- |
| nf-core/rnafusion | **4.0.0** | Fusion detection | Diss |
| nf-core/rnafusion | 3.0.2 | Building STAR-Fusion / Arriba / FusionCatcher references | Env (launcher; previously a local 3.0.2 checkout) |
| Arriba; STAR-Fusion; FusionCatcher | as pinned by rnafusion 4.0.0 | Fusion calling | Diss (versions n.r.) |
| fusion-report | as pinned by rnafusion 4.0.0 | Merging and scoring calls | Diss (version n.r.) |
| FusionInspector | as pinned by rnafusion 4.0.0 | Per-sample re-evaluation (abridged output used) | Diss (version n.r.) |
| STAR | as pinned by rnafusion / rnasplice | Alignment (indexes pre-built) | Diss (version n.r.) |
| nf-core/rnasplice | **1.0.3** | Splicing events | Diss |
| rMATS; SUPPA; Salmon | as pinned by rnasplice 1.0.3 | Event calling and quantification (**quantification invalidated**: strandedness error) | Diss (versions n.r.) |

> The exact subtool versions of nf-core/sarek, rnafusion and rnasplice are recorded in each run's
> `pipeline_info/software_versions.yml` on the analysis server. Those folders are not in the repository.

### 4.2 Database construction

| Tool / package | Version | Used for | Source |
| --- | --- | --- | --- |
| Proteogenomic database workflow (`proteogenomic_db`) | **0.1.0** | v5 search database and v7 revised database | Run (`software_version` in manifests); Env (`pyproject.toml`) |
| nf-core/protegerna | **1.0.0dev** | Nextflow implementation (test and single-participant runs) | Diss; Run |
| biopython | 1.88 | Translation | Env; Run |
| gffutils | 0.14 | GENCODE transcript models | Env; Run |
| pandas | 3.0.1 | Tables | Env; Run |
| pyfaidx | 0.9.0.4 | Genome sequence access | Env; Run |
| tqdm | 4.70.0 | Progress | Env; Run |
| pytest; hypothesis | ≥ 8; ≥ 6.100 | Test suite (revised code only) | Env (v7 `environment.yml`) |
| MultiQC | as pinned by nf-core/protegerna | Pipeline-information report only | Env |

### 4.3 DIA searches

| Tool | Version | Used for | Source |
| --- | --- | --- | --- |
| bigbio/quantmsdiann | **2.2.0** | DIA search workflow (12 searches: 6 reference-only, 6 proteogenomic) | Run (pmultiqc); Diss |
| DIA-NN | **1.8.1** | Library-free identification and quantification | Run; Diss |
| OpenMS FileConverter | 3.5.0-pre-HEAD-2025-12-12 | mzML indexing / peak-picking pre-processing | Run (pmultiqc) |
| quantms-utils | 0.0.30 | Samplesheet check, MSstats conversion | Run (pmultiqc) |
| sdrf-pipelines | 0.1.5 | SDRF parsing | Run (pmultiqc) |
| pmultiqc | as pinned by quantmsdiann 2.2.0 | QC report | Run |
| pyteomics; matplotlib | n.r. | DIA acquisition-mode detection (`02_detect_acquisition_mode.py`) | n.r. |
| pandas; numpy; scikit-learn; seaborn | n.r. | Stratified batching (`01a`, `01b`) | n.r. |

All 11 pmultiqc version tables in the repository agree. The batch-4 proteogenomic table lists only the pre-processing
tools.

## 5. Objective 4: multi-omics integration

| Tool / package | Version | Used for | Source |
| --- | --- | --- | --- |
| R | 4.6.1 | DE, DA, pathways, figures | Run (`sessionInfo.txt`) |
| edgeR | **4.10.6** | TMM normalisation | Run; Diss |
| limma | **3.68.5** | voom / protein DA | Run; Diss |
| variancePartition | **1.42.0** | dream mixed model | Run; Diss |
| lme4 | 2.0 | dream back-end | Run |
| fgsea | **1.38.0** | Preranked GSEA | Run; Diss |
| AnnotationDbi | 1.74.0 | Gene ID mapping | Run |
| org.Hs.eg.db | 3.23.1 | Gene annotation | Run |
| BiocParallel | 1.46.0 | Parallel back-end (`SerialParam`) | Run |
| dplyr | 1.2.1 | | Run |
| tidyr | 1.3.2 | | Run |
| tibble | 3.3.1 | | Run |
| stringr | 1.6.0 | | Run |
| readr | 2.2.0 | | Run |
| data.table | 1.18.6.1 | | Run |
| ggplot2 | 4.0.3 | | Run |
| clusterProfiler; enrichplot | n.r. | Optional enrichment and running-score plots | n.r. (not in the saved session info) |
| Python | 3.11.13 | Integration scripts, linking pipeline, fusion catalogue | Run (manifests); Diss |
| pandas; NumPy; SciPy | n.r. | Integration scripts | Diss (versions n.r.) |
| pysam | **0.24.1** | WGS duplication check | Diss |
| IGV | n.r. | Visual inspection of the six duplications | n.r. |

## 6. Reference data and resources

| Resource | Version / release | Used for | Objective | Source |
| --- | --- | --- | --- | --- |
| GRCh38_full_analysis_set_plus_decoy_hla.fa | 1000 Genomes | Reference of the Answer ALS CRAMs; SV calling and WGS check | 2, 4 | Diss |
| GRCh38 primary assembly | Ensembl 112 (GENCODE 46) | RNA pipelines and database reconstruction | 3, 4 | Diss |
| GENCODE annotation and protein translations | **v46** | Transcript models, GENCODE validation, novel-peptide checks | 3, 4 | Diss |
| Ensembl transcripts (AnnotSV) | v113 | AnnotSV gene/transcript annotation | 2 | Diss |
| dbSNP; GATK known indels | dbSNP 138 | Sarek BQSR | 2 | Diss |
| snpEff cache | GRCh38.105 | Sarek annotation | 2 | Diss |
| VEP cache | 112 | Sarek annotation | 2 | Diss |
| ALSoD gene table | accessed 24 Feb 2026 (154 genes) | ALS candidate panel | 2, 4 | Diss |
| STRchive disease loci | hg38 general release | Repeat flag in the raw-call audit | 2 | Diss |
| Arriba references | v2.5.0 | Blacklist, cytobands, known fusions, protein domains | 3 | Diss; Env (`rnafusion.json`) |
| FusionCatcher and STAR-Fusion (CTAT) references | built for GENCODE v46 | Fusion calling | 3 | Diss |
| fusion-report databases; HGNC complete set | n.r. (downloaded with the references) | Fusion annotation | 3 | Diss |
| UniProt human reference proteome UP000005640 | **2026_01** (canonical; + additional isoforms for uniqueness) | Search database reference component; novel-peptide checks | 3, 4 | Diss |
| UniProt reviewed human with isoforms | REST download (42,562 entries) | Reference-only search database | 3 | Diss |
| cRAP contaminants | downloaded 2023-07-04 (116 entries) | Contaminants | 3 | Diss |
| Answer ALS RNA counts | release 7 (`AnswerALS-1276-T-v1`) | Expression analyses | 4 | Diss |
| Answer ALS protein matrix | `AnswerALS-447-P` (pre-batch-corrected) | Primary protein DA | 4 | Diss |
| Answer ALS portal metadata | Feb 2024 snapshot | Cohort matching | 0 | README |
| MSigDB gene sets | **v2026.1** | Pathway analysis | 4 | Diss |
| gnomAD | n.r. (via AnnotSV and resource links) | Population frequency annotation | 2 | Diss |

## 7. Notes and inconsistencies to fix


- **Unrecorded versions.** Sarek, rnafusion and rnasplice subtool versions, bcftools, Apptainer, IGV, and the Python
  packages of the batching, acquisition-mode and integration scripts weren't captured in the repository. 
  - Versions can be found in each run's `pipeline_info/software_versions.yml` from the server.
- R analyses were run on Windows 11 from RStudio. 
- Python analyses and the nf-core pipelines were run on Hemera (Stellenbosch University server) or a Windows Subsystem for Linux (WSL) on my personal device.
