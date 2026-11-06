#!/usr/bin/env python3
"""SUPPA IOE events -> annotated-transcript protein candidates and peptide FASTA.

Optional PSI matrices act only as an event-level inclusion filter. PSI values are
reported separately (``--out_psi_summary_tsv``) and are not embedded in
consequence records, protein mappings, junction peptides, or FASTA headers.

Rescue follows the rMATS rules (same start codons, Kozak threshold, minimum ORF
length, exploratory tiers and FASTAs). Because SUPPA translates complete annotated
transcripts, ``--allow_alt_start`` applies when a transcript has no annotated start
codon (``cds_start_NF``) or its annotated CDS yields no protein, and
``--allow_longest_orf`` only when nothing else translates.

Example::

    python suppatoprotein.py \
        --gtf_db gencode_v46.gtf.db --genome GRCh38.primary_assembly.fa \
        --annotation_release GENCODE_46 --organism Homo_sapiens \
        --event_files 'suppa/generate_events/per_local_event/events.ioe' \
        --psi_files 'batch*/suppa/psi_per_local_event/suppa_local.psi' \
        --reference_proteome UP000005640_9606.fasta \
        --min_psi 0.05 --min_psi_samples 3 --short_junction_peptides \
        --out_prot_fa suppa.primary.fasta --out_junc_fa suppa.junctions.fasta \
        --out_consequence_tsv suppa.consequences.tsv --out_psi_summary_tsv suppa.psi.tsv
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm

from proteogenomic.provenance import (
    batch_from_path, configure_logging, load_sample_metadata, require_files,
)
from proteogenomic.splice_reconstruction_core import (
    CanonicalProteinCache, GenomeSequenceCache, TranscriptResolver, merge_protein_mappings,
    rank_compatible_transcripts, SpliceFileResult,
)
from proteogenomic.proteogenomic_models import SpliceProteinResult
from proteogenomic.proteogenomic_policies import ReconstructionPolicy
from proteogenomic.splice_cli import parse_suppa_args
from proteogenomic.suppa_parsing import expand_file_patterns, normalise_event_id, parse_suppa_event_coords, split_list_field
from proteogenomic.suppa_psi import evaluate_psi_event, load_psi_files, write_psi_filter_summary
from proteogenomic.splice_annotation import build_transcript_models
from proteogenomic.release_validation import preflight_producer_contract
from proteogenomic.splice_consequence import evaluate_shared_splice_consequence
from proteogenomic.rmats_stages import choose_output_tier
from proteogenomic.splice_rescue import (
    ALT_START_NOTE_PREFIX, RESCUE_STRATEGIES, alternative_start_fields, alternative_start_from_note,
    find_alternative_start, longest_orf_from_sequence, normalise_start_codons,
)

from proteogenomic.splice_translation import (
    CONSEQUENCE_TSV_COLUMNS, _translate_until_first_stop, add_protein_mapping,
    append_reason,
    canonical_start_genomic,
    count_reference_unique_tryptic_peptides,
    digest_tryptic_peptides,
    extract_cds_sequence_for_model,
    generate_codon_aware_junction_peptides,
    load_reference_tryptic_peptides,
    match_transcript_id,
    normalize_phase_value, open_genome_index,
    should_include_protein_in_fasta,
    write_consequence_tsv,
    write_junction_fasta,
    write_protein_fasta,
    transcript_cds_audit_fields,
    prepare_run_manifest, publish_run_manifest,
    translate_cds_for_model, mask_selenocysteine_stops_for_consequence,
    is_mitochondrial_chromosome,
)


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
    """Classify an annotated isoform relative to its closest opposite IOE isoform.

    Frame, stop and NMD values come from ``evaluate_shared_splice_consequence``
    (the same definitions rMATS reports); the classes below are derived from them.
    """
    cds = tx_model.get("cds") or []
    strand = tx_model.get("strand")
    altered_first = sorted(cds, key=lambda x: x[0], reverse=strand == "-")[0] if cds else None
    altered_phase = (normalize_phase_value(altered_first[2]) or 0) if altered_first else 0
    shared = evaluate_shared_splice_consequence(
        cds, (reference_model.get("cds") or []) if reference_model else None,
        strand, cds_seq, tx_model.get("exons") or [],
        translation_start_offset_nt=altered_phase,
        nmd_distance_threshold_nt=nmd_distance_threshold_nt,
    ).to_dict()

    ri_event = str(event_type or "").upper() == "RI"
    ri_orf_preserved = None
    if ri_event:
        ri_orf_preserved = bool(shared["frame_status"] == "INFRAME" and not shared["premature_stop"] and protein)

    classes = ["annotated_cds"]
    if shared["frameshift"]:
        classes.append("frameshift_relative_to_opposite_isoform")
    elif shared["frame_status"] == "INFRAME":
        classes.append("inframe_relative_to_opposite_isoform")
    if shared["premature_stop"]:
        classes.append("premature_stop")
    if shared["nmd_predicted"]:
        classes.append("nmd_predicted")
    if ri_event:
        classes.append("ri_orf_preserved" if ri_orf_preserved else "ri_orf_not_preserved")

    return {
        "region_class": "annotated_cds",
        "frame_comparison_transcript": reference_model.get("transcript_id") if reference_model else None,
        "frame_comparison_basis": "codon_phase_at_shared_genomic_positions" if reference_model else "no_opposite_isoform",
        "canonical_start_genomic": canonical_start_genomic(cds, strand),
        "start_retained_relative_to_own_annotation": True if cds else None,
        "start_loss_relative_to_own_annotation": False if cds else None,
        "ri_event": ri_event,
        "ri_orf_preserved": ri_orf_preserved,
        "consequence_class": ";".join(classes),
        **shared,
    }


def _collect_suppa_row(
    rowd: Dict, rid: int, event_type: str, source_path: Path,
    transcripts: Dict[str, Dict], fa_index, args, collectors,
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

        protein, strategy, note, alt_start = _translate_transcript(cds_seq, txm, args)
        opposite, opposite_ranking = rank_compatible_transcripts(txm, opposite_models)
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
        consequence.update(alternative_start_fields(alt_start))
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
        identical_to_opposite = bool(protein and opposite_protein and protein == opposite_protein)
        if identical_to_opposite:
            include = False
            reasons = append_reason(reasons, "protein_sequence_identical_to_opposite_isoform")
        # As in rMATS: rescue products go to their own FASTA, so primary-database
        # consequence filters must not hide them (unless identical to the opposite isoform).
        rescue = bool(protein and strategy in RESCUE_STRATEGIES)
        if rescue and not identical_to_opposite:
            include, reasons = True, ""

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
        # The unique-peptide requirement is a primary-database rule (as in rMATS).
        if include and not rescue and args.require_unique_event_peptide:
            if has_event_unique is not True:
                include = False
                reasons = append_reason(reasons, "no_opposite_isoform_unique_tryptic_peptide")
            if has_unique is not True:
                include = False
                reasons = append_reason(reasons, "no_reference_unique_tryptic_peptide")

        tier_decision = choose_output_tier(include, strategy)
        tier = tier_decision.tier
        consequence_rows.append({
            **base_row, **consequence,
            "coords": ";".join(f"{s}-{e}" for s, e, _ in cds),
            "first_overlap": canonical_start_genomic(cds, txm.get("strand")),
            "trim": phase_trim, "trimmed": bool(phase_trim),
            "pad_partial_codons": args.pad_partial_codons,
            "translation_strategy": strategy,
            "translation_note": note,
            "database_output_tier": tier,
            "has_reference_unique_tryptic_peptide": has_unique,
            "reference_unique_tryptic_peptide_count": unique_count,
            "has_opposite_isoform_unique_tryptic_peptide": has_event_unique,
            "opposite_isoform_unique_tryptic_peptide_count": event_unique_count,
            "protein_sequence": protein, "protein_length": len(protein) if protein else 0,
            "protein_in_fasta": include, "fasta_exclusion_reasons": reasons,
        })
        target = collectors.get(tier_decision.collector_name)
        if include and target is not None:
            add_protein_mapping(target, protein, {
                "source_file": source_path.name, "gene_id": txm.get("gene_id"),
                "gene_symbol": txm.get("gene_name"), "tx": tx_id,
                "event_type": parsed_event_type, "event_id": event_id,
                "source_event_id": event_id,
                "psi_min_threshold": args.min_psi,
                "psi_min_samples": args.min_psi_samples,
                "variant": membership, "translation_strategy": strategy,
                "translation_note": note,
                "database_output_tier": tier,
                "transcript_selection_score": opposite_ranking.score,
                "transcript_selection_rank": opposite_ranking.rank,
                "transcript_candidate_count": opposite_ranking.candidate_count,
                "transcript_selection_ambiguous": opposite_ranking.ambiguous,
                **_rescue_mapping_fields(strategy, alt_start),
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


def _translate_transcript(cds_seq, txm, args):
    """Translate one complete IOE transcript, with rMATS-equivalent explicit rescue.

    Returns (protein, translation_strategy, translation_note, alt_start_assessment).

    * The annotated CDS is translated as before (primary product).
    * ``--allow_alt_start``: when the transcript has no annotated start codon
      (``cds_start_NF``) or its annotated CDS yields no protein, translate from
      the first in-frame alternative start meeting the Kozak threshold.
    * ``--allow_longest_orf``: when nothing else translates, use the longest
      stop-delimited ORF of at least ``--min_alt_orf_aa`` residues.
    """
    pad = args.pad_partial_codons
    protein = translate_cds_for_model(cds_seq, txm, pad=pad)
    table = 2 if is_mitochondrial_chromosome(txm.get("chrom")) else 1
    if args.allow_alt_start and (txm.get("cds_start_nf") or not protein):
        offset = find_alternative_start(
            cds_seq, args.alternative_start_codons, args.min_alt_start_kozak_strength,
        )
        if offset is not None:
            alternative = _translate_until_first_stop(cds_seq[offset:], pad=pad, table=table)
            if alternative:
                note = f"{ALT_START_NOTE_PREFIX}{offset}"
                return (alternative, "alternative_start", note,
                        alternative_start_from_note(cds_seq, "alternative_start", note))
    if protein:
        return protein, "annotated_cds", ANNOTATED_NOTE, None
    if args.allow_longest_orf:
        orf = longest_orf_from_sequence(
            cds_seq, pad=pad, min_alt_orf_aa=args.min_alt_orf_aa, translation_table=table,
        )
        if orf:
            return orf, "alternative_orf", "longest_orf_rescue_explicitly_allowed", None
    return None, "not_translated", ANNOTATED_NOTE, None


ANNOTATED_NOTE = "complete_ioe_transcript_annotated_cds"


def _rescue_mapping_fields(strategy, alt_start):
    """FASTA-header alternative-start provenance, matching the rMATS mapping fields."""
    return {
        "alt_start": "Yes" if strategy == "alternative_start" else "No",
        "alt_start_codon": alt_start.codon if alt_start else None,
        "alt_start_kozak_strength": alt_start.kozak_strength if alt_start else None,
        "alt_start_kozak_score": alt_start.kozak_score if alt_start else None,
        "alt_start_kozak_context": alt_start.context_minus6_plus6 if alt_start else None,
    }


def process_suppa_row(
    rowd: Dict, rid: int, event_type: str, source_path: Path,
    transcripts: Dict[str, Dict], fa_index, args,
    canonical_cache: CanonicalProteinCache, reference_peptides=None,
) -> SpliceProteinResult:
    """Return all products for one SUPPA row without mutating caller state."""
    result = SpliceProteinResult()
    _collect_suppa_row(
        rowd, rid, event_type, source_path, transcripts, fa_index, args,
        {
            "primary": result.proteins,
            "alternative_start": result.alternative_start_proteins,
            "exploratory_orf": result.exploratory_orf_proteins,
        },
        canonical_cache, result.junction_records,
        result.consequence_rows, reference_peptides,
    )
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
    alt_start_prot_info: Optional[Dict] = None,
    exploratory_orf_prot_info: Optional[Dict] = None,
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
    progress = tqdm(desc=p.name)
    for chunk_number, chunk in enumerate(chunk_iter):
        if chunk_number == 0:
            columns = set(chunk.columns)
            if not ({"event_id", "event"} & columns):
                raise ValueError(f"SUPPA table {p} lacks event_id/event column")
            missing = {"alternative_transcripts", "total_transcripts"} - columns
            if missing:
                raise ValueError(f"SUPPA table {p} lacks required column(s): {', '.join(sorted(missing))}")
        for rowd in chunk.to_dict(orient="records"):
            progress.update(1)
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
            details = (psi_lookup.get(event_id, {}) if psi_lookup else {}).get("sample_details", [])
            rowd["sample_id"] = ";".join(sorted({x["sample_id"] for x in details})) or "NA"
            rowd["batch"] = ";".join(sorted({x["batch"] for x in details})) or batch_from_path(p)
            rowd["condition"] = ";".join(sorted({x["condition"] for x in details})) or "NA"
            parsed = parse_suppa_event_coords(event_id)
            psi_record = {
                "source_file": str(p),
                "sample_id": rowd["sample_id"],
                "batch": rowd["batch"],
                "condition": rowd["condition"],
                "event_type": parsed["etype"] if parsed else event_type,
                "event_id": event_id,
                **psi_decision,
            }
            psi_filter_rows.append(psi_record)
            if keep_event:
                passed_count += 1
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
                if alt_start_prot_info is not None:
                    merge_protein_mappings(alt_start_prot_info, row_result.alternative_start_proteins)
                if exploratory_orf_prot_info is not None:
                    merge_protein_mappings(exploratory_orf_prot_info, row_result.exploratory_orf_proteins)
                junction_recs.extend(row_result.junction_records)
                consequence_rows.extend(row_result.consequence_rows)
                generated = len(row_result.consequence_rows)
                psi_record["consequence_rows_generated"] = generated
                psi_record["reconstruction_status"] = (
                    "reconstructed" if generated > 0 else "no_consequence_row_generated"
                )
            row_count += 1
    progress.close()

    logging.info(
        "Processed %d SUPPA events from %s (%d passed PSI filtering)",
        row_count,
        p,
        passed_count,
    )


# --------------------------- ARGUMENTS ---------------------------
def validate_args(args, parser):
    """Validate dependent CLI options and apply named policy presets."""
    try:
        require_files([args.gtf_db, args.genome], "critical reference")
        if args.reference_proteome:
            require_files(args.reference_proteome, "reference proteome")
        if args.sample_metadata:
            require_files([args.sample_metadata], "sample metadata")
    except FileNotFoundError as exc:
        parser.error(str(exc))
    if args.short_junction_peptides and not args.out_junc_fa:
        parser.error("--out_junc_fa is required when --short_junction_peptides is set")
    args.alternative_start_codons, invalid_codons = normalise_start_codons(args.alternative_start_codons)
    if invalid_codons:
        parser.error(f"Invalid --alternative_start_codons: {', '.join(invalid_codons)}")
    if args.min_alt_orf_aa < 1:
        parser.error("--min_alt_orf_aa must be at least 1")
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
    # Inputs are fingerprinted now; the manifest is only published after success.
    manifest = prepare_run_manifest(args, args.out_prot_fa, Path(__file__).name)
    run(args)
    publish_run_manifest(manifest)
    return 0


def run(args):
    """Run SUPPA reconstruction for parsed and validated ``args``."""
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

    psi_files = expand_file_patterns(args.psi_files, "PSI", require_each=True)
    if args.psi_files and not psi_files:
        raise FileNotFoundError(
            "No SUPPA PSI files matched the supplied --psi_files patterns"
        )
    if psi_files:
        logging.info(
            "Found %d PSI files",
            len(psi_files),
        )

    # ----------------------------------------------------
    # Load PSI lookup
    # ----------------------------------------------------
    # None is reserved for a deliberately omitted PSI filter.
    psi_lookup = None
    if not psi_files:
        logging.info("No PSI files supplied; all IOE events will be considered.")
    else:
        psi_lookup = load_psi_files(psi_files, load_sample_metadata(args.sample_metadata))
        if not psi_lookup:
            # A requested PSI filter must never fail open into "keep every event".
            raise ValueError("PSI files were supplied, but no PSI events could be loaded")
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
        result = SpliceFileResult({}, {}, {}, [], [], [])
        process_event_file(
            event_type=path.stem, p=path, transcripts=transcripts,
            fa_index=fa_index, args=args, prot_info=result.proteins,
            canonical_cache=canonical_cache, junction_recs=result.junction_records,
            consequence_rows=result.consequence_rows, psi_lookup=psi_lookup,
            psi_filter_rows=result.summary_rows, reference_peptides=reference_peptides,
            alt_start_prot_info=result.alternative_start_proteins,
            exploratory_orf_prot_info=result.exploratory_orf_proteins,
        )
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(reconstruct_file, event_files):
            merge_protein_mappings(prot_info, result.proteins)
            merge_protein_mappings(alt_start_prot_info, result.alternative_start_proteins)
            merge_protein_mappings(exploratory_orf_prot_info, result.exploratory_orf_proteins)
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
    raise SystemExit(main())
