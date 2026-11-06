"""Typed records shared by splice, fusion, QC, and merge pipelines."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Optional, TypedDict


def _required_text(value: object, field_name: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


class SerializableRecord:
    """Validated domain record serialized only at an output boundary."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


class Strand(StrEnum):
    PLUS = "+"
    MINUS = "-"


@dataclass(frozen=True, order=True)
class GenomicInterval:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 1 or self.end < self.start:
            raise ValueError(f"invalid 1-based inclusive interval: {self.start}-{self.end}")


@dataclass(frozen=True)
class CDSSegment:
    interval: GenomicInterval
    phase: Optional[int]
    phase_missing: bool = False


class TranscriptRecord(TypedDict, total=False):
    transcript_id: str
    gene_id: str
    gene_name: Optional[str]
    chrom: str
    strand: str
    exons: list[tuple[int, int]]
    cds: list[tuple[int, int, Optional[int]]]
    cds_start_nf: bool
    cds_end_nf: bool
    non_atg_start: bool
    stop_codon_readthrough: bool
    selenocysteine_intervals: list[tuple[int, int]]


@dataclass(frozen=True)
class SpliceCandidate:
    source_file: Path
    event_type: str
    event_id: str
    variant: str
    transcript: TranscriptRecord
    exon_chain: tuple[GenomicInterval, ...]

    def __post_init__(self) -> None:
        _required_text(self.event_type, "event_type")
        _required_text(self.event_id, "event_id")
        _required_text(self.variant, "variant")


@dataclass(frozen=True)
class BreakpointResolution(SerializableRecord):
    requested_genomic_position: int
    resolved_genomic_position: int
    transcript_offset: int
    location: str
    snap_distance_nt: int = 0

    def __post_init__(self) -> None:
        if min(self.requested_genomic_position, self.resolved_genomic_position) < 1:
            raise ValueError("breakpoint genomic positions are 1-based and must be positive")
        if self.transcript_offset < 0 or self.snap_distance_nt < 0:
            raise ValueError("breakpoint offsets and distances must be non-negative")
        _required_text(self.location, "location")


@dataclass(frozen=True)
class TranslationResult(SerializableRecord):
    nucleotide_sequence: str
    protein_sequence: str
    frame_status: str
    translation_strategy: str
    first_stop_nt_1based: Optional[int] = None

    def __post_init__(self) -> None:
        if set(self.nucleotide_sequence.upper()) - set("ACGTN"):
            raise ValueError("nucleotide_sequence contains unsupported symbols")
        if "*" in self.protein_sequence[:-1]:
            raise ValueError("protein_sequence contains an internal stop")
        _required_text(self.frame_status, "frame_status")
        _required_text(self.translation_strategy, "translation_strategy")


@dataclass(frozen=True)
class FusionCandidate(SerializableRecord):
    sample_id: str
    fusion_name: str
    donor_transcript_id: str
    acceptor_transcript_id: str
    donor_breakpoint: BreakpointResolution
    acceptor_breakpoint: BreakpointResolution
    translation: TranslationResult
    caller: str = "FusionInspector"

    def __post_init__(self) -> None:
        for name in ("sample_id", "fusion_name", "donor_transcript_id", "acceptor_transcript_id"):
            _required_text(getattr(self, name), name)


@dataclass(frozen=True)
class SpliceConsequence(SerializableRecord):
    original_cds_len: Optional[int]
    altered_cds_len: int
    cds_delta_nt: Optional[int]
    frame_status: str
    frameshift: Optional[bool]
    premature_stop: bool
    terminal_stop: Optional[bool]
    first_stop_aa: Optional[int]
    first_stop_nt_1based: Optional[int]
    nmd_predicted: bool
    nmd_reason: str
    nearest_downstream_exon_junction_nt: Optional[int]
    nmd_distance_nt: Optional[int]

    def __post_init__(self) -> None:
        if self.altered_cds_len < 0 or (self.original_cds_len is not None and self.original_cds_len < 0):
            raise ValueError("CDS lengths must be non-negative")
        _required_text(self.frame_status, "frame_status")
        _required_text(self.nmd_reason, "nmd_reason")


@dataclass(frozen=True)
class ProteinMapping(SerializableRecord):
    original_record_id: str
    sequence_sha256: str
    source: str
    event_id: Optional[str] = None
    transcript_id: Optional[str] = None

    def __post_init__(self) -> None:
        _required_text(self.original_record_id, "original_record_id")
        if len(self.sequence_sha256) != 64:
            raise ValueError("sequence_sha256 must be a 64-character SHA-256 digest")
        _required_text(self.source, "source")


@dataclass(frozen=True)
class DatabaseRecord(SerializableRecord):
    record_id: str
    sequence: str
    source: str
    record_type: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _required_text(self.record_id, "record_id")
        _required_text(self.source, "source")
        _required_text(self.record_type, "record_type")
        normalized = self.sequence.strip().upper().rstrip("*")
        if not normalized:
            raise ValueError("sequence must not be empty")
        if set(normalized) - set("ACDEFGHIKLMNPQRSTVWYBXZJUO"):
            raise ValueError("sequence contains unsupported amino-acid symbols")
        object.__setattr__(self, "sequence", normalized)


@dataclass
class SpliceProteinResult:
    """Caller-neutral result produced after rMATS/SUPPA-specific reconstruction."""
    candidates: list[SpliceCandidate] = field(default_factory=list)
    proteins: dict[str, dict[str, Any]] = field(default_factory=dict)
    alternative_start_proteins: dict[str, dict[str, Any]] = field(default_factory=dict)
    exploratory_orf_proteins: dict[str, dict[str, Any]] = field(default_factory=dict)
    junction_records: list[Any] = field(default_factory=list)
    consequence_rows: list[dict[str, Any]] = field(default_factory=list)

    def merge_into(self, other: "SpliceProteinResult") -> None:
        """Merge another result without exposing collector arguments to pipelines."""
        from splice_reconstruction_core import merge_protein_mappings

        merge_protein_mappings(self.proteins, other.proteins)
        merge_protein_mappings(
            self.alternative_start_proteins, other.alternative_start_proteins
        )
        merge_protein_mappings(
            self.exploratory_orf_proteins, other.exploratory_orf_proteins
        )
        self.junction_records.extend(other.junction_records)
        self.consequence_rows.extend(other.consequence_rows)
        self.candidates.extend(other.candidates)


@dataclass(frozen=True)
class ConsequenceRecord:
    values: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(frozen=True)
class OutputBundle:
    primary_fasta: Optional[Path] = None
    rescue_fasta: Optional[Path] = None
    exploratory_fasta: Optional[Path] = None
    excluded_audit_tsv: Optional[Path] = None
    consequence_tsv: Optional[Path] = None
