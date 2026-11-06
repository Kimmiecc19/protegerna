#!/usr/bin/env python3
"""
SUPPA -> typed protein candidates and peptide FASTA:
Parse SUPPA IOE event definitions to generate variant protein and junction peptide FASTA files.

Optional PSI matrices act only as an event-level inclusion filter. PSI values are
reported separately and are not embedded in consequence records, protein
mappings, junction peptides, or FASTA headers.
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from tqdm import tqdm

from proteogenomic.provenance import (
    batch_from_path, configure_logging, load_sample_metadata, require_files, sample_provenance,
)
from proteogenomic.splice_reconstruction_core import (
    CanonicalProteinCache, GenomeSequenceCache, TranscriptResolver, merge_protein_mappings,
    rank_compatible_transcripts, SpliceFileResult,
)
from glob import glob 
from proteogenomic.proteogenomic_models import GenomicInterval, SpliceCandidate, SpliceProteinResult
from proteogenomic.proteogenomic_policies import ReconstructionPolicy
from proteogenomic.splice_cli import parse_suppa_args
from proteogenomic.suppa_parsing import expand_file_patterns, normalise_event_id, parse_suppa_event_coords, split_list_field
from proteogenomic.suppa_psi import evaluate_psi_event, load_psi_files, write_psi_filter_summary
from proteogenomic.splice_annotation import build_transcript_models
from proteogenomic.release_validation import preflight_producer_contract
from proteogenomic.splice_consequence import evaluate_shared_splice_consequence

from proteogenomic.splice_translation import (
    CONSEQUENCE_TSV_COLUMNS, _translate_until_first_stop,
    add_protein_mapping,
    append_reason,
    cds_frame_at_genomic_position,
    canonical_start_genomic,
    count_reference_unique_tryptic_peptides,
    digest_tryptic_peptides,
    exon_junction_positions_from_exon_segments,
    extract_cds_sequence_for_model,
    extract_sequence_from_indexed_genome,
    first_stop_codon_aa,
    interval_length,
    load_reference_tryptic_peptides,
    match_transcript_id, merge_intervals, normalize_phase_value,
    nmd_prediction,
    open_genome_index,
    pad_to_codon,
    should_include_protein_in_fasta,
    trim_to_codon,
    write_consequence_tsv,
    write_junction_fasta,
    write_protein_fasta,
    transcript_cds_audit_fields, write_run_manifest,
    translate_cds_for_model,
    mask_selenocysteine_stops_for_consequence,
)


# --------------------------- HELPERS: INTERVALS AND OVERLAPS ---------------------------
# --------------------------- FASTA handling (pyfaidx) ---------------------------





# --------------------------- TRANSCRIPT ID RESOLUTION AND PARSE GTF---------------------------
# --------------------------- BUILD TRANSCRIPTS MODEL (gene -> transcripts) -----------
# --------------------------- SUPPA event parsing -----------









# --------------------------- TRIM/PAD ---------------------------


# --------------------------- TRANSLATION HELPERS ---------------------------



# --------------------------- CODON-AWARE SHORT JUNCTION PEPTIDE GENERATION ---------------------------
def generate_codon_aware_junction_peptides(
    cds_segments: List[Tuple[int, int, int]],
    tx_model: Dict,
    prot_id: str,
    var_name: str,
    event_type: str,
    genome_index,
    max_flank: int = 15,
    min_flank: int = 7,
    pad: bool = False,
    sequence_cache: Optional[GenomeSequenceCache] = None,
) -> List[SeqRecord]:
    """Generate codon-aware peptide windows around altered CDS junctions."""
    peptides = []
    strand = tx_model["strand"]
    chrom = tx_model["chrom"]

    ordered = sorted(cds_segments, key=lambda x: x[0], reverse=(strand == "-"))
    seg_lens = [e - s + 1 for (s, e, _) in ordered]
    total_nt = sum(seg_lens)
    if total_nt <= 0 or len(ordered) < 2:
        return peptides

    transcript_seg_map = []
    cur = 0
    for (s, e, _frame), length in zip(ordered, seg_lens):
        transcript_seg_map.append((cur, cur + length - 1, s, e))
        cur += length

    junction_nt_positions = [transcript_seg_map[i][0] for i in range(1, len(transcript_seg_map))]

    def map_window(win_s: int, win_e: int) -> List[Tuple[int, int]]:
        """Map a transcript-relative half-open window to genomic intervals."""
        out: List[Tuple[int, int]] = []
        for t_s, t_e, g_s, g_e in transcript_seg_map:
            if win_e <= t_s or win_s > t_e:
                continue
            ov_s = max(win_s, t_s)
            ov_e = min(win_e - 1, t_e)
            off_s = ov_s - t_s
            off_e = ov_e - t_s
            if strand == "+":
                gs = g_s + off_s
                ge = g_s + off_e
            else:
                # Transcript order on the negative strand runs from high to low
                # genomic coordinates. Convert offsets from the segment end.
                gs = g_e - off_e
                ge = g_e - off_s
            if gs > ge:
                gs, ge = ge, gs
            out.append((gs, ge))
        return out

    for j_nt in junction_nt_positions:
        win_s = max(0, j_nt - max_flank * 3)
        win_e = min(total_nt, j_nt + max_flank * 3)
        if win_s % 3 != 0:
            win_s += 3 - (win_s % 3)
            if win_s >= win_e:
                continue

        aa_len = (win_e - win_s) // 3
        if aa_len < (min_flank * 2):
            need = (min_flank * 2) * 3 - (win_e - win_s)
            # Extend toward the 5' side first so a junction near the CDS 3' end
            # is not discarded merely because rightward space is exhausted.
            left_extra = min(win_s, need)
            left_extra -= left_extra % 3
            win_s -= left_extra
            need -= left_extra
            right_extra = min(total_nt - win_e, need)
            win_e = min(total_nt, win_e + right_extra)
            aa_len = (win_e - win_s) // 3
            if aa_len < (min_flank * 2):
                continue

        segments = map_window(win_s, win_e)
        if not segments:
            continue

        nt = (
            sequence_cache.extract(chrom, segments, strand)
            if sequence_cache is not None
            else extract_sequence_from_indexed_genome(genome_index, chrom, segments, strand)
        )
        if not nt:
            continue

        seq_for = pad_to_codon(nt) if pad else trim_to_codon(nt)
        prot = str(Seq(seq_for).translate(to_stop=False)).split("*", 1)[0]
        if len(prot) < (min_flank * 2):
            continue

        coords = ";".join(f"{s}-{e}" for s, e in segments)
        header = (
            f"{prot_id}|var={var_name}|gene_id={tx_model.get('gene_id', 'NA')}"
            f"|tx={tx_model.get('transcript_id', 'NA')}|gene_symbol={tx_model.get('gene_name', 'NA')}"
            f"|event={event_type}|junction_nt={j_nt}|window_nt={win_s}-{win_e - 1}"
            f"|coords={coords}|pep_len={len(prot)}|flank_aa={max_flank}"
        )
        peptides.append(SeqRecord(Seq(prot), id=header, description=""))

    return peptides


# --------------------------- CONSEQUENCE ANNOTATION HELPERS ---------------------------














# --------------------------- EVENT PROCESSING ---------------------------
def _resolved_transcript_models(tx_ids, transcripts, resolver=None):
    """Return unique resolved transcript models while preserving IOE order."""
    resolved = []
    seen = set()
    missing = []
    for requested_id in tx_ids:
        resolution = resolver.resolve(requested_id) if resolver else None
        matched = resolution.matched_id if resolution else match_transcript_id(requested_id, transcripts)
        if not matched:
            missing.append(requested_id)
            continue
        model = transcripts[matched]
        stable_id = model.get("transcript_id") or matched
        stable_base = stable_id.split(".", 1)[0]
        if stable_base in seen:
            continue
        seen.add(stable_base)
        resolved.append(model)
    return resolved, missing


def _closest_opposite_transcript(tx_model, opposite_models):
    """Choose and score the biologically closest opposite-group transcript."""
    return rank_compatible_transcripts(tx_model, opposite_models)


def _annotated_cds_sequence(tx_model, fa_index, sequence_cache=None):
    """Extract a complete annotated CDS and apply only its leading GTF phase.

    The phase aligns the first retained CDS feature to a codon boundary.  It is
    translation metadata, not evidence that the splice event is frameshifting.
    """
    cds = tx_model.get("cds") or []
    raw = (
        sequence_cache.extract(
            tx_model.get("chrom"), [(x[0], x[1]) for x in cds], tx_model.get("strand")
        )
        if sequence_cache and cds else extract_cds_sequence_for_model(tx_model, fa_index)
    )
    if not raw or not cds:
        return raw, 0
    first = sorted(cds, key=lambda x: x[0], reverse=tx_model.get("strand") == "-")[0]
    phase = normalize_phase_value(first[2]) or 0
    return (raw[phase:] if phase < len(raw) else ""), phase


def _comparison_consequence(tx_model, reference_model, cds_seq, event_type, variant, protein, nmd_distance_threshold_nt=55):
    """Classify an annotated isoform relative to its closest opposite IOE isoform."""
    cds = tx_model.get("cds") or []
    reference_cds = reference_model.get("cds") if reference_model else []
    altered_first = sorted(cds, key=lambda x: x[0], reverse=tx_model.get("strand") == "-")[0] if cds else None
    reference_first = (
        sorted(reference_cds, key=lambda x: x[0], reverse=reference_model.get("strand") == "-")[0]
        if reference_model and reference_cds else None
    )
    altered_phase = normalize_phase_value(altered_first[2]) or 0 if altered_first else 0
    reference_phase = normalize_phase_value(reference_first[2]) or 0 if reference_first else 0
    altered_len = interval_length(cds) - altered_phase
    reference_len = interval_length(reference_cds) - reference_phase
    delta = altered_len - reference_len if reference_model and cds and reference_cds else None
    phase_mismatch = False
    if delta is not None:
        strand = tx_model.get("strand")
        candidates = []
        for start, end, _phase in cds:
            for pos in (start, end):
                if any(rstart <= pos <= rend for rstart, rend, _ in reference_cds):
                    candidates.append(pos)
        phase_mismatch = any(
            cds_frame_at_genomic_position(cds, pos, strand)
            != cds_frame_at_genomic_position(reference_cds, pos, strand)
            for pos in candidates
        )
    frame_status = "NA" if delta is None else ("FRAMESHIFT" if phase_mismatch else "INFRAME")
    frameshift = None if delta is None else frame_status == "FRAMESHIFT"

    stop_aa, stop_nt, terminal_stop, _ = first_stop_codon_aa(cds_seq, start_nt=0, pad=False)
    premature_stop = bool(stop_aa is not None and terminal_stop is False)
    junctions = exon_junction_positions_from_exon_segments(
        tx_model.get("exons"), cds, tx_model.get("strand"),
        translation_start_offset_nt=altered_phase,
    )
    nmd_pred, nmd_reason, nearest_junc, nmd_dist = nmd_prediction(
        stop_nt if premature_stop else None, junctions, nmd_distance_threshold_nt
    )
    ri_event = str(event_type or "").upper() == "RI"
    ri_orf_preserved = None
    if ri_event:
        ri_orf_preserved = bool(frame_status == "INFRAME" and not premature_stop and protein)

    classes = ["annotated_cds"]
    if frameshift:
        classes.append("frameshift_relative_to_opposite_isoform")
    elif frame_status == "INFRAME":
        classes.append("inframe_relative_to_opposite_isoform")
    if premature_stop:
        classes.append("premature_stop")
    if nmd_pred:
        classes.append("nmd_predicted")
    if ri_event:
        classes.append("ri_orf_preserved" if ri_orf_preserved else "ri_orf_not_preserved")

    shared = evaluate_shared_splice_consequence(
        cds, reference_cds if reference_model else None,
        tx_model.get("strand"), cds_seq, tx_model.get("exons") or [],
        translation_start_offset_nt=altered_phase,
        nmd_distance_threshold_nt=nmd_distance_threshold_nt,
    ).to_dict()
    return {
        "region_class": "annotated_cds",
        "original_cds_len": reference_len if reference_model else None,
        "altered_cds_len": altered_len,
        "cds_delta_nt": delta,
        "frame_comparison_transcript": reference_model.get("transcript_id") if reference_model else None,
        "frame_comparison_basis": "codon_phase_at_shared_genomic_positions" if reference_model else "no_opposite_isoform",
        "canonical_start_genomic": canonical_start_genomic(cds, tx_model.get("strand")),
        "start_retained_relative_to_own_annotation": True if cds else None,
        "start_loss_relative_to_own_annotation": False if cds else None,
        "frame_status": frame_status,
        "frameshift": frameshift,
        "premature_stop": premature_stop,
        "terminal_stop": terminal_stop,
        "first_stop_aa": stop_aa,
        "first_stop_nt_1based": stop_nt,
        "nmd_predicted": nmd_pred,
        "nmd_reason": nmd_reason,
        "nearest_downstream_exon_junction_nt": nearest_junc,
        "nmd_distance_nt": nmd_dist,
        "ri_event": ri_event,
        "ri_orf_preserved": ri_orf_preserved,
        "consequence_class": ";".join(classes),
        **shared,
    }


def _collect_suppa_row(
    rowd: Dict, rid: int, event_type: str, source_path: Path,
    transcripts: Dict[str, Dict], fa_index, args, prot_info,
    canonical_cache: CanonicalProteinCache, junction_recs,
    consequence_rows, reference_peptides=None,
) -> None:
    """Translate the complete annotated transcripts assigned to one SUPPA event.

    IOE transcript membership is authoritative.  Each transcript is processed
    independently; exons from different transcripts are never unioned and no
    incomplete synthetic CDS is passed to the primary database.
    """
    event_id = normalise_event_id(rowd.get("event_id") or rowd.get("event")) or f"{source_path.name}:{rid}"
    provenance = {
        "sample_id": rowd.get("sample_id", "NA"),
        "batch": rowd.get("batch", batch_from_path(source_path)),
        "condition": rowd.get("condition", "NA"),
        "organism": args.organism,
        "annotation_release": args.annotation_release,
    }
    parsed = parse_suppa_event_coords(event_id)
    parsed_event_type = parsed["etype"] if parsed else event_type
    alt_ids = split_list_field(rowd.get("alternative_transcripts"))
    total_ids = split_list_field(rowd.get("total_transcripts"))
    alt_bases = {tx.split(".", 1)[0] for tx in alt_ids}
    ref_ids = [tx for tx in total_ids if tx.split(".", 1)[0] not in alt_bases]

    resolver = getattr(args, "transcript_resolver", None)
    alt_models, missing_alt = _resolved_transcript_models(alt_ids, transcripts, resolver)
    ref_models, missing_ref = _resolved_transcript_models(ref_ids, transcripts, resolver)
    candidates = [("alternative", model, ref_models) for model in alt_models]
    candidates.extend(("reference", model, alt_models) for model in ref_models)

    if not candidates:
        consequence_rows.append({
            "source_file": str(source_path), "event_type": parsed_event_type,
            "event_id": event_id, "variant": "unresolved_event",
            "event_processing_status": "no_transcript_match",
            "requested_alternative_transcripts": ",".join(alt_ids),
            "requested_reference_transcripts": ",".join(ref_ids),
            "unresolved_transcripts": ",".join(missing_alt + missing_ref),
            "database_output_tier": "excluded", "protein_in_fasta": False,
            "fasta_exclusion_reasons": "no_transcript_match",
        })
        return

    for membership, txm, opposite_models in candidates:
        tx_id = txm.get("transcript_id")
        base_row = {
            "source_file": str(source_path), "event_type": parsed_event_type,
            "event_id": event_id, "gene_id": txm.get("gene_id"),
            "gene_symbol": txm.get("gene_name"), "tx": tx_id,
            "variant": membership, "ioe_transcript_group": membership,
            "reconstruction_scope": "annotated_event_transcript_candidate",
            "expression_evidence_status": "candidate_not_sample_expression_proof",
            "event_processing_status": "processed_annotated_transcript",
            "unresolved_transcripts": ",".join(missing_alt + missing_ref),
            **transcript_cds_audit_fields(txm),
            **provenance,
        }
        cds = txm.get("cds") or []
        if not cds:
            consequence_rows.append({
                **base_row, "region_class": "noncoding_transcript",
                "translation_strategy": "not_translated",
                "translation_note": "transcript_has_no_annotated_cds",
                "database_output_tier": "excluded", "protein_sequence": None,
                "protein_length": 0, "protein_in_fasta": False,
                "fasta_exclusion_reasons": "no_annotated_cds",
            })
            continue

        cds_seq, phase_trim = _annotated_cds_sequence(txm, fa_index, getattr(args, "sequence_cache", None))
        if not cds_seq:
            consequence_rows.append({
                **base_row, "region_class": "sequence_extraction_failed",
                "translation_strategy": "not_translated",
                "translation_note": "annotated_cds_sequence_extraction_failed",
                "database_output_tier": "excluded", "protein_sequence": None,
                "protein_length": 0, "protein_in_fasta": False,
                "fasta_exclusion_reasons": "sequence_extraction_failed",
            })
            continue

        protein = translate_cds_for_model(cds_seq, txm, pad=args.pad_partial_codons)
        opposite, opposite_ranking = _closest_opposite_transcript(txm, opposite_models)
        consequence = _comparison_consequence(
            txm, opposite, mask_selenocysteine_stops_for_consequence(cds_seq, txm),
            parsed_event_type, membership, protein,
            args.nmd_distance_threshold_nt,
        )
        consequence.update({
            **transcript_cds_audit_fields(txm),
            "selenocysteine_reconstruction_supported": True,
            "transcript_selection_score": opposite_ranking.score,
            "transcript_selection_rank": opposite_ranking.rank,
            "transcript_candidate_count": opposite_ranking.candidate_count,
            "transcript_selection_ambiguous": opposite_ranking.ambiguous,
            "transcript_tied_best_count": opposite_ranking.tied_best_count,
            "transcript_selection_reason": opposite_ranking.reason,
            "transcript_manual_review_required": opposite_ranking.ambiguous,
            "compatible_transcripts": opposite_ranking.candidate_count,
            **{f"transcript_rank_{i + 1}": tx for i, tx in enumerate(opposite_ranking.top_candidates)},
            "transcript_selection_path": opposite_ranking.selection_path,
        })
        if opposite_ranking.ambiguous:
            logging.warning(
                "Ambiguous SUPPA opposite-transcript assignment requires manual review: "
                "event=%s transcript=%s tied_best_count=%d",
                event_id, txm.get("transcript_id"), opposite_ranking.tied_best_count,
            )
        include, reasons = should_include_protein_in_fasta(consequence, args)
        if not protein:
            include = False
            reasons = append_reason(reasons, "no_translatable_orf")

        opposite_protein = None
        if opposite:
            opposite_key = opposite.get("transcript_id")
            def load_opposite_protein():
                opposite_seq, _ = _annotated_cds_sequence(opposite, fa_index, getattr(args, "sequence_cache", None))
                return translate_cds_for_model(
                    opposite_seq, opposite, pad=args.pad_partial_codons
                ) if opposite_seq else None
            opposite_protein = canonical_cache.get_or_compute(opposite_key, load_opposite_protein)
        if protein and opposite_protein and protein == opposite_protein:
            include = False
            reasons = append_reason(reasons, "protein_sequence_identical_to_opposite_isoform")

        event_unique_count = 0
        if protein and opposite_protein:
            candidate_peptides = digest_tryptic_peptides(
                protein, args.max_missed_cleavages,
                args.min_database_peptide_length, args.max_database_peptide_length,
            )
            opposite_peptides = digest_tryptic_peptides(
                opposite_protein, args.max_missed_cleavages,
                args.min_database_peptide_length, args.max_database_peptide_length,
            )
            event_unique_count = len(candidate_peptides - opposite_peptides)
        has_event_unique = event_unique_count > 0 if opposite_protein else None

        unique_count = count_reference_unique_tryptic_peptides(
            protein, reference_peptides,
            max_missed_cleavages=args.max_missed_cleavages,
            min_len=args.min_database_peptide_length,
            max_len=args.max_database_peptide_length,
        ) if protein else 0
        has_unique = unique_count > 0 if reference_peptides is not None else None
        if include and args.require_unique_event_peptide:
            if has_event_unique is not True:
                include = False
                reasons = append_reason(reasons, "no_opposite_isoform_unique_tryptic_peptide")
            if has_unique is not True:
                include = False
                reasons = append_reason(reasons, "no_reference_unique_tryptic_peptide")

        tier = "primary_dia" if include else "excluded"
        consequence_rows.append({
            **base_row, **consequence,
            "coords": ";".join(f"{s}-{e}" for s, e, _ in cds),
            "first_overlap": canonical_start_genomic(cds, txm.get("strand")),
            "trim": phase_trim, "trimmed": bool(phase_trim),
            "pad_partial_codons": args.pad_partial_codons,
            "translation_strategy": "annotated_cds" if protein else "not_translated",
            "translation_note": "complete_ioe_transcript_annotated_cds",
            "database_output_tier": tier,
            "has_reference_unique_tryptic_peptide": has_unique,
            "reference_unique_tryptic_peptide_count": unique_count,
            "has_opposite_isoform_unique_tryptic_peptide": has_event_unique,
            "opposite_isoform_unique_tryptic_peptide_count": event_unique_count,
            "protein_sequence": protein, "protein_length": len(protein) if protein else 0,
            "protein_in_fasta": include, "fasta_exclusion_reasons": reasons,
        })
        if include:
            add_protein_mapping(prot_info, protein, {
                "source_file": source_path.name, "gene_id": txm.get("gene_id"),
                "gene_symbol": txm.get("gene_name"), "tx": tx_id,
                "event_type": parsed_event_type, "event_id": event_id,
                "source_event_id": event_id,
                "psi_min_threshold": args.min_psi,
                "psi_min_samples": args.min_psi_samples,
                "variant": membership, "translation_strategy": "annotated_cds",
                "translation_note": "complete_ioe_transcript_annotated_cds",
                "database_output_tier": tier,
                "transcript_selection_score": opposite_ranking.score,
                "transcript_selection_rank": opposite_ranking.rank,
                "transcript_candidate_count": opposite_ranking.candidate_count,
                "transcript_selection_ambiguous": opposite_ranking.ambiguous,
                **provenance,
            })
            if args.short_junction_peptides:
                junction_recs.extend(generate_codon_aware_junction_peptides(
                    cds_segments=cds, tx_model=txm, genome_index=fa_index,
                    prot_id=f"{tx_id}|{membership}", var_name=membership,
                    event_type=parsed_event_type, max_flank=args.junction_max_flank,
                    min_flank=args.junction_min_flank, pad=args.pad_partial_codons,
                    sequence_cache=getattr(args, "sequence_cache", None),
                ))


def process_suppa_row(
    rowd: Dict, rid: int, event_type: str, source_path: Path,
    transcripts: Dict[str, Dict], fa_index, args,
    canonical_cache: CanonicalProteinCache, reference_peptides=None,
) -> SpliceProteinResult:
    """Return all products for one SUPPA row without mutating caller state."""
    result = SpliceProteinResult()
    _collect_suppa_row(
        rowd, rid, event_type, source_path, transcripts, fa_index, args,
        result.proteins, canonical_cache, result.junction_records,
        result.consequence_rows, reference_peptides,
    )
    event_id = normalise_event_id(rowd.get("event_id") or rowd.get("event")) or f"{source_path.name}:{rid}"
    for row in result.consequence_rows:
        transcript = transcripts.get(str(row.get("tx")), {})
        result.candidates.append(SpliceCandidate(
            Path(source_path), str(event_type), str(event_id),
            str(row.get("variant") or "unknown"), transcript,
            tuple(GenomicInterval(int(start), int(end)) for start, end in transcript.get("exons", [])),
        ))
    return result


def process_event_file(
    event_type,
    p: Path,
    transcripts,
    fa_index,
    args,
    prot_info,
    canonical_cache,
    junction_recs,
    consequence_rows,
    psi_lookup: Optional[Dict[str, Dict]],
    psi_filter_rows: List[Dict],
    reference_peptides,
):
    """Filter IOE events by PSI, then reconstruct proteins from approved events.

    PSI statistics are retained in the event-level filter summary rather than
    embedded as per-sample FASTA metadata.
    """
    row_count = 0
    passed_count = 0
    logging.info("Loading SUPPA events from %s", p)
    try:
        chunk_iter = pd.read_csv(p, sep="\t", header=0, dtype=str, chunksize=50000)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise ValueError(f"Could not read SUPPA event table {p}: {exc}") from exc
    for chunk_number, chunk in enumerate(chunk_iter):
        if chunk_number == 0:
            columns = set(chunk.columns)
            if not ({"event_id", "event"} & columns):
                raise ValueError(f"SUPPA table {p} lacks event_id/event column")
            missing = {"alternative_transcripts", "total_transcripts"} - columns
            if missing:
                raise ValueError(f"SUPPA table {p} lacks required column(s): {', '.join(sorted(missing))}")
        records = chunk.to_dict(orient="records")
        for rowd in tqdm(records, total=len(records), desc=p.name):
            if not isinstance(rowd, dict):
                row_count += 1
                continue

            event_id = normalise_event_id(
                rowd.get("event_id") or rowd.get("event")
            ) or f"{p.name}:{row_count}"
            keep_event, psi_decision = evaluate_psi_event(
                event_id=event_id,
                psi_lookup=psi_lookup,
                min_psi=args.min_psi,
                min_samples=args.min_psi_samples,
                keep_events_missing_psi=args.keep_events_missing_psi,
            )
            stats = psi_lookup.get(event_id, {}) if psi_lookup else {}
            details = stats.get("sample_details", [])
            rowd["sample_id"] = ";".join(sorted({x["sample_id"] for x in details})) or "NA"
            rowd["batch"] = ";".join(sorted({x["batch"] for x in details})) or batch_from_path(p)
            rowd["condition"] = ";".join(sorted({x["condition"] for x in details})) or "NA"
            parsed = parse_suppa_event_coords(event_id)
            psi_record = {
                "source_file": str(p),
                "sample_id": rowd.get("sample_id", "NA"),
                "batch": rowd.get("batch", batch_from_path(p)),
                "condition": rowd.get("condition", "NA"),
                "event_type": parsed["etype"] if parsed else event_type,
                "event_id": event_id,
                **psi_decision,
            }
            psi_filter_rows.append(psi_record)
            if not keep_event:
                row_count += 1
                continue

            passed_count += 1
            consequence_count_before = len(consequence_rows)
            row_result = process_suppa_row(
                rowd=rowd,
                rid=row_count,
                event_type=event_type,
                source_path=p,
                transcripts=transcripts,
                fa_index=fa_index,
                args=args,
                canonical_cache=canonical_cache,
                reference_peptides=reference_peptides,
            )
            merge_protein_mappings(prot_info, row_result.proteins)
            junction_recs.extend(row_result.junction_records)
            consequence_rows.extend(row_result.consequence_rows)
            generated = len(consequence_rows) - consequence_count_before
            psi_record["consequence_rows_generated"] = generated
            psi_record["reconstruction_status"] = (
                "reconstructed" if generated > 0 else "no_consequence_row_generated"
            )
            row_count += 1

    logging.info(
        "Processed %d SUPPA events from %s (%d passed PSI filtering)",
        row_count,
        p,
        passed_count,
    )

















# --------------------------- FASTA WRITERS ---------------------------



# --------------------------- ARGUMENTS ---------------------------
def validate_args(args, parser):
    """Validate dependent CLI options and apply named policy presets."""
    try:
        require_files([args.gtf_db, args.genome], "critical reference")
        if args.reference_proteome:
            require_files([args.reference_proteome], "reference proteome")
        if args.sample_metadata:
            require_files([args.sample_metadata], "sample metadata")
    except FileNotFoundError as exc:
        parser.error(str(exc))
    if args.short_junction_peptides and not args.out_junc_fa:
        parser.error("--out_junc_fa is required when --short_junction_peptides is set")
    if not 0.0 <= args.min_psi <= 1.0:
        parser.error("--min_psi must be between 0 and 1")
    if args.min_psi_samples < 1:
        parser.error("--min_psi_samples must be at least 1")
    if args.nmd_distance_threshold_nt < 0:
        parser.error("--nmd_distance_threshold_nt must be non-negative")
    if args.workers < 1 or args.sequence_cache_entries < 1:
        parser.error("--workers and --sequence_cache_entries must be at least 1")
    if args.allow_alt_start and not args.out_alt_start_prot_fa:
        parser.error("--out_alt_start_prot_fa is required with --allow_alt_start")
    if args.allow_longest_orf and not args.out_exploratory_orf_fa:
        parser.error("--out_exploratory_orf_fa is required with --allow_longest_orf")
    if args.require_unique_event_peptide and not args.reference_proteome:
        parser.error("--require_unique_event_peptide requires --reference_proteome")
    if args.quantms_conservative:
        if not args.reference_proteome:
            parser.error("--quantms_conservative requires --reference_proteome")
        args.require_unique_event_peptide = True
        args.exclude_nmd_from_dia = True
        args.exclude_start_loss_from_dia = True
        args.require_ri_orf_preserved = True


def main(argv=None):
    args, parser = parse_suppa_args(argv)

    configure_logging("INFO")
    
    validate_args(args, parser)
    preflight_producer_contract("suppa", args.annotation_release)
    write_run_manifest(args, args.out_prot_fa, Path(__file__).name)
    run(args)

# --------------------------- MAIN LOGIC ---------------------------
def run(args):
    args.reconstruction_policy = ReconstructionPolicy.from_namespace(args)

    logging.info("Loading transcript models...")
    transcripts = build_transcript_models(args.gtf_db)
    args.transcript_resolver = TranscriptResolver(transcripts)

    logging.info("Opening genome...")
    fa_index = open_genome_index(args.genome)
    args.sequence_cache = GenomeSequenceCache(fa_index, args.sequence_cache_entries)

    prot_info = {}
    alt_start_prot_info = {}
    exploratory_orf_prot_info = {}
    canonical_cache = CanonicalProteinCache()
    junction_recs = []
    consequence_rows = []
    psi_filter_rows = []
    reference_peptides = load_reference_tryptic_peptides(
        args.reference_proteome,
        args.max_missed_cleavages,
        args.min_database_peptide_length,
        args.max_database_peptide_length,
        cache_path=args.reference_peptide_cache,
    )

    event_files = expand_file_patterns(args.event_files, "event")

    logging.info(
        "Found %d event files",
        len(event_files),
    )
    if not event_files:
        raise FileNotFoundError(
            "No SUPPA event files matched the supplied --event_files patterns"
        )

    psi_files = expand_file_patterns(args.psi_files, "PSI")
    if psi_files:
        logging.info(
            "Found %d PSI files",
            len(psi_files),
        )

    # ----------------------------------------------------
    # Load PSI lookup
    # ----------------------------------------------------
    sample_metadata = load_sample_metadata(args.sample_metadata)
    psi_lookup = load_psi_files(psi_files, sample_metadata) if psi_files else None

    if not psi_lookup:
        if psi_files:
            logging.warning(
                "PSI files were supplied, but no PSI events were loaded. "
                "PSI filtering will not be applied."
                )
        else:
            logging.info(
                "No PSI files supplied; all IOE events will be considered."
                )
        psi_lookup = None
    else:
        logging.info(
            "PSI filtering enabled: retain events with PSI >= %.4f "
            "in at least %d sample(s)",
            args.min_psi,
            args.min_psi_samples,
            )

    # ----------------------------------------------------
    # Process event files
    # ----------------------------------------------------
    def reconstruct_file(event_file):
        path = Path(event_file)
        local_proteins, local_junctions = {}, []
        local_consequences, local_psi = [], []
        process_event_file(
            event_type=path.stem, p=path, transcripts=transcripts,
            fa_index=fa_index, args=args, prot_info=local_proteins,
            canonical_cache=canonical_cache, junction_recs=local_junctions,
            consequence_rows=local_consequences, psi_lookup=psi_lookup,
            psi_filter_rows=local_psi, reference_peptides=reference_peptides,
        )
        return SpliceFileResult(
            local_proteins, {}, {}, local_junctions, local_consequences, local_psi
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(reconstruct_file, event_files):
            merge_protein_mappings(prot_info, result.proteins)
            junction_recs.extend(result.junction_records)
            consequence_rows.extend(result.consequence_rows)
            psi_filter_rows.extend(result.summary_rows)

    # ----------------------------------------------------
    # Write outputs
    # ----------------------------------------------------
    if psi_files:
        psi_summary = (
            args.out_psi_summary_tsv
            or f"{args.out_prot_fa}.psi_filter.tsv"
        )
        write_psi_filter_summary(
            psi_filter_rows,
            psi_summary,
        )

    consequence_tsv = (
        args.out_consequence_tsv
        or f"{args.out_prot_fa}.consequences.tsv"
    )

    write_consequence_tsv(
        consequence_rows,
        consequence_tsv,
        CONSEQUENCE_TSV_COLUMNS,
    )

    write_protein_fasta(
        prot_info,
        args.out_prot_fa,
        "suppa",
    )
    if args.out_alt_start_prot_fa:
        write_protein_fasta(alt_start_prot_info, args.out_alt_start_prot_fa, "suppa")
    if args.out_exploratory_orf_fa:
        write_protein_fasta(exploratory_orf_prot_info, args.out_exploratory_orf_fa, "suppa")

    if args.short_junction_peptides:
        write_junction_fasta(
            junction_recs,
            args.out_junc_fa,
        )

if __name__ == "__main__":
    main()        
