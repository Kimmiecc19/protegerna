#!/usr/bin/env python3
"""
sv_review_extract.py
====================

Step 1 of the alignment-free technical review of prioritised structural variants.

Extracts, from the raw per-participant caller VCFs (bcftools concat of Manta and
TIDDIT), every raw record that matches an event in the manual-review shortlists:

  * Supplementary_Table_filtered_intersection_manual_review_shortlist.tsv
  * Supplementary_Table_filtered_union_only_manual_review_shortlist.tsv

Every VCF is read once. Records are matched to shortlist events by chromosome,
compatible SV type and either reciprocal overlap or breakpoint distance. Raw
records are extracted for recorded carriers AND non-carriers, so the output also
supports the consolidation-fidelity audit (carriers without a raw call;
non-carriers with a raw call).

Outputs (in --out-dir):
  review_events.tsv          normalised event list (both shortlists)
  raw_record_matches.tsv     one row per (event, participant, matched raw record)
  carrier_status.tsv         one row per (event, recorded carrier), incl. carriers
                             with no matching raw record
  vcf_manifest.tsv           VCF file -> participant ID, record counts
  header_definitions.tsv     INFO/FORMAT/FILTER definitions found in the VCF headers
  run_log.json               parameters, input checksums, timings

Only the Python standard library is required.

Example (from 02_SV_analysis/05_sv_audit/):
  python 01b_extract_raw_calls.py \
      --intersection-tsv ../04_sv_prioritization/02c_results_prioritise_annotsv_events/intersection_filtered/Supplementary_Table_intersection_manual_review_shortlist.tsv \
      --input-dir 01a_fixed_vcf_names/fixed_vcf_names --vcf-glob '*.vcf.gz' \
      --out-dir 01bc_results_raw_call_review/intersection_filtered --padding 500 --min-ro 0.5
"""

from __future__ import annotations

import argparse
import bisect
import csv
import datetime as _dt
import gzip
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

__version__ = "1.0.0"

SAMPLE_ID_RE = re.compile(r"(CASE|CTRL)-NEU[A-Z0-9]+-\d+(?:-[A-Z])?")
TIER_RE = re.compile(r"(\d+)")

# Raw-record columns written to raw_record_matches.tsv
RAW_COLS = ["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT", "SAMPLE_VALUES"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def normalize_chrom(chrom: str) -> str:
    chrom = str(chrom).strip()
    return chrom[3:] if chrom.lower().startswith("chr") else chrom


def normalize_sv_type(sv_type: str) -> str:
    """Collapse caller-specific SV type spellings to DEL/DUP/INS/INV/BND."""
    sv_type = (sv_type or "").upper().strip("<>")
    if sv_type.startswith("DEL"):
        return "DEL"
    if sv_type.startswith("DUP") or sv_type in {"TDUP", "CNV_GAIN"}:
        return "DUP"
    if sv_type.startswith("INS"):
        return "INS"
    if sv_type.startswith("INV"):
        return "INV"
    if sv_type in {"BND", "TRA", "CTX"}:
        return "BND"
    return sv_type or "NA"


# Which raw-record types may represent a shortlist event of a given type.
# BND is allowed for INV only when both breakends are on the same chromosome
# (Manta reports inversions as paired BND records by default).
COMPATIBLE = {
    "DEL": {"DEL"},
    "DUP": {"DUP"},
    "INS": {"INS"},
    "INV": {"INV", "BND"},
}


def md5sum(path: Path, block: int = 1 << 20) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(block), b""):
            digest.update(chunk)
    return digest.hexdigest()


def open_text(path: Path):
    if str(path).endswith((".gz", ".bgz")):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "rt", encoding="utf-8", errors="replace")


def parse_info(info: str) -> dict:
    out = {}
    if info in ("", "."):
        return out
    for item in info.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            out[key] = value
        else:
            out[item] = True
    return out


