#!/usr/bin/env bash
# 01_build_revised_database.sh
#
# Objective Three, Chapter 5 ("Revised database (comparison release)", Figure 5.4):
# build the REVISED database (v7) with the corrected code in proteogenomic_db/ and the
# configuration config/workflow.publication.frozen.toml.
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
#   --config FILE       workflow TOML (default: config/workflow.publication.frozen.toml)
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
CONFIG="$HERE/config/workflow.publication.frozen.toml"
PROJECT_DIR="$(dirname "$HERE")"
MODE=run

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir) PROJECT_DIR="${2:?--project-dir needs a folder}"; shift 2 ;;
        --config) CONFIG="${2:?--config needs a file}"; shift 2 ;;
        --dry-run) MODE=dry-run; shift ;;
        --explain) MODE=explain; shift ;;
        -h|--help)
            cat <<'HELP'
Usage: bash 01_build_revised_database.sh [--dry-run | --explain] [--project-dir DIR] [--config FILE]

  --project-dir DIR  folder the TOML paths are relative to (default: 03_proteogenomic_database/)
  --config FILE      workflow TOML (default: config/workflow.publication.frozen.toml)
  --dry-run          print every resolved command without running it
  --explain          print every resolved setting and where it came from
HELP
            exit 0
            ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
done

[[ -f "$CONFIG" ]] || { echo "ERROR: configuration not found: $CONFIG" >&2; exit 1; }
cd "$PROJECT_DIR"
export PYTHONPATH="$HERE/proteogenomic_db${PYTHONPATH:+:$PYTHONPATH}"

case "$MODE" in
    dry-run) exec python3 "$HERE/proteogenomic_db/proteogenomic_workflow.py" "$CONFIG" --dry-run ;;
    explain) exec python3 "$HERE/proteogenomic_db/proteogenomic_workflow.py" explain "$CONFIG" ;;
    run) exec python3 "$HERE/proteogenomic_db/proteogenomic_workflow.py" "$CONFIG" ;;
esac
