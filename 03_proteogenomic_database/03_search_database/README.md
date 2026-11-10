# 03 Proteogenomic search database (v5)

**Objective:** Objective Three: translate gene-fusion and alternative-splicing events detected in RNA-seq into a protein search database for DIA proteomics.  
**Dissertation:** Chapter 5, Sections 5.2.6–5.2.7 and 5.3.1–5.3.7; tables and figures: Table 5.1, Table 5.2, Table 5.3, Table 5.4, Figure 5.1, Figure 5.2, Figure 5.3, Table 5A.2, Table 5A.3, Table 5A.4, Table 5A.5  
**Back to:** [objective README](../README.md)

## What this step does

Builds the database that was searched in Chapters 5 and 6: validates the CDS-phase translation against GENCODE v46, reconstructs
fusion proteins from FusionInspector and splice isoforms from rMATS and SUPPA, applies the biological filters, merges with the
reference proteome and cRAP (exact-sequence deduplication with full provenance), runs FASTA QC and writes a release report. The
result is `proteogenomic_database.fasta` (80,657 entries, MD5 `3f8ed11769fcd5a62587b528cd2eb52a`). The workflow code is the
`proteogenomic_db/` package (see its README).

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01_build_gtf_database.py` | Build the gffutils database of the GENCODE v46 GTF that the reconstruction workflow reads | Section 5.2.6 |
| `02_build_search_database.sh` | Build the v5 search database: GENCODE validation, fusion/rMATS/SUPPA reconstruction, merge, QC, release report | Table 5.1, Table 5.2, Figure 5.1, Figure 5.2, Figure 5.3, Table 5A.2, Table 5A.3, Table 5A.4, Table 5A.5 |
| `03_summarise_fusion_concordance.py` | Compare reconstructed fusion proteins with FusionInspector predictions (Tables 5.3, 5.4) | Table 5.3, Table 5.4 |

## Order of running

1. `01_build_gtf_database.py` (once per GTF).
2. `02_build_search_database.sh` (all stages, or `--stage NAME`).
3. `03_summarise_fusion_concordance.py`.

## How to run each script

Commands are those used for the dissertation, with paths run from `03_proteogenomic_database/`. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01_build_gtf_database.py`

Build the gffutils database of the GENCODE v46 GTF that the reconstruction workflow reads.

- **Dissertation:** Section 5.2.6
- **Inputs:** Homo_sapiens_GRCh38_46.gtf
- **Outputs:** gencode_v46.gtf.db
- **Run for the dissertation:** 2026
- **Before running:** Pass the GENCODE v46 GTF (not in the repository) as the first argument or set `GENCODE_GTF`. Writes `data/gencode_v46.gtf.db`, the `gtf_db` named in the TOML.

```bash
python 03_search_database/01_build_gtf_database.py /path/to/Homo_sapiens_GRCh38_46.gtf
```

### `02_build_search_database.sh`

Build the v5 search database: GENCODE validation, fusion/rMATS/SUPPA reconstruction, merge, QC, release report.

- **Dissertation:** Sections 5.2.6–5.2.7; Table 5.1, Table 5.2, Figure 5.1, Figure 5.2, Figure 5.3, Table 5A.2, Table 5A.3, Table 5A.4, Table 5A.5
- **Inputs:** GRCh38 primary assembly (Ensembl 112); gencode_v46.gtf.db (01_build_gtf_database.py); GENCODE v46 translations; UniProt UP000005640 2026_01; cRAP; FusionInspector abridged TSVs; rMATS JC tables; SUPPA events.ioe
- **Outputs:** results_pgdb_publication_rerun_v5/ (proteogenomic_database.fasta 80,657 entries, MD5 3f8ed117…; metadata, mapping, summary, qc/, release_report)
- **Run record:** results_pgdb_publication_rerun_v5/.proteogenomic_state/*.json; workflow.publication.v5.toml
- **Run for the dissertation:** 2026-10-03
- **Previous name:** `05_ALS_integration/proteogenomic_db_compare_v5_v7/code_proteogenomic_database_v5 (proteogenomic_workflow.py)`
- **Before running:** `--project-dir` defaults to `03_proteogenomic_database/`, which all TOML paths are relative to. The event inputs are the saved results in `02_event_detection/`; put the reference files named in the TOML (`gencode_v46.gtf.db`, GRCh38 genome, UniProt, GENCODE translations, cRAP) in `03_proteogenomic_database/data/`. Outputs go to `03_search_database/results_pgdb_publication_rerun_v5/` (re-running overwrites the saved database). Use `--dry-run` or `--explain` first. Needs Python ≥ 3.11 and the `proteogenomic_db` package (`pip install -e 03_search_database/proteogenomic_db`).
- **Note:** Modules in 03_search_database/proteogenomic_db/: validate_gencode_translation.py, fusiontoprotein.py, rmatstoprotein.py, suppatoprotein.py, merge_proteogenomic_database.py, proteogenomic_fasta_qc.py, release_report.py. 02_results_proteogenomic_db/ holds a second copy of the summaries.

```bash
bash 03_search_database/02_build_search_database.sh --dry-run   # then without --dry-run; config/workflow.publication.v5.toml; --stage NAME runs one stage
```

### `03_summarise_fusion_concordance.py`

Compare reconstructed fusion proteins with FusionInspector predictions (Tables 5.3, 5.4).

- **Dissertation:** Sections 5.2.7, 5.3.4; Table 5.3, Table 5.4
- **Inputs:** fusion.biological.tsv
- **Outputs:** results_pgdb_publication_rerun_v5/qc/fusion_prediction_concordance.md
- **Run for the dissertation:** 2026-10
- **Previous name:** `code_proteogenomic_database_v7/summarize_fusion_concordance.py`

```bash
python 03_search_database/03_summarise_fusion_concordance.py 03_search_database/results_pgdb_publication_rerun_v5/fusion.biological.tsv --output 03_search_database/results_pgdb_publication_rerun_v5/qc/fusion_prediction_concordance.md
```

### Configuration

- `config/workflow.publication.v5.toml` – the frozen configuration used for the dissertation.
- `config/workflow.minimum.example.toml`, `config/workflow.full.example.toml` – templates.

Each stage writes its configuration hash, software version (0.1.0) and input SHA-256 checksums to
`results_pgdb_publication_rerun_v5/.proteogenomic_state/`. `02_results_proteogenomic_db/` holds a second copy of the summary tables.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
