#!/usr/bin/env python3
"""Canonical transcript translation, consequence, peptide, and FASTA utilities."""

import json
import hashlib
import logging
import pickle
import re
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq
from .proteogenomic_digestion import digest_record_dicts, digest_sequences
from .proteogenomic_policies import DigestionPolicy

from .pgdb_header import serialize_pgdb_header
from .audit import audit_fields

try:
    from pyfaidx import Fasta
except ImportError as exc:
    raise SystemExit("Error: pyfaidx is required. Install with pip install pyfaidx") from exc


def append_reason(existing: str, reason: str) -> str:
    """Append one semicolon-delimited exclusion reason."""
    return ";".join(filter(None, (existing, reason)))



def open_genome_index(genome: str):
    """Open pyfaidx Fasta index."""
    return Fasta(genome, sequence_always_upper=True, rebuild=False)



def extract_sequence_from_indexed_genome(fa_index, chrom: str, segments: List[Tuple[int, int]], strand: str) -> Optional[str]:
    """Fetch concatenated sequence for 1-based inclusive genomic segments."""
    if chrom not in fa_index:
        alt = None
        if chrom.startswith("chr"):
            alt = chrom[3:] if chrom[3:] in fa_index else None
        else:
            alt = "chr" + chrom if ("chr" + chrom) in fa_index else None
        if not alt:
            logging.debug("Chromosome %s not found in FASTA index", chrom)
            return None
        chrom = alt

    seq_parts = []
    for s, e in segments:
        if s <= 0 or e < s:
            logging.debug("Skipping invalid genomic segment: %s-%s", s, e)
            continue
        try:
            seq_parts.append(str(fa_index[chrom][s - 1:e]))
        except (KeyError, ValueError, IndexError) as exc:
            logging.debug("Failed to extract %s:%s-%s: %s", chrom, s, e, exc)
            return None

    if not seq_parts:
        return None

    full = "".join(seq_parts)
    if strand == "-":
        return str(Seq(full).reverse_complement())
    return full



def extract_cds_sequence_for_model(
    tx_model: Dict,
    fa_index,
    cds_segments: Optional[List[Tuple[int, int, int]]] = None,
) -> Optional[str]:
    """Extract canonical or altered CDS sequence for a transcript model."""
    segments = cds_segments if cds_segments is not None else tx_model.get("cds", [])
    if not segments:
        return None
    coords = [(s, e) for s, e, _ in segments]
    return extract_sequence_from_indexed_genome(
        fa_index,
        tx_model["chrom"],
        coords,
        tx_model["strand"],
    )



def trim_to_codon(seq: str) -> str:
    rem = len(seq) % 3
    return seq if rem==0 else seq[:-rem]



def pad_to_codon(seq: str) -> str:
    rem = len(seq) % 3
    return seq if rem == 0 else seq + ("N" * (3 - rem))



def _prepare_nt_for_translation(seq: str, pad: bool = False) -> str:
    """Normalise nucleotide sequence and make its length codon-compatible."""
    if not seq:
        return ""
    seq = seq.upper().replace("U", "T")
    return pad_to_codon(seq) if pad else trim_to_codon(seq)



def _translate_until_first_stop(
    seq: str, pad: bool = False, table: int = 1,
    force_initial_methionine: bool = False,
) -> Optional[str]:
    """Translate a nucleotide sequence in its current frame until the first stop codon."""
    seq_for = _prepare_nt_for_translation(seq, pad=pad)
    if not seq_for:
        return None
    aa = str(Seq(seq_for).translate(table=table, to_stop=False))
    if aa and force_initial_methionine:
        aa = "M" + aa[1:]
    aa = aa.split("*", 1)[0]
    return aa or None


def is_mitochondrial_chromosome(chrom: object) -> bool:
    return str(chrom or "").strip().upper().removeprefix("CHR") in {"M", "MT"}


def _genomic_feature_cds_offset(cds_segments, feature_start: int, feature_end: int, strand: str) -> Optional[int]:
    """Map the transcript-leading base of a genomic feature to a CDS offset."""
    ordered = sorted(cds_segments or [], key=lambda x: int(x[0]), reverse=strand == "-")
    position = int(feature_end) if strand == "-" else int(feature_start)
    cursor = 0
    for start, end, *_ in ordered:
        start, end = int(start), int(end)
        if start <= position <= end:
            return cursor + (end - position if strand == "-" else position - start)
        cursor += end - start + 1
    return None


