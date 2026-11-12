<h1 align="center">protegerna</h1>

<p align="center">
  <b>Advancing Gene Function and Disease Mechanism Insight through a Containerised Multi-Omics Integration Tool</b><br>
  <i>Code for the PhD dissertation of Kimberly Christine Coetzer, Stellenbosch University</i>
</p>

---

## Aim

To develop a reproducible multi-omics framework that connects candidate genetic events across participant-matched genomic,
transcriptomic and proteomic evidence, so that the molecular consequences of putative causative or contributing variants in
heritable disorders can be traced, graded and inspected. Amyotrophic lateral sclerosis (ALS), using matched data from Answer ALS,
is the demonstration setting.

## Objectives and where to find them

| Objective | Folder | Dissertation |
| --- | --- | --- |
| 1. Investigate the omics tool landscape in bio.tools (availability, adoption, metadata gaps) | [`01_biotools_landscape`](01_biotools_landscape/README.md) | Chapter 3; Appendix 3A |
| 2. Reproducible SV detection, consolidation, annotation, ALS-informed nomination and interactive exploration | [`02_SV_analysis`](02_SV_analysis/README.md) | Chapter 4; Appendix 4A |
| 3. Translate fusion and splicing events into a protein search database for DIA proteomics | [`03_proteogenomic_database`](03_proteogenomic_database/README.md), [`03b_protegerna_nextflow`](03b_protegerna_nextflow/README.md) | Chapter 5; Appendix 5A |
| 4. Integrate SVs, transcriptomic alterations and proteomic evidence within participants and grade the evidence | [`04_integration`](04_integration/README.md) | Chapter 6; Appendix 6A |
| Shared cohort preparation (347 matched participants) and schematic figures | [`00_general`](00_general/README.md) | Sections 4.2.1, 5.2.2–5.2.4, 6.2.2–6.2.4 |

Chapters 1, 2 and 7 (introduction, literature review, discussion) have no code.

```text
00_general: 347 matched participants
        |
01 Tool landscape (bio.tools) ---- provenance for the tools used below
        |
02 WGS: SV calling -> consolidation -> AnnotSV -> prioritisation -> raw-call audit -> dashboard
        |                                                   |
03 RNA-seq: fusions + splicing -> search database -> DIA searches
        |                                                   |
04 Integration: single layers -> within-participant linking -> cross-layer evaluation
```

## Finding the code for a table or figure

- Each objective README has a **script-to-dissertation map** listing every table and figure of its chapter with the script that
  produced it.
- Each step folder has a README with the **command used** for every script, its inputs and outputs, the run record it wrote and
  what to edit before running.

## Repository layout

| Folder | Contents |
| --- | --- |
| `00_general/` | Cohort filtering and matching, cohort description, Nextflow resource review, schematic figures |
| `01_biotools_landscape/` | bio.tools retrieval, filtering, EDAM mapping and landscape analysis |
| `02_SV_analysis/` | `01_sv_calling` → `06_dashboard` |
| `03_proteogenomic_database/` | `01_sample_batches` → `06_search_assessment`; the database workflow package is in `03_search_database/proteogenomic_db/` |
| `03b_protegerna_nextflow/` | nf-core/protegerna Nextflow pipeline |
| `04_integration/` | `01_single_layer` → `04_figures`; shared `lib/` and `data/` |

Within each step, scripts are numbered in the order they were run (`01a`, `01b`, `02`, ...). Results sit next to the scripts in
folders named `NN_results_<script>` so that each output can be traced to the script that wrote it.

## Reproducibility

- Heavy computation used nf-core pipelines in Apptainer containers (Sarek 3.5.1, rnafusion 4.0.0, rnasplice 1.0.3,
  quantmsdiann 2.2.0); their parameter files are kept with the launch scripts.
- Settings live in configuration files (YAML, TOML, JSON) or at the top of each script, and most steps write a run record
  (manifest, `summary.json`, log or `sessionInfo.txt`) with inputs, checksums and settings.
- Scripts find repository files from their own location, so they run from a fresh clone. Data, references and tools that
  are not in the repository are set in a **Settings** block (or environment variable) at the top of each launcher and
  appear as `/path/to/...` placeholders until you set them. Credentials are only ever read from environment variables.
- Results are never edited by hand: to change a result, change the input or setting and re-run.

## Data

This work uses controlled-access whole-genome sequencing, RNA-seq and DIA proteomics data from
[Answer ALS](https://www.answerals.org/). These data are **not** redistributed here and must be requested through the
[Answer ALS data portal](https://dataportal.answerals.org/). Do not commit participant-level data, credentials or tokens.

## Contributors

- **Kimberly Christine Coetzer**<sup>1</sup>, PhD candidate
- **Professor Gian van der Spuy**<sup>1,2,3</sup>, supervisor
- **Professor Gerard Tromp**<sup>1,2,3</sup>, co-supervisor

<sup>1</sup> Division of Molecular Biology and Human Genetics, Department of Biomedical Sciences, Faculty of Medicine and Health Sciences, Stellenbosch University
<sup>2</sup> SAMRC Centre for Tuberculosis Research
<sup>3</sup> Centre for Bioinformatics and Computational Biology, Faculty of Science, Stellenbosch University

## Citation

If you use code from this repository, please cite the dissertation (citation to follow on submission) and the tools and resources
named in each objective README.
