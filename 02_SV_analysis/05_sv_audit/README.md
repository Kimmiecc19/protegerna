# 05 Raw-call review and audited release

**Objective:** Objective Two: a reproducible workflow for structural-variant (SV) detection, consolidation, annotation, ALS-informed nomination and interactive exploration.  
**Dissertation:** Chapter 4, Sections 4.2.9 and 4.3.6–4.3.7; tables and figures: Table 4.3, Table 4.10, Table 4.11, Table 4.12, Figure 4.4, Table 4A.2, Table 4A.5  
**Back to:** [objective README](../README.md)

## What this step does

Checks every shortlisted event against each participant's raw Manta and TIDDIT records (≥ 50% reciprocal overlap, or both
breakpoints within 500 bp), scores split-read, read-pair, depth and repeat-context evidence, and re-tiers events from the raw-call
carrier counts. The audited release re-evaluates the 50 filtered intersection nominations under the final rules (50 bp minimum,
length ratio ≥ 0.70, strict PASS) and sensitivity policies, giving 24 primary candidates and 55 participant–candidate pairs. An
independent script re-checks the release.

## Scripts

| Script | What it does | Dissertation tables/figures |
| --- | --- | --- |
| `01a_prep_sarek_for_review.sh` | Reheader per-participant raw VCFs with cohort sample names for the raw-call review | Section 4.2.9 |
| `01b_extract_raw_calls.py` | Extract raw Manta/TIDDIT records matching each shortlisted event for every participant (≥ 50% RO or both breakpoints ≤ 500 bp) | Table 4.10, Table 4A.2 |
| `01c_score_raw_call_evidence.py` | Split-read, discordant-pair, depth and context evidence per carrier and event | Table 4.10, Table 4A.2 |
| `02a_build_audited_release.py` | Re-evaluate the 50 filtered-intersection nominations under the final audit rules (50 bp, length ratio 0.70, strict PASS) and sensitivity policies | Table 4.3, Table 4.11, Table 4.12, Figure 4.4, Table 4A.5 |
| `02b_verify_audited_release.py` | Independent re-check of counts, PASS/genotype handling, matching limits and dispositions | Table 4.12 |

## Order of running

1. `01a_prep_sarek_for_review.sh` – reheader the per-participant VCFs.
2. `01b_extract_raw_calls.py` then `01c_score_raw_call_evidence.py` for each set (intersection/union-only × filtered/unfiltered).
3. `02a_build_audited_release.py` on `intersection_filtered`.
4. `02b_verify_audited_release.py`.

## How to run each script

Commands are those used for the dissertation, with paths relative to this step's folder unless stated otherwise. Replace placeholders in angle brackets, and `/path/to/...` values for data or tools outside the repository, with your own paths. Every Python script prints its options with `--help`.

### `01a_prep_sarek_for_review.sh`

Reheader per-participant raw VCFs with cohort sample names for the raw-call review.

