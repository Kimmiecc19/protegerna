#!/usr/bin/env bash
set -euo pipefail

# Retain the unfiltered entry point while using the shared sequential runner.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/02_run_annotsv_filtered.sh" --mode unfiltered "$@"