def to_int(value, default=None):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def split_ids(value) -> list[str]:
    if value is None:
        return []
    value = str(value).strip()
    if value in ("", "nan", "NA", "."):
        return []
    return [sample_id.strip() for sample_id in re.split(r"[;,|\s]+", value) if sample_id.strip()]


def parse_tier(value) -> str:
    m = TIER_RE.search(str(value or ""))
    return m.group(1) if m else ""


# --------------------------------------------------------------------------- #
# Shortlists
# --------------------------------------------------------------------------- #
def read_tsv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_events(intersection: Path | None, union: Path | None) -> list[dict]:
    events = []
    for path, shortlist, prefix in ((intersection, "intersection", "INT"), (union, "union_only", "UO")):
        for row in read_tsv(path) if path else []:
            samples = split_ids(row.get("samples"))
            case = [sample_id for sample_id in samples if sample_id.startswith("CASE")]
            control = [sample_id for sample_id in samples if sample_id.startswith("CTRL")]
            events.append({
                "shortlist": shortlist,
                "event_id": row["event_id"],
                "review_event_id": f"{prefix}-{row['event_id']}",
                "review_rank": row.get("review_rank", ""),
                "tier": parse_tier(row.get("prioritisation_tier")),
                "chrom": normalize_chrom(row["chrom"]),
                "start": to_int(row["start"]),
                "end": to_int(row["end"]),
                "sv_length_bp": to_int(row.get("sv_length_bp")),
                "sv_type": normalize_sv_type(row["sv_type"]),
                **{key: row.get(key, "") for key in ("genes", "highest_alsod_evidence", "max_annotsv_ranking_score",
                                                     "acmg_classes", "octopusv_record_ids")},
                "case_carriers": ";".join(case),
                "control_carriers": ";".join(control),
                "recorded_carriers": ";".join(case + control),
                "n_recorded_carriers": len(case) + len(control),
            })

    bad = [event["event_id"] for event in events if event["start"] is None or event["end"] is None]
    if bad:
        sys.exit(f"ERROR: events with missing coordinates: {bad[:5]}")
    for event in events:
        if event["end"] < event["start"]:
            event["start"], event["end"] = event["end"], event["start"]
    return events


class EventIndex:
    """Per-chromosome index of events sorted by start for fast overlap lookup."""

    def __init__(self, events: list[dict], padding: int):
        self.padding = padding
        self.by_chrom: dict[str, list[dict]] = defaultdict(list)
        for event in events:
            self.by_chrom[event["chrom"]].append(event)
        self.starts = {}
        self.max_len = {}
        for chromosome, chromosome_events in self.by_chrom.items():
            chromosome_events.sort(key=lambda event: event["start"])
            self.starts[chromosome] = [event["start"] for event in chromosome_events]
            self.max_len[chromosome] = max(event["end"] - event["start"] for event in chromosome_events)

    def candidates(self, chrom: str, start: int, end: int):
        chromosome_events = self.by_chrom.get(chrom)
        if not chromosome_events:
            return []
        lo = bisect.bisect_left(self.starts[chrom], start - self.max_len[chrom] - self.padding)
        hi = bisect.bisect_right(self.starts[chrom], end + self.padding)
        return chromosome_events[lo:hi]


# --------------------------------------------------------------------------- #
# Raw record interpretation and matching
# --------------------------------------------------------------------------- #
BND_MATE_RE = re.compile(r"[\[\]]([^:\[\]]+):(\d+)[\[\]]")


def record_interval(chrom: str, pos: int, alt: str, info: dict):
    """Return (svtype, start, end, svlen, mate_chrom) for a raw SV record."""
    svtype = normalize_sv_type(info.get("SVTYPE") or alt)
    end = to_int(info.get("END"))
    svlen = to_int(info.get("SVLEN"))
    mate_chrom = ""
    if svtype == "BND":
        m = BND_MATE_RE.search(alt)
        if m:
            mate_chrom = normalize_chrom(m.group(1))
            mate_pos = int(m.group(2))
            if mate_chrom == chrom:
                end = mate_pos
    if end is None:
        end = pos + abs(svlen) if svlen is not None and svtype != "INS" else pos
    start, end = min(pos, end), max(pos, end)
    if svlen is None and svtype in {"DEL", "DUP", "INV"}:
        svlen = end - start
    return svtype, start, end, svlen, mate_chrom


