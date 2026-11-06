"""Fusion audit tables, FASTAs, peptide tables, and run summaries."""
from __future__ import annotations
import logging
import hashlib
from collections import defaultdict
from typing import Any, Callable
import pandas as pd
from .audit import audit_fields
from .fusion_filtering import (
    compute_dia_exclusion_reasons, filter_database_isoforms, join_reasons,
    summarise_filtering, digest_tryptic_peptides,
)
from .fusion_orchestration import infer_condition_from_sample
from .fusion_values import normalize_text_or_none, sequence_hash
from .splice_translation import _fasta_token, serialize_pgdb_header
LOGGER=logging.getLogger(__name__); logger=LOGGER


def write_candidate_fastas(
    dataframe: Any, cds_handle: Any, protein_handle: Any, organism: str,
    normalize: Callable[[Any], Any], token: Callable[[Any], str],
    serialize_header: Callable[..., str],
) -> int:
    """Write the supplied (DIA-eligible) fusion candidates without deduplication."""
    count = 0
    for row_index, (_, row) in enumerate(dataframe.iterrows(), 1):
        protein = normalize(row.get("protein_sequence"))
        cds = normalize(row.get("cds_sequence"))
        if not protein or not cds:
            continue
        digest = hashlib.sha256(f"{row_index}|{protein}".encode()).hexdigest()[:12].upper()
        protein_id, cds_id = f"FUSION_P{digest}", f"FUSION_C{digest}"
        name = token(row.get("fusion_name", "FUSION"))
        metadata = [
            ("schema_version", "pgdb-merge-input-v1"),
            ("source", "fusioninspector"),
            ("gene_id", f"{row.get('gene_1_id', 'NA')}--{row.get('gene_2_id', 'NA')}"),
            ("transcript", f"{row.get('donor_tid', 'NA')}--{row.get('acceptor_tid', 'NA')}"),
            ("event_type", "FUSION"), ("event_id", row.get("pair_token", row_index)),
            ("frame_status", row.get("frame_status")),
            ("sample_id", row.get("sample_id")), ("batch", row.get("batch")),
            ("condition", row.get("condition")),
            ("annotation_release", row.get("annotation_release")),
            ("database_output_tier", row.get("database_output_tier", "primary")),
            ("junction_aa", row.get("junction_aa")),
        ]
        cds_header = serialize_header(cds_id, name, [
            ("record_type", "cds"), ("record_id", cds_id), *metadata,
            ("variant", "fusion_cds"), ("sequence_length", len(cds)),
        ], organism=organism)
        protein_header = serialize_header(protein_id, name, [
            ("record_type", "protein"), ("record_id", protein_id), *metadata,
            ("variant", "fusion_protein"), ("protein_length", len(protein)),
        ], organism=organism)
        cds_handle.write(f">{cds_header}\n{cds}\n")
        protein_handle.write(f">{protein_header}\n{protein}\n")
        count += 1
    return count


def log_grouped_concordance_counts(ranking_df, group_col, group_label, concordance_col):
    """Log concordance counts grouped by a given metadata column."""
    if group_col not in ranking_df.columns or concordance_col not in ranking_df.columns:
        return

    logger.info(group_label)
    grouped = (
        ranking_df.assign(
            _group=ranking_df[group_col].fillna("NA"),
            _conc=ranking_df[concordance_col].fillna("NA"),
        )
        .groupby(["_group", "_conc"])
        .size()
        .reset_index(name="count")
        .sort_values(by=["_group", "count", "_conc"], ascending=[True, False, True])
    )
    for _, rec in grouped.iterrows():
        logger.info(f"  - {rec['_group']} | {rec['_conc']}: {int(rec['count'])}")

