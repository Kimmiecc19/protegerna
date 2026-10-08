#!/usr/bin/env python3
"""
This script creates a samplesheet CSV file from paired FASTQ files located in subdirectories of a given directory.
It identifies paired reads based on naming conventions (_1/_2 or _r1/_r2) and writes the sample name, file paths, and strandedness to the CSV.
The output can be used for nf-core/rnaseq and nf-core/rnafusion.
""" 

import os
import csv
import argparse
import re

def collect_paired_reads(directory):
    paired_reads = []

    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory):
        # Filter files for read1 and read2, accounting for both _1 and _r1 patterns
        read1_files = sorted([os.path.join(root, file) for file in files if re.search(r'(_1|_r1)\.fastq\.gz$', file, re.IGNORECASE)])
        read2_files = sorted([os.path.join(root, file) for file in files if re.search(r'(_2|_r2)\.fastq\.gz$', file, re.IGNORECASE)])

        # Ensure that only paired reads are considered
        for read1 in read1_files:
            # Create the corresponding read2 filename
            if "_1.fastq.gz" in read1:
                read2 = read1.replace("_1.fastq.gz", "_2.fastq.gz")
            else:  # For _r1 files
                read2 = read1.replace("_r1.fastq.gz", "_r2.fastq.gz")

            if read2 in read2_files:
                # Append the full paths to the paired reads
                paired_reads.append((read1, read2))
            else:
                print(f"Could not find a pair for: {read1}")

    return paired_reads

def extract_basename(filename):
    return os.path.basename(filename).split("_")[0]

def write_samplesheet(paired_reads, output_file):
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["sample", "fastq_1", "fastq_2", "strandedness"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for read1, read2 in paired_reads:
            base_name = extract_basename(read1)
            writer.writerow({"sample": base_name, "fastq_1": read1, "fastq_2": read2, "strandedness": "forward"})
            #writer.writerow({"sample": base_name, "fastq_1": read1, "fastq_2": read2, "strandedness": "auto"})

def main():
    parser = argparse.ArgumentParser(description="Create a samplesheet CSV from paired FASTQ files in subdirectories.")
    parser.add_argument("directory", help="The directory containing the FASTQ files and subdirectories")
    parser.add_argument("output_file", help="The output CSV file")
    args = parser.parse_args()

    directory = args.directory
    output_file = args.output_file
    
    # Collect the paired reads
    paired_reads = collect_paired_reads(directory)

    if not paired_reads:
        print("No paired FASTQ files found in the directory.")
        return

    # Write the samplesheet
    write_samplesheet(paired_reads, output_file)
    print(f"Samplesheet created successfully: {output_file}")

if __name__ == "__main__":
    main()