def translate_cds_for_model(
    sequence: str, tx_model: Dict, cds_segments=None, pad: bool = False,
    stop_at_first: bool = True,
) -> Optional[str]:
    """Translate with annotated initiation, mitochondrial code, and Sec rules.

    Stop-codon readthrough is deliberately not guessed because the stop codon
    does not encode the inserted amino acid; callers audit/exclude that class.
    """
    prepared = _prepare_nt_for_translation(sequence, pad=pad)
    if not prepared:
        return None
    table = 2 if is_mitochondrial_chromosome(tx_model.get("chrom")) else 1
    amino_acids = list(str(Seq(prepared).translate(table=table, to_stop=False)))
    segments = cds_segments if cds_segments is not None else tx_model.get("cds", [])
    ordered_segments = sorted(
        segments or [], key=lambda x: int(x[0]),
        reverse=str(tx_model.get("strand")) == "-",
    )
    leading_trim = 0
    if cds_segments is None and ordered_segments:
        leading_trim = normalize_phase_value(ordered_segments[0][2]) or 0
    for interval in tx_model.get("selenocysteine_intervals", ()) or ():
        offset = _genomic_feature_cds_offset(
            segments, int(interval[0]), int(interval[1]), str(tx_model.get("strand"))
        )
        if offset is not None:
            offset -= leading_trim
        if offset is not None and offset % 3 == 0 and offset // 3 < len(amino_acids):
            amino_acids[offset // 3] = "U"
    annotated_alternative_initiation = bool(tx_model.get("non_atg_start"))
    mitochondrial_initiation = is_mitochondrial_chromosome(tx_model.get("chrom"))
    if (
        amino_acids
        and (annotated_alternative_initiation or mitochondrial_initiation)
        and not tx_model.get("cds_start_nf")
    ):
        amino_acids[0] = "M"
    protein = "".join(amino_acids)
    if stop_at_first:
        protein = protein.split("*", 1)[0]
    return protein or None


def mask_selenocysteine_stops_for_consequence(
    sequence: str, tx_model: Dict, cds_segments=None
) -> str:
    """Replace annotated Sec TGA codons with a synonymous non-stop placeholder.

    This is only for stop/NMD arithmetic; protein translation still emits U.
    """
    chars = list(str(sequence or "").upper())
    segments = cds_segments if cds_segments is not None else tx_model.get("cds", [])
    ordered = sorted(
        segments or [], key=lambda x: int(x[0]),
        reverse=str(tx_model.get("strand")) == "-",
    )
    leading_trim = 0
    if cds_segments is None and ordered:
        leading_trim = normalize_phase_value(ordered[0][2]) or 0
    for start, end in tx_model.get("selenocysteine_intervals", ()) or ():
        offset = _genomic_feature_cds_offset(
            segments, int(start), int(end), str(tx_model.get("strand"))
        )
        if offset is None:
            continue
        offset -= leading_trim
        if 0 <= offset and offset + 3 <= len(chars) and "".join(chars[offset:offset + 3]) == "TGA":
            chars[offset:offset + 3] = list("TGC")
    return "".join(chars)



def interval_length(intervals):
    """Return total length of interval tuples or CDS segment tuples."""
    total = 0
    for item in intervals or []:
        try:
            s, e = int(item[0]), int(item[1])
            if e >= s:
                total += e - s + 1
        except (TypeError, ValueError, IndexError):
            continue
    return total


def cds_frame_at_genomic_position(cds_segments, position, strand):
    """Return coding frame at a 1-based genomic CDS position.

    CDS features are traversed in transcript order. The leading GTF phase is
    subtracted once, matching the bases skipped before translation. Overlapping
    CDS features are rejected because their shared boundary would otherwise be
    order-dependent; directly adjacent, non-overlapping features are valid.
    """
    if strand not in {"+", "-"}:
        raise ValueError("strand must be + or -")
    ordered_genomic = sorted(
        [(int(x[0]), int(x[1]), x[2] if len(x) > 2 else 0) for x in cds_segments or []],
        key=lambda x: (x[0], x[1]),
    )
    for previous, current in zip(ordered_genomic, ordered_genomic[1:]):
        if current[0] <= previous[1]:
            raise ValueError(
                f"overlapping CDS segments make frame ambiguous: {previous[:2]} and {current[:2]}"
            )
    ordered = list(reversed(ordered_genomic)) if strand == "-" else ordered_genomic
    if not ordered:
        return None
    offset = -(normalize_phase_value(ordered[0][2]) or 0)
    coordinate = int(position)
    for start, end, _phase in ordered:
        if start <= coordinate <= end:
            offset += end - coordinate if strand == "-" else coordinate - start
            return offset % 3
        offset += end - start + 1
    return None


def classify_phased_junction_frame(
    donor_coding_nt: Optional[int],
    acceptor_upstream_coding_nt: Optional[int],
    donor_phase: Optional[int],
    acceptor_phase: Optional[int],
) -> str:
    """Classify a junction with the repository's sole phase convention.

    GTF phase is the number of bases to skip at the leading edge of a CDS
    feature. Missing phase remains unknown and returns ``NA``; callers may use a
    separately labelled sequence-length fallback but must not coerce phase to 0.
    """
    values = (donor_coding_nt, acceptor_upstream_coding_nt, donor_phase, acceptor_phase)
    if any(value is None for value in values):
        return "NA"
    donor_next_frame = (int(donor_phase) + int(donor_coding_nt)) % 3
    acceptor_frame = (int(acceptor_phase) + int(acceptor_upstream_coding_nt)) % 3
    return "INFRAME" if donor_next_frame == acceptor_frame else "FRAMESHIFT"


def merge_intervals(intervals):
    """Merge overlapping or directly adjacent genomic intervals."""
    ordered = sorted((int(item[0]), int(item[1])) for item in (intervals or []))
    merged = []
    for start, end in ordered:
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def intersect_interval_lists(a, b):
    """Return intersections between normalized inclusive interval lists."""
    left, right = merge_intervals(a), merge_intervals(b)
    output = []
    i = j = 0
    while i < len(left) and j < len(right):
        left_start, left_end = left[i]
        right_start, right_end = right[j]
        if left_end < right_start:
            i += 1
        elif right_end < left_start:
            j += 1
        else:
            output.append((max(left_start, right_start), min(left_end, right_end)))
            if left_end < right_end:
                i += 1
            else:
                j += 1
    return output


def subtract_interval_list(intervals, remove_start, remove_end):
    """Subtract one inclusive interval from a list."""
    output = []
    for start, end in intervals:
        if end < remove_start or start > remove_end:
            output.append((start, end))
        else:
            if start < remove_start:
                output.append((start, remove_start - 1))
            if end > remove_end:
                output.append((remove_end + 1, end))
    return output


def replace_interval_in_list(intervals, target_start, target_end, replacements):
    """Replace an overlapping inclusive interval once and normalize output."""
    output, pending = [], list(replacements)
    for start, end in intervals:
        if end < target_start or start > target_end:
            output.append((start, end))
            continue
        if start < target_start:
            output.append((start, target_start - 1))
        if pending:
            output.extend(pending)
            pending = []
        if end > target_end:
            output.append((target_end + 1, end))
    return merge_intervals(output)


def match_transcript_id(tx_id, transcripts_or_alias_index, transcript_models=None, preferred_chrom=None):
    """Resolve a versioned/unversioned transcript ID to a transcript-model key.

    The two-argument form accepts a transcript-model dictionary.  The extended
    form accepts an alias index followed by the model dictionary and ranks
    ambiguous aliases by chromosome match, CDS length, and exon count.
    """
    if not tx_id:
        return None
    base = str(tx_id).split('.', 1)[0]
    if transcript_models is None:
        models = transcripts_or_alias_index
        for candidate in (str(tx_id), base):
            if candidate in models:
                return candidate
        for candidate in models:
            if str(candidate).split('.', 1)[0] == base:
                return candidate
        logging.warning("match_transcript_id: no match for %s", tx_id)
        return None

    alias_index = transcripts_or_alias_index
    candidates = []
    for key in (str(tx_id), base):
        candidates.extend(alias_index.get(key, []))
    if not candidates:
        candidates.extend(key for key in (str(tx_id), base) if key in transcript_models)
    unique = [candidate for candidate in dict.fromkeys(candidates) if candidate in transcript_models]
    if not unique:
        return None

    def rank(candidate):
        model = transcript_models[candidate]
        model_chrom = str(model.get('chrom', '')).removeprefix('chr')
        wanted_chrom = str(preferred_chrom or '').removeprefix('chr')
        chrom_bonus = int(bool(wanted_chrom) and model_chrom == wanted_chrom)
        cds_len = model.get('cds_len', interval_length(model.get('cds')))
        exon_count = model.get('exon_count', len(model.get('exons') or []))
        return chrom_bonus, int(cds_len or 0), int(exon_count or 0), str(candidate)

    return max(unique, key=rank)


def normalize_phase_value(value):
    """Convert a GTF/GFF CDS phase value to 0, 1, 2, or ``None``."""
    if value in (None, '.', ''):
        return None
    try:
        phase = int(value)
    except (TypeError, ValueError):
        return None
    return phase if phase in {0, 1, 2} else None



def canonical_start_genomic(cds_list, strand):
    """Return annotated CDS start coordinate in transcript direction."""
    if not cds_list:
        return None
    if strand == '+':
        return min(int(c[0]) for c in cds_list)
    return max(int(c[1]) for c in cds_list)



def first_stop_codon_aa(seq_nt, start_nt=0, pad=False):
    """Return first stop codon details in a codon-aligned sequence.

    Returns (stop_aa_1based, stop_nt_1based, is_terminal_stop, translated_aa).
    A terminal stop is the final codon of the translated nucleotide sequence and is
    not treated as a premature termination codon.
    """
    if not seq_nt:
        return None, None, None, None
    seq = seq_nt.upper().replace('U', 'T')
    if start_nt < 0:
        start_nt = 0
    seq = seq[start_nt:]
    seq = pad_to_codon(seq) if pad else trim_to_codon(seq)
    if not seq:
        return None, None, None, None
    aa = str(Seq(seq).translate(to_stop=False))
    stop_idx = aa.find('*')
    if stop_idx == -1:
        return None, None, None, aa
    is_terminal = (stop_idx == len(aa) - 1)
    return stop_idx + 1, start_nt + (stop_idx * 3) + 1, is_terminal, aa



def exon_junction_positions_from_exon_segments(
    exon_segments, cds_segments, strand, translation_start_offset_nt=0
):
    """Return all transcript exon junctions as CDS-relative 1-based positions.

    Junctions in the 3-prime UTR are retained.  Negative positions can represent 5-prime UTR
    junctions and are harmless to downstream-junction NMD filtering.
    """
    if not exon_segments or not cds_segments:
        return []
    reverse = strand == '-'
    exons = sorted(((int(x[0]), int(x[1])) for x in exon_segments), key=lambda x: x[0], reverse=reverse)
    cds = sorted(((int(x[0]), int(x[1])) for x in cds_segments), key=lambda x: x[0], reverse=reverse)
    cds_start_genomic = cds[0][1] if reverse else cds[0][0]
    transcript_cursor = 0
    cds_start_offset = None
    junction_offsets = []
    for index, (start, end) in enumerate(exons):
        if start <= cds_start_genomic <= end:
            within = end - cds_start_genomic if reverse else cds_start_genomic - start
            cds_start_offset = transcript_cursor + within
        transcript_cursor += end - start + 1
        if index < len(exons) - 1:
            junction_offsets.append(transcript_cursor)
    if cds_start_offset is None:
        return []
    return [
        offset - cds_start_offset - int(translation_start_offset_nt or 0)
        for offset in junction_offsets
    ]



def nmd_prediction(stop_nt_1based, exon_junction_nt_positions, distance_threshold_nt=55):
    """Apply the 55-nt NMD rule using the stop codon's final nucleotide.

    Coordinates are 1-based nucleotide positions relative to the translated
    CDS. ``stop_nt_1based`` is the first base of the three-base stop codon, so
    ``stop_end`` is ``start + 2``. Distance is measured from that final stop
    nucleotide to the nearest downstream exon-exon junction. This anchoring is
    the convention described for the ~50--55 nt boundary by Nagy & Maquat
    (1998), Trends Biochem Sci 23:198--199, doi:10.1016/S0968-0004(98)01208-0.
    """
    if stop_nt_1based is None:
        return False, 'no_premature_stop_detected', None, None
    stop_end = int(stop_nt_1based) + 2
    downstream = [int(j) for j in (exon_junction_nt_positions or []) if int(j) > stop_end]
    if not downstream:
        return False, 'no_downstream_junction_after_stop', None, None
    nearest = min(downstream)
    distance = nearest - stop_end
    return distance >= int(distance_threshold_nt), (
        'ptc_far_upstream_of_downstream_junction' if distance >= int(distance_threshold_nt) else 'stop_near_terminal_junction'
    ), nearest, distance



def should_include_protein_in_fasta(consequence, args):
    """Apply optional DIA/search-FASTA filters. Defaults are permissive.

    Missing/``None`` ``cds_completeness`` means "not annotated as incomplete",
    not "proven complete". Only explicit partial-CDS labels are excluded. This
    preserves callers that cannot supply GTF completeness tags while preventing
    an unknown value from being misrepresented as a complete annotation.
    """
    if not consequence:
        return True, ''
    reasons = []
    # A missing/None boolean is intentionally treated as "not flagged", not as unknown.
    configured = getattr(args, 'reconstruction_policy', None)
    dia = configured.dia if configured is not None else None
    exclude_incomplete = dia.exclude_incomplete_cds if dia else getattr(args, 'exclude_incomplete_cds', True)
    exclude_frameshift = dia.exclude_frameshift if dia else getattr(args, 'exclude_frameshift_from_dia', False)
    exclude_nmd = dia.exclude_nmd if dia else getattr(args, 'exclude_nmd_from_dia', False)
    exclude_start_loss = dia.exclude_start_loss if dia else getattr(args, 'exclude_start_loss_from_dia', False)
    if exclude_incomplete and consequence.get('cds_completeness') not in (None, 'complete'):
        reasons.append('incomplete_cds_excluded_from_dia')
    if consequence.get('stop_codon_readthrough') is True:
        reasons.append('annotated_stop_codon_readthrough_not_reconstructed')
    if consequence.get('selenocysteine_reconstruction_supported') is False:
        reasons.append('annotated_selenocysteine_not_supported_for_altered_cds')
    if exclude_frameshift and consequence.get('frameshift') is True:
        reasons.append('frameshift_excluded_from_dia')
    if exclude_nmd and consequence.get('nmd_predicted') is True:
        reasons.append('nmd_predicted_excluded_from_dia')
    if exclude_start_loss and consequence.get('start_loss') is True:
        reasons.append('start_loss_excluded_from_dia')
    if getattr(args, 'exclude_premature_stop_from_dia', False) and consequence.get('premature_stop') is True:
        reasons.append('premature_stop_excluded_from_dia')
    if getattr(args, 'require_ri_orf_preserved', False) and consequence.get('ri_event') is True and consequence.get('ri_orf_preserved') is not True:
        reasons.append('retained_intron_orf_not_preserved')
    return len(reasons) == 0, ';'.join(reasons)



def write_consequence_tsv(rows, out_path, preferred_columns=None):
    """Write biological interpretation/consequence table."""
    if not out_path:
        return
    # Production callers pass the declared schema and receive the evidence
    # extension. Keeping the no-schema path unchanged preserves this utility's
    # backwards-compatible generic TSV behaviour.
    if preferred_columns is not None:
        from .biological_evidence import biological_evidence_fields
        audited_rows = [
            {**row, **biological_evidence_fields(row), **audit_fields(row)}
            for row in (rows or [])
        ]
    else:
        audited_rows = [{**row, **audit_fields(row)} for row in (rows or [])]
    df = pd.DataFrame(audited_rows)
    if preferred_columns is None:
        evidence_columns = {
            'reading_frame', 'nmd', 'stop_gain', 'unique_peptide',
            'junction_peptide', 'reference_peptide_overlap', 'psi',
            'junction_reads', 'inclusion_tier', 'consequence_category', 'confidence_score',
            'confidence', 'confidence_reasons', 'compatible_transcripts',
            'transcript_rank_1', 'transcript_rank_2', 'transcript_rank_3',
            'transcript_selection_path',
        }
        legacy_prefix = ['source_file', 'event_type', 'event_id', 'gene_id', 'gene_symbol', 'tx']
        preferred_columns = legacy_prefix + [
            column for column in CONSEQUENCE_TSV_COLUMNS
            if column not in evidence_columns and column not in legacy_prefix
        ]
    for column in preferred_columns:
        if column not in df.columns:
            df[column] = pd.NA
    ordered = list(preferred_columns)
    ordered.extend(column for column in df.columns if column not in ordered)
    df = df.reindex(columns=ordered)
    df.to_csv(out_path, sep='\t', index=False)
    logging.info('Wrote consequence annotation table to %s (%d rows)', out_path, len(df))



def _fasta_token(value, default="NA"):
    """Return a delimiter-safe FASTA header token."""
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "na", "n/a", "."}:
        return default
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[|;,=]", "_", text)
    return text



