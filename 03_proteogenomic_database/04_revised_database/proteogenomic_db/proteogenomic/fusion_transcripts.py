"""Fusion transcript discovery, ranking, and model construction."""
from __future__ import annotations
import logging
from collections import defaultdict
from .fusion_coordinates import (
    build_cds_tx_segments, build_transcript_segments,
    extract_cds_sequence, get_cds_exons, get_exon_intervals,
)
from .fusion_values import chrom_matches, normalize_gene_symbol, normalize_transcript_id
from .splice_annotation import child_features_by_parent
from .splice_translation import match_transcript_id
LOGGER = logging.getLogger(__name__)


def get_transcript_candidates(
    db,
    gene_id,
    transcript_index=None,
    preferred_chrom=None,
    gene_symbol=None,
    gene_symbol_index=None,
):
    """Return ranked transcript candidates as (transcript_id, chrom)."""
    if gene_id is None:
        return []

    raw = str(gene_id).strip()
    if not raw:
        return []

    base = raw.split(".")[0]
    candidates = []
    for cand in (raw, base, f"gene:{raw}", f"gene:{base}"):
        if cand and cand not in candidates:
            candidates.append(cand)

    transcripts = []
    if transcript_index is not None:
        for key in candidates:
            transcripts.extend(transcript_index.get(key, []))
    else:
        gene_feature = None
        for cand in candidates:
            try:
                gene_feature = db[cand]
                break
            except KeyError:
                continue
        if gene_feature is not None:
            for child in db.children(
                gene_feature.id, featuretype="transcript", level=1
            ):
                exon_count = sum(1 for _ in db.children(child.id, featuretype="exon"))
                cds_len = sum(
                    (cds.end - cds.start + 1)
                    for cds in db.children(child.id, featuretype="CDS")
                )
                transcripts.append((child.id, cds_len, exon_count, child.chrom))

    if not transcripts:
        symbol_key = normalize_gene_symbol(gene_symbol)
        if gene_symbol_index is not None and symbol_key:
            transcripts.extend(gene_symbol_index.get(symbol_key, []))

    if not transcripts:
        return []

    if preferred_chrom is not None:
        matched = [t for t in transcripts if chrom_matches(t[3], preferred_chrom)]
        if matched:
            transcripts = matched

    # De-duplicate by transcript id while preserving first seen payload.
    dedup = {}
    for t in transcripts:
        tid = t[0]
        if tid not in dedup:
            dedup[tid] = t
    transcripts = list(dedup.values())

    # Rank: CDS support first, then longer CDS, then exon count.
    transcripts.sort(key=lambda x: (x[1] > 0, x[1], x[2]), reverse=True)
    return [(t[0], t[3]) for t in transcripts]

def get_ranked_transcript_candidates(
    db,
    gene_id,
    transcript_index,
    preferred_chrom,
    breakpoint=None,
    gene_symbol=None,
    gene_symbol_index=None,
    transcript_models=None,
    preferred_transcript_id=None,
):
    """Return transcript candidates sorted for top-1 selection.

    Ranking priority:
    1) chromosome match
    2) CDS completeness (start+stop codon support)
    3) expression proxy when available
    4) exon support
    """
    candidates = get_transcript_candidates(
        db,
        gene_id,
        transcript_index=transcript_index,
        preferred_chrom=preferred_chrom,
        gene_symbol=gene_symbol,
        gene_symbol_index=gene_symbol_index,
    )

    preferred_tx = normalize_transcript_id(preferred_transcript_id)
    ranked = []
    for transcript_id, chrom in candidates:
        cds_len = 0
        exon_count = 0
        cds_exon_count = 0
        cds_complete = 0
        expr_present = 0
        expr_value = 0.0

        model = (transcript_models or {}).get(transcript_id)
        if model:
            cds_len = int(model.get("cds_len") or 0)
            exon_count = int(model.get("exon_count") or 0)
            cds_exon_count = int(model.get("cds_exon_count") or 0)
            cds_complete = 1 if model.get("cds_complete") else 0
            expr = model.get("expression_proxy")
            if expr is not None:
                expr_present = 1
                expr_value = float(expr)
        else:
            try:
                cds_exons = get_cds_exons(db, transcript_id)
                cds_len = sum((end - start + 1) for start, end, _, _ in cds_exons)
                cds_exon_count = len(cds_exons)
                exon_count = sum(
                    1 for _ in db.children(transcript_id, featuretype="exon")
                )
            except (KeyError, AttributeError):
                pass

        chrom_match = (
            1 if (preferred_chrom and chrom_matches(chrom, preferred_chrom)) else 0
        )
        preferred_bonus = (
            1
            if (preferred_tx and normalize_transcript_id(transcript_id) == preferred_tx)
            else 0
        )
        exon_support = max(cds_exon_count, exon_count)
        ranked.append(
            (
                transcript_id,
                chrom,
                chrom_match,
                cds_complete,
                expr_present,
                expr_value,
                exon_support,
                cds_len,
                preferred_bonus,
            )
        )

    ranked.sort(
        key=lambda item: (
            item[2],
            item[3],
            item[4],
            item[5],
            item[6],
            item[7],
            item[8],
        ),
        reverse=True,
    )
    return [(item[0], item[1]) for item in ranked]

