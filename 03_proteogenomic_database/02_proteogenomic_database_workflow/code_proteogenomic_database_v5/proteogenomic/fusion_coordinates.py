"""Fusion transcript-coordinate mapping and breakpoint resolution."""
from __future__ import annotations
import logging
from dataclasses import asdict
from typing import Any, Optional
from Bio.Seq import Seq
from .fusion_models import FusionMetadata
from .fusion_values import chrom_matches, parse_int_or_none
from .splice_translation import classify_phased_junction_frame, normalize_phase_value

logger = logging.getLogger(__name__)


def resolve_chrom_name(genome, chrom):
    """Resolve chromosome naming differences (chr1 vs 1) against genome keys."""
    if chrom is None:
        return None

    chrom = str(chrom)
    if chrom in genome:
        return chrom

    if chrom.startswith("chr"):
        alt = chrom[3:]
        return alt if alt in genome else None

    alt = f"chr{chrom}"
    return alt if alt in genome else None

def get_feature_intervals(db, transcript_id, featuretype):
    """
    Return transcript child intervals as dictionaries sorted by genomic start.

    For CDS features, phase is retained. For exon features, phase is None.
    """
    try:
        features = list(
            db.children(transcript_id, featuretype=featuretype, order_by="start")
        )
    except (KeyError, AttributeError, TypeError, ValueError) as e:
        logger.debug(
            "Could not fetch %s features for %s: %s", featuretype, transcript_id, e
        )
        return []

    intervals = []
    for feat in features:
        phase = None
        if featuretype == "CDS":
            phase = normalize_phase_value(
                getattr(feat, "phase", None)
                if getattr(feat, "phase", None) not in (None, ".", "")
                else getattr(feat, "frame", None)
            )
            if phase is None:
                phase = normalize_phase_value(getattr(feat, "score", None))
        intervals.append(
            {
                "genomic_start": int(feat.start),
                "genomic_end": int(feat.end),
                "strand": feat.strand,
                "phase": phase,
                "phase_missing": featuretype == "CDS" and phase is None,
                "featuretype": featuretype,
            }
        )

    return intervals

def get_cds_exons(db, transcript_id):
    """
    Backward-compatible wrapper.

    Returns list of (start, end, phase, strand), matching the old API.
    """
    intervals = get_feature_intervals(db, transcript_id, "CDS")
    return [
        (x["genomic_start"], x["genomic_end"], x["phase"], x["strand"])
        for x in intervals
    ]

def get_exon_intervals(db, transcript_id):
    """
    Backward-compatible wrapper.

    Returns list of (start, end, strand), matching the old API.
    """
    intervals = get_feature_intervals(db, transcript_id, "exon")
    return [(x["genomic_start"], x["genomic_end"], x["strand"]) for x in intervals]

def build_transcript_segments(intervals):
    """
    Build strand-aware transcript-space segments from genomic intervals.

    Input can be either:
    - list of dicts with genomic_start/genomic_end/strand/phase
    - list of tuples from get_exon_intervals or get_cds_exons

    Output uses a single consistent schema:
    genomic_start, genomic_end, transcript_start, transcript_end, strand, phase.
    """
    if not intervals:
        return []

    normalised = []
    for item in intervals:
        if isinstance(item, dict):
            normalised.append(
                {
                    "genomic_start": int(item["genomic_start"]),
                    "genomic_end": int(item["genomic_end"]),
                    "strand": item["strand"],
                    "phase": item.get("phase"),
                }
            )
        elif len(item) == 3:
            start, end, strand = item
            normalised.append(
                {
                    "genomic_start": int(start),
                    "genomic_end": int(end),
                    "strand": strand,
                    "phase": None,
                }
            )
        elif len(item) == 4:
            start, end, phase, strand = item
            normalised.append(
                {
                    "genomic_start": int(start),
                    "genomic_end": int(end),
                    "strand": strand,
                    "phase": normalize_phase_value(phase),
                }
            )
        else:
            raise ValueError(f"Unexpected interval format: {item}")

    strand = normalised[0]["strand"]
    ordered = normalised if strand == "+" else list(reversed(normalised))

    segments = []
    cursor = 0
    for item in ordered:
        seg_len = item["genomic_end"] - item["genomic_start"] + 1
        segments.append(
            {
                "genomic_start": item["genomic_start"],
                "genomic_end": item["genomic_end"],
                "transcript_start": cursor,
                "transcript_end": cursor + seg_len - 1,
                "strand": item["strand"],
                "phase": item.get("phase"),
            }
        )
        cursor += seg_len

    return segments

