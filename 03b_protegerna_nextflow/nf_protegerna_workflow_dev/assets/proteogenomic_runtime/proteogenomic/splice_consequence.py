"""Shared coding-consequence calculations for rMATS and SUPPA candidates."""
from __future__ import annotations

from typing import Any, Optional, Sequence
from .proteogenomic_models import SpliceConsequence

from .splice_translation import (
    cds_frame_at_genomic_position, exon_junction_positions_from_exon_segments,
    first_stop_codon_aa, interval_length, nmd_prediction, normalize_phase_value,
)


def evaluate_shared_splice_consequence(
    altered_cds: Sequence[Sequence[Any]],
    reference_cds: Optional[Sequence[Sequence[Any]]],
    strand: str,
    nucleotide_sequence: Optional[str],
    exon_chain: Sequence[Sequence[int]],
    translation_start_offset_nt: int = 0,
    nmd_distance_threshold_nt: int = 55,
    pad_partial_codons: bool = False,
) -> SpliceConsequence:
    """Evaluate the fields that must mean the same in both splice callers."""
    altered = list(altered_cds or [])
    reference = list(reference_cds or [])
    altered_phase = normalize_phase_value(
        sorted(altered, key=lambda x: x[0], reverse=strand == "-")[0][2]
    ) if altered else 0
    reference_phase = normalize_phase_value(
        sorted(reference, key=lambda x: x[0], reverse=strand == "-")[0][2]
    ) if reference else 0
    altered_len = interval_length(altered) - int(altered_phase or 0)
    reference_len = interval_length(reference) - int(reference_phase or 0) if reference else None
    delta = altered_len - reference_len if reference_len is not None else None
    shared_positions = [
        position
        for start, end, *_ in altered
        for position in (int(start), int(end))
        if any(int(rstart) <= position <= int(rend) for rstart, rend, *_ in reference)
    ]
    if reference_len is None:
        frame_status, frameshift = "NA", None
    else:
        mismatch = any(
            cds_frame_at_genomic_position(altered, position, strand)
            != cds_frame_at_genomic_position(reference, position, strand)
            for position in shared_positions
        )
        frame_status = "FRAMESHIFT" if mismatch else "INFRAME"
        frameshift = mismatch
    stop_aa, stop_nt, terminal_stop, _ = first_stop_codon_aa(
        nucleotide_sequence, start_nt=0, pad=pad_partial_codons
    )
    premature_stop = bool(stop_aa is not None and terminal_stop is False)
    junctions = exon_junction_positions_from_exon_segments(
        exon_chain, altered, strand,
        translation_start_offset_nt=translation_start_offset_nt,
    )
    nmd, reason, nearest, distance = nmd_prediction(
        stop_nt if premature_stop else None, junctions, nmd_distance_threshold_nt
    )
    return SpliceConsequence(
        reference_len, altered_len, delta, frame_status, frameshift,
        premature_stop, terminal_stop, stop_aa, stop_nt,
        nmd, reason, nearest, distance,
    )
