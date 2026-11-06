"""Thin fusion application orchestration."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Sequence
from gffutils import FeatureDB
from pyfaidx import Fasta
from .fusion_cli import parse_arguments, validate_argument_dependencies
from .fusion_filtering import build_reference_proteome_indices
from .fusion_orchestration import group_fusioninspector_inputs, process_samples
from .fusion_reporting import prepare_ranking_dataframe, report_summary, write_outputs, digest_filtered_database
from .fusion_transcripts import build_transcript_models
from .release_validation import preflight_producer_contract
from .pipeline_config import PipelineConfig
from .provenance import configure_logging, load_sample_metadata
from .splice_translation import prepare_run_manifest, publish_run_manifest
logger = logging.getLogger(__name__)


def load_reference_data(args):
    """Load the indexed genome and the transcript annotation models."""
    logger.info("Loading genome and GTF database...")
    try:
        genome = Fasta(args.genome, sequence_always_upper=True, rebuild=False)
    except (OSError, ValueError):
        # Missing or stale .fai: let pyfaidx (re)build it.
        genome = Fasta(args.genome, sequence_always_upper=True, rebuild=True)
    logger.info("Loaded genome with pyfaidx index")

    db = FeatureDB(args.gtf_db, keep_order=True)
    transcript_models, transcript_alias_index, transcript_index, gene_symbol_index = (
        build_transcript_models(db)
    )
    return genome, db, transcript_models, transcript_alias_index, transcript_index, gene_symbol_index


def load_reference_proteome(args):
    """Load reference proteins and digested peptides when requested."""

    ref_protein_set = None
    ref_pep_set = None

    if args.reference_proteome:

        (
            ref_protein_set,
            ref_pep_set,
        ) = build_reference_proteome_indices(
            args.reference_proteome,
            max_missed_cleavages=args.max_missed_cleavages,
            min_len=args.digested_min_peptide_length,
            max_len=args.digested_max_peptide_length,
            cache_path=args.reference_peptide_cache,
        )

        logger.info(
            "Loaded %d reference proteins and %d reference tryptic peptides",
            len(ref_protein_set),
            len(ref_pep_set),
        )

    return (
        ref_protein_set,
        ref_pep_set,
    )

def discover_input_samples(args):
    """Discover FusionInspector files and group them by sample identifier."""

    logger.info("Parsing FusionInspector outputs...")

    sample_groups = group_fusioninspector_inputs(
        fusioninspector_paths=args.fusioninspector,
        recursive=args.recursive_inputs,
    )

    if not sample_groups:
        raise RuntimeError("No FusionInspector files found.")

    file_count = sum(len(group["fusioninspector"]) for group in sample_groups.values())

    logger.info(
        "Grouped %d FusionInspector file(s) into %d sample(s)",
        file_count,
        len(sample_groups),
    )

    return sample_groups

def main(argv: Optional[Sequence[str]] = None):

    args = parse_arguments(argv)
    configure_logging("INFO")
    validate_argument_dependencies(args)
    preflight_producer_contract("fusioninspector", args.annotation_release)
    args.sample_metadata_lookup = load_sample_metadata(args.sample_metadata)
    args = PipelineConfig.from_namespace(args)
    manifest_base = (
        args.filtered_protein_fasta
        or args.biological_interpretation_tsv
        or args.dia_database_metadata_tsv
        or "fusiontoprotein"
    )
    # Inputs are fingerprinted now; the manifest is published once outputs are written.
    manifest = prepare_run_manifest(args, manifest_base, Path(__file__).name)

    (
        genome,
        db,
        transcript_models,
        transcript_alias_index,
        transcript_index,
        gene_symbol_index,
    ) = load_reference_data(args)

    ref_protein_set, ref_pep_set = load_reference_proteome(args)

    sample_groups = discover_input_samples(args)

    ranking_rows, summary = process_samples(
        sample_groups=sample_groups,
        db=db,
        genome=genome,
        transcript_models=transcript_models,
        transcript_alias_index=transcript_alias_index,
        transcript_index=transcript_index,
        gene_symbol_index=gene_symbol_index,
        args=args,
        ref_pep_set=ref_pep_set,
        ref_protein_set=ref_protein_set,
    )
    ranking_df = prepare_ranking_dataframe(ranking_rows)
    report_summary(summary, ranking_df)

    filtered_df = write_outputs(ranking_df, args)
    digest_filtered_database(filtered_df, args)
    publish_run_manifest(manifest)

    if summary["protein_count"] == 0:
        # A legitimate result under a strict policy, not a failure: outputs are
        # complete (empty), so the workflow can continue and record the step.
        logger.warning("No fusion proteins passed reconstruction for these inputs; outputs are empty")
    return 0
