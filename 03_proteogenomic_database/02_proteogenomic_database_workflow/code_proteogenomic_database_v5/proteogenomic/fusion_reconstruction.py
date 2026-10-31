"""Fusion CDS reconstruction orchestration separated from caller parsing and I/O."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ReconstructionOperations:
    metadata_factory: Callable[[], Any]
    resolve_breakpoint: Callable[..., Any]
    nearest_boundary: Callable[..., Any]
    retained_segments: Callable[..., Any]
    extract_sequence: Callable[..., Any]
    update_breakpoints: Callable[..., Any]
    update_junction: Callable[..., Any]
    update_frame_and_stop: Callable[..., Any]


def create_fusion_cds(
    genome: Any, donor: Any, acceptor: Any, breakpoint1: Any, breakpoint2: Any,
    early_stop_aa_cutoff: int, operations: ReconstructionOperations,
):
    """Build one fusion CDS; unexpected errors propagate as release-fatal."""
    metadata = operations.metadata_factory()
    if not all((
        genome, donor.chrom, acceptor.chrom, donor.cds_segments,
        acceptor.cds_segments, donor.exon_segments, acceptor.exon_segments,
        donor.cds_tx_segments, acceptor.cds_tx_segments,
    )):
        metadata.reason = "missing_cds_or_segments"
        return None, asdict(metadata)
    donor_resolved = operations.resolve_breakpoint(donor.exon_segments, breakpoint1, role="donor")
    acceptor_resolved = operations.resolve_breakpoint(acceptor.exon_segments, breakpoint2, role="acceptor")
    if donor_resolved is None:
        metadata.low_confidence = True
        donor_resolved = operations.nearest_boundary(donor.exon_segments, breakpoint1, role="donor")
    if acceptor_resolved is None:
        metadata.low_confidence = True
        acceptor_resolved = operations.nearest_boundary(acceptor.exon_segments, breakpoint2, role="acceptor")
    if donor_resolved is None or acceptor_resolved is None:
        metadata.reason = "breakpoint_unresolvable_on_exon_chain"
        return None, asdict(metadata)
    donor_tx_offset = int(donor_resolved["tx_offset"])
    acceptor_tx_offset = int(acceptor_resolved["tx_offset"])
    donor_prefix_end_tx = donor_tx_offset + 1
    acceptor_start_tx = acceptor_tx_offset
    donor_pieces = operations.retained_segments(donor.cds_tx_segments, 0, donor_prefix_end_tx)
    acceptor_pieces = operations.retained_segments(acceptor.cds_tx_segments, acceptor_start_tx, None)
    donor_fragment = operations.extract_sequence(genome, donor.chrom, donor_pieces)
    acceptor_fragment = operations.extract_sequence(genome, acceptor.chrom, acceptor_pieces)
    if not donor_fragment or not acceptor_fragment:
        metadata.reason = "empty_fragment_after_splice_resolution"
        return None, asdict(metadata)
    fused = donor_fragment + acceptor_fragment
    metadata.donor_tx_offset = donor_tx_offset
    metadata.acceptor_tx_offset = acceptor_tx_offset
    metadata = operations.update_breakpoints(metadata, donor_resolved, acceptor_resolved)
    metadata = operations.update_junction(
        metadata=metadata, donor_fragment=donor_fragment,
        acceptor_fragment=acceptor_fragment,
        donor_cds_segments=donor.cds_segments,
        acceptor_cds_segments=acceptor.cds_segments,
        cds_tx_segments2=acceptor.cds_tx_segments,
        acceptor_start_tx=acceptor_start_tx,
    )
    metadata = operations.update_frame_and_stop(
        metadata=metadata, fused_cds=fused,
        donor_coding_pieces=donor_pieces, acceptor_coding_pieces=acceptor_pieces,
        cds_tx_segments1=donor.cds_tx_segments,
        cds_tx_segments2=acceptor.cds_tx_segments,
        donor_prefix_end_tx=donor_prefix_end_tx,
        acceptor_start_tx=acceptor_start_tx,
        early_stop_aa_cutoff=early_stop_aa_cutoff,
    )
    return fused, asdict(metadata)

