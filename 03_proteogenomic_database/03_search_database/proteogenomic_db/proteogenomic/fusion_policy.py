"""Separate biological reconstructability from database-retention policy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text.lower() in {"na", "nan", "none", "."} else text


def _bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower() if value is not None else ""
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


@dataclass(frozen=True)
class BiologicalEligibility:
    eligible: bool
    reasons: tuple[str, ...]


def assess_biological_eligibility(row: Mapping[str, Any]) -> BiologicalEligibility:
    """Assess whether reconstruction produced an interpretable protein candidate."""
    reasons: list[str] = []
    if _bool(row.get("low_confidence")) is True:
        reasons.append("low_confidence_reconstruction")
    if _text(row.get("frame_status")) == "NA":
        reasons.append("unknown_frame")
    if _bool(row.get("orientation_pass")) is False:
        reasons.append("orientation_or_splice_support_failed")
    if not _text(row.get("protein_sequence")):
        reasons.append("missing_protein_sequence")
    if _bool(row.get("donor_stop_codon_readthrough")) is True or _bool(row.get("acceptor_stop_codon_readthrough")) is True:
        reasons.append("annotated_stop_codon_readthrough_not_reconstructed")
    if int(row.get("donor_selenocysteine_feature_count") or 0) > 0 or int(row.get("acceptor_selenocysteine_feature_count") or 0) > 0:
        reasons.append("annotated_selenocysteine_not_supported_for_fusion_cds")
    donor_chrom = str(row.get("chrom1") or "").upper().removeprefix("CHR")
    acceptor_chrom = str(row.get("chrom2") or "").upper().removeprefix("CHR")
    if donor_chrom in {"M", "MT"} or acceptor_chrom in {"M", "MT"}:
        reasons.append("mitochondrial_nuclear_fusion_translation_not_supported")
    return BiologicalEligibility(not reasons, tuple(reasons))
