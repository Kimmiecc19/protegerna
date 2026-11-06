"""rMATS file discovery, coordinate normalization, and event compatibility."""
from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple
import pandas as pd
from .splice_translation import merge_intervals
from .suppa_parsing import expand_file_patterns


def normalise_event_file_lists(args):
    """Expand, sort, and de-duplicate rMATS event-file patterns by type."""
    event_patterns = {
        "SE": args.se_files,
        "A3SS": args.a3ss_files,
        "A5SS": args.a5ss_files,
        "MXE": args.mxe_files,
        "RI": args.ri_files,
    }
    event_files = {}
    for event_type, values in event_patterns.items():
        if isinstance(values, str):
            values = [x for x in re.split(r"[,\s]+", values) if x]
        event_files[event_type] = expand_file_patterns(values, f"{event_type} event")
    return event_files


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return not (a_end < b_start or b_end < a_start)


def _safe_int(value) -> Optional[int]:
    """Safely coerce rMATS coordinate values to integers."""
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


RMATS_COORDINATE_BASE = {
    # rMATS genomic starts are 0-based; genomic ends are 1-based inclusive.
    "exonStart_0base": 0,
    "longExonStart_0base": 0, "longExonStart": 0,
    "shortES": 0, "flankingES": 0,
    "shortExonStart_0base": 0, "shortExonStart": 0,
    "1stExonStart_0base": 0, "X1stExonStart_0base": 0,
    "2ndExonStart_0base": 0, "X2ndExonStart_0base": 0,
    "riExonStart_0base": 0, "downstreamES": 0,
    "exonEnd": 1, "longExonEnd": 1, "longExonEnd_0base": 1,
    "shortEE": 1, "flankingEE": 1,
    "shortExonEnd": 1, "shortExonEnd_0base": 1,
    "1stExonEnd": 1, "X1stExonEnd": 1,
    "2ndExonEnd": 1, "X2ndExonEnd": 1,
    "riExonEnd": 1, "upstreamEE": 1,
}


def _row_int(row: dict, names: List[str], zero_based: bool = False) -> Optional[int]:
    """Return the first available coordinate from an rMATS row.

    rMATS columns ending in `_0base` represent 0-based starts and must be
    converted to 1-based inclusive coordinates before comparison with GTF/CDS
    coordinates. When mixed column names are supplied, conversion is applied
    only to the selected column when that column is explicitly marked `_0base`.
    The `zero_based` argument is retained for backwards compatibility for calls
    where all candidate names are known to be 0-based.
    """
    for name in names:
        if name in row:
            value = _safe_int(row.get(name))
            if value is not None:
                if name not in RMATS_COORDINATE_BASE:
                    raise ValueError(
                        f"Unknown rMATS coordinate column {name!r}; add its base "
                        "explicitly to RMATS_COORDINATE_BASE"
                    )
                convert_from_zero_based = zero_based and RMATS_COORDINATE_BASE[name] == 0
                return value + 1 if convert_from_zero_based else value
    return None


def _rmats_start_1based(row: dict, names: List[str]) -> Optional[int]:
    """Read an rMATS exon-start field and convert its 0-based value to 1-based.

    Conversion follows RMATS_COORDINATE_BASE, so already 1-based fallback names
    are not shifted. Standard start columns such as ``shortES`` and
    ``downstreamES`` are 0-based even though their names omit ``_0base``.
    """
    return _row_int(row, names, zero_based=True)


# Former name of _rmats_start_1based (identical behaviour), kept for callers.
_row_int_auto = _rmats_start_1based


def _normalise_chrom(chrom: Optional[str]) -> Optional[str]:
    """Normalise chromosome names for loose comparisons only."""
    if chrom is None:
        return None
    c = str(chrom).strip()
    if not c or c.lower() == "nan":
        return None
    return c[3:] if c.startswith("chr") else c


def _row_chrom(row: dict) -> Optional[str]:
    """Extract an rMATS chromosome field if present."""
    for key in ("chr", "chrom", "Chromosome", "seqname"):
        if key in row and pd.notna(row[key]):
            return str(row[key]).strip()
    return None