def _compact_values(values, limit=10):
    """Return a deterministic compact list for a FASTA header."""
    cleaned = sorted({_fasta_token(v) for v in values if _fasta_token(v) != "NA"})
    if not cleaned:
        return "NA"
    shown = cleaned[:limit]
    if len(cleaned) > limit:
        shown.append(f"plus_{len(cleaned) - limit}_more")
    return ",".join(shown)



def digest_tryptic_records(protein_sequence, max_missed_cleavages=2, min_len=7, max_len=40):
    """Canonical digestion result with 1-based positions and missed-cleavage count."""
    return digest_record_dicts(
        protein_sequence, DigestionPolicy(max_missed_cleavages, min_len, max_len)
    )


def digest_tryptic_peptides(protein_sequence, max_missed_cleavages=2, min_len=7, max_len=40):
    """Return unique tryptic peptide sequences (K/R, except before P)."""
    return digest_sequences(
        protein_sequence, DigestionPolicy(max_missed_cleavages, min_len, max_len)
    )



def load_reference_tryptic_peptides(fasta_path, max_missed_cleavages=2, min_len=7, max_len=40, cache_path=None):
    """Build the canonical-proteome tryptic-peptide set used for uniqueness checks."""
    if not fasta_path:
        return None
    digest = hashlib.sha256()
    with open(fasta_path, "rb") as reference_handle:
        for block in iter(lambda: reference_handle.read(1024 * 1024), b""):
            digest.update(block)
    cache_key = f"{digest.hexdigest()}:{max_missed_cleavages}:{min_len}:{max_len}"
    if cache_path and Path(cache_path).is_file():
        try:
            with Path(cache_path).open("rb") as cache_handle:
                cached = pickle.load(cache_handle)
            if cached.get("cache_key") == cache_key and isinstance(cached.get("peptides"), set):
                logging.info("Loaded %d reference tryptic peptides from cache", len(cached["peptides"]))
                return cached["peptides"]
        except (OSError, EOFError, pickle.UnpicklingError, AttributeError, TypeError):
            logging.warning("Ignoring invalid reference-peptide cache: %s", cache_path)
    peptides = set()
    with Path(fasta_path).open("r", encoding="utf-8") as fasta_handle:
        for record in SeqIO.parse(fasta_handle, "fasta"):
            peptides.update(digest_tryptic_peptides(
                str(record.seq), max_missed_cleavages, min_len, max_len
            ))
    logging.info("Loaded %d reference tryptic peptides", len(peptides))
    if cache_path:
        cache_file = Path(cache_path)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with cache_file.open("wb") as cache_handle:
            pickle.dump({"cache_key": cache_key, "peptides": peptides}, cache_handle, protocol=pickle.HIGHEST_PROTOCOL)
    return peptides



