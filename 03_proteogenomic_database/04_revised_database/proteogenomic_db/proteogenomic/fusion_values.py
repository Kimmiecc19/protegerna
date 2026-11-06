"""Canonical scalar and caller-value normalization for fusion processing."""
from __future__ import annotations
import hashlib
import re
from typing import Any, Optional
import pandas as pd
from .fusion_models import MISSING_TEXT_VALUES


def is_missing_text(value: Any) -> bool:
    """Return whether a caller field contains a supported missing placeholder."""
    return value is None or pd.isna(value) or str(value).strip() in MISSING_TEXT_VALUES

def normalize_gene_id(value: Any) -> Optional[str]:
    """
    Normalize gene identifiers from caller outputs.

    Keeps Ensembl gene IDs and strips version suffixes (e.g. ENSG... .12 -> ENSG...).
    Returns None for missing placeholders or unparsable values.
    """
    if is_missing_text(value):
        return None

    text = str(value).strip()
    # Prefer any ENSG-like token embedded in complex strings.
    match = re.search(r"(ENSG\d+(?:\.\d+)?)", text)
    if match:
        return match.group(1).split(".")[0]

    # If caller supplied a plain gene symbol or non-Ensembl token, keep as-is.
    return text

def normalize_gene_symbol(value: Any) -> Optional[str]:
    """Normalize gene symbols for robust symbol-index lookups."""
    if is_missing_text(value):
        return None

    text = str(value).strip()

    return text.upper()

def parse_int_or_none(value):
    """Safely parse integer-like values from caller outputs."""
    if value is None or pd.isna(value):
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None

def parse_bool_or_none(value):
    """Safely parse boolean-like values from mixed caller outputs."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if text in {"true", "t", "1", "yes", "y"}:
        return True
    if text in {"false", "f", "0", "no", "n"}:
        return False
    return None

def normalize_text_or_none(value: Any, peptide: bool = False) -> Optional[str]:
    """Normalize text fields; peptide=True keeps only amino-acid letters and '*' stops."""
    if is_missing_text(value):
        return None
    text = str(value).strip()
    if peptide:
        text = re.sub(r"[^A-Za-z*]", "", text).upper()
        if text.endswith("*"):
            text = text[:-1]
        return text if text else None
    return text

def classify_splice_support(value):
    """Classify splice-support labels: True (supported), False, or None when missing.

    ONLY_REF_SPLICE and other labels are treated as supported. NO_SPLICE and
    poor splice labels are treated as lower confidence.
    """
    text = normalize_text_or_none(value)
    if not text:
        return None

    token = re.sub(r"[^a-z0-9]+", "", text.lower())
    # NO_SPLICE / poor-splice labels fail; every other non-empty label passes.
    return not ("nosplice" in token or "poor" in token)

def first_existing_column(df, candidates):
    """Return the first column name present in df from a candidate list."""
    return next((col for col in candidates if col in df.columns), None)

def normalize_chrom_token(chrom):
    """Normalize chromosome labels for comparisons (chr1/1 and M/MT)."""
    if is_missing_text(chrom):
        return None
    token = str(chrom).strip()
    if token.lower().startswith("chr"):
        token = token[3:]
    token = token.upper()
    return "MT" if token == "M" else token

def chrom_matches(left, right):
    """Return whether two non-missing chromosome labels are equivalent."""
    left_token = normalize_chrom_token(left)
    right_token = normalize_chrom_token(right)
    return left_token is not None and left_token == right_token

def sequence_hash(sequence):
    """Return the canonical SHA-256 identity for a biological sequence."""
    return hashlib.sha256(str(sequence or "").encode("utf-8")).hexdigest()

def normalize_transcript_id(value: Any) -> Optional[str]:
    """Normalize transcript IDs and strip optional version suffixes."""
    if is_missing_text(value):
        return None

    text = str(value).strip()

    if "." in text:
        text = text.split(".")[0]

    return text

def extract_transcript_id_token(value: Any) -> Optional[str]:
    """Extract a likely transcript identifier token from mixed caller fields."""
    if is_missing_text(value):
        return None

    text = str(value).strip()

    # Prefer explicit Ensembl transcript tokens if present.
    m = re.search(r"(ENST\d+(?:\.\d+)?)", text)
    if m:
        return m.group(1)

    # Otherwise split common delimiter-packed fields and use the first non-empty token.
    for token in re.split(r"[|,;\s]+", text):
        token = token.strip()
        if token:
            return token

    return None

def split_breakpoint_value(value):
    """
    Parse a breakpoint value into (chromosome, position).

    Accepts values such as "chr1:12345", "1:12345", or "12345".
    Returns (None, None) when parsing fails.
    """
    if pd.isna(value):
        return None, None

    text = str(value).strip()
    if not text:
        return None, None

    # Supports both chr:pos and chr:pos:strand formats.
    m = re.match(r"^([^:]+):(\d+)(?::[+-])?$", text)
    if m:
        return m.group(1), int(m.group(2))

    if ":" in text:
        parts = text.split(":")
        if len(parts) >= 2:
            chrom = parts[0].strip() or None
            try:
                return chrom, int(parts[1])
            except (TypeError, ValueError):
                return chrom, None

    try:
        return None, int(text)
    except (TypeError, ValueError):
        return None, None

