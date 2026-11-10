"""Map bio.tools EDAM operations to reproducible ontology-derived ancestors.
This script is intended to be run from the 03_edam_annotation pipeline, but can also be run independently. 
It reads one or more normalised function TSV files, resolves the EDAM operation URIs against a retained 
EDAM OWL snapshot, and exports a long-format TSV with the original function records augmented with the 
pinned EDAM term, ontology depth, and high-level operation group(s). 
A crosswalk TSV is also produced to document the observed EDAM operations and their pinned ancestors.

Notes:
The input is one or more *.functions.tsv files produced by
fetch_biotools.py or *_function_operations.tsv files produced by the R
filter. The EDAM OWL snapshot is retained locally and identified by checksum.
No categories are inferred from tool descriptions or topics.

Usage (from 03_edam_annotation):
python map_edam_operations.py \
  --input "../02_filter_biotools/results_filter_biotools/*_all_function_operations.tsv" \
  --output results_edam_annotation/all_edam_operations_mapped.tsv \
  --crosswalk-output results_edam_annotation/edam_operation_crosswalk.tsv \
  --edam-owl edam/EDAM.owl \
  --aggregation-depth 1

Add --download-edam to retain a new snapshot at --edam-owl.
"""
from __future__ import annotations

# 1. Imports and ontology constants -------------------------------------------

import argparse
import csv
import hashlib
import glob
import json
import platform
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
DEFAULT_EDAM_URL = "https://edamontology.org/EDAM.owl"

FUNCTION_COLUMNS = [
    "biotools_id", "name", "retrieval_query", "function_index", "operation_index",
    "operation_term", "operation_uri", "input_data_terms", "input_data_uris",
    "input_format_terms", "input_format_uris", "output_data_terms", "output_data_uris",
    "output_format_terms", "output_format_uris", "input_json", "output_json",
    "omic_type", "canonical_record_id", "flag_duplicate_record", "scope_classification",
    "scope_reason", "flag_scope_review", "flag_scope_out_of_scope", "flag_topic_exclusion",
    "source_function_file",
]
MAPPING_COLUMNS = [
    "operation_uri_normalized", "operation_term_pinned", "operation_annotation_status",
    "operation_obsolete", "operation_ontology_depth", "operation_group_uri",
    "operation_group_term", "operation_group_depth",
]


# 2. Snapshot checksums and URI normalisation ---------------------------------

def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_uri(uri: str) -> str:
    uri = (uri or "").strip()
    return uri.replace("https://edamontology.org/", "http://edamontology.org/")


