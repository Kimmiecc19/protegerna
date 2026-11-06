"""Producer-header contracts and reference-concordance release gates."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping


CONTRACT_VERSION = "pgdb-merge-input-v1"
PRODUCER_SOURCES = frozenset({"rmats", "suppa", "fusioninspector", "fusion"})


@dataclass(frozen=True)
class MergeInputContract:
    version: str = CONTRACT_VERSION
    required_fields: tuple[str, ...] = (
        "schema_version", "source", "record_type", "record_id", "event_type", "event_id",
        "annotation_release", "database_output_tier",
    )

    def violations(self, metadata: Mapping[str, str], inferred_source: str) -> tuple[str, ...]:
        source = str(metadata.get("source") or inferred_source).strip().lower()
        if source not in PRODUCER_SOURCES:
            return ()
        missing = tuple(field for field in self.required_fields if not str(metadata.get(field) or "").strip())
        declared = str(metadata.get("schema_version") or "").strip()
        problems = [f"missing:{field}" for field in missing]
        if declared and declared != self.version:
            problems.append(f"unsupported_schema_version:{declared}")
        return tuple(problems)

    def validate(self, metadata: Mapping[str, str], inferred_source: str) -> None:
        problems = self.violations(metadata, inferred_source)
        if problems:
            raise ValueError(
                f"merge input violates {self.version}: " + ";".join(problems)
            )


def preflight_producer_contract(source: str, annotation_release: str) -> None:
    """Fail at startup if a producer cannot satisfy the merge header contract."""
    MergeInputContract().validate({
        "schema_version": CONTRACT_VERSION, "source": source,
        "record_type": "protein", "record_id": "PREFLIGHT",
        "event_type": "PREFLIGHT", "event_id": "PREFLIGHT",
        "annotation_release": annotation_release,
        "database_output_tier": "primary",
    }, source)


REQUIRED_GENCODE_STRATA = frozenset({
    "positive_strand", "negative_strand", "partial_cds",
    "multi_exon_cds", "nonzero_leading_phase",
})


def validate_gencode_concordance_summary(path: str | Path) -> Mapping[str, Any]:
    """Require complete, mismatch-free validation of the matched reference release."""
    summary_path = Path(path)
    if not summary_path.is_file():
        raise FileNotFoundError(f"GENCODE concordance summary not found: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    coverage = summary.get("required_coverage") or {}
    missing = sorted(name for name in REQUIRED_GENCODE_STRATA if coverage.get(name) is not True)
    mismatch_rate = float(summary.get("mismatch_rate", 1.0))
    maximum = float(summary.get("max_mismatch_rate", 0.0))
    if missing or mismatch_rate > maximum:
        raise RuntimeError(
            "GENCODE concordance release gate failed: "
            f"missing_strata={missing}; mismatch_rate={mismatch_rate}; maximum={maximum}"
        )
    if int(summary.get("total", 0)) < 1:
        raise RuntimeError("GENCODE concordance release gate has no validated transcripts")
    fallback_unexplained = summary.get("mismatch_count", 0 if mismatch_rate <= maximum else 1)
    if int(summary.get("unexplained_complete_mismatch_count", fallback_unexplained)) != 0:
        raise RuntimeError("GENCODE concordance release gate has unexplained complete-CDS mismatches")
    return summary
