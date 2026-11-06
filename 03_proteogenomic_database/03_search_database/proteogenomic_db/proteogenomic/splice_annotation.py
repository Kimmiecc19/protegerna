"""Shared GENCODE transcript-model loading for splice producers."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import gffutils


LOGGER = logging.getLogger(__name__)


def build_transcript_models(gtf_db: str) -> dict[str, dict]:
    """Load transcript, exon, CDS phase, completeness, and special features."""
    db_path = Path(gtf_db)
    if not db_path.is_file():
        raise ValueError(f"Prebuilt gffutils DB not found: {gtf_db}")
    started = time.time()
    database = gffutils.FeatureDB(str(db_path), keep_order=True)
    LOGGER.info("Loaded gffutils DB %s in %.2fs", db_path, time.time() - started)

    transcripts: dict[str, dict] = {}
    for transcript in database.features_of_type("transcript"):
        transcript_id = transcript.attributes.get("transcript_id", [transcript.id])[0]
        gene_id = transcript.attributes.get("gene_id", ["NA"])[0]
        gene_name = next((
            transcript.attributes[key][0]
            for key in ("gene_name", "gene_symbol", "gene")
            if transcript.attributes.get(key) and transcript.attributes[key][0]
        ), None)
        exons = [
            (int(feature.start), int(feature.end))
            for feature in database.children(transcript, featuretype="exon", order_by="start")
        ]
        cds = []
        for feature in database.children(transcript, featuretype="CDS", order_by="start"):
            try:
                phase = int(feature.frame) if feature.frame not in (None, "", ".") else None
            except (TypeError, ValueError):
                phase = None
            cds.append((int(feature.start), int(feature.end), phase))
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
                (int(feature.start), int(feature.end))
                for feature in database.children(
                    transcript, featuretype="Selenocysteine", order_by="start"
                )
            ],
        }

    for transcript_id in list(transcripts):
        if "." in transcript_id:
            alias = transcript_id.split(".", 1)[0]
            if alias not in transcripts:
                transcripts[alias] = dict(transcripts[transcript_id], transcript_id=alias)
    LOGGER.info("Parsed %d transcripts including versionless aliases", len(transcripts))
    return transcripts
