"""Pure stages for rMATS event projection and candidate classification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class VariantProjection:
    variant: str
    exon_chain: tuple[tuple[int, int], ...]
    cds_segments: tuple[tuple[int, int, Optional[int]], ...]


@dataclass(frozen=True)
class FrameResolution:
    first_overlap_position: int
    upstream_cds_nt: int
    trim_nt: int
    inferred_frame: int
    annotated_phase: Optional[int]
    mismatch: bool


@dataclass(frozen=True)
class OutputTierDecision:
    tier: str
    collector_name: Optional[str]


def project_event_variants(
    chains: Mapping[str, Sequence[Sequence[int]]],
    transcript_cds: Sequence[Sequence[Any]],
    intersect: Callable[[list[tuple[int, int]], Sequence[Sequence[Any]]], Sequence[Sequence[Any]]],
) -> tuple[VariantProjection, ...]:
    """Project caller-local alternatives onto CDS without sequence I/O."""
    return tuple(
        VariantProjection(
            str(name), tuple((int(x[0]), int(x[1])) for x in chain),
            tuple((int(x[0]), int(x[1]), x[2]) for x in intersect(list(chain), transcript_cds)),
        )
        for name, chain in chains.items()
    )


def resolve_variant_frame(
    transcript_cds: Sequence[Sequence[Any]], cds_segments: Sequence[Sequence[Any]], strand: str,
    first_overlap: Callable[[Sequence[Sequence[Any]], str], Optional[int]],
    upstream_count: Callable[[Sequence[Sequence[Any]], int, str], int],
    frame_at: Callable[[Sequence[Sequence[Any]], int, str], int],
    normalize_phase: Callable[[Any], Optional[int]],
) -> Optional[FrameResolution]:
    position = first_overlap(cds_segments, strand)
    if position is None:
        return None
    upstream = upstream_count(transcript_cds, position, strand)
    inferred = frame_at(transcript_cds, position, strand)
    if inferred is None:
        ordered = sorted(transcript_cds, key=lambda x: (int(x[0]), int(x[1])), reverse=(strand == "-"))
        leading_phase = normalize_phase(ordered[0][2]) if ordered else None
        inferred = (upstream - int(leading_phase or 0)) % 3
    segment = next((x for x in transcript_cds if int(x[0]) <= position <= int(x[1])), None)
    phase = normalize_phase(segment[2]) if segment else None
    boundary = bool(segment and position == (int(segment[1]) if strand == "-" else int(segment[0])))
    trim = int(phase) if phase is not None and boundary else inferred
    return FrameResolution(
        position, upstream, trim,
        inferred, phase, trim != inferred,
    )


def choose_output_tier(include: bool, strategy: str) -> OutputTierDecision:
    if not include:
        return OutputTierDecision("excluded", None)
    if strategy == "alternative_start":
        return OutputTierDecision("exploratory", "alternative_start")
    if strategy == "alternative_orf":
        return OutputTierDecision("exploratory", "exploratory_orf")
    return OutputTierDecision("primary_dia", "primary")
