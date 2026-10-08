#!/usr/bin/env python3
"""Build event-level union/intersection AnnotSV sensitivity-analysis outputs.

Matching is deterministic and performed within each processing stratum (filtered or
unfiltered). Exact matches use normalized chromosome, start, end and SV type. If no
exact match exists, interval SVs can match by same chromosome/type, >=80% reciprocal
overlap and both breakpoints within max(500 bp, 10% of the longer event). INS/BND
events instead require both breakpoints within 500 bp. Candidate matches are assigned
one-to-one in descending similarity, with exact matches taking precedence.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "final_annotsv_results"
OUT = BASE / "sensitivity_analysis"
GENES = ROOT / "data" / "gene_lists" / "alsod_gene_transcript_map_gencode_v46.csv"

FILES = {
    "filtered": {
        "intersection": BASE / "filtered" / "manta_tiddit.intersect.cohort.annotated.tsv",
        "union": BASE / "filtered" / "manta_tiddit.union.cohort.annotated.tsv",
    },
    "unfiltered": {
        "intersection": BASE / "unfiltered" / "manta_tiddit.intersect.cohort.annotated.tsv",
        "union": BASE / "unfiltered" / "manta_tiddit.union.cohort.annotated.tsv",
    },
}

HIGH_ALS_LEVELS = {"Definitive ALS gene", "Strong evidence", "Moderate evidence"}
# No event reaches the conventional positive-score range expected in phenotype-rich
# AnnotSV runs; >=0.9 captures the highest observed score band in these completed files.
HIGH_RANK_THRESHOLD = 0.9


def norm_chrom(value: str) -> str:
    value = (value or "").strip()
    return value[3:] if value.lower().startswith("chr") else value


def split_values(value: str) -> list[str]:
    if not value:
        return []
    normalized = value.replace(",", ";")
    return [x.strip() for x in normalized.split(";") if x.strip() and x.strip() != "."]


def fnum(value: str):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def event_key(row: dict[str, str]) -> tuple[str, int, int, str]:
    return (
        norm_chrom(row.get("SV_chrom", "")),
        int(float(row.get("SV_start") or 0)),
        int(float(row.get("SV_end") or row.get("SV_start") or 0)),
        (row.get("SV_type") or "").upper(),
    )


def load_events(path: Path) -> dict[str, dict]:
    events: dict[str, dict] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            annot_id = row["AnnotSV_ID"]
            ev = events.setdefault(annot_id, {
                "annot_id": annot_id,
                "key": event_key(row),
                "samples": set(), "genes": set(), "scores": [], "criteria": set(),
                "acmg_classes": set(), "annotation_modes": set(), "filters": set(),
            })
            ev["samples"].update(split_values(row.get("Samples_ID", "")))
            ev["genes"].update(split_values(row.get("Gene_name", "")))
            score = fnum(row.get("AnnotSV_ranking_score", ""))
            if score is not None:
                ev["scores"].append(score)
            if row.get("AnnotSV_ranking_criteria"):
                ev["criteria"].add(row["AnnotSV_ranking_criteria"].strip())
            if row.get("ACMG_class"):
                ev["acmg_classes"].add(row["ACMG_class"].strip())
            if row.get("Annotation_mode"):
                ev["annotation_modes"].add(row["Annotation_mode"].strip())
            if row.get("FILTER"):
                ev["filters"].add(row["FILTER"].strip())
    return events


def reciprocal_overlap(a: tuple, b: tuple) -> tuple[float, int, int]:
    _, a_start, a_end, _ = a
    _, b_start, b_end, _ = b
    a_len, b_len = max(1, a_end - a_start + 1), max(1, b_end - b_start + 1)
    overlap = max(0, min(a_end, b_end) - max(a_start, b_start) + 1)
    return min(overlap / a_len, overlap / b_len), abs(a_start - b_start), abs(a_end - b_end)


def match_events(union: dict[str, dict], inter: dict[str, dict]) -> dict[str, dict]:
    matches: dict[str, dict] = {}
    used_i: set[str] = set()
    exact_index = defaultdict(list)
    for iid, iev in inter.items():
        exact_index[iev["key"]].append(iid)
    for uid, uev in union.items():
        candidates = [x for x in exact_index.get(uev["key"], []) if x not in used_i]
        if candidates:
            iid = sorted(candidates)[0]
            used_i.add(iid)
            matches[uid] = {"intersection_id": iid, "rule": "exact", "reciprocal_overlap": 1.0,
                            "start_delta_bp": 0, "end_delta_bp": 0}

    by_chr_type = defaultdict(list)
    for iid, iev in inter.items():
        if iid not in used_i:
            by_chr_type[(iev["key"][0], iev["key"][3])].append((iid, iev))
    possible = []
    for uid, uev in union.items():
        if uid in matches:
            continue
        uk = uev["key"]
        for iid, iev in by_chr_type[(uk[0], uk[3])]:
            ro, ds, de = reciprocal_overlap(uk, iev["key"])
            if uk[3] in {"INS", "BND", "TRA"}:
                ok, rule = ds <= 500 and de <= 500, "breakpoint_500bp"
            else:
                longer = max(1, uk[2] - uk[1] + 1, iev["key"][2] - iev["key"][1] + 1)
                tolerance = max(500, math.ceil(0.10 * longer))
                ok, rule = ro >= 0.80 and ds <= tolerance and de <= tolerance, "reciprocal_overlap_80"
            if ok:
                sample_jaccard = len(uev["samples"] & iev["samples"]) / max(1, len(uev["samples"] | iev["samples"]))
                possible.append((ro, sample_jaccard, -(ds + de), uid, iid, rule, ds, de))
    possible.sort(reverse=True)
    used_u = set(matches)
    for ro, sj, negdist, uid, iid, rule, ds, de in possible:
        if uid in used_u or iid in used_i:
            continue
        used_u.add(uid); used_i.add(iid)
        matches[uid] = {"intersection_id": iid, "rule": rule, "reciprocal_overlap": ro,
                        "start_delta_bp": ds, "end_delta_bp": de}
    return matches


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gene_evidence = {}
    with GENES.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            gene_evidence[row["Gene symbol"].strip()] = row["Category"].strip()

    all_rows, summaries, unmatched_intersections = [], [], []
    for stratum, paths in FILES.items():
        union, inter = load_events(paths["union"]), load_events(paths["intersection"])
        matches = match_events(union, inter)
        matched_i = {m["intersection_id"] for m in matches.values()}
        for iid in sorted(set(inter) - matched_i):
            ev = inter[iid]
            unmatched_intersections.append({"stratum": stratum, "intersection_annotsv_id": iid,
                "chrom": ev["key"][0], "start": ev["key"][1], "end": ev["key"][2], "sv_type": ev["key"][3]})

        reverse_matches = {m["intersection_id"]: (uid, m) for uid, m in matches.items()}

        def row_for(ev, status, uid="", iid="", match=None):
            chrom, start, end, sv_type = ev["key"]
            als_hits = sorted(g for g in ev["genes"] if g in gene_evidence)
            high_als = sorted(g for g in als_hits if gene_evidence[g] in HIGH_ALS_LEVELS)
            als_labels = [f"{g} ({gene_evidence[g]})" for g in als_hits]
            max_score = max(ev["scores"]) if ev["scores"] else None
            priority_reason = []
            if status == "union-only" and high_als:
                priority_reason.append("high-priority ALS gene")
            if status == "union-only" and max_score is not None and max_score >= HIGH_RANK_THRESHOLD:
                priority_reason.append(f"AnnotSV score >= {HIGH_RANK_THRESHOLD:g}")
            match = match or {}
            return {
                "stratum": stratum, "callset_status": status, "union_annotsv_id": uid,
                "intersection_annotsv_id": iid,
                "match_rule": match.get("rule", "none"),
                "reciprocal_overlap": match.get("reciprocal_overlap", ""),
                "start_delta_bp": match.get("start_delta_bp", ""), "end_delta_bp": match.get("end_delta_bp", ""),
                "chrom": chrom, "start": start, "end": end, "sv_length_bp": end - start + 1,
                "sv_type": sv_type, "samples": ";".join(sorted(ev["samples"])), "sample_count": len(ev["samples"]),
                "case_sample_count": sum(s.startswith("CASE-") for s in ev["samples"]),
                "control_sample_count": sum(s.startswith("CTRL-") for s in ev["samples"]),
                "genes": ";".join(sorted(ev["genes"])), "alsod_gene_hits": ";".join(als_labels),
                "high_priority_als_genes": ";".join(high_als),
                "max_annotsv_ranking_score": max_score if max_score is not None else "",
                "annotsv_ranking_criteria": " | ".join(sorted(ev["criteria"])),
                "acmg_classes": ";".join(sorted(ev["acmg_classes"])), "vcf_filters": ";".join(sorted(ev["filters"])),
                "union_only_priority": "yes" if priority_reason else "no",
                "priority_reason": "; ".join(priority_reason),
            }

        # Primary callset: retain every intersection event and link to a union event
        # where the deterministic matching rules identify one.
        for iid, ev in inter.items():
            uid, match = reverse_matches.get(iid, ("", {}))
            all_rows.append(row_for(ev, "intersection-primary", uid=uid, iid=iid, match=match))

        # Sensitivity extension: append only union events not already represented by
        # a matched primary intersection event.
        n_priority = 0
        for uid, ev in union.items():
            if uid in matches:
                continue
            row = row_for(ev, "union-only", uid=uid)
            all_rows.append(row)
            n_priority += row["union_only_priority"] == "yes"
        summaries.append({
            "stratum": stratum, "union_events": len(union), "intersection_events": len(inter),
            "intersection_events_matched_to_union": len(matches), "union_only_events": len(union) - len(matches),
            "unmatched_intersection_events": len(inter) - len(matched_i),
            "union_only_priority_events": n_priority,
            "exact_matches": sum(m["rule"] == "exact" for m in matches.values()),
            "fuzzy_matches": sum(m["rule"] != "exact" for m in matches.values()),
        })

    columns = list(all_rows[0])
    compact_columns = [c for c in columns if c != "samples"]
    with (OUT / "Supplementary_Table_AnnotSV_sensitivity_analysis.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=compact_columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(all_rows)
    priority = [r for r in all_rows if r["union_only_priority"] == "yes"]
    with (OUT / "Supplementary_Table_AnnotSV_union_only_priority.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader(); writer.writerows(priority)
    with (OUT / "analysis_summary.json").open("w", encoding="utf-8") as handle:
        json.dump({"summaries": summaries, "unmatched_intersections": unmatched_intersections,
                   "high_rank_threshold": HIGH_RANK_THRESHOLD,
                   "high_als_levels": sorted(HIGH_ALS_LEVELS)}, handle, indent=2)
    print(json.dumps({"summaries": summaries, "priority_rows": len(priority),
                      "unmatched_intersections": len(unmatched_intersections)}, indent=2))


if __name__ == "__main__":
    main()
