# Structural variant analysis in AnswerALS

This directory contains the structural-variant (SV) analysis workflow for the
dissertation’s ALS cohort.

It processes whole-genome sequencing callsets, consolidates calls from Manta and
TIDDIT, annotates and prioritizes candidate events, evaluates call quality and
carrier evidence, and prepares tables and figures for review.

The workflow is designed for research nomination and cohort analysis. Its
outputs are not clinical diagnoses or clinical variant classifications.

## Workflow at a glance

<p align="center">
  <img src="..\00_general\figures\objective2_workflow.png" alt="Objective Two Flowchart" width="800">
</p>

---

## Directory guide

| Directory | Purpose |
| --- | --- |
| `01_sarek/` | Sarek samplesheet generation, run configuration, launch script, and resource analysis. |
| `02_octopusv/` | Manta/TIDDIT VCF correction and merging, cohort union/intersection callsets, and caller statistics/plots. |
| `03_annotsv/` | ALSoD gene/transcript mapping and filtered or unfiltered AnnotSV execution. |
| `04_sv_analysis/` | VCF QC and burden summaries, AnnotSV prioritization, participant-level tables, raw-record review, evidence summaries, and audited-release build/verification scripts. |
| `05_dashboard/` | Shiny application for exploring SV annotations and linking out to external genomic and literature resources. |
| `06_dissertation_figures/` | R scripts and style helpers for cohort statistics and dissertation workflow figures. |

# Objective Two: structural variant analysis (Chapter 4)

This folder contains the code for **Objective Two** of the dissertation, reported in
**Chapter 4: structural variant detection, consolidation, annotation and nomination in Answer ALS**.
It calls germline structural variants (SVs) from whole-genome sequencing (WGS) of 347 Answer ALS
participants, merges the Manta and TIDDIT calls, annotates them with AnnotSV, nominates
ALS-relevant events, audits each nomination against the raw caller records, and provides the
proteGErna-SV dashboard for exploring the annotated calls.

The audited release produced here (primary candidates and participant support) is the genomic input to
Objective Four (`../objective4_integration`, Chapter 6).

> Outputs are research nominations. They are not clinical variant classifications.

## Contents

