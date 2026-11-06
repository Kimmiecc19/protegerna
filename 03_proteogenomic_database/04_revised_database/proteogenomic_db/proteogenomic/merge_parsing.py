"""FASTA discovery, parsing, normalization, and record-level filtering."""
from __future__ import annotations
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from .release_validation import MergeInputContract
from .merge_models import (
    VALID_AA, ParsedRecord, ProteinFilterConfig, clean_value, fasta_suffix,
    joined, normalize_sequence, sequence_hashes, split_multi_value,
)
from .pgdb_header import PGDBHeader
from .splice_translation import digest_tryptic_peptides as shared_digest_tryptic_peptides
from .audit import exclusion_codes
from .provenance import open_text
LOGGER = logging.getLogger("merge_proteogenomic_database")
DECOY_RE = re.compile(r"(?:^|\|)(?:REV_|REVERSE_|DECOY_|XXX_)", re.IGNORECASE)
RESCUE_TIERS = frozenset({"alternative_start", "exploratory_orf", "exploratory"})


def discover_fasta_files(inputs: Sequence[str], recursive: bool) -> List[Path]:
    """Resolve input FASTA files from explicit files and directories."""
    discovered: Set[Path] = set()

    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Input does not exist: {path}")

        if path.is_file():
            if fasta_suffix(path):
                discovered.add(path)
            else:
                LOGGER.warning("Skipping non-FASTA input file: %s", path)
            continue

        iterator = path.rglob("*") if recursive else path.glob("*")
        for candidate in iterator:
            if candidate.is_file() and fasta_suffix(candidate):
                discovered.add(candidate.resolve())

    return sorted(discovered, key=lambda p: str(p))

# Plain-text or gzip-compressed FASTA input (shared implementation).
open_text_auto = open_text

def parse_pipe_header(description: str) -> Tuple[str, Dict[str, str]]:
    """Parse legacy PGDB and UniProt-like PGDB headers without corrupting fields."""
    parsed = PGDBHeader.parse(description)
    return parsed.record_id, parsed.metadata

def parse_uniprot_header(description: str) -> Dict[str, Set[str]]:
    """Extract common metadata from UniProt-style FASTA headers."""
    out = {"accessions": set(), "entries": set(), "genes": set(), "protein_names": set()}
    first, _, remainder = description.partition(" ")
    parts = first.split("|")
    if len(parts) >= 3 and parts[0] in {"sp", "tr"}:
        out["accessions"].add(parts[1])
        out["entries"].add(parts[2])
    gene_match = re.search(r"(?:^|\s)GN=([^\s]+)", description)
    if gene_match:
        out["genes"].add(gene_match.group(1))
    name = re.split(r"\sOS=", remainder, maxsplit=1)[0].strip()
    if name:
        out["protein_names"].add(name)
    return out

def infer_source(metadata: Dict[str, str], record_id: str, path: Path) -> str:
    explicit = clean_value(metadata.get("source"))
    if explicit != "NA":
        return explicit.lower()

    haystack = " ".join([record_id, path.name, str(path.parent)]).lower()
    if "rmats" in haystack:
        return "rmats"
    if "suppa" in haystack:
        return "suppa"
    if "fusion" in haystack or "star-fusion" in haystack or "fusioninspector" in haystack:
        return "fusioninspector"
    return "unknown"

def infer_record_type(metadata: Dict[str, str], record_id: str) -> str:
    explicit = clean_value(metadata.get("record_type"))
    if explicit != "NA":
        return explicit.lower()

    rid = record_id.upper()
    if "JUNC" in rid or "PEPTIDE" in rid:
        return "junction_peptide"
    if re.search(r"(?:^|_)C\d+$", rid) or "CDS" in rid:
        return "cds"
    return "protein"

def collect_set(metadata: Dict[str, str], keys: Sequence[str]) -> Set[str]:
    values: Set[str] = set()
    for key in keys:
        values.update(split_multi_value(metadata.get(key)))
    return values

