"""Biological evaluation of fusion transcript-pair candidates."""
from __future__ import annotations
import logging, re
from functools import partial
from typing import Any
from Bio.Seq import Seq
from .fusion_models import (
    CandidatePairRequest, FusionFilterConfig, FusionMetadata, RankingRecordRequest,
    PartnerLookupContext, PartnerRequest, ReferenceContext,
    TranscriptCandidate,
)
from .fusion_coordinates import (
    extract_sequence_from_segments, intersect_tx_segments, nearest_breakpoint_boundary,
    resolve_breakpoint_on_exon_chain, model_nmd_status,
    update_breakpoint_metadata, update_frame_and_stop_metadata,
    update_junction_metadata,
)
from .fusion_transcripts import collect_transcript_cds_candidates
from .fusion_values import (
    normalize_chrom_token, normalize_gene_id, normalize_text_or_none,
    normalize_transcript_id, parse_bool_or_none, parse_int_or_none,
    sequence_hash,
)
from .fusion_filtering import evaluate_junction_peptides
from .fusion_reconstruction import ReconstructionOperations, create_fusion_cds as reconstruct_fusion_cds
from .provenance import sample_provenance
LOGGER=logging.getLogger(__name__); logger=LOGGER

def classify_frame_annotation(value):
    """Classify caller frame annotations to INFRAME/FRAMESHIFT/NA."""
    text = normalize_text_or_none(value)
    if not text:
        return "NA"

    token = text.lower().replace("_", "-").replace(" ", "")
    if "in-frame" in token or "inframe" in token:
        return "INFRAME"
    if "frameshift" in token or "out-of-frame" in token or "outofframe" in token:
        return "FRAMESHIFT"
    return "NA"

def classify_caller_concordance(
    reconstructed_protein, caller_peptide, frame_status, caller_frame_annotation,
    caller_fusion_cds=None,
):
    """Classify protein, junction-peptide, or frame agreement with caller output."""
    recon = normalize_text_or_none(reconstructed_protein, peptide=True)
    caller = normalize_text_or_none(caller_peptide, peptide=True)
    caller_cds = normalize_text_or_none(caller_fusion_cds)
    caller_protein = None
    if caller_cds:
        normalized_cds = re.sub(
            r"[^ACGTN]", "", caller_cds.upper().replace("U", "T")
        )
        caller_protein = translate_fusion(normalized_cds) if normalized_cds else None
    caller_frame = classify_frame_annotation(caller_frame_annotation)
    frame_state = frame_status if frame_status in {"INFRAME", "FRAMESHIFT"} else "NA"
    frame_agree = (
        frame_state != "NA" and caller_frame != "NA" and frame_state == caller_frame
    )

    if recon and caller_protein and recon == caller_protein:
        return "identical_protein"

    if recon and caller and caller in recon:
        return "same_junction_peptide"

    if frame_agree:
        return "frame_agreement"

    if caller or caller_protein or caller_frame != "NA":
        return "discordant_sequence"

    return "no_caller_reference"

def create_fusion_cds(
    genome, donor: TranscriptCandidate, acceptor: TranscriptCandidate,
    breakpoint1, breakpoint2, early_stop_aa_cutoff=30,
):
    """Delegate fusion CDS construction to the reconstruction module."""
    operations = ReconstructionOperations(
        metadata_factory=FusionMetadata,
        # Outside-span breakpoints are not snapped here: create_fusion_cds snaps
        # them itself and marks the reconstruction low confidence.
        resolve_breakpoint=partial(resolve_breakpoint_on_exon_chain, snap_outside=False),
        nearest_boundary=nearest_breakpoint_boundary,
        retained_segments=intersect_tx_segments,
        extract_sequence=extract_sequence_from_segments,
        update_breakpoints=update_breakpoint_metadata,
        update_junction=update_junction_metadata,
        update_frame_and_stop=update_frame_and_stop_metadata,
    )
    return reconstruct_fusion_cds(
        genome, donor, acceptor, breakpoint1, breakpoint2,
        early_stop_aa_cutoff, operations,
    )

