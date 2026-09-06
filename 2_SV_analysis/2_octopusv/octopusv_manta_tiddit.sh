#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'TXT'
Usage: octopusv_manta_tiddit --root-dir DIR --outdir DIR [options]

Correct Manta and TIDDIT VCFs, merge callers within each participant, build
sample-mode cohorts, and generate reports.

Required:
  -r, --root-dir DIR   Sarek results directory
  -o, --outdir DIR     Output directory

Options:
      --min-svlen N    Minimum SV length (default: 50)
      --max-svlen N    Maximum SV length (default: 100000)
      --force-merge    Rebuild merges even when valid outputs exist
      --skip-merge     Reuse valid merges and never run a merge command
      --dry-run        Validate outputs and print the resume plan without writes
      --status         Alias for --dry-run
      --adopt-existing Treat legacy outputs with no parameter record as having
                       been created with the supplied SV-length settings
  -h, --help           Show this help
TXT
}

die() { echo "ERROR: $1" >&2; exit "${2:-1}"; }

ROOT_DIR=""
OUTDIR=""
MIN_SVLEN=50
MAX_SVLEN=100000
FORCE_MERGE=false
SKIP_MERGE=false
DRY_RUN=false
ADOPT_EXISTING=false
PARAMETERS_CHANGED=false
INPUTS_CHANGED=false
declare -A COHORT_CHANGED=()
REUSED=0; REBUILD=0; INVALID=0; BLOCKED=0

while (( $# )); do
    case "$1" in
        -r|--root-dir) ROOT_DIR="${2:?ERROR: $1 requires a directory}"; shift 2 ;;
        -o|--outdir) OUTDIR="${2:?ERROR: $1 requires a directory}"; shift 2 ;;
        --min-svlen) MIN_SVLEN="${2:?ERROR: $1 requires an integer}"; shift 2 ;;
        --max-svlen) MAX_SVLEN="${2:?ERROR: $1 requires an integer}"; shift 2 ;;
        --force-merge) FORCE_MERGE=true; shift ;;
        --skip-merge) SKIP_MERGE=true; shift ;;
        --dry-run|--status) DRY_RUN=true; shift ;;
        --adopt-existing) ADOPT_EXISTING=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ -n "$ROOT_DIR" && -d "$ROOT_DIR" ]] || die "Valid --root-dir is required" 2
[[ -n "$OUTDIR" ]] || die "--outdir is required" 2
[[ "$MIN_SVLEN" =~ ^[0-9]+$ && "$MAX_SVLEN" =~ ^[0-9]+$ ]] || die "SV lengths must be non-negative integers" 2
(( MIN_SVLEN <= MAX_SVLEN )) || die "--min-svlen exceeds --max-svlen" 2
[[ "$FORCE_MERGE" == false || "$SKIP_MERGE" == false ]] || die "--force-merge and --skip-merge are mutually exclusive" 2

for cmd in bcftools octopusv; do
    command -v "$cmd" >/dev/null || die "Required command not found: $cmd" 127
done

[[ "$DRY_RUN" == true ]] || mkdir -p "$OUTDIR"/{corrected/{manta,tiddit},cleaned/{manta,tiddit},tmp_vcf/{manta,tiddit},merged,stats,plots,circos,logs,per_sample/{union,intersect}/{caller,vcf,consensus}}

PARAM_FILE="$OUTDIR/.octopusv_manta_tiddit.parameters"
PARAM_VALUE="format=1 min_svlen=$MIN_SVLEN max_svlen=$MAX_SVLEN"
if [[ -s "$PARAM_FILE" ]]; then
    [[ "$(<"$PARAM_FILE")" == "$PARAM_VALUE" ]] || PARAMETERS_CHANGED=true
elif find "$OUTDIR/corrected" "$OUTDIR/merged" -type f -size +0c -print -quit 2>/dev/null | grep -q .; then
    if [[ "$ADOPT_EXISTING" == false ]]; then
        echo "ERROR: Existing outputs have no parameter record." >&2
        echo "ERROR: Use --adopt-existing only if they used min-svlen=$MIN_SVLEN and max-svlen=$MAX_SVLEN." >&2
        exit 2
    fi
    echo "WARNING: Adopting legacy outputs with the supplied SV-length settings." >&2
fi