def count_reference_unique_tryptic_peptides(protein_sequence, reference_peptides, max_missed_cleavages=2, min_len=7, max_len=40):
    """Count detectable tryptic peptides absent from the supplied reference proteome."""
    if reference_peptides is None:
        return 0
    peptides = digest_tryptic_peptides(
        protein_sequence, max_missed_cleavages, min_len, max_len
    )
    return sum(peptide not in reference_peptides for peptide in peptides)



def add_protein_mapping(prot_info, protein_sequence, mapping):
    """Retain mappings, producing e.g. ``{sequence: {'mappings': [mapping]}}``."""
    entry = prot_info.setdefault(protein_sequence, {"mappings": []})
    key = tuple((k, str(mapping.get(k, "NA"))) for k in sorted(mapping))
    existing = {
        tuple((k, str(m.get(k, "NA"))) for k in sorted(m))
        for m in entry["mappings"]
    }
    if key not in existing:
        entry["mappings"].append(dict(mapping))



def build_splice_fasta_header(source, record_number, protein_sequence, entry):
    """Build a shared rMATS/SUPPA protein FASTA header schema."""
    mappings = entry.get("mappings", [])
    first = mappings[0] if mappings else {}
    prefix = source.upper()
    tier = _fasta_token(first.get("database_output_tier"), "primary_dia")
    code = {"primary": "P", "primary_dia": "P", "exploratory": "X",
            "alternative_start": "X", "exploratory_orf": "X"}.get(tier, "P")
    record_id = f"{prefix}_{code}{record_number:06d}"
    gene_symbol = _fasta_token(first.get('gene_symbol'))
    metadata = [
        ("schema_version", "pgdb-merge-input-v1"),
        ("source", source.lower()), ("record_type", "protein"),
        ("record_id", record_id), ("gene_id", first.get('gene_id')),
        ("transcript", first.get('tx')), ("event_type", first.get('event_type')),
        ("event_id", first.get('event_id')), ("variant", first.get('variant')),
        ("source_event_id", first.get("source_event_id")),
        ("psi_min_threshold", first.get("psi_min_threshold")),
        ("psi_min_samples", first.get("psi_min_samples")),
        ("sample_id", first.get('sample_id')), ("batch", first.get('batch')),
        ("condition", first.get('condition')),
        ("annotation_release", first.get('annotation_release')),
        ("alt_start", first.get("alt_start", "No")),
        ("alt_start_codon", first.get("alt_start_codon")),
        ("alt_start_kozak_strength", first.get("alt_start_kozak_strength")),
        ("alt_start_kozak_score", first.get("alt_start_kozak_score")),
        ("alt_start_kozak_context", first.get("alt_start_kozak_context")),
        ("transcript_selection_score", first.get("transcript_selection_score")),
        ("transcript_selection_rank", first.get("transcript_selection_rank")),
        ("transcript_candidate_count", first.get("transcript_candidate_count")),
        ("transcript_selection_ambiguous", first.get("transcript_selection_ambiguous")),
        ("mapping_count", len(mappings)),
        ("all_transcripts", _compact_values(m.get('tx') for m in mappings)),
        ("all_event_types", _compact_values(m.get('event_type') for m in mappings)),
        ("all_event_ids", _compact_values(m.get('event_id') for m in mappings)),
        ("all_variants", _compact_values(m.get('variant') for m in mappings)),
        ("translation_strategy", first.get('translation_strategy')),
        ("translation_note", first.get('translation_note')),
        ("database_output_tier", tier),
        ("passed_dia_filters", first.get("passed_dia_filters")),
        ("fasta_exclusion_reasons", first.get("fasta_exclusion_reasons")),
        ("protein_length", len(protein_sequence)),
    ]
    return serialize_pgdb_header(
        record_id, gene_symbol, metadata,
        organism=first.get("organism", "unknown_organism"),
    )



