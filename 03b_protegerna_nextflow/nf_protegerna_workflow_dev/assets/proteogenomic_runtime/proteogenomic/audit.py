"""Stable decision codes and typed failure accounting for auditable runs."""
from __future__ import annotations
import json, re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping

OBSERVATION_FIELDS = (
    "frame_status", "nmd_predicted", "cds_completeness", "region_class",
    "protein_product_class", "translation_strategy", "has_junction_spanning_peptide",
    "has_unique_junction_peptide", "has_reference_unique_tryptic_peptide",
    "transcript_selection_ambiguous", "transcript_candidate_count",
)
POLICY_FIELDS = (
    "protein_in_fasta", "database_output_tier", "exclude_incomplete_cds",
    "require_unique_event_peptide", "quantms_conservative",
)

def exclusion_code(reason: object) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", str(reason or "").strip().upper()).strip("_")
    return f"PGDB_EXCL_{token}" if token else "NA"

def exclusion_codes(reasons: object) -> str:
    values = [exclusion_code(item) for item in str(reasons or "").split(";") if item.strip()]
    return ";".join(values) if values else "NA"

def audit_fields(row: Mapping[str, Any], reason_field: str = "fasta_exclusion_reasons") -> dict[str, str]:
    reasons = row.get(reason_field)
    observations = {key: row.get(key) for key in OBSERVATION_FIELDS if key in row}
    decisions = {key: row.get(key) for key in POLICY_FIELDS if key in row}
    decisions["exclusion_reasons"] = reasons
    return {
        "exclusion_reason_codes": exclusion_codes(reasons),
        "biological_observations_json": json.dumps(observations, sort_keys=True, default=str),
        "policy_decisions_json": json.dumps(decisions, sort_keys=True, default=str),
    }


@dataclass
class FailureLedger:
    """Count attempted, successful, and failed records without hiding failures."""

    attempted: int = 0
    succeeded: int = 0
    failures: Counter[str] = field(default_factory=Counter)

    def record_attempt(self) -> None:
        self.attempted += 1

    def record_success(self) -> None:
        self.succeeded += 1

    def record_failure(self, reason: str) -> None:
        self.failures[str(reason or "unknown_failure")] += 1

    @property
    def failure_count(self) -> int:
        return sum(self.failures.values())


    def to_dict(self) -> dict[str, object]:
        return {
            "attempted": self.attempted,
            "succeeded": self.succeeded,
            "failure_count": self.failure_count,
            "failure_reasons": dict(self.failures),
        }
