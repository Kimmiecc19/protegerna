"""Canonical sample, batch, condition, and input-validation helpers."""
from __future__ import annotations

import csv
import logging.config
from os import PathLike
import re
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, TypedDict


class SampleMetadata(TypedDict):
    sample_id: str
    batch: str
    condition: str


class SampleProvenance(SampleMetadata):
    provenance_source: str


MISSING = {"", ".", "na", "n/a", "none", "nan", "unknown"}


def clean_text(value: object, default: str = "NA") -> str:
    text = "" if value is None else str(value).strip()
    return default if text.lower() in MISSING else text


def batch_from_path(path: object) -> str:
    """Extract batch labels such as batch3 from any POSIX/Windows path."""
    match = re.search(r"(?:^|[\\/])((?:batch)[-_]?\d+)(?:[\\/]|$)", str(path), re.I)
    return match.group(1).lower().replace("_", "").replace("-", "") if match else "NA"


def condition_from_text(value: object) -> str:
    """Conservatively infer a condition; never guess from CASE-CTRL contrasts."""
    text = clean_text(value, "")
    tokens = [x for x in re.split(r"[^A-Za-z0-9]+", text.upper()) if x]
    case = {"CASE", "TUMOR", "TUMOUR", "DISEASE", "TREATMENT", "TREATED"}
    control = {"CTRL", "CONTROL", "NORMAL", "HEALTHY", "UNTREATED"}
    case_hit = next((x for x in tokens if x in case), None)
    control_hit = next((x for x in tokens if x in control), None)
    if case_hit and not control_hit:
        return "CASE"
    if control_hit and not case_hit:
        return "CTRL"
    return "NA"


def load_sample_metadata(path: Optional[str | PathLike[str]]) -> Dict[str, SampleMetadata]:
    """Load TSV/CSV with required sample_id and optional batch/condition columns."""
    if not path:
        return {}
    metadata_path = Path(path)
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Sample metadata file not found: {metadata_path}")
    delimiter = "," if metadata_path.suffix.lower() == ".csv" else "\t"
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames or "sample_id" not in reader.fieldnames:
            raise ValueError("Sample metadata requires a 'sample_id' column")
        result: Dict[str, SampleMetadata] = {}
        for line_number, row in enumerate(reader, 2):
            sample_id = clean_text(row.get("sample_id"), "")
            if not sample_id:
                raise ValueError(f"Missing sample_id at {metadata_path}:{line_number}")
            if sample_id in result:
                raise ValueError(f"Duplicate sample_id '{sample_id}' in {metadata_path}")
            result[sample_id] = {
                "sample_id": sample_id,
                "batch": clean_text(row.get("batch")),
                "condition": clean_text(row.get("condition")),
            }
    return result


def sample_provenance(
    sample_id: object,
    source_path: object,
    metadata: Optional[Mapping[str, SampleMetadata]] = None,
) -> SampleProvenance:
    sample = clean_text(sample_id)
    explicit: Optional[SampleMetadata] = (metadata or {}).get(sample)
    explicit_batch = clean_text(explicit.get("batch")) if explicit else "NA"
    explicit_condition = clean_text(explicit.get("condition")) if explicit else "NA"
    return {
        "sample_id": sample,
        "batch": explicit_batch if explicit_batch != "NA" else batch_from_path(source_path),
        "condition": (
            explicit_condition
            if explicit_condition != "NA"
            else condition_from_text(sample)
        ),
        "provenance_source": "sample_metadata" if explicit else "path_and_sample_inference",
    }


def require_files(paths: Iterable[str | PathLike[str]], label: str) -> None:
    missing = [str(path) for path in paths if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing {label} file(s): {', '.join(missing)}")


def configure_logging(level: str = "INFO") -> None:
    """Install deterministic logging while preserving test-owned loggers."""
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}},
        "handlers": {"stderr": {"class": "logging.StreamHandler", "formatter": "standard", "stream": "ext://sys.stderr"}},
        "root": {"level": str(level).upper(), "handlers": ["stderr"]},
    })
