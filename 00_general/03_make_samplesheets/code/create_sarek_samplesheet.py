import os
import csv
import argparse
import math

def collect_reads(directory):
    cram_files = []
    crai_files = []

    # Get the present working directory
    pwd = os.path.abspath(os.getcwd())

    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory):
        print(f"Checking directory: {root}")  # Debug: print current directory
        # Collect CRAM and CRAI files separately
        for file in files:
            if file.endswith(".cram"):
                full_path = os.path.join(root, file)
                # Make the path relative to the present working directory
                relative_path = os.path.relpath(full_path, pwd)
                cram_files.append(os.path.join(pwd, relative_path))
            elif file.endswith(".crai"):
                full_path = os.path.join(root, file)
                # Make the path relative to the present working directory
                relative_path = os.path.relpath(full_path, pwd)
                crai_files.append(os.path.join(pwd, relative_path))

    return cram_files, crai_files

def extract_patient_id(filename):
    base = os.path.basename(filename)
    return base.split("-")[0] + "-" + base.split("-")[1]

def extract_sample_id(filename):
    base = os.path.basename(filename)
    return base.split("-G")[0]

def write_samplesheet(cram_files, crai_files, output_file_base):
    total_files = len(cram_files)
    num_splits = 14  # We want to split into 7 parts (347/7)
    files_per_split = math.ceil(total_files / num_splits)  # Divide into approximately equal parts

    for i in range(num_splits):
        split_output_file = f"{output_file_base}_part_{i+1}.csv"
        with open(split_output_file, "w", newline="") as csvfile:
            fieldnames = ["patient", "sample", "cram", "crai"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            lane_counter = 1
            # Get the range of files for this part
            start_idx = i * files_per_split
            end_idx = min(start_idx + files_per_split, total_files)

            for cram in cram_files[start_idx:end_idx]:
                patient_id = extract_patient_id(cram)
                sample_id = extract_sample_id(cram)
                crai = next((c for c in crai_files if extract_sample_id(c) == sample_id), None)
                full_cram = cram
                full_crai = crai if crai else "Not found"
                writer.writerow({"patient": patient_id, "sample": sample_id, "cram": full_cram, "crai": full_crai})
                #lane_counter += 1

        print(f"Created: {split_output_file}")

def main():
    parser = argparse.ArgumentParser(description="Create a samplesheet CSV from CRAM and CRAI files in subdirectories.")
    parser.add_argument("directory", help="The directory containing the CRAM and CRAI files")
    parser.add_argument("output_file_base", help="The base name for the output CSV files")
    args = parser.parse_args()

    directory = args.directory
    output_file_base = args.output_file_base

    cram_files, crai_files = collect_reads(directory)

    if not cram_files:
        print("No CRAM files found in the directory.")
        return

    write_samplesheet(cram_files, crai_files, output_file_base)
    print(f"Samplesheet created successfully.")

if __name__ == "__main__":
    main()


