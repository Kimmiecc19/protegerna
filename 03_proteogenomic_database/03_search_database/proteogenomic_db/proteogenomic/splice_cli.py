"""Shared command-line construction for splice-protein producers."""
from __future__ import annotations

import argparse
from typing import Sequence



def _show_only_common_options(parser: argparse.ArgumentParser, common: set[str]) -> None:
    """Keep advanced options accepted for compatibility but out of normal help."""
    for action in parser._actions:
        if action.dest not in common and action.dest != "help":
            action.help = argparse.SUPPRESS


def _add_references(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("reference annotation")
    group.add_argument("--gtf_db", required=True, help="Prebuilt gffutils database")
    group.add_argument("--genome", "--genome-fasta", dest="genome", required=True, help="Indexed genome FASTA")
    group.add_argument("--annotation_release", required=True, help="Reference annotation release, for example GENCODE_46")
    group.add_argument("--organism", required=True, help="Organism label written to FASTA metadata")


def _add_outputs(parser: argparse.ArgumentParser, *, event_summary: bool = False) -> None:
    group = parser.add_argument_group("outputs")
    group.add_argument("--out_prot_fa", required=True)
    group.add_argument("--out_alt_start_prot_fa", help="Separate FASTA for alternative-start products")
    group.add_argument("--out_exploratory_orf_fa", help="Separate FASTA for explicitly enabled longest stop-delimited ORFs")
    group.add_argument("--out_junc_fa", help="Short junction-peptide FASTA; required with --short_junction_peptides")
    group.add_argument("--out_consequence_tsv", help="Consequence audit TSV; defaults beside the primary FASTA")
    if event_summary:
        group.add_argument("--out_event_summary_tsv", help="Event filtering and reconstruction audit TSV")


def _add_reconstruction(parser: argparse.ArgumentParser, *, rmats: bool = False) -> None:
    group = parser.add_argument_group("reconstruction")
    group.add_argument("--pad_partial_codons", action="store_true")
    group.add_argument("--allow_alt_start", action="store_true", help="Allow translation from a downstream in-frame start")
    if rmats:
        group.add_argument("--alternative_start_codons", nargs="+", default=["ATG"])
        group.add_argument("--min_alt_start_kozak_strength", choices=("weak", "moderate", "strong"), default="weak")
    group.add_argument("--allow_longest_orf", action="store_true", help="Enable exploratory longest-ORF rescue")
    group.add_argument("--min_alt_orf_aa", type=int, default=30)
    group.add_argument("--short_junction_peptides", action="store_true")
    group.add_argument("--junction_max_flank", type=int, default=15)
    group.add_argument("--junction_min_flank", type=int, default=7)
    if rmats:
        group.add_argument("--chunksize", type=int, default=50000)
    group.add_argument("--sequence_cache_entries", type=int, default=100000)
    group.add_argument("--workers", type=int, default=1)
    group.add_argument("--nmd_distance_threshold_nt", type=int, default=55)


def _add_filtering(parser: argparse.ArgumentParser, *, rmats: bool = False) -> None:
    group = parser.add_argument_group("DIA filtering")
    group.add_argument("--exclude_frameshift_from_dia", action="store_true")
    group.add_argument("--exclude_nmd_from_dia", action="store_true")
    group.add_argument("--exclude_start_loss_from_dia", action="store_true")
    group.add_argument("--exclude_premature_stop_from_dia", action="store_true")
    group.add_argument("--exclude_incomplete_cds", action=argparse.BooleanOptionalAction, default=True)
    group.add_argument("--require_ri_orf_preserved", action="store_true")
    if rmats:
        group.add_argument("--require_ri_read_evidence", action=argparse.BooleanOptionalAction, default=True)
        group.add_argument("--min_ri_inclusion_reads", type=int, default=1)
        group.add_argument("--exclude_ri_nmd_from_primary", action=argparse.BooleanOptionalAction, default=True)
        group.add_argument("--require_ri_junction_peptide", action=argparse.BooleanOptionalAction, default=True)
        group.add_argument(
            "--include_failed_filter_proteins",
            action="store_true",
            help=("Export reconstructable, non-canonical rMATS proteins even when DIA policy "
                  "filters fail; retain the failure reasons in audit provenance"),
        )
    group.add_argument("--reference_proteome", help="Target-only canonical/reference FASTA")
    group.add_argument("--reference_peptide_cache", help="Checksum-validated peptide cache")
    group.add_argument("--require_unique_event_peptide", action="store_true")
    group.add_argument("--quantms_conservative", action="store_true", help="Enable the recommended primary quantms policy")


def _add_digestion(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("tryptic digestion")
    group.add_argument("--max_missed_cleavages", type=int, default=2)
    group.add_argument("--min_database_peptide_length", type=int, default=7)
    group.add_argument("--max_database_peptide_length", type=int, default=40)


def build_rmats_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="rMATS to protein FASTA plus codon-aware junction peptides")
    _add_references(parser)
    inputs = parser.add_argument_group("rMATS inputs")
    for event in ("se", "a3ss", "a5ss", "mxe", "ri"):
        inputs.add_argument(f"--{event}_files", nargs="*", help=f"{event.upper()} event files")
    _add_outputs(parser, event_summary=True)
    evidence = parser.add_argument_group("rMATS event evidence")
    evidence.add_argument("--max_fdr", type=float)
    evidence.add_argument("--min_abs_inc_level_difference", type=float)
    evidence.add_argument("--min_inclusion_junction_reads", type=int)
    evidence.add_argument("--min_skipping_junction_reads", type=int)
    evidence.add_argument("--rmats_conservative_event_filter", action="store_true")
    _add_reconstruction(parser, rmats=True)
    _add_filtering(parser, rmats=True)
    _add_digestion(parser)
    _show_only_common_options(parser, {
        "gtf_db", "genome", "annotation_release", "organism",
        "se_files", "a3ss_files", "a5ss_files", "mxe_files", "ri_files",
        "out_prot_fa", "out_consequence_tsv", "reference_proteome", "workers",
    })
    return parser


def build_suppa_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SUPPA to protein FASTA plus codon-aware junction peptides")
    _add_references(parser)
    inputs = parser.add_argument_group("SUPPA inputs and PSI evidence")
    inputs.add_argument("--event_files", nargs="+", required=True)
    inputs.add_argument("--sample_metadata")
    inputs.add_argument("--psi_files", nargs="+")
    inputs.add_argument("--min_psi", type=float, default=0.05)
    inputs.add_argument("--min_psi_samples", type=int, default=1)
    inputs.add_argument("--keep_events_missing_psi", action="store_true")
    inputs.add_argument("--out_psi_summary_tsv")
    _add_outputs(parser)
    _add_reconstruction(parser)
    _add_filtering(parser)
    _add_digestion(parser)
    _show_only_common_options(parser, {
        "gtf_db", "genome", "annotation_release", "organism",
        "event_files", "psi_files", "out_prot_fa", "out_consequence_tsv",
        "reference_proteome", "workers",
    })
    return parser


def parse_rmats_args(argv: Sequence[str] | None = None):
    parser = build_rmats_parser()
    return parser.parse_args(argv), parser


def parse_suppa_args(argv: Sequence[str] | None = None):
    parser = build_suppa_parser()
    return parser.parse_args(argv), parser