def safe_attr_first(feature, keys, default=None):
    """Return the first available gffutils attribute value from a list of keys."""
    for key in keys:
        values = feature.attributes.get(key, [])
        if values:
            return values[0]
    return default

def build_single_transcript_model(db, feature, children=None):
    """Build one transcript-model record from a gffutils transcript feature.

    ``children`` optionally maps featuretype -> pre-fetched child features
    (see splice_annotation.child_features_by_parent); without it the database
    is queried for this transcript.
    """
    transcript_id = feature.id
    transcript_base = transcript_id.split(".")[0] if transcript_id else None

    gene_id = safe_attr_first(feature, ["gene_id"])
    gene_base = gene_id.split(".")[0] if gene_id else None

    parent_id = safe_attr_first(feature, ["Parent"])
    parent_base = parent_id.split(".")[0] if parent_id else None

    gene_symbol = safe_attr_first(feature, ["gene_name", "gene_symbol", "gene"])

    prefetched = children is not None
    children = children or {}
    cds_exons = get_cds_exons(db, transcript_id, children.get("CDS", []) if prefetched else None)
    exons = get_exon_intervals(db, transcript_id, children.get("exon", []) if prefetched else None)

    exon_segments = build_transcript_segments(exons)
    cds_segments = build_transcript_segments(cds_exons)
    cds_tx_segments = build_cds_tx_segments(cds_exons, exon_segments)

    cds_len = sum(end - start + 1 for start, end, _phase, _strand in cds_exons)
    exon_count = len(exons)
    cds_exon_count = len(cds_exons)

    if prefetched:
        has_start_codon = bool(children.get("start_codon"))
        has_stop_codon = bool(children.get("stop_codon"))
    else:
        try:
            has_start_codon = any(
                True for _ in db.children(transcript_id, featuretype="start_codon")
            )
            has_stop_codon = any(
                True for _ in db.children(transcript_id, featuretype="stop_codon")
            )
        except (KeyError, AttributeError, TypeError, ValueError):
            has_start_codon = False
            has_stop_codon = False

    expression_proxy = None
    for key in ("TPM", "FPKM", "RPKM", "coverage", "cov", "expr", "expression"):
        raw_values = feature.attributes.get(key, [])
        if not raw_values:
            continue
        try:
            expression_proxy = float(raw_values[0])
            break
        except (TypeError, ValueError):
            continue

    tags = feature.attributes.get("tag", [])
    if prefetched:
        selenocysteine_feature_count = len(children.get("Selenocysteine", ()))
    else:
        try:
            selenocysteine_feature_count = sum(
                1 for _ in db.children(feature.id, featuretype="Selenocysteine")
            )
        except (KeyError, AttributeError, TypeError, ValueError):
            selenocysteine_feature_count = 0
    cds_start_nf = "cds_start_NF" in tags
    cds_end_nf = "cds_end_NF" in tags
    completeness = (
        "partial_start_and_end" if cds_start_nf and cds_end_nf else
        "partial_start" if cds_start_nf else
        "partial_end" if cds_end_nf else "complete"
    )
    return {
        "transcript_id": transcript_id,
        "transcript_base": transcript_base,
        "gene_id": gene_id,
        "gene_base": gene_base,
        "parent_id": parent_id,
        "parent_base": parent_base,
        "chrom": feature.chrom,
        "strand": feature.strand,
        "exons": exons,
        "cds_exons": cds_exons,
        "exon_segments": exon_segments,
        "cds_segments": cds_segments,
        "cds_tx_segments": cds_tx_segments,
        "cds_len": cds_len,
        "exon_count": exon_count,
        "cds_exon_count": cds_exon_count,
        "cds_complete": bool(has_start_codon and has_stop_codon and cds_len > 0),
        "cds_start_nf": cds_start_nf,
        "cds_end_nf": cds_end_nf,
        "cds_completeness": completeness,
        "non_atg_start": "non_ATG_start" in tags,
        "stop_codon_readthrough": "stop_codon_readthrough" in tags,
        "selenocysteine_feature_count": selenocysteine_feature_count,
        "expression_proxy": expression_proxy,
        "gene_symbol": gene_symbol,
    }

