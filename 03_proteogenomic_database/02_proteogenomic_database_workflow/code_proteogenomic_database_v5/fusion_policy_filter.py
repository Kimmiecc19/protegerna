#!/usr/bin/env python3
"""Keep only fusion FASTA records whose protein sequence satisfied the fusion DIA policy."""
import argparse
from pathlib import Path

import pandas as pd


def read_fasta(path):
    header, chunks = None, []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(chunks)
                header, chunks = line, []
            elif line:
                chunks.append(line.strip())
    if header is not None:
        yield header, "".join(chunks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True, type=Path)
    ap.add_argument("--biological", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    bio = pd.read_csv(args.biological, sep="\t", dtype=str, keep_default_na=False,
                      usecols=["protein_sequence", "dia_fasta_include"])
    passing = set(bio.loc[bio["dia_fasta_include"].str.lower() == "true", "protein_sequence"])
    passing.discard("")

    kept = total = 0
    kept_seqs = set()
    with open(args.out, "w") as out:
        for header, seq in read_fasta(args.fasta):
            total += 1
            if seq in passing:
                out.write(f"{header}\n{seq}\n")
                kept += 1
                kept_seqs.add(seq)
    print(f"FASTA records read: {total}")
    print(f"records kept (policy-compliant sequence): {kept}")
    print(f"distinct policy-compliant sequences written: {len(kept_seqs)}")
    print(f"policy-compliant sequences in biological table: {len(passing)}")
    if len(kept_seqs) != len(passing):
        print("WARNING: some policy-compliant sequences were not found in the FASTA")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