def classify_frame(fusion_meta):
    """Classify fusion frame from junction metadata."""
    if not fusion_meta:
        return "NA"
    status = normalize_text_or_none(fusion_meta.get("frame_status"))
    if not status:
        return "NA"
    token = status.strip().upper()
    return token if token in {"INFRAME", "FRAMESHIFT"} else "NA"

def translate_fusion(cds_seq, table=1, force_initial_methionine=False):
    """Translate fusion CDS in-frame from nucleotide 1 to the first stop codon."""
    if not cds_seq:
        return ""

    seq = cds_seq[: len(cds_seq) - (len(cds_seq) % 3)]
    if not seq:
        return ""

    protein = str(Seq(seq).translate(table=table, to_stop=True))
    if protein and force_initial_methionine:
        protein = "M" + protein[1:]
    return protein

def classify_protein_product(protein_seq, fusion_meta, protein_identical_to_reference):
    """Classify the translated product relative to the fusion junction.

    A fusion transcript can retain a donor stop codon before the RNA junction.
    In that case, translation yields a donor-only protein rather than a
    junction-spanning fusion protein.
    """
    stop_before_junction = parse_bool_or_none(fusion_meta.get("stop_before_junction"))

    if stop_before_junction is True:
        if protein_identical_to_reference is True:
            return "donor_only_reference_identical"
        if protein_identical_to_reference is False:
            return "donor_only_truncated"
        return "donor_only_reference_status_unknown"

    return "junction_spanning_fusion"

def annotate_nmd(cds_seq, exon_junction_positions, distance_threshold_nt=55):
    """Annotate NMD status for the detected ORF on the fusion CDS.

    The call is recorded as metadata; it only affects DIA eligibility when
    --exclude_nmd_from_dia (or --quantms_conservative) is set.
    """
    return model_nmd_status(
        cds_seq,
        1 if cds_seq else None,
        exon_junction_positions,
        distance_threshold_nt=distance_threshold_nt,
    )

def summarize_functional_consequences(
    fusion_cds,
    donor_cds_length,
    acceptor_cds_length,
    frame_status,
    fusion_meta,
    junction_peptide_unique,
):
    """Summarize predicted functional consequences for a fusion candidate."""
    donor_retained_nt = int(fusion_meta.get("junction_nt") or 0)
    acceptor_retained_nt = max(0, len(fusion_cds) - donor_retained_nt)

    donor_cds_retained_pct = None
    if donor_cds_length:
        donor_cds_retained_pct = round(
            (donor_retained_nt / float(donor_cds_length)) * 100.0, 2
        )

    acceptor_cds_retained_pct = None
    if acceptor_cds_length:
        acceptor_cds_retained_pct = round(
            (acceptor_retained_nt / float(acceptor_cds_length)) * 100.0, 2
        )

    early_stop_after_junction = fusion_meta.get("reason") == "early_stop_after_junction"
    stop_before_junction = (
        parse_bool_or_none(fusion_meta.get("stop_before_junction")) is True
    )
    product_class = normalize_text_or_none(fusion_meta.get("protein_product_class"))
    low_confidence = bool(fusion_meta.get("low_confidence"))
    inframe = frame_status == "INFRAME"

    if stop_before_junction:
        predicted_loss_of_function = product_class == "donor_only_truncated"
        predicted_chimera = False
        fusion_effect_class = product_class or "donor_only_product"
    else:
        predicted_loss_of_function = bool(
            early_stop_after_junction or low_confidence or not inframe
        )
        predicted_chimera = bool(inframe and not predicted_loss_of_function)

        if early_stop_after_junction:
            fusion_effect_class = "early_stop_loss_of_function"
        elif not inframe:
            fusion_effect_class = "frameshift_loss_of_function"
        elif predicted_chimera:
            fusion_effect_class = "predicted_chimera"
        elif predicted_loss_of_function:
            fusion_effect_class = "likely_loss_of_function"
        else:
            fusion_effect_class = "uncertain"

    return {
        "fusion_effect_class": fusion_effect_class,
        "donor_cds_retained_pct": donor_cds_retained_pct,
        "acceptor_cds_retained_pct": acceptor_cds_retained_pct,
        "predicted_loss_of_function": predicted_loss_of_function,
        "predicted_chimera": predicted_chimera,
        "early_stop_after_junction": early_stop_after_junction,
        "has_unique_junction_peptide": bool(junction_peptide_unique),
    }

