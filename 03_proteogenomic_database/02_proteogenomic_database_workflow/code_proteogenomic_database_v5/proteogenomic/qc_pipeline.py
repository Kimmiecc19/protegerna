"""QC application orchestration."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, List, Sequence
from .provenance import configure_logging, require_files
from .qc_cli import parse_args
from .qc_calculations import (
    add_peptide_eligibility, build_reference_peptide_set, header_metadata_rows,
    header_metadata_summary_rows, length_distribution_rows, metadata_summary,
    peptide_uniqueness_rows, quantms_database_validation, sequence_qc,
)
from .qc_io import parse_all_fastas, write_tsv
from .qc_reporting import write_filtered_fasta


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    configure_logging("INFO")
    require_files(args.fasta, "input FASTA")
    require_files(args.metadata, "metadata")
    if args.reference_proteome:
        require_files([args.reference_proteome], "reference proteome")
    fasta_paths = [Path(p) for p in args.fasta]
    metadata_paths = [Path(p) for p in args.metadata]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    records = parse_all_fastas(fasta_paths, args.labels)
    sequence_rows, duplicate_sequence_rows, summary_rows = sequence_qc(records)
    add_peptide_eligibility(
        records,
        sequence_rows,
        summary_rows,
        args.max_missed_cleavages,
        args.min_peptide_length,
        args.max_peptide_length,
    )
    length_rows = length_distribution_rows(records)
    parsed_header_rows = header_metadata_rows(records)
    parsed_header_summary = header_metadata_summary_rows(parsed_header_rows)
    quantms_rows, quantms_summary = quantms_database_validation(records)

    write_tsv(outdir / f"{args.prefix}.sequence_qc.tsv", sequence_rows)
    write_tsv(outdir / f"{args.prefix}.duplicate_sequences.tsv", duplicate_sequence_rows)
    write_tsv(outdir / f"{args.prefix}.qc_summary.tsv", summary_rows)
    write_tsv(outdir / f"{args.prefix}.length_distribution.tsv", length_rows)
    write_tsv(outdir / f"{args.prefix}.header_metadata.tsv", parsed_header_rows)
    write_tsv(
        outdir / f"{args.prefix}.header_metadata_summary.tsv",
        parsed_header_summary,
        fieldnames=["summary_type", "field", "value", "count", "statistic"],
    )
    write_tsv(outdir / f"{args.prefix}.quantms_validation.tsv", quantms_rows)
    write_tsv(
        outdir / f"{args.prefix}.quantms_validation_summary.tsv",
        quantms_summary,
        fieldnames=["metric", "value"],
    )

    if metadata_paths:
        meta_rows = metadata_summary(metadata_paths, args.labels)
        write_tsv(outdir / f"{args.prefix}.metadata_summary.tsv", meta_rows)

    if args.reference_proteome:
        ref_path = Path(args.reference_proteome)
        if not ref_path.exists():
            raise FileNotFoundError(f"Reference proteome FASTA not found: {ref_path}")
        ref_peptides = build_reference_peptide_set(
            ref_path,
            args.max_missed_cleavages,
            args.min_peptide_length,
            args.max_peptide_length,
        )
        pep_rows = peptide_uniqueness_rows(
            records,
            ref_peptides,
            args.max_missed_cleavages,
            args.min_peptide_length,
            args.max_peptide_length,
        )
        write_tsv(outdir / f"{args.prefix}.peptide_uniqueness.tsv", pep_rows)

    filtered_stats = None
    if args.write_filtered_fasta:
        filtered_fasta = outdir / (
            f"{args.prefix}.filtered_min{args.min_protein_length}aa.fasta"
        )
        exclusions_tsv = outdir / f"{args.prefix}.filtered_fasta_exclusions.tsv"
        filtered_stats = write_filtered_fasta(
            records=records,
            fasta_path=filtered_fasta,
            exclusions_path=exclusions_tsv,
            min_protein_length=args.min_protein_length,
            exclude_no_eligible_peptide=args.exclude_no_eligible_peptide,
            max_missed_cleavages=args.max_missed_cleavages,
            min_peptide_length=args.min_peptide_length,
            max_peptide_length=args.max_peptide_length,
        )

    all_summary = next(row for row in summary_rows if row["source_label"] == "ALL")
    logging.info("QC complete: %s FASTA records processed", f"{len(records):,}")
    logging.info("Total residues: %s", f"{int(all_summary['total_residues']):,}")
    logging.info("Unique protein sequences: %s", f"{int(all_summary['n_unique_sequences']):,}")
    logging.info(
        "Proteins with eligible peptide: "
        f"{int(all_summary['n_proteins_with_eligible_peptide']):,} "
        f"({float(all_summary['pct_proteins_with_eligible_peptide']):.3f}%)"
    )
    logging.info(
        "Proteins without eligible peptide: "
        f"{int(all_summary['n_proteins_without_eligible_peptide']):,}"
    )
    if filtered_stats is not None:
        logging.info("Filtered FASTA records retained: %s", f"{filtered_stats['kept_records']:,}")
        logging.info("Filtered FASTA records excluded: %s", f"{filtered_stats['excluded_records']:,}")
    logging.info("Output directory: %s", outdir)
    failing_quantms = sum(not bool(row["quantms_ready"]) for row in quantms_rows)
    quantms_warnings = sum(bool(str(row["validation_warnings"]).strip()) for row in quantms_rows)
    logging.info("quantms/DIA-NN validation failures: %s", f"{failing_quantms:,}")
    logging.info("quantms/DIA-NN annotation warnings: %s", f"{quantms_warnings:,}")
    if args.strict_quantms and failing_quantms:
        raise RuntimeError(
            f"Final FASTA failed strict quantms validation for {failing_quantms} record(s)"
        )
