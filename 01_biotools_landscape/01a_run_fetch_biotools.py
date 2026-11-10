"""Run the bio.tools fetch for each omics category.
This script is a launcher for fetch_biotools.py, which does the actual fetching and enrichment.

Publication options (--citation-source, --publication-cache, --cache-days,
--no-publication-enrichment) are passed through to fetch_biotools.py;
run that script with --help to list them.

Example usage:
    python run_fetch_biotools.py --omics genomics transcriptomics --output-tag 20240601
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch bio.tools records for each omics category.")
    # The launcher stays standard-library-only: --python-path may select the
    # environment containing requests and the other fetcher dependencies.
    parser.add_argument("--python-path", default=sys.executable,
                        help="Python executable used to run the fetcher (default: current interpreter).")
    parser.add_argument("--omics", nargs="+", choices=list(QUERIES), default=list(QUERIES),
                        help="Categories to fetch (default: all).")
    parser.add_argument("--output-dir", type=Path,
                        help="Output directory (default: results/01ab_results_fetch_biotools/results_fetch_biotools_final).")
    parser.add_argument("--output-tag", default=datetime.now().strftime("%Y%m%d"),
                        help="Filename suffix (default: today's YYYYMMDD).")
    parser.add_argument("--publication-cache", help="Shared publication response cache JSON.")
    args, fetcher_args = parser.parse_known_args()

    code_dir = Path(__file__).resolve().parent
    output_dir = args.output_dir or code_dir / "results" / "01ab_results_fetch_biotools" / "results_fetch_biotools_final"
    output_dir.mkdir(parents=True, exist_ok=True)
    fetcher = code_dir / "fetch_biotools.py"
    # One cache shared by every domain, so repeated publications are looked up once.
    cache_path = args.publication_cache or str(output_dir / "publication-cache.json")

    for omic_domain in args.omics:
        output_path = output_dir / f"{omic_domain}_fetch_biotools_{args.output_tag}.tsv"
        subprocess.run([args.python_path, str(fetcher), QUERIES[omic_domain], str(output_path),
                        "--publication-cache", cache_path, *fetcher_args], check=True)

    print(f"Tool tables, publication/function audit tables and manifests written to {output_dir}")


if __name__ == "__main__":
    main()