def parse_fasta_record(
    record: SeqRecord,
    input_path: Path,
    forced_source: Optional[str] = None,
    contract: Optional[MergeInputContract] = None,
) -> ParsedRecord:
    description = record.description.strip()
    record_id, metadata = parse_pipe_header(description)

    if record_id == "NA":
        record_id = clean_value(record.id)

    sequence = normalize_sequence(record.seq)
    md5, sha256 = sequence_hashes(sequence)
    source = forced_source or infer_source(metadata, record_id, input_path)
    record_type = infer_record_type(metadata, record_id)
    if contract is not None:
        contract.validate(metadata, source)

    is_static_database = source in {"reference", "crap"}

    gene_symbols = collect_set(metadata, (
        "gene_symbol", "gene_symbols", "gene", "genes", "all_gene_symbols",
        "donor_gene", "acceptor_gene",
    ))
    gene_ids = collect_set(metadata, (
        "gene_id", "gene_ids", "all_gene_ids", "donor_gene_id", "acceptor_gene_id",
    ))
    transcripts = collect_set(metadata, (
        "transcript", "transcripts", "all_transcripts",
        "donor_transcript", "acceptor_transcript",
    ))
    event_types = collect_set(metadata, ("event_type", "event_types", "all_event_types"))
    event_ids = collect_set(metadata, ("event_id", "event_ids", "all_event_ids", "fusion_name"))
    variants = collect_set(metadata, ("variant", "variants", "all_variants"))
    callers = collect_set(metadata, ("caller", "callers", "contributing_callers"))

    uniprot_accessions = collect_set(metadata, ("uniprot", "uniprot_accession", "accession"))
    uniprot_entries = collect_set(metadata, ("uniprotkb", "uniprot_entry", "entry_name"))
    protein_names = collect_set(metadata, ("protein_name", "protein_names"))
    translation_strategies = collect_set(metadata, ("translation_strategy", "translation_strategies"))
    database_output_tiers = collect_set(metadata, ("database_output_tier", "database_output_tiers"))
    protein_product_classes = collect_set(metadata, ("protein_product_class", "protein_product_classes"))

    if is_static_database:
        parsed_uni = parse_uniprot_header(description)
        if parsed_uni["accessions"]:
            record_id = sorted(parsed_uni["accessions"])[0]
        uniprot_accessions.update(parsed_uni["accessions"])
        uniprot_entries.update(parsed_uni["entries"])
        gene_symbols.update(parsed_uni["genes"])
        protein_names.update(parsed_uni["protein_names"])
        event_types.add("REFERENCE" if source == "reference" else "CONTAMINANT")

    if not callers and source not in {"unknown", "reference", "crap"}:
        callers.add(source)

    return ParsedRecord(
        input_file=str(input_path), original_id=record_id, original_description=description,
        sequence=sequence, sequence_md5=md5, sequence_sha256=sha256, source=source,
        record_type=record_type,
        gene_symbols=gene_symbols, gene_ids=gene_ids, transcripts=transcripts,
        event_types=event_types, event_ids=event_ids, variants=variants, callers=callers,
        uniprot_accessions=uniprot_accessions, uniprot_entries=uniprot_entries,
        protein_names=protein_names, metadata=metadata,
        translation_strategies=translation_strategies,
        database_output_tiers=database_output_tiers,
        protein_product_classes=protein_product_classes,
    )

def validate_protein_sequence(sequence: str) -> Tuple[bool, str]:
    if not sequence:
        return False, "empty_sequence"

    invalid = sorted(set(sequence) - VALID_AA)
    if invalid:
        return False, f"invalid_amino_acids:{''.join(invalid)}"

    return True, "ok"

def digest_tryptic_peptides(
    sequence: str,
    min_peptide_length: int = 6,
    max_peptide_length: int = 40,
    max_missed_cleavages: int = 3,
) -> Set[str]:
    """Return unique DIA-NN-eligible tryptic peptides.

    Trypsin cleaves after K or R unless followed by P. Peptides are generated
    with zero through ``max_missed_cleavages`` missed cleavages and filtered
    to the configured amino-acid length interval.
    """
    return shared_digest_tryptic_peptides(
        sequence, max_missed_cleavages, min_peptide_length, max_peptide_length
    )

def biological_record_row(
    record: ParsedRecord,
    included_in_dia_fasta: bool,
    exclusion_reason: str = "",
    sequence_id: str = "",
) -> Dict[str, object]:
    """Build one biological-interpretation row without discarding provenance."""
    return {
        "included_in_dia_fasta": included_in_dia_fasta,
        "exclusion_reason": exclusion_reason or "NA",
        "exclusion_reason_codes": exclusion_codes(exclusion_reason),
        "sequence_id": sequence_id or "NA",
        "sequence_md5": record.sequence_md5,
        "sequence_sha256": record.sequence_sha256,
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
        "event_types": joined(record.event_types),
        "event_ids": joined(record.event_ids),
        "variants": joined(record.variants),
        "callers": joined(record.callers),
        "translation_strategies": joined(record.translation_strategies),
        "database_output_tiers": joined(record.database_output_tiers),
        "protein_product_classes": joined(record.protein_product_classes),
        "protein_length": len(record.sequence),
        "n_eligible_tryptic_peptides": record.n_eligible_tryptic_peptides,
        "min_eligible_peptide_length": record.min_eligible_peptide_length or "NA",
        "max_eligible_peptide_length": record.max_eligible_peptide_length or "NA",
        "original_description": record.original_description,
        "sequence": record.sequence,
    }

