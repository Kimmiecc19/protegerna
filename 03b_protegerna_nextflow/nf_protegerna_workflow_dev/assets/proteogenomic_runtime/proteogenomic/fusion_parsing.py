"""Caller-specific fusion parsing with no reconstruction dependencies."""
from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

import pandas as pd
from .fusion_values import (
    classify_splice_support,
    extract_transcript_id_token,
    first_existing_column,
    split_breakpoint_value,
)

LOGGER = logging.getLogger(__name__)


def parse_fusioninspector(
    source: pd.DataFrame, output_columns: Sequence[str]
) -> pd.DataFrame:
    """Normalize FusionInspector rows without mutating the caller dataframe."""
    df = source.copy()
    required = {"LeftBreakpoint", "RightBreakpoint", "LeftGene", "RightGene"}
    if not required.issubset(df.columns):
        LOGGER.warning("FusionInspector missing required columns: %s", sorted(required - set(df.columns)))
        return pd.DataFrame(columns=output_columns)

    def split_gene(value: Any) -> tuple[Optional[str], Optional[str]]:
        if value is None or pd.isna(value):
            return None, None
        symbol, separator, gene_id = str(value).strip().partition("^")
        return symbol or None, (gene_id or None) if separator else None

    left = df["LeftGene"].apply(split_gene)
    right = df["RightGene"].apply(split_gene)
    left_bp = df["LeftBreakpoint"].apply(split_breakpoint_value)
    right_bp = df["RightBreakpoint"].apply(split_breakpoint_value)
    df["gene_1_symbol"] = left.apply(lambda item: item[0])
    df["gene_2_symbol"] = right.apply(lambda item: item[0])
    df["gene_1_id"] = left.apply(lambda item: item[1])
    df["gene_2_id"] = right.apply(lambda item: item[1])
    df["chrom1"] = left_bp.apply(lambda item: item[0])
    df["breakpoint1"] = left_bp.apply(lambda item: item[1])
    df["chrom2"] = right_bp.apply(lambda item: item[0])
    df["breakpoint2"] = right_bp.apply(lambda item: item[1])
    df = df.dropna(subset=["breakpoint1", "breakpoint2"])
    tx1 = first_existing_column(df, ["CDS_LEFT_ID", "LeftTranscript", "LeftTranscriptID", "LeftTrans"])
    tx2 = first_existing_column(df, ["CDS_RIGHT_ID", "RightTranscript", "RightTranscriptID", "RightTrans"])
    df["tx_1_id"] = df[tx1].apply(extract_transcript_id_token) if tx1 else None
    df["tx_2_id"] = df[tx2].apply(extract_transcript_id_token) if tx2 else None
    split = first_existing_column(df, ["JunctionReadCount", "JunctionReads"])
    span = first_existing_column(df, ["SpanningFragCount", "SpanningFrags"])
    orientation = first_existing_column(df, ["SpliceType", "ORF"])
    df["split_reads"] = df[split] if split else None
    df["spanning_reads"] = df[span] if span else None
    df["confidence"] = None
    df["caller_annotations"] = df["annots"] if "annots" in df else None
    df["large_anchor_support"] = df["LargeAnchorSupport"] if "LargeAnchorSupport" in df else None
    df["orientation_pass"] = df[orientation].apply(classify_splice_support) if orientation else None
    df["caller_frame_annotation"] = df["PROT_FUSION_TYPE"] if "PROT_FUSION_TYPE" in df else None
    df["caller_fusion_transcript"] = None
    df["caller_peptide_sequence"] = df["FUSION_TRANSL"] if "FUSION_TRANSL" in df else None
    df["caller_fusion_cds"] = df["FUSION_CDS"] if "FUSION_CDS" in df else None
    df["caller"] = "fusioninspector"
    return df[list(output_columns)]