def record_skip(stats, reason):
    """Increment skipped-pair counters for a given reason."""
    stats["skipped_count"] += 1
    stats["skip_reasons"][reason] += 1

def log_fusion_progress(idx, total, sample_label, fusion_name):
    """Log progress periodically while processing fusion events."""
    if idx == 0 or (idx + 1) % 25 == 0 or idx + 1 == total:
        sample_prefix = f"[{sample_label}] " if sample_label else ""
        logger.info(
            "%sProcessing fusion %d/%d: %s",
            sample_prefix,
            idx + 1,
            total,
            fusion_name,
        )

def parse_fusion_row_context(row):
    """Extract and normalize per-row fusion metadata used during reconstruction."""
    breakpoint1 = parse_int_or_none(row.get("breakpoint1"))
    breakpoint2 = parse_int_or_none(row.get("breakpoint2"))
    gene_1_symbol = normalize_text_or_none(row.get("gene_1_symbol"))
    gene_2_symbol = normalize_text_or_none(row.get("gene_2_symbol"))

    return {
        "fusion_name": f"{gene_1_symbol or 'NA'}-{gene_2_symbol or 'NA'}",
        "gene_1_id": normalize_gene_id(row.get("gene_1_id")),
        "gene_2_id": normalize_gene_id(row.get("gene_2_id")),
        "gene_1_symbol": gene_1_symbol,
        "gene_2_symbol": gene_2_symbol,
        "preferred_tx1": normalize_transcript_id(row.get("tx_1_id")),
        "preferred_tx2": normalize_transcript_id(row.get("tx_2_id")),
        "bp_chrom1": row.get("chrom1"),
        "bp_chrom2": row.get("chrom2"),
        "breakpoint1": breakpoint1,
        "breakpoint2": breakpoint2,
    }

def collect_partner_candidates(
    lookup: PartnerLookupContext,
    request: PartnerRequest,
):
    """Collect the top-ranked transcript/CDS candidate for one fusion partner."""
    return collect_transcript_cds_candidates(
        lookup.db,
        request.gene_id,
        lookup.transcript_index,
        request.breakpoint_chrom,
        lookup.genome,
        breakpoint=request.breakpoint,
        cds_cache=lookup.cds_cache,
        transcript_alias_index=lookup.transcript_alias_index,
        transcript_models=lookup.transcript_models,
        preferred_transcript_id=request.preferred_transcript,
        gene_symbol=request.gene_symbol,
        gene_symbol_index=lookup.gene_symbol_index,
        max_transcripts_per_gene=lookup.max_transcripts_per_gene,
    )

def compute_breakpoint_snap_summary(fusion_meta, args):
    """Return breakpoint snap-distance annotations for DIA confidence assessment."""
    donor_snap_distance = fusion_meta.get("donor_breakpoint_snap_distance_nt")
    acceptor_snap_distance = fusion_meta.get("acceptor_breakpoint_snap_distance_nt")

    max_snap_distance = max(
        [
            d
            for d in [
                parse_int_or_none(donor_snap_distance),
                parse_int_or_none(acceptor_snap_distance),
            ]
            if d is not None
        ]
        or [0]
    )

    breakpoint_snapped_far = bool(
        max_snap_distance > int(args.max_breakpoint_snap_distance_nt)
    )

    return max_snap_distance, breakpoint_snapped_far

def classify_breakpoint_resolution(location, snap_distance):
    """Map internal resolver details onto an auditable biological category."""
    if location == "outside_snapped":
        return "snapped_outside_transcript"
    if location == "intronic_splice_junction":
        return "snapped_intronic_breakpoint"
    if location == "annotated_boundary":
        return "exact_annotated_boundary"
    if location == "exonic" and (parse_int_or_none(snap_distance) or 0) == 0:
        return "exact_reported_breakpoint"
    return "unresolved"

