"""Exploratory translation rescue shared by the rMATS and SUPPA producers.

Both producers apply the same rules when ``--allow_alt_start`` or
``--allow_longest_orf`` is set:

* alternative start: the first in-frame codon from ``--alternative_start_codons``
  whose -6..+6 Kozak context reaches ``--min_alt_start_kozak_strength``;
* longest ORF: the longest stop-delimited ORF (>= ``--min_alt_orf_aa``) in any frame.

Rescue products are written to their own exploratory FASTAs, never the primary one.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

from Bio.Seq import Seq

from .splice_reconstruction_core import assess_alternative_start
from .splice_translation import _prepare_nt_for_translation

KOZAK_STRENGTH_RANK = {"weak": 0, "moderate": 1, "strong": 2}
RESCUE_STRATEGIES = frozenset({"alternative_start", "alternative_orf"})
ALT_START_NOTE_PREFIX = "translated_from_downstream_atg_nt_"


def normalise_start_codons(codons: Iterable[str]) -> tuple[list[str], list[str]]:
    """Return (DNA-normalised codons, invalid entries) for --alternative_start_codons."""
    normalised = [str(codon).upper().replace("U", "T") for codon in codons]
    return normalised, [codon for codon in normalised if not re.fullmatch(r"[ACGT]{3}", codon)]


def find_alternative_start(
    sequence: str,
    allowed_codons: Iterable[str] = ("ATG",),
    min_kozak_strength: str = "weak",
) -> Optional[int]:
    """Offset of the first in-frame allowed start codon meeting the Kozak threshold."""
    seq = (sequence or "").upper().replace("U", "T")
    allowed = {str(codon).upper().replace("U", "T") for codon in allowed_codons}
    minimum = KOZAK_STRENGTH_RANK[min_kozak_strength]
    for offset in range(0, len(seq) - 2, 3):
        if seq[offset:offset + 3] not in allowed:
            continue
        assessment = assess_alternative_start(seq, offset)
        if assessment.frame_conserved and KOZAK_STRENGTH_RANK[assessment.kozak_strength] >= minimum:
            return offset
    return None


def longest_orf_from_sequence(
    seq: str,
    pad: bool = False,
    min_alt_orf_aa: int = 30,
    translation_table: int = 1,
) -> Optional[str]:
    """Return the longest stop-delimited ORF across all three frames.

    Reserved for explicit exploratory rescue of sequences that cannot be
    translated as an annotated CDS-derived product.
    """
    seq_u = (seq or "").upper().replace("U", "T")
    best = ""
    for frame in range(3):
        frame_seq = _prepare_nt_for_translation(seq_u[frame:], pad=pad)
        if not frame_seq:
            continue
        aa = str(Seq(frame_seq).translate(table=translation_table, to_stop=False))
        for candidate in aa.split("*"):
            if len(candidate) >= min_alt_orf_aa and len(candidate) > len(best):
                best = candidate
    return best or None


def alternative_start_from_note(sequence: str, strategy: str, note: str):
    """Kozak assessment of the start encoded in an alternative-start translation note."""
    if strategy != "alternative_start":
        return None
    match = re.search(r"_nt_(\d+)$", note or "")
    return assess_alternative_start(sequence, int(match.group(1))) if match else None


def alternative_start_fields(alt_start) -> dict:
    """Audit columns describing an alternative start (None values when absent)."""
    return {
        "alt_start": "Yes" if alt_start else "No",
        "alt_start_codon": alt_start.codon if alt_start else None,
        "alt_start_offset_nt": alt_start.offset_nt if alt_start else None,
        "alt_start_frame_conserved": alt_start.frame_conserved if alt_start else None,
        "alt_start_kozak_strength": alt_start.kozak_strength if alt_start else None,
        "alt_start_kozak_score": alt_start.kozak_score if alt_start else None,
        "alt_start_kozak_context": alt_start.context_minus6_plus6 if alt_start else None,
    }