def rmats_event_intervals(event_type: str, row: dict) -> List[Tuple[int, int]]:
    """Return event-defining genomic intervals for an rMATS row.

    These intervals are used only for transcript pre-filtering. The downstream
    exon-chain reconstruction remains the source of truth for sequence building.
    """
    event_type = str(event_type or "").upper()
    intervals: List[Tuple[int, int]] = []

    def add_interval(start: Optional[int], end: Optional[int]) -> None:
        if start is None or end is None:
            return
        s, e = int(start), int(end)
        if s > e:
            s, e = e, s
        if e >= s:
            intervals.append((s, e))

    if event_type == "SE":
        add_interval(
            _row_int_auto(row, ["exonStart_0base"]),
            _row_int(row, ["exonEnd"]),
        )

    elif event_type in {"A3SS", "A5SS"}:
        # Include both long and short exon spans. This intentionally errs on the
        # side of keeping a transcript when either alternative boundary touches
        # coding sequence; identical-CDS/protein filters below remove neutral cases.
        add_interval(
            _rmats_start_1based(row, ["longExonStart_0base", "longExonStart"]),
            _row_int(row, ["longExonEnd", "longExonEnd_0base"]),
        )
        add_interval(
            _rmats_start_1based(row, ["shortES", "shortExonStart_0base", "shortExonStart"]),
            _row_int(row, ["shortEE", "shortExonEnd", "shortExonEnd_0base"]),
        )

    elif event_type == "MXE":
        add_interval(
            _row_int_auto(row, ["1stExonStart_0base", "X1stExonStart_0base"]),
            _row_int(row, ["1stExonEnd", "X1stExonEnd"]),
        )
        add_interval(
            _row_int_auto(row, ["2ndExonStart_0base", "X2ndExonStart_0base"]),
            _row_int(row, ["2ndExonEnd", "X2ndExonEnd"]),
        )

    elif event_type == "RI":
        ri_s = _row_int_auto(row, ["riExonStart_0base"])
        ri_e = _row_int(row, ["riExonEnd"])
        up_e = _row_int(row, ["upstreamEE"])
        down_s = _rmats_start_1based(row, ["downstreamES"])
        if up_e is not None and down_s is not None:
            add_interval(up_e + 1, down_s - 1)
        else:
            add_interval(ri_s, ri_e)

    return merge_intervals(intervals)


def event_overlaps_transcript_cds(event_type: str, row: dict, tx_model: Dict) -> bool:
    """True when an rMATS event plausibly touches this transcript's CDS.

    This is the first transcript-explosion filter. It removes transcripts that
    belong to the same gene but whose coding sequence cannot be affected by the
    rMATS event coordinates.
    """
    cds = tx_model.get("cds") or []
    if not cds:
        return False

    if str(event_type or "").upper() == "RI":
        # A spliced reference transcript has no CDS bases inside the retained
        # intron. Exact flanking exon boundaries establish coding compatibility.
        return transcript_is_event_compatible(event_type, row, tx_model)

    row_c = _normalise_chrom(_row_chrom(row))
    tx_c = _normalise_chrom(tx_model.get("chrom"))
    if row_c and tx_c and row_c != tx_c:
        return False

    event_intervals = rmats_event_intervals(event_type, row)
    if not event_intervals:
        return False

    for ev_s, ev_e in event_intervals:
        for cds_s, cds_e, _frame in cds:
            if overlaps(ev_s, ev_e, cds_s, cds_e):
                return True
    return False


def transcript_is_event_compatible(event_type: str, row: dict, tx_model: Dict) -> bool:
    """Require the annotated transcript to represent an rMATS event boundary."""
    exons = set(tuple(x) for x in (tx_model.get("exons") or []))
    event_type = str(event_type or "").upper()

    if event_type == "SE":
        exon = (_rmats_start_1based(row, ["exonStart_0base"]), _row_int(row, ["exonEnd"]))
        return None not in exon and exon in exons
    if event_type in {"A3SS", "A5SS"}:
        long_exon = (
            _rmats_start_1based(row, ["longExonStart_0base", "longExonStart"]),
            _row_int(row, ["longExonEnd", "longExonEnd_0base"]),
        )
        short_exon = (
            _rmats_start_1based(row, ["shortES", "shortExonStart_0base", "shortExonStart"]),
            _row_int(row, ["shortEE", "shortExonEnd", "shortExonEnd_0base"]),
        )
        return (None not in long_exon and long_exon in exons) or (None not in short_exon and short_exon in exons)
    if event_type == "MXE":
        exon1 = (_rmats_start_1based(row, ["1stExonStart_0base", "X1stExonStart_0base"]), _row_int(row, ["1stExonEnd", "X1stExonEnd"]))
        exon2 = (_rmats_start_1based(row, ["2ndExonStart_0base", "X2ndExonStart_0base"]), _row_int(row, ["2ndExonEnd", "X2ndExonEnd"]))
        return (None not in exon1 and exon1 in exons) or (None not in exon2 and exon2 in exons)
    if event_type == "RI":
        upstream_end = _row_int(row, ["upstreamEE"])
        downstream_start = _rmats_start_1based(row, ["downstreamES"])
        retained_exon = (
            _rmats_start_1based(row, ["riExonStart_0base"]),
            _row_int(row, ["riExonEnd"]),
        )
        has_retained_model = None not in retained_exon and retained_exon in exons
        if upstream_end is None or downstream_start is None:
            return has_retained_model
        has_spliced_flanks = (
            any(end == upstream_end for _start, end in exons)
            and any(start == downstream_start for start, _end in exons)
        )
        return has_retained_model or has_spliced_flanks
    return False
