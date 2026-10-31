"""Fusion CLI schema and argument dependency validation."""
from __future__ import annotations
import argparse, logging
from typing import Optional, Sequence
from .provenance import require_files
LOGGER=logging.getLogger(__name__); logger=LOGGER


def add_input_arguments(parser: argparse.ArgumentParser) -> None:
    """Add caller and reference input options."""
    group = parser.add_argument_group("inputs")
    group.add_argument(
        "--fusioninspector",
        nargs="+",
        required=True,
        help=(
            "FusionInspector TSV file(s) or directories. "
            "Directories are searched for "
            "*.fusion_predictions.final.abridged.tsv files."
        ),
    )
    group.add_argument(
        "--recursive_inputs",
        action="store_true",
        help="Recursively search supplied directories.",
    )
    group.add_argument("--gtf_db", required=True, help="Prebuilt gffutils database")
    group.add_argument("--genome", required=True, help="Genome FASTA")
    group.add_argument("--sample_metadata", help="TSV/CSV with sample_id and optional batch/condition columns")
    group.add_argument("--annotation_release", required=True, help="Reference annotation release, for example GENCODE_46")
    group.add_argument("--organism", required=True, help="Organism label written to FASTA metadata, for example Homo_sapiens")
    group.add_argument(
        "--reference_proteome",
        default=None,
        help="Reference protein FASTA for peptide-uniqueness filtering",
    )
    group.add_argument("--reference_peptide_cache", help="Persistent checksum-validated reference tryptic-peptide cache")

def add_output_arguments(parser: argparse.ArgumentParser) -> None:
    """Add metadata, FASTA, and peptide output options."""
    group = parser.add_argument_group("outputs")
    group.add_argument(
        "--biological_interpretation_tsv",
        default=None,
        help="Optional biological interpretation TSV output containing all reconstructed fusion candidates",
    )
    group.add_argument(
        "--filtered_cds_fasta",
        default=None,
        help="Optional filtered CDS FASTA output that keeps one best isoform per source file and protein sequence",
    )
    group.add_argument(
        "--filtered_protein_fasta",
        default=None,
        help="Optional filtered protein FASTA output that keeps one best isoform per source file and protein sequence",
    )
    group.add_argument(
        "--dia_database_metadata_tsv",
        default=None,
        help="Optional DIA database metadata TSV matching the filtered FASTA outputs",
    )
    group.add_argument(
        "--out_sequence_sample_tsv",
        default=None,
        help=(
            "Optional per-sample audit TSV. This provenance file is not intended "
            "as input to the event-level database merge and does not affect FASTA retention."
        ),
    )
    group.add_argument(
        "--digested_peptide_tsv",
        default=None,
        help="Optional TSV path for digested tryptic peptides",
    )

def add_reconstruction_arguments(parser: argparse.ArgumentParser) -> None:
    """Add reconstruction, execution, and cache controls."""
    group = parser.add_argument_group("reconstruction")
    group.add_argument(
        "--nmd_distance_threshold_nt",
        type=int,
        default=55,
        help="NMD rule threshold: stop codon end must be at least this many nt upstream of a downstream exon junction",
    )
    group.add_argument(
        "--early_stop_aa_cutoff",
        type=int,
        default=30,
        help="Early stop cutoff in amino acids downstream of junction to consider non-functional (default 30)",
    )
    group.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes for per-sample parallel processing",
    )
    group.add_argument(
        "--max_transcripts_per_gene", type=int, default=3,
        help=(
            "Maximum ranked CDS-containing transcripts evaluated per fusion partner "
            "(default: 3). Set to 1 only for a conservative representative-transcript "
            "strategy; this is not exhaustive reconstruction. Identical protein "
            "products are deduplicated downstream."
        ),
    )
    group.add_argument(
        "--transcript_model_cache",
        default=None,
        help="Optional path to write/read cached transcript models (pickle)",
    )
    group.add_argument(
        "--digest_trypsin",
        action="store_true",
        help="Enable in silico trypsin digestion (K/R not before P)",
    )

