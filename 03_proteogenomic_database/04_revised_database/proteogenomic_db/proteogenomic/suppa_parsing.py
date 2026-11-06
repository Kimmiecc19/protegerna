"""SUPPA input discovery and event-coordinate parsing."""
from __future__ import annotations
import logging
import re
from glob import glob
from typing import Optional
import pandas as pd


def expand_file_patterns(patterns, label, require_each=False):
    """Expand, sort, and de-duplicate file globs while preserving order.

    With ``require_each`` an unmatched pattern is an error instead of a warning.
    """
    files = []
    for pattern in patterns or []:
        matches = sorted(glob(pattern, recursive=True))
        if matches:
            files.extend(matches)
        elif require_each:
            raise FileNotFoundError(f"No {label} files matched pattern: {pattern}")
        else:
            logging.warning("No %s files matched pattern: %s", label, pattern)
    return list(dict.fromkeys(files))


def split_list_field(val):
    if pd.isna(val):
        return []
    s = str(val).strip()
    if s in ("", "."):
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def normalise_event_id(event_id: object) -> Optional[str]:
    """Return a clean SUPPA event identifier suitable for exact matching.

    SUPPA writes the same event identifier to the IOE ``event_id`` field and
    to the unlabeled first column of the PSI matrix. Normalisation is therefore
    deliberately conservative: missing values are rejected and surrounding
    whitespace is removed without altering coordinates, gene versions, or event
    syntax.
    """
    if event_id is None or pd.isna(event_id):
        return None
    value = str(event_id).strip()
    return value or None


def parse_suppa_event_coords(event_id: str):
    if not isinstance(event_id, str):
        logging.warning("Malformed SUPPA event ID (expected text): %r", event_id)
        return None
    parts = [p for p in re.split(r"[;\t]", event_id) if p]
    for p in parts:
        if "chr" in p and ":" in p:
            toks = p.split(":")
            # SUPPA event tokens have the form: TYPE:chr:range1:range2:...:strand
            # capture all intermediate range tokens (toks[2:-1]) so callers
            # can decide which ones are relevant per event type.
            if len(toks) >= 4:
                return {
                    "etype": toks[0],
                    "chrom": toks[1],
                    "ranges": toks[2:-1],
                    "strand": toks[-1],
                }
    logging.warning("Malformed SUPPA event ID; coordinates could not be parsed: %s", event_id)
    return None
