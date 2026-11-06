#!/usr/bin/env python3
"""Validate canonical CDS reconstruction against a matching GENCODE protein FASTA."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional, TypedDict

from Bio import SeqIO

from rmatstoprotein import build_transcript_models
from proteogenomic.splice_translation import (
    extract_cds_sequence_for_model, translate_cds_for_model,
    normalize_phase_value, open_genome_index,
)


class ConcordanceRow(TypedDict):
    transcript_id: str
    strand: str
    exon_class: str
    completeness: str
    leading_phase: Optional[int]
    phase_class: str
    status: str
    reconstructed_length: int
    reference_length: int
    reconstructed_sha256: str
    reference_sha256: str
    first_difference_aa_1based: Optional[int]
    non_atg_start: bool
    stop_codon_readthrough: bool
    selenocysteine_feature_count: int
    translation_table: int


def fasta_transcript_id(record: Any) -> Optional[str]:
    """Extract ENST ID from common GENCODE protein FASTA headers."""
    tokens = str(record.id).split("|") + str(record.description).split("|")
    for token in tokens:
        clean = token.strip().split(".", 1)[0]
        if clean.startswith("ENST"):
            return clean
    return None


def load_reference(path: Path) -> dict[str, str]:
    proteins: dict[str, str] = {}
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8") as handle:
            for record in SeqIO.parse(handle, "fasta"):
                transcript_id = fasta_transcript_id(record)
                if transcript_id:
                    proteins.setdefault(transcript_id, str(record.seq).rstrip("*").upper())
    except ValueError as exc:
        raise ValueError(
            f"{path} is not a valid GENCODE protein FASTA. Use the matching "
            "pc_translations FASTA (gencode.v*.pc_translations.fa[.gz]), "
            "not metadata.SwissProt."
        ) from exc
    if not proteins:
        raise ValueError(
            f"No ENST-labelled protein FASTA records were found in {path}. "
            "Use the matching GENCODE pc_translations FASTA, not "
            "gencode.v*.metadata.SwissProt (which is a tabular mapping file)."
        )
    return proteins


def validate(gtf_db: Path, genome: Path, protein_fasta: Path) -> list[ConcordanceRow]:
    models = build_transcript_models(str(gtf_db))
    reference = load_reference(protein_fasta)
    genome_index = open_genome_index(str(genome))
    rows: list[ConcordanceRow] = []
    validated_transcripts: set[str] = set()
    try:
        for key, model in models.items():
            transcript_id = str(model.get("transcript_id") or key).split(".", 1)[0]
            if transcript_id not in reference or transcript_id in validated_transcripts:
                continue
            validated_transcripts.add(transcript_id)
            cds = model.get("cds") or []
            ordered = sorted(cds, key=lambda x: x[0], reverse=model.get("strand") == "-")
            leading_phase = normalize_phase_value(ordered[0][2]) if ordered else None
            raw = extract_cds_sequence_for_model(model, genome_index)
            translated = None
            if raw:
                trimmed = raw[int(leading_phase or 0):]
                translated = translate_cds_for_model(trimmed, model)
            expected = reference[transcript_id]
            completeness = (
                "partial" if model.get("cds_start_nf") or model.get("cds_end_nf") else "complete"
            )
            if translated == expected:
                status = "identical_protein"
            elif not translated:
                status = "no_reconstructable_product"
            elif (
                completeness == "partial" and leading_phase in {1, 2}
                and len(expected) == len(translated) + 1
                and expected[1:] == translated
            ):
                status = "explained_partial_leading_residue"
            elif model.get("stop_codon_readthrough") and expected.startswith(translated):
                status = "explained_stop_codon_readthrough_unsupported"
            else:
                status = "discordant_sequence"
            first_difference = None
            if translated != expected:
                limit = min(len(translated or ""), len(expected))
                first_difference = next(
                    (index + 1 for index in range(limit) if translated[index] != expected[index]),
                    limit + 1,
                )
            rows.append({
                "transcript_id": transcript_id,
                "strand": str(model.get("strand")),
                "exon_class": "multi_exon" if len(cds) > 1 else "single_exon",
                "completeness": completeness,
                "leading_phase": leading_phase,
                "phase_class": "nonzero" if leading_phase in {1, 2} else (
                    "zero" if leading_phase == 0 else "missing"
                ),
                "status": status,
                "reconstructed_length": len(translated or ""),
                "reference_length": len(expected),
                "reconstructed_sha256": hashlib.sha256((translated or "").encode()).hexdigest(),
                "reference_sha256": hashlib.sha256(expected.encode()).hexdigest(),
                "first_difference_aa_1based": first_difference,
                "non_atg_start": bool(model.get("non_atg_start")),
                "stop_codon_readthrough": bool(model.get("stop_codon_readthrough")),
                "selenocysteine_feature_count": len(model.get("selenocysteine_intervals") or ()),
                "translation_table": 2 if str(model.get("chrom")).lower() in {"chrm", "mt", "m"} else 1,
            })
    finally:
        genome_index.close()
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtf_db", required=True, type=Path)
    parser.add_argument("--genome", required=True, type=Path)
    parser.add_argument("--gencode_protein_fasta", required=True, type=Path)
    parser.add_argument("--out_tsv", required=True, type=Path)
    parser.add_argument("--out_summary_json", required=True, type=Path)
    parser.add_argument("--max_mismatch_rate", type=float, default=0.0)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    rows = validate(args.gtf_db, args.genome, args.gencode_protein_fasta)
    if not rows:
        raise RuntimeError("No shared GENCODE transcript IDs were available for validation")
    columns = list(ConcordanceRow.__annotations__)
    args.out_tsv.write_text(
        "\t".join(columns) + "\n" + "".join(
            "\t".join(str(row[column]) if row[column] is not None else "NA" for column in columns) + "\n"
            for row in rows
        ), encoding="utf-8",
    )
    counts = Counter(row["status"] for row in rows)
    unexplained_statuses = {"discordant_sequence", "no_reconstructable_product"}
    mismatch_count = sum(counts[status] for status in unexplained_statuses)
    mismatch_rate = mismatch_count / len(rows)
    raw_difference_count = len(rows) - counts["identical_protein"]
    unexplained_complete_mismatch_count = sum(
        1 for row in rows
        if row["completeness"] == "complete" and row["status"] in unexplained_statuses
    )
    unexplained_partial_mismatch_count = sum(
        1 for row in rows
        if row["completeness"] == "partial" and row["status"] in unexplained_statuses
    )
    strata = {}
    for field in ("strand", "exon_class", "completeness", "phase_class"):
        strata[field] = {
            value: dict(Counter(row["status"] for row in rows if row[field] == value))
            for value in sorted({str(row[field]) for row in rows})
        }
    summary = {
        "total": len(rows), "counts": dict(counts),
        "mismatch_count": mismatch_count, "mismatch_rate": mismatch_rate,
        "raw_difference_count": raw_difference_count,
        "raw_difference_rate": raw_difference_count / len(rows),
        "unexplained_complete_mismatch_count": unexplained_complete_mismatch_count,
        "unexplained_partial_mismatch_count": unexplained_partial_mismatch_count,
        "max_mismatch_rate": args.max_mismatch_rate, "strata": strata,
    }
    required_coverage = {
        "positive_strand": any(row["strand"] == "+" for row in rows),
        "negative_strand": any(row["strand"] == "-" for row in rows),
        "partial_cds": any(row["completeness"] == "partial" for row in rows),
        "multi_exon_cds": any(row["exon_class"] == "multi_exon" for row in rows),
        "nonzero_leading_phase": any(row["phase_class"] == "nonzero" for row in rows),
    }
    coverage_failures = [name for name, present in required_coverage.items() if not present]
    summary["required_coverage"] = required_coverage
    summary["coverage_failures"] = coverage_failures
    summary["release_gate_passed"] = bool(
        not coverage_failures
        and mismatch_rate <= args.max_mismatch_rate
        and unexplained_complete_mismatch_count == 0
    )
    args.out_summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["release_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
