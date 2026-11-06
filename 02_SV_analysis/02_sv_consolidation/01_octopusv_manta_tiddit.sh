#!/usr/bin/env bash
set -euo pipefail

# Reports and circos plots are generated for the four cohort SVCFs only, not per-sample SVCFs.
usage() {
    cat <<'TXT'
Usage: octopusv_manta_tiddit --input-dir DIR --out-dir DIR [options]

Correct Manta and TIDDIT VCFs, merge callers within each participant, build
sample-mode cohorts, and generate reports.

Required:
  -r, --input-dir DIR   Sarek results directory
  -o, --out-dir DIR     Output directory

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

INPUT_DIR=""
OUT_DIR=""
MIN_SVLEN=50
MAX_SVLEN=100000
FORCE_MERGE=false
SKIP_MERGE=false
DRY_RUN=false
ADOPT_EXISTING=false
PARAMETERS_CHANGED=false
INPUTS_CHANGED=false
declare -A COHORT_CHANGED=()
declare -A COHORT_BLOCKED=()
declare -A CORRECTED_CHANGED=()
declare -a CURRENT_SAMPLE_IDS=() MANTA_INPUTS=() TIDDIT_INPUTS=()
REUSED=0; REBUILD=0; INVALID=0; BLOCKED=0

while (( $# )); do
    case "$1" in
        -r|--input-dir|--root-dir) INPUT_DIR="${2:?ERROR: $1 requires a directory}"; shift 2 ;;
        -o|--out-dir|--outdir) OUT_DIR="${2:?ERROR: $1 requires a directory}"; shift 2 ;;
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

[[ -n "$INPUT_DIR" && -d "$INPUT_DIR" ]] || { echo "ERROR: Valid --input-dir is required" >&2; exit 2; }
[[ -n "$OUT_DIR" ]] || { echo "ERROR: --out-dir is required" >&2; exit 2; }
[[ "$MIN_SVLEN" =~ ^[0-9]+$ && "$MAX_SVLEN" =~ ^[0-9]+$ ]] || { echo "ERROR: SV lengths must be non-negative integers" >&2; exit 2; }
(( MIN_SVLEN <= MAX_SVLEN )) || { echo "ERROR: --min-svlen exceeds --max-svlen" >&2; exit 2; }
[[ "$FORCE_MERGE" == false || "$SKIP_MERGE" == false ]] || { echo "ERROR: --force-merge and --skip-merge are mutually exclusive" >&2; exit 2; }

for cmd in bcftools octopusv; do
    command -v "$cmd" >/dev/null || { echo "ERROR: Required command not found: $cmd" >&2; exit 127; }
done

[[ "$DRY_RUN" == true ]] || mkdir -p "$OUT_DIR"/{working/{manta,tiddit},corrected/{manta,tiddit},cleaned/{manta,tiddit},tmp_vcf/{manta,tiddit},merged,stats,plots,circos,logs,per_sample/{union,intersect}/{caller,vcf,consensus}}

PARAM_FILE="$OUT_DIR/.octopusv_manta_tiddit.parameters"
PARAM_VALUE="format=1 min_svlen=$MIN_SVLEN max_svlen=$MAX_SVLEN"
if [[ -s "$PARAM_FILE" ]]; then
    [[ "$(<"$PARAM_FILE")" == "$PARAM_VALUE" ]] || PARAMETERS_CHANGED=true
elif find "$OUT_DIR/corrected" "$OUT_DIR/merged" -type f -size +0c -print -quit 2>/dev/null | grep -q .; then
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
nonempty() { [[ -s "$1" ]]; }
valid_vcf() { [[ -s "$1" ]] && bcftools view -h "$1" >/dev/null 2>&1; }
# An SVCF is valid when OctopuSV can convert it to a valid VCF. Diagnostics go to $2 if given.
valid_svcf() {
    local input="$1" log="${2:-/dev/null}" probe rc=1
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
        fi
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

# OctopuSV names side outputs (HTML report, plots, circos tables) after the -o path.
# Rename those written next to a temporary output to match the published name.
publish_side_outputs() {
    local tmp_prefix="$1" final_prefix="$2" f
    for f in "$tmp_prefix"[._]*; do
        [[ -e "$f" ]] && mv -f "$f" "${final_prefix}${f#"$tmp_prefix"}"
    done
    return 0
}

# Run "${@:6}" (which must write TMP) with output to LOG, check TMP with CHECK, then move it to OUTPUT.
run_to() {
    local output="$1" tmp="$2" check="$3" log="$4" failed="$5" invalid_msg="$6"
    shift 6
    rm -f "$tmp"
    "$@" > "$log" 2>&1 || { rm -f "$tmp"; echo "ERROR: $failed" >&2; exit 1; }
    "$check" "$tmp" || { rm -f "$tmp"; echo "ERROR: $invalid_msg" >&2; exit 1; }
    mv -f "$tmp" "$output"
}

sample_id_from_path() {
    basename "$1" | sed -E 's/\.(manta|tiddit)\..*$//'
}

validate_input_sample_sets() {
    local caller file sample_id diff
    local -a manta_names=() tiddit_names=() inputs=()
    for caller in manta tiddit; do
        local -a names=()
        inputs=()
        while IFS= read -r -d '' file; do
            names+=("$(sample_id_from_path "$file")")
            inputs+=("$file")
        done < <(
            find "$INPUT_DIR" -type f -path "*/variant_calling/${caller}/*" -name "*.${caller}*.vcf*" ! -name '*.tbi' ! -name '*.csi' -print0 | sort -z
        )
        (( ${#names[@]} > 0 )) || { echo "ERROR: No $caller input VCFs found" >&2; exit 1; }
        if [[ "$(printf '%s\n' "${names[@]}" | sort | uniq -d | head -n 1)" != "" ]]; then
            echo "ERROR: Duplicate $caller sample names would overwrite outputs:" >&2
            printf '%s\n' "${names[@]}" | sort | uniq -d >&2
            exit 1
        fi
        if [[ "$caller" == manta ]]; then manta_names=("${names[@]}"); MANTA_INPUTS=("${inputs[@]}"); else tiddit_names=("${names[@]}"); TIDDIT_INPUTS=("${inputs[@]}"); fi
    done
    diff="$(comm -3 <(printf '%s\n' "${manta_names[@]}" | sort) <(printf '%s\n' "${tiddit_names[@]}" | sort))"
    [[ -z "$diff" ]] || { echo "ERROR: Manta and TIDDIT sample-name sets differ:" >&2; printf '%s\n' "$diff" >&2; exit 1; }
    mapfile -t CURRENT_SAMPLE_IDS < <(printf '%s\n' "${manta_names[@]}" | sort)
}

prepare_working_vcf() {
    local source="$1" sample_id="$2" caller="$3" working="$4" current tmp
    if usable_vcf "$working" "$source" && [[ "$(bcftools query -l "$working")" == "$sample_id" ]]; then
        reuse "$working"
        return
    fi
    current="$(bcftools query -l "$source")"
    [[ "$(printf '%s\n' "$current" | sed '/^$/d' | wc -l)" -eq 1 ]] || {
        printf 'ERROR: Expected one sample in %s; found:\n%s\n' "$source" "$current" >&2
        exit 1
    }
    rebuild "working copy $caller/$sample_id"
    [[ "$DRY_RUN" == true ]] && return
    tmp="${working}.tmp.$$"
    rm -f "$tmp"
    if [[ "$current" == "$sample_id" ]]; then
        cp -- "$source" "$tmp"
    else
        bcftools reheader -s <(printf '%s\n' "$sample_id") "$source" -o "$tmp" \
            > "$OUT_DIR/logs/${sample_id}.${caller}.reheader.log" 2>&1
    fi
    [[ -s "$tmp" && "$(bcftools query -l "$tmp")" == "$sample_id" ]] && valid_vcf "$tmp" || {
        rm -f "$tmp"
        echo "ERROR: Working-copy validation failed for $source" >&2
        exit 1
    }
    mv -f "$tmp" "$working"
}

correct_vcfs() {
    local caller="$1" vcf working sample_id clean corrected tmp clean_tmp corrected_tmp clean_changed correct_log validate_log rc
    local -a vcfs
    if [[ "$caller" == manta ]]; then vcfs=("${MANTA_INPUTS[@]}"); else vcfs=("${TIDDIT_INPUTS[@]}"); fi
    echo "Found ${#vcfs[@]} $caller VCFs"

    for vcf in "${vcfs[@]}"; do
        sample_id="$(sample_id_from_path "$vcf")"
        clean="$OUT_DIR/cleaned/$caller/${sample_id}.${caller}.clean.vcf.gz"
        corrected="$OUT_DIR/corrected/$caller/${sample_id}.${caller}.corrected.svcf"
        tmp="$OUT_DIR/tmp_vcf/$caller/${sample_id}.${caller}.tmp.vcf"
        clean_tmp="${clean%.vcf.gz}.tmp.$$.vcf.gz"
        corrected_tmp="${corrected%.svcf}.tmp.$$.svcf"
        correct_log="$OUT_DIR/logs/${sample_id}.${caller}.correct.log"
        validate_log="$OUT_DIR/logs/${sample_id}.${caller}.correct.validate.log"
        clean_changed=false

        working="$OUT_DIR/working/$caller/$(basename "$vcf")"
        prepare_working_vcf "$vcf" "$sample_id" "$caller" "$working"

        if usable_vcf "$clean" "$vcf" "$working"; then
            reuse "$clean"
        else
            INPUTS_CHANGED=true
            clean_changed=true
            [[ -e "$clean" ]] && invalid "$clean"
            rebuild "$clean"
            if [[ "$DRY_RUN" == false ]]; then
                echo "Cleaning $caller VCF for $sample_id"
                run_to "$clean" "$clean_tmp" valid_vcf "$OUT_DIR/logs/${sample_id}.${caller}.clean.log" \
                    "Cleaning failed for $sample_id" "Cleaning failed for $sample_id" \
                    octopusv clean "$working" "$clean_tmp"
            fi
        fi

        if [[ "$PARAMETERS_CHANGED" == false && "$clean_changed" == false ]] && usable_svcf "$corrected" "$clean"; then
            reuse "$corrected"
        else
            INPUTS_CHANGED=true
            [[ -e "$corrected" ]] && invalid "$corrected"
            rebuild "$corrected"
            CORRECTED_CHANGED["$caller/$sample_id"]=true
            if [[ "$DRY_RUN" == false ]]; then
                rm -f "$corrected_tmp" "$tmp"
                echo "Correcting $caller VCF for $sample_id"
                if ! gzip -cd "$clean" > "$tmp"; then
                    rm -f "$tmp" "$corrected_tmp"
                    echo "ERROR: Could not decompress cleaned $caller VCF for $sample_id: $clean" >&2
                    exit 1
                fi
                if octopusv correct -i "$tmp" -o "$corrected_tmp" \
                    --min-svlen "$MIN_SVLEN" --max-svlen "$MAX_SVLEN" --filter-pass \
                    > "$correct_log" 2>&1; then
                    :
                else
                    rc=$?
                    rm -f "$tmp" "$corrected_tmp"
                    echo "ERROR: OctopuSV correction command failed for $sample_id ($caller; exit code $rc)" >&2
                    tail -n 50 "$correct_log" >&2
                    exit 1
                fi
                rm -f "$tmp"
                if ! valid_svcf "$corrected_tmp" "$validate_log"; then
                    rm -f "$corrected_tmp"
                    echo "ERROR: Correction completed, but its SVCF failed validation for $sample_id ($caller)" >&2
                    tail -n 50 "$validate_log" >&2
                    exit 1
                fi
                mv -f "$corrected_tmp" "$corrected"
            fi
        fi
    done
}

cohort_membership_matches() {
    local manifest="$1"
    [[ -s "$manifest" ]] && cmp -s "$manifest" <(printf '%s\n' "${CURRENT_SAMPLE_IDS[@]}")
}

merge_sample_cohort() {
    local label="$1" input_dir="$2" suffix="$3" sample_id input
    local cohort_svcf="$OUT_DIR/merged/${label}.svcf" tmp log names manifest available=true
    local -a files=()
    tmp="${cohort_svcf}.tmp.$$"
    log="$OUT_DIR/logs/${label}.sample_merge.log"
    manifest="${cohort_svcf}.samples.txt"
    if [[ "${COHORT_BLOCKED[$label]:-false}" == true ]]; then
        blocked "$cohort_svcf has blocked per-sample inputs"
        return
    fi
    for sample_id in "${CURRENT_SAMPLE_IDS[@]}"; do
        input="$input_dir/${sample_id}${suffix}"
        files+=("$input")
        [[ -s "$input" ]] || available=false
    done
    names="$(printf '%s\n' "${CURRENT_SAMPLE_IDS[@]}" | paste -sd, -)"
    cohort_current() {
        [[ "$PARAMETERS_CHANGED" == false && "$INPUTS_CHANGED" == false && "$available" == true ]] \
            && cohort_membership_matches "$manifest" && usable_svcf "$cohort_svcf" "${files[@]}" "$manifest"
    }
    if [[ "$SKIP_MERGE" == true ]]; then
        if cohort_current; then
            reuse "$cohort_svcf (--skip-merge)"
            return
        fi
        invalid "$cohort_svcf (stale, invalid, missing, or current sample membership unverified)"
        blocked "$cohort_svcf requires rebuilding but --skip-merge is set"
        COHORT_BLOCKED["$label"]=true
        return
    fi
    if [[ "$FORCE_MERGE" == false ]] && cohort_current; then
        reuse "$cohort_svcf"
        return
    fi
    [[ -e "$cohort_svcf" ]] && invalid "$cohort_svcf"
    rebuild "$cohort_svcf"
    COHORT_CHANGED["$label"]=true
    [[ "$DRY_RUN" == true ]] && return
    [[ "$available" == true ]] || { echo "ERROR: Missing current inputs for $label" >&2; exit 1; }
    rm -f "$tmp"
    printf '%s\n' "${CURRENT_SAMPLE_IDS[@]}" > "${manifest}.tmp.$$"
    octopusv merge -i "${files[@]}" --mode sample --sample-names "$names" --union -o "$tmp" > "$log" 2>&1 || {
        rm -f "$tmp"; echo "ERROR: Sample merge failed for $label" >&2; exit 1;
    }
    valid_svcf "$tmp" || { rm -f "$tmp"; echo "ERROR: New cohort failed validation for $label" >&2; exit 1; }
    # Publish membership first: if interrupted, the older cohort stays stale by time.
    mv -f "${manifest}.tmp.$$" "$manifest"
    mv -f "$tmp" "$cohort_svcf"
}

ensure_caller_merge() {
    local operation="$1" sample_id="$2" manta="$3" tiddit="$4" output="$5" tmp
    if [[ "$FORCE_MERGE" == false && "$PARAMETERS_CHANGED" == false
            && "${CORRECTED_CHANGED[manta/$sample_id]:-false}" == false
            && "${CORRECTED_CHANGED[tiddit/$sample_id]:-false}" == false ]] && usable_svcf "$output" "$manta" "$tiddit"; then
        reuse "$output"
        return 0
    fi
    [[ -e "$output" ]] && invalid "$output (stale or invalid caller merge)"
    if [[ "$SKIP_MERGE" == true ]]; then
        blocked "$output is stale/missing/invalid and --skip-merge is set"
        return 1
    fi
    rebuild "$output"
    [[ "$DRY_RUN" == true ]] && return 0
    tmp="${output}.tmp.$$"
    run_to "$output" "$tmp" valid_svcf "$OUT_DIR/logs/${sample_id}.manta_tiddit.${operation}.caller_merge.log" \
        "Caller merge failed for $sample_id ($operation)" "Invalid caller merge for $sample_id" \
        octopusv merge -i "$manta" "$tiddit" --mode caller --caller-names Manta,TIDDIT "--$operation" -o "$tmp"
}

ensure_sample_vcf() {
    local input="$1" output="$2" changed="$3" label="$4" tmp
    if [[ "$FORCE_MERGE" == false && "$PARAMETERS_CHANGED" == false && "$changed" == false ]] && usable_vcf "$output" "$input"; then
        reuse "$output"
        return
    fi
    [[ -e "$output" ]] && invalid "$output"
    rebuild "$output"
    [[ "$DRY_RUN" == true ]] && return
    tmp="${output}.tmp.$$"
    run_to "$output" "$tmp" valid_vcf "$OUT_DIR/logs/${label}.svcf2vcf.log" \
        "Caller conversion failed for $label" "Invalid converted VCF for $label" \
        octopusv svcf2vcf -i "$input" -o "$tmp"
}

ensure_consensus() {
    local input="$1" output="$2" changed="$3" label="$4" tmp
    if [[ "$FORCE_MERGE" == false && "$PARAMETERS_CHANGED" == false && "$changed" == false ]] && usable_svcf "$output" "$input"; then
        reuse "$output"
        return
    fi
    INPUTS_CHANGED=true
    [[ -e "$output" ]] && invalid "$output"
    rebuild "$output"
    [[ "$DRY_RUN" == true ]] && return
    tmp="${output}.tmp.$$"
    run_to "$output" "$tmp" valid_svcf "$OUT_DIR/logs/${label}.consensus_correct.log" \
        "Consensus correction failed for $label" "Invalid consensus for $label" \
        octopusv correct -i "$input" -o "$tmp" --min-svlen "$MIN_SVLEN" --max-svlen "$MAX_SVLEN" --filter-pass
}

merge_callers_per_sample() {
    local operation="$1" base sample_id manta tiddit caller_svcf sample_vcf consensus before caller_changed vcf_changed
    base="$OUT_DIR/per_sample/$operation"
    for sample_id in "${CURRENT_SAMPLE_IDS[@]}"; do
        manta="$OUT_DIR/corrected/manta/${sample_id}.manta.corrected.svcf"
        tiddit="$OUT_DIR/corrected/tiddit/${sample_id}.tiddit.corrected.svcf"
        caller_svcf="$base/caller/${sample_id}.${operation}.caller.svcf"
        sample_vcf="$base/vcf/${sample_id}.${operation}.vcf"
        consensus="$base/consensus/${sample_id}.${operation}.consensus.svcf"
        if [[ "$DRY_RUN" == false && (! -s "$manta" || ! -s "$tiddit") ]]; then
            echo "ERROR: Missing current corrected inputs for $sample_id" >&2; exit 1
        fi
        before="$REBUILD"
        if ! ensure_caller_merge "$operation" "$sample_id" "$manta" "$tiddit" "$caller_svcf"; then
            COHORT_BLOCKED["manta_tiddit.${operation}.cohort"]=true
            continue
        fi
        caller_changed=false
        (( REBUILD == before )) || caller_changed=true
        before="$REBUILD"
        ensure_sample_vcf "$caller_svcf" "$sample_vcf" "$caller_changed" "${sample_id}.manta_tiddit.${operation}"
        vcf_changed=false
        (( REBUILD == before )) || vcf_changed=true
        ensure_consensus "$sample_vcf" "$consensus" "$vcf_changed" "${sample_id}.manta_tiddit.${operation}"
    done
}

report_and_convert() {
    local label svcf vcf stats circos stats_tmp circos_tmp vcf_tmp
    label="$1"
    svcf="$OUT_DIR/merged/${label}.svcf"
    vcf="$OUT_DIR/merged/${label}.vcf"
    stats="$OUT_DIR/stats/${label}.stats.txt"
    circos="$OUT_DIR/circos/${label}.circos.png"
    stats_tmp="$OUT_DIR/stats/${label}.stats.tmp.$$.txt"
    circos_tmp="$OUT_DIR/circos/${label}.circos.tmp.$$.png"
    vcf_tmp="$OUT_DIR/merged/${label}.tmp.$$.vcf"

    if [[ "${COHORT_BLOCKED[$label]:-false}" == true ]]; then
        blocked "reports for $label (cohort is stale or blocked)"
        return
    fi
    if ! valid_svcf "$svcf"; then
        if [[ "$DRY_RUN" == true && "${COHORT_CHANGED[$label]:-false}" == true ]]; then
            rebuild "$label reports and VCF (after planned cohort rebuild)"
            return
        fi
        blocked "reports for $label (cohort unavailable)"; return
    fi

    if [[ "$FORCE_MERGE" == false && "$PARAMETERS_CHANGED" == false && "${COHORT_CHANGED[$label]:-false}" == false ]] \
        && usable_vcf "$vcf" "$svcf" && [[ -s "$stats" ]] && fresh "$stats" "$svcf" \
        && valid_png "$circos" && fresh "$circos" "$svcf" && valid_plots "$OUT_DIR/plots/$label" "$stats"; then
        reuse "$label reports and VCF"
        return
    fi
    [[ -e "$vcf" ]] && invalid "$label reports or VCF"
    rebuild "$label reports and VCF"
    [[ "$DRY_RUN" == true ]] && return

    echo "Generating reports for $label"
    run_to "$stats" "$stats_tmp" nonempty "$OUT_DIR/logs/${label}.stat.log" \
        "Statistics failed for $label" "Statistics failed for $label" \
        octopusv stat -i "$svcf" -o "$stats_tmp" --report
    publish_side_outputs "${stats_tmp%.txt}" "${stats%.txt}"
    octopusv plot "$stats" -o "$OUT_DIR/plots/$label" > "$OUT_DIR/logs/${label}.plot.log" 2>&1
    valid_plots "$OUT_DIR/plots/$label" "$stats" || { echo "ERROR: Plot generation failed for $label" >&2; exit 1; }
    run_to "$circos" "$circos_tmp" valid_png "$OUT_DIR/logs/${label}.circos.log" \
        "Circos plot failed for $label" "Circos plot failed for $label" \
        octopusv plot-circos -i "$svcf" -o "$circos_tmp"
    publish_side_outputs "${circos_tmp%.png}" "${circos%.png}"
    run_to "$vcf" "$vcf_tmp" valid_vcf "$OUT_DIR/logs/${label}.svcf2vcf.log" \
        "VCF conversion failed for $label" "VCF conversion failed for $label" \
        octopusv svcf2vcf -i "$svcf" -o "$vcf_tmp"

    if [[ "$label" =~ ^manta_tiddit\.(union|intersect)\.cohort$ ]]; then
        local operation expected observed unique
        operation="${BASH_REMATCH[1]}"
        expected="${#CURRENT_SAMPLE_IDS[@]}"
        observed="$(bcftools query -l "$vcf" | wc -l)"
        unique="$(bcftools query -l "$vcf" | sort -u | wc -l)"
        [[ "$observed" -eq "$expected" && "$unique" -eq "$expected" ]] || {
            echo "ERROR: $label sample columns incomplete/duplicated: expected=$expected observed=$observed unique=$unique" >&2
            exit 1
        }
        echo "Confirmed $observed unique sample columns in ${label}.vcf"
    fi
}

validate_input_sample_sets

for caller in manta tiddit; do
    INPUTS_CHANGED=false
    correct_vcfs "$caller"
    merge_sample_cohort "$caller.cohort" "$OUT_DIR/corrected/$caller" ".${caller}.corrected.svcf"
done

for operation in union intersect; do
    INPUTS_CHANGED=false
    merge_callers_per_sample "$operation"
    merge_sample_cohort "manta_tiddit.${operation}.cohort" "$OUT_DIR/per_sample/$operation/consensus" \
        ".${operation}.consensus.svcf"
done

for label in manta.cohort tiddit.cohort manta_tiddit.union.cohort manta_tiddit.intersect.cohort; do
    report_and_convert "$label"
done

printf 'Resume summary: reused=%d rebuild=%d invalid_or_stale=%d blocked=%d mode=%s\n' \
    "$REUSED" "$REBUILD" "$INVALID" "$BLOCKED" "$([[ "$DRY_RUN" == true ]] && echo dry-run || echo execute)"
(( BLOCKED == 0 )) || { echo "ERROR: One or more required stages are blocked" >&2; exit 3; }
if [[ "$DRY_RUN" == false ]]; then
    param_tmp="${PARAM_FILE}.tmp.$$"
    printf '%s\n' "$PARAM_VALUE" > "$param_tmp"
    mv -f "$param_tmp" "$PARAM_FILE"
fi
printf 'Done. Outputs are in %s\n' "$OUT_DIR"

# OctopuSV citation:
# Guo Q, Li Y, Wang T-Y, Ramakrishnan A, Yang R. OctopuSV and TentacleSV:
# a one-stop toolkit for multi-sample, cross-platform structural variant
# comparison and analysis. Bioinformatics. 2025; doi:10.1093/bioinformatics/btaf599.
