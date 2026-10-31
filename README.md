<h1 align="center">protegerna</h1>

<p align="center">
  <b>Advancing Gene Function and Disease Mechanism Insight through a Containerized Multi-Omics Integration Tool</b>
  <br>
  <i>PhD research repository</i>
</p>

---

<h2 align="center">Abstract</h2>

<!-- Abstract to be added. -->

## Overview

Sequencing now finds candidate disease variants faster than they can be
interpreted. Once a putative causative or contributing variant has been
identified in a heritable disorder, the harder question is *what it does*: which
transcripts and proteins it changes, and through what molecular mechanism.

This repository contains the code, workflows and configuration for a
reproducible framework that links genomic, transcriptomic and proteomic evidence
in order to move from candidate variants to candidate disease mechanisms. ALS is
used as the model disease throughout, drawing on matched multi-omic data from
the Answer ALS programme.

## Aim

To develop a reproducible framework for multi-omics analysis that facilitates
the elucidation of molecular mechanisms and gene function in heritable disorders
after the identification of putative causative or contributing variants, using
ALS as a model system.

## Objectives

1. **Bioinformatics tool landscape.** Investigate the bioinformatics tool
   landscape represented in the [bio.tools](https://bio.tools) registry, and
   determine whether publicly available metadata can identify widely adopted,
   actively maintained and reproducible tools before installation and
   benchmarking.
2. **Structural-variant workflow.** Develop and demonstrate a reproducible
   workflow for structural-variant (SV) detection, consolidation, annotation and
   interactive exploration, using ALS as a model for disease-focused candidate
   nomination.
3. **Proteogenomic database.** Generate a high-confidence fusion and
   splice-aware proteogenomic database, suitable for data-independent
   acquisition (DIA) mass spectrometry, from splice and fusion events detected
   in RNA-seq data.
4. **Multi-omics integration.** Develop and demonstrate a reproducible framework
   that integrates structural variants, transcriptomic alterations and proteomic
   evidence to prioritise candidate disease mechanisms, using ALS as the disease
   model.

## Significance

- **Closing the variant-to-function gap.** Many variants found in heritable
  disease, structural variants especially, lack functional interpretation.
  Tracing a variant's effect through RNA and protein provides evidence that a
  single data type cannot.
- **Reproducibility by design.** Multi-omics studies often depend on tools and
  parameters that are hard to reconstruct. Every stage here is version-pinned,
  containerised or configuration-driven, and writes provenance records (input
  hashes, software versions and parameter manifests) so that analyses can be
  rerun and audited.
- **Evidence-led tool selection.** Objective 1 tests whether registry metadata
  can guide tool choice before costly installation and benchmarking. This
  addresses a practical bottleneck for researchers building new pipelines.
- **Detecting non-canonical proteins.** Standard reference proteomes omit
  proteins produced by alternative splicing and gene fusions. A sample-derived
  proteogenomic database makes these products searchable in DIA proteomics.
- **Transparent prioritisation.** Candidates are ranked by named, rule-based
  evidence tiers rather than an opaque composite score, so every prioritised
  gene can be traced back to its supporting records.
- **Transferable framework.** ALS is the demonstration case, but the framework
  is disease-agnostic and can be applied to other heritable disorders with
  matched multi-omic data.

## Framework and approach

<p align="center">
  <img src="00_general/figures/archive/protegerna_flowchart_october2025.png" alt="Protegerna multi-omics integration flowchart" width="800">
</p>

> **NOTE:** This figure is outdated.

```text
 Objective 1: Tool landscape (bio.tools metadata) informs tool selection
                                            │
      ┌─────────────────────────────────────┼───────────────────────────────────────────┐
      ▼                                     ▼                                           ▼
 Genomics (WGS)                         Transcriptomics (RNA-seq)           Proteomics (DIA-MS)
 Objective 2: SV calling,               differential splicing               quantification and
 consolidation, annotation,             and gene fusions                    differential abundance
 prioritisation, dashboard                  │                                           │
      │                                     ▼                                 ▲         │
      │                 Objective 3: Proteogenomic database ──────────────────┘         │
      │                 (splice + fusion protein sequences)                             │
      │                                     │                                           │
      ▼                                     ▼                                           ▼
 Objective 4: Integration of SV, transcriptomic and proteomic evidence
 and evidence-tiered gene prioritisation
```

### Objective 1: Tool landscape analysis

- Programmatic retrieval of genomics, transcriptomics, proteomics and
  multi-omics tool records from the bio.tools API, enriched with publication and
  citation metadata and GitHub repository activity.
- A staged curation and filtering workflow covering EDAM topic and operation
  mapping, exclusion terms, licence, documentation and URL accessibility checks,
  and citation thresholds, with the number of tools retained recorded at each
  step.
- Descriptive analysis of adoption, maintenance and reproducibility indicators
  across omics domains.

### Objective 2: Structural-variant detection and interpretation

- **Calling:** [nf-core/sarek](https://nf-co.re/sarek) on whole-genome
  sequencing data with Manta, TIDDIT and CNVkit, annotated with Ensembl VEP and
  snpEff.
- **Consolidation:** caller harmonisation and cohort-level merging with
  OctopuSV, producing union and intersection call sets.
- **Annotation and ranking:** AnnotSV, combined with ALS-specific gene resources
  such as ALSoD.
- **Prioritisation and QC:** Python modules for call-set QC, participant-level
  carrier tables, review-evidence extraction and an independently verified,
  audited candidate release.
- **Exploration:** *proteGErna-SV*, an R Shiny dashboard for interactive
  browsing and filtering of annotated SVs.

### Objective 3: Proteogenomic database (`nf-core/protegerna`)

- An nf-core–style Nextflow DSL2 pipeline, containerised with Apptainer, that
  takes results from [nf-core/rnasplice](https://nf-co.re/rnasplice) (rMATS,
  SUPPA) and [nf-core/rnafusion](https://nf-co.re/rnafusion) (FusionInspector).
- Stages: input and reference validation (including a GENCODE concordance gate)
  → fusion and splice-event translation to protein → exact amino-acid sequence
  deduplication and merging with the reference proteome and contaminants →
  strict FASTA QC.
- All filtering policy is explicit in configuration (TOML/JSON) and mapped to
  Nextflow parameters, and runs are resumable.
- The resulting database is designed for DIA searches, for example with DIA-NN
  through [nf-core/quantms](https://nf-co.re/quantms).

### Objective 4: Multi-omics integration (ALS case study)

- **Cohort definition:** participant filtering, case–control matching and
  stratified batching so that samples are matched across omics layers.
- **Genomics:** SV-to-gene harmonisation against a versioned GENCODE annotation.
- **Transcriptomics:** differential expression (DESeq2) and a consensus-splicing
  pipeline that matches rMATS and SUPPA events by exact event geometry and
  assigns deterministic confidence tiers. Fusion events are also annotated.
- **Proteomics:** DIA quantification (quantms/DIA-NN) and differential abundance
  testing (MSstats).
- **Integration:** a configuration-driven Python module that combines qualifying
  evidence into a one-row-per-gene table. Genes are assigned to ordinal evidence
  tiers based on the number of supporting omics layers, replication across
  cohorts and samples, and concordance of molecular direction. Full audit
  tables, a gene-ID mapping audit and a provenance manifest are written
  alongside the results.

## Repository structure

| Directory | Contents |
| --- | --- |
| `00_general/` | Participant filtering, cross-omic sample matching, stratified batching and shared plotting helpers |
| `01_omics_tool_landscape/` | Objective 1: bio.tools retrieval, filtering, EDAM mapping and landscape analysis |
| `02_SV_analysis/` | Objective 2: Sarek configuration, OctopuSV merging, AnnotSV annotation, SV prioritisation and the Shiny dashboard |
| `03_proteomics/` | Objective 3: DIA quantification and differential abundance testing |
| `04_proteogenomic_nextflow/` | Objective 3: the `nf-core/protegerna` Nextflow pipeline |
| `05_ALS_case_study/` | Objective 4: genomics, transcriptomics, proteomics and integration code for the ALS case study |

## Reproducibility principles

- Workflow managers (Nextflow / nf-core) with container images
  (Apptainer/Singularity) for heavy computation.
- Parameters are kept in version-controlled configuration files rather than
  hard-coded.
- Run manifests record software versions, input checksums (SHA-256) and the
  parameters applied.
- Outputs are deterministic and never edited by hand: to change a result,
  correct the input or configuration and rerun.
- Synthetic test fixtures are included where possible. No participant-level data
  are stored in this repository.

## Data

This work uses controlled-access data from [Answer
ALS](https://www.answerals.org/), comprising whole-genome sequencing, RNA-seq
and DIA proteomics. These data are **not** redistributed here and must be
requested from the data provider under its access terms.

---

<h2 align="center">Contributors</h2>

- **Kimberly Christine Coetzer**<sup>1</sup>, PhD candidate
- **Professor Gian van der Spuy**<sup>1,2,3</sup>, supervisor
- **Professor Gerard Tromp**<sup>1,2,3</sup>, co-supervisor

<sup>1</sup> Division of Molecular Biology and Human Genetics, Department of Biomedical Sciences, Faculty of Medicine and Health Sciences, Stellenbosch University  
<sup>2</sup> SAMRC Centre for Tuberculosis Research  
<sup>3</sup> Centre for Bioinformatics and Computational Biology, Faculty of Science, Stellenbosch University

## Citation

If you use code from this repository, please cite the dissertation (citation to
follow on submission) and the underlying tools listed in each component's
`CITATIONS.md` or README.
