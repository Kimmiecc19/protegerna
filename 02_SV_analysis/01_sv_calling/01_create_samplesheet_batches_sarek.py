import argparse
import csv
import math
import os

NUM_SPLITS = 14  # 347 samples split into 14 batch samplesheets


def collect_reads(directory):
    """Return CRAM and CRAI paths found under directory, expressed under the working directory."""
    pwd = os.path.abspath(os.getcwd())
    cram_files, crai_files = [], []
    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(pwd, os.path.relpath(os.path.join(root, file), pwd))
            if file.endswith(".cram"):
                cram_files.append(full_path)
            elif file.endswith(".crai"):
                crai_files.append(full_path)
    return cram_files, crai_files


def extract_patient_id(filename):
    parts = os.path.basename(filename).split("-")
    return parts[0] + "-" + parts[1]


def extract_sample_id(filename):
    return os.path.basename(filename).split("-G")[0]


def write_samplesheet(cram_files, crai_files, output_file_base):
    crai_by_sample = {}
    for crai in crai_files:
        crai_by_sample.setdefault(extract_sample_id(crai), crai)  # first match wins
    files_per_split = math.ceil(len(cram_files) / NUM_SPLITS)

    for i in range(NUM_SPLITS):
        split_output_file = f"{output_file_base}_part_{i+1}.csv"
        with open(split_output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["patient", "sample", "cram", "crai"])
            writer.writeheader()
            for cram in cram_files[i * files_per_split:(i + 1) * files_per_split]:
                sample_id = extract_sample_id(cram)
                writer.writerow({"patient": extract_patient_id(cram), "sample": sample_id, "cram": cram,
                                 "crai": crai_by_sample.get(sample_id, "Not found")})
        print(f"Created: {split_output_file}")


def main():
    parser = argparse.ArgumentParser(description="Create a samplesheet CSV from CRAM and CRAI files in subdirectories.")
    parser.add_argument("directory", help="The directory containing the CRAM and CRAI files")
    parser.add_argument("output_file_base", help="The base name for the output CSV files")
    args = parser.parse_args()

    cram_files, crai_files = collect_reads(args.directory)
    if not cram_files:
        print("No CRAM files found in the directory.")
        return

    write_samplesheet(cram_files, crai_files, args.output_file_base)
    print("Samplesheet created successfully.")


if __name__ == "__main__":
    main()