reuse() { echo "REUSE: $1"; REUSED=$((REUSED+1)); }
rebuild() { echo "REBUILD: $1"; REBUILD=$((REBUILD+1)); }
invalid() { echo "INVALID/STALE: $1"; INVALID=$((INVALID+1)); }
blocked() { echo "BLOCKED: $1"; BLOCKED=$((BLOCKED+1)); }
valid_vcf() { [[ -s "$1" ]] && bcftools view -h "$1" >/dev/null 2>&1; }
valid_svcf() { validate_svcf_logged "$1" /dev/null; }
validate_svcf_logged() {
    local input="$1" log="$2" probe rc
    [[ -s "$input" ]] || {
        printf 'ERROR: SVCF is missing or empty: %s\n' "$input" > "$log"
        return 1
    }
    probe="${TMPDIR:-/tmp}/octopusv-svcf-probe.$$.$RANDOM.vcf"
    rm -f "$probe"
    if octopusv svcf2vcf -i "$input" -o "$probe" > "$log" 2>&1; then
        if valid_vcf "$probe"; then
            rc=0
        else
            printf 'ERROR: SVCF conversion did not produce a valid VCF: %s\n' "$probe" >> "$log"
            rc=1
        fi
    else
        rc=$?
    fi
    rm -f "$probe"
    return "$rc"
}
valid_png() { [[ -s "$1" ]] && [[ "$(od -An -tx1 -N8 "$1" 2>/dev/null | tr -d ' \n')" == 89504e470d0a1a0a ]]; }
valid_plots() {
    local prefix="$1" dependency="$2" f found=false
    for f in "${prefix}"*; do
        [[ -f "$f" ]] || continue
        found=true
        [[ -s "$f" && "$f" -nt "$dependency" ]] || return 1
    done
    [[ "$found" == true ]]
}
fresh() { local out="$1" i; shift; [[ -e "$out" ]] || return 1; for i in "$@"; do [[ "$out" -nt "$i" ]] || return 1; done; }
usable_vcf() { valid_vcf "$1" && fresh "$@"; }
usable_svcf() { valid_svcf "$1" && fresh "$@"; }

sample_name() {
    basename "$1" | sed -E 's/\.(manta|tiddit)\..*$//'
}

input_vcfs() {
    find "$ROOT_DIR" -type f -path "*/variant_calling/$1/*" -name "*.$1*.vcf*" \
        ! -name '*.tbi' ! -name '*.csi' -print0 | sort -z
}

validate_input_sample_sets() {
    local caller file diff
    local -a manta_names=() tiddit_names=()
    for caller in manta tiddit; do
        local -a names=()
        while IFS= read -r -d '' file; do names+=("$(sample_name "$file")"); done < <(input_vcfs "$caller")
        (( ${#names[@]} > 0 )) || die "No $caller input VCFs found"
        if [[ "$(printf '%s\n' "${names[@]}" | sort | uniq -d | head -n 1)" != "" ]]; then
            echo "ERROR: Duplicate $caller sample names would overwrite outputs:" >&2
            printf '%s\n' "${names[@]}" | sort | uniq -d >&2
            exit 1
        fi
        if [[ "$caller" == manta ]]; then manta_names=("${names[@]}"); else tiddit_names=("${names[@]}"); fi
    done
    diff="$(comm -3 <(printf '%s\n' "${manta_names[@]}" | sort) <(printf '%s\n' "${tiddit_names[@]}" | sort))"
    [[ -z "$diff" ]] || { echo "ERROR: Manta and TIDDIT sample-name sets differ:" >&2; printf '%s\n' "$diff" >&2; exit 1; }
}

reheader_vcf() {
    local vcf="$1" sample="$2" caller="$3" current tmp
    current="$(bcftools query -l "$vcf")"
    [[ "$current" == "$sample" ]] && return

    [[ "$(printf '%s\n' "$current" | sed '/^$/d' | wc -l)" -eq 1 ]] || {
        printf 'ERROR: Expected one sample in %s; found:\n%s\n' "$vcf" "$current" >&2
        exit 1
    }

    case "$vcf" in
        *.vcf.gz) tmp="${vcf%.vcf.gz}.reheader.tmp.vcf.gz" ;;
        *.vcf) tmp="${vcf%.vcf}.reheader.tmp.vcf" ;;
        *) die "Unsupported VCF filename: $vcf" ;;
    esac

    echo "Reheadering $vcf: $current -> $sample"
    if [[ "$DRY_RUN" == true ]]; then rebuild "reheader $caller/$sample"; return; fi
    rm -f "$tmp" "$tmp.tbi" "$tmp.csi"
    bcftools reheader -s <(printf '%s\n' "$sample") "$vcf" -o "$tmp" \
        > "$OUTDIR/logs/${sample}.${caller}.reheader.log" 2>&1

    [[ -s "$tmp" && "$(bcftools query -l "$tmp")" == "$sample" ]] || {
        echo "ERROR: Failed to reheader $vcf" >&2
        rm -f "$tmp"
        exit 1
    }

    mv -f "$tmp" "$vcf"
    rm -f "$vcf.tbi" "$vcf.csi"
}

