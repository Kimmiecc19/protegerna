"""Pure and read-only proteogenomic FASTA QC calculations."""
from __future__ import annotations
import math
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Optional, Sequence, Tuple
from .qc_models import FastaRecord, MetadataCounts, VALID_AA, STOP
from .qc_io import parse_fasta, read_tsv
from .splice_translation import digest_tryptic_records


def safe_int(value: Optional[str]) -> Optional[int]:
    if value in (None, "", "NA", "nan"):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None

def header_metadata_rows(records: Sequence[FastaRecord]) -> List[Dict[str, object]]:
    """Return one parsed metadata/QC row per FASTA record."""
    rows: List[Dict[str, object]] = []
    all_keys = set()
    parsed = []
    for rec in records:
        identifier, metadata = rec.identifier, rec.metadata
        all_keys.update(metadata)
        parsed.append((rec, identifier, metadata))

    preferred = [
        "source", "record_type", "record_id", "gene_symbol", "gene_id",
        "transcript", "protein_name", "event_type", "event_id", "event_ids", "variant",
        "mapping_count", "event_count", "gene_count", "transcript_count",
        "protein_length", "sequence_md5", "uniprot", "uniprotkb",
        "mapped_gene_symbol", "ensp", "mapped_ensg", "mapped_transcript_name",
        "annotation_status", "annotation_source", "annotation_release",
        "mapped_transcript_count", "unmapped_transcript_count",
        "mapped_transcripts", "unmapped_transcripts",
        "translation_strategy", "translation_strategies",
        "translation_note", "database_output_tier", "database_output_tiers",
        "has_reference_unique_tryptic_peptide",
        "reference_unique_tryptic_peptide_count", "protein_product_class",
        "protein_product_classes", "GN", "OS",
    ]
    ordered_keys = [key for key in preferred if key in all_keys]
    ordered_keys.extend(sorted(all_keys - set(ordered_keys)))

    for rec, identifier, metadata in parsed:
        expected_length = safe_int(metadata.get("protein_length"))
        expected_md5 = metadata.get("sequence_md5")
        observed_md5 = hashlib.md5(rec.sequence.encode("utf-8")).hexdigest()
        row: Dict[str, object] = {
            "source_label": rec.source_label,
            "source_file": rec.source_file,
            "record_ordinal": rec.ordinal,
            "header_identifier": identifier,
            "header_field_count": len(metadata),
            "header_has_key_value_metadata": bool(metadata),
            "observed_sequence_length": len(rec.sequence),
            "header_length_matches_sequence": (
                None if expected_length is None else expected_length == len(rec.sequence)
            ),
            "observed_sequence_md5": observed_md5,
            "header_md5_matches_sequence": (
                None if not expected_md5 else expected_md5.lower() == observed_md5.lower()
            ),
        }
        row.update({key: metadata.get(key, "") for key in ordered_keys})
        rows.append(row)
    return rows

