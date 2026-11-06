"""Merge FASTA, TSV, and JSON reporting."""
from __future__ import annotations
import csv, json, logging
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from .merge_aggregation import aggregate_metadata_row, build_output_header, mapping_rows
from .merge_models import SequenceAggregate
LOGGER = logging.getLogger("merge_proteogenomic_database")


def write_tsv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count

def write_outputs(
    aggregates: Sequence[SequenceAggregate],
    out_fasta: Path,
    out_metadata: Path,
    out_mapping: Path,
    id_prefix: str,
    id_width: int,
    max_header_values: int,
    organism: str,
    annotation_release: str,
) -> Tuple[Dict[str, str], int]:
    """Write sequence-level FASTA, metadata, and original-record mappings."""
    out_fasta.parent.mkdir(parents=True, exist_ok=True)

    id_map: Dict[str, str] = {}
    metadata_rows: List[Dict[str, object]] = []
    all_mapping_rows: List[Dict[str, object]] = []
    fasta_records: List[SeqRecord] = []

    for index, aggregate in enumerate(aggregates, start=1):
        sequence_id = f"{id_prefix}{index:0{id_width}d}"
        id_map[aggregate.sequence_sha256] = sequence_id

        header = build_output_header(
            sequence_id, aggregate, max_header_values, organism, annotation_release
        )
        primary_identifier = header.partition(" ")[0]
        fasta_records.append(
            SeqRecord(
                Seq(aggregate.sequence),
                id=primary_identifier,
                name=primary_identifier,
                description=header,
            )
        )
        metadata_rows.append(aggregate_metadata_row(sequence_id, aggregate))
        all_mapping_rows.extend(mapping_rows(sequence_id, aggregate))

    with out_fasta.open("w", encoding="utf-8") as handle:
        SeqIO.write(fasta_records, handle, "fasta")

    # Primary metadata mirrors the compact FASTA contract. Detailed hashes,
    # decisions, and diagnostics remain in the record-level provenance TSV.
    metadata_fields = ["sequence_id", "gene", "transcript", "event", "source", "confidence"]
    write_tsv(out_metadata, metadata_rows, metadata_fields)

    mapping_fields = [
        "sequence_id",
        "sequence_md5",
        "sequence_sha256",
        "input_file",
        "original_id",
        "source",
        "record_type",
        "gene_symbols",
        "gene_ids",
        "transcripts",
        "uniprot_accessions",
        "uniprot_entries",
        "protein_names",
        "translation_strategies",
        "database_output_tiers",
        "protein_product_classes",
        "event_types",
        "event_ids",
        "variants",
        "callers",
        "protein_length",
        "n_eligible_tryptic_peptides",
        "min_eligible_peptide_length",
        "max_eligible_peptide_length",
        "original_description",
        "confidence",
        "extended_provenance",
    ]
    mapping_count = write_tsv(out_mapping, all_mapping_rows, mapping_fields)

    return id_map, mapping_count

def flatten_summary_for_tsv(summary: Dict[str, object]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for key, value in summary.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                rows.append({"metric": f"{key}.{subkey}", "value": subvalue})
        elif isinstance(value, list):
            rows.append({"metric": key, "value": ";".join(map(str, value))})
        else:
            rows.append({"metric": key, "value": value})

    return rows

def write_summary_files(summary: Dict[str, object], tsv_path: Path, json_path: Path) -> None:
    write_tsv(tsv_path, flatten_summary_for_tsv(summary), ("metric", "value"))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