correct_vcfs() {
    local caller vcf sample clean corrected tmp clean_tmp corrected_tmp clean_changed correct_log validate_log rc
    caller="$1"
    local -a vcfs

    mapfile -d '' vcfs < <(input_vcfs "$caller")
    (( ${#vcfs[@]} )) || die "No $caller VCFs found"
    echo "Found ${#vcfs[@]} $caller VCFs"

    for vcf in "${vcfs[@]}"; do
        sample="$(sample_name "$vcf")"
        clean="$OUTDIR/cleaned/$caller/${sample}.${caller}.clean.vcf.gz"
        corrected="$OUTDIR/corrected/$caller/${sample}.${caller}.corrected.svcf"
        tmp="$OUTDIR/tmp_vcf/$caller/${sample}.${caller}.tmp.vcf"
        clean_tmp="${clean%.vcf.gz}.tmp.$$.vcf.gz"
        corrected_tmp="${corrected%.svcf}.tmp.$$.svcf"
        correct_log="$OUTDIR/logs/${sample}.${caller}.correct.log"
        validate_log="$OUTDIR/logs/${sample}.${caller}.correct.validate.log"
        clean_changed=false

        reheader_vcf "$vcf" "$sample" "$caller"

        if usable_vcf "$clean" "$vcf"; then
            reuse "$clean"
        else
            INPUTS_CHANGED=true
            clean_changed=true
            [[ -e "$clean" ]] && invalid "$clean"
            rebuild "$clean"
            if [[ "$DRY_RUN" == false ]]; then
                rm -f "$clean_tmp"
                echo "Cleaning $caller VCF for $sample"
                octopusv clean "$vcf" "$clean_tmp" > "$OUTDIR/logs/${sample}.${caller}.clean.log" 2>&1
                valid_vcf "$clean_tmp" || { rm -f "$clean_tmp"; die "Cleaning failed for $sample"; }
                mv -f "$clean_tmp" "$clean"
            fi
        fi

        if [[ "$PARAMETERS_CHANGED" == false && "$clean_changed" == false ]] && usable_svcf "$corrected" "$clean"; then
            reuse "$corrected"
        else
            INPUTS_CHANGED=true
            [[ -e "$corrected" ]] && invalid "$corrected"
            rebuild "$corrected"
            if [[ "$DRY_RUN" == false ]]; then
                rm -f "$corrected_tmp" "$tmp"
                echo "Correcting $caller VCF for $sample"
                if ! gzip -cd "$clean" > "$tmp"; then
                    rm -f "$tmp" "$corrected_tmp"
                    die "Could not decompress cleaned $caller VCF for $sample: $clean"
                fi
                if octopusv correct -i "$tmp" -o "$corrected_tmp" \
                    --min-svlen "$MIN_SVLEN" --max-svlen "$MAX_SVLEN" --filter-pass \
                    > "$correct_log" 2>&1; then
                    :
                else
                    rc=$?
                    rm -f "$tmp" "$corrected_tmp"
                    echo "ERROR: OctopuSV correction command failed for $sample ($caller; exit code $rc)" >&2
                    tail -n 50 "$correct_log" >&2
                    exit 1
                fi
                rm -f "$tmp"
                if ! validate_svcf_logged "$corrected_tmp" "$validate_log"; then
                    rm -f "$corrected_tmp"
                    echo "ERROR: Correction completed, but its SVCF failed validation for $sample ($caller)" >&2
                    tail -n 50 "$validate_log" >&2
                    exit 1
                fi
                mv -f "$corrected_tmp" "$corrected"
            fi
        fi
    done
}

merge_sample_cohort() {
    local label="$1" input_dir="$2" glob="$3" name_regex="$4"
    local cohort_svcf tmp log names
    local -a files

    cohort_svcf="$OUTDIR/merged/${label}.svcf"
    tmp="${cohort_svcf}.tmp.$$"
    log="$OUTDIR/logs/${label}.sample_merge.log"

    mapfile -t files < <(find "$input_dir" -maxdepth 1 -type f -name "$glob" | sort)
    if (( ${#files[@]} == 0 )); then
        [[ "$DRY_RUN" == true ]] && { blocked "no current input SVCFs for $label"; return; }
        die "No input SVCFs for $label"
    fi
    names="$(printf '%s\n' "${files[@]}" | sed -E "s|.*/||; s/${name_regex}//" | paste -sd, -)"

    if [[ "$SKIP_MERGE" == true ]]; then
        if [[ "$PARAMETERS_CHANGED" == true ]]; then blocked "$cohort_svcf requires rebuilding after parameter changes"; return; fi
        if valid_svcf "$cohort_svcf"; then reuse "$cohort_svcf (--skip-merge)"; return; fi
        blocked "$cohort_svcf is missing/invalid and merge is skipped"; return
    fi
    if [[ "$FORCE_MERGE" == false && "$PARAMETERS_CHANGED" == false && "$INPUTS_CHANGED" == false ]] && usable_svcf "$cohort_svcf" "${files[@]}"; then
        reuse "$cohort_svcf"; return
    fi
    [[ -e "$cohort_svcf" ]] && invalid "$cohort_svcf"
    rebuild "$cohort_svcf"
    COHORT_CHANGED["$label"]=true
    [[ "$DRY_RUN" == true ]] && return

    echo "[$(date --iso-8601=seconds)] Merging ${#files[@]} samples for $label"
    rm -f "$tmp"
    octopusv merge -i "${files[@]}" --mode sample --sample-names "$names" --union -o "$tmp" > "$log" 2>&1 || {
        rm -f "$tmp"
        die "Sample merge failed for $label"
    }
    valid_svcf "$tmp" || { rm -f "$tmp"; die "New cohort failed validation for $label"; }
    mv -f "$tmp" "$cohort_svcf"
}

merge_callers_per_sample() {
    local operation manta tiddit sample caller_svcf sample_vcf consensus base tmp_vcf tmp_consensus caller_changed vcf_changed
    operation="$1"
    base="$OUTDIR/per_sample/$operation"
    local -a manta_files

    mapfile -t manta_files < <(find "$OUTDIR/corrected/manta" -maxdepth 1 -type f -name '*.manta.corrected.svcf' | sort)
    if (( ${#manta_files[@]} == 0 )); then
        [[ "$DRY_RUN" == true ]] && { blocked "no corrected Manta SVCFs for per-sample $operation"; return; }
        die "No corrected Manta SVCFs found"
    fi

    echo "[$(date --iso-8601=seconds)] Building per-sample Manta/TIDDIT $operation callsets"
    for manta in "${manta_files[@]}"; do
        caller_changed=false
        vcf_changed=false
        sample="$(basename "$manta" .manta.corrected.svcf)"
        tiddit="$OUTDIR/corrected/tiddit/${sample}.tiddit.corrected.svcf"
        # Keep the simple/simple_no_validate layout so their completed stages
        # can be validated and reused during an upgrade/resume.
        caller_svcf="$base/caller/${sample}.${operation}.caller.svcf"
        sample_vcf="$base/vcf/${sample}.${operation}.vcf"
        consensus="$base/consensus/${sample}.${operation}.consensus.svcf"

        [[ -s "$tiddit" ]] || die "Missing TIDDIT SVCF for $sample"
        if [[ "$SKIP_MERGE" == true && "$PARAMETERS_CHANGED" == true ]]; then blocked "$caller_svcf requires rebuilding after parameter changes"; continue; fi
        if [[ "$SKIP_MERGE" == true ]] && ! valid_svcf "$caller_svcf"; then blocked "$caller_svcf is missing/invalid and merge is skipped"; continue; fi
        if [[ "$FORCE_MERGE" == true || "$PARAMETERS_CHANGED" == true || ! -s "$sample_vcf" ]] || ! valid_svcf "$caller_svcf" || ! fresh "$caller_svcf" "$manta" "$tiddit"; then
            [[ -e "$caller_svcf" ]] && invalid "$caller_svcf"
            if [[ "$SKIP_MERGE" == true ]]; then reuse "$caller_svcf (--skip-merge)"; else
            caller_changed=true
            rebuild "$caller_svcf"
            if [[ "$DRY_RUN" == false ]]; then
            rm -f "$caller_svcf" "$sample_vcf" "$consensus"
            octopusv merge -i "$manta" "$tiddit" --mode caller --caller-names Manta,TIDDIT \
                "--$operation" -o "$caller_svcf" \
                > "$OUTDIR/logs/${sample}.manta_tiddit.${operation}.caller_merge.log" 2>&1 || {
                rm -f "$caller_svcf"
                die "Per-sample $operation merge failed for $sample"
            }
            fi
            fi
        else
            reuse "$caller_svcf"
        fi

        # Conversion followed by bcftools header parsing is the SVCF
        # parser/integrity check at this stage.
        if [[ "$FORCE_MERGE" == true || "$PARAMETERS_CHANGED" == true || "$caller_changed" == true ]] || ! usable_vcf "$sample_vcf" "$caller_svcf"; then
            vcf_changed=true
            [[ -e "$sample_vcf" ]] && invalid "$sample_vcf"
            rebuild "$sample_vcf"
            if [[ "$DRY_RUN" == false ]]; then
            tmp_vcf="${sample_vcf}.tmp.$$"
            rm -f "$tmp_vcf"
            octopusv svcf2vcf -i "$caller_svcf" -o "$tmp_vcf" \
                > "$OUTDIR/logs/${sample}.manta_tiddit.${operation}.svcf2vcf.log" 2>&1 || {
                rm -f "$tmp_vcf"
                die "Caller SVCF conversion failed for $sample ($operation)"
            }
            valid_vcf "$tmp_vcf" || {
                rm -f "$tmp_vcf"
                die "Caller SVCF conversion produced no output for $sample ($operation)"
            }
            mv -f "$tmp_vcf" "$sample_vcf"
            fi
        else
            reuse "$sample_vcf"
        fi

        if [[ "$FORCE_MERGE" == true || "$PARAMETERS_CHANGED" == true || "$vcf_changed" == true ]] || ! usable_svcf "$consensus" "$sample_vcf"; then
            INPUTS_CHANGED=true
            [[ -e "$consensus" ]] && invalid "$consensus"
            rebuild "$consensus"
            if [[ "$DRY_RUN" == false ]]; then
            tmp_consensus="${consensus}.tmp.$$"
            rm -f "$tmp_consensus"
            octopusv correct -i "$sample_vcf" -o "$tmp_consensus" \
                --min-svlen "$MIN_SVLEN" --max-svlen "$MAX_SVLEN" --filter-pass \
                > "$OUTDIR/logs/${sample}.manta_tiddit.${operation}.consensus_correct.log" 2>&1 || {
                rm -f "$tmp_consensus"
                die "Consensus correction failed for $sample ($operation)"
            }
            valid_svcf "$tmp_consensus" || {
                rm -f "$tmp_consensus"
                die "Consensus correction produced no output for $sample ($operation)"
            }
            mv -f "$tmp_consensus" "$consensus"
            fi
        else
            reuse "$consensus"
        fi

        [[ "$DRY_RUN" == true || -s "$consensus" ]] || die "Consensus correction failed for $sample ($operation)"
    done

    local tiddit_count consensus_count
    tiddit_count="$(find "$OUTDIR/corrected/tiddit" -maxdepth 1 -type f -name '*.tiddit.corrected.svcf' | wc -l)"
    consensus_count="$(find "$base/consensus" -maxdepth 1 -type f -name '*.consensus.svcf' | wc -l)"
    [[ "$DRY_RUN" == true || ( "$tiddit_count" -eq "${#manta_files[@]}" && "$consensus_count" -eq "${#manta_files[@]}" ) ]] || {
        die "Sample counts differ: Manta=${#manta_files[@]}, TIDDIT=$tiddit_count, consensus=$consensus_count"
    }
}

report_and_convert() {
    local label="$1" svcf vcf stats circos stats_tmp circos_tmp vcf_tmp
    svcf="$OUTDIR/merged/${label}.svcf"
    vcf="$OUTDIR/merged/${label}.vcf"
    stats="$OUTDIR/stats/${label}.stats.txt"
    circos="$OUTDIR/circos/${label}.circos.png"
    stats_tmp="$OUTDIR/stats/${label}.stats.tmp.$$.txt"
    circos_tmp="$OUTDIR/circos/${label}.circos.tmp.$$.png"
    vcf_tmp="$OUTDIR/merged/${label}.tmp.$$.vcf"

    if ! valid_svcf "$svcf"; then
        if [[ "$DRY_RUN" == true && "${COHORT_CHANGED[$label]:-false}" == true ]]; then
            rebuild "$label reports and VCF (after planned cohort rebuild)"
            return
        fi
        blocked "reports for $label (cohort unavailable)"; return
    fi

    if [[ "$FORCE_MERGE" == false && "$PARAMETERS_CHANGED" == false && "${COHORT_CHANGED[$label]:-false}" == false ]] && usable_vcf "$vcf" "$svcf" && [[ -s "$stats" ]] && fresh "$stats" "$svcf" \
        && valid_png "$circos" && fresh "$circos" "$svcf" \
        && valid_plots "$OUTDIR/plots/$label" "$stats"; then
        reuse "$label reports and VCF"
        return
    fi
    [[ -e "$vcf" ]] && invalid "$label reports or VCF"
    rebuild "$label reports and VCF"
    [[ "$DRY_RUN" == true ]] && return

    echo "Generating reports for $label"
    rm -f "$stats_tmp" "$circos_tmp" "$vcf_tmp"
    octopusv stat -i "$svcf" -o "$stats_tmp" --report > "$OUTDIR/logs/${label}.stat.log" 2>&1
    [[ -s "$stats_tmp" ]] || { rm -f "$stats_tmp"; die "Statistics failed for $label"; }
    mv -f "$stats_tmp" "$stats"
    octopusv plot "$stats" -o "$OUTDIR/plots/$label" > "$OUTDIR/logs/${label}.plot.log" 2>&1
    valid_plots "$OUTDIR/plots/$label" "$stats" || die "Plot generation failed for $label"
    octopusv plot-circos -i "$svcf" -o "$circos_tmp" > "$OUTDIR/logs/${label}.circos.log" 2>&1
    valid_png "$circos_tmp" || { rm -f "$circos_tmp"; die "Circos plot failed for $label"; }
    mv -f "$circos_tmp" "$circos"
    octopusv svcf2vcf -i "$svcf" -o "$vcf_tmp" > "$OUTDIR/logs/${label}.svcf2vcf.log" 2>&1
    valid_vcf "$vcf_tmp" || { rm -f "$vcf_tmp"; die "VCF conversion failed for $label"; }
    mv -f "$vcf_tmp" "$vcf"

    if [[ "$label" =~ ^manta_tiddit\.(union|intersect)\.cohort$ ]]; then
        local operation expected observed unique
        operation="${BASH_REMATCH[1]}"
        expected="$(find "$OUTDIR/per_sample/$operation/consensus" -maxdepth 1 -type f -name '*.consensus.svcf' | wc -l)"
        observed="$(bcftools query -l "$vcf" | wc -l)"
        unique="$(bcftools query -l "$vcf" | sort -u | wc -l)"
        [[ "$observed" -eq "$expected" && "$unique" -eq "$expected" ]] || {
            die "$label sample columns incomplete/duplicated: expected=$expected observed=$observed unique=$unique"
        }
        echo "Confirmed $observed unique sample columns in ${label}.vcf"
    fi
}

validate_input_sample_sets

for caller in manta tiddit; do
    INPUTS_CHANGED=false
    correct_vcfs "$caller"
    merge_sample_cohort "$caller.cohort" "$OUTDIR/corrected/$caller" "*.${caller}.corrected.svcf" "\\.${caller}\\.corrected\\.svcf$"
done

for operation in union intersect; do
    INPUTS_CHANGED=false
    merge_callers_per_sample "$operation"
    merge_sample_cohort "manta_tiddit.${operation}.cohort" "$OUTDIR/per_sample/$operation/consensus" \
        '*.consensus.svcf' '\.(union|intersect)\.consensus\.svcf$'
done

for label in manta.cohort tiddit.cohort manta_tiddit.union.cohort manta_tiddit.intersect.cohort; do
    report_and_convert "$label"
done

printf 'Resume summary: reused=%d rebuild=%d invalid_or_stale=%d blocked=%d mode=%s\n' \
    "$REUSED" "$REBUILD" "$INVALID" "$BLOCKED" "$([[ "$DRY_RUN" == true ]] && echo dry-run || echo execute)"
(( BLOCKED == 0 )) || die "One or more required stages are blocked" 3
if [[ "$DRY_RUN" == false ]]; then
    param_tmp="${PARAM_FILE}.tmp.$$"
    printf '%s\n' "$PARAM_VALUE" > "$param_tmp"
    mv -f "$param_tmp" "$PARAM_FILE"
fi
printf 'Done. Outputs are in %s\n' "$OUTDIR"

# OctopuSV citation:
# Guo Q, Li Y, Wang T-Y, Ramakrishnan A, Yang R. OctopuSV and TentacleSV:
# a one-stop toolkit for multi-sample, cross-platform structural variant
# comparison and analysis. Bioinformatics. 2025; doi:10.1093/bioinformatics/btaf599.
