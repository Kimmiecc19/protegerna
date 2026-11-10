# Reproducibility

## Principles used throughout the repository

- **Containers for heavy computation.** nf-core pipelines ran in Apptainer containers at pinned releases:
  Sarek 3.5.1, rnafusion 4.0.0, rnasplice 1.0.3, quantmsdiann 2.2.0. Their parameter files sit next to the launch scripts.
- **Settings in files.** Settings live in configuration files (YAML, TOML, JSON) or at the top of each script.
- **Run records.** Most steps write a record (manifest, `summary.json`, log or `sessionInfo.txt`) with inputs, checksums and
  settings.
- **Traceable outputs.** Scripts are numbered in the order they were run (`01a`, `01b`, `02`, ...). Results sit beside them in
  `NN_results_<script>` folders.
- **No hand edits.** Results are never edited by hand. To change a result, change the input or setting and re-run.

## Paths

Every script resolves repository files from its own location, so the code runs from a fresh clone without editing. Data,
references and tools outside the repository are set in each launcher's **Settings** block or through environment
variables (see [Troubleshooting & FAQ](Troubleshooting-and-FAQ#external-settings-at-a-glance)). The configurations exactly
as run on the analysis server are kept with their results (e.g. `results_pgdb_publication_rerun_v5/workflow.publication.v5.toml`).

## Run records by objective

| Objective | Run records |
| --- | --- |
| 1 | `*.manifest.json` (fetch: queries, counts, MD5s); `{domain}_reproducibility_manifest.json`; `reproducibility_manifest_20261005.json`; `reproducibility_manifest_full_population_20261008.json` |
| 2 | AnnotSV logs; `*.manifest.json` (callset QC); `*_prioritisation_summary.json` (inputs with SHA-256); `run_log.json`, `evidence_thresholds.json`; `input_checksums.json`, `release_parameters.json`, `verification.json` |
| 3 | Configuration hash and input checksums for every database stage; frozen TOMLs (`workflow.publication.v5.toml`, `workflow.publication.frozen.toml`); Nextflow `pipeline_info/` |
| 4 | `sessionInfo.txt` (R); `run_manifest.json` (linking pipeline); `summary.json` (most Python scripts) |

## Frozen inputs and checksums

| Item | Value |
| --- | --- |
| bio.tools analysis date | 2026-09-30 (fetch on 2026-09-29) |
| GitHub metadata | Frozen cache `github_commit_cache_final.csv` |
| EDAM snapshot | `EDAM.owl`, MD5 52e00fc4… |
| ALSoD gene list | Accessed 24 Feb 2026 (154 genes) |
| v5 search database | `proteogenomic_database.fasta`, 80,657 entries, MD5 `3f8ed11769fcd5a62587b528cd2eb52a` |
| v7 revised database | 30,031 sequences, MD5 `e6b4632b…` |
| Answer ALS metadata | Feb 2024 portal snapshot |

Check a database checksum with:

```bash
md5sum results_pgdb_publication_rerun_v5/proteogenomic_database.fasta
```

## Random seeds (Objective 4)

| Analysis | Seed |
| --- | --- |
| Pathway label permutation | 20261014 |
| SV-scan null; evaluation table | 1 |
| Stage 3 carrier permutation | `numpy.random.default_rng(1)` |
| `01e` row order among tied p-values | set `PYTHONHASHSEED=0` |
| Fusion label permutation | not saved |