def write_digested_peptides_tsv(
    proteins_df,
    output_tsv,
    max_missed_cleavages=2,
    min_len=7,
    max_len=40,
):
    """Write tryptic peptides from protein rows to a TSV file."""
    if proteins_df.empty:
        pd.DataFrame().to_csv(output_tsv, sep="\t", index=False)
        return 0

    rows = []
    seen_per_source = defaultdict(set)

    for _, rec in proteins_df.iterrows():
        source_file = normalize_text_or_none(rec.get("source_file")) or "NA"
        protein_seq = normalize_text_or_none(rec.get("protein_sequence"), peptide=True)
        if not protein_seq:
            continue

        for pep in digest_tryptic_peptides(
            protein_seq,
            max_missed_cleavages=max_missed_cleavages,
            min_len=min_len,
            max_len=max_len,
        ):
            peptide_seq = pep["peptide_sequence"]
            dedup_key = (source_file, peptide_seq)
            if dedup_key in seen_per_source[source_file]:
                continue
            seen_per_source[source_file].add(dedup_key)

            rows.append(
                {
                    "source_file": source_file,
                    "source_basename": rec.get("source_basename"),
                    "fusion_name": rec.get("fusion_name"),
                    "pair_token": rec.get("pair_token"),
                    "primary_caller": rec.get("primary_caller"),
                    "protein_length": rec.get("protein_length"),
                    "protein_sequence": protein_seq,
                    "peptide_sequence": peptide_seq,
                    "peptide_length": pep["peptide_length"],
                    "peptide_start_aa": pep["peptide_start_aa"],
                    "peptide_end_aa": pep["peptide_end_aa"],
                    "missed_cleavages": pep["missed_cleavages"],
                    "frame_status": rec.get("frame_status"),
                    "nmd_predicted": rec.get("nmd_predicted"),
                }
            )

    out_df = pd.DataFrame(rows)
    out_df.to_csv(output_tsv, sep="\t", index=False)
    return len(out_df)

def write_sequence_sample_presence_tsv(ranking_df, out_path):
    """Write long-format protein/CDS sequence-to-sample presence table."""
    if not out_path:
        return
    rows = []
    if ranking_df is not None and not ranking_df.empty:
        seen = set()
        for _, rec in ranking_df.iterrows():
            sample_id = rec.get("sample_id") or rec.get("sample_basename")
            condition = rec.get("condition") or infer_condition_from_sample(sample_id)
            common = {
                "sample_id": sample_id,
                "batch": rec.get("batch"),
                "condition": condition,
                "source_file": rec.get("source_file"),
                "source_basename": rec.get("source_basename"),
                "fusion_name": rec.get("fusion_name"),
                "pair_token": rec.get("pair_token"),
                "primary_caller": rec.get("primary_caller"),
                "gene_1_symbol": rec.get("gene_1_symbol"),
                "gene_2_symbol": rec.get("gene_2_symbol"),
                "donor_tid": rec.get("donor_tid"),
                "acceptor_tid": rec.get("acceptor_tid"),
                "frame_status": rec.get("frame_status"),
                "fusion_effect_class": rec.get("fusion_effect_class"),
                "dia_fasta_include": rec.get("dia_fasta_include"),
                "dia_exclusion_reasons": rec.get("dia_exclusion_reasons"),
            }
            for seq_type, seq_col, len_col in [
                ("protein", "protein_sequence", "protein_length"),
                ("cds", "cds_sequence", "cds_length"),
            ]:
                seq = rec.get(seq_col)
                if seq is None or str(seq).strip() == "" or str(seq).lower() == "nan":
                    continue
                sh = sequence_hash(seq)
                key = (
                    seq_type,
                    sh,
                    sample_id,
                    rec.get("source_file"),
                    rec.get("pair_token"),
                )
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "sequence_hash": sh,
                        "sequence_type": seq_type,
                        "sequence_length": rec.get(len_col),
                        **common,
                        "sequence": seq,
                    }
                )
    out_df = pd.DataFrame(rows)
    if out_df.empty:
        out_df = pd.DataFrame(
            columns=[
                "sequence_hash",
                "sequence_type",
                "sequence_length",
                "sample_id",
                "condition",
                "source_file",
                "source_basename",
                "fusion_name",
                "pair_token",
                "primary_caller",
                "gene_1_symbol",
                "gene_2_symbol",
                "donor_tid",
                "acceptor_tid",
                "frame_status",
                "fusion_effect_class",
                "dia_fasta_include",
                "dia_exclusion_reasons",
                "sequence",
            ]
        )
    out_df.to_csv(out_path, sep="\t", index=False)
    logger.info(
        "Sequence-sample presence TSV saved to: %s (%d rows)", out_path, len(out_df)
    )

