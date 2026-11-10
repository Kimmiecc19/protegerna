#!/usr/bin/env python3

import os
import gzip
import shutil
import time
import urllib.request
import urllib.parse
from datetime import datetime

# ==============================
# Configuration
# ==============================

# Written beside this script, where the reference search (02a) and its params file expect it.
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_results_make_reference_database")

HUMAN_FASTA_GZ = "uniprot_human_reviewed_isoforms.fasta.gz"
HUMAN_FASTA = "uniprot_human_reviewed_isoforms.fasta"

CRAP_FASTA = "crap.fasta"

FINAL_FASTA = "human_reference_deduplicated.fasta"
LOG_FILE = "database_build_log.txt"

CRAP_URL = "ftp://ftp.thegpm.org/fasta/cRAP/crap.fasta"

MAX_RETRIES = 5
BACKOFF_FACTOR = 2
CHUNK_SIZE = 1024 * 1024  # 1 MB


# ==============================
# URL Builder
# ==============================

def build_uniprot_url():
    # https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=fasta&includeIsoform=true&query=%28%28proteome%3AUP000005640%29+AND+reviewed%3Dtrue%29
    base_url = "https://rest.uniprot.org/uniprotkb/stream"
    params = {
        "compressed": "true",
        "format": "fasta",
        "query": "reviewed:true AND organism_id:9606",
        "includeIsoform": "true"
    }
    return base_url + "?" + urllib.parse.urlencode(params)


# ==============================
# Utility Functions
# ==============================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def download_with_retry(url, destination):
    if os.path.exists(destination):
        print(f"{destination} already exists.")
        return

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            print(f"Downloading: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response, open(destination, "wb") as out_file:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out_file.write(chunk)

            print(f"Saved to: {destination}")
            return

        except Exception as e:
            attempt += 1
            wait_time = BACKOFF_FACTOR ** attempt
            print(f"Download failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to download {url} after {MAX_RETRIES} attempts.")


def decompress_gz(gz_path, output_path):
    if os.path.exists(output_path):
        print(f"{output_path} already decompressed.")
        return

    print(f"Decompressing: {gz_path}")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def parse_fasta(filepath):
    sequences = {}
    header = None
    seq_lines = []

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if header:
                    seq = "".join(seq_lines)
                    if seq not in sequences:
                        sequences[seq] = header
                header = line
                seq_lines = []
            else:
                seq_lines.append(line)

        if header:
            seq = "".join(seq_lines)
            if seq not in sequences:
                sequences[seq] = header

    return sequences


def write_fasta(sequence_dict, output_file):
    with open(output_file, "w") as out:
        for seq, header in sequence_dict.items():
            out.write(header + "\n")
            out.write(seq + "\n")


# ==============================
# Main Workflow
# ==============================

def main():
    ensure_dir(OUTPUT_DIR)

    human_gz_path = os.path.join(OUTPUT_DIR, HUMAN_FASTA_GZ)
    human_fasta_path = os.path.join(OUTPUT_DIR, HUMAN_FASTA)
    crap_path = os.path.join(OUTPUT_DIR, CRAP_FASTA)
    final_path = os.path.join(OUTPUT_DIR, FINAL_FASTA)
    log_path = os.path.join(OUTPUT_DIR, LOG_FILE)

    # Build UniProt URL
    uniprot_url = build_uniprot_url()

    # Download databases
    download_with_retry(uniprot_url, human_gz_path)
    download_with_retry(CRAP_URL, crap_path)

    # Decompress UniProt
    decompress_gz(human_gz_path, human_fasta_path)

    # Parse and deduplicate
    print("Parsing and deduplicating sequences...")

    human_sequences = parse_fasta(human_fasta_path)
    crap_sequences = parse_fasta(crap_path)

    combined_sequences = dict(human_sequences)

    for seq, header in crap_sequences.items():
        if seq not in combined_sequences:
            combined_sequences[seq] = header

    # Write final FASTA
    write_fasta(combined_sequences, final_path)

    # Logging
    with open(log_path, "w") as log:
        log.write("Database Build Log\n")
        log.write(f"Date: {datetime.now()}\n\n")
        log.write("Source:\n")
        log.write("UniProt reviewed human proteome (taxonomy 9606) with isoforms\n")
        log.write("cRAP contaminant database\n\n")
        log.write(f"Human unique sequences: {len(human_sequences)}\n")
        log.write(f"cRAP sequences: {len(crap_sequences)}\n")
        log.write(f"Total unique sequences (combined): {len(combined_sequences)}\n")

    print("\nDatabase construction complete.")
    print(f"Final FASTA: {final_path}")
    print(f"Log file: {log_path}")


if __name__ == "__main__":
    main()