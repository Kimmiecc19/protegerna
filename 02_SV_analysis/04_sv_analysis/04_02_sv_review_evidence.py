#!/usr/bin/env python3
"""
sv_review_evidence.py
=====================

Step 2 of the alignment-free technical review of prioritised structural variants.

Reads the outputs of sv_review_extract.py and turns the raw Manta and TIDDIT
fields into explicit evidence columns, then applies predefined, parameterised
rules to label each (event, carrier) pair and each event.

Evidence extracted
------------------
Manta (FORMAT GT:FT:GQ:PL:PR:SR; INFO IMPRECISE, CIPOS, CIEND, HOMLEN, HOMSEQ ...)
  PR = paired reads (ref,alt); SR = split reads (ref,alt); IMPRECISE flag.
TIDDIT v3 (FORMAT GT:CN:COV:DV:RV:LQ:RR:DR; INFO LTE, LFA, LFB, REGIONA, REGIONB)
  DV = discordant pairs supporting the event; RV = split reads supporting the event;
  DR / RR = pairs / reads supporting the reference (breakpoint A,B);
  COV = coverage at A, between and B; LQ = fraction of low-quality reads (A,B);
  CN = copy-number genotype for imprecise events.
  NB: the TIDDIT v3 header describes COV as "(at A,B, and between)", but the
  values written are ordered A, BETWEEN, B (verified empirically: homozygous
  deletions have ~0 coverage in the MIDDLE value). The default --tiddit-cov-order
  is therefore "A,between,B". The script also reports an empirical check
  (tiddit_cov_order_check.tsv) so the choice can be justified.

Evidence lines (per event x participant)
----------------------------------------
  split_read   : max(Manta SR_alt, TIDDIT RV) >= --min-split
  paired_end   : max(Manta PR_alt, TIDDIT DV) >= --min-pairs
  read_depth   : TIDDIT COV_between / mean(COV_A, COV_B)
                   DEL consistent if <= --del-max-ratio
                   DUP consistent if >= --dup-min-ratio
                   not_assessable if event < --min-depth-len bp or coverage missing
  Supporting flags: both_callers, precise_breakpoint (Manta not IMPRECISE),
  any_pass_record, low_mapq (TIDDIT max LQ > --max-lq or Manta MaxMQ0Frac filter).

Carrier label (size-aware rule, default since v1.1.0)
-----------------------------------------------------
  Independent evidence lines: (1) Manta precise split-read junction (not IMPRECISE,
  SR alt >= --min-split); (2) TIDDIT split reads (RV >= --min-split); (3) discordant
  pairs (Manta PR alt or TIDDIT DV >= --min-pairs); (4) read depth consistent.
  not_found     no raw record matched this carrier
  supported     >= 2 evidence lines and >= 1 PASS record; OR, for events shorter than
                --small-sv-len, a PASS Manta record with a precise split-read junction
                (discordant pairs and read depth are uninformative below fragment size)
  weak          otherwise with >= 1 line, no PASS record, or read depth inconsistent
  no_evidence   raw record matched but no evidence line met its threshold
  carrier_label_strict / event_evidence_label_strict / suggested_outcome_strict
  keep the v1.0.0 rule (split reads pooled across callers, no small-SV rule) as a
  sensitivity analysis.

Event label and suggested outcome: see summarise_events() below.

Optional context
----------------
  --intersection-annotsv-files / --union-annotsv-files: AnnotSV context
             joined on callset plus AnnotSV_ID == event_id, with unique keys.
  --str-bed  BED of short tandem repeat loci (e.g. STRipy or ExpansionHunter
             catalogue converted to BED); events within --str-padding bp are flagged

Outputs (in --out-dir, default = --in-dir)
  evidence_per_record.tsv    parsed evidence for every matched raw record
  evidence_per_carrier.tsv   one row per (event, recorded carrier)
  evidence_per_event.tsv     one row per event, with labels and fidelity flags
  evidence_summary.tsv       counts by shortlist x tier x suggested outcome
  evidence_thresholds.json   thresholds and inputs used

Requires: pandas.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# All-NaN reductions (e.g. nanmax of two missing values) intentionally return NaN.
warnings.filterwarnings("ignore", category=RuntimeWarning)

__version__ = "1.1.0"


# --------------------------------------------------------------------------- #
# Field parsing
# --------------------------------------------------------------------------- #
def parse_info(info: str) -> dict:
    out = {}
    if not isinstance(info, str) or info in ("", "."):
        return out
    for item in info.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            out[key] = value
        else:
            out[item] = True
    return out


def parse_sample(fmt: str, values: str) -> dict:
    if not isinstance(fmt, str) or not isinstance(values, str):
        return {}
    return dict(zip(fmt.split(":"), values.split(":")))


def nums(value, n=None):
    """'12,3' -> [12.0, 3.0]; missing -> list of NaN."""
    if value is None or value is True or (isinstance(value, float) and math.isnan(value)):
        return [np.nan] * (n or 1)
    out = []
    for x in str(value).split(","):
        try:
            out.append(float(x))
        except ValueError:
            out.append(np.nan)
    if n and len(out) < n:
        out += [np.nan] * (n - len(out))
    return out


def first(value):
    return nums(value)[0]


def record_evidence(row: pd.Series, cov_order: str = "A,between,B") -> dict:
    info = parse_info(row["INFO"])
    sample_fields = parse_sample(row["FORMAT"], row["SAMPLE_VALUES"])
    evidence = {
        "gt": sample_fields.get("GT", ""),
        "qual": first(row["QUAL"]),
        "filter": row["FILTER"],
        "is_pass": str(row["FILTER"]) in ("PASS", "."),
    }
    if row["caller"] == "Manta":
        pair_reads = nums(sample_fields.get("PR"), 2)
        split_reads = nums(sample_fields.get("SR"), 2)
        evidence.update({
            "manta_ft": sample_fields.get("FT", ""),
            "manta_gq": first(sample_fields.get("GQ")),
            "manta_pr_ref": pair_reads[0], "manta_pr_alt": pair_reads[1],
            "manta_sr_ref": split_reads[0], "manta_sr_alt": split_reads[1],
            "manta_imprecise": bool(info.get("IMPRECISE", False)),
            "manta_cipos": info.get("CIPOS", ""),
            "manta_ciend": info.get("CIEND", ""),
            "manta_homlen": first(info.get("HOMLEN")),
            "manta_homseq": info.get("HOMSEQ", ""),
            "manta_svinslen": first(info.get("SVINSLEN")),
        })
        alternate_reads = np.nansum([pair_reads[1], split_reads[1]])
        total_reads = np.nansum([pair_reads[0], pair_reads[1], split_reads[0], split_reads[1]])
        evidence["manta_alt_reads"] = alternate_reads
        evidence["manta_alt_fraction"] = alternate_reads / total_reads if total_reads > 0 else np.nan
        evidence["manta_low_mapq"] = "MaxMQ0Frac" in str(row["FILTER"])
    elif row["caller"] == "TIDDIT":
        raw = nums(sample_fields.get("COV"), 3)
        # reorder to [A, B, between]
        coverage = [raw[0], raw[2], raw[1]] if cov_order == "A,between,B" else raw
        low_quality_fraction = nums(sample_fields.get("LQ"), 2)
        reference_pairs = nums(sample_fields.get("DR"), 2)
        reference_splits = nums(sample_fields.get("RR"), 2)
        alternate_pairs, alternate_splits = first(sample_fields.get("DV")), first(sample_fields.get("RV"))
        local_evidence = nums(info.get("LTE"), 2)
        flank = np.nanmean([coverage[0], coverage[1]]) if not np.all(np.isnan(coverage[:2])) else np.nan
        ratio = coverage[2] / flank if flank and flank > 0 and not np.isnan(coverage[2]) else np.nan
        evidence.update({
            "tiddit_cn": first(sample_fields.get("CN")),
            "tiddit_cov_a": coverage[0], "tiddit_cov_b": coverage[1], "tiddit_cov_between": coverage[2],
            "tiddit_depth_ratio": ratio,
            "tiddit_dv": alternate_pairs, "tiddit_rv": alternate_splits,
            "tiddit_dr_a": reference_pairs[0], "tiddit_dr_b": reference_pairs[1],
            "tiddit_rr_a": reference_splits[0], "tiddit_rr_b": reference_splits[1],
            "tiddit_lq_a": low_quality_fraction[0], "tiddit_lq_b": low_quality_fraction[1],
            "tiddit_lq_max": np.nanmax(low_quality_fraction) if not np.all(np.isnan(low_quality_fraction)) else np.nan,
            "tiddit_lte_pairs": local_evidence[0], "tiddit_lte_splits": local_evidence[1],
            "tiddit_regiona": info.get("REGIONA", ""), "tiddit_regionb": info.get("REGIONB", ""),
        })
        alternate_reads = np.nansum([alternate_pairs, alternate_splits])
        evidence["tiddit_alt_reads"] = alternate_reads
        evidence["tiddit_pair_fraction"] = alternate_pairs / (alternate_pairs + np.nanmean(reference_pairs)) if not np.isnan(alternate_pairs) and not np.all(np.isnan(reference_pairs)) and (alternate_pairs + np.nanmean(reference_pairs)) > 0 else np.nan
    return evidence


# --------------------------------------------------------------------------- #
# Carrier-level evidence
# --------------------------------------------------------------------------- #
def best(df: pd.DataFrame, caller: str, key: str) -> pd.Series | None:
    sub = df[df["caller"] == caller]
    if sub.empty:
        return None
    sub = sub.assign(_k=sub[key].fillna(-1), _p=sub["is_pass"].astype(int),
                     _ro=pd.to_numeric(sub["reciprocal_overlap"], errors="coerce").fillna(0))
    return sub.sort_values(["_k", "_p", "_ro"], ascending=False).iloc[0]


def carrier_evidence(group: pd.DataFrame, event: pd.Series, args) -> dict:
    manta_record = best(group, "Manta", "manta_alt_reads")
    tiddit_record = best(group, "TIDDIT", "tiddit_alt_reads")

    def value(record, key):
        return record[key] if record is not None and key in record and not pd.isna(record[key]) else np.nan

    def field(record, key):
        return record[key] if record is not None else ""

    manta_sr, tiddit_rv = value(manta_record, "manta_sr_alt"), value(tiddit_record, "tiddit_rv")
    split_read_count = np.nanmax([manta_sr, tiddit_rv])
    pair_count = np.nanmax([value(manta_record, "manta_pr_alt"), value(tiddit_record, "tiddit_dv")])
    split_ok = bool(not np.isnan(split_read_count) and split_read_count >= args.min_split)
    pairs_ok = bool(not np.isnan(pair_count) and pair_count >= args.min_pairs)

    ratio = value(tiddit_record, "tiddit_depth_ratio")
    length = abs(int(event["end"]) - int(event["start"]))
    if event["sv_type"] not in ("DEL", "DUP") or length < args.min_depth_len or np.isnan(ratio):
        depth = "not_assessable"
    elif event["sv_type"] == "DEL":
        depth = "consistent" if ratio <= args.del_max_ratio else "inconsistent"
    else:
        depth = "consistent" if ratio >= args.dup_min_ratio else "inconsistent"

    any_pass = bool(group["is_pass"].any())
    low_mapq = bool((tiddit_record is not None and value(tiddit_record, "tiddit_lq_max") > args.max_lq) or
                    (manta_record is not None and bool(manta_record.get("manta_low_mapq", False))))
    precise = bool(manta_record is not None and not manta_record["manta_imprecise"])

    # ---- strict rule (v1.0.0): split / pairs / depth, split pooled across callers
    lines_strict = int(split_ok) + int(pairs_ok) + int(depth == "consistent")

    # ---- size-aware rule (default, v1.1.0)
    # Independent observations: Manta precise split-read junction, TIDDIT split reads,
    # discordant pairs (either caller), read depth. For events shorter than
    # --small-sv-len, discordant pairs and read depth are not expected to be
    # informative, so a PASS precise (assembled) split-read junction is sufficient.
    manta_junction = bool(precise and not np.isnan(manta_sr) and manta_sr >= args.min_split)
    tiddit_split = bool(not np.isnan(tiddit_rv) and tiddit_rv >= args.min_split)
    lines = int(manta_junction) + int(tiddit_split) + int(pairs_ok) + int(depth == "consistent")
    small = length < args.small_sv_len

    def decide(n_lines, small_rule_ok):
        if group.empty:
            return "not_found", "no matching raw record"
        if depth == "inconsistent":
            return "weak", "read depth inconsistent with SV type"
        if n_lines >= 2 and any_pass:
            return "supported", f"{n_lines} evidence lines"
        if small_rule_ok and any_pass:
            return "supported", "small SV: PASS precise split-read junction"
        if n_lines == 0:
            return "no_evidence", "matched record(s) below all thresholds"
        why = ["single evidence line"] if n_lines == 1 else []
        if not any_pass:
            why.append("no PASS record")
        return "weak", "; ".join(why) or "below support rule"

    label, reason = decide(lines, small and manta_junction and manta_record is not None and bool(manta_record["is_pass"]))
    label_strict, _ = decide(lines_strict, False)

    return {
        "n_raw_records": len(group),
        "callers_found": ";".join(sorted(group["caller"].unique())) if not group.empty else "",
        "both_callers": bool({"Manta", "TIDDIT"} <= set(group["caller"])),
        "any_pass_record": any_pass,
        "manta_record_id": field(manta_record, "ID"),
        "manta_filter": field(manta_record, "FILTER"),
        "manta_gt": field(manta_record, "gt"),
        "manta_pr_alt": value(manta_record, "manta_pr_alt"), "manta_pr_ref": value(manta_record, "manta_pr_ref"),
        "manta_sr_alt": manta_sr, "manta_sr_ref": value(manta_record, "manta_sr_ref"),
        "manta_alt_fraction": value(manta_record, "manta_alt_fraction"),
        "manta_imprecise": bool(manta_record["manta_imprecise"]) if manta_record is not None else "",
        "manta_homlen": value(manta_record, "manta_homlen"),
        "manta_start_diff": field(manta_record, "start_diff"),
        "manta_end_diff": field(manta_record, "end_diff"),
        "tiddit_record_id": field(tiddit_record, "ID"),
        "tiddit_filter": field(tiddit_record, "FILTER"),
        "tiddit_gt": field(tiddit_record, "gt"),
        "tiddit_dv": value(tiddit_record, "tiddit_dv"), "tiddit_rv": tiddit_rv,
        "tiddit_cn": value(tiddit_record, "tiddit_cn"),
        "tiddit_cov_a": value(tiddit_record, "tiddit_cov_a"), "tiddit_cov_b": value(tiddit_record, "tiddit_cov_b"),
        "tiddit_cov_between": value(tiddit_record, "tiddit_cov_between"),
        "tiddit_depth_ratio": ratio,
        "tiddit_lq_max": value(tiddit_record, "tiddit_lq_max"),
        "tiddit_start_diff": field(tiddit_record, "start_diff"),
        "tiddit_end_diff": field(tiddit_record, "end_diff"),
        "precise_breakpoint": precise,
        "split_read_support": split_read_count, "paired_end_support": pair_count,
        "ev_split_read": split_ok, "ev_paired_end": pairs_ok, "ev_read_depth": depth,
        "n_evidence_lines": lines, "low_mapq": low_mapq,
        "ev_manta_junction": manta_junction, "ev_tiddit_split": tiddit_split,
        "n_evidence_lines_strict": lines_strict,
        "carrier_label": label, "carrier_label_reason": reason,
        "carrier_label_strict": label_strict,
    }


# --------------------------------------------------------------------------- #
# Context annotation
# --------------------------------------------------------------------------- #

# Explicit schemas also keep headers available for empty extraction results.
RECORD_EVIDENCE_COLUMNS = [
    "gt", "qual", "filter", "is_pass", "manta_ft", "manta_gq", "manta_pr_ref", "manta_pr_alt",
    "manta_sr_ref", "manta_sr_alt", "manta_imprecise", "manta_cipos", "manta_ciend",
    "manta_homlen", "manta_homseq", "manta_svinslen", "manta_alt_reads", "manta_alt_fraction",
    "manta_low_mapq", "tiddit_cn", "tiddit_cov_a", "tiddit_cov_b", "tiddit_cov_between",
    "tiddit_depth_ratio", "tiddit_dv", "tiddit_rv", "tiddit_dr_a", "tiddit_dr_b", "tiddit_rr_a",
    "tiddit_rr_b", "tiddit_lq_a", "tiddit_lq_b", "tiddit_lq_max", "tiddit_lte_pairs",
    "tiddit_lte_splits", "tiddit_regiona", "tiddit_regionb", "tiddit_alt_reads",
    "tiddit_pair_fraction"
]
CARRIER_EVIDENCE_COLUMNS = [
    "n_raw_records", "callers_found", "both_callers", "any_pass_record", "manta_record_id",
    "manta_filter", "manta_gt", "manta_pr_alt", "manta_pr_ref", "manta_sr_alt", "manta_sr_ref",
    "manta_alt_fraction", "manta_imprecise", "manta_homlen", "manta_start_diff", "manta_end_diff",
    "tiddit_record_id", "tiddit_filter", "tiddit_gt", "tiddit_dv", "tiddit_rv", "tiddit_cn",
    "tiddit_cov_a", "tiddit_cov_b", "tiddit_cov_between", "tiddit_depth_ratio", "tiddit_lq_max",
    "tiddit_start_diff", "tiddit_end_diff", "precise_breakpoint", "split_read_support",
    "paired_end_support", "ev_split_read", "ev_paired_end", "ev_read_depth", "n_evidence_lines",
    "low_mapq", "ev_manta_junction", "ev_tiddit_split", "n_evidence_lines_strict", "carrier_label",
    "carrier_label_reason", "carrier_label_strict"
]

CONTEXT_PATTERNS = re.compile(r"^(Repeat_|SegDup_|ENCODE_blacklist|GC_content|Gap_)", re.I)


def load_annotsv_context(paths: list[Path], shortlist: str) -> pd.DataFrame:
    """Load one context row per callset/event without discarding conflicting data.

    Only AnnotSV_ID, Annotation_mode and the context columns are read, so large
    unfiltered AnnotSV tables fit in memory.
    """
    frames = []
    for path in paths:
        header = list(pd.read_csv(path, sep="\t", nrows=0).columns)
        if "AnnotSV_ID" not in header:
            raise ValueError(f"{path}: missing AnnotSV_ID")
        context_columns = [column for column in header if CONTEXT_PATTERNS.match(column)]
        mode = ["Annotation_mode"] if "Annotation_mode" in header else []
        data = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                           usecols=["AnnotSV_ID", *mode, *context_columns])
        if mode:
            data = data[data["Annotation_mode"] == "full"]
        if data.empty:
            continue
        if data["AnnotSV_ID"].isin(["", "."]).any():
            raise ValueError(f"{path}: empty AnnotSV_ID")
        frame = data[["AnnotSV_ID", *context_columns]].rename(
            columns={"AnnotSV_ID": "event_id", **{column: f"ctx_{column}" for column in context_columns}})
        frame.insert(0, "shortlist", shortlist)
        frames.append(frame)
    return combine_context_frames(frames)


def combine_context_frames(frames):
    if not frames:
        return pd.DataFrame(columns=["shortlist", "event_id"])
    context = pd.concat(frames, ignore_index=True).fillna("").drop_duplicates()
    keys = ["shortlist", "event_id"]
    conflicts = context[context.duplicated(keys, keep=False)]
    if not conflicts.empty:
        raise ValueError(f"Conflicting annotation context for callset/event keys: {conflicts[keys].to_dict('records')[:10]}")
    return context


def str_overlaps(events: pd.DataFrame, bed: Path, pad: int) -> pd.Series:
    loci = {}
    with open(bed, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.startswith(("#", "track", "browser")):
                continue
            fields = line.rstrip("\n").split("\t")
            chrom = fields[0][3:] if fields[0].lower().startswith("chr") else fields[0]
            name = fields[3] if len(fields) > 3 else f"{fields[0]}:{fields[1]}-{fields[2]}"
            loci.setdefault(chrom, []).append((int(fields[1]), int(fields[2]), name))
    hits = []
    for _, event in events.iterrows():
        padded_start, padded_end = int(event["start"]) - pad, int(event["end"]) + pad
        names = [locus_name for locus_start, locus_end, locus_name in loci.get(str(event["chrom"]), []) if locus_start <= padded_end and locus_end >= padded_start]
        hits.append(";".join(names))
    return pd.Series(hits, index=events.index)


def nonempty(v) -> bool:
    return isinstance(v, str) and v.strip() not in ("", ".", "nan", "NA")


# --------------------------------------------------------------------------- #
# Event summary
# --------------------------------------------------------------------------- #
def summarise_events(events: pd.DataFrame, carriers: pd.DataFrame, records: pd.DataFrame,
                     args) -> pd.DataFrame:
    rows = []
    for _, event in events.iterrows():
        key = (event["shortlist"], event["event_id"])
        carrier_group = carriers[(carriers["shortlist"] == key[0]) & (carriers["event_id"] == key[1])]
        with_vcf = carrier_group[carrier_group["vcf_available"] == "yes"]
        n_car = len(carrier_group)
        counts = carrier_group["carrier_label"].value_counts()
        n_sup = int(counts.get("supported", 0))
        n_weak = int(counts.get("weak", 0))
        n_noev = int(counts.get("no_evidence", 0))
        n_nf = int(counts.get("not_found", 0))
        n_found = len(with_vcf) - n_nf

        nc = records[(records["shortlist"] == key[0]) & (records["event_id"] == key[1]) &
                     (records["recorded_carrier"] == "no")]
        nc_pass = nc[nc["is_pass"]]
        nc_samples = sorted(nc_pass["sample_id"].unique())

        def event_label(col):
            carrier_counts = carrier_group[col].value_counts()
            supported_count, weak_count = int(carrier_counts.get("supported", 0)), int(carrier_counts.get("weak", 0))
            if n_found == 0:
                return "not_found_in_raw"
            if supported_count >= max(1, math.ceil(args.min_supported_fraction * len(with_vcf))):
                return "supported"
            if supported_count >= 1:
                return "partially_supported"
            if weak_count >= 1:
                return "weak"
            return "no_evidence"

        label = event_label("carrier_label")
        label_strict = event_label("carrier_label_strict")

        fidelity = []
        if n_nf:
            fidelity.append(f"{n_nf} recorded carrier(s) without a raw call")
        if nc_samples:
            fidelity.append(f"{len(nc_samples)} non-carrier(s) with a PASS raw call")
        if n_car - len(with_vcf):
            fidelity.append(f"{n_car - len(with_vcf)} carrier VCF(s) missing")

        rows.append({
            "shortlist": event["shortlist"], "event_id": event["event_id"],
            "review_event_id": event["review_event_id"], "review_rank": event.get("review_rank", ""),
            "tier": event["tier"], "chrom": event["chrom"], "start": event["start"], "end": event["end"],
            "sv_type": event["sv_type"], "sv_length_bp": event.get("sv_length_bp", ""), "genes": event["genes"],
            "highest_alsod_evidence": event.get("highest_alsod_evidence", ""),
            "acmg_classes": event.get("acmg_classes", ""),
            "n_recorded_carriers": n_car, "n_carriers_with_vcf": len(with_vcf),
            "n_carriers_raw_call_found": n_found,
            "n_carriers_supported": n_sup, "n_carriers_weak": n_weak,
            "n_carriers_no_evidence": n_noev, "n_carriers_not_found": n_nf,
            "n_carriers_both_callers": int(carrier_group["both_callers"].astype(bool).sum()),
            "n_carriers_precise_breakpoint": int(carrier_group["precise_breakpoint"].astype(bool).sum()),
            "median_split_read_support": carrier_group["split_read_support"].median(),
            "median_paired_end_support": carrier_group["paired_end_support"].median(),
            "median_tiddit_depth_ratio": carrier_group["tiddit_depth_ratio"].median(),
            "any_low_mapq": bool(carrier_group["low_mapq"].astype(bool).any()),
            "n_noncarriers_with_pass_raw_call": len(nc_samples),
            "noncarriers_with_pass_raw_call": ";".join(nc_samples[:50]) + (" ..." if len(nc_samples) > 50 else ""),
            "event_evidence_label": label,
            "event_evidence_label_strict": label_strict,
            "fidelity_flags": "; ".join(fidelity),
        })
    return pd.DataFrame(rows)



def raw_call_retier(records: pd.DataFrame, event_evidence: pd.DataFrame, args) -> pd.DataFrame:
    """Recount carriers from the raw caller VCFs and re-apply the chapter's tier rules.

    Raw carriers = recorded carriers with a PASS raw call, plus non-carriers with a PASS
    raw call whose breakpoints are within --tight-bp of the event (insertions: start only).
    Tier rules (as in the chapter): Tier 4 if no carrier, >= 3 control carriers, control
    frequency >= 5%, cohort frequency >= 10%, or >= 1 control carrier with control
    frequency >= case frequency; Tier 3 if any control carrier below those thresholds;
    otherwise the original Tier 1/2 assignment is kept.
    """
    pass_records = records[records["is_pass"]].copy()
    start_difference = pd.to_numeric(pass_records["start_diff"], errors="coerce").abs()
    end_difference = pd.to_numeric(pass_records["end_diff"], errors="coerce").abs()
    ins = pass_records["event_sv_type"].eq("INS") | pass_records["raw_sv_type"].eq("INS")
    tight = (start_difference <= args.tight_bp) & ((end_difference <= args.tight_bp) | ins)
    keep = pass_records[(pass_records["recorded_carrier"] == "yes") | tight]
    carrier_counts = (keep.groupby(["shortlist", "event_id", "group"])["sample_id"].nunique()
           .unstack("group", fill_value=0).reindex(columns=["CASE", "CTRL"], fill_value=0)
           .rename(columns={"CASE": "raw_case_carriers", "CTRL": "raw_control_carriers"}).reset_index())
    out = event_evidence.merge(carrier_counts, on=["shortlist", "event_id"], how="left")
    out[["raw_case_carriers", "raw_control_carriers"]] = out[["raw_case_carriers", "raw_control_carriers"]].fillna(0).astype(int)
    case_count, control_count = out["raw_case_carriers"], out["raw_control_carriers"]
    case_frequency, control_frequency = case_count / args.case_n, control_count / args.control_n
    overall_frequency = (case_count + control_count) / (args.case_n + args.control_n)
    out["raw_case_frequency"], out["raw_control_frequency"] = case_frequency.round(4), control_frequency.round(4)
    tier_four = (case_count + control_count == 0) | (control_count >= 3) | (control_frequency >= 0.05) | (overall_frequency >= 0.10) | ((control_count >= 1) & (control_frequency >= case_frequency))
    original_tier = pd.to_numeric(out["tier"], errors="coerce")
    updated_tier = original_tier.where(~tier_four, 4)
    updated_tier = updated_tier.where(~((~tier_four) & (control_count > 0) & original_tier.isin([1, 2])), 3)
    failed = (case_count + control_count == 0) & (out["n_carriers_raw_call_found"] > 0)
    updated_tier = updated_tier.where(~failed)
    out["tier_raw_recount"] = updated_tier.astype("Int64")
    out["raw_call_status"] = np.where(failed, "recorded carriers' raw calls all failed caller filters",
                                      np.where(case_count + control_count == 0, "no raw call", "PASS raw call(s)"))
    out["tier_changed"] = (out["tier_raw_recount"] != original_tier).map({True: "yes", False: "no"})
    out["raw_case_only"] = ((control_count == 0) & (case_count > 0)).map({True: "yes", False: "no"})
    return out

def suggest_outcome(event: pd.Series) -> tuple[str, str]:
    risk = []
    if nonempty(event.get("str_loci_nearby")):
        risk.append("near STR locus")
    if nonempty(event.get("ctx_SegDup_left")) or nonempty(event.get("ctx_SegDup_right")):
        risk.append("segmental duplication at breakpoint")
    blacklist_columns = [column for column in event.index if column.startswith("ctx_ENCODE_blacklist")]
    if any(nonempty(event[column]) for column in blacklist_columns):
        risk.append("ENCODE blacklist at breakpoint")
    if str(event["any_low_mapq"]).lower() == "true":
        risk.append("low mapping quality")

    evidence_label = event["event_evidence_label"]
    if evidence_label in ("not_found_in_raw", "no_evidence"):
        out = "likely_artefact_or_merge_error"
    elif evidence_label == "supported" and not risk and not nonempty(event["fidelity_flags"]):
        out = "technically_supported"
    elif evidence_label in ("supported", "partially_supported"):
        out = "supported_with_caveats"
    elif risk:
        out = "likely_artefact_or_merge_error"
    else:
        out = "uncertain"
    return out, "; ".join(risk)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", "--in-dir", dest="input_dir", type=Path, required=True, help="Output directory of sv_review_extract.py")
    parser.add_argument("--out-dir", type=Path, help="Default: --input-dir")
    parser.add_argument("--min-split", type=int, default=3, help="Min split reads (Manta SR alt or TIDDIT RV); default 3")
    parser.add_argument("--min-pairs", type=int, default=3, help="Min discordant pairs (Manta PR alt or TIDDIT DV); default 3")
    parser.add_argument("--min-depth-len", type=int, default=1000,
                    help="Min event length (bp) for the read-depth check; default 1000")
    parser.add_argument("--del-max-ratio", type=float, default=0.75, help="DEL depth ratio upper bound; default 0.75")
    parser.add_argument("--dup-min-ratio", type=float, default=1.25, help="DUP depth ratio lower bound; default 1.25")
    parser.add_argument("--max-lq", type=float, default=0.3, help="TIDDIT low-quality read fraction flag; default 0.3")
    parser.add_argument("--min-supported-fraction", type=float, default=0.5,
                    help="Fraction of carriers that must be 'supported' for an event to be 'supported'; default 0.5")
    parser.add_argument("--str-bed", dest="str_bed_path", type=Path, help="BED of STR loci (chrom, start, end, name)")
    parser.add_argument("--str-padding", type=int, default=100, help="Padding (bp) for STR overlap; default 100")
    parser.add_argument("--tight-bp", type=int, default=50,
                    help="Max breakpoint distance (bp) for counting a non-carrier's raw call as the same event "
                         "in the carrier recount; default 50")
    parser.add_argument("--case-n", type=int, default=296, help="CASE-prefixed denominator; default 296")
    parser.add_argument("--control-n", type=int, default=51, help="CTRL-prefixed denominator; default 51")
    parser.add_argument("--small-sv-len", type=int, default=500,
                    help="Events shorter than this (bp; ~fragment length) can be supported by a PASS precise "
                         "Manta split-read junction alone; default 500")
    parser.add_argument("--tiddit-cov-order", choices=["A,between,B", "A,B,between"], default="A,between,B",
                    help="Order of the three TIDDIT FORMAT/COV values (default A,between,B; see docstring)")
    parser.add_argument("--intersection-annotsv-files", type=Path, nargs="*", default=[],
                        help="Intersection AnnotSV TSV files with explicit provenance")
    parser.add_argument("--union-annotsv-files", type=Path, nargs="*", default=[],
                        help="Union AnnotSV TSV files; context is joined to union_only events")
    args = parser.parse_args(argv)
    out_dir = args.out_dir or args.input_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    read_input_table = lambda filename: pd.read_csv(args.input_dir / filename, sep="\t", dtype=str, keep_default_na=False)
    events = read_input_table("review_events.tsv")
    records = read_input_table("raw_record_matches.tsv")
    carriers = read_input_table("carrier_status.tsv")
    original_record_count = len(records)
    records = records.drop_duplicates(subset=["shortlist", "event_id", "sample_id", "caller", "CHROM", "POS", "ID", "ALT"])
    if len(records) < original_record_count:
        print(f"[warn] {original_record_count - len(records)} duplicate raw records removed "
              f"(the same participant was probably read from more than one VCF, e.g. .vcf and .vcf.gz)")
    print(f"[info] {len(events)} events, {len(records)} matched raw records, {len(carriers)} carrier-event pairs")

    # ---- per record
    if records.empty:
        record_results = records.copy()
        for column in RECORD_EVIDENCE_COLUMNS:
            record_results[column] = pd.Series(dtype=bool if column == "is_pass" else object)
    else:
        parsed = pd.DataFrame([record_evidence(record, args.tiddit_cov_order) for _, record in records.iterrows()],
                              index=records.index, columns=RECORD_EVIDENCE_COLUMNS)
        record_results = pd.concat([records, parsed], axis=1)
    # empirical check of the COV order: median of the three raw COV values by type and genotype
    tiddit_records = record_results[record_results["caller"] == "TIDDIT"].copy()
    if not tiddit_records.empty:
        raw = tiddit_records["SAMPLE_VALUES"].str.split(":")
        fmt = tiddit_records["FORMAT"].str.split(":")
        covs = [dict(zip(format_fields, sample_values)).get("COV", "") for format_fields, sample_values in zip(fmt, raw)]
        cv = pd.Series(covs, index=tiddit_records.index).str.split(",", expand=True).apply(pd.to_numeric, errors="coerce")
        if cv.shape[1] >= 3:
            tiddit_records[["cov_value_1", "cov_value_2", "cov_value_3"]] = cv.iloc[:, :3].values
            tiddit_records["len"] = pd.to_numeric(tiddit_records["raw_svlen"], errors="coerce").abs()
            chk = (tiddit_records[(tiddit_records["len"] >= args.min_depth_len) & tiddit_records["raw_sv_type"].isin(["DEL", "DUP"])]
                   .groupby(["raw_sv_type", "gt"])[["cov_value_1", "cov_value_2", "cov_value_3"]]
                   .agg(["median", "size"]))
            chk.columns = ["_".join(column) for column in chk.columns]
            chk.to_csv(out_dir / "tiddit_cov_order_check.tsv", sep="\t")
            print("[info] TIDDIT COV order check (median raw values; the 'between' value should be ~half "
                  "the flanks for 0/1 DEL and ~0 for 1/1 DEL):")
            print(chk.filter(like="median").round(1).to_string())
    record_results.to_csv(out_dir / "evidence_per_record.tsv", sep="\t", index=False)
    print(f"[out] {out_dir / 'evidence_per_record.tsv'}")

    # ---- per carrier
    if events.duplicated(["shortlist", "event_id"]).any():
        raise ValueError("review_events.tsv contains duplicate callset/event keys")
    event_index = events.set_index(["shortlist", "event_id"])
    grouped = {group_key: carrier_records for group_key, carrier_records in record_results[record_results["recorded_carrier"] == "yes"]
               .groupby(["shortlist", "event_id", "sample_id"])} if not record_results.empty else {}
    empty = record_results.iloc[0:0]
    rows = []
    for _, carrier in carriers.iterrows():
        event = event_index.loc[(carrier["shortlist"], carrier["event_id"])]
        carrier_records = grouped.get((carrier["shortlist"], carrier["event_id"], carrier["sample_id"]), empty)
        rows.append({**carrier.to_dict(), "sv_type": event["sv_type"], "genes": event["genes"],
                     **carrier_evidence(carrier_records, event, args)})
    # Keep the complete output schema even when carrier_status.tsv has no rows.
    # DataFrame([]) has no columns, which otherwise breaks event summaries and
    # writes a carrier TSV without a header.
    carrier_columns = list(dict.fromkeys([
        *carriers.columns, "sv_type", "genes", *CARRIER_EVIDENCE_COLUMNS,
    ]))
    carrier_results = pd.DataFrame(rows, columns=carrier_columns)
    if carriers.empty:
        print("[warn] carrier_status.tsv contains no recorded carrier-event pairs; "
              "carrier evidence cannot be assessed. Check the extraction inputs; "
              "raw-call recounts will still be produced.")
    if not carrier_results.empty:
        carrier_results.loc[carrier_results["vcf_available"] == "no", ["carrier_label", "carrier_label_reason"]] = ["vcf_missing", "no VCF for participant"]
    carrier_results.to_csv(out_dir / "evidence_per_carrier.tsv", sep="\t", index=False)
    print(f"[out] {out_dir / 'evidence_per_carrier.tsv'} ({len(carrier_results)} rows)")

    # ---- per event
    event_evidence = summarise_events(events, carrier_results, record_results, args)
    event_evidence = raw_call_retier(record_results, event_evidence, args)
    if args.intersection_annotsv_files or args.union_annotsv_files:
        context = combine_context_frames([
            load_annotsv_context(args.intersection_annotsv_files, "intersection"),
            load_annotsv_context(args.union_annotsv_files, "union_only"),
        ])
        event_evidence = event_evidence.merge(context, how="left", on=["shortlist", "event_id"], validate="one_to_one")
        print(f"[info] AnnotSV context joined for {event_evidence.filter(like='ctx_').notna().any(axis=1).sum()} events")
    if args.str_bed_path:
        event_evidence["str_loci_nearby"] = str_overlaps(event_evidence, args.str_bed_path, args.str_padding)
    else:
        event_evidence["str_loci_nearby"] = ""
    outcomes = event_evidence.apply(suggest_outcome, axis=1, result_type="expand")
    event_evidence["context_risk"] = outcomes[1]
    event_evidence["suggested_outcome"] = outcomes[0]
    failed = event_evidence["raw_call_status"].str.startswith("recorded carriers")
    event_evidence.loc[failed, "suggested_outcome"] = "excluded_failed_caller_filter"
    strict_outcomes = event_evidence.assign(event_evidence_label=event_evidence["event_evidence_label_strict"]).apply(
        suggest_outcome, axis=1, result_type="expand")
    event_evidence["suggested_outcome_strict"] = strict_outcomes[0]
    event_evidence.loc[failed, "suggested_outcome_strict"] = "excluded_failed_caller_filter"
    event_evidence["manual_review_decision"] = ""   # for you to fill in
    event_evidence["manual_review_notes"] = ""
    event_evidence.to_csv(out_dir / "evidence_per_event.tsv", sep="\t", index=False)
    print(f"[out] {out_dir / 'evidence_per_event.tsv'} ({len(event_evidence)} rows)")

    summary = (event_evidence.groupby(["shortlist", "tier", "tier_raw_recount", "suggested_outcome"], dropna=False).size()
            .rename("n_events").reset_index())
    summary.to_csv(out_dir / "evidence_summary.tsv", sep="\t", index=False)
    print(f"[out] {out_dir / 'evidence_summary.tsv'}")
    print(event_evidence.groupby(["shortlist", "suggested_outcome"]).size().to_string())
    print("[info] tier before (rows) vs after raw-call recount (columns):")
    print(pd.crosstab([event_evidence["shortlist"], event_evidence["tier"]], event_evidence["tier_raw_recount"].astype("string").fillna("excluded")).to_string())

    with open(out_dir / "evidence_thresholds.json", "w", encoding="utf-8") as handle:
        json.dump({"script": "sv_review_evidence.py", "version": __version__,
                   "run": _dt.datetime.now().isoformat(timespec="seconds"),
                   "parameters": {name: str(value) for name, value in vars(args).items()},
                   "tiddit_cov_order": args.tiddit_cov_order}, handle, indent=2)
    print(f"[out] {out_dir / 'evidence_thresholds.json'}")


if __name__ == "__main__":
    main()
