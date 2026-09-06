"""Run the bio.tools fetch for each omics category."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


QUERIES = {
    "genomics": (
        "genomic,genome,dna,gene,variant calling,variant,assembly,assemblies,"
        "annotation,sequencing,read alignment,vcf,snp,indel,reference genome,"
        "sequence analysis,sequence alignment"
    ),
    "transcriptomics": (
        "transcriptomic,transcriptome,rna-seq,RNAseq,rna seq,gene expression,"
        "fusion gene,transcript,rna sequencing,splicing,splice,expression analysis"
    ),
    "proteomics": (
        "proteomic,protein,peptide,mass spectrometry,MS,MS/MS,quantitative "
        "proteomics,peptide identification,protein identification,protein "
        "inference,protein annotation"
    ),
    "multiomics": (
        "multi-omic,multiomic,proteogenomic,integration,integrative,cross-omic,"
        "pan-omic,pathway,network"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch bio.tools records for each omics category."
    )
    parser.add_argument(
        "--python-path",
        default=sys.executable,
        help="Python executable used to run the fetcher (default: current interpreter).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    code_dir = Path(__file__).resolve().parent
    results_dir = code_dir.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    fetcher = code_dir / "fetch_biotools_final2026.py"

    for omic, query in QUERIES.items():
        output = results_dir / f"{omic}_august2026.tsv"
        subprocess.run(
            [args.python_path, str(fetcher), query, str(output), "--tsv"],
            check=True,
        )

    print(f"Tool tables and manifests written to {results_dir}")


if __name__ == "__main__":
    main()