def build_exon_segments(exons):
    """Backward-compatible wrapper around build_transcript_segments()."""
    return build_transcript_segments(exons)

def build_cds_segments(cds_exons):
    """Backward-compatible wrapper around build_transcript_segments()."""
    return build_transcript_segments(cds_exons)

def genomic_to_tx_offset_in_segment(seg, genomic_pos):
    """Map a genomic coordinate inside a segment to transcript-space offset."""
    genomic_pos = int(genomic_pos)

    if seg["strand"] == "+":
        within = genomic_pos - int(seg["genomic_start"])
    else:
        within = int(seg["genomic_end"]) - genomic_pos

    return int(seg["transcript_start"]) + within

def build_cds_tx_segments(cds_exons, exon_segments):
    """
    Project CDS intervals onto transcript-space coordinates using exon segments.

    This replaces the duplicated CDS/exon coordinate handling.
    """
    if not cds_exons or not exon_segments:
        return []

    cds_intervals = []
    for start, end, phase, strand in cds_exons:
        cds_intervals.append(
            {
                "genomic_start": int(start),
                "genomic_end": int(end),
                "strand": strand,
                "phase": normalize_phase_value(phase),
            }
        )

    projected = []
    for cds in cds_intervals:
        for exon in exon_segments:
            ov_start = max(cds["genomic_start"], int(exon["genomic_start"]))
            ov_end = min(cds["genomic_end"], int(exon["genomic_end"]))

            if ov_start > ov_end:
                continue

            tx_start = genomic_to_tx_offset_in_segment(exon, ov_start)
            tx_end = genomic_to_tx_offset_in_segment(exon, ov_end)

            if tx_start > tx_end:
                tx_start, tx_end = tx_end, tx_start

            projected.append(
                {
                    "tx_start": int(tx_start),
                    "tx_end": int(tx_end),
                    "genomic_start": int(ov_start),
                    "genomic_end": int(ov_end),
                    "phase": cds["phase"],
                    "strand": cds["strand"],
                }
            )

    projected.sort(key=lambda x: (x["tx_start"], x["tx_end"]))
    return projected

def intersect_tx_segments(segments, start_tx, end_tx_exclusive=None):
    """
    Return transcript-space pieces overlapping [start_tx, end_tx_exclusive).

    If end_tx_exclusive is None, retain until the end of the transcript/CDS chain.
    """
    if not segments:
        return []

    start = int(start_tx)
    end = None if end_tx_exclusive is None else int(end_tx_exclusive)
    pieces = []

    for seg in segments:
        seg_start = int(seg.get("tx_start", seg.get("transcript_start")))
        seg_end_excl = int(seg.get("tx_end", seg.get("transcript_end"))) + 1

        ov_start = max(start, seg_start)
        ov_end_excl = seg_end_excl if end is None else min(end, seg_end_excl)

        if ov_end_excl <= ov_start:
            continue

        offset = ov_start - seg_start
        length = ov_end_excl - ov_start

        if seg["strand"] == "+":
            genomic_start = int(seg["genomic_start"]) + offset
            genomic_end = genomic_start + length - 1
        else:
            genomic_end = int(seg["genomic_end"]) - offset
            genomic_start = genomic_end - length + 1

        pieces.append(
            {
                "tx_start": int(ov_start),
                "tx_end": int(ov_end_excl - 1),
                "genomic_start": int(genomic_start),
                "genomic_end": int(genomic_end),
                "phase": seg.get("phase"),
                "strand": seg.get("strand"),
                "length": int(length),
            }
        )

    return pieces