def write_junction_fasta(junction_recs, out_path):
    uniq = {}
    for rec in junction_recs:
        key = str(rec.seq)
        if key not in uniq:
            uniq[key] = rec
    SeqIO.write(list(uniq.values()), out_path, "fasta")


def write_protein_fasta(prot_info, out_path, source):
    """Write de-duplicated proteins with the shared biological header schema."""
    records = list(prot_info.items())
    with open(out_path, "w") as handle:
        for index, (protein, entry) in enumerate(records, start=1):
            header = build_splice_fasta_header(source, index, protein, entry)
            handle.write(f">{header}\n{protein}\n")
    logging.info("Writing FASTA to %s (unique sequences: %d)", out_path, len(records))
CONSEQUENCE_TSV_COLUMNS = [
    'event_id', 'tx', 'gene_symbol', 'reading_frame', 'nmd', 'stop_gain',
    'unique_peptide', 'junction_peptide', 'reference_peptide_overlap', 'psi',
    'junction_reads', 'inclusion_tier', 'consequence_category', 'confidence_score', 'confidence',
    'confidence_reasons',
    'source_file', 'event_type', 'gene_id',
    'variant', 'ioe_transcript_group', 'requested_alternative_transcripts',
    'reconstruction_scope', 'expression_evidence_status',
    'requested_reference_transcripts', 'unresolved_transcripts',
    'event_processing_status', 'region_class', 'coords', 'first_overlap',
    'psi_mean', 'psi_max', 'psi_valid_samples',
    'inclusion_junction_reads', 'skipping_junction_reads',
    'canonical_start_genomic', 'original_cds_len', 'altered_cds_len',
    'cds_delta_nt', 'start_retained', 'start_loss',
    'start_retained_relative_to_own_annotation',
    'start_loss_relative_to_own_annotation', 'terminal_stop',
    'cds_start_nf', 'cds_end_nf', 'cds_completeness', 'frame_status',
    'non_atg_start', 'stop_codon_readthrough',
    'selenocysteine_feature_count', 'selenocysteine_reconstruction_supported',
    'translation_table',
    'frameshift', 'inframe', 'premature_stop',
    'first_stop_aa_1based', 'first_stop_nt_1based', 'nmd_predicted',
    'nmd_reason', 'nearest_downstream_exon_junction_nt', 'nmd_distance_nt',
    'ri_event', 'ri_orf_preserved', 'ri_boundary_fallback',
    'ri_read_evidence_supported', 'ri_ambiguous_base_count',
    'ri_intronic_stop_count', 'ri_export_plausibility',
    'ri_has_junction_spanning_searchable_peptide', 'trim', 'trimmed',
    'frame_mismatch', 'pad_partial_codons',
    'translation_strategy', 'translation_note', 'database_output_tier',
    'has_reference_unique_tryptic_peptide',
    'reference_unique_tryptic_peptide_count',
    'has_opposite_isoform_unique_tryptic_peptide',
    'opposite_isoform_unique_tryptic_peptide_count', 'protein_sequence',
    'protein_length', 'protein_in_fasta', 'fasta_exclusion_reasons',
    'consequence_class',
    'frame_comparison_basis', 'frame_comparison_transcript', 'first_stop_aa',
    'alt_start_kozak_context', 'transcript_selection_score',
    'transcript_selection_rank', 'transcript_candidate_count',
    'transcript_selection_ambiguous', 'transcript_tied_best_count',
    'transcript_selection_reason', 'transcript_manual_review_required',
    'compatible_transcripts', 'transcript_rank_1', 'transcript_rank_2',
    'transcript_rank_3', 'transcript_selection_path',
]