def prepare_ranking_dataframe(ranking_rows):
    """Convert ranking rows into a prepared ranking DataFrame."""

    ranking_df = pd.DataFrame(ranking_rows)

    if ranking_df.empty:
        return ranking_df

    if "sample_id" not in ranking_df.columns:
        ranking_df["sample_id"] = ranking_df.get("sample_basename")

    if "condition" not in ranking_df.columns:
        ranking_df["condition"] = ranking_df["sample_id"].apply(
            infer_condition_from_sample
        )

    if (
        "protein_sequence_hash" not in ranking_df.columns
        and "protein_sequence" in ranking_df.columns
    ):
        ranking_df["protein_sequence_hash"] = ranking_df["protein_sequence"].apply(
            sequence_hash
        )

    if (
        "cds_sequence_hash" not in ranking_df.columns
        and "cds_sequence" in ranking_df.columns
    ):
        ranking_df["cds_sequence_hash"] = ranking_df["cds_sequence"].apply(
            sequence_hash
        )

    ranking_df["dia_exclusion_reasons"] = ranking_df.apply(
        lambda rec: join_reasons(compute_dia_exclusion_reasons(rec)),
        axis=1,
    )

    ranking_df["dia_fasta_include"] = (
        ranking_df["dia_exclusion_reasons"].fillna("").eq("")
    )
    audit_rows = ranking_df.apply(
        lambda rec: audit_fields(rec.to_dict(), "dia_exclusion_reasons"), axis=1
    )
    for column in ("exclusion_reason_codes", "biological_observations_json", "policy_decisions_json"):
        ranking_df[column] = audit_rows.apply(lambda row: row[column])

    ranking_df["sanity_flags"] = ranking_df["dia_exclusion_reasons"]

    return ranking_df

