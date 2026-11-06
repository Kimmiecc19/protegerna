"""QC command-line construction."""
from __future__ import annotations
import argparse
from typing import Optional, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="QC variant protein FASTA outputs from fusiontoprotein, rMATS, and SUPPA scripts."
    )
    parser.add_argument("--fasta", nargs="+", required=True, help="Protein FASTA files to QC.")
    parser.add_argument(
        "--labels",
        nargs="*",
        help="Optional labels for FASTA files, e.g. fusion rmats suppa. Must match --fasta length if supplied.",
    )
    parser.add_argument(
        "--metadata",
        nargs="*",
        default=[],
        help="Optional consequence/ranking TSV files from fusion, rMATS, or SUPPA.",
    )
    parser.add_argument(
        "--reference_proteome",
        nargs="+",
        help="Optional reference protein FASTA(s) for tryptic peptide uniqueness checks (plain or .gz).",
    )
    parser.add_argument("--outdir", default="proteogenomic_fasta_qc", help="Output directory.")
    parser.add_argument("--prefix", default="proteogenomic_fasta", help="Output filename prefix.")
    parser.add_argument("--max_missed_cleavages", type=int, default=2)
    parser.add_argument("--min_peptide_length", type=int, default=7)
    parser.add_argument("--max_peptide_length", type=int, default=40)
    parser.add_argument(
        "--min_protein_length",
        type=int,
        default=6,
        help="Minimum protein length retained in the filtered FASTA (default: 6 aa).",
    )
    parser.add_argument(
        "--exclude_no_eligible_peptide",
        action=argparse.BooleanOptionalAction, default=False,
        help=(
            "Also exclude proteins that generate no theoretical tryptic peptide "
            "within the configured peptide-length and missed-cleavage limits."
        ),
    )
    parser.add_argument(
        "--write_filtered_fasta",
        action=argparse.BooleanOptionalAction, default=False,
        help=(
            "Opt in to a diagnostic cleaned FASTA. QC is observational by default; "
            "only the merge command may create the final deduplicated/DIA-filtered database."
        ),
    )
    parser.add_argument(
        "--strict_quantms",
        action=argparse.BooleanOptionalAction, default=False,
        help="Exit with an error if the final FASTA fails target-only quantms/DIA-NN validation.",
    )
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
