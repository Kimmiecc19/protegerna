#!/usr/bin/env python3
"""
Authoritatively merge proteogenomic FASTAs and collapse exact amino-acid
sequences across callers, events, and transcripts.

The script is designed for FASTA files produced by rMATS-, SUPPA-, and
FusionInspector-to-protein workflows using pipe-delimited headers such as:

    >PGDB|source=rmats|record_type=protein|record_id=RMATS_P000001|...

It also tolerates simpler FASTA headers and attempts to infer a missing source
from filenames and record identifiers.

Primary outputs
---------------
1. A sequence-level FASTA containing one record per unique amino-acid sequence.
2. A sequence-level metadata TSV containing aggregated provenance.
3. A record-to-sequence mapping TSV retaining every original FASTA record.
4. A biological-interpretation TSV retaining every original record, including
   records excluded from the final DIA search FASTA.
5. Summary TSV and JSON files describing the merge and filtering.

Deduplication is based on exact normalized amino-acid sequence equality. Before
exact-sequence collapse, proteins below the configured intact-protein minimum and proteins that
do not produce at least one DIA-NN-compatible tryptic peptide are excluded from
the DIA FASTA but retained in the biological-interpretation output.

Example
-------
python merge_proteogenomic_database.py \
    --gencode_concordance_summary gencode_translation_concordance.json \
    --annotation_release GENCODE_46 --organism Homo_sapiens \
    --inputs fusion.primary.fasta rmats.primary.fasta suppa.primary.fasta \
    --reference_fasta UP000005640_9606.fasta --contaminants_fasta crap.fasta \
    --out_fasta proteogenomic_database.fasta --out_metadata proteogenomic_metadata.tsv \
    --out_mapping proteogenomic_mapping.tsv --out_summary_tsv proteogenomic_summary.tsv \
    --out_summary_json proteogenomic_summary.json
"""

from __future__ import annotations

import argparse
import itertools
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from proteogenomic.provenance import configure_logging, require_files
from proteogenomic.release_validation import check_concordance_binding, validate_gencode_concordance_summary
from proteogenomic.pipeline_config import PipelineConfig
from proteogenomic.merge_models import ProteinFilterConfig
from proteogenomic.merge_parsing import discover_fasta_files, parse_record_types, read_input_records
from proteogenomic.merge_models import ParsedRecord, SequenceAggregate, sequence_hashes
from proteogenomic.merge_parsing import digest_tryptic_peptides
from proteogenomic.merge_aggregation import (
    add_to_aggregates, aggregate_exact_sequences, build_summary, order_aggregates, retained_biological_rows,
)
from proteogenomic.merge_peptide_evidence import final_database_peptide_rows, iter_final_database_peptide_rows
from proteogenomic.merge_reporting import write_outputs, write_summary_files, write_tsv
LOGGER = logging.getLogger("merge_proteogenomic_database")

# Names re-exported for callers and tests that import them from this script.
__all__ = [
    "ParsedRecord", "SequenceAggregate", "sequence_hashes", "digest_tryptic_peptides",
    "aggregate_exact_sequences", "final_database_peptide_rows", "build_parser", "main",
]


