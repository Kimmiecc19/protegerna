# 02 Participant-level linking (Stages 1–3)

**Objective:** Objective Four: link SVs, transcriptomic alterations and proteomic evidence within participants and grade the evidence for candidate mechanisms.  
**Dissertation:** Chapter 6, Sections 6.2.13 and 6.3.8; tables and figures: Table 6.15  
**Back to:** [objective README](../README.md)

## What this step does

Links evidence within participants. Stage 1 links variant-only peptides to annotated isoform and fusion events; Stage 1b
extracts PASS SV carriers; Stage 2 links SVs to nearby isoform events (5 kb) and fusion breakpoints (100 kb) and builds
variant–event–peptide chains; Stage 3 tests rare SVs (≤ 17 carriers) against gene RNA and protein levels, with a carrier-label
permutation null (600 permutations, seed 1). All input paths are in `../lib/paths.py`.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `00_run_linking_pipeline.py` | Runs scripts 01–05 in order and writes run_manifest.json | Table 6.15 |
| `01_link_peptides_to_events.py` | Stage 1: link variant-only peptides to annotated isoform/fusion events in the same participant | Section 6.2.13 |
| `02_extract_sv_carriers.py` | Stage 1b: PASS SV carriers among pooled-batch participants with cohort carrier counts | Section 6.2.13 |
| `03_link_svs_to_events.py` | Stage 2: SVs within 5 kb of isoform events or spanning fusion breakpoints (100 kb) | Sections 6.2.13 (Event-linking windows) |
| `04_test_rare_sv_rna_protein.py` | Stage 3: rare SVs (≤ 17 carriers) vs gene RNA and protein | Table 6.15 |
| `05_permutation_null.py` | Carrier-label permutation null for Stage 3 (600 permutations) | Table 6.15 |

## Order of running

Run `00_run_linking_pipeline.py`; it runs 01–05 in order, checks inputs (`--check`), resumes (`--from-stage`) and writes
`run_manifest.json` with script checksums.

## How to run each script

Commands are those used for the dissertation, with paths run from `04_integration/`. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `00_run_linking_pipeline.py`

Runs scripts 01–05 in order and writes run_manifest.json.

- **Dissertation:** Sections 6.2.13 (Participant-level event linking), 6.3.8; Table 6.15
- **Inputs:** paths in lib/paths.py (SV VCF, PGDB v5, rnafusion, counts, GTF, UniProt, DIA-NN matrices, excluded runs)
- **Outputs:** 02_results_participant_linking/ (run.log, run_manifest.json)
- **Run record:** 02_results_participant_linking/run_manifest.json
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `13_run_objective4.py`
- **Before running:** `lib/paths.py` resolves every input from this repository except the GENCODE v46 GTF: set `OBJ4_GTF=/path/to/Homo_sapiens_GRCh38_46.gtf` (or edit that line). Any other path can be overridden with `OBJ4_<NAME>`. Run `--check` first. Results go to `02_participant_linking/02_results_participant_linking/b1to6_<date>/` unless you pass `--out`.
- **Note:** The run used the server copies (13a–13e, obj4_paths.py); names fixed in the repo copy on 8 Nov 2026.

```bash
OBJ4_GTF=/path/to/Homo_sapiens_GRCh38_46.gtf python 02_participant_linking/00_run_linking_pipeline.py --check
OBJ4_GTF=/path/to/Homo_sapiens_GRCh38_46.gtf python 02_participant_linking/00_run_linking_pipeline.py --nperm 600
```

### `01_link_peptides_to_events.py`

Stage 1: link variant-only peptides to annotated isoform/fusion events in the same participant.

- **Dissertation:** Section 6.2.13
- **Inputs:** v5 pr_matrix; PGDB metadata/mapping; fusion tables; UniProt; RNA counts; SV VCF
- **Outputs:** 02_results_participant_linking/links_peptide_event.tsv, novel_peptides_detected.tsv, summary_stage1_feasibility.json
- **Run record:** run_manifest.json
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `13a_link_feasibility.py`
- **Before running:** Run through `00_run_linking_pipeline.py`.

```bash
(via 00) python 01_link_peptides_to_events.py <out>
```

### `02_extract_sv_carriers.py`

Stage 1b: PASS SV carriers among pooled-batch participants with cohort carrier counts.

- **Dissertation:** Section 6.2.13
- **Inputs:** manta_tiddit.intersect.cohort.vcf; rnafusion sample list
- **Outputs:** 02_results_participant_linking/sv_carriers.tsv
- **Run record:** run_manifest.json
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `13b_cache_sv_batch5.py`
- **Before running:** Run through `00_run_linking_pipeline.py`.
- **Note:** Re-run on 8 Nov with the local intersection VCF: identical to the saved sv_carriers.tsv.

```bash
(via 00) python 02_extract_sv_carriers.py <out>
```

### `03_link_svs_to_events.py`

Stage 2: SVs within 5 kb of isoform events or spanning fusion breakpoints (100 kb); chains.

- **Dissertation:** Sections 6.2.13 (Event-linking windows)
- **Inputs:** sv_carriers.tsv; links_peptide_event.tsv; PGDB mapping; fusion.metadata.tsv; RNA counts
- **Outputs:** 02_results_participant_linking/links_variant_event.tsv, chains_variant_event_peptide.tsv, summary.json
- **Run record:** run_manifest.json
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `13c_link_variant_event.py`
- **Before running:** Run through `00_run_linking_pipeline.py`.

```bash
(via 00) python 03_link_svs_to_events.py <out>
```

### `04_test_rare_sv_rna_protein.py`

Stage 3: rare SVs (≤ 17 carriers) vs gene RNA and protein; tiers A/B/C.

- **Dissertation:** Sections 6.2.13, 6.3.8; Table 6.15
- **Inputs:** sv_carriers.tsv; GTF; v5 pg_matrix; RNA counts
- **Outputs:** 02_results_participant_linking/variant_gene_rna_protein.tsv, variant_gene_rna_protein_summary.json
- **Run record:** run_manifest.json
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `13d_protein_rna_link.py`
- **Before running:** Run through `00_run_linking_pipeline.py`.

```bash
(via 00) python 04_test_rare_sv_rna_protein.py <out>
```

### `05_permutation_null.py`

Carrier-label permutation null for Stage 3 (600 permutations).

- **Dissertation:** Sections 6.2.13, 6.3.8; Table 6.15
- **Inputs:** variant_gene_rna_protein.tsv; RNA; protein
- **Outputs:** 02_results_participant_linking/permutation_null_summary.json
- **Run record:** run_manifest.json
- **Run for the dissertation:** 2026-10-24
- **Previous name:** `13e_permutation_null.py`
- **Before running:** Run through `00_run_linking_pipeline.py`.
- **Note:** Seed is fixed in the script (default_rng(1)).

```bash
(via 00) python 05_permutation_null.py <out> 600
```

The dissertation run (24 Oct 2026) used the server copies of these scripts (`13a`–`13e`, `obj4_paths.py`); its `run_manifest.json` lists batches 4–6.

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
