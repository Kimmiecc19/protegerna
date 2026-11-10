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
#   --project-dir DIR   folder the paths in the TOML are relative to
#                       (default: 03_proteogenomic_database/, the parent of this script's folder)
#   --config FILE       workflow TOML (default: config/workflow.publication.v5.toml next to this script)
#   --dry-run           print every resolved command without running it
#   --explain           print every resolved setting and where it came from
#   --stage NAME        run only this workflow stage (repeatable); passed through to the workflow
#
# Requirements: Python 3.11 with the packages in proteogenomic_db/environment.yml. The script always runs
# the bundled v5 code in proteogenomic_db/, never an installed `proteogenomic-workflow` command.
# The TOML reads the rnafusion / rnasplice results in 02_event_detection/ and writes to
# 03_search_database/results_pgdb_publication_rerun_v5/. Place the reference files it names under
# 03_proteogenomic_database/data/ (see 01_build_gtf_database.py for the GTF database).

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/config/workflow.publication.v5.toml"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODE=run
STAGES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-dir) PROJECT_DIR="${2:?--project-dir needs a folder}"; shift 2 ;;
        --config) CONFIG="${2:?--config needs a file}"; shift 2 ;;
        --stage) STAGES+=(--stage "${2:?--stage needs a name}"); shift 2 ;;
        --dry-run) MODE=dry-run; shift ;;
        --explain) MODE=explain; shift ;;
        -h|--help)
            echo 'Usage: bash 02_build_search_database.sh [--dry-run | --explain] [--project-dir DIR] [--config FILE] [--stage NAME ...]'
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

CONFIG="$(realpath "$CONFIG")"
cd "$PROJECT_DIR"
export PYTHONPATH="$SCRIPT_DIR/proteogenomic_db${PYTHONPATH:+:$PYTHONPATH}"
WORKFLOW=(python3 "$SCRIPT_DIR/proteogenomic_db/proteogenomic_workflow.py")

if [[ "$MODE" == explain ]]; then
    exec "${WORKFLOW[@]}" explain "$CONFIG"
elif [[ "$MODE" == dry-run ]]; then
    exec "${WORKFLOW[@]}" "$CONFIG" --dry-run "${STAGES[@]}"
else
    exec "${WORKFLOW[@]}" "$CONFIG" "${STAGES[@]}"
fi