def header_metadata_summary_rows(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Summarise final FASTA composition from parsed PGDB header fields."""
    output: List[Dict[str, object]] = []
    categorical_fields = [
        "source", "record_type", "event_type", "variant", "annotation_status",
        "annotation_source", "annotation_release", "translation_strategy",
        "translation_strategies", "database_output_tier", "database_output_tiers",
        "protein_product_class", "protein_product_classes",
    ]
    for field in categorical_fields:
        counts = Counter(
            str(row.get(field, "")).strip() or "MISSING"
            for row in rows
        )
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            output.append({
                "summary_type": "categorical_count",
                "field": field,
                "value": value,
                "count": count,
                "statistic": "",
            })

    for field in [
        "mapping_count", "event_count", "gene_count", "transcript_count",
        "mapped_transcript_count", "unmapped_transcript_count",
    ]:
        values = [safe_int(str(row.get(field, ""))) for row in rows]
        values = [value for value in values if value is not None]
        if not values:
            continue
        for statistic, value in [
            ("n_nonmissing", len(values)),
            ("min", min(values)),
            ("median", median(values)),
            ("mean", round(mean(values), 3)),
            ("max", max(values)),
            ("sum", sum(values)),
        ]:
            output.append({
                "summary_type": "numeric_summary",
                "field": field,
                "value": "",
                "count": "",
                "statistic": f"{statistic}={value}",
            })

    for field in ["header_length_matches_sequence", "header_md5_matches_sequence"]:
        counts = Counter(str(row.get(field)) for row in rows)
        for value, count in sorted(counts.items()):
            output.append({
                "summary_type": "header_consistency",
                "field": field,
                "value": value,
                "count": count,
                "statistic": "",
            })
    return output

def quantms_database_validation(
    records: Sequence[FastaRecord],
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    """Validate a final target-only protein FASTA for quantms/DIA-NN submission."""
    parsed = [(rec, rec.identifier, rec.metadata) for rec in records]
    accession_counts = Counter(identifier for _, identifier, _ in parsed)
    sequence_counts = Counter(rec.sequence for rec in records)
    rows: List[Dict[str, object]] = []

    decoy_re = re.compile(r"^(?:REV_|REVERSE_|DECOY_|XXX_)", re.IGNORECASE)
    rescue_re = re.compile(r"(?:alternative_start|exploratory_orf)", re.IGNORECASE)

    for rec, identifier, metadata in parsed:
        source = str(metadata.get("source", "")).lower()
        record_type = str(metadata.get("record_type", "protein")).lower()
        gene_symbol = (
            metadata.get("GN")
            or metadata.get("mapped_gene_symbol")
            or metadata.get("gene_symbol")
            or ""
        )
        organism = metadata.get("OS", "")
        tiers = " ".join([
            str(metadata.get("database_output_tier", "")),
            str(metadata.get("database_output_tiers", "")),
        ])
        is_contaminant = any(token in source for token in ("crap", "contaminant"))
        reasons: List[str] = []
        warnings: List[str] = []
        if not identifier or identifier in {"PGDB", "NA"}:
            reasons.append("missing_or_invalid_accession")
        if accession_counts[identifier] > 1:
            reasons.append("duplicate_accession")
        if sequence_counts[rec.sequence] > 1:
            reasons.append("duplicate_exact_protein_sequence")
        if decoy_re.search(identifier) or "decoy" in source:
            reasons.append("input_contains_decoy")
        if record_type != "protein":
            reasons.append("nonprotein_record")
        if not rec.sequence:
            reasons.append("empty_sequence")
        if invalid_characters(rec.sequence):
            reasons.append("invalid_amino_acid")
        if internal_stop_count(rec.sequence) > 0 or has_terminal_stop(rec.sequence):
            reasons.append("stop_character_present")
        if rescue_re.search(tiers):
            reasons.append("rescue_tier_in_primary_database")
        gene_missing = str(gene_symbol).strip().upper() in {"", "NA", "N/A", "NONE", "NULL", "."}
        organism_missing = str(organism).strip().upper() in {"", "NA", "N/A", "NONE", "NULL", "."}
        if not is_contaminant and gene_missing:
            # A gene symbol is useful for interpretation, but neither quantms nor
            # DIA-NN requires one to identify and quantify a valid protein entry.
            # Some legitimate UniProt records have no GN annotation, so report
            # this as an auditable annotation warning rather than rejecting the
            # search database.
            warnings.append("missing_gene_symbol")
        if not is_contaminant and organism_missing:
            reasons.append("missing_organism")
        rows.append({
            "source_label": rec.source_label,
            "source_file": rec.source_file,
            "record_ordinal": rec.ordinal,
            "accession": identifier,
            "source": source,
            "record_type": record_type,
            "gene_symbol": gene_symbol,
            "organism": organism,
            "database_output_tiers": tiers.strip(),
            "sequence_hash": rec.sequence_hash,
            "quantms_ready": not reasons,
            "validation_reasons": ";".join(reasons),
            "validation_warnings": ";".join(warnings),
        })

    reason_counts = Counter(
        reason
        for row in rows
        for reason in str(row["validation_reasons"]).split(";")
        if reason
    )
    warning_counts = Counter(
        warning
        for row in rows
        for warning in str(row["validation_warnings"]).split(";")
        if warning
    )
    summary = [
        {"metric": "records_checked", "value": len(rows)},
        {"metric": "records_passing", "value": sum(bool(row["quantms_ready"]) for row in rows)},
        {"metric": "records_failing", "value": sum(not bool(row["quantms_ready"]) for row in rows)},
    ]
    summary.extend(
        {"metric": f"failure:{reason}", "value": count}
        for reason, count in sorted(reason_counts.items())
    )
    summary.extend(
        {"metric": f"warning:{warning}", "value": count}
        for warning, count in sorted(warning_counts.items())
    )
    return rows, summary

def invalid_characters(seq: str) -> str:
    chars = sorted({aa for aa in seq.upper() if aa not in VALID_AA})
    return "".join(chars)

def internal_stop_count(seq: str) -> int:
    """Count internal stops, excluding a single terminal stop if present."""
    if not seq:
        return 0
    body = seq[:-1] if seq.endswith(STOP) else seq
    return body.count(STOP)

def has_terminal_stop(seq: str) -> bool:
    return bool(seq) and seq.endswith(STOP)

def digest_tryptic_peptides(
    protein_sequence: str,
    max_missed_cleavages: int = 2,
    min_len: int = 7,
    max_len: int = 40,
) -> List[Tuple[str, int, int, int]]:
    """Return tryptic peptides as (sequence, start_aa, end_aa, missed_cleavages).

    Trypsin cleaves after K/R unless followed by P. Stop codons split the protein into independent segments.
    Coordinates are 1-based within the original protein sequence after removing stop separators.
    """
    return [
        (row["peptide_sequence"], row["peptide_start_aa"],
         row["peptide_end_aa"], row["missed_cleavages"])
        for row in digest_tryptic_records(
            protein_sequence, max_missed_cleavages, min_len, max_len
        )
    ]

def build_reference_peptide_set(
    reference_proteome: Path,
    max_missed_cleavages: int,
    min_len: int,
    max_len: int,
) -> set:
    peptide_set = set()
    for rec in parse_fasta(reference_proteome, "reference"):
        for pep, _, _, _ in digest_tryptic_peptides(rec.sequence, max_missed_cleavages, min_len, max_len):
            peptide_set.add(pep)
    return peptide_set

def length_distribution_rows(records: Sequence[FastaRecord]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    grouped: Dict[str, List[int]] = defaultdict(list)
    for rec in records:
        grouped[rec.source_label].append(len(rec.sequence))
    grouped["ALL"] = [len(r.sequence) for r in records]

    for label, lengths in grouped.items():
        if not lengths:
            rows.append({
                "source_label": label,
                "n_sequences": 0,
                "min_len": None,
                "q1_len": None,
                "median_len": None,
                "mean_len": None,
                "q3_len": None,
                "max_len": None,
                "n_lt_7aa": 0,
                "n_lt_30aa": 0,
                "n_ge_30aa": 0,
                "n_ge_100aa": 0,
            })
            continue
        sorted_lengths = sorted(lengths)
        rows.append({
            "source_label": label,
            "n_sequences": len(lengths),
            "min_len": min(lengths),
            "q1_len": quantile(sorted_lengths, 0.25),
            "median_len": median(lengths),
            "mean_len": round(mean(lengths), 3),
            "q3_len": quantile(sorted_lengths, 0.75),
            "max_len": max(lengths),
            "n_lt_7aa": sum(x < 7 for x in lengths),
            "n_lt_30aa": sum(x < 30 for x in lengths),
            "n_ge_30aa": sum(x >= 30 for x in lengths),
            "n_ge_100aa": sum(x >= 100 for x in lengths),
        })
    return rows

def quantile(sorted_values: Sequence[int], q: float) -> float:
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_values[lo])
    frac = pos - lo
    return round(sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac, 3)

def sequence_qc(records: Sequence[FastaRecord]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    header_counts = Counter((rec.source_label, rec.header) for rec in records)
    global_header_counts = Counter(rec.header for rec in records)
    seq_counts_by_source = Counter((rec.source_label, rec.sequence) for rec in records)
    global_seq_counts = Counter(rec.sequence for rec in records)

    sequence_rows: List[Dict[str, object]] = []
    for rec in records:
        bad_chars = invalid_characters(rec.sequence)
        row = {
            "source_label": rec.source_label,
            "source_file": rec.source_file,
            "record_ordinal": rec.ordinal,
            "header": rec.header,
            "sequence_hash": rec.sequence_hash,
            "sequence_length": len(rec.sequence),
            "is_empty_sequence": len(rec.sequence) == 0,
            "invalid_aa_characters": bad_chars,
            "has_invalid_aa": bool(bad_chars),
            "has_terminal_stop": has_terminal_stop(rec.sequence),
            "internal_stop_count": internal_stop_count(rec.sequence),
            "has_internal_stop": internal_stop_count(rec.sequence) > 0,
            "duplicate_header_within_source": header_counts[(rec.source_label, rec.header)] > 1,
            "duplicate_header_global": global_header_counts[rec.header] > 1,
            "duplicate_sequence_within_source": seq_counts_by_source[(rec.source_label, rec.sequence)] > 1,
            "duplicate_sequence_global": global_seq_counts[rec.sequence] > 1,
        }
        sequence_rows.append(row)

    duplicate_sequence_rows: List[Dict[str, object]] = []
    seq_to_records: Dict[Tuple[str, str], List[FastaRecord]] = defaultdict(list)
    for rec in records:
        seq_to_records[(rec.source_label, rec.sequence)].append(rec)

    duplicate_sequence_rows.extend(
        {
            "source_label": label,
            "sequence_hash": hashlib.sha256(seq.encode("utf-8")).hexdigest(),
            "sequence_length": len(seq),
            "duplicate_count": len(recs),
            "headers": "|".join(r.header for r in recs),
            "source_files": "|".join(sorted({r.source_file for r in recs})),
        }
        for (label, seq), recs in seq_to_records.items()
        if len(recs) > 1
    )
    summary_rows: List[Dict[str, object]] = []
    for label in sorted({rec.source_label for rec in records} | {"ALL"}):
        subset = records if label == "ALL" else [rec for rec in records if rec.source_label == label]
        if not subset:
            continue
        subset_headers = [rec.header for rec in subset]
        subset_seqs = [rec.sequence for rec in subset]
        subset_qc = [row for row in sequence_rows if label == "ALL" or row["source_label"] == label]
        summary_rows.append({
            "source_label": label,
            "n_records": len(subset),
            "n_unique_headers": len(set(subset_headers)),
            "n_duplicate_header_records": sum(bool(row["duplicate_header_within_source"] if label != "ALL" else row["duplicate_header_global"]) for row in subset_qc),
            "n_unique_sequences": len(set(subset_seqs)),
            "n_duplicate_sequence_records": sum(bool(row["duplicate_sequence_within_source"] if label != "ALL" else row["duplicate_sequence_global"]) for row in subset_qc),
            "n_empty_sequences": sum(bool(row["is_empty_sequence"]) for row in subset_qc),
            "n_invalid_aa_sequences": sum(bool(row["has_invalid_aa"]) for row in subset_qc),
            "n_terminal_stop_sequences": sum(bool(row["has_terminal_stop"]) for row in subset_qc),
            "n_internal_stop_sequences": sum(bool(row["has_internal_stop"]) for row in subset_qc),
            "total_internal_stop_codons": sum(int(row["internal_stop_count"]) for row in subset_qc),
        })

    return sequence_rows, duplicate_sequence_rows, summary_rows

def add_peptide_eligibility(
    records: Sequence[FastaRecord],
    sequence_rows: List[Dict[str, object]],
    summary_rows: List[Dict[str, object]],
    max_missed_cleavages: int,
    min_len: int,
    max_len: int,
) -> None:
    """Add theoretical digest eligibility to per-record and aggregate QC rows."""
    eligibility_by_key: Dict[Tuple[str, int], Tuple[int, bool]] = {}

    for rec in records:
        peptides = digest_tryptic_peptides(
            rec.sequence,
            max_missed_cleavages=max_missed_cleavages,
            min_len=min_len,
            max_len=max_len,
        )
        unique_peptides = {peptide for peptide, _, _, _ in peptides}
        eligibility_by_key[(rec.source_label, rec.ordinal)] = (
            len(unique_peptides),
            bool(unique_peptides),
        )

    for row in sequence_rows:
        n_peptides, eligible = eligibility_by_key[(
            str(row["source_label"]),
            int(row["record_ordinal"]),
        )]
        row["n_eligible_tryptic_peptides"] = n_peptides
        row["has_eligible_tryptic_peptide"] = eligible

    for summary in summary_rows:
        label = str(summary["source_label"])
        subset = records if label == "ALL" else [
            rec for rec in records if rec.source_label == label
        ]
        eligibility = [
            eligibility_by_key[(rec.source_label, rec.ordinal)][1]
            for rec in subset
        ]
        summary["total_residues"] = sum(len(rec.sequence) for rec in subset)
        summary["n_proteins_shorter_than_min_peptide"] = sum(
            len(rec.sequence) < min_len for rec in subset
        )
        summary["n_proteins_with_eligible_peptide"] = sum(eligibility)
        summary["n_proteins_without_eligible_peptide"] = len(eligibility) - sum(eligibility)
        summary["pct_proteins_with_eligible_peptide"] = round(
            100.0 * sum(eligibility) / len(eligibility), 3
        ) if eligibility else 0.0

def truthy(value: object) -> Optional[bool]:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "t", "1", "yes", "y"}:
        return True
    return False if text in {"false", "f", "0", "no", "n"} else None

def first_present(row: Dict[str, str], candidates: Sequence[str]) -> Optional[str]:
    return next(
        (
            row[col]
            for col in candidates
            if col in row and row[col] not in (None, "", "NA", "nan")
        ),
        None,
    )

def _summarise_metadata_rows(rows: List[Dict[str, str]]) -> MetadataCounts:
    """Summarise a single metadata TSV into counters.

    Extracted from metadata_summary to reduce nesting and keep the main
    function focused on I/O and high-level aggregation.
    """
    counts = MetadataCounts()

    for row in rows:
        if frame := first_present(row, ["frame_status", "frame", "frame_class"]):
            counts.frame_statuses[str(frame).upper()] += 1

        premature = first_present(row, ["premature_stop", "has_premature_stop", "early_stop_after_junction"])
        if premature is not None:
            val = truthy(premature)
            counts.premature_stops[str(val if val is not None else premature)] += 1

        nmd = first_present(row, ["nmd_predicted"])
        if nmd is not None:
            val = truthy(nmd)
            counts.nmd_predictions[str(val if val is not None else nmd)] += 1

        start_loss = first_present(row, [
            "start_loss", "start_lost", "start_loss_relative_to_own_annotation"
        ])
        if start_loss is not None:
            val = truthy(start_loss)
            counts.start_losses[str(val if val is not None else start_loss)] += 1

        ri_orf = first_present(row, ["ri_orf_preserved", "retained_intron_orf_preserved"])
        if ri_orf is not None:
            val = truthy(ri_orf)
            counts.retained_intron_orfs[str(val if val is not None else ri_orf)] += 1

        for candidates, counter in (
            (["frame_mismatch"], counts.frame_mismatches),
            (["ri_boundary_fallback"], counts.ri_boundary_fallbacks),
            (["symbol_coordinate_gene_id_collision"], counts.fusion_gene_id_collisions),
        ):
            audit_value = first_present(row, candidates)
            if audit_value is not None:
                parsed = truthy(audit_value)
                counter[str(parsed if parsed is not None else audit_value)] += 1

        caller_count = first_present(row, ["contributing_caller_count"])
        if caller_count is not None:
            counts.contributing_caller_counts[str(caller_count)] += 1

        consequence = " ".join(str(v).lower() for v in row.values() if v is not None)
        if "utr" in consequence or "noncoding" in consequence or "no_cds" in consequence:
            counts.utr_or_noncoding["utr_or_noncoding_flagged"] += 1

    return counts

def metadata_summary(metadata_paths: Sequence[Path], labels: Optional[Sequence[str]]) -> List[Dict[str, object]]:
    rows_out: List[Dict[str, object]] = []
    if labels and len(labels) not in {0, len(metadata_paths)}:
        # Metadata labels can differ from FASTA labels. This uses metadata path stem if not one-to-one.
        labels = None

    for i, path in enumerate(metadata_paths):
        if not path.exists():
            raise FileNotFoundError(f"Metadata TSV not found: {path}")
        label = labels[i] if labels and i < len(labels) else path.stem
        rows = read_tsv(path)
        if not rows:
            rows_out.append({"metadata_label": label, "metadata_file": str(path), "n_rows": 0})
            continue

        counts = _summarise_metadata_rows(rows)

        rows_out.append({
            "metadata_label": label,
            "metadata_file": str(path),
            "n_rows": len(rows),
            "frame_status_counts": counter_to_string(counts.frame_statuses),
            "premature_stop_counts": counter_to_string(counts.premature_stops),
            "nmd_predicted_counts": counter_to_string(counts.nmd_predictions),
            "start_loss_counts": counter_to_string(counts.start_losses),
            "ri_orf_preserved_counts": counter_to_string(counts.retained_intron_orfs),
            "frame_mismatch_counts": counter_to_string(counts.frame_mismatches),
            "ri_boundary_fallback_counts": counter_to_string(counts.ri_boundary_fallbacks),
            "fusion_gene_id_collision_counts": counter_to_string(counts.fusion_gene_id_collisions),
            "contributing_caller_count_distribution": counter_to_string(
                counts.contributing_caller_counts
            ),
            "utr_or_noncoding_rows_detected": counts.utr_or_noncoding.get("utr_or_noncoding_flagged", 0),
        })

    return rows_out

def counter_to_string(counter: Counter) -> str:
    if not counter:
        return ""
    return ";".join(f"{key}:{counter[key]}" for key in sorted(counter))

def peptide_uniqueness_rows(
    records: Sequence[FastaRecord],
    reference_peptide_set: set,
    max_missed_cleavages: int,
    min_len: int,
    max_len: int,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for rec in records:
        peptides = digest_tryptic_peptides(rec.sequence, max_missed_cleavages, min_len, max_len)
        peptide_seqs = sorted({p[0] for p in peptides})
        unique_peps = sorted([p for p in peptide_seqs if p not in reference_peptide_set])
        rows.append({
            "source_label": rec.source_label,
            "source_file": rec.source_file,
            "header": rec.header,
            "sequence_hash": rec.sequence_hash,
            "sequence_length": len(rec.sequence),
            "n_tryptic_peptides": len(peptide_seqs),
            "n_reference_unique_tryptic_peptides": len(unique_peps),
            "has_reference_unique_tryptic_peptide": len(unique_peps) > 0,
            "reference_unique_tryptic_peptides": "|".join(unique_peps),
        })
    return rows