def build_ranking_record(request: RankingRecordRequest) -> dict[str, Any]:
    """Build one biological-interpretation/DIA-metadata row for a valid fusion protein."""
    event = request.event
    row = event.row
    donor = event.donor
    acceptor = event.acceptor
    args = request.config
    fusion_cds = request.fusion_cds
    fusion_meta = request.fusion_meta
    protein_seq = request.protein_sequence
    functional = request.functional
    junction_eval = request.junction_evaluation
    nmd = request.nmd

    provenance = sample_provenance(
        event.sample_label, row.get("source_file"),
        getattr(args, "sample_metadata_lookup", {}),
    )
    return {
        "sample_basename": event.sample_label,
        "sample_id": event.sample_label,
        "batch": provenance["batch"],
        "condition": provenance["condition"],
        "annotation_release": getattr(args, "annotation_release", "NA"),
        "source_file": row.get("source_file"),
        "source_basename": row.get("source_basename"),
        "fusion_name": event.fusion_name,
        "event_index": event.event_index,
        "pair_token": request.pair_token,
        "primary_caller": row.get("caller"),
        "gene_1_symbol": row.get("gene_1_symbol"),
        "gene_2_symbol": row.get("gene_2_symbol"),
        "gene_1_id": row.get("gene_1_id"),
        "gene_2_id": row.get("gene_2_id"),
        "chrom1": event.breakpoint_chrom1,
        "chrom2": event.breakpoint_chrom2,
        "breakpoint1": event.breakpoint1,
        "breakpoint2": event.breakpoint2,
        "split_reads_max": parse_int_or_none(row.get("split_reads_max")),
        "split_reads_sum": parse_int_or_none(row.get("split_reads_sum")),
        "spanning_reads_max": parse_int_or_none(row.get("spanning_reads_max")),
        "spanning_reads_sum": parse_int_or_none(row.get("spanning_reads_sum")),
        "confidence": row.get("confidence"),
        "contributing_callers": row.get("contributing_callers"),
        "contributing_caller_count": row.get("contributing_caller_count"),
        "deduplicated_input_row_count": row.get("deduplicated_input_row_count"),
        "symbol_coordinate_gene_id_collision": row.get(
            "symbol_coordinate_gene_id_collision"
        ),
        "caller_annotations": row.get("caller_annotations"),
        "large_anchor_support": row.get("large_anchor_support"),
        "orientation_pass": row.get("orientation_pass"),
        "caller_frame_annotation": request.caller_frame_annotation,
        "caller_fusion_transcript": row.get("caller_fusion_transcript"),
        "caller_peptide_sequence": request.caller_peptide,
        "caller_fusion_cds": row.get("caller_fusion_cds"),
        "caller_vs_reconstructed_concordance": request.concordance,
        "donor_tid": donor.get("transcript_id"),
        "acceptor_tid": acceptor.get("transcript_id"),
        "donor_transcript_rank": donor.get("transcript_rank"),
        "acceptor_transcript_rank": acceptor.get("transcript_rank"),
        "donor_original_transcript_candidate_rank": donor.get(
            "original_transcript_candidate_rank"
        ),
        "acceptor_original_transcript_candidate_rank": acceptor.get(
            "original_transcript_candidate_rank"
        ),
        "donor_strand": donor.get("strand"),
        "acceptor_strand": acceptor.get("strand"),
        "donor_cds_start_nf": donor.get("cds_start_nf"),
        "donor_cds_end_nf": donor.get("cds_end_nf"),
        "donor_cds_completeness": donor.get("cds_completeness"),
        "acceptor_cds_start_nf": acceptor.get("cds_start_nf"),
        "acceptor_cds_end_nf": acceptor.get("cds_end_nf"),
        "acceptor_cds_completeness": acceptor.get("cds_completeness"),
        "donor_non_atg_start": donor.get("non_atg_start"),
        "acceptor_non_atg_start": acceptor.get("non_atg_start"),
        "donor_stop_codon_readthrough": donor.get("stop_codon_readthrough"),
        "acceptor_stop_codon_readthrough": acceptor.get("stop_codon_readthrough"),
        "donor_selenocysteine_feature_count": donor.get("selenocysteine_feature_count", 0),
        "acceptor_selenocysteine_feature_count": acceptor.get("selenocysteine_feature_count", 0),
        "donor_transcript_candidate_count": donor.get("transcript_candidate_count"),
        "acceptor_transcript_candidate_count": acceptor.get("transcript_candidate_count"),
        "donor_phase_missing": fusion_meta.get("donor_phase_missing"),
        "acceptor_phase_missing": fusion_meta.get("acceptor_phase_missing"),
        "phase_inferred": fusion_meta.get("phase_inferred"),
        "frame_inference_method": fusion_meta.get("frame_inference_method"),
        "transcript_selection_strategy": (
            "conservative_representative"
            if getattr(args, "max_transcripts_per_gene", 1) == 1
            else "ranked_multi_transcript"
        ),
        "reconstruction_scope": "annotation_model_projected_candidate_not_sample_expression_proof",
        "frame_status": request.frame_status,
        "protein_product_class": fusion_meta.get("protein_product_class"),
        "first_stop_codon_nt_start_1based": fusion_meta.get(
            "first_stop_codon_nt_start_1based"
        ),
        "first_stop_codon_nt_end_1based": fusion_meta.get(
            "first_stop_codon_nt_end_1based"
        ),
        "stop_before_junction": fusion_meta.get("stop_before_junction"),
        "translation_reaches_junction": fusion_meta.get("translation_reaches_junction"),
        "translation_crosses_junction": fusion_meta.get("translation_crosses_junction"),
        "translated_acceptor_aa": fusion_meta.get("translated_acceptor_aa"),
        "low_confidence": fusion_meta.get("low_confidence"),
        "fusion_effect_class": functional["fusion_effect_class"],
        "donor_cds_retained_pct": functional["donor_cds_retained_pct"],
        "acceptor_cds_retained_pct": functional["acceptor_cds_retained_pct"],
        "predicted_loss_of_function": functional["predicted_loss_of_function"],
        "predicted_chimera": functional["predicted_chimera"],
        "early_stop_after_junction": functional["early_stop_after_junction"],
        "has_junction_spanning_peptide": junction_eval.get(
            "has_junction_spanning_peptide"
        ),
        "has_unique_junction_peptide": junction_eval.get("has_unique_junction_peptide"),
        "junction_tryptic_peptide_count": junction_eval.get(
            "junction_tryptic_peptide_count"
        ),
        "junction_tryptic_unique_count": junction_eval.get(
            "junction_tryptic_unique_count"
        ),
        "junction_tryptic_peptides": junction_eval.get("junction_tryptic_peptides"),
        "junction_tryptic_unique_peptides": junction_eval.get(
            "junction_tryptic_unique_peptides"
        ),
        "canonical_uniqueness_assessed": junction_eval.get(
            "canonical_uniqueness_assessed"
        ),
        "protein_identical_to_reference": request.protein_identical_to_reference,
        "donor_retained_cds_nt": request.donor_retained_cds_nt,
        "acceptor_retained_cds_nt": request.acceptor_retained_cds_nt,
        "min_retained_cds_nt": args.min_retained_cds_nt,
        "dia_min_protein_length": args.min_protein_length,
        "require_junction_peptide_for_dia": args.require_junction_peptide,
        "require_unique_junction_peptide_for_dia": args.require_unique_junction_peptide,
        "exclude_frameshift_from_dia": args.exclude_frameshift_from_dia,
        "exclude_truncated_from_dia": args.exclude_truncated_from_dia,
        "exclude_nmd_from_dia": args.exclude_nmd_from_dia,
        "include_donor_only_products": args.include_donor_only_products,
        "max_breakpoint_snap_distance_nt": args.max_breakpoint_snap_distance_nt,
        "breakpoint_snapped_far": request.breakpoint_snapped_far,
        "max_breakpoint_snap_distance_observed_nt": request.max_snap_distance,
        "translation_input_nt_length": len(fusion_cds),
        "exclude_incomplete_cds": args.exclude_incomplete_cds,
        "nmd_predicted": nmd.get("nmd_predicted"),
        "nmd_reason": nmd.get("nmd_reason"),
        "stop_codon_nt_start_1based": nmd.get("stop_codon_nt_start_1based"),
        "stop_codon_nt_end_1based": nmd.get("stop_codon_nt_end_1based"),
        "nearest_downstream_exon_junction_nt": nmd.get(
            "nearest_downstream_exon_junction_nt"
        ),
        "nmd_distance_nt": nmd.get("nmd_distance_nt"),
        "junction_nt": fusion_meta.get("junction_nt"),
        "junction_aa": fusion_meta.get("junction_aa"),
        "junction_peptide_unique": request.junction_peptide_unique,
        "exon_junction_nt_positions": "|".join(
            str(x) for x in fusion_meta.get("exon_junction_nt_positions", [])
        ),
        "donor_breakpoint_location": fusion_meta.get("donor_breakpoint_location"),
        "acceptor_breakpoint_location": fusion_meta.get("acceptor_breakpoint_location"),
        "donor_resolved_genomic_pos": fusion_meta.get("donor_resolved_genomic_pos"),
        "acceptor_resolved_genomic_pos": fusion_meta.get(
            "acceptor_resolved_genomic_pos"
        ),
        "donor_breakpoint_snap_distance_nt": fusion_meta.get(
            "donor_breakpoint_snap_distance_nt"
        ),
        "acceptor_breakpoint_snap_distance_nt": fusion_meta.get(
            "acceptor_breakpoint_snap_distance_nt"
        ),
        "donor_breakpoint_resolution_class": classify_breakpoint_resolution(
            fusion_meta.get("donor_breakpoint_location"),
            fusion_meta.get("donor_breakpoint_snap_distance_nt"),
        ),
        "acceptor_breakpoint_resolution_class": classify_breakpoint_resolution(
            fusion_meta.get("acceptor_breakpoint_location"),
            fusion_meta.get("acceptor_breakpoint_snap_distance_nt"),
        ),
        "independent_junction_evidence": (
            (parse_int_or_none(row.get("split_reads_sum")) or 0)
            >= int(getattr(args, "min_split_reads_for_snapped_product", 1))
        ),
        "cds_length": len(fusion_cds),
        "adjusted_cds_length": len(fusion_cds),
        "cds_sequence": fusion_cds,
        "protein_length": len(protein_seq),
        "protein_sequence": protein_seq,
        "protein_sequence_hash": sequence_hash(protein_seq),
        "cds_sequence_hash": sequence_hash(fusion_cds),
    }

