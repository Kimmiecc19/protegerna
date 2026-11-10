#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

# ---- Settings (override with environment variables) --------------------------
# Batch assignments written by 03_proteogenomic_database/01_sample_batches/01a_make_stratified_batches.py
csv_file="${CSV_FILE:-$REPO_DIR/03_proteogenomic_database/01_sample_batches/01_results_stratified_batches/batch_files/transcriptomic_batches.csv}"
# Folder where the downloaded RNA-seq FASTQ sample folders currently reside (controlled access, external)
base_dir="${FASTQ_DIR:-/path/to/transcriptomics/fastq/rna_samples}"
# Destination folder where the batch_N folders will be created
dest_base="${BATCH_DIR:-$base_dir/rna_batches}"
# -------------------------------------------------------------------------------

# Read the CSV file line by line, skipping the header
tail -n +2 "$csv_file" | while IFS=',' read -r directory subdirectory batch
do
  src="$base_dir/$directory/$subdirectory"
  dest="$dest_base/batch_$batch"

  # Create destination directory if it doesn't exist
  mkdir -p "$dest"

  # Move the subdirectory to the batch directory
  if [ -d "$src" ]; then
    echo "Moving $src to $dest"
    mv "$src" "$dest/"
  else
    echo "Warning: $src does not exist."
  fi
done
