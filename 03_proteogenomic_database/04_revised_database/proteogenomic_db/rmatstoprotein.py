#!/usr/bin/env python3
"""Convert rMATS splice events into typed protein candidates and audit outputs."""
import json
import logging
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

import pandas as pd
from Bio.SeqRecord import SeqRecord
from tqdm import tqdm

from proteogenomic.provenance import batch_from_path, configure_logging, require_files
from proteogenomic.splice_reconstruction_core import (
    CanonicalProteinCache, GenomeSequenceCache, merge_protein_mappings,
    SpliceFileResult, SpliceReconstructionConfig, genome_to_transcript,
)
from proteogenomic.splice_translation import (
    CONSEQUENCE_TSV_COLUMNS,
    _translate_until_first_stop,
    add_protein_mapping,
    append_reason,
    cds_frame_at_genomic_position,
    canonical_start_genomic,
    count_reference_unique_tryptic_peptides,
    extract_sequence_from_indexed_genome,
    generate_codon_aware_junction_peptides,
    interval_length,
    load_reference_tryptic_peptides,
    match_transcript_id,
    merge_intervals,
    normalize_phase_value, open_genome_index,
    subtract_interval_list,
    replace_interval_in_list,
    should_include_protein_in_fasta,
    write_consequence_tsv,
    write_junction_fasta,
    write_protein_fasta,
    transcript_cds_audit_fields,
    prepare_run_manifest, publish_run_manifest, translate_cds_for_model, is_mitochondrial_chromosome,
    mask_selenocysteine_stops_for_consequence,
)
from proteogenomic.proteogenomic_models import SpliceProteinResult
from proteogenomic.proteogenomic_policies import ReconstructionPolicy
from proteogenomic.rmats_stages import choose_output_tier, project_event_variants, resolve_variant_frame
from proteogenomic.splice_cli import parse_rmats_args
from proteogenomic.rmats_parsing import (
    _rmats_start_1based, _row_int, _row_int_auto, event_overlaps_transcript_cds,
    normalise_event_file_lists, overlaps, rmats_event_intervals, transcript_is_event_compatible,
)
from proteogenomic.rmats_parsing import RMATS_COORDINATE_BASE  # noqa: F401  (compatibility export)
from proteogenomic.rmats_evidence import (
    count_event_rows, evaluate_rmats_event, finalise_primary_event_peptide_evidence,
    finish_event_summary, retained_intron_evidence, write_event_summary,
)
from proteogenomic.splice_annotation import build_transcript_models
from proteogenomic.splice_rescue import (
    ALT_START_NOTE_PREFIX, RESCUE_STRATEGIES, alternative_start_fields, alternative_start_from_note,
    find_alternative_start, longest_orf_from_sequence, normalise_start_codons,
)

# Former private name, kept for callers of the rMATS module.
_longest_orf_from_sequence = longest_orf_from_sequence
from proteogenomic.release_validation import preflight_producer_contract
from proteogenomic.splice_consequence import evaluate_shared_splice_consequence

Interval = Tuple[int, int]


class CDSSegment(NamedTuple):
    start: int
    end: int
    frame: Optional[int]


_RETAINED_INTRON_VARIANTS = frozenset({"retained", "retention", "ri_retained"})


def event_file_provenance(path: Path, args) -> Dict[str, str]:
    """Record batch and rMATS comparison without pretending counts are per-sample."""
    parts = list(path.parts)
    comparison = next((part for part in reversed(parts[:-1]) if "-" in part), "NA")
    conditions = ";".join(x for x in comparison.split("-") if x) if comparison != "NA" else "NA"
    explicit = getattr(args, 'event_metadata_lookup', {}).get(str(path.resolve()), {})
    return {
        "sample_id": "NA",
        "batch": explicit.get('batch', batch_from_path(path)),
        "condition": explicit.get('condition', conditions),
        "comparison": explicit.get('sample', comparison),
        "organism": args.organism,
        "annotation_release": args.annotation_release,
    }


# --------------------------- GENE -> TRANSCRIPT LOOKUP ---------------------------
def canonicalize_gene_field(raw_gene: str) -> str:
    """Return the versionless Ensembl ID for ENS* identifiers, otherwise the stripped symbol."""
    if raw_gene is None:
        return ""
    g = str(raw_gene).strip()
    if re.match(r"^ENS[A-Z0-9]+", g, flags=re.IGNORECASE):
        return g.split('.', 1)[0]
    return g


def generate_gene_id_candidates(raw_gene: Optional[str]) -> List[str]:
    """Return ordered, de-duplicated keys to probe ``transcripts_lookup``.

    Variants: raw, versionless Ensembl ID, upper/lower case, and space-free forms.
    """
    if raw_gene is None or str(raw_gene).strip() == "":
        return ["NA"]
    g = str(raw_gene).strip()
    candidates = [g, canonicalize_gene_field(g), g.split('.', 1)[0], g.upper(), g.lower(), g.replace(" ", "")]
    return list(dict.fromkeys(x for x in candidates if x))