def coding_bases_in_tx_range(cds_tx_segments, start_tx, end_tx_exclusive):
    """Count CDS bases overlapping [start_tx, end_tx_exclusive)."""
    return sum(
        piece["length"]
        for piece in intersect_tx_segments(cds_tx_segments, start_tx, end_tx_exclusive)
    )

def retained_tx_overlap_segments(cds_tx_segments, start_tx, end_tx_exclusive=None):
    """Backward-compatible wrapper around intersect_tx_segments()."""
    return intersect_tx_segments(cds_tx_segments, start_tx, end_tx_exclusive)

def retained_segment_lengths_prefix(segments, prefix_len):
    """Return retained segment lengths for prefix [0, prefix_len)."""
    return [piece["length"] for piece in intersect_tx_segments(segments, 0, prefix_len)]

def retained_segment_lengths_suffix(segments, suffix_start):
    """Return retained segment lengths for suffix [suffix_start, end)."""
    return [
        piece["length"] for piece in intersect_tx_segments(segments, suffix_start, None)
    ]

def extract_interval_sequence(genome, chrom, start, end):
    """Extract 1-based inclusive genomic interval sequence."""
    if start is None or end is None:
        return None

    start = int(start)
    end = int(end)

    if start <= 0 or end < start:
        return None

    resolved = resolve_chrom_name(genome, chrom)
    if resolved is None:
        return None

    try:
        record = genome[resolved]
        segment = record[start - 1 : end]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        logger.debug("Could not extract %s:%s-%s: %s", chrom, start, end, e)
        return None

    return str(segment.seq) if hasattr(segment, "seq") else str(segment)

def extract_sequence_from_segments(genome, chrom, segments):
    """
    Extract and concatenate transcript-oriented sequence from genomic segments.
    """
    if not segments:
        return None

    seq_parts = []

    for seg in segments:
        seq = extract_interval_sequence(
            genome,
            chrom,
            int(seg["genomic_start"]),
            int(seg["genomic_end"]),
        )

        if not seq:
            logger.debug(
                (
                    "Sequence extraction failed: "
                    "chrom=%s genomic=%d-%d strand=%s "
                    "tx=%s-%s"
                ),
                chrom,
                int(seg["genomic_start"]),
                int(seg["genomic_end"]),
                seg.get("strand", "?"),
                seg.get("tx_start", seg.get("transcript_start")),
                seg.get("tx_end", seg.get("transcript_end")),
            )
            return None

        if seg.get("strand") == "-":
            seq = str(Seq(seq).reverse_complement())

        seq_parts.append(seq)

    return "".join(seq_parts)

def extract_coding_sequence_from_pieces(genome, chrom, pieces):
    """Backward-compatible wrapper."""
    return extract_sequence_from_segments(genome, chrom, pieces)

def extract_cds_sequence(db, transcript_id, genome, chrom):
    """
    Extract full transcript-oriented CDS sequence and CDS segments.

    Returns:
        cds_sequence, strand, cds_segments
    """
    try:
        resolved_chrom = resolve_chrom_name(genome, chrom)
        if resolved_chrom is None:
            logger.debug("Chromosome %s not found in genome", chrom)
            return None, None, None

        cds_exons = get_cds_exons(db, transcript_id)
        if not cds_exons:
            return None, None, None

        cds_segments = build_cds_segments(cds_exons)
        if not cds_segments:
            return None, None, None

        strand = cds_segments[0]["strand"]
        cds_seq = extract_sequence_from_segments(genome, resolved_chrom, cds_segments)

        if not cds_seq:
            return None, None, None

        return cds_seq, strand, cds_segments

    except (KeyError, AttributeError, TypeError, ValueError, IndexError) as e:
        logger.debug("Error extracting CDS sequence for %s: %s", transcript_id, e)
        return None, None, None