def cds_completeness(cds_start_nf: bool, cds_end_nf: bool) -> str:
    """Return an auditable GENCODE incomplete-CDS classification."""
    if cds_start_nf and cds_end_nf:
        return 'partial_start_and_end'
    if cds_start_nf:
        return 'partial_start'
    if cds_end_nf:
        return 'partial_end'
    return 'complete'


def transcript_cds_audit_fields(tx_model: Dict) -> Dict:
    """Return consequence-table fields shared by SUPPA and rMATS."""
    start_nf = bool((tx_model or {}).get('cds_start_nf'))
    end_nf = bool((tx_model or {}).get('cds_end_nf'))
    return {
        'cds_start_nf': start_nf,
        'cds_end_nf': end_nf,
        'cds_completeness': cds_completeness(start_nf, end_nf),
        'non_atg_start': bool((tx_model or {}).get('non_atg_start')),
        'stop_codon_readthrough': bool((tx_model or {}).get('stop_codon_readthrough')),
        'selenocysteine_feature_count': len((tx_model or {}).get('selenocysteine_intervals') or ()),
        'translation_table': 2 if is_mitochondrial_chromosome((tx_model or {}).get('chrom')) else 1,
    }


def write_run_manifest(args, output_fasta, script_name=None):
    """Write versioned configuration and input-checksum provenance."""
    path = f"{output_fasta}.run_config.json"
    arguments = args.to_dict() if hasattr(args, 'to_dict') else vars(args)
    serialized = json.dumps(arguments, default=str, sort_keys=True, separators=(',', ':'))
    output_prefixes = ('out_', 'filtered_', 'biological_', 'dia_database_', 'digested_')
    input_paths = set()
    for name, value in arguments.items():
        if name.startswith(output_prefixes) or name in {'profile', 'workers', 'chunksize'}:
            continue
        values = value if isinstance(value, (list, tuple)) else [value]
        for item in values:
            candidate = Path(str(item)) if isinstance(item, (str, Path)) else None
            if candidate and candidate.is_file():
                input_paths.add(candidate)
            elif candidate and candidate.is_dir():
                input_paths.update(p for p in candidate.rglob('*') if p.is_file())

    def sha256_file(input_path):
        digest = hashlib.sha256()
        with input_path.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
        return digest.hexdigest()

    try:
        version = importlib.metadata.version('proteogenomic-database-reconstruction')
    except importlib.metadata.PackageNotFoundError:
        version = '0.1.0'
    payload = {
        'schema_version': 'pgdb-producer-run-v1',
        'software_version': version,
        'script': script_name,
        'configuration_sha256': hashlib.sha256(serialized.encode('utf-8')).hexdigest(),
        'arguments': arguments,
        'input_sha256': {str(item): sha256_file(item) for item in sorted(input_paths)},
    }
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, default=str, sort_keys=True)
        handle.write('\n')
    logging.info('Wrote resolved run manifest to %s', path)
    return path
