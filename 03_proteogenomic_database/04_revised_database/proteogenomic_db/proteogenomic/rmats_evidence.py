"""rMATS statistical and junction-read evidence evaluation."""
from __future__ import annotations
from typing import Dict, Optional, Tuple
import pandas as pd
import logging
from collections import defaultdict
from pathlib import Path
from .rmats_parsing import _safe_int
from .splice_reconstruction_core import genome_to_transcript
from .splice_translation import (
    add_protein_mapping, append_reason, digest_tryptic_peptides,
    digest_tryptic_records, merge_intervals, subtract_interval_list,
)


def _safe_float(value) -> Optional[float]:
    """Return a finite float from an rMATS scalar, otherwise ``None``."""
    try:
        if pd.isna(value):
            return None
        result = float(value)
        return result if pd.notna(result) else None
    except (TypeError, ValueError):
        return None


def _sum_rmats_counts(value) -> int:
    """Sum a comma-separated rMATS junction-count field, ignoring missing cells."""
    if value is None or pd.isna(value):
        return 0
    total = 0
    for token in str(value).split(","):
        parsed = _safe_int(token.strip())
        if parsed is not None and parsed >= 0:
            total += parsed
    return total


def evaluate_rmats_event(row: dict, args) -> Tuple[bool, Dict]:
    """Apply optional rMATS statistical and junction-evidence filters."""
    fdr = _safe_float(row.get("FDR"))
    inc_delta = _safe_float(row.get("IncLevelDifference"))
    inclusion_reads = sum(
        _sum_rmats_counts(row.get(column))
        for column in ("IJC_SAMPLE_1", "IJC_SAMPLE_2")
    )
    skipping_reads = sum(
        _sum_rmats_counts(row.get(column))
        for column in ("SJC_SAMPLE_1", "SJC_SAMPLE_2")
    )

    reasons = []
    if args.max_fdr is not None and (fdr is None or fdr > args.max_fdr):
        reasons.append("fdr_missing_or_above_threshold")
    if (
        args.min_abs_inc_level_difference is not None
        and (inc_delta is None or abs(inc_delta) < args.min_abs_inc_level_difference)
    ):
        reasons.append("inc_level_difference_missing_or_below_threshold")
    if args.min_inclusion_junction_reads is not None and inclusion_reads < args.min_inclusion_junction_reads:
        reasons.append("insufficient_inclusion_junction_reads")
    if args.min_skipping_junction_reads is not None and skipping_reads < args.min_skipping_junction_reads:
        reasons.append("insufficient_skipping_junction_reads")

    keep = not reasons
    return keep, {
        "event_filter_applied": any(
            value is not None
            for value in (
                args.max_fdr,
                args.min_abs_inc_level_difference,
                args.min_inclusion_junction_reads,
                args.min_skipping_junction_reads,
            )
        ),
        "fdr": fdr,
        "max_fdr": args.max_fdr,
        "inc_level_difference": inc_delta,
        "min_abs_inc_level_difference": args.min_abs_inc_level_difference,
        "inclusion_junction_reads": inclusion_reads,
        "skipping_junction_reads": skipping_reads,
        "min_inclusion_junction_reads": args.min_inclusion_junction_reads,
        "min_skipping_junction_reads": args.min_skipping_junction_reads,
        "passed_filter": keep,
        "reason": "passed_rmats_filter" if keep else ";".join(reasons),
    }


