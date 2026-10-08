#!/bin/bash

# Path to your CSV file
csv_file="transcriptomic_batches.csv"

# Base directory where your samples currently reside
base_dir="/path/to/samples"

# Destination base directory where artificial batch folders will be created
dest_base="/path/to/batch/dir/"

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
