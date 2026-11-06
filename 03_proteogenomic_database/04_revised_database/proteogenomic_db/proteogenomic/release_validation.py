"""Producer-header contracts and reference-concordance release gates."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


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


BOUND_REFERENCE_INPUTS = ("gtf_db", "genome")


def producer_manifest_path(fasta: str | Path) -> Path:
    """Producers write ``<output FASTA>.run_config.json`` beside each FASTA."""
    return Path(f"{fasta}.run_config.json")


def check_concordance_binding(
    summary: Mapping[str, Any],
    annotation_release: str,
    producer_fastas: Iterable[str | Path] = (),
) -> dict[str, list[str]]:
    """Require the concordance summary to describe the release being merged.

    The summary must name the same ``annotation_release`` as the merge, and
    every producer FASTA that has a run manifest must have been generated from
    the same annotation release and from byte-identical ``gtf_db``/``genome``
    inputs (by SHA-256) as the validation run. Returns the FASTAs that were
    checked and those without a producer manifest.
    """
    reference = summary.get("reference")
    if not isinstance(reference, Mapping):
        raise RuntimeError(
            "GENCODE concordance summary does not identify its reference inputs; "
            "rerun validate_gencode_translation.py with --annotation_release"
        )
    validated_release = str(reference.get("annotation_release") or "").strip()
    if validated_release != str(annotation_release).strip():
        raise RuntimeError(
            "GENCODE concordance summary was produced for annotation release "
            f"'{validated_release}', not the merged release '{annotation_release}'"
        )
    expected = {}
    for name in BOUND_REFERENCE_INPUTS:
        entry = reference.get(name)
        if not isinstance(entry, Mapping) or not entry.get("sha256"):
            raise RuntimeError(f"GENCODE concordance summary lacks a checksum for {name}")
        expected[name] = str(entry["sha256"])

    checked: list[str] = []
    unbound: list[str] = []
    for fasta in producer_fastas:
        manifest_path = producer_manifest_path(fasta)
        if not manifest_path.is_file():
            unbound.append(str(fasta))
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        arguments = manifest.get("arguments") or {}
        hashes = manifest.get("input_sha256") or {}
        producer_release = str(arguments.get("annotation_release") or "").strip()
        if producer_release != validated_release:
            raise RuntimeError(
                f"{fasta} was produced for annotation release '{producer_release}', "
                f"but the concordance summary validates '{validated_release}'"
            )
        for name, sha in expected.items():
            # A manifest that does not name and checksum the reference cannot verify
            # the binding; it must never be reported as checked.
            value = arguments.get(name)
            if not value:
                raise RuntimeError(
                    f"Producer manifest {manifest_path} does not record --{name}; "
                    "the reference binding of this FASTA cannot be verified"
                )
            observed = hashes.get(str(Path(str(value))))
            if not observed:
                raise RuntimeError(
                    f"Producer manifest {manifest_path} has no checksum for {name} ({value}); "
                    "the reference binding of this FASTA cannot be verified"
                )
            if observed != sha:
                raise RuntimeError(
                    f"{fasta} was produced from a {name} ({value}) that differs from the "
                    "reference input validated by the GENCODE concordance summary"
                )
        checked.append(str(fasta))
    return {"checked": checked, "without_manifest": unbound}
