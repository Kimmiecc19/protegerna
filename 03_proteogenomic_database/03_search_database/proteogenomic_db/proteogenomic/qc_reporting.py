"""Optional diagnostic FASTA and exclusion reporting."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Sequence
from .qc_models import FastaRecord
from .qc_calculations import digest_tryptic_peptides
from .qc_io import write_tsv
from .audit import exclusion_codes


def write_filtered_fasta(
    records: Sequence[FastaRecord],
    fasta_path: Path,
    exclusions_path: Path,
    min_protein_length: int,
    exclude_no_eligible_peptide: bool,
    max_missed_cleavages: int,
    min_peptide_length: int,
    max_peptide_length: int,
) -> Dict[str, int]:
    """Write a filtered FASTA without sequence deduplication.

    Exact-sequence collapse and aggregate provenance headers belong exclusively
    to the merge stage. QC preserves every passing record and its original
    header so it cannot discard a scientifically preferable annotation.
    """
    fasta_path.parent.mkdir(parents=True, exist_ok=True)
    exclusions: List[Dict[str, object]] = []
    kept = 0
    kept_residues = 0

    with fasta_path.open("w", encoding="utf-8") as handle:
        for rec in records:
            reasons: List[str] = []

            if len(rec.sequence) < min_protein_length:
                reasons.append(f"protein_shorter_than_{min_protein_length}aa")

            peptides = digest_tryptic_peptides(
                rec.sequence,
                max_missed_cleavages=max_missed_cleavages,
                min_len=min_peptide_length,
                max_len=max_peptide_length,
            )
            has_eligible_peptide = bool(peptides)
            if exclude_no_eligible_peptide and not has_eligible_peptide:
                reasons.append("no_eligible_tryptic_peptide")

            if reasons:
                exclusions.append({
                    "source_label": rec.source_label,
                    "source_file": rec.source_file,
                    "record_ordinal": rec.ordinal,
                    "header": rec.header,
                    "sequence_hash": rec.sequence_hash,
                    "sequence_length": len(rec.sequence),
                    "has_eligible_tryptic_peptide": has_eligible_peptide,
                    "exclusion_reasons": ";".join(reasons),
                    "exclusion_reason_codes": exclusion_codes(";".join(reasons)),
                    "duplicate_of_header": "",
                })
                continue

            handle.write(f">{rec.header}\n")
            for start in range(0, len(rec.sequence), 60):
                handle.write(rec.sequence[start:start + 60] + "\n")
            kept += 1
            kept_residues += len(rec.sequence)

    write_tsv(
        exclusions_path,
        exclusions,
        fieldnames=[
            "source_label", "source_file", "record_ordinal", "header",
            "sequence_hash", "sequence_length",
            "has_eligible_tryptic_peptide", "exclusion_reasons", "exclusion_reason_codes",
            "duplicate_of_header",
        ],
    )

    return {
        "input_records": len(records),
        "kept_records": kept,
        "excluded_records": len(exclusions),
        "filtered_total_residues": kept_residues,
    }
