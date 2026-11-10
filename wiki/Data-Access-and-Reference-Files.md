# Data access and reference files

## Controlled-access participant data (Answer ALS)

All participant data come from [Answer ALS](https://www.answerals.org/). They are **controlled access** and are **not** in this
repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) and use them under its data-use
terms.

| Data | Used by | Notes |
| --- | --- | --- |
| Portal metadata tables: `aals_dataportal_datatable.csv`, `aals_released_files.csv`, `Proteomics_Batch_Effect_Samples_52.csv`, `Sample Mapping File Feb 2024.csv` | Cohort preparation | Feb 2024 snapshot. How they were downloaded is recorded in `00_general/01_filtering_matching_patients/data/aals_metadata_neuromine/downloading_aals_data.md` |
| WGS CRAM + CRAI (347 participants) | Obj. 2, Obj. 4 (duplication check) | Aligned and duplicate-marked by Answer ALS against `GRCh38_full_analysis_set_plus_decoy_hla.fa` |
| RNA-seq FASTQ (346 participants + 66 recurring controls = 412 samples) | Obj. 3 | |
| DIA proteomics mzML (SCIEX TripleTOF 6600; 346 participants + 71 recurring controls) and per-batch SDRF | Obj. 3 | |
| RNA counts release 7 (`AnswerALS-1276-T-v1-release7_raw-counts.csv`) and sample metadata | Obj. 4 | Place in `04_integration/data/` |
| Consortium protein matrix (`AnswerALS-447-P_proteomics-protein-matrix_prebatchcorrected.txt`) | Obj. 4 | Place in `04_integration/data/` |

## Public reference files

| Reference | Version | Used by |
| --- | --- | --- |
| `GRCh38_full_analysis_set_plus_decoy_hla.fa` (+ `.fai`) | 1000 Genomes | Obj. 2 (calling, raw-call audit), Obj. 4 (duplication check) |
| dbSNP, known indels | dbSNP 138 | Obj. 2 (Sarek) |
| snpEff cache | GRCh38.105 | Obj. 2 (Sarek) |
| VEP cache | 112 | Obj. 2 (Sarek) |
| ALSoD gene table | accessed 24 Feb 2026 (154 genes) | Obj. 2, 4. Keep the saved `alsod_gene_list.csv`; re-downloading may give a different list |
| Ensembl REST | release 112 | Obj. 2 (gene → Ensembl mapping) |
| AnnotSV annotation folder (GRCh38) | 3.5.8 | Obj. 2 |
| STRchive disease loci (hg38 BED) | – | Obj. 2 raw-call audit (`04_sv_prioritization/data/`) |
| GRCh38 primary assembly | Ensembl 112 | Obj. 3 |
| GENCODE GTF and protein translations | v46 | Obj. 3, 4 |
| UniProt human proteome UP000005640 (canonical + isoforms) | 2026_01 | Obj. 3, 4 |
| cRAP contaminants | 116 entries | Obj. 3 |
| MSigDB gene sets | v2026.1 | Obj. 4 (`04_integration/data/gene_sets/`) |
| EDAM ontology snapshot | `EDAM.owl` (MD5 52e00fc4…) | Obj. 1 (saved in `01_biotools_landscape/results/02bc_results_edam_annotation/edam/`) |
| nf-core/rnafusion and rnasplice references | built locally | Obj. 3 (`02_event_detection/01_build_rnafusion_references.sh`) |

## Public data sources for Objective 1

Objective 1 uses no participant data. It queries the [bio.tools](https://bio.tools/) API, Dimensions citation data and GitHub
repository metadata. The saved run used a frozen GitHub cache (`01_biotools_landscape/data/03a_data_tool_analysis/github_commit_cache_final.csv`).
If you re-fetch these sources, you will get different numbers.

## Where the scripts expect files

| Files | Location |
| --- | --- |
| Answer ALS portal tables (cohort preparation) | `00_general/01_filtering_matching_patients/data/aals_metadata_neuromine/` |
| RNA counts, protein matrix, cohort manifests (Objective 4) | `04_integration/data/` |
| Reference files for the database build (GTF database, genome, UniProt, GENCODE translations, cRAP) | `03_proteogenomic_database/data/` |
| Everything else (CRAMs, FASTQ, mzML/SDRF, genome references, AnnotSV, container caches) | Anywhere; set its environment variable or Settings-block value |

## Notes

> Keep the controlled-access raw data outside the repository to prevent accidental commits

