# Installation

This page lists everything you need to run the four objectives. Each objective page repeats the subset it needs.

> **Platform.** The heavy computation (nf-core pipelines) was run on a Linux server with Apptainer and no job scheduler. The
> Python and R analysis scripts run on any Linux or macOS machine. On Windows, use WSL2.

## 1. Clone the repository

```bash
git clone https://github.com/Kimmiecc19/protegerna.git
cd protegerna
```

> The code used in the dissertation can be found in the `v1.0.0-phd` branch and the latest release with the same name.

The Nextflow pipeline is also published separately at
[github.com/Kimmiecc19/nf_protegerna](https://github.com/Kimmiecc19/nf_protegerna).

## 2. Software summary

| Software | Version used | Needed for |
| --- | --- | --- |
| Python | ≥ 3.10 (Obj. 1); 3.11 (Obj. 3 database workflow, Obj. 4) | All objectives |
| R | ≥ 4.6 (Obj. 1); 4.6.1 (Obj. 2, 4) | Obj. 1, 2, 4; cohort preparation |
| Nextflow | ≥ 25.10.4 for nf-core/protegerna; a version compatible with each nf-core release below | Obj. 2, 3 |
| Java | Version compatible with your Nextflow | Obj. 2, 3 |
| Apptainer (Singularity) | – | Obj. 2, 3 (Docker also works for the protegerna `test` profile) |
| conda / mamba | – | Obj. 3 database workflow |
| nf-core/sarek | 3.5.1 (Manta 1.6.0, TIDDIT 3.6.1) | Obj. 2 |
| OctopuSV, bcftools | OctopuSV 0.3.5 | Obj. 2 |
| AnnotSV | 3.5.8 (with GRCh38 annotations) | Obj. 2 |
| nf-core/rnafusion | 4.0.0 | Obj. 3 |
| nf-core/rnasplice | 1.0.3 | Obj. 3 |
| bigbio/quantmsdiann | 2.2.0 (DIA-NN 1.8.1) | Obj. 3 |

## 3. Python environments

### General analysis environment (Objectives 1, 2, 3 helper scripts, 4)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests pandas numpy scipy scikit-learn beautifulsoup4 pyteomics matplotlib pysam==0.24.1
```

| Package | Used by |
| --- | --- |
| `requests` | Obj. 1 (bio.tools API), Obj. 2 (ALSoD / Ensembl REST), Obj. 3 (UniProt download) |
| `pandas`, `numpy` | Obj. 2, 3, 4 |
| `beautifulsoup4` | Obj. 2 (ALSoD scraping), Nextflow syntax reference |
| `scikit-learn` | Obj. 3 stratified batching |
| `pyteomics`, `matplotlib` | Obj. 3 DIA acquisition-mode detection |
| `scipy` | Obj. 4 |
| `pysam` 0.24.1 | Obj. 4 WGS duplication check |

### Proteogenomic database workflow (Objective 3)

The `proteogenomic_db` package has its own pinned environment (Python 3.11, biopython 1.88, gffutils 0.14, pandas,
pyfaidx 0.9.0.4, tqdm):

```bash
conda env create -f 03_proteogenomic_database/03_search_database/proteogenomic_db/environment.yml
conda activate proteogenomic-database-reconstruction
pip install -e 03_proteogenomic_database/03_search_database/proteogenomic_db
```

Run its unit tests to confirm the install:

```bash
pip install pytest   # not included in environment.yml
cd 03_proteogenomic_database/03_search_database/proteogenomic_db
python -m pytest tests
```

The revised v7 build (`04_revised_database/proteogenomic_db`) has its own `environment.yml` and `pyproject.toml`; install it
the same way into a separate environment if necessary.

## 4. R packages

Each Objective 1 R script checks for its packages at start-up and says what is missing. For Objectives 2 and 4, install:

```r
install.packages(c(
  # Objective 2: dashboard and figures
  "shiny", "shinydashboard", "DT", "vcfR", "shinyjs", "httr", "jsonlite",
  "ggplot2", "dplyr", "tidyr", "stringr", "purrr", "readr", "scales",
  "patchwork", "data.table", "yaml"
))

if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")
BiocManager::install(c(
  # Objective 4: differential expression, abundance and enrichment
  "edgeR", "limma", "variancePartition", "fgsea", "clusterProfiler",
  "enrichplot", "org.Hs.eg.db", "BiocParallel"
))
```

Alternatively, add the same check to the scripts in objectives 2 and 4, so that they install missing packages automatically.

Versions used for the dissertation: R 4.6.1, shiny 1.14.0, shinydashboard 0.7.3, DT 0.34.0, vcfR 1.16.0, shinyjs 2.1.1,
httr 1.4.8, jsonlite 2.0.0, edgeR 4.10.6, limma 3.68.5, variancePartition 1.42.0, fgsea 1.38.0. 
The R analyses save a `sessionInfo.txt` with their results, which records the full package list.

## 5. Nextflow and containers

Several nf-core pipelines are used for objectives 2, 3, and 4. 
Follow the installation process for [Nextflow](https://www.nextflow.io/docs/latest/getstarted.html) or [nf-core](https://nf-co.re/docs/get_started/environment_setup/overview) and [Apptainer](https://apptainer.org/docs/admin/main/installation.html).

```bash
# Nextflow (needs Java)
curl -s https://get.nextflow.io | bash
mv nextflow ~/bin/          # depends on user PATH
nextflow -version

# Check Apptainer
apptainer --version
```

The pipelines used are:
[nf-core/sarek 3.5.1](https://nf-co.re/sarek/3.5.1) (Objective 2)
[nf-core/rnafusion 4.0.0](https://nf-co.re/rnafusion/4.0.0) (Objective 3)
 [nf-core/rnasplice 1.0.3](https://nf-co.re/rnasplice/1.0.3) (Objective 3), and
[bigbio/quantmsdiann 2.2.0](https://github.com/bigbio/quantmsdiann) (Objective 3)

These can be downloaded for [offline use](https://nf-co.re/docs/get_started/offline_use) or run directly from the nf-core repository.

Remember to set `NXF_APPTAINER_CACHEDIR` to a folder with plenty of space so that container images are downloaded only once.

To build the nf_protegerna dependency image, see [nf-protegerna pipeline](nf-protegerna-Pipeline).

## 6. Other tools (Objective 2)

- **OctopuSV 0.3.5** and **bcftools**: install with conda (`conda install -c bioconda bcftools`) and follow the OctopuSV
  install instructions.
- **AnnotSV 3.5.8**: install it with its GRCh38 annotation folder. The annotation scripts read the install location from
  the `ANNOTSV_BIN_DIR` and `ANNOTATIONS` environment variables (see [Objective 2](Objective-2-Structural-Variants)).

## 7. Credentials

| Credential | Used for | How to supply |
| --- | --- | --- |
| COSMIC account | Building nf-core/rnafusion references | Pass at run time from environment variables. Never write it in a script or params file. |
| `GITHUB_TOKEN` | Refreshing the GitHub cache in Objective 1 (optional) | Environment variable. The saved run used a frozen cache, so you don't need a token to reproduce it. |
| Answer ALS portal access | All participant data | Request through the [data portal](https://dataportal.answerals.org/) |

## Checking the installation

| Check | Command |
| --- | --- |
| Python | `python -c "import pandas, numpy, requests; print('ok')"` |
| Database workflow | `python -m pytest 03_proteogenomic_database/03_search_database/proteogenomic_db/tests` |
| Nextflow pipeline | `nextflow run . -profile test --proteogenomic_container /abs/path/protegerna.sif` (from `03b_protegerna_nextflow/nf_protegerna_workflow_dev/`). Expected result: **4** unique sequences. |
| R dashboard | `Rscript -e 'shiny::runApp("02_SV_analysis/06_dashboard/proteGErna-SV.R")'` should open the empty dashboard (Figure 4.5) |
