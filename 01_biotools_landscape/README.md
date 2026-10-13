# Omics bioinformatics tool landscape

This directory contains the data collection and analysis workflow for the dissertation’s comparative landscape of bioinformatics tools supporting **genomics, transcriptomics, proteomics, and multiomics**. It uses the [bio.tools](https://bio.tools/) registry to assemble tool records, applies documented scope and eligibility rules, maps annotated functions to the EDAM ontology, and analyses tool characteristics, citations, adoption, and maintenance.

The goal is to describe how these tool ecosystems differ and where their coverage, annotation, and evidence have limitations. Registry metadata and citation or GitHub indicators are proxies for discoverability, uptake, and activity; they do not establish software quality or scientific impact.

## Workflow

<p align="center">
  <img src="../00_general/figures/objective1_methods_flowchart.png" alt="Objective One Flowchart" width="800">
</p>


The numbered folders reflect the intended order:

1. **Fetch registry records** — `01_fetch_biotools/` queries bio.tools for four omics domains and exports tool tables, function and publication audit tables, and retrieval manifests.
2. **Curate scope and eligibility** — `02_filter_biotools/` applies domain-specific topic inclusion lists and shared exclusion terms. It produces reviewable scope classifications, quality flags, candidate populations, and summaries.
3. **Map function annotations** — `03_edam_annotation/` maps bio.tools `function.operation` annotations to the local EDAM ontology snapshot and writes a crosswalk and mapping manifest. The mapping uses ontology terms and hierarchy; it does not infer functions from free-text descriptions.
4. **Analyse and visualise** — `04_visualize_biotools/` produces figures, statistical summaries, audit tables, and reproducibility manifests. The main analysis focuses on the candidate population; a separate script analyses the full retrieved population for age and registration questions.

## Repository contents

| Path | Purpose |
| --- | --- |
| `01_fetch_biotools/` | Python registry retrieval and enrichment scripts; retrieved TSVs and audit sidecars are in `results_fetch_biotools/`. |
| `02_filter_biotools/` | R scope and candidate selection, domain topic lists, exclusion terms, and filtering outputs. |
| `03_edam_annotation/` | EDAM mapper, ontology snapshot, validation sample, mapped operations, and crosswalk. |
| `04_visualize_biotools/` | R analyses, shared helpers, `visualize_config.yaml`, cached GitHub metadata, figures, tables, and manifests. |

## Reproducing the workflow

Run commands from this directory. The scripts resolve most inputs and outputs relative to their own locations. Use a recent Python 3 installation and R with the packages listed by the scripts. The fetcher requires Python’s `requests` package; the R filtering and plotting scripts check for their required packages at startup.

NOTE: Large output files have not been included in this repository.

### 1. Fetch records

The checked-in fetch results are a dated snapshot. To query bio.tools again, run:

```bash
python 01_fetch_biotools/run_fetch_biotools.py --output-tag YYYYMMDD
```

The launcher fetches all four domains by default. To fetch selected domains, add for example `--omics genomics proteomics`. Use `--help` on the launcher and `fetch_biotools.py` for available retrieval and publication-enrichment options. Network responses and registry metadata can change between runs.

### 2. Filter and curate

Run the R script with the tag used for the fetched files:

```bash
Rscript 02_filter_biotools/filter_biotools.R --omic=all --analysis-date=2026-09-30 --input-tag=YYYYMMDD
```

The default topic lists and exclusions are in `02_filter_biotools/data_filter_biotools/`. Filtering outputs include full retrieved populations and candidate sets, with TSV/RDS tables and audit summaries. Optional URL checks are network-dependent and can be enabled with `--check-urls`.

### 3. Map EDAM operations

The repository includes an EDAM OWL snapshot. From `03_edam_annotation/`, map the function-operation tables produced by filtering:

```bash
python map_edam_operations.py \
  --input "../02_filter_biotools/results_filter_biotools/*_all_function_operations.tsv" \
  --output results_edam_annotation/all_edam_operations_mapped.tsv \
  --crosswalk-output results_edam_annotation/edam_operation_crosswalk.tsv \
  --edam-owl edam/EDAM.owl \
  --aggregation-depth 1
```

The mapper supports glob input. See `python map_edam_operations.py --help` for options, including retaining a newer ontology snapshot.

### 4. Generate analyses and figures

From this directory, run:

```bash
Rscript 04_visualize_biotools/visualize_biotools.R
Rscript 04_visualize_biotools/visualize_age_registration_full_population.R
```

Both scripts use `04_visualize_biotools/visualize_config.yaml` by default. Pass `--config=path/to/config.yaml` to use another configuration. Outputs are written beneath `04_visualize_biotools/results_tool_analysis/`.

The checked-in configuration uses an analysis date of **2026-09-30**, a frozen GitHub cache, and **Dimensions** as the citation source. Reproducing the saved analyses means using the included input snapshots and cache. Refreshing registry, citation, URL, or GitHub data can produce different results. GitHub authentication, when needed, is read from the `GITHUB_TOKEN` environment variable; do not commit tokens.

## Interpreting the data

- The fetched tables preserve provenance and audit detail in sidecar files, including publication and function records and JSON manifests.
- Scope decisions and candidate eligibility are separate steps. Consult the scope review, quality flag, and candidate output tables before interpreting a filtered set.
- Citation values are source- and coverage-dependent. Unknown or incomplete citation data should not be interpreted as zero. The analysis code documents the rules for complete, conflict-free comparisons.
- GitHub stars, forks, watchers, and commit recency are descriptive engagement or activity signals, not direct measures of quality, use, or maintenance capacity.
- bio.tools annotations are registry metadata and may be missing, outdated, or inconsistent. EDAM mapping only applies to supplied operation annotations.
- The repository includes dated generated outputs to support inspection. These snapshots should be interpreted with their accompanying manifests and retrieval or analysis dates.

## Data and attribution

Tool metadata is retrieved from [bio.tools](https://bio.tools/); functional categories are mapped against [EDAM](https://edamontology.org/). Citation and repository metadata retain source and retrieval details in the generated audit files. Please consult the source registries and linked tool records when reusing individual records. Cite the dissertation and this repository according to the project’s publication details once available.

## License

---