- **Dissertation:** Section 4.2.9
- **Inputs:** per-participant Sarek VCFs
- **Outputs:** fixed_vcf_names/*.vcf(.gz); 01a_fixed_vcf_names/fixed_vcf_list.txt
- **Run record:** fixed_vcf_list.txt
- **Run for the dissertation:** 2026-09-29
- **Before running:** Pass the per-participant Sarek VCF folders as arguments (controlled access), or set `INPUT_DIR_GLOB`. Reheadered VCFs go to `01a_fixed_vcf_names/fixed_vcf_names/` (override with `OUTPUT_DIR`); do not commit them.
- **Note:** mkdir bug fixed 8 Nov 2026. The review (01b) read fixed_concat_vcf_names on the server.

```bash
bash 01a_prep_sarek_for_review.sh [input_dir ...]
```

### `01b_extract_raw_calls.py`

Extract raw Manta/TIDDIT records matching each shortlisted event for every participant (≥ 50% RO or both breakpoints ≤ 500 bp).

- **Dissertation:** Section 4.2.9; Table 4.10, Table 4A.2
- **Inputs:** 02c manual-review shortlists; per-participant raw VCFs
- **Outputs:** 01bc_results_raw_call_review/<set>/review_events.tsv, raw_record_matches.tsv, carrier_status.tsv, vcf_manifest.tsv
- **Run record:** <set>/run_log.json (parameters, input MD5s)
- **Run for the dissertation:** 2026-10-05
- **Before running:** The raw VCFs are controlled-access and are not in the repository; point `--input-dir` at the reheadered VCFs from `01a`.
- **Note:** Raw VCFs are not in the repo, so this step cannot be re-run locally.

```bash
python 01b_extract_raw_calls.py --intersection-tsv ../04_sv_prioritization/02c_results_prioritise_annotsv_events/intersection_filtered/Supplementary_Table_intersection_manual_review_shortlist.tsv --input-dir 01a_fixed_vcf_names/fixed_vcf_names --vcf-glob '*.vcf.gz' --out-dir 01bc_results_raw_call_review/intersection_filtered --padding 500 --min-ro 0.5
# one run per set: intersection/union_only x filtered/unfiltered (union runs use --union-tsv)
```

### `01c_score_raw_call_evidence.py`

Split-read, discordant-pair, depth and context evidence per carrier and event; raw-call re-tiering.

- **Dissertation:** Section 4.2.9; Table 4.10, Table 4A.2
- **Inputs:** 01b outputs; STRchive BED; AnnotSV annotated TSVs
- **Outputs:** 01bc_results_raw_call_review/<set>/evidence_per_{record,carrier,event}.tsv, evidence_summary.tsv, tiddit_cov_order_check.tsv
- **Run record:** <set>/evidence_thresholds.json
- **Run for the dissertation:** 2026-10-05

```bash
python 01c_score_raw_call_evidence.py --input-dir 01bc_results_raw_call_review/<set> --str-bed ../04_sv_prioritization/data/STRchive-disease-loci.hg38.general.bed --intersection-annotsv-files ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_intersect_cohort_filtered_05102026/manta_tiddit.intersect.cohort.annotated.tsv   # defaults: --min-split 3 --min-pairs 3 --del-max-ratio 0.75 --dup-min-ratio 1.25 --max-lq 0.3 --case-n 296 --control-n 51
```

### `02a_build_audited_release.py`

Re-evaluate the 50 filtered-intersection nominations under the final audit rules (50 bp, length ratio 0.70, strict PASS) and sensitivity policies.

- **Dissertation:** Sections 4.2.9, 4.3.7; 6.2.7; Table 4.3, Table 4.11, Table 4.12, Figure 4.4, Table 4A.5
- **Inputs:** intersection_filtered review outputs; filtered annotated TSVs (05102026)
- **Outputs:** 02_results_audited_release/ (audited_candidates, primary_candidates, participant_support, integration_pairs, matching_sensitivity, raw_match_audit, consolidation_findings, summary.json)
- **Run record:** 02_results_audited_release/input_checksums.json, release_parameters.json
- **Run for the dissertation:** 2026-10-05
- **Note:** primary_candidates.tsv and participant_support.tsv feed Chapter 6.

```bash
python 02a_build_audited_release.py --input-dir 01bc_results_raw_call_review/intersection_filtered --intersection-annotations ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_intersect_cohort_filtered_05102026/manta_tiddit.intersect.cohort.annotated.tsv --union-annotations ../03_sv_annotation/02a_results_annotsv_filtered/octopusv_union_cohort_filtered_05102026/manta_tiddit.union.cohort.annotated.tsv --out-dir 02_results_audited_release
```

### `02b_verify_audited_release.py`

Independent re-check of counts, PASS/genotype handling, matching limits and dispositions.

- **Dissertation:** Section 4.2.9; Table 4.12
- **Inputs:** release outputs; review inputs
- **Outputs:** 02_results_audited_release/verification.json
- **Run record:** verification.json
- **Run for the dissertation:** 2026-10-05

```bash
python 02b_verify_audited_release.py --out-dir 02_results_audited_release --input-dir 01bc_results_raw_call_review/intersection_filtered
```

**Used later:** `02_results_audited_release/primary_candidates.tsv` and `participant_support.tsv` are inputs to Objective Four.

**Next step:** [`06_dashboard`](../06_dashboard/README.md).

## Data access

Answer ALS data are controlled-access and are not in this repository. Request them from the [Answer ALS data portal](https://dataportal.answerals.org/) under its data-use terms. Do not commit participant-level files, credentials or access tokens.
