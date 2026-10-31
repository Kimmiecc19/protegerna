"""Exact-sequence aggregation and provenance-preserving projections."""
from __future__ import annotations
from collections import Counter
import json
from typing import Callable, Dict, Iterable, List
from .merge_models import (
    ParsedRecord, SequenceAggregate, joined, representative_value,
    sanitize_header_value, sorted_values,
)
from .merge_parsing import biological_record_row
from .pgdb_header import PGDBHeader


def aggregate_exact_sequences(records: Sequence[ParsedRecord]) -> Dict[str, SequenceAggregate]:
    """Group records by exact amino-acid sequence."""
    aggregates: Dict[str, SequenceAggregate] = {}

    for record in records:
        key = record.sequence
        if key not in aggregates:
            aggregates[key] = SequenceAggregate(
                sequence=record.sequence,
                sequence_md5=record.sequence_md5,
                sequence_sha256=record.sequence_sha256,
            )
        aggregates[key].add(record)

    return aggregates

def sequence_aggregate_sink(
    aggregates: Dict[str, SequenceAggregate],
) -> Callable[[ParsedRecord], None]:
    """Return a streaming sink that aggregates a record immediately by sequence."""
    def add(record: ParsedRecord) -> None:
        aggregate = aggregates.get(record.sequence)
        if aggregate is None:
            aggregate = SequenceAggregate(
                sequence=record.sequence, sequence_md5=record.sequence_md5,
                sequence_sha256=record.sequence_sha256,
            )
            aggregates[record.sequence] = aggregate
        aggregate.add(record)
    return add

def order_aggregates(aggregates: Iterable[SequenceAggregate]) -> List[SequenceAggregate]:
    """Provide deterministic sequence-ID assignment."""
    return sorted(
        aggregates,
        key=lambda agg: (
            joined(agg.gene_symbols),
            len(agg.sequence),
            agg.sequence_sha256,
        ),
    )

def build_output_header(
    sequence_id: str,
    aggregate: SequenceAggregate,
    max_header_values: int,
    organism: str,
    annotation_release: str,
) -> str:
    """Construct an essential-metadata-only DIA FASTA header.

    Reconstruction diagnostics, hashes, samples, and intermediate decisions
    belong in the provenance TSV and are intentionally excluded here.
    """

    def limited(values: Iterable[str]) -> str:
        items = sorted_values(values)
        if not items:
            return "NA"
        if max_header_values <= 0 or len(items) <= max_header_values:
            return ",".join(sanitize_header_value(x) for x in items)
        shown = items[:max_header_values]
        return ",".join(sanitize_header_value(x) for x in shown) + f",plus_{len(items)-len(shown)}"

    confidence_order = {"Rejected": 0, "Exploratory": 1, "Moderate": 2, "High confidence": 3}
    confidences = {
        record.metadata.get("confidence", "") for record in aggregate.records
        if record.metadata.get("confidence")
    }
    fallback_confidence = "Exploratory" if "exploratory" in {
        tier.lower() for tier in aggregate.database_output_tiers
    } else "Moderate"
    confidence = max(confidences, key=lambda value: confidence_order.get(value, -1), default=fallback_confidence)
    fields = [
        ("source", limited(aggregate.sources)),
        ("record_type", "protein"),
        ("record_id", sequence_id),
        ("gene_symbol", limited(aggregate.gene_symbols)),
        ("transcript", limited(aggregate.transcripts)),
        ("event_ids", limited(aggregate.event_ids)),
        ("confidence", confidence),
    ]

    gene_for_diann = sanitize_header_value(representative_value(aggregate.gene_symbols))
    tokens = [f"PGDB|{sequence_id}|{sequence_id} GN={gene_for_diann} OS={sanitize_header_value(organism)}"]
    tokens.extend(f"{key}={sanitize_header_value(value)}" for key, value in fields)
    return "|".join(tokens)

def aggregate_metadata_row(sequence_id: str, aggregate: SequenceAggregate) -> Dict[str, object]:
    return {
        "sequence_id": sequence_id,
        "gene": joined(aggregate.gene_symbols or aggregate.gene_ids),
        "transcript": joined(aggregate.transcripts),
        "event": joined(aggregate.event_ids),
        "source": joined(aggregate.sources),
        "confidence": max(
            (record.metadata["confidence"] for record in aggregate.records if record.metadata.get("confidence")),
            key=lambda value: {"Rejected": 0, "Exploratory": 1, "Moderate": 2, "High confidence": 3}.get(value, -1),
            default=("Exploratory" if "exploratory" in {tier.lower() for tier in aggregate.database_output_tiers} else "Moderate"),
        ),
        "sequence_md5": aggregate.sequence_md5,
        "sequence_sha256": aggregate.sequence_sha256,
        "protein_length": len(aggregate.sequence),
        "n_eligible_tryptic_peptides": max(
            (record.n_eligible_tryptic_peptides for record in aggregate.records), default=0
        ),
        "min_eligible_peptide_length": min(
            (record.min_eligible_peptide_length for record in aggregate.records
             if record.min_eligible_peptide_length is not None),
            default="NA",
        ),
        "max_eligible_peptide_length": max(
            (record.max_eligible_peptide_length for record in aggregate.records
             if record.max_eligible_peptide_length is not None),
            default="NA",
        ),
        "passes_dia_filter": True,
        "mapping_count": len(aggregate.records),
        "source_count": len(aggregate.sources),
        "gene_symbol_count": len(aggregate.gene_symbols),
        "gene_id_count": len(aggregate.gene_ids),
        "transcript_count": len(aggregate.transcripts),
        "event_type_count": len(aggregate.event_types),
        "event_count": len(aggregate.event_ids),
        "variant_count": len(aggregate.variants),
        "sources": joined(aggregate.sources),
        "record_types": joined(aggregate.record_types),
        "gene_symbols": joined(aggregate.gene_symbols),
        "gene_ids": joined(aggregate.gene_ids),
        "transcripts": joined(aggregate.transcripts),
        "uniprot_accessions": joined(aggregate.uniprot_accessions),
        "uniprot_entries": joined(aggregate.uniprot_entries),
        "protein_names": joined(aggregate.protein_names),
        "translation_strategies": joined(aggregate.translation_strategies),
        "database_output_tiers": joined(aggregate.database_output_tiers),
        "protein_product_classes": joined(aggregate.protein_product_classes),
        "event_types": joined(aggregate.event_types),
        "event_ids": joined(aggregate.event_ids),
        "variants": joined(aggregate.variants),
        "callers": joined(aggregate.callers),
        "sample_ids": joined(aggregate.sample_ids),
        "batches": joined(aggregate.batches),
        "conditions": joined(aggregate.conditions),
        "annotation_releases": joined(aggregate.annotation_releases),
        "original_ids": joined(aggregate.original_ids),
        "input_files": joined(aggregate.input_files),
        "sequence": aggregate.sequence,
    }

