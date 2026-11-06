"""Merge domain models and normalization primitives."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set
from .pgdb_header import (  # noqa: F401  (re-exported merge primitives)
    clean_value, join_values, normalize_protein_sequence, sanitize_header_value,
    sequence_hashes, sorted_values, split_values,
)


FASTA_EXTENSIONS = {
    ".fa",
    ".faa",
    ".fasta",
    ".fas",
    ".fa.gz",
    ".faa.gz",
    ".fasta.gz",
    ".fas.gz",
}

__all__ = [
    "FASTA_EXTENSIONS", "VALID_AA", "ProteinFilterConfig", "ParsedRecord", "SequenceAggregate",
    "clean_value", "sanitize_header_value", "split_multi_value", "normalize_sequence",
    "fasta_suffix", "sequence_hashes", "sorted_values", "joined", "representative_value",
    "CONFIDENCE_ORDER", "aggregate_confidence",
]

_FASTA_EXTENSIONS_LONGEST_FIRST = tuple(sorted(FASTA_EXTENSIONS, key=len, reverse=True))

VALID_AA = set("ACDEFGHIKLMNPQRSTVWYBXZJUO")

@dataclass(frozen=True)
class ProteinFilterConfig:
    allowed_record_types: Set[str]
    min_length: int
    max_length: Optional[int]
    invalid_policy: str
    min_peptide_length: int
    max_peptide_length: int
    max_missed_cleavages: int
    include_rescue_tiers: bool = False

@dataclass
class ParsedRecord:
    """Normalized representation of one input FASTA record."""

    input_file: str
    original_id: str
    original_description: str
    sequence: str
    sequence_md5: str
    sequence_sha256: str
    source: str
    record_type: str
    gene_symbols: Set[str] = field(default_factory=set)
    gene_ids: Set[str] = field(default_factory=set)
    transcripts: Set[str] = field(default_factory=set)
    event_types: Set[str] = field(default_factory=set)
    event_ids: Set[str] = field(default_factory=set)
    variants: Set[str] = field(default_factory=set)
    callers: Set[str] = field(default_factory=set)
    uniprot_accessions: Set[str] = field(default_factory=set)
    uniprot_entries: Set[str] = field(default_factory=set)
    protein_names: Set[str] = field(default_factory=set)
    translation_strategies: Set[str] = field(default_factory=set)
    database_output_tiers: Set[str] = field(default_factory=set)
    protein_product_classes: Set[str] = field(default_factory=set)
    sample_ids: Set[str] = field(default_factory=set)
    batches: Set[str] = field(default_factory=set)
    conditions: Set[str] = field(default_factory=set)
    annotation_releases: Set[str] = field(default_factory=set)
    metadata: Dict[str, str] = field(default_factory=dict)
    n_eligible_tryptic_peptides: int = 0
    min_eligible_peptide_length: Optional[int] = None
    max_eligible_peptide_length: Optional[int] = None

@dataclass
class SequenceAggregate:
    """All provenance associated with one exact amino-acid sequence."""

    sequence: str
    sequence_md5: str
    sequence_sha256: str
    records: List[ParsedRecord] = field(default_factory=list)
    sources: Set[str] = field(default_factory=set)
    input_files: Set[str] = field(default_factory=set)
    gene_symbols: Set[str] = field(default_factory=set)
    gene_ids: Set[str] = field(default_factory=set)
    transcripts: Set[str] = field(default_factory=set)
    event_types: Set[str] = field(default_factory=set)
    event_ids: Set[str] = field(default_factory=set)
    variants: Set[str] = field(default_factory=set)
    callers: Set[str] = field(default_factory=set)
    original_ids: Set[str] = field(default_factory=set)
    record_types: Set[str] = field(default_factory=set)
    uniprot_accessions: Set[str] = field(default_factory=set)
    uniprot_entries: Set[str] = field(default_factory=set)
    protein_names: Set[str] = field(default_factory=set)
    translation_strategies: Set[str] = field(default_factory=set)
    database_output_tiers: Set[str] = field(default_factory=set)
    protein_product_classes: Set[str] = field(default_factory=set)
    sample_ids: Set[str] = field(default_factory=set)
    batches: Set[str] = field(default_factory=set)
    conditions: Set[str] = field(default_factory=set)
    annotation_releases: Set[str] = field(default_factory=set)

    def add(self, record: ParsedRecord) -> None:
        self.records.append(record)
        self.sources.add(record.source)
        self.input_files.add(record.input_file)
        self.original_ids.add(record.original_id)
        self.record_types.add(record.record_type)
        self.gene_symbols.update(record.gene_symbols)
        self.gene_ids.update(record.gene_ids)
        self.transcripts.update(record.transcripts)
        self.event_types.update(record.event_types)
        self.event_ids.update(record.event_ids)
        self.variants.update(record.variants)
        self.callers.update(record.callers)
        self.uniprot_accessions.update(record.uniprot_accessions)
        self.uniprot_entries.update(record.uniprot_entries)
        self.protein_names.update(record.protein_names)
        self.translation_strategies.update(record.translation_strategies)
        self.database_output_tiers.update(record.database_output_tiers)
        self.protein_product_classes.update(record.protein_product_classes)
        self.sample_ids.update(split_multi_value(record.metadata.get("sample_id")))
        self.batches.update(split_multi_value(record.metadata.get("batch")))
        self.conditions.update(split_multi_value(record.metadata.get("condition")))
        self.annotation_releases.update(split_multi_value(record.metadata.get("annotation_release")))

# Header-value primitives are defined once in pgdb_header; merge uses the same
# implementations under its historical names.
split_multi_value = split_values
joined = join_values


def normalize_sequence(raw_sequence: object) -> str:
    """Normalize an amino-acid sequence for exact-sequence deduplication."""
    return normalize_protein_sequence(raw_sequence, remove_stops=True)


def fasta_suffix(path: Path) -> str:
    """Return a normalized FASTA extension, including optional .gz."""
    name = path.name.lower()
    return next((ext for ext in _FASTA_EXTENSIONS_LONGEST_FIRST if name.endswith(ext)), "")


def representative_value(values: Iterable[str]) -> str:
    """Deterministic representative: the first sorted non-missing value, else NA."""
    items = sorted_values(values)
    return items[0] if items else "NA"


CONFIDENCE_ORDER = {"Rejected": 0, "Exploratory": 1, "Moderate": 2, "High confidence": 3}


def aggregate_confidence(aggregate: "SequenceAggregate") -> str:
    """Best producer confidence among the records of one exact sequence.

    Without any producer confidence, exploratory-tier sequences are labelled
    Exploratory and all others Moderate.
    """
    # Records are scanned in order (not via a set) so ties between unranked
    # labels resolve deterministically.
    confidences = [
        record.metadata["confidence"] for record in aggregate.records
        if record.metadata.get("confidence")
    ]
    fallback = "Exploratory" if "exploratory" in {
        tier.lower() for tier in aggregate.database_output_tiers
    } else "Moderate"
    return max(confidences, key=lambda value: CONFIDENCE_ORDER.get(value, -1), default=fallback)
