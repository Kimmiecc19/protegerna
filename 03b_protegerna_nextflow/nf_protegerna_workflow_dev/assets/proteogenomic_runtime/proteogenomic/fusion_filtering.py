"""Fusion candidate peptide evidence, ranking, and DIA policy filtering."""
from __future__ import annotations
import logging
from collections import defaultdict
import pandas as pd
from Bio import SeqIO
from .fusion_policy import assess_biological_eligibility
from .fusion_values import normalize_text_or_none, parse_bool_or_none, parse_int_or_none
from .splice_translation import digest_tryptic_records, load_reference_tryptic_peptides
LOGGER=logging.getLogger(__name__); logger=LOGGER


def deduplicate_fusions(combined_df):
    """
    Aggregate duplicate fusion events detected by multiple callers.

    Deduplicates on fusion coordinates and carries forward multi-caller evidence
    instead of dropping all but the first record.
    """
    subset_cols = [
        "gene_1_symbol",
        "gene_2_symbol",
        "gene_1_id",
        "gene_2_id",
        "chrom1",
        "breakpoint1",
        "chrom2",
        "breakpoint2",
    ]
    initial_count = len(combined_df)
    combined_df = combined_df.copy()
    symbol_key = [
        "gene_1_symbol", "gene_2_symbol", "chrom1", "breakpoint1", "chrom2", "breakpoint2"
    ]
    id_pair_counts = combined_df.groupby(symbol_key, dropna=False)[
        ["gene_1_id", "gene_2_id"]
    ].apply(lambda group: len(group.drop_duplicates()))
    colliding_symbol_keys = set(id_pair_counts[id_pair_counts > 1].index)

    def max_or_none(values):
        vals = [v for v in values if v is not None]
        return max(vals) if vals else None

    def sum_or_none(values):
        vals = [v for v in values if v is not None]
        return sum(vals) if vals else None

    def merge_text_values(values):
        merged = []
        seen = set()
        for value in values:
            normalized = normalize_text_or_none(value)
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(normalized)
        return "|".join(merged) if merged else None

    def aggregate_group(group):
        first = group.iloc[0].copy()

        # pandas groupby(...).apply(..., include_groups=False) deliberately
        # removes the grouping columns from ``group``. Restore the biological
        # fusion key explicitly so downstream reconstruction always receives
        # the normalized schema declared by PARSED_FUSION_COLUMNS.
        group_key = group.name
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        for column, value in zip(subset_cols, group_key):
            first[column] = value
        symbol_group_key = (
            first.get("gene_1_symbol"), first.get("gene_2_symbol"),
            first.get("chrom1"), first.get("breakpoint1"),
            first.get("chrom2"), first.get("breakpoint2"),
        )
        first["symbol_coordinate_gene_id_collision"] = symbol_group_key in colliding_symbol_keys

        callers = sorted(
            {str(c).strip() for c in group["caller"] if pd.notna(c) and str(c).strip()}
        )
        first["caller"] = callers[0] if callers else first.get("caller")
        first["contributing_callers"] = "|".join(callers) if callers else None
        first["contributing_caller_count"] = len(callers)
        first["deduplicated_input_row_count"] = len(group)

        split_vals = (
            [parse_int_or_none(v) for v in group["split_reads"]]
            if "split_reads" in group
            else []
        )
        span_vals = (
            [parse_int_or_none(v) for v in group["spanning_reads"]]
            if "spanning_reads" in group
            else []
        )

        first["split_reads_max"] = max_or_none(split_vals)
        first["split_reads_sum"] = sum_or_none(split_vals)
        first["spanning_reads_max"] = max_or_none(span_vals)
        first["spanning_reads_sum"] = sum_or_none(span_vals)

        # Keep compatibility fields as max evidence while exposing sum/max separately.
        first["split_reads"] = first["split_reads_max"]
        first["spanning_reads"] = first["spanning_reads_max"]

        conf_vals = sorted(
            {
                str(v).strip()
                for v in group["confidence"]
                if pd.notna(v) and str(v).strip()
            }
        )
        first["confidence"] = "|".join(conf_vals) if conf_vals else None

        orient_vals = (
            [parse_bool_or_none(v) for v in group["orientation_pass"]]
            if "orientation_pass" in group
            else []
        )
        orient_vals = [v for v in orient_vals if v is not None]
        first["orientation_pass"] = any(orient_vals) if orient_vals else None

        for col in [
            "caller_annotations",
            "large_anchor_support",
            "caller_frame_annotation",
            "caller_fusion_transcript",
            "caller_peptide_sequence",
            "caller_fusion_cds",
        ]:
            if col in group:
                first[col] = merge_text_values(group[col])

        for col in ["source_file", "source_basename"]:
            if col in group:
                first[col] = merge_text_values(group[col])

        return first

    deduplicated = combined_df.groupby(
        subset_cols,
        dropna=False,
        sort=False,
        group_keys=False,
    ).apply(
        aggregate_group,
        include_groups=False,
    )
    deduplicated = deduplicated.reset_index(drop=True)
    removed_count = initial_count - len(deduplicated)

    if removed_count > 0:
        logger.info(f"Removed {removed_count} duplicate fusion events")

    return deduplicated.reset_index(drop=True)