def fusion_pair_token(sample_label, event_index, donor_index, acceptor_index):
    """Stable candidate identifier: ``<sample>:<event>_<donor isoform>_<acceptor isoform>``."""
    return f"{sample_label}:{event_index}_{donor_index}_{acceptor_index}"


def evaluate_candidate_pair(
    request: CandidatePairRequest,
    references: ReferenceContext,
):
    """
    Reconstruct and annotate one donor/acceptor transcript pair.

    Returns
    -------
    tuple
        (record, failure_reason). record is None when reconstruction fails.
    """
    row = request.row
    donor = request.donor
    acceptor = request.acceptor
    args = references.args

    donor_candidate = TranscriptCandidate(
        chrom=donor["chrom"],
        cds_segments=donor["segments"],
        exon_segments=donor.get("exon_segments", []),
        cds_tx_segments=donor.get("cds_tx_segments", []),
    )

    acceptor_candidate = TranscriptCandidate(
        chrom=acceptor["chrom"],
        cds_segments=acceptor["segments"],
        exon_segments=acceptor.get("exon_segments", []),
        cds_tx_segments=acceptor.get("cds_tx_segments", []),
    )

    fusion_cds, fusion_meta = create_fusion_cds(
        references.genome,
        donor_candidate,
        acceptor_candidate,
        request.breakpoint1,
        request.breakpoint2,
        early_stop_aa_cutoff=args.early_stop_aa_cutoff,
    )

    if not fusion_cds:
        reason = fusion_meta.get("reason") or "unknown"
        return None, f"fusion_cds_failed:{reason}"

    frame_status = classify_frame(fusion_meta)
    caller_frame_annotation = row.get("caller_frame_annotation")
    caller_peptide = row.get("caller_peptide_sequence")

    protein_seq = translate_fusion(
        fusion_cds,
        table=2 if normalize_chrom_token(donor.get("chrom")) == "MT" else 1,
        force_initial_methionine=bool(donor.get("non_atg_start")),
    )

    nmd = annotate_nmd(
        fusion_cds,
        fusion_meta.get("exon_junction_nt_positions", []),
        distance_threshold_nt=args.nmd_distance_threshold_nt,
    )

    junction_eval = evaluate_junction_peptides(
        protein_seq,
        fusion_meta.get("fusion_junction_nt"),
        reference_peptide_set=references.reference_peptides,
        max_missed_cleavages=args.max_missed_cleavages,
        min_len=args.digested_min_peptide_length,
        max_len=args.digested_max_peptide_length,
    )
    junction_peptide_unique = junction_eval.get("has_unique_junction_peptide")

    donor_retained_cds_nt = parse_int_or_none(fusion_meta.get("junction_nt")) or 0
    acceptor_retained_cds_nt = max(0, len(fusion_cds) - donor_retained_cds_nt)

    protein_identical_to_reference = (
        protein_seq in references.reference_proteins
        if references.reference_proteins is not None and protein_seq
        else None
    )

    protein_product_class = classify_protein_product(
        protein_seq=protein_seq,
        fusion_meta=fusion_meta,
        protein_identical_to_reference=protein_identical_to_reference,
    )
    fusion_meta["protein_product_class"] = protein_product_class

    junction_nt = parse_int_or_none(fusion_meta.get("fusion_junction_nt"))
    if junction_nt is None:
        translated_acceptor_aa = None
    elif parse_bool_or_none(fusion_meta.get("stop_before_junction")) is True:
        translated_acceptor_aa = 0
    else:
        translated_acceptor_aa = max(0, len(protein_seq) - (junction_nt // 3))
    fusion_meta["translated_acceptor_aa"] = translated_acceptor_aa

    max_snap_distance, breakpoint_snapped_far = compute_breakpoint_snap_summary(
        fusion_meta,
        args,
    )

    fusion_meta["low_confidence"] = bool(
        fusion_meta.get("low_confidence") or breakpoint_snapped_far
    )

    # The sample label makes the token (written as the FASTA event_id) unique across
    # samples; event_index alone restarts at 0 for every sample.
    pair_token = fusion_pair_token(
        request.sample_label, request.event_index, request.donor_index, request.acceptor_index,
    )

    concordance = classify_caller_concordance(
        protein_seq,
        caller_peptide,
        frame_status,
        caller_frame_annotation,
        row.get("caller_fusion_cds"),
    )

    functional = summarize_functional_consequences(
        fusion_cds,
        donor.get("cds_length"),
        acceptor.get("cds_length"),
        frame_status,
        fusion_meta,
        junction_peptide_unique,
    )

    record = build_ranking_record(
        RankingRecordRequest(
            event=request,
            pair_token=pair_token,
            fusion_cds=fusion_cds,
            fusion_meta=fusion_meta,
            protein_sequence=protein_seq,
            frame_status=frame_status,
            caller_frame_annotation=caller_frame_annotation,
            caller_peptide=caller_peptide,
            concordance=concordance,
            functional=functional,
            junction_evaluation=junction_eval,
            junction_peptide_unique=junction_peptide_unique,
            nmd=nmd,
            donor_retained_cds_nt=donor_retained_cds_nt,
            acceptor_retained_cds_nt=acceptor_retained_cds_nt,
            protein_identical_to_reference=protein_identical_to_reference,
            breakpoint_snapped_far=breakpoint_snapped_far,
            max_snap_distance=max_snap_distance,
            config=FusionFilterConfig.from_namespace(args),
        )
    )

    return record, None