def report_summary(summary, ranking_df):
    """Log processing and concordance summaries."""

    logger.info("\n=== RESULTS ===")
    logger.info("Total fusions processed: %d", summary["total_rows"])
    logger.info("Isoform pairs evaluated: %d", summary["pair_evaluated_count"])
    logger.info(
        "Fusions with >=1 valid isoform pair: %d",
        summary["events_with_valid_output"],
    )
    logger.info("Valid fusion proteins generated: %d", summary["protein_count"])
    no_product = max(0, summary["total_rows"] - summary["events_with_valid_output"])
    no_product_pct = (100.0 * no_product / summary["total_rows"]) if summary["total_rows"] else 0.0
    logger.info(
        "Fusion events with no reconstructable product: %d (%.2f%%)",
        no_product, no_product_pct,
    )
    logger.info("Candidate pairs skipped: %d", summary["skipped_count"])
    logger.info("Fusion events with >1 CDS-containing transcript candidate: %d", summary.get("events_with_alternative_transcripts", 0))
    logger.info("Alternative isoform pairs not evaluated at the configured limit: %d", summary.get("alternative_isoform_pairs_not_evaluated", 0))

    skip_reasons = summary.get("skip_reasons") or {}

    if skip_reasons:
        logger.info("Skip reasons:")
        for reason, count in sorted(
            skip_reasons.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            logger.info("  - %s: %s", reason, count)

    if ranking_df.empty:
        return

    concordance_col = "caller_vs_reconstructed_concordance"
    frame_col = "frame_status"
    caller_col = "primary_caller"

    if concordance_col in ranking_df.columns:
        logger.info("Concordance summary (all valid isoform pairs):")

        concordance_counts = ranking_df[concordance_col].fillna("NA").value_counts()

        concordance_total = int(concordance_counts.sum())
        for label, count in concordance_counts.items():
            percentage = 100.0 * int(count) / concordance_total if concordance_total else 0.0
            logger.info("  - %s: %s (%.2f%%)", label, count, percentage)

    log_grouped_concordance_counts(
        ranking_df,
        group_col=caller_col,
        group_label="Concordance by caller:",
        concordance_col=concordance_col,
    )

    log_grouped_concordance_counts(
        ranking_df,
        group_col=frame_col,
        group_label="Concordance by reconstructed frame status:",
        concordance_col=concordance_col,
    )

def write_biological_interpretation_table(ranking_df, args):
    """Write biological interpretation TSV if requested."""

    if not args.biological_interpretation_tsv:
        return ranking_df

    output_df = ranking_df.copy()

    if not output_df.empty:
        numeric_cols = [
            "split_reads_max",
            "split_reads_sum",
            "spanning_reads_max",
            "spanning_reads_sum",
            "protein_length",
        ]

        for numeric_col in numeric_cols:
            if numeric_col in output_df.columns:
                output_df[numeric_col] = pd.to_numeric(
                    output_df[numeric_col],
                    errors="coerce",
                )

        output_df = output_df.sort_values(
            by=[
                "protein_length",
                "split_reads_sum",
                "spanning_reads_sum",
            ],
            ascending=[False, False, False],
            na_position="last",
        )

    output_df.to_csv(
        args.biological_interpretation_tsv,
        sep="\t",
        index=False,
    )

    logger.info(
        "Biological interpretation TSV saved to: %s",
        args.biological_interpretation_tsv,
    )

    return output_df

def write_filtered_fasta_outputs(
    filtered_df, cds_out, prot_out, organism="unknown_organism"
):
    """Write candidates via the dedicated output module."""
    return write_candidate_fastas(
        filtered_df, cds_out, prot_out, organism,
        normalize_text_or_none, _fasta_token, serialize_pgdb_header,
    )

def write_filtered_database_outputs(ranking_df, args):
    """Filter database isoforms and write filtered database outputs."""

    if not ranking_df.empty:
        summarise_filtering(
            "DIA FASTA eligibility before de-duplication",
            ranking_df,
        )

    filtered_df = filter_database_isoforms(ranking_df)

    # Producer headers must carry the configured annotation release.
    release = getattr(args, "annotation_release", None)
    if release and not filtered_df.empty:
        if "annotation_release" not in filtered_df.columns:
            filtered_df["annotation_release"] = release
        else:
            filtered_df["annotation_release"] = filtered_df["annotation_release"].fillna(release)

    logger.info(
        "DIA-eligible fusion candidates exported without de-duplication: %d of %d",
        len(filtered_df),
        len(ranking_df),
    )

    if not filtered_df.empty:
        summarise_filtering(
            "Candidate FASTA before authoritative merge filtering",
            filtered_df,
        )

    if args.dia_database_metadata_tsv:
        filtered_df.to_csv(
            args.dia_database_metadata_tsv,
            sep="\t",
            index=False,
        )

        logger.info(
            "DIA database metadata TSV saved to: %s",
            args.dia_database_metadata_tsv,
        )

    if args.filtered_cds_fasta and args.filtered_protein_fasta:
        with open(args.filtered_cds_fasta, "w") as filtered_cds_out, open(
            args.filtered_protein_fasta,
            "w",
        ) as filtered_prot_out:
            filtered_count = write_filtered_fasta_outputs(
                filtered_df,
                filtered_cds_out,
                filtered_prot_out,
                organism=args.organism,
            )

        logger.info("Filtered CDS FASTA saved to: %s", args.filtered_cds_fasta)
        logger.info("Filtered protein FASTA saved to: %s", args.filtered_protein_fasta)
        logger.info("Filtered FASTA records written: %d", filtered_count)

    elif args.filtered_cds_fasta or args.filtered_protein_fasta:
        logger.warning(
            "Both --filtered_cds_fasta and --filtered_protein_fasta are required "
            "to write the filtered FASTA outputs"
        )

    return filtered_df

def write_outputs(ranking_df, args):
    """Write all non-digestion output files."""

    ranking_df = write_biological_interpretation_table(
        ranking_df,
        args,
    )

    if args.out_sequence_sample_tsv:
        write_sequence_sample_presence_tsv(
            ranking_df,
            args.out_sequence_sample_tsv,
        )

    filtered_df = write_filtered_database_outputs(
        ranking_df,
        args,
    )

    return filtered_df

def digest_filtered_database(filtered_df, args):
    """Optionally digest filtered fusion proteins and write peptide TSV."""

    if not args.digest_trypsin:
        return

    if filtered_df.empty:
        logger.warning("No proteins available for trypsin digestion")
        return

    if not args.digested_peptide_tsv:
        logger.warning(
            "--digest_trypsin is set but --digested_peptide_tsv was not provided"
        )
        return

    peptide_count = write_digested_peptides_tsv(
        filtered_df,
        args.digested_peptide_tsv,
        max_missed_cleavages=args.max_missed_cleavages,
        min_len=args.digested_min_peptide_length,
        max_len=args.digested_max_peptide_length,
    )

    logger.info(
        "Digested peptide TSV saved to: %s",
        args.digested_peptide_tsv,
    )

    logger.info(
        "Unique tryptic peptides written: %d",
        peptide_count,
    )
