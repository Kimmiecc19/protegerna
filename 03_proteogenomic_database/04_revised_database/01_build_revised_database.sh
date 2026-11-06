#!/usr/bin/env bash
# 01_build_revised_database.sh
#
# Objective Three, Chapter 5 ("Revised database (comparison release)", Figure 5.4):
# build the REVISED database (v7) with the corrected code in proteogenomic_db/ and the
# configuration config/workflow.publication.v7.filtered.toml.
#
# The revised database was built only to show how the corrected filters change database
# composition. It was NOT searched, so no peptide result in the dissertation comes from it.
# Genome, GENCODE v46 annotation, translation check, digestion rules, fusion parameters and
# merge rules are the same as the search database (03_search_database). The corrected code:
#   - makes fusion processing independent of the order in which parallel workers finish;
#   - excludes (rather than flags) rMATS products that fail a database rule;
#   - requires a reference-unique peptide for rMATS products;
#   - checks peptide uniqueness against UniProt canonical AND isoform sequences;
#   - reads SUPPA events once instead of six times.
#
# Usage:
#   bash 01_build_revised_database.sh [--dry-run | --explain] [--project-dir DIR] [--config FILE]
#
#   --project-dir DIR   folder that contains data/ and results/ (default: current directory)
#   --config FILE       workflow TOML (default: config/workflow.publication.v7.filtered.toml)
#   --dry-run           print every resolved command without running it
#   --explain           print every resolved setting and where it came from
#
# Afterwards, compare the two builds with 02_compare_search_and_revised_databases.py.
#
# Requirements: the package in proteogenomic_db/ (the v7 code) installed in its own environment,
# or Python 3.11 with the packages in proteogenomic_db/environment.yml. Do not install the v5 and v7
# packages in the same environment: both provide the command `proteogenomic-workflow`.

set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HERE/config/workflow.publication.v7.filtered.toml"
PROJECT_DIR="$PWD"
MODE="run"

# Revised database reported in Chapter 5 (30,031 unique sequences).
EXPECTED_MD5="e6b4632bafd6a6a026fc4c18fff06ca6"
EXPECTED_ENTRIES=30031

usage() { sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir) PROJECT_DIR="${2:?--project-dir needs a folder}"; shift 2 ;;
        --config)      CONFIG="${2:?--config needs a file}"; shift 2 ;;
        --dry-run)     MODE="dry-run"; shift ;;
        --explain)     MODE="explain"; shift ;;
        -h|--help)     usage; exit 0 ;;
        *) echo "ERROR: unknown option $1" >&2; usage >&2; exit 2 ;;
    esac
done

CONFIG="$(cd -- "$(dirname -- "$CONFIG")" && pwd)/$(basename -- "$CONFIG")"
[[ -f "$CONFIG" ]] || { echo "ERROR: configuration not found: $CONFIG" >&2; exit 1; }
cd "$PROJECT_DIR"

# Always run the bundled v7 module, so an installed v5 command cannot be picked up by mistake.
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

case "$MODE" in
    dry-run) "${WORKFLOW[@]}" "$CONFIG" --dry-run; exit 0 ;;
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

"${WORKFLOW[@]}" "$CONFIG" 2>&1 | tee -a "$LOG"

FASTA="$OUT_DIR/proteogenomic_database.fasta"
if [[ -f "$FASTA" ]]; then
    MD5="$(md5sum "$FASTA" | cut -d' ' -f1)"
    N="$(grep -c '^>' "$FASTA")"
    {
        echo "fasta    $FASTA"
        echo "entries  $N (expected $EXPECTED_ENTRIES)"
        echo "md5      $MD5 (expected $EXPECTED_MD5)"
        echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } | tee -a "$LOG"
    [[ "$MD5" == "$EXPECTED_MD5" ]] || echo "WARNING: the revised database differs from the build reported in Chapter 5." | tee -a "$LOG" >&2
fi
