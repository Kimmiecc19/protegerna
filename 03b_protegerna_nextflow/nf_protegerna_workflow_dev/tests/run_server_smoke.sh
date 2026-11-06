#!/usr/bin/env bash
set -euo pipefail
image=${1:?Usage: bash tests/run_server_smoke.sh /absolute/path/protegerna.sif}
image=$(realpath "$image")
shift
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
apptainer test "$image"
nextflow run . -profile test \
    --proteogenomic_container "$image" \
    --outdir results/server_smoke -work-dir work/server_smoke "$@"
count=$(awk '/^>/{n++} END{print n+0}' results/server_smoke/merge/proteogenomic_database.fasta)
test "$count" = 4
test "$(awk '/^>/{n++} END{print n+0}' results/server_smoke/fusion/fusion.primary.fasta)" = 2
test "$(awk '/^>/{n++} END{print n+0}' results/server_smoke/rmats/rmats.primary.fasta)" = 1
test "$(awk '/^>/{n++} END{print n+0}' results/server_smoke/suppa/suppa.primary.fasta)" = 1
traces=(results/server_smoke/pipeline_info/execution_trace_*.tsv)
test "$(awk 'NR>1{n++} END{print n+0}' "${traces[-1]}")" = 9
test -s results/server_smoke/pipeline_info/software_versions.yml
echo 'PASS: nine Nextflow processes, all producers, strict QC, four final sequences'