def mapping_rows(
    sequence_id: str,
    aggregate: SequenceAggregate,
) -> Iterator[Dict[str, object]]:
    for record in sorted(
        aggregate.records,
        key=lambda r: (r.input_file, r.original_id),
    ):
        yield {
            "sequence_id": sequence_id,
            "sequence_md5": aggregate.sequence_md5,
            "sequence_sha256": aggregate.sequence_sha256,
            "input_file": record.input_file,
            "original_id": record.original_id,
            "source": record.source,
            "record_type": record.record_type,
            "gene_symbols": joined(record.gene_symbols),
            "gene_ids": joined(record.gene_ids),
            "transcripts": joined(record.transcripts),
            "uniprot_accessions": joined(record.uniprot_accessions),
            "uniprot_entries": joined(record.uniprot_entries),
            "protein_names": joined(record.protein_names),
            "translation_strategies": joined(record.translation_strategies),
            "database_output_tiers": joined(record.database_output_tiers),
            "protein_product_classes": joined(record.protein_product_classes),
            "event_types": joined(record.event_types),
            "event_ids": joined(record.event_ids),
            "variants": joined(record.variants),
            "callers": joined(record.callers),
            "protein_length": len(record.sequence),
            "n_eligible_tryptic_peptides": record.n_eligible_tryptic_peptides,
            "min_eligible_peptide_length": record.min_eligible_peptide_length or "NA",
            "max_eligible_peptide_length": record.max_eligible_peptide_length or "NA",
            "original_description": record.original_description,
            "confidence": record.metadata.get("confidence", "NA"),
            "extended_provenance": json.dumps(record.metadata, sort_keys=True, separators=(",", ":")),
        }

def retained_biological_rows(
    aggregates: Sequence[SequenceAggregate],
    id_map: Dict[str, str],
) -> Iterator[Dict[str, object]]:
    for aggregate in aggregates:
        sequence_id = id_map[aggregate.sequence_sha256]
        for record in aggregate.records:
            yield biological_record_row(record, True, sequence_id=sequence_id)

def build_summary(
    fasta_files: Sequence[Path],
    read_stats: Counter,
    all_aggregates: Dict[str, SequenceAggregate],
    retained_aggregates: Sequence[SequenceAggregate],
    mapping_count: int,
    biological_interpretation_count: int,
) -> Dict[str, object]:
    source_record_counts: Counter = Counter()
    source_sequence_counts: Counter = Counter()
    for aggregate in retained_aggregates:
        for source in aggregate.sources:
            source_sequence_counts[source] += 1
        for record in aggregate.records:
            source_record_counts[record.source] += 1

    retained_records = sum(len(agg.records) for agg in retained_aggregates)
    redundancy_fraction = (
        1.0 - (len(retained_aggregates) / retained_records)
        if retained_records
        else 0.0
    )

    return {
        "input_fasta_file_count": len(fasta_files),
        "input_fasta_files": [str(path) for path in fasta_files],
        "records_read": int(read_stats.get("records_read", 0)),
        "records_retained_after_dia_filtering": int(
            read_stats.get("records_retained_after_dia_filtering", 0)
        ),
        "records_removed_short_protein": int(read_stats.get("records_skipped_too_short", 0)),
        "records_removed_no_valid_peptide": int(
            read_stats.get("records_skipped_no_eligible_tryptic_peptide", 0)
        ),
        "records_removed_invalid_sequence": sum(
            int(value) for key, value in read_stats.items() if str(key).startswith("records_invalid_")
        ),
        "unique_sequences_before_filtering": len(all_aggregates),
        "unique_sequences_written": len(retained_aggregates),
        "record_mappings_written": mapping_count,
        "biological_interpretation_rows_written": biological_interpretation_count,
        "retained_original_records": retained_records,
        "exact_sequence_redundancy_fraction": redundancy_fraction,
        "source_record_counts": dict(sorted(source_record_counts.items())),
        "source_unique_sequence_counts": dict(sorted(source_sequence_counts.items())),
        "read_filter_statistics": dict(sorted(read_stats.items())),
    }
