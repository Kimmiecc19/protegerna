"""Shared GENCODE transcript-model loading for splice producers."""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple, Optional

import gffutils


LOGGER = logging.getLogger(__name__)


class ChildFeature(NamedTuple):
    start: int
    end: int
    strand: str
    frame: Optional[str]
    score: Optional[str]


def child_features_by_parent(database, featuretypes) -> dict[str, dict[str, list[ChildFeature]]]:
    """Return ``{parent_id: {featuretype: [ChildFeature, ...]}}`` from one SQL query.

    Equivalent to calling ``database.children(parent, featuretype=..., order_by="start")``
    for every parent, but avoids one query per transcript and feature type
    (hundreds of thousands of queries for a GENCODE database). Features are
    returned ordered by genomic start, as ``order_by="start"`` would.
    """
    featuretypes = tuple(featuretypes)
    placeholders = ",".join("?" for _ in featuretypes)
    query = (
        "SELECT DISTINCT relations.parent, features.id, features.featuretype, "
        "features.start, features.end, features.strand, features.frame, features.score "
        "FROM features JOIN relations ON relations.child = features.id "
        f"WHERE features.featuretype IN ({placeholders}) ORDER BY features.start"
    )
    grouped: dict[str, dict[str, list[ChildFeature]]] = defaultdict(lambda: defaultdict(list))
    for parent, _feature_id, featuretype, start, end, strand, frame, score in database.conn.execute(query, featuretypes):
        grouped[parent][featuretype].append(ChildFeature(int(start), int(end), strand, frame, score))
    return grouped




def build_transcript_models(gtf_db: str) -> dict[str, dict]:
    """Load transcript, exon, CDS phase, completeness, and special features."""
    db_path = Path(gtf_db)
    if not db_path.is_file():
        raise ValueError(f"Prebuilt gffutils DB not found: {gtf_db}")
    started = time.time()
    database = gffutils.FeatureDB(str(db_path), keep_order=True)
    LOGGER.info("Loaded gffutils DB %s in %.2fs", db_path, time.time() - started)

    transcripts: dict[str, dict] = {}
    children = child_features_by_parent(database, ("exon", "CDS", "Selenocysteine"))
    empty: dict[str, list[ChildFeature]] = {}
    for transcript in database.features_of_type("transcript"):
        transcript_id = transcript.attributes.get("transcript_id", [transcript.id])[0]
        gene_id = transcript.attributes.get("gene_id", ["NA"])[0]
        gene_name = next((
            transcript.attributes[key][0]
            for key in ("gene_name", "gene_symbol", "gene")
            if transcript.attributes.get(key) and transcript.attributes[key][0]
        ), None)
        features = children.get(transcript.id, empty)
        exons = [(feature.start, feature.end) for feature in features.get("exon", ())]
        cds = []
        for feature in features.get("CDS", ()):
            try:
                phase = int(feature.frame) if feature.frame not in (None, "", ".") else None
            except (TypeError, ValueError):
                phase = None
            cds.append((feature.start, feature.end, phase))
        tags = transcript.attributes.get("tag", [])
        transcript_type = next((
            transcript.attributes[key][0]
            for key in ("transcript_type", "transcript_biotype")
            if transcript.attributes.get(key)
        ), None)
        transcripts[transcript_id] = {
            "transcript_id": transcript_id,
            "gene_id": gene_id,
            "gene_name": gene_name,
            "chrom": transcript.chrom,
            "strand": transcript.strand,
            "exons": sorted(exons),
            "cds": sorted(cds),
            "transcript_type": transcript_type,
            "tags": list(tags),
            "transcript_support_level": transcript.attributes.get("transcript_support_level", [None])[0],
            "cds_start_nf": "cds_start_NF" in tags,
            "cds_end_nf": "cds_end_NF" in tags,
            "non_atg_start": "non_ATG_start" in tags,
            "stop_codon_readthrough": "stop_codon_readthrough" in tags,
            "selenocysteine_intervals": [
                (feature.start, feature.end) for feature in features.get("Selenocysteine", ())
            ],
        }

    for transcript_id in list(transcripts):
        if "." in transcript_id:
            alias = transcript_id.split(".", 1)[0]
            if alias not in transcripts:
                transcripts[alias] = dict(transcripts[transcript_id], transcript_id=alias)
    LOGGER.info("Parsed %d transcripts including versionless aliases", len(transcripts))
    return transcripts
