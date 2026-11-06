"""Small, interpretable confidence rubric for reconstructed proteins."""
from __future__ import annotations

from typing import Any, Mapping


def _true(row: Mapping[str, Any], *names: str) -> bool:
    return any(row.get(name) is True for name in names)


def score_protein_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return an auditable 0--100 score, tier, and contributing reasons.

    The score is deliberately a rubric rather than a probability. Missing
    optional experimental evidence is neutral, so older inputs remain usable.
    """
    impossible = str(row.get("region_class") or "") in {
        "sequence_extraction_failed", "canonical_sequence_extraction_failed",
        "no_cds_after_event", "noncoding_transcript", "no_transcript_overlap",
    } or not row.get("protein_sequence")
    severe_truncation = _true(row, "start_loss") and _true(row, "premature_stop")
    has_peptide = _true(
        row, "has_reference_unique_tryptic_peptide",
        "has_opposite_isoform_unique_tryptic_peptide",
        "ri_has_junction_spanning_searchable_peptide",
    )
    explicit_peptide_assessment = any(name in row for name in (
        "has_reference_unique_tryptic_peptide",
        "has_opposite_isoform_unique_tryptic_peptide",
        "ri_has_junction_spanning_searchable_peptide",
    ))
    if impossible or severe_truncation or (explicit_peptide_assessment and not has_peptide):
        reasons = []
        if impossible: reasons.append("impossible_translation_or_orf")
        if explicit_peptide_assessment and not has_peptide: reasons.append("no_unique_or_junction_peptide")
        if severe_truncation: reasons.append("severe_truncation")
        return {"confidence_score": 0, "confidence": "Rejected",
                "confidence_reasons": ";".join(reasons)}

    score, reasons = 20, []
    if _true(row, "inframe", "ri_orf_preserved") or row.get("frame_status") == "inframe":
        score += 20; reasons.append("frame_preserved")
    if int(row.get("transcript_candidate_count") or 0) > 0 and not _true(row, "transcript_selection_ambiguous"):
        score += 15; reasons.append("compatible_transcript")
    if row.get("premature_stop") is False:
        score += 15; reasons.append("no_premature_stop")
    if has_peptide:
        score += 20; reasons.append("unique_or_junction_peptide")
    psi = row.get("psi_max", row.get("psi_mean"))
    reads = row.get("inclusion_junction_reads")
    try:
        supported = (psi is not None and float(psi) > 0) or (reads is not None and int(reads) > 0)
    except (TypeError, ValueError):
        supported = False
    if supported:
        score += 10; reasons.append("psi_or_read_support")
    # FIX (2026-10-12): rMATS writes rescue products with tier "exploratory"; the
    # translation strategy identifies them regardless of the tier label.
    if (row.get("database_output_tier") in {"alternative_start", "exploratory_orf", "exploratory"}
            or row.get("translation_strategy") in {"alternative_start", "alternative_orf"}
            or _true(row, "start_loss")):
        score = min(score, 39); reasons.append("alternative_start_or_uncertain_orf")
    if row.get("cds_completeness") not in {None, "complete"}:
        score = min(score, 39); reasons.append("partial_cds")
    score = min(score, 100)
    tier = "High confidence" if score >= 80 else "Moderate" if score >= 50 else "Exploratory"
    return {"confidence_score": score, "confidence": tier,
            "confidence_reasons": ";".join(reasons) or "limited_evidence"}


def simplified_consequence(row: Mapping[str, Any]) -> str:
    """Map detailed diagnostics to one reader-facing biological category."""
    if not row.get("protein_sequence") or str(row.get("region_class") or "") in {
        "sequence_extraction_failed", "canonical_sequence_extraction_failed",
        "no_cds_after_event", "no_transcript_overlap",
    }:
        return "Ambiguous"
    if row.get("nmd_predicted") is True:
        return "NMD candidate"
    if row.get("premature_stop") is True:
        return "Premature stop"
    if row.get("frameshift") is True or str(row.get("frame_status") or "").lower() == "frameshift":
        return "Frameshift"
    if str(row.get("region_class") or "") == "cds_unchanged" or row.get("cds_delta_nt") == 0:
        return "Canonical"
    return "Altered protein"


def biological_evidence_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    """Produce the compact reader-facing evidence-table fields."""
    score = score_protein_evidence(row)
    unique = _true(row, "has_reference_unique_tryptic_peptide", "has_opposite_isoform_unique_tryptic_peptide")
    junction = _true(row, "ri_has_junction_spanning_searchable_peptide")
    return {
        "reading_frame": row.get("frame_status") or ("preserved" if _true(row, "inframe") else "altered" if _true(row, "frameshift") else None),
        "nmd": row.get("nmd_predicted"), "stop_gain": row.get("premature_stop"),
        "unique_peptide": unique, "junction_peptide": junction,
        "reference_peptide_overlap": not unique if any(k in row for k in ("has_reference_unique_tryptic_peptide", "has_opposite_isoform_unique_tryptic_peptide")) else None,
        "psi": row.get("psi_max", row.get("psi_mean")),
        "junction_reads": row.get("inclusion_junction_reads"),
        "inclusion_tier": row.get("database_output_tier"),
        "consequence_category": simplified_consequence(row), **score,
    }