def segment_tx_start_genomic(seg):
    """Return genomic coordinate of transcript-direction segment start."""
    return (
        int(seg["genomic_start"]) if seg["strand"] == "+" else int(seg["genomic_end"])
    )

def segment_tx_end_genomic(seg):
    """Return genomic coordinate of transcript-direction segment end."""
    return (
        int(seg["genomic_end"]) if seg["strand"] == "+" else int(seg["genomic_start"])
    )

def make_breakpoint_result(
    tx_offset,
    resolved_genomic_pos,
    location_type,
    segment=None,
    reported_genomic_pos=None,
):
    """Create a consistent breakpoint-resolution dictionary."""
    snap_distance = None
    if reported_genomic_pos is not None and resolved_genomic_pos is not None:
        try:
            snap_distance = abs(int(reported_genomic_pos) - int(resolved_genomic_pos))
        except (TypeError, ValueError):
            snap_distance = None

    record = {
        "tx_offset": int(tx_offset),
        "resolved_genomic_pos": int(resolved_genomic_pos),
        "location_type": location_type,
        "segment": segment,
        "snap_distance_nt": snap_distance,
    }
    return record

def nearest_breakpoint_boundary(segments, genomic_pos, role):
    """
    Snap breakpoint outside the transcript span to the nearest transcript boundary.
    """
    if genomic_pos is None or not segments:
        return None

    candidates = []

    for seg in segments:
        if role == "donor":
            tx_offset = int(seg["transcript_end"])
            boundary_gpos = segment_tx_end_genomic(seg)
        elif role == "acceptor":
            tx_offset = int(seg["transcript_start"])
            boundary_gpos = segment_tx_start_genomic(seg)
        else:
            raise ValueError("role must be 'donor' or 'acceptor'")

        candidates.append(
            (
                abs(int(genomic_pos) - int(boundary_gpos)),
                tx_offset,
                boundary_gpos,
                seg,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    _, tx_offset, boundary_gpos, seg = candidates[0]

    return make_breakpoint_result(
        tx_offset=tx_offset,
        resolved_genomic_pos=boundary_gpos,
        location_type="outside_snapped",
        segment=seg,
        reported_genomic_pos=genomic_pos,
    )

def resolve_breakpoint_on_exon_chain(segments, genomic_pos, role):
    """
    Resolve a genomic breakpoint against a transcript exon chain.

    Resolution priority:
    1. exonic coordinate
    2. intronic coordinate snapped to splice junction
    3. outside transcript span snapped to nearest boundary
    """
    if genomic_pos is None or not segments:
        return None

    if role not in {"donor", "acceptor"}:
        raise ValueError("role must be 'donor' or 'acceptor'")

    pos = int(genomic_pos)

    # 1. Exonic breakpoint.
    for seg in segments:
        gs = int(seg["genomic_start"])
        ge = int(seg["genomic_end"])

        if gs <= pos <= ge:
            tx_offset = genomic_to_tx_offset_in_segment(seg, pos)
            expected_boundary = (
                segment_tx_end_genomic(seg) if role == "donor"
                else segment_tx_start_genomic(seg)
            )
            return make_breakpoint_result(
                tx_offset=tx_offset,
                resolved_genomic_pos=pos,
                location_type=("annotated_boundary" if pos == expected_boundary else "exonic"),
                segment=seg,
                reported_genomic_pos=pos,
            )

    # 2. Intronic breakpoint between adjacent transcript-ordered exons.
    for i in range(len(segments) - 1):
        left = segments[i]
        right = segments[i + 1]

        intron_start = min(int(left["genomic_end"]), int(right["genomic_end"])) + 1
        intron_end = max(int(left["genomic_start"]), int(right["genomic_start"])) - 1

        if intron_start <= pos <= intron_end:
            if role == "donor":
                tx_offset = int(left["transcript_end"])
                resolved_gpos = segment_tx_end_genomic(left)
                chosen_seg = left
            else:
                tx_offset = int(right["transcript_start"])
                resolved_gpos = segment_tx_start_genomic(right)
                chosen_seg = right

            return make_breakpoint_result(
                tx_offset=tx_offset,
                resolved_genomic_pos=resolved_gpos,
                location_type="intronic_splice_junction",
                segment=chosen_seg,
                reported_genomic_pos=pos,
            )

    # 3. Outside transcript span.
    return nearest_breakpoint_boundary(segments, pos, role)

def map_genomic_to_transcript_offset(segments, genomic_pos):
    """
    Backward-compatible genomic-to-transcript mapper.

    Returns:
        offset, segment, within_segment_offset
    """
    if genomic_pos is None or not segments:
        return None, None, None

    pos = int(genomic_pos)

    for seg in segments:
        gs = int(seg["genomic_start"])
        ge = int(seg["genomic_end"])

        if gs <= pos <= ge:
            offset = genomic_to_tx_offset_in_segment(seg, pos)
            within = pos - gs if seg["strand"] == "+" else ge - pos
            return offset, seg, within

    return None, None, None

def update_breakpoint_metadata(metadata, donor_resolved, acceptor_resolved):
    """Populate breakpoint-resolution fields in the metadata."""

    metadata.donor_breakpoint_location = donor_resolved.get("location_type")
    metadata.acceptor_breakpoint_location = acceptor_resolved.get("location_type")

    metadata.donor_resolved_genomic_pos = donor_resolved.get("resolved_genomic_pos")
    metadata.acceptor_resolved_genomic_pos = acceptor_resolved.get(
        "resolved_genomic_pos"
    )

    metadata.donor_breakpoint_snap_distance_nt = donor_resolved.get("snap_distance_nt")
    metadata.acceptor_breakpoint_snap_distance_nt = acceptor_resolved.get(
        "snap_distance_nt"
    )

    return metadata

def summarize_junction_codon_state(junction_nt):
    """Summarize how many codon bases lie on each side of a junction."""
    summary = {
        "fusion_junction_frame_remainder": None,
        "junction_codon_spans_breakpoint": None,
        "junction_codon_bases_on_donor": None,
        "junction_codon_bases_on_acceptor": None,
        "junction_codon_side": None,
    }
    if junction_nt is None:
        return summary
    remainder = int(junction_nt) % 3
    summary["fusion_junction_frame_remainder"] = remainder
    if remainder == 0:
        summary.update({
            "junction_codon_spans_breakpoint": False,
            "junction_codon_bases_on_donor": 0,
            "junction_codon_bases_on_acceptor": 0,
            "junction_codon_side": "boundary",
        })
        return summary
    donor_bases = remainder
    acceptor_bases = 3 - remainder
    summary.update({
        "junction_codon_spans_breakpoint": True,
        "junction_codon_bases_on_donor": donor_bases,
        "junction_codon_bases_on_acceptor": acceptor_bases,
        "junction_codon_side": "donor" if donor_bases > acceptor_bases else "acceptor",
    })
    return summary

def update_junction_metadata(
    metadata,
    donor_fragment,
    acceptor_fragment,
    donor_cds_segments,
    acceptor_cds_segments,
    cds_tx_segments2,
    acceptor_start_tx,
):
    """Populate fusion-junction and exon-junction metadata."""

    donor_len = len(donor_fragment)
    acceptor_cds_start = coding_bases_in_tx_range(
        cds_tx_segments2,
        0,
        acceptor_start_tx,
    )

    junction_summary = summarize_junction_codon_state(donor_len)

    metadata.fusion_junction_frame_remainder = junction_summary[
        "fusion_junction_frame_remainder"
    ]
    metadata.junction_codon_spans_breakpoint = junction_summary[
        "junction_codon_spans_breakpoint"
    ]
    metadata.junction_codon_bases_on_donor = junction_summary[
        "junction_codon_bases_on_donor"
    ]
    metadata.junction_codon_bases_on_acceptor = junction_summary[
        "junction_codon_bases_on_acceptor"
    ]
    metadata.junction_codon_side = junction_summary["junction_codon_side"]

    donor_lengths = retained_segment_lengths_prefix(
        donor_cds_segments,
        donor_len,
    )

    acceptor_lengths = retained_segment_lengths_suffix(
        acceptor_cds_segments,
        acceptor_cds_start,
    )

    metadata.exon_junction_nt_positions = exon_junction_positions_from_segment_lengths(
        donor_lengths,
        acceptor_lengths,
    )

    metadata.donor_split_offset = donor_len - 1
    metadata.acceptor_split_offset = acceptor_cds_start

    metadata.fusion_junction_nt = donor_len
    metadata.junction_nt = donor_len
    metadata.junction_aa = donor_len // 3

    return metadata

def update_frame_and_stop_metadata(
    metadata,
    fused_cds,
    donor_coding_pieces,
    acceptor_coding_pieces,
    cds_tx_segments1,
    cds_tx_segments2,
    donor_prefix_end_tx,
    acceptor_start_tx,
    early_stop_aa_cutoff,
):
    """Populate frame-status and early-stop metadata."""

    seq_based_frame = "INFRAME" if len(fused_cds) % 3 == 0 else "FRAMESHIFT"

    meta_frame = seq_based_frame

    donor_phase = donor_coding_pieces[-1].get("phase") if donor_coding_pieces else None

    acceptor_phase = (
        acceptor_coding_pieces[0].get("phase") if acceptor_coding_pieces else None
    )

    metadata.donor_phase_missing = donor_phase is None
    metadata.acceptor_phase_missing = acceptor_phase is None
    metadata.phase_inferred = donor_phase is None or acceptor_phase is None
    metadata.frame_inference_method = (
        "sequence_length_fallback" if metadata.phase_inferred else "annotated_gtf_phase"
    )

    if donor_phase is not None and acceptor_phase is not None:

        donor_len = coding_bases_in_tx_range(
            cds_tx_segments1,
            0,
            donor_prefix_end_tx,
        )

        acceptor_within = coding_bases_in_tx_range(
            cds_tx_segments2,
            0,
            acceptor_start_tx,
        )

        phase_call = compute_frame_status(
            donor_len,
            acceptor_within,
            normalize_phase_value(donor_phase),
            normalize_phase_value(acceptor_phase),
        )

        if phase_call in {"INFRAME", "FRAMESHIFT"}:
            meta_frame = phase_call

    metadata.frame_status = meta_frame

    # Search the complete reconstructed ORF. Translation begins at nucleotide 1,
    # so a retained donor stop codon may terminate translation before the RNA
    # fusion junction is reached.
    stop_nt = first_in_frame_stop_codon_nt(fused_cds, 1)
    junction_nt = parse_int_or_none(metadata.fusion_junction_nt)

    metadata.first_stop_codon_nt_start_1based = stop_nt
    metadata.first_stop_codon_nt_end_1based = (
        stop_nt + 2 if stop_nt is not None else None
    )

    if junction_nt is not None:
        acceptor_start_nt_1based = junction_nt + 1

        if stop_nt is None:
            metadata.stop_before_junction = False
            metadata.translation_reaches_junction = True
            metadata.translation_crosses_junction = True
        else:
            stop_end_nt = stop_nt + 2
            metadata.stop_before_junction = stop_end_nt < acceptor_start_nt_1based
            # A downstream stop still means that translation reached the
            # fusion boundary. The old interval-containment test incorrectly
            # marked all such products as not reaching the junction.
            metadata.translation_reaches_junction = stop_end_nt >= junction_nt
            metadata.translation_crosses_junction = (
                stop_end_nt >= acceptor_start_nt_1based
            )

            if metadata.stop_before_junction:
                metadata.reason = "translation_stops_before_junction"
            elif meta_frame == "FRAMESHIFT":
                stop_aa_distance = (stop_nt - junction_nt) / 3.0
                if stop_aa_distance <= early_stop_aa_cutoff:
                    metadata.low_confidence = True
                    metadata.reason = "early_stop_after_junction"

    return metadata

def compute_frame_status(donor_len, acceptor_within, donor_phase, acceptor_phase):
    """Compatibility wrapper around the single shared phase implementation."""
    result = classify_phased_junction_frame(
        donor_len, acceptor_within, donor_phase, acceptor_phase
    )
    if result == "NA":
        logger.debug(
            "Phase information unavailable for frame determination "
            "(donor_phase=%s, acceptor_phase=%s). "
            "Using sequence-length frame classification.",
            donor_phase,
            acceptor_phase,
        )
    return result

def exon_junction_positions_from_segment_lengths(donor_lengths, acceptor_lengths):
    """Return 1-based exon-junction positions in fused transcript coordinates."""
    positions = []
    cursor = 0

    for idx, seg_len in enumerate(donor_lengths):
        cursor += int(seg_len)
        if idx < len(donor_lengths) - 1:
            positions.append(cursor)

    for idx, seg_len in enumerate(acceptor_lengths):
        cursor += int(seg_len)
        if idx < len(acceptor_lengths) - 1:
            positions.append(cursor)

    return positions

def first_in_frame_stop_codon_nt(seq, start_nt_1based):
    """Return 1-based start nucleotide of first in-frame stop codon, else None."""
    if not seq or start_nt_1based is None:
        return None

    start_idx = max(0, int(start_nt_1based) - 1)
    stop_codons = {"TAA", "TAG", "TGA"}
    for idx in range(start_idx, len(seq) - 2, 3):
        codon = str(seq[idx : idx + 3]).upper()
        if codon in stop_codons:
            return idx + 1
    return None

def build_nmd_metadata(reason=None):
    """Build a standard NMD metadata payload."""
    return {
        "nmd_predicted": None,
        "nmd_reason": reason,
        "stop_codon_nt_start_1based": None,
        "stop_codon_nt_end_1based": None,
        "nearest_downstream_exon_junction_nt": None,
        "nmd_distance_nt": None,
    }

def model_nmd_status(
    cds_seq, orf_start_nt_1based, exon_junction_positions, distance_threshold_nt=55
):
    """Model NMD likelihood using stop-codon distance to downstream exon junctions."""
    result = build_nmd_metadata()

    if not cds_seq or orf_start_nt_1based is None:
        result["nmd_reason"] = "no_valid_orf"
        return result

    junctions = sorted({int(pos) for pos in (exon_junction_positions or [])})
    if not junctions:
        result["nmd_predicted"] = False
        result["nmd_reason"] = "intronless_transcript"
        return result

    stop_start = first_in_frame_stop_codon_nt(cds_seq, orf_start_nt_1based)
    if stop_start is None:
        result["nmd_predicted"] = False
        result["nmd_reason"] = "no_inframe_stop_codon"
        return result

    stop_end = stop_start + 2
    result["stop_codon_nt_start_1based"] = stop_start
    result["stop_codon_nt_end_1based"] = stop_end

    if stop_end >= max(junctions):
        result["nmd_predicted"] = False
        result["nmd_reason"] = "stop_in_last_exon"
        return result

    downstream = [int(pos) for pos in junctions if int(pos) > stop_end]
    if not downstream:
        result["nmd_predicted"] = False
        result["nmd_reason"] = "no_downstream_junction_after_stop"
        return result

    nearest_junction = min(downstream)
    distance_nt = nearest_junction - stop_end
    result["nearest_downstream_exon_junction_nt"] = nearest_junction
    result["nmd_distance_nt"] = distance_nt
    result["nmd_predicted"] = distance_nt >= int(distance_threshold_nt)
    result["nmd_reason"] = (
        "ptc_far_upstream_of_downstream_junction"
        if result["nmd_predicted"]
        else "stop_near_terminal_junction"
    )
    return result