# Retained-intron and final event-level evidence
def retained_intron_evidence(
    tx_model, cds_segments, protein_sequence, trim, rowd, sequence_cache, args
):
    """Return conservative, auditable RI sequence/read/export evidence."""
    if not protein_sequence:
        return {}
    inserted = [(int(s), int(e)) for s, e, _phase in cds_segments]
    for start, end, _phase in tx_model.get("cds", []):
        next_intervals = []
        for left, right in inserted:
            next_intervals.extend(subtract_interval_list([(left, right)], int(start), int(end)))
        inserted = next_intervals
    inserted = merge_intervals(inserted)
    config = args.reconstruction_config
    inclusion_reads = sum(_sum_rmats_counts(rowd.get(column)) for column in ("IJC_SAMPLE_1", "IJC_SAMPLE_2"))
    read_supported = inclusion_reads >= config.min_ri_inclusion_reads

    altered_intervals = [(int(s), int(e)) for s, e, _ in cds_segments]
    boundaries = []
    ambiguous = 0
    stop_count = 0
    for start, end in inserted:
        genomic_tx_start = end if tx_model.get("strand") == "-" else start
        cursor = genome_to_transcript(
            altered_intervals, tx_model.get("strand"), genomic_tx_start
        ) - int(trim or 0)
        if cursor >= 0:
            boundaries.append(cursor // 3)
        intron_seq = (sequence_cache.extract(
            tx_model["chrom"], [(start, end)], tx_model["strand"]
        ) or "").upper()
        ambiguous += sum(base not in {"A", "C", "G", "T"} for base in intron_seq)
        frame_skip = (-cursor) % 3
        stop_count += sum(
            intron_seq[index:index + 3] in {"TAA", "TAG", "TGA"}
            for index in range(frame_skip, max(len(intron_seq) - 2, frame_skip), 3)
        )
    peptide_records = digest_tryptic_records(
        protein_sequence, config.max_missed_cleavages,
        config.min_database_peptide_length, config.max_database_peptide_length,
    )
    junction_searchable = any(
        int(record["peptide_start_aa"]) - 1 < boundary < int(record["peptide_end_aa"])
        for boundary in boundaries for record in peptide_records
    )
    export_plausibility = (
        "unlikely_nuclear_retained_or_nmd" if stop_count or not junction_searchable
        else "plausible_exported_candidate"
    )
    return {
        "ri_read_evidence_supported": read_supported,
        "ri_inclusion_junction_reads": inclusion_reads,
        "ri_ambiguous_base_count": ambiguous,
        "ri_intronic_stop_count": stop_count,
        "ri_export_plausibility": export_plausibility,
        "ri_has_junction_spanning_searchable_peptide": junction_searchable,
    }

def write_event_summary(rows, out_path):
    """Write one auditable filtering/reconstruction record per rMATS input row."""
    if not out_path:
        return
    df = pd.DataFrame(rows or [])
    df.to_csv(out_path, sep="\t", index=False, lineterminator="\n")
    passed = int(df.get("passed_filter", pd.Series(dtype=bool)).fillna(False).sum()) if not df.empty else 0
    logging.info("Wrote rMATS event summary to %s (%d events; %d passed)", out_path, len(df), passed)

def count_event_rows(path: Path) -> Optional[int]:
    """Count data rows for progress reporting without retaining the file."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except OSError:
        return None

def finish_event_summary(summary, status, generated, reconstruction_status):
    """Attach reconstruction outcome fields to an event audit record."""
    summary.update({
        "event_processing_status": status,
        "consequence_rows_generated": generated,
        "reconstruction_status": reconstruction_status,
    })
    return summary

def finalise_primary_event_peptide_evidence(consequence_rows, prot_info, args):
    """Compare paired rMATS isoforms and rebuild the conservative primary FASTA."""
    groups = defaultdict(list)
    for row in consequence_rows:
        key = (row.get("source_file"), row.get("event_type"), row.get("event_id"), row.get("tx"))
        groups[key].append(row)

    for rows in groups.values():
        peptide_cache = {}
        for row in rows:
            protein = row.get("protein_sequence")
            if protein:
                peptide_cache[id(row)] = digest_tryptic_peptides(
                    protein, args.max_missed_cleavages,
                    args.min_database_peptide_length, args.max_database_peptide_length,
                )

        for row in rows:
            protein = row.get("protein_sequence")
            if not protein:
                row["has_opposite_isoform_unique_tryptic_peptide"] = None
                row["opposite_isoform_unique_tryptic_peptide_count"] = 0
                row["frame_comparison_basis"] = "no_translated_candidate"
                continue

            opposite_rows = [
                other for other in rows
                if other is not row and other.get("variant") != row.get("variant")
                and other.get("protein_sequence")
            ]
            opposite_peptides = set()
            for other in opposite_rows:
                opposite_peptides.update(peptide_cache.get(id(other), set()))

            if opposite_rows:
                event_unique_count = len(peptide_cache.get(id(row), set()) - opposite_peptides)
                has_event_unique = event_unique_count > 0
                comparison_basis = "paired_rmats_isoform_same_annotated_transcript"
                comparison_variants = ",".join(sorted({str(x.get("variant")) for x in opposite_rows}))
            else:
                event_unique_count = 0
                has_event_unique = None
                comparison_basis = "no_opposite_translated_isoform"
                comparison_variants = None

            row["has_opposite_isoform_unique_tryptic_peptide"] = has_event_unique
            row["opposite_isoform_unique_tryptic_peptide_count"] = event_unique_count
            row["frame_comparison_basis"] = comparison_basis
            row["frame_comparison_variant"] = comparison_variants

            if (row.get("database_output_tier") in {"primary", "primary_dia"}
                    and args.require_unique_event_peptide and has_event_unique is not True):
                row["fasta_exclusion_reasons"] = append_reason(
                    row.get("fasta_exclusion_reasons"),
                    "no_opposite_isoform_unique_tryptic_peptide",
                )
                if not getattr(args, "include_failed_filter_proteins", False):
                    row["database_output_tier"] = "excluded"
                    row["protein_in_fasta"] = False

    # Provisional mappings were collected before both isoforms were available.
    prot_info.clear()
    for row in consequence_rows:
        if row.get("database_output_tier") not in {"primary", "primary_dia"} or row.get("protein_in_fasta") is not True:
            continue
        protein = row.get("protein_sequence")
        if not protein:
            continue
        add_protein_mapping(prot_info, protein, {
            "source_file": Path(str(row.get("source_file", "NA"))).name,
            "sample_id": row.get("sample_id", "NA"),
            "batch": row.get("batch", "NA"),
            "condition": row.get("condition", "NA"),
            "organism": row.get("organism", args.organism),
            "annotation_release": row.get("annotation_release", args.annotation_release),
            "gene_id": row.get("gene_id"), "gene_symbol": row.get("gene_symbol"),
            "tx": row.get("tx"), "event_type": row.get("event_type"),
            "event_id": row.get("event_id"), "variant": row.get("variant"),
            "translation_strategy": row.get("translation_strategy"),
            "translation_note": row.get("translation_note"),
            "database_output_tier": "primary_dia",
            "fasta_exclusion_reasons": row.get("fasta_exclusion_reasons"),
            "passed_dia_filters": not bool(row.get("fasta_exclusion_reasons")),
            "transcript_selection_score": row.get("transcript_selection_score"),
            "transcript_selection_rank": row.get("transcript_selection_rank"),
            "transcript_candidate_count": row.get("transcript_candidate_count"),
            "transcript_selection_ambiguous": row.get("transcript_selection_ambiguous"),
        })