def reciprocal_overlap(a0, a1, b0, b1) -> float:
    ov = min(a1, b1) - max(a0, b0)
    if ov <= 0:
        return 0.0
    la, lb = max(a1 - a0, 1), max(b1 - b0, 1)
    return min(ov / la, ov / lb)


def match_record(event: dict, record_type: str, record_start: int, record_end: int, mate_chrom: str,
                 padding: int, min_ro: float, any_type: bool):
    """Return match descriptor dict or None."""
    type_ok = any_type or record_type in COMPATIBLE.get(event["sv_type"], {event["sv_type"]})
    if record_type == "BND" and event["sv_type"] == "INV" and mate_chrom and mate_chrom != event["chrom"]:
        type_ok = False
    if not type_ok:
        return None
    start_difference = record_start - event["start"]
    end_difference = record_end - event["end"]
    if event["sv_type"] == "INS" or record_type == "INS":
        if abs(start_difference) <= padding:
            return {"match_type": "insertion_position", "reciprocal_overlap": "",
                    "start_diff": start_difference, "end_diff": end_difference}
        return None
    overlap_fraction = reciprocal_overlap(event["start"], event["end"], record_start, record_end)
    bp_ok = abs(start_difference) <= padding and abs(end_difference) <= padding
    if overlap_fraction >= min_ro or bp_ok:
        if overlap_fraction >= min_ro and bp_ok:
            match_type = "overlap_and_breakpoints"
        elif overlap_fraction >= min_ro:
            match_type = "reciprocal_overlap"
        else:
            match_type = "breakpoint_distance"
        return {"match_type": match_type, "reciprocal_overlap": round(overlap_fraction, 4),
                "start_diff": start_difference, "end_diff": end_difference}
    return None


def caller_of(record_id: str, info: dict, vcf_name: str) -> str:
    src = str(info.get("SOURCE", "")).lower()
    rid = record_id.lower()
    if "tiddit" in src or rid.startswith("sv_"):
        return "TIDDIT"
    if "manta" in src or rid.startswith("manta"):
        return "Manta"
    name = vcf_name.lower()
    if "tiddit" in name:
        return "TIDDIT"
    if "manta" in name:
        return "Manta"
    return "unknown"


# --------------------------------------------------------------------------- #
# VCF discovery and sample resolution
# --------------------------------------------------------------------------- #
def find_vcfs(vcf_dir: Path, pattern: str) -> list[Path]:
    files = sorted(vcf_path for vcf_path in vcf_dir.rglob(pattern)
                   if vcf_path.is_file() and not vcf_path.name.endswith((".tbi", ".csi", ".idx")))
    copies = defaultdict(list)
    for path in files:
        copies[path.with_suffix("") if path.suffix == ".gz" else path].append(path)
    duplicates = [paths for paths in copies.values() if len(paths) > 1]
    if duplicates:
        details = "; ".join(", ".join(str(path) for path in paths) for paths in duplicates)
        raise ValueError(f"Compressed and uncompressed VCF copies both selected: {details}. "
                         "Select one representation with --vcf-glob.")
    return files


