"""Merge domain models and normalization primitives."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple
from .pgdb_header import clean_value as pgdb_clean_value, normalize_protein_sequence
from .pgdb_header import join_values as pgdb_join_values
from .pgdb_header import sanitize_header_value as pgdb_sanitize_header_value
from .pgdb_header import sequence_hashes as pgdb_sequence_hashes
from .pgdb_header import sorted_values as pgdb_sorted_values, split_values as pgdb_split_values


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

def clean_value(value: object, default: str = "NA") -> str:
    """Return a stripped value or a consistent missing-value token."""
    return pgdb_clean_value(value, default)

def sanitize_header_value(value: object) -> str:
    """Make a metadata value safe for use in a pipe-delimited FASTA header."""
    return pgdb_sanitize_header_value(value)

def split_multi_value(value: object) -> Set[str]:
    """Split common list encodings while preserving identifiers such as chr1:1-2."""
    return pgdb_split_values(value)

def normalize_sequence(raw_sequence: object) -> str:
    """Normalize an amino-acid sequence for exact-sequence deduplication."""
    return normalize_protein_sequence(raw_sequence, remove_stops=True)

def fasta_suffix(path: Path) -> str:
    """Return a normalized FASTA extension, including optional .gz."""
    name = path.name.lower()
    for ext in sorted(FASTA_EXTENSIONS, key=len, reverse=True):
        if name.endswith(ext):
            return ext
    return ""

def sequence_hashes(sequence: str) -> Tuple[str, str]:
    return pgdb_sequence_hashes(sequence)

def sorted_values(values: Iterable[str]) -> List[str]:
    return pgdb_sorted_values(values)

def joined(values: Iterable[str], separator: str = ";") -> str:
    return pgdb_join_values(values, separator=separator)

def representative_value(values: Iterable[str]) -> str:
    items = sorted_values(values)
    if not items:
        return "NA"
    if len(items) == 1:
        return items[0]
    return items[0]