def build_transcripts_lookup(transcripts: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Map gene_id/gene_name (and case/version variants) to transcript IDs.

    Versionless transcript keys are resolver aliases, not additional biological
    models; excluding them prevents every isoform from being ranked and
    reconstructed twice while match_transcript_id still accepts either form.
    """
    lookup = defaultdict(list)
    versioned_bases = {tid.split('.', 1)[0] for tid in transcripts if '.' in tid}
    for tid, info in transcripts.items():
        if '.' not in tid and tid in versioned_bases:
            continue
        gid = info.get("gene_id")
        gname = info.get("gene_name")
        keys = []
        if gid:
            keys += [gid, str(gid).split('.', 1)[0]]
        if gname:
            keys += [gname, gname.upper(), gname.lower()]
        for key in keys:
            lookup[key].append(tid)
    return {key: list(dict.fromkeys(values)) for key, values in lookup.items()}


# --------------------------- BUILD VARIANT EXON CHAINS ---------------------------
def _event_identifier(row: dict) -> str:
    return row.get('ID') or row.get('Event') or row.get('GeneID') or row.get('geneSymbol') or ''


def build_variant_chains_for_transcript(event_type: str, row: dict, tx_exons: List[Tuple[int,int]]) -> Dict[str, List[Tuple[int,int]]]:
    """Construct exon chains for a transcript given an rMATS event row.
    Interpret rMATS coordinate columns with names containing '_0base' as 0-based starts and convert them to 1-based.
    """
    def get_int(names):
        return _row_int_auto(row, list(names))

    chains = {}

    # SE
    if event_type == "SE":
        exon_s = _rmats_start_1based(row, ['exonStart_0base'])
        exon_e = get_int(['exonEnd'])
        if exon_s is None or exon_e is None:
            logging.warning("Missing coordinates for SE event; skipping (id=%s)", _event_identifier(row))
            return {}
        chains['included'] = tx_exons.copy()
        chains['skipped'] = subtract_interval_list(tx_exons, exon_s, exon_e)

    # A3SS / A5SS
    elif event_type in ("A3SS", "A5SS"):
        long_s = _rmats_start_1based(row, ['longExonStart_0base', 'longExonStart'])
        long_e = get_int(['longExonEnd', 'longExonEnd_0base'])
        # flankingES/EE describe the neighbouring exon, never the short alternative.
        short_s = _rmats_start_1based(row, ['shortES', 'shortExonStart_0base', 'shortExonStart'])
        short_e = get_int(['shortEE', 'shortExonEnd', 'shortExonEnd_0base'])
        if None in (long_s, long_e, short_s, short_e):
            logging.warning("Missing coordinates for %s event; skipping (id=%s)", event_type, _event_identifier(row))
            return {}
        chains['long'] = replace_interval_in_list(tx_exons, long_s, long_e, [(long_s, long_e)])
        chains['short'] = replace_interval_in_list(tx_exons, short_s, short_e, [(short_s, short_e)])

    # MXE
    elif event_type == "MXE":
        x1_s = _rmats_start_1based(row, ['1stExonStart_0base', 'X1stExonStart_0base'])
        x1_e = get_int(['1stExonEnd', 'X1stExonEnd'])
        x2_s = _rmats_start_1based(row, ['2ndExonStart_0base', 'X2ndExonStart_0base'])
        x2_e = get_int(['2ndExonEnd', 'X2ndExonEnd'])
        if None in (x1_s, x1_e, x2_s, x2_e):
            logging.warning("Missing coordinates for MXE event; skipping (id=%s)", _event_identifier(row))
            return {}
        contains_x1 = any(start <= x1_s and end >= x1_e for start, end in tx_exons)
        contains_x2 = any(start <= x2_s and end >= x2_e for start, end in tx_exons)
        # An ordinary annotated isoform contains zero or one MXE alternative;
        # subtracting the absent alternative is intentionally a no-op. A model
        # containing both is not mutually exclusive and cannot be reconstructed
        # safely with this two-chain operation.
        if contains_x1 and contains_x2:
            logging.warning(
                "MXE transcript contains both alternative exons; skipping non-biological chain (id=%s)",
                _event_identifier(row),
            )
            return {}
        without_mxe = subtract_interval_list(tx_exons, x1_s, x1_e)
        without_mxe = subtract_interval_list(without_mxe, x2_s, x2_e)
        chains['exon1'] = merge_intervals(without_mxe + [(x1_s, x1_e)])
        chains['exon2'] = merge_intervals(without_mxe + [(x2_s, x2_e)])

    # RI
    elif event_type == "RI":
        ri_s = _rmats_start_1based(row, ['riExonStart_0base'])
        ri_e = get_int(['riExonEnd'])
        up_e = get_int(['upstreamEE'])
        down_s = _rmats_start_1based(row, ['downstreamES'])
        if ri_s is None or ri_e is None:
            return {}
        up_e = up_e if up_e is not None else ri_s - 1
        down_s = down_s if down_s is not None else ri_e + 1
        intron_start, intron_end = up_e + 1, down_s - 1
        if intron_start > intron_end:
            logging.warning("Empty/inverted RI interval; skipping event (id=%s)", _event_identifier(row))
            return {}
        spliced = merge_intervals(tx_exons)
        chains['retained'] = merge_intervals(spliced + [(intron_start, intron_end)])
        chains['spliced'] = spliced

    # sort
    for k in list(chains.keys()):
        chains[k] = sorted(chains[k], key=lambda x: x[0])
    return chains

# --------------------------- CDS INTERSECTION AND FRAME CALCULATION ---------------------------
def intersect_chain_with_cds(exon_chain: List[Interval], cds_list: List[CDSSegment]) -> List[CDSSegment]:
    """Project an altered exon chain through the annotated coding span.

    Intersecting only with the original CDS features silently drops retained
    introns, mutually exclusive exons, and extended alternative splice sites.
    The annotated CDS start/end remain the coding boundaries, while altered
    exonic sequence inside that span is retained for consequence translation.
    """
    if not exon_chain or not cds_list:
        return []
    coding_start = min(start for start, _end, _phase in cds_list)
    coding_end = max(end for _start, end, _phase in cds_list)
    cds_segs = []
    for exon_start, exon_end in exon_chain:
        ov_start = max(exon_start, coding_start)
        ov_end = min(exon_end, coding_end)
        if ov_start > ov_end:
            continue
        phase = 0
        for cds_start, cds_end, cds_phase in cds_list:
            if overlaps(ov_start, ov_end, cds_start, cds_end):
                phase = cds_phase
                break
        cds_segs.append((ov_start, ov_end, phase))
    return sorted(cds_segs, key=lambda x: x[0])

def compute_upstream_cds_nt(transcript_cds: List[Tuple[int,int,int]], first_overlap_pos: int, strand: str) -> int:
    """Return the CDS offset at an exonic coordinate or intronic insertion boundary.

    Mapping is deterministic in transcript order on both strands. Overlapping
    CDS intervals and coordinates outside the CDS span raise instead of allowing
    feature sort order to choose an offset. A coordinate in a gap between CDS
    exons is valid for retained-intron reconstruction and maps to the cumulative
    CDS length immediately upstream in transcript order.
    """
    if not transcript_cds:
        return 0

    intervals = [(int(start), int(end)) for start, end, _phase in transcript_cds]
    position = int(first_overlap_pos)
    try:
        return genome_to_transcript(intervals, strand, position)
    except IndexError:
        if position < min(start for start, _end in intervals) or position > max(end for _start, end in intervals):
            raise
        ordered = sorted(intervals, reverse=(strand == "-"))
        upstream = 0
        for start, end in ordered:
            if (strand == "+" and position < start) or (strand == "-" and position > end):
                return upstream
            upstream += end - start + 1
        return upstream

def first_overlap_in_cds_order(cds_segments: List[Tuple[int,int,int]], strand: str) -> Optional[int]:
    """Return the genomic coordinate of the first overlap position in transcript order.
    For '+' strand this is the start coordinate of the first CDS segment; for '-' strand it's the end coordinate of the first CDS segment in transcript order.
    Returns None if `cds_segments` is empty.
    """
    if not cds_segments:
        return None
    cds_sorted = sorted(cds_segments, key=lambda x: x[0])
    if strand == '+':
        s, e, f = cds_sorted[0]
        return s
    else:
        s, e, f = cds_sorted[-1]
        return e

# --------------------------- TRANSLATION ---------------------------
def translate_consequence_aware(
    cds_seq: str,
    consequence: Dict,
    pad: bool = False,
    annotated_start_offset: Optional[int] = None,
    allow_alt_start: bool = False,
    allow_longest_orf: bool = False,
    min_alt_orf_aa: int = 30,
    alternative_start_codons: Tuple[str, ...] = ("ATG",),
    min_alt_start_kozak_strength: str = "weak",
    translation_table: int = 1,
    force_annotated_start_methionine: bool = False,
) -> Tuple[Optional[str], str, str]:
    """Translate an altered CDS using splice consequence information.

    The default behaviour is conservative and biologically interpretable:
    annotated CDS-derived sequence is translated in its reconstructed frame and
    stopped at the first in-frame stop codon. Longest-ORF rescue is only used
    when explicitly allowed and only after canonical/alternative-start routes fail.

    Returns
    -------
    (protein_sequence, translation_strategy, translation_note)
    """
    if not cds_seq:
        return None, "not_translated", "empty_cds_sequence"

    seq = (cds_seq or "").upper().replace("U", "T")
    region = consequence.get("region_class") if consequence else None
    start_loss = bool(consequence.get("start_loss")) if consequence else False

    # Use the annotated CDS start whenever it is retained in the altered CDS.
    # This avoids selecting arbitrary downstream ATGs or longest ORFs when the
    # biologically annotated start codon is still present.
    if annotated_start_offset is not None and annotated_start_offset >= 0:
        if annotated_start_offset < len(seq):
            prot = _translate_until_first_stop(
                seq[annotated_start_offset:], pad=pad, table=translation_table,
                force_initial_methionine=force_annotated_start_methionine,
            )
            if prot:
                return prot, "annotated_cds", "translated_from_retained_annotated_start"
        return None, "not_translated", "annotated_start_offset_out_of_range"

    # If the annotated start is lost, do not silently invent a protein. Only use
    # a downstream ATG when the user explicitly permits alternative initiation.
    if start_loss:
        if not allow_alt_start:
            return None, "not_translated", "start_lost_alt_start_not_allowed"

        atg = find_alternative_start(seq, alternative_start_codons, min_alt_start_kozak_strength)
        if atg is None:
            return None, "not_translated", "start_lost_no_downstream_atg"

        prot = _translate_until_first_stop(seq[atg:], pad=pad, table=translation_table)
        if prot:
            return prot, "alternative_start", f"{ALT_START_NOTE_PREFIX}{atg}"
        return None, "not_translated", "downstream_atg_no_valid_translation"

    # For in-frame events, frameshifts, premature stops and retained introns,
    # the altered CDS already encodes the relevant consequence. Translate in the
    # reconstructed frame until the first stop codon.
    if region not in {"no_cds_after_event", "noncoding_transcript", "utr_or_noncoding_event", "no_transcript_overlap"}:
        prot = _translate_until_first_stop(seq, pad=pad, table=translation_table)
        if prot:
            strategy = "canonical_frameshift_or_truncated" if consequence and (consequence.get("frameshift") or consequence.get("premature_stop")) else "canonical_cds"
            return prot, strategy, "translated_reconstructed_cds_to_first_stop"

    # Explicit exploratory rescue only. This should not be the default DIA FASTA
    # route because it can create biologically weak protein hypotheses.
    if allow_longest_orf:
        prot = longest_orf_from_sequence(
            seq, pad=pad, min_alt_orf_aa=min_alt_orf_aa, translation_table=translation_table,
        )
        if prot:
            return prot, "alternative_orf", "longest_orf_rescue_explicitly_allowed"

    return None, "not_translated", "no_valid_translation_strategy"

# --------------------------- CONSEQUENCE ANNOTATION ---------------------------
def genomic_pos_in_segments(pos, segments):
    if pos is None:
        return False
    try:
        p = int(pos)
    except (TypeError, ValueError):
        return False
    for s, e, *_rest in segments or []:
        if int(s) <= p <= int(e):
            return True
    return False


def classify_splice_consequence(tx_model, chain_exons, cds_segments, seq_nt_for_consequence, event_type, variant_name, trim=0, pad=False, protein_sequence=None, nmd_distance_threshold_nt=55):
    """Classify transcript-level coding consequences for an altered splice isoform.

    The intent is consequence-aware annotation, not a full VEP-like predictor.
    Frame, stop and NMD calls come from the caller-neutral
    ``evaluate_shared_splice_consequence`` so rMATS and SUPPA report the same
    definitions; ``consequence_class`` and ``ri_orf_preserved`` are derived from
    those reported values (see ``finalise_consequence_class``).
    """
    cds_list = tx_model.get('cds', []) or []
    strand = tx_model.get('strand')
    original_cds_len = interval_length(cds_list)
    altered_cds_len = interval_length(cds_segments)
    shared = evaluate_shared_splice_consequence(
        cds_segments, cds_list, strand, seq_nt_for_consequence, chain_exons,
        translation_start_offset_nt=trim,
        nmd_distance_threshold_nt=nmd_distance_threshold_nt,
        pad_partial_codons=pad,
    ).to_dict()

    if not cds_list:
        region_class = 'noncoding_transcript'
    elif not cds_segments:
        # Event may be UTR-only or remove all CDS from this transcript model.
        region_class = 'utr_or_noncoding_event' if chain_exons else 'no_transcript_overlap'
    elif altered_cds_len == 0:
        region_class = 'no_cds_after_event'
    elif altered_cds_len < original_cds_len:
        region_class = 'partial_cds_overlap'
    else:
        region_class = 'cds_overlap'

    canonical_start = canonical_start_genomic(cds_list, strand)
    start_retained = genomic_pos_in_segments(canonical_start, cds_segments)
    consequence = {
        'region_class': region_class,
        'canonical_start_genomic': canonical_start,
        'start_retained': start_retained,
        'start_loss': bool(cds_list and cds_segments and not start_retained),
        'ri_event': (str(event_type or '').upper() == 'RI'
                     or str(variant_name or '').lower() in _RETAINED_INTRON_VARIANTS),
        **shared,
    }
    return finalise_consequence_class(consequence, cds_segments, protein_sequence)


def finalise_consequence_class(consequence, cds_segments, protein_sequence):
    """Set ``ri_orf_preserved`` and ``consequence_class`` once the protein is known."""
    ri_event = consequence['ri_event']
    ri_orf_preserved = None
    if ri_event:
        ri_orf_preserved = bool(
            cds_segments and consequence.get('frame_status') == 'INFRAME'
            and not consequence.get('premature_stop') and protein_sequence
        )
    classes = [consequence['region_class']]
    if consequence.get('start_loss'):
        classes.append('start_lost')
    if consequence.get('frameshift'):
        classes.append('frameshift')
    elif consequence.get('frame_status') == 'INFRAME':
        classes.append('inframe')
    if consequence.get('premature_stop'):
        classes.append('premature_stop')
    if consequence.get('nmd_predicted'):
        classes.append('nmd_predicted')
    if ri_event:
        classes.append('ri_orf_preserved' if ri_orf_preserved else 'ri_orf_not_preserved')
    consequence['ri_orf_preserved'] = ri_orf_preserved
    consequence['consequence_class'] = ';'.join(classes)
    return consequence


# --------------------------- EVENT PROCESSING ---------------------------
# ---------------------------------------------------------------------------
# Per-isoform reconstruction for one rMATS event on one compatible transcript.
#
# _evaluate_rmats_variant_projections runs these steps for every projected
# isoform, in order:
#   1. _base_audit_row          identity, provenance and transcript-selection fields
#   2. _variant_cds             altered CDS sequence, or an audit row explaining why not
#   3. _resolve_frame_and_trim  annotated reading frame and leading-nucleotide trim
#   4. _annotated_start_offset  position of the annotated start codon in the altered CDS
#   5. _translate_variant       consequence-aware translation and consequence annotation
#   6. _fasta_decision          inclusion rules and output tier (the database policy)
#   7. _record_variant          audit row, protein mapping and junction peptides
# ---------------------------------------------------------------------------

class _VariantCds(NamedTuple):
    sequence: Optional[str]           # altered CDS nucleotides (untrimmed)
    segments: List[Tuple[int, int]]   # genomic CDS segments used for extraction
    coords: Optional[str]             # 'start-end;start-end' audit string
    excluded_row: Optional[Dict]      # audit row when the isoform stops here


class _VariantFrame(NamedTuple):
    first_overlap_position: int
    upstream_cds_nt: int
    trim: int
    sequence: str                     # CDS nucleotides after the frame trim
    trimmed: bool
    mismatch: bool


class _TranslatedVariant(NamedTuple):
    protein: Optional[str]
    strategy: str
    note: str
    alt_start: Optional[object]       # assess_alternative_start result, if any
    consequence: Dict


class _FastaDecision(NamedTuple):
    include: bool
    exclusion_reasons: str
    tier: str
    collector: Optional[str]          # 'primary', 'alternative_start', 'exploratory_orf' or None
    unique_peptide_count: int
    has_unique_peptide: Optional[bool]


def _base_audit_row(event_type, rowd, event_id, source_path, tx_model, args, var_name):
    """Step 1: fields shared by every audit row of this isoform."""
    return {
        'source_file': str(source_path),
        **event_file_provenance(source_path, args),
        'event_type': event_type,
        'event_id': event_id,
        'gene_id': tx_model.get('gene_id'),
        'gene_symbol': tx_model.get('gene_name'),
        'tx': tx_model.get('transcript_id'),
        'variant': var_name,
        'reconstruction_scope': 'local_event_projected_onto_annotation_model',
        'expression_evidence_status': 'candidate_not_sample_expression_proof',
        'transcript_selection_score': rowd.get('_transcript_selection_score'),
        'transcript_selection_rank': rowd.get('_transcript_selection_rank'),
        'transcript_candidate_count': rowd.get('_transcript_candidate_count'),
        'transcript_selection_ambiguous': rowd.get('_transcript_selection_ambiguous'),
        'transcript_tied_best_count': rowd.get('_transcript_tied_best_count'),
        'transcript_manual_review_required': bool(rowd.get('_transcript_selection_ambiguous')),
        **transcript_cds_audit_fields(tx_model),
        'ri_boundary_fallback': bool(
            event_type == 'RI'
            and (_row_int(rowd, ['upstreamEE']) is None
                 or _row_int(rowd, ['downstreamES']) is None)
        ),
    }


def _excluded_row(base_row, fields, protein, coords, reason):
    """Audit row for an isoform that never reaches translation."""
    return {
        **base_row,
        **fields,
        'protein_sequence': protein,
        'protein_length': len(protein) if protein else 0,
        'coords': coords,
        'protein_in_fasta': False,
        'fasta_exclusion_reasons': reason,
    }


def _extract(tx_model, segments, fa_index, args):
    """Transcript-oriented sequence for genomic segments, via the run-level cache when present."""
    sequence_cache = getattr(args, 'sequence_cache', None)
    if sequence_cache is not None:
        return sequence_cache.extract(tx_model['chrom'], segments, tx_model['strand'])
    return extract_sequence_from_indexed_genome(fa_index, tx_model['chrom'], segments, tx_model['strand'])


def _variant_cds(base_row, chain_exons, cds_segments, event_type, var_name, tx_model, fa_index, args):
    """Step 2: extract the altered CDS, or explain why the isoform cannot be translated."""
    if not cds_segments:
        consequence = classify_splice_consequence(
            tx_model, chain_exons, cds_segments, None, event_type, var_name,
            trim=0, pad=args.pad_partial_codons, protein_sequence=None,
            nmd_distance_threshold_nt=args.nmd_distance_threshold_nt,
        )
        return _VariantCds(None, [], None, _excluded_row(base_row, consequence, None, None, 'no_cds_overlap'))

    segments = [(s, e) for s, e, _ in cds_segments]
    coords = ';'.join(f'{s}-{e}' for s, e in segments)
    sequence = _extract(tx_model, segments, fa_index, args)
    if not sequence:
        return _VariantCds(None, segments, coords, _excluded_row(
            base_row, {'region_class': 'sequence_extraction_failed'}, None, coords,
            'sequence_extraction_failed'))

    canonical_sequence = _extract(tx_model, [(s, e) for s, e, _ in tx_model['cds']], fa_index, args)
    if not canonical_sequence:
        return _VariantCds(None, segments, coords, _excluded_row(
            base_row, {'region_class': 'canonical_sequence_extraction_failed'}, None, coords,
            'canonical_sequence_extraction_failed'))

    # Second transcript-explosion filter: the reconstructed altered
    # CDS must differ from the annotated canonical CDS sequence.
    if canonical_sequence == sequence:
        canonical_protein = translate_cds_for_model(
            canonical_sequence, tx_model, pad=args.pad_partial_codons
        )
        return _VariantCds(None, segments, coords, _excluded_row(
            base_row,
            {'region_class': 'cds_unchanged',
             'translation_strategy': 'annotated_reference_cds',
             'translation_note': 'opposite_isoform_reference_for_comparison',
             'database_output_tier': 'excluded'},
            canonical_protein, coords, 'cds_sequence_identical_to_canonical'))

    return _VariantCds(sequence, segments, coords, None)


def _resolve_frame_and_trim(tx_model, cds_segments, sequence, event_id):
    """Step 3: reading frame from the annotation; None when it cannot be resolved."""
    frame = resolve_variant_frame(
        tx_model['cds'], cds_segments, tx_model['strand'], first_overlap_in_cds_order,
        compute_upstream_cds_nt, cds_frame_at_genomic_position, normalize_phase_value,
    )
    if frame is None:
        return None
    if frame.mismatch:
        logging.warning(
            "Frame mismatch for %s (event %s): gtf_frame=%d inferred_frame=%d; using gtf_frame",
            tx_model.get("transcript_id"), event_id, frame.trim_nt, frame.inferred_frame,
        )
    trim = frame.trim_nt
    trimmed = bool(trim and len(sequence) > trim)
    return _VariantFrame(
        first_overlap_position=frame.first_overlap_position,
        upstream_cds_nt=frame.upstream_cds_nt,
        trim=trim,
        sequence=sequence[trim:] if trimmed else sequence,
        trimmed=trimmed,
        mismatch=frame.mismatch,
    )


def _annotated_start_offset(tx_model, cds_segments, frame):
    """Step 4: offset of the annotated start codon in the trimmed altered CDS, if it lies inside it."""
    cds_list = tx_model['cds']
    canonical_start = canonical_start_genomic(cds_list, tx_model['strand'])
    if canonical_start is None:
        return None
    canonical_upstream = compute_upstream_cds_nt(cds_list, canonical_start, tx_model['strand'])
    total_nt = sum((e - s + 1) for s, e, _ in cds_segments)
    if not (frame.upstream_cds_nt <= canonical_upstream < frame.upstream_cds_nt + total_nt):
        return None
    return canonical_upstream - frame.upstream_cds_nt - frame.trim


def _canonical_protein(tx_model, args, canonical_cache):
    """Annotated reference protein for this transcript (cached across events)."""
    pad_flag = args.pad_partial_codons

    def load_canonical_protein():
        canonical_raw = args.sequence_cache.extract(
            tx_model['chrom'], [(s, e) for s, e, _phase in tx_model['cds']], tx_model['strand']
        )
        return (
            translate_cds_for_model(canonical_raw, tx_model, pad=pad_flag)
            if canonical_raw else None
        )
    return canonical_cache.get_or_compute(tx_model["transcript_id"], load_canonical_protein)


def _translate_variant(frame, start_offset, chain_exons, cds_segments, event_type, var_name,
                       rowd, tx_model, args):
    """Step 5: translate with consequence awareness and annotate the biological consequence."""
    pad_flag = args.pad_partial_codons
    consequence_nt = mask_selenocysteine_stops_for_consequence(
        frame.sequence, tx_model, cds_segments=cds_segments
    )
    consequence = classify_splice_consequence(
        tx_model, chain_exons, cds_segments, consequence_nt, event_type, var_name,
        trim=frame.trim, pad=pad_flag, protein_sequence=None,
        nmd_distance_threshold_nt=args.nmd_distance_threshold_nt,
    )
    protein, strategy, note = translate_consequence_aware(
        cds_seq=frame.sequence,
        consequence=consequence,
        pad=pad_flag,
        annotated_start_offset=start_offset,
        allow_alt_start=args.allow_alt_start,
        allow_longest_orf=args.allow_longest_orf,
        min_alt_orf_aa=args.min_alt_orf_aa,
        alternative_start_codons=tuple(args.alternative_start_codons),
        min_alt_start_kozak_strength=args.min_alt_start_kozak_strength,
        translation_table=2 if is_mitochondrial_chromosome(tx_model.get("chrom")) else 1,
        force_annotated_start_methionine=bool(tx_model.get("non_atg_start")),
    )
    alt_start = alternative_start_from_note(frame.sequence, strategy, note)

    # Only ri_orf_preserved/consequence_class depend on the translated protein.
    finalise_consequence_class(consequence, cds_segments, protein)
    consequence.update({
        **transcript_cds_audit_fields(tx_model),
        "selenocysteine_reconstruction_supported": not bool(
            tx_model.get("selenocysteine_intervals")
        ),
        **alternative_start_fields(alt_start),
    })
    if event_type == "RI" and str(var_name).lower() in _RETAINED_INTRON_VARIANTS:
        consequence.update(retained_intron_evidence(
            tx_model, cds_segments, protein, frame.trim, rowd, args.sequence_cache, args
        ))
    return _TranslatedVariant(protein, strategy, note, alt_start, consequence)


def _fasta_decision(consequence, protein, strategy, canonical_protein, reference_peptides, args):
    """Step 6: database policy - does the protein enter a FASTA, and which tier?

    Order matters and mirrors the release policy:
      a. general DIA consequence filters (should_include_protein_in_fasta)
      b. retained-intron evidence rules (only when RI evidence was evaluated)
      c. no translatable ORF / identical to the annotated protein
      d. rescue products (alternative start, alternative ORF) bypass a-c, because they
         go to their own FASTA, unless identical to the annotated protein
      e. tier choice, then the optional reference-unique tryptic peptide requirement
      f. --include_failed_filter_proteins: a reconstructable, non-canonical protein
         that fails only policy filters (a, b, e) stays in the primary FASTA; the
         failed rules remain in fasta_exclusion_reasons (passed_dia_filters=False)
    """
    include, reasons = should_include_protein_in_fasta(consequence, args)
    if consequence.get("ri_read_evidence_supported") is not None:
        config = args.reconstruction_config
        if config.require_ri_read_evidence and consequence.get("ri_read_evidence_supported") is not True:
            include = False
            reasons = append_reason(reasons, "ri_without_required_read_evidence")
        if int(consequence.get("ri_ambiguous_base_count") or 0) > 0:
            include = False
            reasons = append_reason(reasons, "ri_contains_ambiguous_genomic_bases")
        if config.exclude_ri_nmd_from_primary and consequence.get("nmd_predicted") is True:
            include = False
            reasons = append_reason(reasons, "ri_nmd_predicted_excluded_from_primary")
        if config.require_ri_junction_peptide and consequence.get("ri_has_junction_spanning_searchable_peptide") is not True:
            include = False
            reasons = append_reason(reasons, "ri_no_junction_spanning_searchable_peptide")
    identical_to_canonical = bool(protein and canonical_protein and protein == canonical_protein)
    if not protein:
        include = False
        reasons = append_reason(reasons, 'no_translatable_orf')
    elif identical_to_canonical:
        include = False
        reasons = append_reason(reasons, 'protein_sequence_identical_to_canonical')
    keep_failed = bool(
        getattr(args, 'include_failed_filter_proteins', False) and protein and not identical_to_canonical
    )
    if keep_failed:
        include = True

    # Rescue products are isolated from the primary FASTA, so
    # primary-database consequence filters must not silently
    # prevent them from being audited in their dedicated FASTA.
    if protein and strategy in RESCUE_STRATEGIES:
        if not (canonical_protein and protein == canonical_protein):
            include = True
            reasons = ''

    unique_peptide_count = count_reference_unique_tryptic_peptides(
        protein,
        reference_peptides,
        max_missed_cleavages=args.max_missed_cleavages,
        min_len=args.min_database_peptide_length,
        max_len=args.max_database_peptide_length,
    ) if protein else 0
    has_unique_peptide = unique_peptide_count > 0 if reference_peptides is not None else None

    tier_decision = choose_output_tier(include, strategy)
    tier = tier_decision.tier
    collector = tier_decision.collector_name
    # FIX (2026-10-12): this gate previously compared the tier with "primary", but
    # choose_output_tier returns "primary_dia", so --require_unique_event_peptide never
    # removed proteins lacking a reference-unique tryptic peptide (SUPPA always did).
    if tier in {"primary", "primary_dia"} and args.require_unique_event_peptide and has_unique_peptide is not True:
        reasons = append_reason(reasons, 'no_reference_unique_tryptic_peptide')
        if not keep_failed:
            tier = "excluded"
            collector = None
            include = False
    return _FastaDecision(include, reasons, tier, collector, unique_peptide_count, has_unique_peptide)


def _protein_mapping_metadata(source_path, args, tx_model, event_type, event_id, var_name,
                              rowd, variant):
    """FASTA-header provenance for one retained protein."""
    alt_start = variant.alt_start
    return {
        "source_file": source_path.name,
        **event_file_provenance(source_path, args),
        "gene_id": tx_model.get("gene_id"),
        "gene_symbol": tx_model.get("gene_name"),
        "tx": tx_model.get("transcript_id"),
        "event_type": event_type,
        "event_id": event_id,
        "variant": var_name,
        "translation_strategy": variant.strategy,
        "translation_note": variant.note,
        "database_output_tier": None,  # filled by caller
        "transcript_selection_score": rowd.get('_transcript_selection_score'),
        "transcript_selection_rank": rowd.get('_transcript_selection_rank'),
        "transcript_candidate_count": rowd.get('_transcript_candidate_count'),
        "transcript_selection_ambiguous": rowd.get('_transcript_selection_ambiguous'),
        "transcript_tied_best_count": rowd.get('_transcript_tied_best_count'),
        "transcript_manual_review_required": bool(rowd.get('_transcript_selection_ambiguous')),
        "alt_start": "Yes" if variant.strategy == "alternative_start" else "No",
        "alt_start_codon": alt_start.codon if alt_start else None,
        "alt_start_kozak_strength": alt_start.kozak_strength if alt_start else None,
        "alt_start_kozak_score": alt_start.kozak_score if alt_start else None,
        "alt_start_kozak_context": alt_start.context_minus6_plus6 if alt_start else None,
    }


def _record_variant(base_row, cds, frame, variant, decision, cds_segments, collectors,
                    consequence_rows, junction_recs, source_path, rowd, tx_model, fa_index,
                    args, event_type, event_id, var_name):
    """Step 7: write the audit row and, for retained proteins, the FASTA mapping and junction peptides."""
    protein = variant.protein
    consequence_rows.append({
        **base_row,
        **variant.consequence,
        'coords': cds.coords,
        'first_overlap': frame.first_overlap_position,
        'trim': frame.trim,
        'trimmed': frame.trimmed,
        'pad_partial_codons': args.pad_partial_codons,
        'translation_strategy': variant.strategy,
        'translation_note': variant.note,
        'database_output_tier': decision.tier,
        'has_reference_unique_tryptic_peptide': decision.has_unique_peptide,
        'reference_unique_tryptic_peptide_count': decision.unique_peptide_count,
        'protein_sequence': protein,
        'protein_length': len(protein) if protein else 0,
        'protein_in_fasta': decision.include,
        'fasta_exclusion_reasons': decision.exclusion_reasons,
    })

    target = collectors.get(decision.collector)
    if not (decision.include and target is not None):
        return
    mapping = _protein_mapping_metadata(source_path, args, tx_model, event_type, event_id,
                                        var_name, rowd, variant)
    mapping["database_output_tier"] = decision.tier
    add_protein_mapping(target, protein, mapping)

    if args.short_junction_peptides:
        peptides = generate_codon_aware_junction_peptides(
            cds_segments=cds_segments,
            tx_model=tx_model,
            genome_index=fa_index,
            prot_id=f"{tx_model.get('transcript_id', 'NA')}|{var_name}",
            var_name=var_name,
            event_type=event_type,
            max_flank=args.junction_max_flank,
            min_flank=args.junction_min_flank,
            pad=args.pad_partial_codons,
            sequence_cache=getattr(args, 'sequence_cache', None),
        )
        # Tag each peptide with its audit row so peptides of proteins later removed
        # by finalise_primary_event_peptide_evidence can be dropped as well.
        row_key = _audit_row_key(consequence_rows[-1])
        for peptide in peptides:
            peptide.annotations[_ROW_KEY] = row_key
        junction_recs.extend(peptides)


_ROW_KEY = "pgdb_audit_row_key"


def _audit_row_key(row):
    return (str(row.get('source_file')), row.get('event_type'), row.get('event_id'),
            row.get('tx'), row.get('variant'))


def retained_junction_records(junction_recs, consequence_rows):
    """Keep junction peptides only for proteins that remain in a protein FASTA."""
    retained = {_audit_row_key(row) for row in consequence_rows if row.get('protein_in_fasta') is True}
    return [rec for rec in junction_recs if rec.annotations.get(_ROW_KEY) in retained]


def _evaluate_rmats_variant_projections(
    event_type, rowd, event_id, source_path, tx_model, fa_index, args,
    prot_info, alt_start_prot_info, exploratory_orf_prot_info,
    canonical_cache, junction_recs, consequence_rows, reference_peptides,
):
    """Translate and record every rMATS isoform for one compatible transcript."""
    collectors = {
        "primary": prot_info,
        "alternative_start": alt_start_prot_info,
        "exploratory_orf": exploratory_orf_prot_info,
    }
    chains = build_variant_chains_for_transcript(event_type, rowd, tx_model['exons'])
    for projection in project_event_variants(chains, tx_model['cds'], intersect_chain_with_cds):
        var_name = projection.variant
        chain_exons = list(projection.exon_chain)
        cds_segments = list(projection.cds_segments)

        base_row = _base_audit_row(event_type, rowd, event_id, source_path, tx_model, args, var_name)
        cds = _variant_cds(base_row, chain_exons, cds_segments, event_type, var_name,
                           tx_model, fa_index, args)
        if cds.excluded_row is not None:
            consequence_rows.append(cds.excluded_row)
            continue

        frame = _resolve_frame_and_trim(tx_model, cds_segments, cds.sequence, event_id)
        if frame is None:
            # FIX (2026-10-12): previously skipped without an audit row, so these
            # isoforms vanished from the consequence table without a reason.
            consequence_rows.append(_excluded_row(
                base_row, {'region_class': 'unresolved_reading_frame'}, None, cds.coords,
                'unresolved_reading_frame'))
            continue
        base_row['frame_mismatch'] = frame.mismatch

        start_offset = _annotated_start_offset(tx_model, cds_segments, frame)
        canonical_protein = _canonical_protein(tx_model, args, canonical_cache)
        variant = _translate_variant(frame, start_offset, chain_exons, cds_segments,
                                     event_type, var_name, rowd, tx_model, args)
        decision = _fasta_decision(variant.consequence, variant.protein, variant.strategy,
                                   canonical_protein, reference_peptides, args)
        _record_variant(base_row, cds, frame, variant, decision, cds_segments, collectors,
                        consequence_rows, junction_recs, source_path, rowd, tx_model, fa_index,
                        args, event_type, event_id, var_name)


def process_rmats_transcript_variants(
    event_type, rowd, event_id, source_path, tx_model, fa_index, policy,
    canonical_cache, reference_peptides,
) -> SpliceProteinResult:
    """Return reconstructed variants without mutating caller-owned collectors."""
    result = SpliceProteinResult()
    _evaluate_rmats_variant_projections(
        event_type, rowd, event_id, source_path, tx_model, fa_index, policy,
        result.proteins, result.alternative_start_proteins,
        result.exploratory_orf_proteins, canonical_cache,
        result.junction_records, result.consequence_rows, reference_peptides,
    )
    return result


def extract_rmats_gene_id(row: Dict) -> str:
    """Return the first populated rMATS gene identifier field."""
    for column in ("GeneID", "gene_id", "geneSymbol", "geneSymbol.1", "gene_id.1", "gene_id.0"):
        if column in row and pd.notna(row[column]):
            return str(row[column]).strip()
    return "NA"


def lookup_gene_transcripts(raw_gene: str, transcripts_lookup: Dict[str, List[str]]):
    """Resolve the first matching normalized gene key to transcript IDs."""
    candidates = generate_gene_id_candidates(raw_gene)
    for candidate in candidates:
        if candidate in transcripts_lookup:
            return transcripts_lookup[candidate], candidates
    return transcripts_lookup.get(raw_gene.replace(" ", ""), []), candidates


def rank_rmats_transcript_candidates(event_type, row, transcript_ids, transcripts, gene_id):
    """Resolve, coordinate-filter, and rank transcript models for one event."""
    event_intervals = rmats_event_intervals(event_type, row)
    compatible = []
    for transcript_id in transcript_ids:
        matched_id = match_transcript_id(transcript_id, transcripts)
        if not matched_id:
            logging.warning("Transcript resolution failed for %s (gene %s)", transcript_id, gene_id)
            continue
        model = transcripts[matched_id]
        if not transcript_is_event_compatible(event_type, row, model):
            continue
        if not event_overlaps_transcript_cds(event_type, row, model):
            continue
        overlap_nt = sum(
            max(0, min(event_end, cds_end) - max(event_start, cds_start) + 1)
            for event_start, event_end in event_intervals
            for cds_start, cds_end, _phase in model.get('cds', [])
        )
        compatible.append((overlap_nt, str(model.get('transcript_id') or matched_id), model))
    compatible.sort(key=lambda item: (-item[0], item[1]))
    top_score = compatible[0][0] if compatible else None
    tied_best = sum(item[0] == top_score for item in compatible) if compatible else 0
    return compatible, tied_best


def process_event_file(
    event_type: str,
    p: Path,
    transcripts: Dict[str, Dict],
    transcripts_lookup: Dict[str, List[str]],
    fa_index,
    args,
    prot_info: Dict[str, Dict],
    alt_start_prot_info: Dict[str, Dict],
    exploratory_orf_prot_info: Dict[str, Dict],
    canonical_cache: CanonicalProteinCache,
    junction_recs: List[SeqRecord],
    consequence_rows: List[Dict],
    event_summary_rows: List[Dict],
    reference_peptides: Optional[set],
):
    """Process a single rMATS event file and populate protein FASTA records plus consequence rows."""
    chunksize = int(getattr(args, "chunksize", 50000) or 50000)
    total = count_event_rows(p)

    logging.info("Loading rMATS %s events from %s%s", event_type, p, f" ({total} rows)" if total is not None else "")

    try:
        row_iter = pd.read_csv(p, sep="\t", comment="#", low_memory=False, chunksize=chunksize)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read rMATS {event_type} table {p}: {exc}") from exc
    progress = tqdm(total=total, desc=p.name)
    rid = 0
    for chunk_number, df_chunk in enumerate(row_iter):
        if chunk_number == 0:
            columns = set(df_chunk.columns)
            if not ({"GeneID", "geneSymbol", "gene_id"} & columns):
                raise ValueError(f"rMATS table {p} lacks a gene identifier column")
            if not ({"chr", "chrom", "Chromosome", "seqname"} & columns):
                raise ValueError(f"rMATS table {p} lacks a chromosome column")
        for rowd in df_chunk.to_dict(orient='records'):
            progress.update(1)
            event_summary_rows.append(_process_event_row(
                rowd, rid, event_type, p, transcripts, transcripts_lookup, fa_index, args,
                prot_info, alt_start_prot_info, exploratory_orf_prot_info, canonical_cache,
                junction_recs, consequence_rows, reference_peptides,
            ))
            rid += 1
    progress.close()


def _process_event_row(
    rowd, rid, event_type, p, transcripts, transcripts_lookup, fa_index, args,
    prot_info, alt_start_prot_info, exploratory_orf_prot_info, canonical_cache,
    junction_recs, consequence_rows, reference_peptides,
):
    """Filter, resolve and reconstruct one rMATS row; return its event-summary record."""
    event_id = rowd.get('ID') or rowd.get('Event') or rowd.get('event_id') or f'{p.name}:{rid}'
    keep_event, filter_record = evaluate_rmats_event(rowd, args)
    summary_record = {
        "source_file": str(p),
        **event_file_provenance(p, args),
        "event_type": event_type,
        "event_id": event_id,
        **filter_record,
    }
    if not keep_event:
        return finish_event_summary(
            summary_record, "filtered_before_reconstruction", 0, "not_reconstructed_filtered",
        )

    raw_gene = extract_rmats_gene_id(rowd)
    tx_list, cand_ids = lookup_gene_transcripts(raw_gene, transcripts_lookup)
    if not tx_list:
        logging.debug("No transcripts found in lookup for gene identifier candidates: %s", cand_ids)
        return finish_event_summary(
            summary_record, "no_gene_transcript_match", 0, "no_consequence_row_generated",
        )

    compatible_models, tied_best = rank_rmats_transcript_candidates(
        event_type, rowd, tx_list, transcripts, raw_gene
    )
    if tied_best > 1:
        logging.warning(
            "Ambiguous rMATS transcript assignment requires manual review: "
            "event=%s tied_best_count=%d candidates=%d",
            event_id, tied_best, len(compatible_models),
        )
    consequence_count_before = len(consequence_rows)
    for rank, (selection_score, _tx_name, tx_model) in enumerate(compatible_models, 1):
        ranked_row = {
            **rowd,
            '_transcript_selection_score': selection_score,
            '_transcript_selection_rank': rank,
            '_transcript_candidate_count': len(compatible_models),
            '_transcript_selection_ambiguous': tied_best > 1 and rank <= tied_best,
            '_transcript_tied_best_count': tied_best,
            '_ri_filter_record': filter_record,
        }
        variant_result = process_rmats_transcript_variants(
            event_type, ranked_row, event_id, p, tx_model, fa_index, args,
            canonical_cache, reference_peptides,
        )
        merge_protein_mappings(prot_info, variant_result.proteins)
        merge_protein_mappings(alt_start_prot_info, variant_result.alternative_start_proteins)
        merge_protein_mappings(exploratory_orf_prot_info, variant_result.exploratory_orf_proteins)
        junction_recs.extend(variant_result.junction_records)
        consequence_rows.extend(variant_result.consequence_rows)

    generated = len(consequence_rows) - consequence_count_before
    return finish_event_summary(
        summary_record,
        "processed_coordinate_compatible_transcripts" if generated else "no_compatible_transcript_reconstruction",
        generated,
        "reconstructed" if generated else "no_consequence_row_generated",
    )


# --------------------------- ARGUMENTS ---------------------------
def validate_args(args, parser):
    """Validate dependent CLI options and apply named policy presets."""
    try:
        require_files([args.gtf_db, args.genome], "critical reference")
        if args.reference_proteome:
            require_files(args.reference_proteome, "reference proteome")
    except FileNotFoundError as exc:
        parser.error(str(exc))
    args.alternative_start_codons, invalid_codons = normalise_start_codons(args.alternative_start_codons)
    if invalid_codons:
        parser.error(f"Invalid --alternative_start_codons: {', '.join(invalid_codons)}")
    if args.nmd_distance_threshold_nt < 0:
        parser.error("--nmd_distance_threshold_nt must be non-negative")
    if args.min_alt_orf_aa < 1:
        parser.error("--min_alt_orf_aa must be at least 1")
    if args.workers < 1 or args.sequence_cache_entries < 1:
        parser.error("--workers and --sequence_cache_entries must be at least 1")
    if args.short_junction_peptides and not args.out_junc_fa:
        parser.error("--out_junc_fa is required when --short_junction_peptides is set")
    if args.allow_alt_start and not args.out_alt_start_prot_fa:
        parser.error("--out_alt_start_prot_fa is required with --allow_alt_start")
    if args.allow_longest_orf and not args.out_exploratory_orf_fa:
        parser.error("--out_exploratory_orf_fa is required with --allow_longest_orf")
    if args.require_unique_event_peptide and not args.reference_proteome:
        parser.error("--require_unique_event_peptide requires --reference_proteome")
    if args.max_fdr is not None and not 0.0 <= args.max_fdr <= 1.0:
        parser.error("--max_fdr must be between 0 and 1")
    if (args.min_abs_inc_level_difference is not None
            and not 0.0 <= args.min_abs_inc_level_difference <= 1.0):
        parser.error("--min_abs_inc_level_difference must be between 0 and 1")
    for name in ("min_inclusion_junction_reads", "min_skipping_junction_reads"):
        if getattr(args, name) is not None and getattr(args, name) < 0:
            parser.error(f"--{name} must be non-negative")
    if args.min_ri_inclusion_reads < 1:
        parser.error("--min_ri_inclusion_reads must be at least 1")

    if args.quantms_conservative:
        if not args.reference_proteome:
            parser.error("--quantms_conservative requires --reference_proteome")
        args.require_unique_event_peptide = True
        args.exclude_nmd_from_dia = True
        args.exclude_start_loss_from_dia = True
        args.require_ri_orf_preserved = True

    if args.rmats_conservative_event_filter:
        defaults = {
            "max_fdr": 0.05,
            "min_abs_inc_level_difference": 0.10,
            "min_inclusion_junction_reads": 10,
            "min_skipping_junction_reads": 10,
        }
        for name, value in defaults.items():
            if getattr(args, name) is None:
                setattr(args, name, value)


def main(argv=None):
    args, parser = parse_rmats_args(argv)
    if args.event_metadata:
        args.event_metadata_lookup = json.loads(Path(args.event_metadata).read_text(encoding='utf-8'))

    configure_logging("INFO")

    validate_args(args, parser)
    preflight_producer_contract("rmats", args.annotation_release)
    # Inputs are fingerprinted now; the manifest is only published after success.
    manifest = prepare_run_manifest(args, args.out_prot_fa, Path(__file__).name)
    run(args)
    publish_run_manifest(manifest)
    return 0


def run(args):
    """Run rMATS reconstruction for parsed and validated ``args``."""
    args.reconstruction_policy = ReconstructionPolicy.from_namespace(args)
    args.reconstruction_config = SpliceReconstructionConfig(
        nmd_distance_threshold_nt=args.nmd_distance_threshold_nt,
        pad_partial_codons=args.pad_partial_codons,
        alternative_start_codons=tuple(args.alternative_start_codons),
        min_alt_start_kozak_strength=args.min_alt_start_kozak_strength,
        max_missed_cleavages=args.max_missed_cleavages,
        min_database_peptide_length=args.min_database_peptide_length,
        max_database_peptide_length=args.max_database_peptide_length,
        require_ri_read_evidence=args.require_ri_read_evidence,
        min_ri_inclusion_reads=args.min_ri_inclusion_reads,
        exclude_ri_nmd_from_primary=args.exclude_ri_nmd_from_primary,
        require_ri_junction_peptide=args.require_ri_junction_peptide,
    )
    event_files = normalise_event_file_lists(args)
    if not any(event_files.values()):
        raise FileNotFoundError("No rMATS event files matched the supplied patterns")

    logging.info("Loading prebuilt GTF database")
    transcripts = build_transcript_models(args.gtf_db)
    transcripts_lookup = build_transcripts_lookup(transcripts)
    logging.info("Transcript models loaded: %d", len(transcripts))

    logging.info("Loading genome via pyfaidx: %s", args.genome)
    fa_index = open_genome_index(args.genome)
    args.sequence_cache = GenomeSequenceCache(fa_index, args.sequence_cache_entries)

    prot_info: Dict[str, Dict] = {}
    alt_start_prot_info: Dict[str, Dict] = {}
    exploratory_orf_prot_info: Dict[str, Dict] = {}
    canonical_cache = CanonicalProteinCache()
    junction_recs: List[SeqRecord] = []
    consequence_rows: List[Dict] = []
    event_summary_rows: List[Dict] = []
    reference_peptides = load_reference_tryptic_peptides(
        args.reference_proteome,
        args.max_missed_cleavages,
        args.min_database_peptide_length,
        args.max_database_peptide_length,
        cache_path=args.reference_peptide_cache,
    )

    jobs = [(event_type, Path(path)) for event_type, files in event_files.items() for path in files if path]

    def reconstruct_file(job):
        event_type, path = job
        result = SpliceFileResult({}, {}, {}, [], [], [])
        process_event_file(
            event_type, path, transcripts, transcripts_lookup, fa_index, args,
            result.proteins, result.alternative_start_proteins, result.exploratory_orf_proteins,
            canonical_cache, result.junction_records, result.consequence_rows,
            result.summary_rows, reference_peptides,
        )
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(reconstruct_file, jobs):
            merge_protein_mappings(prot_info, result.proteins)
            merge_protein_mappings(alt_start_prot_info, result.alternative_start_proteins)
            merge_protein_mappings(exploratory_orf_prot_info, result.exploratory_orf_proteins)
            junction_recs.extend(result.junction_records)
            consequence_rows.extend(result.consequence_rows)
            event_summary_rows.extend(result.summary_rows)

    finalise_primary_event_peptide_evidence(consequence_rows, prot_info, args)

    consequence_tsv = args.out_consequence_tsv or (str(args.out_prot_fa) + ".consequences.tsv")
    write_consequence_tsv(consequence_rows, consequence_tsv, CONSEQUENCE_TSV_COLUMNS)
    event_summary_tsv = args.out_event_summary_tsv or (str(args.out_prot_fa) + ".event_summary.tsv")
    write_event_summary(event_summary_rows, event_summary_tsv)

    write_protein_fasta(prot_info, args.out_prot_fa, "rmats")
    if args.out_alt_start_prot_fa:
        write_protein_fasta(alt_start_prot_info, args.out_alt_start_prot_fa, "rmats")
    if args.out_exploratory_orf_fa:
        write_protein_fasta(exploratory_orf_prot_info, args.out_exploratory_orf_fa, "rmats")

    if args.short_junction_peptides:
        write_junction_fasta(retained_junction_records(junction_recs, consequence_rows), args.out_junc_fa)


if __name__ == "__main__":
    raise SystemExit(main())