BIOLOGICAL_INTERPRETATION_FIELDS = [
    "included_in_dia_fasta", "exclusion_reason", "exclusion_reason_codes", "sequence_id",
    "sequence_md5", "sequence_sha256", "input_file", "original_id",
    "source", "record_type", "gene_symbols",
    "gene_ids", "transcripts", "uniprot_accessions", "uniprot_entries",
    "protein_names", "event_types", "event_ids", "variants", "callers",
    "translation_strategies", "database_output_tiers", "protein_product_classes",
    "protein_length", "n_eligible_tryptic_peptides",
    "min_eligible_peptide_length", "max_eligible_peptide_length",
    "original_description", "sequence",
]


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Merge proteogenomic protein FASTA files and collapse exact amino-acid "
            "sequences while preserving biological provenance."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--gencode_concordance_summary", required=True,
        help="Passing JSON summary from validate_gencode_translation; mandatory for final release.",
    )

    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Input FASTA files and/or directories.",
    )
    parser.add_argument("--annotation_release", required=True, help="Reference annotation release recorded in output metadata")
    parser.add_argument("--organism", required=True, help="Organism label written to FASTA headers")
    parser.add_argument(
        "--require_producer_manifests",
        action=argparse.BooleanOptionalAction, default=False,
        help=(
            "Fail when a proteogenomic input FASTA has no <FASTA>.run_config.json, so every "
            "producer FASTA is verified against the GENCODE-validated reference."
        ),
    )
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction, default=False,
        help="Search input directories recursively for FASTA files.",
    )
    parser.add_argument(
        "--reference_fasta",
        nargs="+",
        default=[],
        help="Reviewed human reference-proteome FASTA file(s) to include.",
    )
    parser.add_argument(
        "--contaminants_fasta",
        nargs="+",
        default=[],
        help="cRAP contaminant FASTA file(s) to include. Do not supply iRT standards.",
    )
    parser.add_argument(
        "--record_types",
        nargs="+",
        default=["protein"],
        help=(
            "Record types to retain. The default keeps protein records and excludes "
            "CDS and junction-peptide FASTAs."
        ),
    )
    parser.add_argument(
        "--out_fasta",
        default="proteogenomic_unique_proteins.fasta",
        help="Output FASTA containing one record per exact protein sequence.",
    )
    parser.add_argument(
        "--out_metadata",
        default="proteogenomic_unique_metadata.tsv",
        help="Sequence-level metadata table.",
    )
    parser.add_argument(
        "--out_mapping",
        default="proteogenomic_record_mapping.tsv",
        help="Original-record to unique-sequence mapping table.",
    )
    parser.add_argument(
        "--out_peptide_evidence",
        default="proteogenomic_final_peptide_evidence.tsv",
        help="Post-merge peptide uniqueness, junction, and distinguishing-fragment evidence.",
    )
    parser.add_argument(
        "--out_biological_interpretation",
        default="proteogenomic_biological_interpretation.tsv",
        help=(
            "Record-level biological interpretation table containing every input "
            "record, including records excluded from the final DIA FASTA."
        ),
    )
    parser.add_argument(
        "--out_summary_tsv",
        default="proteogenomic_summary.tsv",
        help="Merge summary in two-column TSV format.",
    )
    parser.add_argument(
        "--out_summary_json",
        default="proteogenomic_summary.json",
        help="Merge summary in JSON format.",
    )

    parser.add_argument(
        "--id_prefix",
        default="PGDB_U",
        help="Prefix used for unique sequence identifiers.",
    )
    parser.add_argument(
        "--id_width",
        type=int,
        default=7,
        help="Zero-padded numeric width used in unique sequence identifiers.",
    )
    parser.add_argument(
        "--max_header_values",
        type=int,
        default=3,
        help=(
            "Maximum values shown for multi-valued header fields. Complete values "
            "remain available in the metadata TSV. Use 0 for no limit."
        ),
    )

    parser.add_argument(
        "--min_protein_length",
        type=int,
        default=6,
        help=(
            "Independent minimum intact-protein length (default: 6 aa). Peptide "
            "eligibility is evaluated separately using --min_peptide_length "
            "(default: 7 aa)."
        ),
    )
    parser.add_argument(
        "--max_protein_length",
        type=int,
        default=None,
        help="Optional maximum amino-acid sequence length retained.",
    )
    parser.add_argument(
        "--min_peptide_length",
        type=int,
        default=7,
        help="Minimum DIA-NN tryptic peptide length.",
    )
    parser.add_argument(
        "--max_peptide_length",
        type=int,
        default=40,
        help="Maximum DIA-NN tryptic peptide length.",
    )
    parser.add_argument(
        "--max_missed_cleavages",
        type=int,
        default=2,
        help="Maximum tryptic missed cleavages used for DIA peptide eligibility.",
    )
    parser.add_argument(
        "--include_rescue_tiers",
        action=argparse.BooleanOptionalAction, default=False,
        help="Allow alternative_start/exploratory_orf records; disabled by default for the primary DIA database.",
    )
    parser.add_argument(
        "--invalid_sequence_policy",
        choices=("error", "warn", "skip"),
        default="warn",
        help="Action for empty or invalid amino-acid sequences.",
    )

    parser.add_argument(
        "--log_level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
        help="Logging verbosity.",
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    numeric_nonnegative = {
        "id_width": args.id_width,
        "max_header_values": args.max_header_values,
        "min_protein_length": args.min_protein_length,
        "min_peptide_length": args.min_peptide_length,
        "max_peptide_length": args.max_peptide_length,
        "max_missed_cleavages": args.max_missed_cleavages,
    }
    for name, value in numeric_nonnegative.items():
        if value < 0:
            raise ValueError(f"--{name} must be >= 0")

    if args.id_width < 1:
        raise ValueError("--id_width must be at least 1")
    if args.min_protein_length < 6:
        raise ValueError("--min_protein_length must be at least 6 for the DIA FASTA")
    if args.min_peptide_length < 1:
        raise ValueError("--min_peptide_length must be at least 1")
    if args.max_peptide_length < args.min_peptide_length:
        raise ValueError("--max_peptide_length cannot be smaller than --min_peptide_length")

    if args.max_protein_length is not None:
        if args.max_protein_length < 1:
            raise ValueError("--max_protein_length must be at least 1")
        if args.max_protein_length < args.min_protein_length:
            raise ValueError(
                "--max_protein_length cannot be smaller than --min_protein_length"
            )

    output_paths = [
        Path(args.out_fasta).resolve(),
        Path(args.out_metadata).resolve(),
        Path(args.out_mapping).resolve(),
        Path(args.out_peptide_evidence).resolve(),
        Path(args.out_biological_interpretation).resolve(),
        Path(args.out_summary_tsv).resolve(),
        Path(args.out_summary_json).resolve(),
    ]
    if len(output_paths) != len(set(output_paths)):
        raise ValueError("All output paths must be distinct")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    try:
        validate_args(args)
        concordance_summary = validate_gencode_concordance_summary(args.gencode_concordance_summary)
        args = PipelineConfig.from_namespace(args)
        record_types = parse_record_types(args.record_types)

        proteogenomic_files = discover_fasta_files(args.inputs, recursive=args.recursive)
        reference_files = discover_fasta_files(args.reference_fasta, recursive=False) if args.reference_fasta else []
        contaminant_files = discover_fasta_files(args.contaminants_fasta, recursive=False) if args.contaminants_fasta else []

        forced_sources: Dict[Path, str] = {}
        for path in reference_files:
            forced_sources[path] = "reference"
        for path in contaminant_files:
            if path in forced_sources:
                raise ValueError(f"FASTA supplied as both reference and contaminant: {path}")
            forced_sources[path] = "crap"

        binding = check_concordance_binding(
            concordance_summary, args.annotation_release, proteogenomic_files,
        )
        LOGGER.info(
            "GENCODE concordance bound to %s; %d producer manifest(s) verified",
            args.annotation_release, len(binding["checked"]),
        )
        if binding["without_manifest"] and args.require_producer_manifests:
            raise RuntimeError(
                "No producer run manifest (reference binding cannot be verified) for: "
                + ", ".join(binding["without_manifest"])
            )
        for path in binding["without_manifest"]:
            LOGGER.warning("No producer run manifest beside %s; reference binding not verified for it", path)

        fasta_files = sorted(set(proteogenomic_files + reference_files + contaminant_files), key=str)
        if not fasta_files:
            raise FileNotFoundError("No FASTA files were found in the supplied inputs")
        require_files(fasta_files, "discovered FASTA")

        LOGGER.info(
            "Discovered %d proteogenomic, %d reference, and %d contaminant FASTA file(s)",
            len(proteogenomic_files), len(reference_files), len(contaminant_files),
        )
        for path in fasta_files:
            LOGGER.debug("  %s", path)

        filter_config = ProteinFilterConfig(
            allowed_record_types=record_types,
            min_length=args.min_protein_length,
            max_length=args.max_protein_length,
            invalid_policy=args.invalid_sequence_policy,
            min_peptide_length=args.min_peptide_length,
            max_peptide_length=args.max_peptide_length,
            max_missed_cleavages=args.max_missed_cleavages,
            include_rescue_tiers=args.include_rescue_tiers,
        )
        # Stages 1-3 (read, validate/filter, collapse identical sequences) run in
        # one streaming pass: records are aggregated as they are read.
        LOGGER.info("Stages 1-3/6: read, filter and collapse identical sequences")
        all_aggregates: Dict[str, SequenceAggregate] = {}
        _, initially_excluded_rows, read_stats = read_input_records(
            fasta_files=fasta_files,
            forced_sources=forced_sources,
            config=filter_config,
            record_sink=lambda record: add_to_aggregates(all_aggregates, record),
        )
        if not all_aggregates:
            raise ValueError("No valid FASTA records remained after filtering")
        LOGGER.info(
            "Collapsed %d retained records into %d exact protein sequences",
            int(read_stats["records_retained_after_dia_filtering"]),
            len(all_aggregates),
        )

        retained = order_aggregates(all_aggregates.values())

        if not retained:
            raise ValueError("No unique sequences passed the sequence-level filters")

        LOGGER.info("Stages 4-6/6: headers, provenance and final FASTA (%d unique proteins)", len(retained))

        id_map, mapping_count = write_outputs(
            aggregates=retained,
            out_fasta=Path(args.out_fasta),
            out_metadata=Path(args.out_metadata),
            out_mapping=Path(args.out_mapping),
            id_prefix=args.id_prefix,
            id_width=args.id_width,
            max_header_values=args.max_header_values,
            organism=args.organism,
            annotation_release=args.annotation_release,
        )
        # Rows are streamed to disk; the header comes from the first row as before.
        peptide_rows = iter_final_database_peptide_rows(retained, id_map, filter_config)
        first_row = next(peptide_rows, None)
        peptide_fields = list(first_row) if first_row is not None else ["sequence_id", "peptide_sequence"]
        write_tsv(
            Path(args.out_peptide_evidence),
            itertools.chain([first_row], peptide_rows) if first_row is not None else (),
            peptide_fields,
        )

        biological_rows: List[Dict[str, object]] = list(initially_excluded_rows)
        biological_rows.extend(retained_biological_rows(retained, id_map))
        biological_count = write_tsv(
            Path(args.out_biological_interpretation),
            biological_rows,
            BIOLOGICAL_INTERPRETATION_FIELDS,
        )

        summary = build_summary(
            fasta_files=fasta_files,
            read_stats=read_stats,
            all_aggregates=all_aggregates,
            retained_aggregates=retained,
            mapping_count=mapping_count,
            biological_interpretation_count=biological_count,
        )
        write_summary_files(
            summary,
            Path(args.out_summary_tsv),
            Path(args.out_summary_json),
        )

        LOGGER.info("Wrote FASTA: %s", Path(args.out_fasta).resolve())
        LOGGER.info("Wrote metadata: %s", Path(args.out_metadata).resolve())
        LOGGER.info("Wrote mapping: %s", Path(args.out_mapping).resolve())
        LOGGER.info("Wrote final peptide evidence: %s", Path(args.out_peptide_evidence).resolve())
        LOGGER.info(
            "Wrote biological interpretation: %s",
            Path(args.out_biological_interpretation).resolve(),
        )
        LOGGER.info("Wrote summary TSV: %s", Path(args.out_summary_tsv).resolve())
        LOGGER.info("Wrote summary JSON: %s", Path(args.out_summary_json).resolve())

        return 0

    except (FileNotFoundError, ValueError, OSError, RuntimeError) as exc:
        # RuntimeError: GENCODE concordance release gate or reference-binding failure.
        LOGGER.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