def build_transcript_models(db):
    """Build transcript models and lookup indices from gffutils DB."""
    transcript_models = {}
    transcript_alias_index = defaultdict(list)
    gene_to_transcripts = defaultdict(list)
    gene_symbol_to_transcripts = defaultdict(list)

    # One bulk query instead of five per transcript.
    children_by_parent = child_features_by_parent(
        db, ("CDS", "exon", "start_codon", "stop_codon", "Selenocysteine")
    )
    for feature in db.features_of_type("transcript"):
        try:
            model = build_single_transcript_model(db, feature, children_by_parent.get(feature.id, {}))
        except (KeyError, AttributeError, TypeError, ValueError, IndexError) as e:
            LOGGER.debug(
                "Skipping transcript model for %s: %s", getattr(feature, "id", "NA"), e
            )
            continue

        transcript_id = model["transcript_id"]
        transcript_base = model["transcript_base"]
        gene_id = model["gene_id"]
        gene_base = model["gene_base"]
        parent_id = model["parent_id"]
        parent_base = model["parent_base"]
        gene_symbol = model["gene_symbol"]

        transcript_models[transcript_id] = model

        for alias in {transcript_id, transcript_base}:
            if alias:
                transcript_alias_index[alias].append(transcript_id)

        transcript_payload = (
            transcript_id,
            model["cds_len"],
            model["exon_count"],
            model["chrom"],
        )

        for gene_key in {gene_id, gene_base, parent_id, parent_base}:
            if gene_key:
                gene_to_transcripts[gene_key].append(transcript_payload)

        symbol_key = normalize_gene_symbol(gene_symbol)
        if symbol_key:
            gene_symbol_to_transcripts[symbol_key].append(transcript_payload)

    LOGGER.info(
        "Built transcript models: %d transcripts, %d transcript aliases, %d gene keys",
        len(transcript_models),
        len(transcript_alias_index),
        len(gene_to_transcripts),
    )
    LOGGER.info(
        "Built gene-symbol index for %d symbols", len(gene_symbol_to_transcripts)
    )

    return (
        transcript_models,
        transcript_alias_index,
        gene_to_transcripts,
        gene_symbol_to_transcripts,
    )

def collect_transcript_cds_candidates(
    db,
    gene_id,
    transcript_index,
    preferred_chrom,
    genome,
    breakpoint=None,
    cds_cache=None,
    transcript_alias_index=None,
    transcript_models=None,
    preferred_transcript_id=None,
    gene_symbol=None,
    gene_symbol_index=None,
    max_transcripts_per_gene=1,
):
    """Select up to max_transcripts_per_gene top-ranked transcript candidates."""
    if cds_cache is None:
        cds_cache = {}

    max_transcripts_per_gene = max(1, int(max_transcripts_per_gene))

    resolved_preferred = match_transcript_id(
        preferred_transcript_id,
        transcript_alias_index or {},
        transcript_models or {},
        preferred_chrom=preferred_chrom,
    )

    fallback_candidates = get_ranked_transcript_candidates(
        db,
        gene_id,
        transcript_index=transcript_index,
        preferred_chrom=preferred_chrom,
        breakpoint=breakpoint,
        gene_symbol=gene_symbol,
        gene_symbol_index=gene_symbol_index,
        transcript_models=transcript_models,
        preferred_transcript_id=resolved_preferred,
    )

    selected = []
    for transcript_rank, (transcript_id, chrom) in enumerate(
        fallback_candidates, start=1
    ):
        if preferred_chrom and not chrom_matches(preferred_chrom, chrom):
            continue

        if transcript_id in cds_cache:
            cds_seq, strand, segments = cds_cache[transcript_id]
        else:
            cds_seq, strand, segments = extract_cds_sequence(
                db, transcript_id, genome, chrom
            )
            cds_cache[transcript_id] = (cds_seq, strand, segments)

        if cds_seq and segments:
            model = (transcript_models or {}).get(transcript_id, {})
            selected.append(
                {
                    "transcript_id": transcript_id,
                    "chrom": chrom,
                    "cds": cds_seq,
                    "cds_length": len(cds_seq),
                    "strand": strand,
                    "segments": segments,
                    "exon_segments": model.get("exon_segments", []),
                    "cds_tx_segments": model.get("cds_tx_segments", []),
                    "transcript_rank": len(selected) + 1,
                    "original_transcript_candidate_rank": transcript_rank,
                    "cds_start_nf": bool(model.get("cds_start_nf")),
                    "cds_end_nf": bool(model.get("cds_end_nf")),
                    "cds_completeness": model.get("cds_completeness", "complete"),
                    "non_atg_start": bool(model.get("non_atg_start")),
                    "stop_codon_readthrough": bool(model.get("stop_codon_readthrough")),
                    "selenocysteine_feature_count": int(model.get("selenocysteine_feature_count") or 0),
                }
            )
    candidate_count = len(selected)
    selected = selected[:max_transcripts_per_gene]
    for candidate in selected:
        candidate["transcript_candidate_count"] = candidate_count
    return selected