def download_snapshot(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "EDAM-operation-mapper/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
        output.write(response.read())


# 3. Parse operation classes and ontology relationships -----------------------

def parse_edam(path: Path) -> Tuple[Dict[str, str], Dict[str, Set[str]], Set[str]]:
    tree = ET.parse(path)
    labels: Dict[str, str] = {}
    parents: Dict[str, Set[str]] = defaultdict(set)
    obsolete: Set[str] = set()
    for element in tree.iter():
        uri = normalize_uri(element.attrib.get(f"{{{RDF}}}about", ""))
        if "/operation_" not in uri:
            continue
        label = element.find(f"{{{RDFS}}}label")
        if label is not None and label.text:
            labels[uri] = label.text.strip()
        for parent in element.findall(f"{{{RDFS}}}subClassOf"):
            parent_uri = normalize_uri(parent.attrib.get(f"{{{RDF}}}resource", ""))
            if "/operation_" in parent_uri:
                parents[uri].add(parent_uri)
        deprecated = element.find(f"{{{OWL}}}deprecated")
        if deprecated is not None and (deprecated.text or "").strip().lower() == "true":
            obsolete.add(uri)
        labels.setdefault(uri, uri.rsplit("/", 1)[-1])
    if not labels:
        raise ValueError(f"No EDAM Operation classes were found in {path}")
    return labels, parents, obsolete


# 4. Compute depths and ancestor groups ---------------------------------------

def calculate_depths(labels: Dict[str, str], parents: Dict[str, Set[str]]) -> Dict[str, int]:
    children: Dict[str, Set[str]] = defaultdict(set)
    roots = []
    for child in labels:
        operation_parents = parents.get(child, set()) & labels.keys()
        if not operation_parents:
            roots.append(child)
        for parent in operation_parents:
            children[parent].add(child)
    depths = {root: 0 for root in roots}
    queue = deque(roots)
    while queue:
        parent = queue.popleft()
        for child in children.get(parent, set()):
            proposed = depths[parent] + 1
            if child not in depths or proposed < depths[child]:
                depths[child] = proposed
                queue.append(child)
    return depths


def ancestors_at_depth(uri: str, target_depth: int, parents: Dict[str, Set[str]],
                       depths: Dict[str, int]) -> Set[str]:
    if uri not in depths:
        return set()
    if depths[uri] <= target_depth:
        return {uri}
    found: Set[str] = set()
    queue = deque([uri])
    seen = {uri}
    while queue:
        current = queue.popleft()
        for parent in parents.get(current, set()):
            if parent in seen:
                continue
            seen.add(parent)
            if depths.get(parent) == target_depth:
                found.add(parent)
            elif depths.get(parent, -1) > target_depth:
                queue.append(parent)
    return found


# 5. Read normalised function records -----------------------------------------

def read_rows(paths: Iterable[Path]) -> Iterable[dict]:
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                row["source_function_file"] = str(path)
                yield row


def first_value(row: dict, *names: str) -> str:
    """First non-empty value; Title Case names cover older fetch headers."""
    for name in names:
        if row.get(name):
            return row[name]
    return ""


# 6. Map operations and export auditable outputs ------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True, help="Normalised function TSV file(s)")
    parser.add_argument("--output", required=True, help="Mapped long-format TSV")
    parser.add_argument("--crosswalk-output", required=True, help="EDAM operation crosswalk TSV")
    parser.add_argument("--edam-owl", required=True, help="Local EDAM OWL snapshot to use or create")
    parser.add_argument("--download-edam",
        action="store_true",
        help="Download and retain a new EDAM snapshot")
    parser.add_argument("--edam-url", default=DEFAULT_EDAM_URL)
    parser.add_argument("--aggregation-depth", type=int, default=1,
                        help="Ontology depth used for high-level operation groups")
    args = parser.parse_args()
    if args.aggregation_depth < 0:
        parser.error("--aggregation-depth must be nonnegative")
    return args


def main() -> None:
    args = parse_args()

    # 6.1 Load the retained ontology snapshot -------------------------------------

    owl_path = Path(args.edam_owl)
    if args.download_edam:
        if owl_path.exists():
            raise FileExistsError(f"Refusing to overwrite retained ontology snapshot: {owl_path}")
        download_snapshot(args.edam_url, owl_path)
    if not owl_path.exists():
        raise FileNotFoundError("EDAM OWL snapshot not found; supply it or use --download-edam")

    labels, parents, obsolete = parse_edam(owl_path)
    depths = calculate_depths(labels, parents)
    output_path = Path(args.output)
    crosswalk_path = Path(args.crosswalk_output)
    for path in (output_path, crosswalk_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    # 6.2 Resolve input patterns and map each annotation --------------------------
    # Missing and unresolved URIs remain explicit audit categories.

    expanded_inputs: List[str] = []
    for pattern in args.input:
        matches = sorted(glob.glob(pattern))
        expanded_inputs.extend(matches or [pattern])
    input_paths = list(dict.fromkeys(Path(input_path).resolve() for input_path in expanded_inputs))
    missing_inputs = [str(input_path) for input_path in input_paths if not input_path.exists()]
    if missing_inputs:
        raise FileNotFoundError("Function input file(s) not found: " + ", ".join(missing_inputs))

    group_cache: Dict[str, List[str]] = {}

    def operation_groups(uri):
        if uri not in group_cache:
            group_cache[uri] = sorted(ancestors_at_depth(uri, args.aggregation_depth, parents, depths)) or [uri]
        return group_cache[uri]

    mapped_rows: List[dict] = []
    observed_uris: Set[str] = set()
    for row in read_rows(input_paths):
        uri = normalize_uri(first_value(row, "operation_uri", "Operation URI"))
        status = "Valid EDAM operation"
        if not uri:
            status = "Operation URI missing"
            groups = [""]
        elif uri not in labels:
            status = "Operation URI unresolved in pinned EDAM version"
            groups = [""]
        else:
            observed_uris.add(uri)
            if uri in obsolete:
                status = "Obsolete EDAM operation"
            groups = operation_groups(uri)
        for group_uri in groups:
            mapped = dict(row)
            mapped.update({
                "operation_uri_normalized": uri,
                "operation_term_pinned": labels.get(uri, first_value(row, "operation_term", "Operation Term")),
                "operation_annotation_status": status,
                "operation_obsolete": uri in obsolete if uri else False,
                "operation_ontology_depth": depths.get(uri, ""),
                "operation_group_uri": group_uri,
                "operation_group_term": labels.get(group_uri, "") if group_uri else "",
                "operation_group_depth": depths.get(group_uri, "") if group_uri else "",
            })
            mapped_rows.append(mapped)

    # 6.3 Export mapped records and the ontology crosswalk ------------------------

    # Retain additional audit columns in first-seen order; empty inputs still
    # expose the complete documented schema for downstream readers.
    extra_columns = list(dict.fromkeys(key for row in mapped_rows for key in row
                                      if key not in FUNCTION_COLUMNS + MAPPING_COLUMNS))
    base_fields = FUNCTION_COLUMNS + extra_columns + MAPPING_COLUMNS
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=base_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(mapped_rows)

    crosswalk_fields = ["operation_uri", "operation_term", "obsolete", "ontology_depth",
                        "operation_group_uri", "operation_group_term", "operation_group_depth"]
    with crosswalk_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=crosswalk_fields, delimiter="\t")
        writer.writeheader()
        for uri in sorted(observed_uris):
            for group_uri in operation_groups(uri):
                writer.writerow({"operation_uri": uri, "operation_term": labels.get(uri, ""),
                    "obsolete": uri in obsolete, "ontology_depth": depths.get(uri, ""),
                    "operation_group_uri": group_uri, "operation_group_term": labels.get(group_uri, ""),
                    "operation_group_depth": depths.get(group_uri, "")})

    # 6.4 Record snapshot, parameters, and file checksums -------------------------

    manifest = {
        "pipeline": "EDAM operation hierarchy mapping",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(Path(__file__).resolve()),
        "python": sys.version,
        "platform": platform.platform(),
        "ontology": {"path": str(owl_path.resolve()), "md5": md5(owl_path),
                     "source_url": args.edam_url if args.download_edam else None},
        "parameters": {"aggregation_depth": args.aggregation_depth,
                       "mapping_relation": "rdfs:subClassOf"},
        "inputs": [{"path": str(input_path.resolve()), "md5": md5(input_path)} for input_path in input_paths],
        "outputs": {"mapped": {"path": str(output_path.resolve()), "md5": md5(output_path)},
                    "crosswalk": {"path": str(crosswalk_path.resolve()), "md5": md5(crosswalk_path)}},
        "counts": {"mapped_rows": len(mapped_rows), "observed_valid_operation_uris": len(observed_uris),
                   "edam_operation_classes": len(labels)},
    }
    with output_path.with_suffix(output_path.suffix + ".manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)


# 7. Command-line entry point -------------------------------------------------

if __name__ == "__main__":
    main()
