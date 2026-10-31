#!/usr/bin/env python3
"""Canonical utilities for the proteogenomic FASTA header contract.

The producer, merge, annotation, and QC scripts all exchange metadata through
the same pipe-delimited PGDB header. Keeping its parser and serializer here
prevents small differences in key casing or legacy-header handling from
changing provenance between pipeline stages.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Set, Tuple


MISSING_TOKENS = {"", ".", "NA", "N/A", "NONE", "NULL", "NAN", "UNKNOWN"}
KEY_VALUE_RE = re.compile(r"(?:^|[\s|])([A-Za-z][A-Za-z0-9_.-]*)=([^\s|]+)")


def clean_value(value: object, default: str = "NA") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return default if text.upper() in MISSING_TOKENS else text


def split_values(value: object) -> Set[str]:
    text = clean_value(value)
    if text == "NA":
        return set()
    return {
        token
        for part in re.split(r"[,;]", text)
        if (token := clean_value(part)) != "NA"
    }


def sorted_values(values: Iterable[object]) -> list[str]:
    return sorted({token for value in values if (token := clean_value(value)) != "NA"})


def join_values(values: Iterable[object], separator: str = ";", missing: str = "NA") -> str:
    items = sorted_values(values)
    return separator.join(items) if items else missing


def sanitize_header_value(value: object) -> str:
    text = re.sub(r"\s+", "_", clean_value(value))
    return text.replace("|", "/").replace(";", ",").replace("=", ":") or "NA"


def serialize_pgdb_header(
    record_id: object,
    gene_symbol: object,
    metadata: Iterable[Tuple[str, object]],
    organism: object = "unknown_organism",
) -> str:
    """Serialize the canonical PGDB header without a leading ``>``.

    Metadata order is retained for readable, deterministic producer headers;
    duplicate keys are rejected because the parser otherwise keeps only the
    first value and silently hides later values.
    """
    safe_record_id = sanitize_header_value(record_id)
    safe_gene_symbol = sanitize_header_value(gene_symbol)
    safe_organism = sanitize_header_value(organism)
    fields = []
    normalized_metadata = {}
    seen = set()
    for raw_key, value in metadata:
        key = str(raw_key).strip().lower()
        if not re.fullmatch(r"[a-z][a-z0-9_.-]*", key):
            raise ValueError(f"Invalid PGDB metadata key: {raw_key!r}")
        if key in seen:
            raise ValueError(f"Duplicate PGDB metadata key: {key}")
        seen.add(key)
        normalized_metadata[key] = clean_value(value)
        fields.append(f"{key}={sanitize_header_value(value)}")
    if normalized_metadata.get("schema_version"):
        from .release_validation import MergeInputContract
        MergeInputContract().validate(normalized_metadata, normalized_metadata.get("source", ""))
    preamble = (
        f"PGDB|{safe_record_id}|{safe_record_id} "
        f"GN={safe_gene_symbol} OS={safe_organism}"
    )
    return "|".join([preamble, *fields])


def normalize_protein_sequence(sequence: object, remove_stops: bool = False) -> str:
    normalized = re.sub(r"\s+", "", str(sequence or "")).upper()
    return normalized.replace("*", "") if remove_stops else normalized


def sequence_hashes(sequence: object) -> Tuple[str, str]:
    encoded = str(sequence).encode("utf-8")
    return hashlib.md5(encoded).hexdigest(), hashlib.sha256(encoded).hexdigest()


@dataclass
class PGDBHeader:
    """Parsed PGDB or fallback FASTA header with lowercase metadata keys."""

    record_id: str
    metadata: Dict[str, str] = field(default_factory=dict)
    prefix: str = "PGDB"

    @classmethod
    def parse(cls, description: str, default_id: str = "NA") -> "PGDBHeader":
        text = str(description or "").strip()
        if not text:
            return cls(clean_value(default_id), {}, clean_value(default_id))

        tokens = text.split("|")
        prefix = tokens[0].strip() or clean_value(default_id)
        record_id = "NA"
        if prefix.upper() == "PGDB" and len(tokens) > 1 and "=" not in tokens[1]:
            record_id = clean_value(tokens[1].strip().split()[0])

        metadata: Dict[str, str] = {}
        for match in KEY_VALUE_RE.finditer(text):
            metadata.setdefault(match.group(1).lower(), match.group(2))
        if "gn" in metadata and "gene_symbol" not in metadata:
            metadata["gene_symbol"] = metadata["gn"]

        record_id = clean_value(
            metadata.get("record_id")
            or (record_id if record_id != "NA" else prefix.split()[0]),
            default=clean_value(default_id),
        )
        return cls(record_id, metadata, prefix)

    @property
    def gene_symbol(self) -> str:
        return clean_value(self.metadata.get("gene_symbol") or self.metadata.get("gn"))

    @property
    def organism(self) -> str:
        return clean_value(self.metadata.get("os"))

    def serialize(self, organism: str = "unknown_organism") -> str:
        record_id = clean_value(self.record_id, "unnamed_record")
        gene_symbol = self.gene_symbol
        fields = {
            key.lower(): value
            for key, value in self.metadata.items()
            if key.lower() not in {"gn", "os"}
        }
        fields["record_id"] = record_id
        return serialize_pgdb_header(record_id, gene_symbol, fields.items(), organism)