- [Workflow at a glance](#workflow-at-a-glance)
- [Data required](#data-required)
- [Software](#software)
- [How to run each step](#how-to-run-each-step)
- [Script-to-dissertation map](#script-to-dissertation-map)
- [Previous file names](#previous-file-names)

## Workflow at a glance

```text
Answer ALS CRAM/CRAI (347 participants)
        │
01_sv_calling            nf-core/sarek 3.5.1: Manta + TIDDIT per participant
        │
02_sv_consolidation      OctopuSV: correct, caller intersection/union, cohort merge
        │
03_sv_annotation         ALSoD gene list; AnnotSV filtered + unfiltered
        │
04_sv_prioritisation     callset statistics; nomination and review tiers
        │
05_sv_audit              raw-call extraction, evidence scoring, audited release, verification
        │
06_dashboard + figures   proteGErna-SV; Chapter 4 figures
```

Numbers give the run order. Scripts that share a number with different letters (`01a`, `01b`)
don't depend on each other and can run in either order.

## Data required

| Data | Used in | Source / notes |
| --- | --- | --- |
| WGS CRAM + CRAI files, 347 participants | 01 | Answer ALS Neuromine data portal (controlled access; data access approved July 2024). Already aligned and duplicate-marked by Answer ALS. |
| `GRCh38_full_analysis_set_plus_decoy_hla.fa` (+ `.fai`) | 01, 04 | 1000 Genomes EBI FTP. Must be the reference the CRAMs were made with. |
| dbSNP 138 and known indels VCFs (+ `.tbi`) | 01 | GATK resource bundle; paths in `sarek_params.json`. |
| snpEff `GRCh38.105` cache; VEP cache v112 (+ dbNSFP, SpliceAI plugins) | 01 | Paths in `sarek_params.json`. |
| ALSoD gene table (accessed 24 February 2026) | 03 | Downloaded by `01_build_alsod_gene_list.py`. ALSoD changes over time, so keep the saved `alsod_gene_list.csv` used in the dissertation. |
| `ALS_candidate_gene_list.txt` (154 symbols, one per line) | 03, 04 | Made from `alsod_gene_list.csv`; AnnotSV candidate-gene filter. |
| AnnotSV 3.5.8 annotation directory | 03 | Installed with AnnotSV (GRCh38, Ensembl transcripts). |
| STRchive disease-associated repeat loci (hg38 BED) | 05 | STRchive general release; used with `--str-bed`. |
| Per-participant raw Manta and TIDDIT VCFs | 05 | Written by Sarek in step 01 (`variant_calling/`). |

Do not commit CRAM, VCF or participant-level tables to a public repository; they fall under the
Answer ALS data-use terms.

## Software

| Tool | Version | Steps |
| --- | --- | --- |
| Nextflow + nf-core/sarek (Apptainer profile) | Sarek 3.5.1; Manta 1.6.0; TIDDIT 3.6.1 | 01 |
| OctopuSV, bcftools | OctopuSV 0.3.5 | 02 |
| AnnotSV | 3.5.8 | 03 |
| Python 3 | pandas, numpy, requests, beautifulsoup4 (only steps 01 and 03); the remaining Python scripts use the standard library | 01, 03–05 |
| R 4.6.1 | shiny 1.14.0, shinydashboard 0.7.3, DT 0.34.0, vcfR 1.16.0, shinyjs 2.1.1, httr 1.4.8, jsonlite 2.0.0; ggplot2, dplyr, tidyr, stringr, stringi, purrr, readr, scales, patchwork, data.table for figures | 06, figures |

Every Python script prints its options with `--help`.

## How to run each step

The commands use these shell variables. Set them for your system:

```bash
CRAM_DIR=/path/to/answerals/cram
SAREK=/path/to/results/sarek
OCTO=/path/to/results/octopusv
ANNOTSV=/path/to/results/annotsv
PRIO=/path/to/results/prioritisation
REVIEW=/path/to/results/sv_review          # absolute path (needed in step 05)
RELEASE=/path/to/results/sv_audited_release # absolute path
```

### 01_sv_calling: SV calling with nf-core/sarek

**01_make_sarek_samplesheets.py** pairs each CRAM with its CRAI and writes Sarek samplesheets,
split into 14 batches (`NUM_SPLITS`).

```bash
python 01_sv_calling/01_make_sarek_samplesheets.py "$CRAM_DIR" sarek_samplesheet
```

- *Input:* folder of CRAM/CRAI files.
- *Output:* `sarek_samplesheet_<n>.csv`, one per batch.

**02_run_sarek.sh** runs Sarek 3.5.1 from `prepare_recalibration` with the tools
`manta,tiddit,cnvkit,merge`. Before running, edit the placeholder paths in the script,
`sarek_params.json` and `sarek.config` (process resources). Run it once per samplesheet:

```bash
bash 01_sv_calling/02_run_sarek.sh      # nextflow run ... -profile apptainer -c sarek.config -params-file sarek_params.json --input <samplesheet> --outdir "$SAREK/<batch>" -resume
```

- *Output:* per-participant Manta and TIDDIT VCFs under `$SAREK/<batch>/variant_calling/`.
- CNVkit also runs, but its output was not used (Section 4.2.4).

**03_summarise_sarek_resources.py** (optional) summarises CPU, memory and runtime from the
Nextflow trace files. **No result in the dissertation comes from it.**

```bash
python 01_sv_calling/03_summarise_sarek_resources.py -i "$SAREK" -p sarek_
```

### 02_sv_consolidation: OctopuSV merging

**01_run_octopusv_merge.sh** checks that the Manta and TIDDIT participant IDs match, then runs OctopuSV
`clean` and `correct` (PASS, 50–100,000 bp) on each caller VCF. It builds the per-participant caller
intersection and union, merges participants into cohort VCFs, and writes `octopusv stat` reports and plots.

```bash
bash 02_sv_consolidation/01_run_octopusv_merge.sh --input-dir "$SAREK" --out-dir "$OCTO"
# options: --min-svlen 50 --max-svlen 100000 --dry-run --force-merge --skip-merge
```

- *Output:* `$OCTO/merged/{manta.cohort, tiddit.cohort, manta_tiddit.intersect.cohort, manta_tiddit.union.cohort}.vcf`,
  `$OCTO/stats/`, `$OCTO/plots/`, `$OCTO/circos/`.

> `octopusv clean` sets every FILTER value to PASS, so caller filter status is not carried into the merged
> VCFs. It is re-applied only in the audit (step 05). See Section 4.2.4.

### 03_sv_annotation: ALSoD gene list and AnnotSV

**01_build_alsod_gene_list.py** downloads the ALSoD gene table and looks up Ensembl 112 (GENCODE v46)
gene and transcript IDs.

```bash
python 03_sv_annotation/01_build_alsod_gene_list.py --out-dir 03_sv_annotation/data
```

- *Output:* `alsod_gene_list.csv` (symbol, evidence category) and `alsod_gene_transcript_map_gencode_v46.csv`.

**02a_run_annotsv_filtered.sh** and **02b_run_annotsv_unfiltered.sh** annotate the intersection
and union cohort VCFs with AnnotSV (`-tx ENSEMBL`, `-variantconvertMode fullsplit`, VCF output).
The filtered run restricts annotation to the ALS candidate genes; the unfiltered run does not.
Neither run uses HPO terms.

```bash
export INPUT_DIR="$OCTO/merged" OUT_DIR="$ANNOTSV" \
       GENES=03_sv_annotation/data/ALS_candidate_gene_list.txt \
       ANNOTATIONS=/path/to/AnnotSV/share/AnnotSV
bash 03_sv_annotation/02a_run_annotsv_filtered.sh   --run-label 08102026
bash 03_sv_annotation/02b_run_annotsv_unfiltered.sh --run-label 08102026
```

- *Output:* `$ANNOTSV/octopusv_{intersect,union}_cohort_{filtered,unfiltered}_<label>/` with
  `*.annotated.tsv` and `*.annotated.vcf`.

### 04_sv_prioritisation: callset statistics and nomination

**01a_summarise_callset_qc.py** produces record-level summaries for each VCF separately. Records must be
PASS, biallelic, of known length and 50–100,000 bp; BND/TRA records are excluded. Run it on the Manta,
TIDDIT, intersection and union cohort VCFs and on the AnnotSV-annotated VCFs.

```bash
python 04_sv_prioritisation/01a_summarise_callset_qc.py \
  -v "$OCTO/merged/manta_tiddit.intersect.cohort.vcf" -o "$PRIO/qc/intersection" --callset intersection \
  --genotypes caller-reported        # needed for carrier and 1/1 summaries (Table 4.8)
```

**01b_prioritise_annotsv_events.py** consolidates AnnotSV rows by `AnnotSV_ID`. It nominates events that
overlap a Definitive, Strong or Moderate ALSoD gene **or** have a maximum AnnotSV score ≥ 0.9, then assigns
review tiers 1–4 from CASE/CTRL carrier counts (296/51). Union-only mode removes union events that share a
source ID, or exact chrom/start/end/type, with the intersection. Run it for the filtered and the
unfiltered annotations:

```bash
# intersection
python 04_sv_prioritisation/01b_prioritise_annotsv_events.py --mode intersection \
  --intersection-vcf "$ANNOTSV/octopusv_intersect_cohort_filtered_08102026/manta_tiddit.intersect.cohort.annotated.vcf" \
  --alsod-csv 03_sv_annotation/data/alsod_gene_list.csv --out-dir "$PRIO/intersection_filtered"
# union-only
python 04_sv_prioritisation/01b_prioritise_annotsv_events.py --mode union-only \
  --intersection-vcf <filtered intersection annotated VCF> \
  --union-vcf "$ANNOTSV/octopusv_union_cohort_filtered_08102026/manta_tiddit.union.cohort.annotated.vcf" \
  --alsod-csv 03_sv_annotation/data/alsod_gene_list.csv --out-dir "$PRIO/union_only_filtered"
# repeat both with the unfiltered annotations -> intersection_unfiltered, union_only_unfiltered
```

- *Output (per run):* `Supplementary_Table_AnnotSV_<scope>_event_prioritisation.tsv` (all events),
  `..._priority.tsv` (nominated), `Supplementary_Table_<scope>_manual_review_shortlist.tsv`, summary JSONs.
- These event tables are also inputs to Objective Four.

**02_build_participant_sv_table.py** writes one row per carrier and intersection event (6,707 carrier calls
for the 185 filtered records). It is a reference table only and was not used for nomination.

```bash
python 04_sv_prioritisation/02_build_participant_sv_table.py --mode all \
  --filtered-tsv <filtered intersection annotated.tsv> --unfiltered-tsv <unfiltered intersection annotated.tsv> \
  --genes-file 03_sv_annotation/data/ALS_candidate_gene_list.txt --out-dir "$PRIO/participant_table"
```

### 05_sv_audit: raw-call review and audited release

**01_extract_raw_calls.py** extracts raw Manta and TIDDIT records that match each shortlisted event for
**all** participants: same chromosome, compatible type, and ≥ 50% reciprocal overlap or both breakpoints
within 500 bp. This lets the audit detect missed carriers as well as unsupported ones.

```bash
python 05_sv_audit/01_extract_raw_calls.py \
  --intersection-tsv "$PRIO/intersection_filtered/Supplementary_Table_filtered_intersection_manual_review_shortlist.tsv" \
  --union-tsv        "$PRIO/union_only_filtered/Supplementary_Table_filtered_union_only_manual_review_shortlist.tsv" \
  --input-dir "$SAREK" --out-dir "$REVIEW"
```

- *Output:* `review_events.tsv`, `raw_record_matches.tsv`, `carrier_status.tsv`, `vcf_manifest.tsv`, `run_log.json`.

**02_score_raw_call_evidence.py** turns caller fields into split-read, discordant-pair, read-depth and
quality evidence, labels each carrier and event, and flags repeat, segmental-duplication, blacklist
and low-mapping-quality context.

```bash
python 05_sv_audit/02_score_raw_call_evidence.py --input-dir "$REVIEW" \
  --str-bed /path/to/strchive_hg38.bed \
  --intersection-annotsv-files <intersection annotated.tsv> --union-annotsv-files <union annotated.tsv>
# defaults: --min-split 3 --min-pairs 3 --del-max-ratio 0.75 --dup-min-ratio 1.25 --max-lq 0.3 --case-n 296 --control-n 51
```

- *Output:* `evidence_per_record.tsv`, `evidence_per_event.tsv`, `evidence_thresholds.json` in `$REVIEW`.

**03_build_audited_release.py** re-evaluates the 50 filtered-intersection nominations with the final
audit rules: breakpoints within 50 bp, length ratio ≥ 0.70, strict PASS, pooled evidence types. It also
checks sensitivity at 10/50/100 bp with ratio 0.70, and at 50 bp with ratio 0.50, then assigns each
nomination one of: primary, exploratory, deprioritised or excluded. **All paths must be absolute.**

```bash
python 05_sv_audit/03_build_audited_release.py --input-dir "$REVIEW" \
  --intersection-annotations <abs path, filtered intersection annotated.tsv> \
  --union-annotations <abs path, filtered union annotated.tsv> --out-dir "$RELEASE"
```

- *Output:* `audited_candidates.tsv`, `primary_candidates.tsv` (24 events),
  `participant_support.tsv` (participant–candidate pairs), `release_parameters.json`, input checksums.

**04_verify_audited_release.py** re-reads the raw records and checks counts, PASS and genotype handling,
matching limits and final decisions independently.

```bash
python 05_sv_audit/04_verify_audited_release.py --out-dir "$RELEASE" --input-dir "$REVIEW"
```

### 06_dashboard: proteGErna-SV

**proteGErna-SV.R** is a Shiny app for exploring an AnnotSV-annotated VCF (upload limit 60 MiB). It has
four views: Overview, Structural variants, Column descriptions and Resource search.
`sv_dashboard_helpers.R` and `www/` must stay in the same folder.

```bash
Rscript -e 'shiny::runApp("06_dashboard/proteGErna-SV.R", launch.browser = TRUE)'
```

The dissertation demonstrates it with the filtered AnnotSV intersection VCF. Keep participant-level
data within its access-controlled environment.

### figures: Chapter 4 figures

**make_chapter4_figures.R** reads the OctopuSV merged VCFs and stats, the prioritisation summaries and
the audited release. It writes Figures 4.3 and 4.4 (PDF + PNG). It sources `sv_thesis_style.R`, which in turn
loads `thesis_palette.R`.

```bash
Rscript figures/make_chapter4_figures.R <project_dir> <out_dir>
```

Check the input paths near the top of the script against your folder layout before running.

## Script-to-dissertation map

| Step / script | Chapter 4 methods | Results, tables and figures |
| --- | --- | --- |
| 01_sv_calling/01–02 | 4.2.3 SV detection with nf-core/sarek | Input to everything below |
| 01_sv_calling/03 | none | Not reported |
| 02_sv_consolidation/01 | 4.2.4 Harmonisation, caller concordance and cohort consolidation | 4.3.2–4.3.3; Table 4.5; Figure 4.2 (workflow) |
| 03_sv_annotation/01 | 4.2.5 Disease-focused annotation (154-gene ALSoD panel) | Gene categories used in 4.3.5 |
| 03_sv_annotation/02a–02b | 4.2.5 | Annotated VCFs used in 4.3.4–4.3.9 |
| 04_sv_prioritisation/01a | 4.2.6 Record statistics and recorded carrier counts | 4.3.2–4.3.4; Tables 4.6, 4.7, 4.8 |
| 04_sv_prioritisation/01b | 4.2.7 Event prioritisation and union comparison; 4.2.8 Selection of priority events | 4.3.5–4.3.6; Tables 4.3, 4.9, 4.10 (applies the rules in Tables 4.1–4.2) |
| 04_sv_prioritisation/02 | 4.2.6 (participant-level table) | 6,707 carrier calls (4.2.6) |
| 05_sv_audit/01–02 | 4.2.9 Technical review: review stage | Table 4.11; Appendix Table 4A.2 |
| 05_sv_audit/03 | 4.2.9 Technical review: audit stage | 4.3.7–4.3.8; Tables 4.12, 4.13; Figure 4.4 |
| 05_sv_audit/04 | 4.2.9 ("a separate script re-read the raw records…") | Verification only |
| 06_dashboard | 4.2.10 Interactive exploration and dashboard | 4.3.9; Figures 4.5–4.10; 4.4.4 |
| figures/make_chapter4_figures.R | none | Figures 4.3, 4.4 |

Figure 4.1 (workflow overview) and Figure 4.2 (OctopuSV diagram) are schematic diagrams that no script draws.

**Used later:** `primary_candidates.tsv`, `participant_support.tsv`, the four prioritisation
event tables, `alsod_gene_list.csv` and `manta_tiddit.intersect.cohort.vcf` are inputs to
Objective Four (Chapter 6, Section 6.2.7).

## Data and reference resources

The workflow uses AnswerALS cohort data, the [ALSoD ALS gene
database](https://alsod.ac.uk/), [Ensembl](https://www.ensembl.org/), and
AnnotSV annotation resources. Cite the source data, software, and resource
versions used in any resulting publication or dissertation chapter.

## License
