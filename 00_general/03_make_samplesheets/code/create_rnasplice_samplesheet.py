import os
import csv
import argparse
import re

def collect_paired_reads(directory):
    paired_reads = []

    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory):
        # Find read1 and read2 files
        read1_files = sorted([os.path.join(root, f) for f in files if re.search(r'(_1|_r1)\.fastq\.gz$', f, re.IGNORECASE)])
        read2_files = sorted([os.path.join(root, f) for f in files if re.search(r'(_2|_r2)\.fastq\.gz$', f, re.IGNORECASE)])

        for read1 in read1_files:
            if "_1.fastq.gz" in read1:
                read2 = read1.replace("_1.fastq.gz", "_2.fastq.gz")
            else:
                read2 = read1.replace("_r1.fastq.gz", "_r2.fastq.gz")

            if read2 in read2_files:
                paired_reads.append((read1, read2))
            else:
                print(f"Could not find a pair for: {read1}")
    return paired_reads

def extract_basename(filepath):
    # Get the immediate parent directory name and replace hyphens with underscores
    parent_dir = os.path.basename(os.path.dirname(filepath))
    return parent_dir.replace('-', '_')

def extract_condition(filepath):
    match = re.search(r'(CASE|CTRL)-', filepath)
    return match.group(1) if match else "UNKNOWN"

def write_samplesheet(paired_reads, output_file):
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["sample", "fastq_1", "fastq_2", "strandedness", "condition"])
        writer.writeheader()

        for read1, read2 in paired_reads:
            base_name = extract_basename(read1)
            condition = extract_condition(read1)
            writer.writerow({
                "sample": base_name,
                "fastq_1": read1,
                "fastq_2": read2,
                "strandedness": "forward",
                "condition": condition
            })

def main():
    parser = argparse.ArgumentParser(description="Create a samplesheet CSV from paired FASTQ files.")
    parser.add_argument("directory", help="Directory with FASTQ files")
    parser.add_argument("output_file", help="Output CSV path")
    args = parser.parse_args()

    paired_reads = collect_paired_reads(args.directory)

    if not paired_reads:
        print("No paired FASTQ files found.")
        return

    write_samplesheet(paired_reads, args.output_file)
    print(f"Samplesheet created: {args.output_file}")

if __name__ == "__main__":
    main()
