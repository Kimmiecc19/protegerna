# protegerna wiki

**Advancing Gene Function and Disease Mechanism Insight through a Containerised Multi-Omics Integration Tool**

Code documentation for the PhD dissertation of Kimberly Christine Coetzer, Division of Molecular Biology and Human Genetics,
Stellenbosch University.

---

## What this project does

protegerna is a reproducible multi-omics framework. It connects candidate genetic events across matched genomic,
transcriptomic and proteomic data from the same participants. This lets you trace, grade and inspect the molecular
consequences of putative causative or contributing variants in heritable disorders. Amyotrophic lateral sclerosis (ALS) is the
demonstration setting, using matched data from [Answer ALS](https://www.answerals.org/).

```text
                 Cohort preparation: 347 matched participants
                                     |
Objective 1   Tool landscape (bio.tools) ---- provenance for the tools used below
                                     |
Objective 2   WGS: SV calling -> consolidation -> AnnotSV -> prioritisation -> raw-call audit -> dashboard
                                     |                                                    |
Objective 3   RNA-seq: fusions + splicing -> proteogenomic search database -> DIA searches
                                     |                                                    |
Objective 4   Integration: single layers -> within-participant linking -> cross-layer evaluation
```

## The four objectives

| # | Objective | Wiki page | Repository folder | Dissertation |
| --- | --- | --- | --- | --- |
| 1 | Investigate the omics tool landscape in bio.tools (availability, adoption, metadata gaps) | [Objective 1: bio.tools landscape](Objective-1-Biotools-Landscape) | `01_biotools_landscape/` | Chapter 3; Appendix 3A |
| 2 | Reproducible SV detection, consolidation, annotation, ALS-informed nomination and interactive exploration | [Objective 2: Structural variants](Objective-2-Structural-Variants) and its [design logic](SV-Workflow-Design-Logic) | `02_SV_analysis/` | Chapter 4; Appendix 4A |
| 3 | Translate fusion and splicing events into a protein search database for DIA proteomics | [Objective 3: Proteogenomic database](Objective-3-Proteogenomic-Database), its [design logic](Proteogenomic-Database-Design-Logic) and the [nf-core/protegerna pipeline](nf-core-protegerna-Pipeline) | `03_proteogenomic_database/`, `03b_protegerna_nextflow/` | Chapter 5; Appendix 5A |
| 4 | Integrate SVs, transcriptomic alterations and proteomic evidence within participants and grade the evidence | [Objective 4: Multi-omics integration](Objective-4-Multi-Omics-Integration) and its [design logic](Integration-Design-Logic) | `04_integration/` | Chapter 6; Appendix 6A |
| – | Shared cohort preparation (347 matched participants) and schematic figures | [Cohort preparation](Cohort-Preparation) | `00_general/` | Sections 4.2.1, 5.2.2–5.2.4, 6.2.2–6.2.4 |

> Chapters 1, 2 and 7 (introduction, literature review and discussion) have no code.

## Where to start

1. **[Installation](Installation)**: software, environments and containers for every objective.
2. **[Data access and reference files](Data-Access-and-Reference-Files)**: what to request from Answer ALS and which public
   references to download.
3. **[Cohort preparation](Cohort-Preparation)**: run this before Objectives 2–4.
4. The objective pages, in order. Each one has the same sections:
   **Overview → Installation → Inputs required → Running → Expected outputs → Before you run / known issues → Dissertation map**.
5. **[Literature and method justification](Literature-and-Method-Justification)**, **[Software and versions](Software-and-Versions)**, **[Reproducibility](Reproducibility)** and **[Troubleshooting & FAQ](Troubleshooting-and-FAQ)**.

## Dependencies between objectives

| Objective | Needs results from |
| --- | --- |
| 1 | Nothing (public bio.tools API) |
| 2 | Cohort preparation |
| 3 | Cohort preparation (batches); Objective 1 for tool provenance (Table 5A.1) |
| 4 | Objective 2 (SV event tables, audited candidates) **and** Objective 3 (v5 database, six DIA searches, rnafusion outputs) |

You can look at saved results without re-running anything. Results sit next to the scripts that wrote them, in folders named
`NN_results_<script>`.

## Data access

This work uses controlled-access WGS, RNA-seq and DIA proteomics data from Answer ALS. These data are **not** redistributed in
this repository. Request them through the [Answer ALS data portal](https://dataportal.answerals.org/). Never commit
participant-level data, credentials or tokens.

## Contributors

- **Kimberly Christine Coetzer**<sup>1</sup>, PhD candidate
- **Professor Gian van der Spuy**<sup>1,2,3</sup>, supervisor
- **Professor Gerard Tromp**<sup>1</sup>, co-supervisor

<sup>1</sup> Division of Molecular Biology and Human Genetics, Department of Biomedical Sciences, Faculty of Medicine and Health
Sciences, Stellenbosch University ·
<sup>2</sup> SAMRC Centre for Tuberculosis Research ·
<sup>3</sup> Centre for Bioinformatics and Computational Biology, Faculty of Science, Stellenbosch University
