"""Typed fusion domain models and output schemas."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional
from .pipeline_config import PipelineConfig

PARSED_FUSION_COLUMNS = [
    "gene_1_symbol", "gene_2_symbol", "chrom1", "breakpoint1", "chrom2",
    "breakpoint2", "gene_1_id", "gene_2_id", "tx_1_id", "tx_2_id",
    "split_reads", "spanning_reads", "confidence", "caller_annotations",
    "large_anchor_support", "orientation_pass", "caller_frame_annotation",
    "caller_fusion_transcript", "caller_peptide_sequence", "caller_fusion_cds", "caller",
]


MISSING_TEXT_VALUES = frozenset({"", ".", "NA", "N/A", "None", "nan"})

RANKING_IDENTITY_COLUMNS = (
    "sample_basename",
    "sample_id",
    "batch",
    "condition",
    "annotation_release",
    "source_file",
    "source_basename",
    "fusion_name",
    "event_index",
    "pair_token",
    "primary_caller",
)

RANKING_CALLER_COLUMNS = (
    "gene_1_symbol",
    "gene_2_symbol",
    "gene_1_id",
    "gene_2_id",
    "chrom1",
    "chrom2",
    "breakpoint1",
    "breakpoint2",
    "split_reads_max",
    "split_reads_sum",
    "spanning_reads_max",
    "spanning_reads_sum",
    "confidence",
    "contributing_callers",
    "contributing_caller_count",
    "deduplicated_input_row_count",
    "symbol_coordinate_gene_id_collision",
    "caller_annotations",
    "large_anchor_support",
    "orientation_pass",
    "caller_frame_annotation",
    "caller_fusion_transcript",
    "caller_peptide_sequence",
    "caller_fusion_cds",
    "caller_vs_reconstructed_concordance",
)

RANKING_TRANSCRIPT_COLUMNS = (
    "donor_tid",
    "acceptor_tid",
    "donor_transcript_rank",
    "acceptor_transcript_rank",
    "donor_original_transcript_candidate_rank",
    "acceptor_original_transcript_candidate_rank",
    "donor_strand",
    "acceptor_strand",
    "donor_cds_start_nf",
    "donor_cds_end_nf",
    "donor_cds_completeness",
    "acceptor_cds_start_nf",
    "acceptor_cds_end_nf",
    "acceptor_cds_completeness",
    "donor_non_atg_start",
    "acceptor_non_atg_start",
    "donor_stop_codon_readthrough",
    "acceptor_stop_codon_readthrough",
    "donor_selenocysteine_feature_count",
    "acceptor_selenocysteine_feature_count",
    "donor_transcript_candidate_count",
    "acceptor_transcript_candidate_count",
    "donor_phase_missing",
    "acceptor_phase_missing",
    "phase_inferred",
    "frame_inference_method",
    "transcript_selection_strategy",
    "reconstruction_scope",
)

RANKING_ANNOTATION_COLUMNS = (
    "frame_status",
    "protein_product_class",
    "first_stop_codon_nt_start_1based",
    "first_stop_codon_nt_end_1based",
    "stop_before_junction",
    "translation_reaches_junction",
    "translation_crosses_junction",
    "translated_acceptor_aa",
    "low_confidence",
    "fusion_effect_class",
    "donor_cds_retained_pct",
    "acceptor_cds_retained_pct",
    "predicted_loss_of_function",
    "predicted_chimera",
    "early_stop_after_junction",
    "has_junction_spanning_peptide",
    "has_unique_junction_peptide",
    "junction_tryptic_peptide_count",
    "junction_tryptic_unique_count",
    "junction_tryptic_peptides",
    "junction_tryptic_unique_peptides",
    "canonical_uniqueness_assessed",
    "protein_identical_to_reference",
    "donor_retained_cds_nt",
    "acceptor_retained_cds_nt",
)

RANKING_POLICY_COLUMNS = (
    "min_retained_cds_nt",
    "dia_min_protein_length",
    "require_junction_peptide_for_dia",
    "require_unique_junction_peptide_for_dia",
    "exclude_frameshift_from_dia",
    "exclude_truncated_from_dia",
    "exclude_nmd_from_dia",
    "include_donor_only_products",
    "max_breakpoint_snap_distance_nt",
    "breakpoint_snapped_far",
    "max_breakpoint_snap_distance_observed_nt",
    "translation_input_nt_length",
    "exclude_incomplete_cds",
)

RANKING_BREAKPOINT_COLUMNS = (
    "nmd_predicted",
    "nmd_reason",
    "stop_codon_nt_start_1based",
    "stop_codon_nt_end_1based",
    "nearest_downstream_exon_junction_nt",
    "nmd_distance_nt",
    "junction_nt",
    "junction_aa",
    "junction_peptide_unique",
    "exon_junction_nt_positions",
    "donor_breakpoint_location",
    "acceptor_breakpoint_location",
    "donor_resolved_genomic_pos",
    "acceptor_resolved_genomic_pos",
    "donor_breakpoint_snap_distance_nt",
    "acceptor_breakpoint_snap_distance_nt",
    "donor_breakpoint_resolution_class",
    "acceptor_breakpoint_resolution_class",
    "independent_junction_evidence",
)

RANKING_SEQUENCE_COLUMNS = (
    "cds_length",
    "adjusted_cds_length",
    "cds_sequence",
    "protein_length",
    "protein_sequence",
    "protein_sequence_hash",
    "cds_sequence_hash",
)

RANKING_RECORD_COLUMNS = (
    RANKING_IDENTITY_COLUMNS
    + RANKING_CALLER_COLUMNS
    + RANKING_TRANSCRIPT_COLUMNS
    + RANKING_ANNOTATION_COLUMNS
    + RANKING_POLICY_COLUMNS
    + RANKING_BREAKPOINT_COLUMNS
    + RANKING_SEQUENCE_COLUMNS
)

@dataclass
class FusionMetadata:
    donor_split_offset: Optional[int] = None
    acceptor_split_offset: Optional[int] = None
    donor_tx_offset: Optional[int] = None
    acceptor_tx_offset: Optional[int] = None
    junction_nt: Optional[int] = None
    junction_aa: Optional[int] = None
    fusion_junction_nt: Optional[int] = None
    frame_status: str = "NA"
    donor_phase_missing: bool = False
    acceptor_phase_missing: bool = False
    phase_inferred: bool = False
    frame_inference_method: str = "unknown"
    reason: Optional[str] = None
    low_confidence: bool = False
    exon_junction_nt_positions: list[int] = field(default_factory=list)

    donor_breakpoint_location: Optional[str] = None
    acceptor_breakpoint_location: Optional[str] = None
    donor_resolved_genomic_pos: Optional[int] = None
    acceptor_resolved_genomic_pos: Optional[int] = None
    donor_breakpoint_snap_distance_nt: Optional[int] = None
    acceptor_breakpoint_snap_distance_nt: Optional[int] = None

    fusion_junction_frame_remainder: Optional[int] = None
    junction_codon_spans_breakpoint: Optional[bool] = None
    junction_codon_bases_on_donor: Optional[int] = None
    junction_codon_bases_on_acceptor: Optional[int] = None
    junction_codon_side: Optional[str] = None

    first_stop_codon_nt_start_1based: Optional[int] = None
    first_stop_codon_nt_end_1based: Optional[int] = None
    stop_before_junction: Optional[bool] = None
    translation_reaches_junction: Optional[bool] = None
    translation_crosses_junction: Optional[bool] = None
    protein_product_class: Optional[str] = None
    translated_acceptor_aa: Optional[int] = None

@dataclass
class TranscriptCandidate:
    chrom: str
    cds_segments: list[dict[str, Any]]
    exon_segments: list[dict[str, Any]]
    cds_tx_segments: list[dict[str, Any]]

@dataclass(frozen=True)
class ReferenceContext:
    """Read-only resources shared while reconstructing fusion candidates."""

    genome: Any
    args: PipelineConfig
    reference_peptides: Optional[set[str]] = None
    reference_proteins: Optional[set[str]] = None

@dataclass(frozen=True)
class PartnerLookupContext:
    """Shared resources used to find donor and acceptor transcript models."""

    db: Any
    genome: Any
    transcript_index: Mapping[str, Any]
    transcript_alias_index: Mapping[str, Any]
    transcript_models: Mapping[str, Any]
    gene_symbol_index: Mapping[str, Any]
    cds_cache: dict[Any, Any]
    max_transcripts_per_gene: int = 1

@dataclass(frozen=True)
class PartnerRequest:
    """Per-partner values used for transcript candidate lookup."""

    gene_id: Optional[str]
    gene_symbol: Optional[str]
    preferred_transcript: Optional[str]
    breakpoint_chrom: Optional[str]
    breakpoint: int

@dataclass(frozen=True)
class CandidatePairRequest:
    """All event-specific values required to evaluate one transcript pair."""

    row: Any
    sample_label: str
    fusion_name: str
    event_index: int
    donor_index: int
    acceptor_index: int
    donor: Mapping[str, Any]
    acceptor: Mapping[str, Any]
    breakpoint_chrom1: Optional[str]
    breakpoint_chrom2: Optional[str]
    breakpoint1: int
    breakpoint2: int

@dataclass(frozen=True)
class RankingRecordRequest:
    """Typed inputs for constructing one stable output-schema record."""

    event: CandidatePairRequest
    pair_token: str
    fusion_cds: str
    fusion_meta: Mapping[str, Any]
    protein_sequence: str
    frame_status: str
    caller_frame_annotation: Any
    caller_peptide: Any
    concordance: str
    functional: Mapping[str, Any]
    junction_evaluation: Mapping[str, Any]
    junction_peptide_unique: Optional[bool]
    nmd: Mapping[str, Any]
    donor_retained_cds_nt: int
    acceptor_retained_cds_nt: int
    protein_identical_to_reference: Optional[bool]
    breakpoint_snapped_far: bool
    max_snap_distance: int
    config: "FusionFilterConfig"

@dataclass(frozen=True)
class FusionFilterConfig:
    """Immutable primary-FASTA policy passed to ranking/output helpers."""
    min_retained_cds_nt: int
    min_protein_length: int
    require_junction_peptide: bool
    require_unique_junction_peptide: bool
    exclude_frameshift_from_dia: bool
    exclude_truncated_from_dia: bool
    exclude_nmd_from_dia: bool
    include_donor_only_products: bool
    max_breakpoint_snap_distance_nt: int
    exclude_incomplete_cds: bool
    max_transcripts_per_gene: int = 3

    @classmethod
    def from_namespace(cls, args: Any) -> "FusionFilterConfig":
        """Build from a CLI object or immutable PipelineConfig at the boundary."""
        values = {}
        for name, definition in cls.__dataclass_fields__.items():
            values[name] = getattr(args, name, definition.default)
        return cls(**values)

@dataclass(frozen=True)
class SampleProcessingContext:
    """Reference data and policy shared across all events in one sample."""

    db: Any
    genome: Any
    transcript_models: Mapping[str, Any]
    transcript_alias_index: Mapping[str, Any]
    transcript_index: Mapping[str, Any]
    gene_symbol_index: Mapping[str, Any]
    args: PipelineConfig
    reference_peptides: Optional[set[str]] = None
    reference_proteins: Optional[set[str]] = None