def read_input_records(
    fasta_files: Sequence[Path],
    forced_sources: Dict[Path, str],
    config: ProteinFilterConfig,
    record_sink: Optional[Callable[[ParsedRecord], None]] = None,
) -> Tuple[List[ParsedRecord], List[Dict[str, object]], Counter]:
    """Read/filter records.

    With ``record_sink`` each retained record is handed to the sink as it is
    read (the merge aggregates this way) and the returned record list is empty.
    """
    records: List[ParsedRecord] = []
    excluded_rows: List[Dict[str, object]] = []
    stats: Counter = Counter()
    contract = MergeInputContract()

    for fasta_path in fasta_files:
        LOGGER.info("Reading %s", fasta_path)
        file_count = 0

        with open_text_auto(fasta_path) as handle:
            for seq_record in SeqIO.parse(handle, "fasta"):
                stats["records_read"] += 1
                file_count += 1
                parsed = parse_fasta_record(
                    seq_record, fasta_path, forced_sources.get(fasta_path),
                    contract=contract,
                )

                first_header_token = parsed.original_description.split()[0]
                if DECOY_RE.search(first_header_token) or parsed.source.lower() == "decoy":
                    raise ValueError(
                        f"Input FASTA contains a decoy record ({parsed.original_id}); "
                        "quantmsdiann requires a target-only database"
                    )

                if parsed.record_type not in config.allowed_record_types:
                    stats["records_skipped_record_type"] += 1
                    excluded_rows.append(biological_record_row(parsed, False, "excluded_record_type"))
                    continue

                is_rescue = any(tier.lower() in RESCUE_TIERS for tier in parsed.database_output_tiers)
                if is_rescue and not config.include_rescue_tiers:
                    stats["records_skipped_rescue_tier"] += 1
                    excluded_rows.append(
                        biological_record_row(parsed, False, "excluded_rescue_database_tier")
                    )
                    continue

                valid, reason = validate_protein_sequence(parsed.sequence)
                if not valid:
                    stats[f"records_invalid_{reason}"] += 1
                    message = f"Invalid sequence in {fasta_path} record {parsed.original_id}: {reason}"
                    if config.invalid_policy == "error":
                        raise ValueError(message)
                    if config.invalid_policy == "warn":
                        LOGGER.warning(message)
                    excluded_rows.append(biological_record_row(parsed, False, reason))
                    continue

                # This independent protein-length floor is applied before the
                # configurable tryptic-peptide eligibility filter below. It is
                # not presented as equivalent to --min_peptide_length.
                if len(parsed.sequence) < config.min_length:
                    stats["records_skipped_too_short"] += 1
                    excluded_rows.append(
                        biological_record_row(parsed, False, f"protein_shorter_than_{config.min_length}aa")
                    )
                    continue

                if config.max_length is not None and len(parsed.sequence) > config.max_length:
                    stats["records_skipped_too_long"] += 1
                    excluded_rows.append(biological_record_row(parsed, False, "protein_longer_than_maximum"))
                    continue

                peptides = digest_tryptic_peptides(
                    parsed.sequence,
                    min_peptide_length=config.min_peptide_length,
                    max_peptide_length=config.max_peptide_length,
                    max_missed_cleavages=config.max_missed_cleavages,
                )
                parsed.n_eligible_tryptic_peptides = len(peptides)
                if peptides:
                    peptide_lengths = [len(peptide) for peptide in peptides]
                    parsed.min_eligible_peptide_length = min(peptide_lengths)
                    parsed.max_eligible_peptide_length = max(peptide_lengths)
                else:
                    stats["records_skipped_no_eligible_tryptic_peptide"] += 1
                    excluded_rows.append(
                        biological_record_row(parsed, False, "no_eligible_tryptic_peptide")
                    )
                    continue

                if record_sink is None:
                    records.append(parsed)
                else:
                    record_sink(parsed)
                stats["records_retained_after_dia_filtering"] += 1

        LOGGER.info("  parsed %d FASTA records", file_count)

    return records, excluded_rows, stats

def parse_record_types(values: Sequence[str]) -> Set[str]:
    out: Set[str] = set()
    for value in values:
        for token in re.split(r"[,;]", value):
            token = clean_value(token).lower()
            if token != "na":
                out.add(token)
    return out or {"protein"}
