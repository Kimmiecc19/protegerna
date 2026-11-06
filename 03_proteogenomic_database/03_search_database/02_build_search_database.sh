#!/usr/bin/env bash
# 02_build_search_database.sh
#
# Objective Three, Chapter 5: build the SEARCH database (v5).
# Runs the proteogenomic database workflow with the frozen configuration
# config/workflow.publication.v5.toml. The workflow stages, in order, are:
#   1 validate GENCODE translation   (validate_gencode_translation.py)  -> Table 5.1
#   2 fusion / rMATS / SUPPA reconstruction (fusiontoprotein.py, rmatstoprotein.py, suppatoprotein.py)
#   3-4 merge with UniProt + cRAP, DIA-suitability filter, deduplication (merge_proteogenomic_database.py)
#   5 final FASTA QC                  (proteogenomic_fasta_qc.py)
#   6 release report                  (release_report.py)            -> Table 5.2
# The merge cannot run unless stage 1 passed.
#
# Every peptide-level result in Chapters 5 and 6 comes from the database this script builds.
#
# Usage:
#   bash 02_build_search_database.sh [--dry-run | --explain] [--project-dir DIR] [--config FILE] [--stage NAME ...]
#
#   --project-dir DIR   folder that contains data/ and results/; the paths in the TOML are relative to it
#                       (default: current directory)
#   --config FILE       workflow TOML (default: config/workflow.publication.v5.toml next to this script)
#   --dry-run           print every resolved command without running it
#   --explain           print every resolved setting and where it came from
#   --stage NAME        run only this workflow stage (repeatable); passed through to the workflow
#
# Requirements: Python 3.11 with the packages in proteogenomic_db/environment.yml. The script always runs
# the bundled v5 code in proteogenomic_db/, never an installed `proteogenomic-workflow` command.
# Before a first run, edit the absolute rnasplice / rnafusion input paths in the TOML.

set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HERE/config/workflow.publication.v5.toml"
PROJECT_DIR="$PWD"
MODE="run"
EXTRA=()

# Expected checksum of the search database used in the dissertation (Chapter 6, Reproducibility).
EXPECTED_MD5="3f8ed11769fcd5a62587b528cd2eb52a"
EXPECTED_ENTRIES=80657

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir) PROJECT_DIR="${2:?--project-dir needs a folder}"; shift 2 ;;
        --config)      CONFIG="${2:?--config needs a file}"; shift 2 ;;
        --dry-run)     MODE="dry-run"; shift ;;
        --explain)     MODE="explain"; shift ;;
        --stage)       EXTRA+=(--stage "${2:?--stage needs a name}"); shift 2 ;;
        -h|--help)     usage; exit 0 ;;
        *) echo "ERROR: unknown option $1" >&2; usage >&2; exit 2 ;;
    esac
done

CONFIG="$(cd -- "$(dirname -- "$CONFIG")" && pwd)/$(basename -- "$CONFIG")"
[[ -f "$CONFIG" ]] || { echo "ERROR: configuration not found: $CONFIG" >&2; exit 1; }
cd "$PROJECT_DIR"

# Always run the bundled v5 module, so an installed v7 command cannot be picked up by mistake.
WORKFLOW=(python3 "$HERE/proteogenomic_db/proteogenomic_workflow.py")
export PYTHONPATH="$HERE/proteogenomic_db${PYTHONPATH:+:$PYTHONPATH}"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || {
    echo "ERROR: the workflow needs Python >= 3.11 (found $(python3 --version 2>&1))." \
         "Activate the environment from proteogenomic_db/environment.yml first." >&2
    exit 1
}

# Read output_dir from the [workflow] section of the TOML.
OUT_DIR="$(awk -F= '/^\[/{sec=$0} sec=="[workflow]" && $1 ~ /^[ 	]*output_dir[ 	]*$/ {gsub(/^[ 	]*"|"[ 	]*$/, "", $2); print $2; exit}' "$CONFIG")"
OUT_DIR="${OUT_DIR:-results}"

echo "Configuration : $CONFIG"
echo "Project folder: $PWD"
echo "Output folder : $OUT_DIR"
echo "Workflow      : ${WORKFLOW[*]}"

case "$MODE" in
    dry-run) "${WORKFLOW[@]}" "$CONFIG" --dry-run "${EXTRA[@]}"; exit 0 ;;
    explain) "${WORKFLOW[@]}" explain "$CONFIG"; exit 0 ;;
esac

mkdir -p "$OUT_DIR"
LOG="$OUT_DIR/build_$(date +%Y%m%d_%H%M%S).log"
{
    echo "started  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "config   $CONFIG"
    echo "sha256   $(sha256sum "$CONFIG" | cut -d' ' -f1)"
    echo "python   $(python3 --version 2>&1)"
} > "$LOG"

"${WORKFLOW[@]}" "$CONFIG" "${EXTRA[@]}" 2>&1 | tee -a "$LOG"

# Check the final FASTA against the build reported in the dissertation (only when the merge ran).
FASTA="$OUT_DIR/proteogenomic_database.fasta"
if [[ -f "$FASTA" && ${#EXTRA[@]} -eq 0 ]]; then
    MD5="$(md5sum "$FASTA" | cut -d' ' -f1)"
    N="$(grep -c '^>' "$FASTA")"
    {
        echo "fasta    $FASTA"
        echo "entries  $N (expected $EXPECTED_ENTRIES)"
        echo "md5      $MD5 (expected $EXPECTED_MD5)"
        echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } | tee -a "$LOG"
    if [[ "$MD5" != "$EXPECTED_MD5" ]]; then
        echo "WARNING: the database differs from the dissertation search database." \
             "Check the inputs, configuration and package version (0.1.0)." | tee -a "$LOG" >&2
    fi
fi