def is_low_confidence_isoform(row):
    """Return True when a row should be excluded from the DIA database FASTA.

    Biological interpretation rows are not removed by this function; it is only
    used when constructing the filtered DIA FASTA.
    """
    if parse_bool_or_none(row.get("dia_fasta_include")) is False:
        return True

    reasons = normalize_text_or_none(row.get("dia_exclusion_reasons"))
    if reasons:
        return True

    peptide = normalize_text_or_none(row.get("protein_sequence"), peptide=True)
    if not peptide:
        return True

    return False


def filter_database_isoforms(ranking_df):
    """Return DIA-eligible candidates without sequence deduplication.

    Only rows that pass the configured fusion DIA policy (dia_fasta_include is
    True, no dia_exclusion_reasons, non-empty protein) are returned for the
    primary fusion FASTA. Every candidate, eligible or not, remains in the
    biological interpretation table. Exact-sequence collapse is still performed
    only by the authoritative merge, which does not re-apply this policy.
    """
    if ranking_df.empty:
        return ranking_df.copy()

    working = ranking_df.copy()
    if "source_file" not in working.columns:
        working["source_file"] = working.get("sample_basename", "NA")

    excluded = working.apply(is_low_confidence_isoform, axis=1).astype(bool)
    logger.info(
        "Fusion DIA policy applied to primary FASTA: %d eligible, %d excluded",
        int((~excluded).sum()), int(excluded.sum()),
    )
    return working.loc[~excluded].reset_index(drop=True)

def digest_tryptic_peptides(
    protein_sequence, max_missed_cleavages=2, min_len=7, max_len=40
):
    """Digest a protein sequence in silico with trypsin (K/R not before P)."""
    return digest_tryptic_records(
        protein_sequence, max_missed_cleavages, min_len, max_len
    )

def build_reference_proteome_indices(
    reference_proteome,
    max_missed_cleavages=2,
    min_len=7,
    max_len=40,
    cache_path=None,
):
    """Build canonical-proteome indices for protein identity and peptide uniqueness checks."""
    protein_set = set()
    peptide_set = load_reference_tryptic_peptides(
        reference_proteome, max_missed_cleavages, min_len, max_len, cache_path
    ) if reference_proteome else set()
    if not reference_proteome:
        return protein_set, peptide_set

    for rec in SeqIO.parse(reference_proteome, "fasta"):
        protein_seq = normalize_text_or_none(str(rec.seq), peptide=True)
        if not protein_seq:
            continue
        protein_set.add(protein_seq)

    return protein_set, peptide_set

