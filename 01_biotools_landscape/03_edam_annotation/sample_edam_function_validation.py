"""Create a reproducible blinded sample for manual EDAM-function validation.
This script reads a set of tool audits and a set of mapped operations, then selects 
a random sample of operations for each omics domain. 
The output is a TSV file with the selected operations and their associated tool metadata, 
along with a manifest JSON file containing metadata about the sampling process.

Example usage:
    python sample_edam_function_validation.py \
        --mapped-operations path/to/mapped_operations.tsv \
        --tool-audits path/to/tool_audit1.tsv path/to/tool_audit2.tsv \
        --output path/to/output_sample.tsv \
        --per-omic 50 \
        --seed 42
Where --tool-audits are *_all_records_quality_flags.tsv outputs from filter_biotools.py

"""

# 1. Imports and table helpers -----------------------------------------------

import argparse
import csv
import glob
import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


OMIC_DOMAINS = ("Genomics", "Transcriptomics", "Proteomics", "Multiomics")


VALID_STATUSES = {"Valid EDAM operation", "Obsolete EDAM operation"}


def annotation_key(row):
    """Return the full tool/domain/operation identity used for stable sampling."""
    return row["biotools_id"], row["omic_type"], (row.get("operation_uri_normalized") or "").strip()


def validate_identity(row, path, require_operation=False):
    """Check and normalise the tool/domain identity; return it as a key."""
    tool_id = (row.get("biotools_id") or "").strip()
    omic_domain = (row.get("omic_type") or "").strip()
    if not tool_id:
        raise ValueError(f"Missing biotools_id in {path}")
    if omic_domain not in OMIC_DOMAINS:
        raise ValueError(f"Invalid or missing omics domain {omic_domain!r} in {path}")
    row["biotools_id"] = tool_id
    row["omic_type"] = omic_domain
    if require_operation and not annotation_key(row)[2]:
        raise ValueError(f"Missing operation URI for {tool_id} / {omic_domain} in {path}")
    return tool_id, omic_domain


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path, require_annotation=False):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = set(reader.fieldnames or [])
        if not {"biotools_id", "omic_type"} <= fields:
            raise ValueError(f"Required tool/domain identifiers are missing from the header in {path}")
        if require_annotation and not {"operation_annotation_status", "operation_uri_normalized"} <= fields:
            raise ValueError(f"Required annotation columns are missing from the header in {path}")
        yield from reader


# 2. Configure the validation sample -----------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapped-operations", required=True)
    parser.add_argument("--tool-audits", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--per-omic", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.per_omic <= 0:
        parser.error("--per-omic must be a positive integer")
    return args


# 3. Read, sample and export validation records -------------------------------

def main() -> None:
    args = parse_args()

    mapped_path = Path(args.mapped_operations)
    audit_paths = list(dict.fromkeys(Path(input_path).resolve() for pattern in args.tool_audits
                                    for input_path in sorted(glob.glob(pattern) or [pattern])))
    tool_metadata = {}
    for path in audit_paths:
        for row in read_tsv(path):
            metadata_key = validate_identity(row, path)
            if metadata_key in tool_metadata and tool_metadata[metadata_key] != row:
                raise ValueError(f"Conflicting metadata for {metadata_key} in {path}")
            tool_metadata[metadata_key] = row

    def representative_key(item):
        return item.get("operation_group_uri", ""), item.get("operation_group_term", "")

    unique_annotations = {}
    for row in read_tsv(mapped_path, require_annotation=True):
        annotated = row.get("operation_annotation_status") in VALID_STATUSES
        metadata_key = validate_identity(row, mapped_path, require_operation=annotated)
        if not annotated:
            continue
        if metadata_key not in tool_metadata:
            raise ValueError(f"Missing tool audit for {metadata_key} in {mapped_path}")
        key = annotation_key(row)
        # One deterministic representative when a multi-parent operation maps
        # to several groups; identity and sample membership do not depend on order.
        if key not in unique_annotations or representative_key(row) < representative_key(unique_annotations[key]):
            unique_annotations[key] = row
    by_omic = defaultdict(list)
    for row in unique_annotations.values():
        by_omic[row["omic_type"]].append(row)

    rng = random.Random(args.seed)
    selected = []
    for omic, rows in sorted(by_omic.items()):
        rows = sorted(rows, key=annotation_key)
        selected.extend(rng.sample(rows, min(args.per_omic, len(rows))))

    fields = ["validation_id", "biotools_id", "tool_name", "omic_type", "operation_uri",
        "operation_term", "operation_group_uri", "operation_group_term", "ontology_depth",
        "homepage", "documentation", "publication_doi", "publication_pmid", "publication_pmcid", "description",
        "reviewer_1_decision", "reviewer_1_reason", "reviewer_2_decision", "reviewer_2_reason",
        "consensus_decision", "consensus_reason"]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for index, row in enumerate(selected, 1):
            tool = tool_metadata[(row["biotools_id"], row["omic_type"])]
            writer.writerow({
                "validation_id": f"FV{index:04d}", "biotools_id": row.get("biotools_id", ""),
                "tool_name": row.get("name", tool.get("name", "")), "omic_type": row.get("omic_type", ""),
                "operation_uri": row.get("operation_uri_normalized", ""),
                "operation_term": row.get("operation_term_pinned", ""),
                "operation_group_uri": row.get("operation_group_uri", ""),
                "operation_group_term": row.get("operation_group_term", ""),
                "ontology_depth": row.get("operation_ontology_depth", ""),
                "homepage": tool.get("homepage", ""), "documentation": tool.get("documentation", ""),
                "publication_doi": tool.get("publication_doi", ""), "publication_pmid": tool.get("publication_pmid", ""), "publication_pmcid": tool.get("publication_pmcid", ""), "description": tool.get("description", ""),
            })
    manifest = {"pipeline": "Manual EDAM function-validation sampling",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(), "seed": args.seed,
        "per_omic_requested": args.per_omic, "sample_rows": len(selected),
        "mapped_operations": {"path": str(mapped_path.resolve()), "md5": md5(mapped_path)},
        "tool_audits": [{"path": str(input_path.resolve()), "md5": md5(input_path)} for input_path in audit_paths],
        "output": {"path": str(output_path.resolve()), "md5": md5(output_path)},
        "allowed_decisions": ["Correct", "Partially correct", "Too broad", "Incorrect", "Unable to determine"]}
    with output_path.with_suffix(output_path.suffix + ".manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)


# 4. Command-line entry point ------------------------------------------------

if __name__ == "__main__":
    main()
