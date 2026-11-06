"""Canonical sample, batch, condition, and input-validation helpers."""
from __future__ import annotations

import csv
import glob
import gzip
import hashlib
import logging.config
import os
from os import PathLike
import re
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, TextIO, TypedDict


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


_GLOB_CHARS = frozenset("*?[")


def resolve_input_files(items: object) -> list[Path]:
    """Resolve input values to the concrete files a producer would read.

    Producers expand glob patterns (``*``, ``?``, ``[...]``, recursive ``**``)
    and walk directories, so provenance and resume fingerprints must hash that
    same resolved file set rather than the literal pattern string. Unmatched
    patterns and non-path values resolve to nothing; membership changes are
    therefore visible as added or removed paths.
    """
    values = items if isinstance(items, (list, tuple, set, frozenset)) else [items]
    resolved: list[Path] = []
    for item in values:
        if not isinstance(item, (str, PathLike)) or item in ("", None):
            continue
        text = str(item)
        if _GLOB_CHARS & set(text):
            candidates = [Path(match) for match in sorted(glob.glob(text, recursive=True))]
        else:
            candidates = [Path(text)]
        for candidate in candidates:
            if candidate.is_file():
                resolved.append(candidate)
            elif candidate.is_dir():
                resolved.extend(sorted(p for p in candidate.rglob("*") if p.is_file()))
    return list(dict.fromkeys(resolved))


_SHA256_CACHE: dict[str, tuple[tuple[int, ...], str]] = {}


def _file_signature(stat: os.stat_result) -> tuple[int, ...]:
    """Identity of a file's current contents as far as the filesystem reports it.

    Device and inode change when a file is replaced by another (rename/copy);
    ctime changes on any in-place write and cannot be reset by tools that
    restore mtime, so a same-size, same-mtime replacement is still detected.
    """
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def sha256_file(path: str | PathLike[str], *, use_cache: bool = True) -> str:
    """SHA-256 of a file, read in 1 MiB blocks.

    With ``use_cache`` the digest is memoised for the current process, keyed by
    the resolved path and its file signature, so multi-GB references shared by
    several steps (genome, gtf_db) are hashed once. ``use_cache=False`` always
    re-reads the file (used for outputs the workflow has just written).
    """
    resolved = str(Path(path).resolve())
    signature = _file_signature(os.stat(resolved))
    cached = _SHA256_CACHE.get(resolved) if use_cache else None
    if cached is not None and cached[0] == signature:
        return cached[1]
    digest = hashlib.sha256()
    with open(resolved, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    # Re-stat after reading: if the file changed meanwhile, do not cache the result.
    if _file_signature(os.stat(resolved)) == signature:
        _SHA256_CACHE[resolved] = (signature, digest.hexdigest())
    return digest.hexdigest()


def forget_file_hashes(paths: Iterable[str | PathLike[str]]) -> None:
    """Drop memoised digests for files a step may have rewritten."""
    for path in paths:
        _SHA256_CACHE.pop(str(Path(path).resolve()), None)


def as_path_list(value: object) -> list[str]:
    """Normalise an optional path or list of paths (CLI ``nargs="+"``) to a list."""
    if not value:
        return []
    if isinstance(value, (str, PathLike)):
        return [str(value)]
    if isinstance(value, Iterable):
        return [str(item) for item in value if item]
    return [str(value)]


def open_text(path: str | PathLike[str]) -> TextIO:
    """Open a UTF-8 text file, transparently decompressing ``.gz``."""
    if str(path).lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


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