def resolve_sample(header_sample: str, path: Path, first_info: dict | None):
    identities = {}
    for label, text in (("header", header_sample), ("filename", path.name),
                        ("path", str(path)),
                        ("INFO/SOURCE", str((first_info or {}).get("SOURCE", "")))):
        matches = {match.group(0) for match in SAMPLE_ID_RE.finditer(text or "")}
        if label == "header" and text and not matches:
            matches = {text}
        for sample_id in matches:
            identities.setdefault(sample_id, []).append(label)
    if len(identities) > 1:
        raise ValueError(f"Conflicting sample identities in {path}: {identities}")
    if identities:
        sample_id = next(iter(identities))
        return sample_id, identities[sample_id][0]
    return header_sample or path.name, "unresolved"


HEADER_DEF_RE = re.compile(r'^##(INFO|FORMAT|FILTER)=<ID=([^,>]+)(.*)>$')
HEADER_ATTR_RE = {"number": re.compile(r"Number=([^,>]+)"), "type": re.compile(r"Type=([^,>]+)"),
                  "description": re.compile(r'Description="([^"]*)"')}


def record_header_definition(line: str, header_defs: dict, vcf_name: str) -> None:
    """Keep the first INFO/FORMAT/FILTER definition seen for each ID."""
    found = HEADER_DEF_RE.match(line.strip())
    if not found:
        return
    kind, fid, rest = found.groups()
    if (kind, fid) not in header_defs:
        attrs = {name: (m.group(1) if (m := pattern.search(rest)) else "") for name, pattern in HEADER_ATTR_RE.items()}
        header_defs[kind, fid] = {"section": kind, "id": fid, **attrs, "first_seen_in": vcf_name}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--intersection-tsv", "--intersection", dest="intersection_tsv", type=Path, help="Intersection manual-review shortlist TSV")
    parser.add_argument("--union-tsv", "--union", dest="union_tsv", type=Path, help="Union-only manual-review shortlist TSV")
    parser.add_argument("--input-dir", "--vcf-dir", dest="input_dir", type=Path, required=True, help="Directory with raw per-participant VCFs (searched recursively)")
    parser.add_argument("--vcf-glob", default="*.vcf*", help="Filename pattern for raw VCFs (default: *.vcf*)")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--padding", type=int, default=500,
                    help="Max breakpoint distance (bp) for a breakpoint-distance or insertion match (default 500)")
    parser.add_argument("--min-ro", type=float, default=0.5, help="Minimum reciprocal overlap (default 0.5)")
    parser.add_argument("--carriers-only", action="store_true",
                    help="Only read VCFs of recorded carriers (faster; disables the non-carrier fidelity check)")
    parser.add_argument("--any-type", action="store_true", help="Do not require compatible SV types")
    parser.add_argument("--no-checksums", action="store_true", help="Skip md5 checksums of inputs in run_log.json")
    args = parser.parse_args(argv)

    if not args.intersection_tsv and not args.union_tsv:
        parser.error("provide --intersection-tsv and/or --union-tsv")
    started_at = _dt.datetime.now()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    events = load_events(args.intersection_tsv, args.union_tsv)
    index = EventIndex(events, args.padding)
    carriers_by_event = {(event_row["shortlist"], event_row["event_id"]): set(split_ids(event_row["recorded_carriers"])) for event_row in events}
    all_carriers = set().union(*carriers_by_event.values()) if carriers_by_event else set()
    print(f"[info] {len(events)} events loaded "
          f"({sum(event_row['shortlist']=='intersection' for event_row in events)} intersection, "
          f"{sum(event_row['shortlist']=='union_only' for event_row in events)} union-only); "
          f"{len(all_carriers)} distinct recorded carriers")

    vcfs = find_vcfs(args.input_dir, args.vcf_glob)
    if not vcfs:
        sys.exit(f"ERROR: no files matching {args.vcf_glob} under {args.input_dir}")
    print(f"[info] {len(vcfs)} VCF files found")

    header_defs = {}
    manifest = []
    matches = []
    samples_seen = defaultdict(list)

    for i, path in enumerate(vcfs, 1):
        n_records = n_matched = 0
        sample_id, how = None, None
        with open_text(path) as handle:
            header_sample = ""
            for line in handle:
                if line.startswith("##"):
                    record_header_definition(line, header_defs, path.name)
                    continue
                if line.startswith("#CHROM"):
                    cols = line.rstrip("\n").split("\t")
                    header_sample = cols[9] if len(cols) > 9 else ""
                    if len(cols) > 10:
                        raise ValueError(f"Expected one sample in {path}; found {len(cols)-9}")
                    continue
                fields = line.rstrip("\n").split("\t")
                if len(fields) < 8:
                    continue
                n_records += 1
                info = parse_info(fields[7])
                resolved_id, resolved_source = resolve_sample(header_sample, path, info)
                if sample_id is not None and resolved_id != sample_id:
                    raise ValueError(f"Sample identity changes within {path}: {sample_id} -> {resolved_id}")
                if sample_id is None:
                    sample_id, how = resolved_id, resolved_source
                    samples_seen[sample_id].append(path.name)
                    if args.carriers_only and sample_id not in all_carriers:
                        break
                chrom = normalize_chrom(fields[0])
                pos = to_int(fields[1])
                rtype, rstart, rend, rsvlen, mate_chrom = record_interval(chrom, pos, fields[4], info)
                for event in index.candidates(chrom, rstart, rend):
                    match = match_record(event, rtype, rstart, rend, mate_chrom,
                                         args.padding, args.min_ro, args.any_type)
                    if not match:
                        continue
                    n_matched += 1
                    key = (event["shortlist"], event["event_id"])
                    oct_ids = set(split_ids(event["octopusv_record_ids"]))
                    matches.append({
                        "shortlist": event["shortlist"],
                        "event_id": event["event_id"],
                        "review_event_id": event["review_event_id"],
                        "tier": event["tier"],
                        "event_sv_type": event["sv_type"],
                        "event_chrom": event["chrom"],
                        "event_start": event["start"],
                        "event_end": event["end"],
                        "sample_id": sample_id,
                        "group": sample_id.split("-")[0] if "-" in sample_id else "",
                        "recorded_carrier": "yes" if sample_id in carriers_by_event[key] else "no",
                        "caller": caller_of(fields[2], info, path.name),
                        "raw_sv_type": rtype,
                        "raw_start": rstart,
                        "raw_end": rend,
                        "raw_svlen": "" if rsvlen is None else rsvlen,
                        **match,
                        "id_matches_octopusv_record": "yes" if fields[2] in oct_ids else "no",
                        "vcf_file": path.name,
                        **dict(zip(RAW_COLS, fields[:9] + [fields[9] if len(fields) > 9 else ""])),
                    })
        if sample_id is None:
            sample_id, how = resolve_sample(header_sample, path, None)
            samples_seen[sample_id].append(path.name)
        manifest.append({"vcf_file": str(path), "sample_id": sample_id, "sample_id_source": how,
                         "is_recorded_carrier_of_any_event": "yes" if sample_id in all_carriers else "no",
                         "n_records_read": n_records, "n_matched_records": n_matched})
        if i % 25 == 0 or i == len(vcfs):
            print(f"[info] {i}/{len(vcfs)} VCFs processed; {len(matches)} matched records so far")

    # Carrier status: every recorded carrier x event, including carriers with no raw match
    found = defaultdict(lambda: defaultdict(int))
    for match in matches:
        found[(match["shortlist"], match["event_id"], match["sample_id"])][match["caller"]] += 1
    have_vcf = set(samples_seen)
    carrier_rows = []
    for event_row in events:
        for sample_id in split_ids(event_row["recorded_carriers"]):
            carrier_row = found.get((event_row["shortlist"], event_row["event_id"], sample_id), {})
            n_total = sum(carrier_row.values())
            carrier_rows.append({
                "shortlist": event_row["shortlist"], "event_id": event_row["event_id"],
                "review_event_id": event_row["review_event_id"], "tier": event_row["tier"],
                "sample_id": sample_id, "group": sample_id.split("-")[0],
                "vcf_available": "yes" if sample_id in have_vcf else "no",
                "n_raw_matches": n_total,
                "n_manta_matches": carrier_row.get("Manta", 0),
                "n_tiddit_matches": carrier_row.get("TIDDIT", 0),
                "raw_call_found": "yes" if n_total else ("no" if sample_id in have_vcf else "vcf_missing"),
            })

    dup = {sample_id: files for sample_id, files in samples_seen.items() if len(files) > 1}
    for sample_id, files in dup.items():
        print(f"[warn] participant {sample_id} resolved from >1 VCF: {files}")
    near_dup = sorted({sample_id for sample_id in samples_seen if re.search(r"-[A-Z]$", sample_id)})
    for sample_id in near_dup:
        base = re.sub(r"-[A-Z]$", "", sample_id)
        if base in samples_seen:
            print(f"[warn] possible duplicate participant: {base} and {sample_id}")

    # ------------------------------------------------------------------ write
    def write(name, rows, fields=None):
        path = args.out_dir / name
        fields = fields or (list(rows[0].keys()) if rows else [])
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print(f"[out] {path} ({len(rows)} rows)")

    ev_fields = ["shortlist", "event_id", "review_event_id", "review_rank", "tier", "chrom", "start", "end",
                 "sv_length_bp", "sv_type", "genes", "highest_alsod_evidence", "max_annotsv_ranking_score",
                 "acmg_classes", "octopusv_record_ids", "n_recorded_carriers", "case_carriers", "control_carriers"]
    write("review_events.tsv", events, ev_fields)
    match_fields = ["shortlist", "event_id", "review_event_id", "tier", "event_sv_type", "event_chrom",
                    "event_start", "event_end", "sample_id", "group", "recorded_carrier", "caller",
                    "raw_sv_type", "raw_start", "raw_end", "raw_svlen", "match_type", "reciprocal_overlap",
                    "start_diff", "end_diff", "id_matches_octopusv_record", "vcf_file"] + RAW_COLS
    write("raw_record_matches.tsv", matches, match_fields)
    write("carrier_status.tsv", carrier_rows,
          ["shortlist", "event_id", "review_event_id", "tier", "sample_id", "group", "vcf_available",
           "n_raw_matches", "n_manta_matches", "n_tiddit_matches", "raw_call_found"])
    write("vcf_manifest.tsv", manifest)
    write("header_definitions.tsv", sorted(header_defs.values(), key=lambda row: (row["section"], row["id"])),
          ["section", "id", "number", "type", "description", "first_seen_in"])

    log = {
        "script": "sv_review_extract.py", "version": __version__,
        "started": started_at.isoformat(timespec="seconds"),
        "finished": _dt.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "parameters": {column: str(value) for column, value in vars(args).items()},
        "n_events": len(events), "n_vcfs": len(vcfs), "n_matched_records": len(matches),
        "n_carrier_event_pairs": len(carrier_rows),
        "n_carrier_event_pairs_without_raw_call": sum(row["raw_call_found"] == "no" for row in carrier_rows),
        "n_carrier_event_pairs_vcf_missing": sum(row["raw_call_found"] == "vcf_missing" for row in carrier_rows),
        "participants_with_multiple_vcfs": dup,
        "possible_duplicate_participants": near_dup,
        "input_md5": {} if args.no_checksums else {
            str(path): md5sum(path) for path in (args.intersection_tsv, args.union_tsv) if path},
    }
    with open(args.out_dir / "run_log.json", "w", encoding="utf-8") as handle:
        json.dump(log, handle, indent=2)
    print(f"[out] {args.out_dir / 'run_log.json'}")
    print(f"[done] carrier-event pairs without a raw call: {log['n_carrier_event_pairs_without_raw_call']}; "
          f"VCF missing: {log['n_carrier_event_pairs_vcf_missing']}")


if __name__ == "__main__":
    main()