def evaluate_junction_peptides(
    protein_sequence,
    junction_nt,
    reference_peptide_set=None,
    max_missed_cleavages=2,
    min_len=7,
    max_len=40,
):
    """Assess whether tryptic peptides truly span the translated fusion junction.

    For a codon-boundary fusion, a peptide must include at least one amino acid
    from the donor side and at least one amino acid from the acceptor side. For
    an out-of-frame/hybrid junction codon, containing the hybrid junction amino
    acid is sufficient to count as junction-spanning.
    """
    out = {
        "junction_aa_index_1based": None,
        "junction_tryptic_peptide_count": 0,
        "junction_tryptic_unique_count": 0,
        "junction_tryptic_peptides": None,
        "junction_tryptic_unique_peptides": None,
        "has_junction_spanning_peptide": False,
        "has_unique_junction_peptide": False,
        "canonical_uniqueness_assessed": reference_peptide_set is not None,
    }

    protein = normalize_text_or_none(protein_sequence, peptide=True)
    if not protein or junction_nt is None:
        return out

    try:
        junction_nt = int(junction_nt)
        if junction_nt <= 0:
            return out
    except (TypeError, ValueError):
        return out

    remainder = junction_nt % 3
    if remainder == 0:
        donor_last_aa = junction_nt // 3
        acceptor_first_aa = donor_last_aa + 1
        out["junction_aa_index_1based"] = acceptor_first_aa

        def spans_junction(start, end):
            return start <= donor_last_aa and end >= acceptor_first_aa

    else:
        hybrid_aa = (junction_nt // 3) + 1
        out["junction_aa_index_1based"] = hybrid_aa

        def spans_junction(start, end):
            return start <= hybrid_aa <= end

    spanning = []
    unique = []
    for pep in digest_tryptic_peptides(
        protein,
        max_missed_cleavages=max_missed_cleavages,
        min_len=min_len,
        max_len=max_len,
    ):
        start = pep.get("peptide_start_aa")
        end = pep.get("peptide_end_aa")
        seq = normalize_text_or_none(pep.get("peptide_sequence"), peptide=True)
        if start is None or end is None or not seq:
            continue
        if spans_junction(int(start), int(end)):
            spanning.append(seq)
            if reference_peptide_set is not None and seq not in reference_peptide_set:
                unique.append(seq)

    spanning = sorted(set(spanning))
    unique = sorted(set(unique))
    out.update(
        {
            "junction_tryptic_peptide_count": len(spanning),
            "junction_tryptic_unique_count": len(unique),
            "junction_tryptic_peptides": "|".join(spanning) if spanning else None,
            "junction_tryptic_unique_peptides": "|".join(unique) if unique else None,
            "has_junction_spanning_peptide": bool(spanning),
            "has_unique_junction_peptide": bool(unique),
        }
    )
    return out

def join_reasons(reasons):
    """Return a stable semicolon-separated reason string."""
    cleaned = []
    seen = set()
    for reason in reasons or []:
        reason = normalize_text_or_none(reason)
        if reason and reason not in seen:
            seen.add(reason)
            cleaned.append(reason)
    return ";".join(cleaned) if cleaned else ""

def compute_dia_exclusion_reasons(row):
    """Compute reasons why a candidate should be omitted from the DIA database FASTA."""
    reasons = list(assess_biological_eligibility(row).reasons)
    if parse_bool_or_none(row.get("exclude_incomplete_cds")) is True:
        if normalize_text_or_none(row.get("donor_cds_completeness")) != "complete":
            reasons.append("donor_incomplete_cds_excluded_from_dia")
        if normalize_text_or_none(row.get("acceptor_cds_completeness")) != "complete":
            reasons.append("acceptor_incomplete_cds_excluded_from_dia")
    product_class = normalize_text_or_none(row.get("protein_product_class"))
    donor_only_classes = {
        "donor_only_reference_identical",
        "donor_only_truncated",
        "donor_only_reference_status_unknown",
    }
    donor_only = product_class in donor_only_classes
    include_donor_only = (
        parse_bool_or_none(row.get("include_donor_only_products")) is True
    )

    protein_length = parse_int_or_none(row.get("protein_length"))
    min_protein_length = parse_int_or_none(row.get("dia_min_protein_length"))
    if (
        protein_length is not None
        and min_protein_length is not None
        and protein_length < min_protein_length
    ):
        reasons.append("protein_too_short_for_dia")

    donor_nt = parse_int_or_none(row.get("donor_retained_cds_nt"))
    acceptor_nt = parse_int_or_none(row.get("acceptor_retained_cds_nt"))
    min_retained_nt = parse_int_or_none(row.get("min_retained_cds_nt"))
    if (
        donor_nt is not None
        and min_retained_nt is not None
        and donor_nt < min_retained_nt
    ):
        reasons.append("donor_retained_cds_lt_threshold")
    if (
        not donor_only
        and acceptor_nt is not None
        and min_retained_nt is not None
        and acceptor_nt < min_retained_nt
    ):
        reasons.append("acceptor_retained_cds_lt_threshold")

    if donor_only and not include_donor_only:
        reasons.append("donor_only_product_not_requested")

    # A canonical-identical donor-only product can be retained when explicitly
    # requested. It remains non-fusion-specific and should be deduplicated when
    # combined with the canonical reference proteome.
    if (
        parse_bool_or_none(row.get("protein_identical_to_reference")) is True
        and not donor_only
    ):
        reasons.append("fusion_protein_identical_to_canonical_proteome")

    if parse_bool_or_none(row.get("breakpoint_snapped_far")) is True:
        reasons.append("breakpoint_snapped_far_from_reported_coordinate")
    snapped_classes = {"snapped_intronic_breakpoint", "snapped_outside_transcript"}
    if (
        normalize_text_or_none(row.get("donor_breakpoint_resolution_class")) in snapped_classes
        or normalize_text_or_none(row.get("acceptor_breakpoint_resolution_class")) in snapped_classes
    ) and parse_bool_or_none(row.get("independent_junction_evidence")) is not True:
        reasons.append("snapped_breakpoint_without_independent_junction_evidence")
    if (
        parse_bool_or_none(row.get("exclude_frameshift_from_dia")) is True
        and normalize_text_or_none(row.get("frame_status")) == "FRAMESHIFT"
    ):
        reasons.append("frameshift_excluded_from_dia")
    if (
        parse_bool_or_none(row.get("exclude_nmd_from_dia")) is True
        and parse_bool_or_none(row.get("nmd_predicted")) is True
    ):
        reasons.append("nmd_predicted_excluded_from_dia")
    if parse_bool_or_none(row.get("exclude_truncated_from_dia")) is True:
        if (
            parse_bool_or_none(row.get("early_stop_after_junction")) is True
            or product_class == "donor_only_truncated"
        ):
            reasons.append("truncated_or_early_stop_excluded_from_dia")

    # Junction-peptide requirements apply only when translation reaches and
    # crosses the fusion junction. Donor-only products cannot produce such a
    # peptide and are assessed under the explicit donor-only option instead.
    if not donor_only:
        if (
            parse_bool_or_none(row.get("require_junction_peptide_for_dia")) is True
            and parse_bool_or_none(row.get("has_junction_spanning_peptide")) is not True
        ):
            reasons.append("no_tryptic_junction_spanning_peptide")
        if (
            parse_bool_or_none(row.get("require_unique_junction_peptide_for_dia"))
            is True
        ):
            if parse_bool_or_none(row.get("canonical_uniqueness_assessed")) is not True:
                reasons.append(
                    "canonical_uniqueness_not_assessed_no_reference_proteome"
                )
            elif parse_bool_or_none(row.get("has_unique_junction_peptide")) is not True:
                reasons.append("no_canonical_unique_junction_peptide")

    return reasons

def summarise_filtering(label, df, reason_col="dia_exclusion_reasons"):
    """Log detailed retained/excluded counts for a filtered table."""
    if df is None or df.empty:
        logger.info("%s: no candidates", label)
        return
    include_col = "dia_fasta_include"
    included = (
        int(df[include_col].fillna(False).astype(bool).sum())
        if include_col in df.columns
        else 0
    )
    logger.info(
        "%s: %d included, %d excluded, %d total",
        label,
        included,
        len(df) - included,
        len(df),
    )
    if reason_col in df.columns:
        counts = defaultdict(int)
        for val in df[reason_col].fillna(""):
            for reason in str(val).split(";"):
                reason = reason.strip()
                if reason:
                    counts[reason] += 1
        if counts:
            logger.info("%s exclusion reasons:", label)
            for reason, count in sorted(
                counts.items(), key=lambda x: x[1], reverse=True
            ):
                logger.info("  - %s: %d", reason, count)
