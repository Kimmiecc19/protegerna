#!/usr/bin/env python3
"""Prioritise AnnotSV intersection or union-only events and rank them for manual review.

Union-only mode excludes union events sharing a nonmissing source record ID or
exact chromosome/start/end/SVTYPE with the supplied intersection VCF. This is a
callset comparison, not approximate biological allele matching. Selection uses
stronger ALSoD evidence or maximum AnnotSV ranking score >=0.9. Selected events
are then placed in cohort-frequency tiers and ranked for manual review.

Outputs (in --out-dir, where <scope> is intersection or union_only):
  Supplementary_Table_AnnotSV_<scope>_event_prioritisation.tsv  all events
  Supplementary_Table_AnnotSV_<scope>_priority.tsv              selected events
  <scope>_prioritisation_summary.json
  Supplementary_Table_<scope>_manual_review_shortlist.tsv       ranked, tiered shortlist
  <scope>_manual_review_summary.json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, TextIO

HIGH_ALS_LEVELS = {"Definitive ALS gene", "Strong evidence", "Moderate evidence"}
HIGH_RANK_THRESHOLD = 0.9
MISSING = {None, "", ".", "NA"}
EVIDENCE_ORDER = {
    "Unassigned": 0, "Tenuous": 1, "Clinical modifier": 2,
    "Moderate evidence": 3, "Strong evidence": 4, "Definitive ALS gene": 5,
}
# Collected per AnnotSV_ID across its full and split rows.
SET_FIELDS = ("octopusv_record_ids", "genes", "criteria", "acmg_classes", "annotation_modes",
              "vcf_filters", "sv_methods", "support_values", "samples")


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8-sig", errors="replace")
    return path.open("r", encoding="utf-8-sig", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_number(value: str | None) -> float | None:
    try:
        number = float(value) if value not in MISSING else math.nan
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def split_annotation_values(value: str | None) -> list[str]:
    if not value or value in {".", "NA"}:
        return []
    return [x.strip() for x in re.split(r"[|,]", value) if x.strip() not in {"", ".", "NA"}]


def parse_info(value: str) -> dict[str, str]:
    info: dict[str, str] = {}
    for item in value.split(";"):
        if "=" in item:
            key, value_text = item.split("=", 1)
            info[key] = value_text
        elif item:
            info[item] = ""
    return info


def is_non_reference_gt(gt: str) -> bool:
    # Retain the existing alternate-known policy (e.g. ./1), but reject invalid GTs.
    alleles = re.split(r"[/|]", gt or "")
    return all(allele == "." or allele.isdigit() for allele in alleles) and any(
        allele.isdigit() and int(allele) > 0 for allele in alleles)


def normalized_acmg_class(value: str | None) -> str | None:
    if not value or value in {".", "NA"}:
        return None
    match = re.search(r"(?:class[ _-]*)?([1-5])(?:\b|$)", value, flags=re.IGNORECASE)
    return f"class {match.group(1)}" if match else value


def natural_chrom_key(value: str) -> tuple[int, str]:
    labels = {"X": 23, "Y": 24, "M": 25, "MT": 25}
    return (int(value), "") if value.isdigit() else (labels.get(value.upper(), 1000), value)


def write_tsv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------- #
# Event loading
# --------------------------------------------------------------------------- #
def event_locus(fields: list[str], info: dict[str, str]) -> tuple[str, int, int, str]:
    start = int(info.get("SV_start") or fields[1])
    return ((info.get("SV_chrom") or fields[0]).removeprefix("chr"), start,
            int(info.get("END") or start), (info.get("SVTYPE") or "").upper())


def new_event(annot_id: str, fields: list[str], info: dict[str, str]) -> dict:
    chrom, start, end, sv_type = event_locus(fields, info)
    return {
        "annotsv_id": annot_id, "chrom": chrom, "start": start, "end": end, "sv_type": sv_type,
        "sv_length_bp": abs(int(info.get("SVLEN") or (end - start + 1))),
        "scores": [], **{name: set() for name in SET_FIELDS},
    }


def load_vcf_events(path: Path) -> tuple[dict[str, dict], list[str]]:
    """Load an AnnotSV VCF and consolidate full/split rows by AnnotSV_ID."""
    if not path.is_file():
        raise FileNotFoundError(f"Input VCF not found: {path}")
    events: dict[str, dict] = {}
    samples: list[str] = []
    with open_text(path) as handle:
        for line_number, line in enumerate(handle, 1):
            if line.startswith("#CHROM"):
                samples = line.rstrip("\r\n").split("\t")[9:]
                continue
            if line.startswith("#") or not line.strip():
                continue
            if not samples:
                raise ValueError(f"No #CHROM header found before data in {path}")
            fields = line.rstrip("\r\n").split("\t")
            where = f"{path}:{line_number}"
            if len(fields) != 9 + len(samples):
                raise ValueError(f"Malformed VCF row at {where}")
            info = parse_info(fields[7])
            if info.get("Annotation_mode") not in {"full", "split"}:
                raise ValueError(f"Expected Annotation_mode=full or split at {where}")
            annot_id = info.get("AnnotSV_ID", "").strip()
            if not annot_id:
                raise ValueError(f"Missing AnnotSV_ID at {where}")
            event = events.setdefault(annot_id, new_event(annot_id, fields, info))
            if event_locus(fields, info) != (event["chrom"], event["start"], event["end"], event["sv_type"]):
                raise ValueError(f"AnnotSV_ID {annot_id} maps to inconsistent events in {path}")
            event["octopusv_record_ids"].add(fields[2])
            event["genes"].update(split_annotation_values(info.get("Gene_name")))
            score = parse_number(info.get("AnnotSV_ranking_score"))
            if score is not None:
                event["scores"].append(score)
            if info.get("AnnotSV_ranking_criteria") not in MISSING:
                event["criteria"].add(info["AnnotSV_ranking_criteria"])
            acmg = normalized_acmg_class(info.get("ACMG_class"))
            if acmg:
                event["acmg_classes"].add(acmg)
            event["annotation_modes"].add(info["Annotation_mode"])
            event["vcf_filters"].add(fields[6])
            if info.get("SVMETHOD"):
                event["sv_methods"].add(info["SVMETHOD"])
            if info.get("SUPPORT") not in {None, "", "."}:
                event["support_values"].add(info["SUPPORT"])
            if len(fields) > 9:
                format_keys = fields[8].split(":")
                if "GT" not in format_keys:
                    raise ValueError(f"Missing FORMAT/GT at {where}")
                gt_index = format_keys.index("GT")
                for sample_id, sample_field in zip(samples, fields[9:]):
                    values = sample_field.split(":")
                    if gt_index < len(values) and is_non_reference_gt(values[gt_index]):
                        event["samples"].add(sample_id)
    if not events:
        raise ValueError(f"No AnnotSV events found in {path}")
    if len(samples) != len(set(samples)):
        raise ValueError(f"Duplicate sample names in {path}")
    if any(not sample_id.startswith(("CASE-", "CTRL-")) for sample_id in samples):
        raise ValueError("Every sample must have a CASE- or CTRL- prefix")
    if any("full" not in event["annotation_modes"] for event in events.values()):
        raise ValueError("Every AnnotSV event must have a full annotation row")
    if not all(event["sv_methods"] == {"OctopuSV"} for event in events.values()):
        raise ValueError(f"Not every event in {path} is marked SVMETHOD=OctopuSV")
    return events, samples


def load_alsod(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"ALSoD gene table not found: {path}")
    evidence: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"Gene symbol", "Category"} <= set(reader.fieldnames or []):
            raise ValueError("ALSoD CSV requires Gene symbol and Category columns")
        for row in reader:
            gene = (row.get("Gene symbol") or "").strip()
            if gene:
                evidence[gene] = (row.get("Category") or "").strip()
    return evidence


# --------------------------------------------------------------------------- #
# Prioritisation
# --------------------------------------------------------------------------- #
def event_row(event: dict, gene_evidence: dict[str, str], scope: str) -> dict:
    als_hits = sorted(gene for gene in event["genes"] if gene in gene_evidence)
    high_als = sorted(gene for gene in als_hits if gene_evidence[gene] in HIGH_ALS_LEVELS)
    max_score = max(event["scores"]) if event["scores"] else None
    als_priority = bool(high_als)
    score_priority = max_score is not None and max_score >= HIGH_RANK_THRESHOLD
    selected = als_priority or score_priority
    route = {(True, True): "ALSoD and AnnotSV score", (True, False): "ALSoD only",
             (False, True): "AnnotSV score only"}.get((als_priority, score_priority), "not applicable")
    reasons = (["stronger ALSoD gene evidence"] if als_priority else []) + (
        [f"maximum AnnotSV ranking score >= {HIGH_RANK_THRESHOLD:g}"] if score_priority else [])
    carriers = sorted(event["samples"])
    joined = lambda name: ";".join(sorted(event[name]))  # noqa: E731
    return {
        "event_id": event["annotsv_id"],
        "octopusv_record_ids": joined("octopusv_record_ids"),
        "caller_support_status": "intersection-primary" if scope == "intersection" else "union-only-exploratory",
        "chrom": event["chrom"], "start": event["start"], "end": event["end"],
        "sv_length_bp": event["sv_length_bp"], "sv_type": event["sv_type"],
        "sample_count": len(carriers),
        "case_sample_count": sum(sample_id.startswith("CASE-") for sample_id in carriers),
        "control_sample_count": sum(sample_id.startswith("CTRL-") for sample_id in carriers),
        "samples": ";".join(carriers),
        "genes": joined("genes"),
        "alsod_gene_hits": ";".join(f"{gene} ({gene_evidence[gene]})" for gene in als_hits),
        "high_priority_als_genes": ";".join(high_als),
        "max_annotsv_ranking_score": max_score if max_score is not None else "",
        "annotsv_ranking_criteria": " | ".join(sorted(event["criteria"])),
        "acmg_classes": joined("acmg_classes"),
        "vcf_filters": joined("vcf_filters"),
        "sv_methods": joined("sv_methods"),
        "read_support_values": joined("support_values"),
        "manual_review_priority": "yes" if selected else "no",
        "priority_route": route,
        "priority_reason": "; ".join(reasons),
        "interpretation_guardrail": "Manual-review candidate only; no pathogenicity assertion.",
        "shortlist": scope,
    }


def build_prioritization(intersection_vcf: Path, alsod_csv: Path, union_vcf: Path | None = None):
    events, samples = load_vcf_events(intersection_vcf)
    scope = "union_only" if union_vcf else "intersection"
    inputs = [intersection_vcf, alsod_csv]
    excluded = 0
    if union_vcf:
        union, union_samples = load_vcf_events(union_vcf)
        if set(union_samples) != set(samples):
            raise ValueError("Intersection and union VCFs must contain the same cohort samples")
        locus = lambda event: (event["chrom"], event["start"], event["end"], event["sv_type"])  # noqa: E731
        loci = {locus(event) for event in events.values()}
        record_ids = {record_id for event in events.values()
                      for record_id in event["octopusv_record_ids"] if record_id not in ("", ".")}
        retained = {key: event for key, event in union.items()
                    if locus(event) not in loci and not (event["octopusv_record_ids"] & record_ids)}
        excluded = len(union) - len(retained)
        events, samples = retained, union_samples
        inputs.append(union_vcf)
    gene_evidence = load_alsod(alsod_csv)
    all_rows = sorted((event_row(event, gene_evidence, scope) for event in events.values()),
                      key=lambda row: (natural_chrom_key(row["chrom"]), row["start"], row["end"], row["event_id"]))
    priority = [row for row in all_rows if row["manual_review_priority"] == "yes"]
    summary = {
        "analysis_name": f"Prioritisation of {scope} structural variants",
        "shortlist": scope,
        "union_events_excluded_as_intersection": excluded,
        "union_only_rule": "Exclude shared nonmissing source VCF IDs or exact chromosome/start/end/SVTYPE matches; no approximate allele matching.",
        "event_rule": "Consolidate full/split annotations by AnnotSV_ID within the selected VCF. No rematching or locus clustering.",
        "priority_rule": f"Selected event with ALSoD evidence in {sorted(HIGH_ALS_LEVELS)} or maximum event-level AnnotSV ranking score >= {HIGH_RANK_THRESHOLD:g}.",
        f"{scope}_events": len(events),
        f"{scope}_priority_events": len(priority),
        "priority_route_counts": dict(sorted(Counter(row["priority_route"] for row in priority).items())),
        "case_n": sum(sample_id.startswith("CASE-") for sample_id in samples),
        "control_n": sum(sample_id.startswith("CTRL-") for sample_id in samples), "cohort_n": len(samples),
        "high_rank_threshold": HIGH_RANK_THRESHOLD, "high_als_levels": sorted(HIGH_ALS_LEVELS),
        "genotype_policy": "Alternate-known: partial GTs with a known alternate allele count as carriers; missing/reference GTs do not. These are preserved merged-VCF GTs, not independently validated raw-caller genotypes.",
        "inputs": {str(path): {"sha256": sha256(path), "bytes": path.stat().st_size} for path in inputs},
    }
    return all_rows, priority, summary


# --------------------------------------------------------------------------- #
# Manual-review tiers and ranking
# --------------------------------------------------------------------------- #
def review_row(row: dict, summary: dict) -> dict:
    case_count, control_count = row["case_sample_count"], row["control_sample_count"]
    case_n, control_n, cohort_n = summary["case_n"], summary["control_n"], summary["cohort_n"]
    if not case_n or not control_n:
        raise ValueError("Case/control tiers require CASE- and CTRL- sample groups.")
    case_frequency, control_frequency = case_count / case_n, control_count / control_n
    overall_frequency = row["sample_count"] / cohort_n
    labels = [label.rsplit("(", 1)[-1].rstrip(")") for label in row["alsod_gene_hits"].split(";") if label]
    highest_evidence = max(labels, key=lambda label: EVIDENCE_ORDER.get(label, 0), default="Unassigned")
    flags = []
    if row["sample_count"] == 0:
        flags.append("no non-reference genotypes")
    if control_count >= 3 or control_frequency >= 0.05:
        flags.append("control frequency >=5% or >=3 control carriers")
    if overall_frequency >= 0.10:
        flags.append("overall carrier frequency >=10%")
    if control_count and control_frequency >= case_frequency:
        flags.append("control frequency >= case frequency")
    if flags:
        tier, reason = 4, "; ".join(flags)
    elif control_count:
        tier, reason = 3, "observed in controls below frequency-review thresholds"
    elif row["high_priority_als_genes"]:
        tier, reason = 1, "case-only with stronger ALSoD gene evidence"
    else:
        tier, reason = 2, "case-only with AnnotSV score priority"
    return dict(
        row, review_rank=0, prioritisation_tier=tier, tier_reason=reason,
        frequency_or_genotype_qc_flag="yes" if flags else "no",
        frequency_or_genotype_qc_reason="; ".join(flags),
        highest_alsod_evidence=highest_evidence, alsod_evidence_rank=EVIDENCE_ORDER.get(highest_evidence, 0),
        case_n=case_n, control_n=control_n, cohort_n=cohort_n,
        case_carrier_frequency=case_frequency, control_carrier_frequency=control_frequency,
        overall_carrier_frequency=overall_frequency,
        case_minus_control_carrier_frequency=case_frequency - control_frequency,
        manual_review_status="not reviewed", manual_review_notes="",
    )


def rank_review_rows(priority: list[dict], summary: dict) -> list[dict]:
    rows = sorted((review_row(row, summary) for row in priority), key=lambda row: (
        row["prioritisation_tier"], -row["alsod_evidence_rank"],
        -(row["max_annotsv_ranking_score"] if row["max_annotsv_ranking_score"] != "" else -999),
        -row["case_minus_control_carrier_frequency"], -row["sample_count"],
        natural_chrom_key(row["chrom"]), row["start"], row["event_id"],
    ))
    for rank, row in enumerate(rows, 1):
        row["review_rank"] = rank
    return rows


def review_summary(summary: dict, rows: list[dict]) -> dict:
    return dict(
        summary,
        manual_review_events=len(rows),
        tier_counts=dict(Counter(row["prioritisation_tier"] for row in rows)),
        tier_definitions={
            "1": "case-only with stronger ALSoD evidence, below frequency-review thresholds",
            "2": "case-only with AnnotSV score priority, below frequency-review thresholds",
            "3": "observed in controls below frequency-review thresholds",
            "4": "frequency or genotype QC review; takes precedence over other tiers",
        },
        tier_interpretation="Study-specific review order; frequency flags do not establish an artifact or pathogenicity.",
        ranking_order=["tier", "ALSoD evidence descending", "AnnotSV score descending",
                       "case-minus-control frequency descending", "carrier count descending",
                       "chromosome, start and event ID"],
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("intersection", "union-only"), default="intersection")
    parser.add_argument("--intersection-vcf", type=Path, required=True,
                        help="Intersection AnnotSV VCF; comparison input in union-only mode")
    parser.add_argument("--union-vcf", type=Path, help="Union AnnotSV VCF, required for union-only mode")
    parser.add_argument("--alsod-csv", type=Path, required=True)
    parser.add_argument("--out-dir", "--outdir", dest="out_dir", type=Path, required=True)
    args = parser.parse_args()
    if (args.mode == "union-only") != (args.union_vcf is not None):
        parser.error("--union-vcf is required for, and only used with, --mode union-only")
    for name in ("intersection_vcf", "union_vcf", "alsod_csv", "out_dir"):
        value = getattr(args, name)
        if value is not None and not value.is_absolute():
            parser.error(f'--{name.replace("_", "-")} must be an absolute path')
    return args


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows, priority, summary = build_prioritization(args.intersection_vcf, args.alsod_csv, args.union_vcf)
    scope = summary["shortlist"]
    # Keep headers even when no events qualify.
    template = all_rows[0] if all_rows else event_row(new_event("", ["1", "1"], {}), {}, scope)
    write_tsv(out_dir / f"Supplementary_Table_AnnotSV_{scope}_event_prioritisation.tsv", all_rows, list(template))
    write_tsv(out_dir / f"Supplementary_Table_AnnotSV_{scope}_priority.tsv", priority, list(template))
    (out_dir / f"{scope}_prioritisation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    rows = rank_review_rows(priority, summary)
    fields = list(rows[0] if rows else review_row(template, summary))
    write_tsv(out_dir / f"Supplementary_Table_{scope}_manual_review_shortlist.tsv", rows, fields)
    final_summary = review_summary(summary, rows)
    (out_dir / f"{scope}_manual_review_summary.json").write_text(json.dumps(final_summary, indent=2), encoding="utf-8")
    print(json.dumps(final_summary, indent=2))


if __name__ == "__main__":
    main()