def add_filtering_arguments(parser: argparse.ArgumentParser) -> None:
    """Add DIA inclusion and confidence-policy options."""
    group = parser.add_argument_group("DIA filtering")
    group.add_argument(
        "--min_protein_length",
        type=int,
        default=30,
        help="Minimum protein length required for DIA FASTA inclusion",
    )
    group.add_argument(
        "--quantms_conservative",
        action="store_true",
        help=(
            "Apply the recommended quantms/DIA-NN fusion database policy: require a "
            "canonical-unique junction peptide and exclude frameshift, truncated, NMD, "
            "unknown-frame, low-confidence, and donor-only products."
        ),
    )
    group.add_argument(
        "--exclude_incomplete_cds", action=argparse.BooleanOptionalAction,
        default=True,
        help="Exclude cds_start_NF/cds_end_NF transcript products from the DIA FASTA while retaining metadata (default: true)",
    )
    group.add_argument(
        "--require_unique_junction_peptide",
        action="store_true",
        help="Require at least one junction-spanning peptide unique vs reference proteome",
    )
    group.add_argument(
        "--require_junction_peptide",
        action="store_true",
        help="Require at least one tryptic peptide spanning the fusion junction for DIA FASTA inclusion",
    )
    group.add_argument(
        "--exclude_frameshift_from_dia",
        action="store_true",
        help="Keep frameshift candidates in metadata but exclude them from the filtered DIA FASTA",
    )
    group.add_argument(
        "--exclude_truncated_from_dia",
        action="store_true",
        help="Keep early-stop/truncated candidates in metadata but exclude them from the filtered DIA FASTA",
    )
    group.add_argument(
        "--exclude_nmd_from_dia",
        action="store_true",
        help="Keep NMD-predicted candidates in metadata but exclude them from the filtered DIA FASTA",
    )
    group.add_argument(
        "--include_donor_only_products",
        action="store_true",
        help=(
            "Allow proteins whose translation terminates before the fusion junction "
            "to remain eligible for the DIA FASTA. These products are labelled "
            "donor-only and cannot provide junction-level fusion evidence."
        ),
    )
    group.add_argument(
        "--min_retained_cds_nt",
        type=int,
        default=30,
        help="Flag/exclude DIA candidates where donor or acceptor retained CDS is shorter than this many nt",
    )
    group.add_argument(
        "--max_breakpoint_snap_distance_nt",
        type=int,
        default=25,
        help="Flag/exclude DIA candidates when resolved splice boundary is farther than this from reported breakpoint",
    )
    group.add_argument(
        "--min_split_reads_for_snapped_product", type=int, default=1,
        help="Minimum FusionInspector junction reads required to admit an intronic/outside snapped product to the primary FASTA",
    )

def add_digestion_arguments(parser: argparse.ArgumentParser) -> None:
    """Add in-silico digestion constraints."""
    group = parser.add_argument_group("tryptic digestion")
    group.add_argument(
        "--max_missed_cleavages",
        type=int,
        default=2,
        help="Maximum missed cleavages for trypsin digestion",
    )
    group.add_argument(
        "--digested_min_peptide_length",
        type=int,
        default=7,
        help="Minimum tryptic peptide length",
    )
    group.add_argument(
        "--digested_max_peptide_length",
        type=int,
        default=40,
        help="Maximum tryptic peptide length",
    )

def build_parser() -> argparse.ArgumentParser:
    """Build the authoritative fusion CLI schema."""
    parser = argparse.ArgumentParser(
        description=(
            "FusionInspector fusion-protein DIA database generator with one "
            "transcript pair per fusion"
        )
    )
    add_input_arguments(parser)
    add_output_arguments(parser)
    add_reconstruction_arguments(parser)
    add_filtering_arguments(parser)
    add_digestion_arguments(parser)

    return parser

def parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = build_parser()

    return parser.parse_args(argv)

def validate_argument_dependencies(args):
    """
    Validate combinations of command-line arguments.
    """

    require_files([args.gtf_db, args.genome], "critical reference")
    if args.reference_proteome:
        require_files([args.reference_proteome], "reference proteome")
    if args.sample_metadata:
        require_files([args.sample_metadata], "sample metadata")
    if args.max_transcripts_per_gene < 1:
        raise ValueError("--max_transcripts_per_gene must be at least 1")
    if args.min_split_reads_for_snapped_product < 1:
        raise ValueError("--min_split_reads_for_snapped_product must be at least 1")

    if args.quantms_conservative:
        if not args.reference_proteome:
            raise ValueError("--quantms_conservative requires --reference_proteome")
        args.require_unique_junction_peptide = True
        args.require_junction_peptide = True
        args.exclude_frameshift_from_dia = True
        args.exclude_truncated_from_dia = True
        args.exclude_nmd_from_dia = True
        args.include_donor_only_products = False
        logger.info("Enabled conservative quantms/DIA-NN fusion database policy")

    if args.require_unique_junction_peptide and not args.reference_proteome:
        logger.error(
            "--require_unique_junction_peptide requires " "--reference_proteome"
        )
        raise ValueError("Missing reference proteome.")

    if args.require_unique_junction_peptide and not args.require_junction_peptide:
        logger.info(
            "--require_unique_junction_peptide implies " "--require_junction_peptide"
        )
        args.require_junction_peptide = True
