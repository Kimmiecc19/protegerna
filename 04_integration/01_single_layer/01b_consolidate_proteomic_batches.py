#!/usr/bin/env python3
"""Stream batch DIA-NN TSVs into audited cohort tables.
Removed the following samples:
batch1 CASE-NEUBK117YXL-5944-P_B09_profile.mzML 112 0
batch1 CASE-NEUFH122WN7-5930-P_B08_profile.mzML 0 0
batch5 CASE-NEUMN012EVP-5972-P_C01_profile.mzML 188 0
batch6 CASE-NEUJY426MBU-5951-P_B10_profile.mzML 264 0
"""
import argparse
import csv
import gzip
import hashlib
import itertools
import json
import math
import sqlite3
import sys
from collections import Counter
from contextlib import contextmanager, ExitStack, closing
from pathlib import Path

VERSION = "1.4.0"
MS = "ProteinName PeptideSequence PrecursorCharge Intensity Run FragmentIon ProductCharge IsotopeLabelType Condition BioReplicate Fraction".split()
META = ["Cohort.Batch", "Cohort.Run", "Cohort.Participant", "Cohort.SampleType", "Cohort.Condition", "Cohort.Fraction"]
MISSING = {"", "NA", "NaN", "nan", "N/A"}

@contextmanager
def reader(path, delimiter="\t"):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        table = csv.DictReader(handle, delimiter=delimiter)
        if not table.fieldnames or len(set(table.fieldnames)) != len(table.fieldnames):
            raise ValueError(f"Missing/duplicate headers: {path}")
        yield table

def require(fields, needed, label):
    missing = set(needed) - set(fields)
    if missing:
        raise ValueError(f"{label}: missing columns {sorted(missing)}")

def rows(path):
    with reader(path) as table:
        return list(table)

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def number(value, label):
    if value in MISSING:
        return None
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric value in {label}: {value!r}") from None
    if not math.isfinite(result):
        raise ValueError(f"Nonfinite value in {label}: {value!r}")
    return result

@contextmanager
def writer(path, fields, delimiter="\t"):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "wt", encoding="utf-8", newline="") as handle:
        table = csv.DictWriter(handle, fieldnames=fields, delimiter=delimiter)
        table.writeheader()
        yield table

def main(argv=None):
    with ExitStack() as resources:
        return consolidate(argv, resources)

def consolidate(argv, resources):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", required=True, type=Path)
    parser.add_argument("--samples", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--expected-batches", type=int, default=6)
    # Participants with at least one run that is NOT excluded via --exclude-runs.
    # The validated six-batch manifest contains 346 participants (WGS has 347).
    parser.add_argument("--expected-participants", type=int, default=346)
    parser.add_argument("--exclude-runs", type=Path,
                        help="TSV with columns batch, file_name, reason; listed runs are validated, counted "
                             "in run_coverage.tsv/excluded_runs.tsv, and left out of every data output")
    parser.add_argument("--msstats-run-aliases", type=Path,
                        help="TSV with columns batch, observed_run, msstats_run, reason; MSstats rows whose Run is "
                             "observed_run are assigned to the manifest run msstats_run (input files are not edited)")
    parser.add_argument("--q-value", type=float, default=.01)
    parser.add_argument("--global-q-value", type=float, default=.01)
    parser.add_argument("--pg-q-value", type=float, default=.01)
    parser.add_argument("--global-pg-q-value", type=float, default=.01)
    parser.add_argument("--protein-quantity", choices=["PG.MaxLFQ", "PG.Quantity", "PG.Normalised"], default="PG.MaxLFQ")
    args = parser.parse_args(argv)
    filters = dict(zip(["Q.Value", "Global.Q.Value", "PG.Q.Value", "Global.PG.Q.Value"],
                       [args.q_value, args.global_q_value, args.pg_q_value, args.global_pg_q_value]))
    if any(not 0 <= v <= 1 for v in filters.values()):
        raise ValueError("Q-value thresholds must be within [0, 1]")
    batches, samples = rows(args.batches), rows(args.samples)
    if not batches or not samples:
        raise ValueError("Both manifests must contain data")
    require(batches[0], ["batch", "report", "msstats", "stats", "database_id", "library_id"], "batch manifest")
    required_samples = ["batch", "report_run", "msstats_run", "file_name", "participant_id", "sample_type", "condition", "fraction"]
    require(samples[0], required_samples, "sample manifest")
    batch_ids = [b["batch"] for b in batches]
    if len(set(batch_ids)) != len(batch_ids) or len(batches) != args.expected_batches:
        raise ValueError("Duplicate batch names or unexpected batch count")
    for field in ["database_id", "library_id"]:
        if any(not b[field] for b in batches) or len({b[field] for b in batches}) != 1:
            raise ValueError(f"All batches must declare the same nonempty {field}; harmonize searches first")
    lookups = {field: {} for field in ["report_run", "msstats_run", "file_name"]}
    for sample in samples:
        if any(sample.get(f) is None for f in required_samples):
            raise ValueError("Malformed sample manifest row")
        if sample["batch"] not in batch_ids or sample["sample_type"] not in {"participant", "qc", "blank", "reference"}:
            raise ValueError(f"Invalid batch/sample_type: {sample}")
        if not sample["condition"] or not sample["fraction"]:
            raise ValueError("Condition and fraction must be explicit")
        if sample["sample_type"] == "participant" and not sample["participant_id"]:
            raise ValueError("Participant runs need participant_id")
        sample["cohort_run"] = f'{sample["batch"]}::{sample["report_run"]}'
        if "::" in sample["batch"] or "::" in sample["report_run"]:
            raise ValueError("Batch and run names cannot contain '::'")
        for field, lookup in lookups.items():
            key = (sample["batch"], sample[field])
            if not sample[field] or key in lookup:
                raise ValueError(f"Empty/duplicate {field} within batch: {key}")
            lookup[key] = sample
    excluded = {}
    if args.exclude_runs:
        exclusions = rows(args.exclude_runs)
        if exclusions:
            require(exclusions[0], ["batch", "file_name", "reason"], "exclusion list")
        for item in exclusions:
            key = (item["batch"], item["file_name"])
            if key not in lookups["file_name"]:
                raise ValueError(f"Excluded run is not in the sample manifest: {key}; mapping uses exact strings")
            if not (item["reason"] or "").strip():
                raise ValueError(f"Excluded run needs a reason: {key}")
            run = lookups["file_name"][key]["cohort_run"]
            if run in excluded:
                raise ValueError(f"Duplicate exclusion: {key}")
            excluded[run] = item["reason"].strip()
    aliases = {}
    if args.msstats_run_aliases:
        alias_rows = rows(args.msstats_run_aliases)
        if alias_rows:
            require(alias_rows[0], ["batch", "observed_run", "msstats_run", "reason"], "MSstats alias list")
        for item in alias_rows:
            key, target = (item["batch"], item["observed_run"]), (item["batch"], item["msstats_run"])
            if not item["observed_run"] or key in lookups["msstats_run"] or key in aliases:
                raise ValueError(f"MSstats alias observed_run must be nonempty, unique and not a manifest msstats_run: {key}")
            if target not in lookups["msstats_run"]:
                raise ValueError(f"MSstats alias target is not in the sample manifest: {target}")
            if not (item["reason"] or "").strip():
                raise ValueError(f"MSstats alias needs a reason: {key}")
            aliases[key] = {"batch": item["batch"], "observed_run": item["observed_run"], "msstats_run": item["msstats_run"],
                            "cohort_run": lookups["msstats_run"][target]["cohort_run"], "reason": item["reason"].strip(), "rows": 0}
    included = [s for s in samples if s["cohort_run"] not in excluded]
    if not included:
        raise ValueError("Every manifest run is excluded")
    manifest_participants = {s["participant_id"] for s in samples if s["sample_type"] == "participant"}
    participants = {s["participant_id"] for s in included if s["sample_type"] == "participant"}
    if len(participants) != args.expected_participants:
        raise ValueError(f"Expected {args.expected_participants} included participants; found {len(participants)} "
                         f"({len(manifest_participants)} in manifest, {len(manifest_participants - participants)} with every run excluded)")
    headers, provenance = {}, []
    for batch in batches:
        for kind in ["report", "msstats", "stats"]:
            path = Path(batch[kind])
            if not path.is_absolute():
                path = args.batches.resolve().parent / path
            batch[kind] = path
            with reader(path, "," if kind == "msstats" else "\t") as table:
                fields = table.fieldnames
                needed = {"report": ["Run", "File.Name", "Protein.Group", args.protein_quantity] + list(filters),
                          "msstats": MS, "stats": ["File.Name"]}[kind]
                require(fields, needed, str(path))
                if set(fields) & set(META):
                    raise ValueError(f"Input already contains cohort columns: {path}")
                if kind in headers and fields != headers[kind]:
                    raise ValueError(f"Inconsistent {kind} schema between batches: {path}")
                headers[kind] = fields
            provenance.append({"batch": batch["batch"], "type": kind, "path": str(path), "sha256": sha256(path)})
    args.outdir.mkdir(parents=True, exist_ok=False)
    out = args.outdir
    # Leave a failure marker if validation fails during streaming; never reuse a partial output.
    (out / "INCOMPLETE.txt").write_text("Outputs are incomplete until SUCCESS.json exists.\n")
    db = resources.enter_context(closing(sqlite3.connect(out / "cohort.sqlite")))
    db.execute("CREATE TABLE protein (feature TEXT, run TEXT, value REAL, PRIMARY KEY(feature,run))")
    db.execute("CREATE TABLE seen (kind TEXT, run TEXT, feature TEXT, PRIMARY KEY(kind,run,feature))")
    counts = {s["cohort_run"]: Counter() for s in samples}

    def identify(batch, field, value):
        key = (batch, value)
        if key not in lookups[field]:
            raise ValueError(f"Unmapped {field}: {key}; mapping uses exact strings")
        return lookups[field][key]

    def annotate(row, sample):
        return dict(row, **dict(zip(META, [sample["batch"], sample["cohort_run"], sample["participant_id"],
                                          sample["sample_type"], sample["condition"], sample["fraction"]])))

    def unique(kind, run, feature):
        try:
            db.execute("INSERT INTO seen VALUES (?,?,?)", (kind, run, feature))
        except sqlite3.IntegrityError:
            raise ValueError(f"Duplicate {kind} measurement: {run}, {feature}") from None

    with writer(out / "diann_report.all.tsv.gz", headers["report"] + META) as all_report, \
         writer(out / "diann_report.filtered.tsv.gz", headers["report"] + META) as filtered:
        for batch in batches:
            with reader(batch["report"]) as table:
                require(table.fieldnames, ["Precursor.Id"], str(batch["report"]))
                for row in table:
                    s = identify(batch["batch"], "report_run", row["Run"])
                    if row["File.Name"] != s["file_name"]:
                        raise ValueError(f"File.Name disagrees with sample manifest for {s['cohort_run']}")
                    run = s["cohort_run"]
                    unique("precursor", run, row["Precursor.Id"])
                    counts[run]["report_rows"] += 1
                    if run in excluded:
                        continue
                    record = annotate(row, s)
                    all_report.writerow(record)
                    qvalues = {key: number(row[key], key) for key in filters}
                    if any(v is not None and not 0 <= v <= 1 for v in qvalues.values()):
                        raise ValueError(f"Q-value outside [0,1] in {run}")
                    if any(qvalues[key] is None or qvalues[key] > limit for key, limit in filters.items()):
                        continue
                    filtered.writerow(record)
                    counts[run]["filtered_rows"] += 1
                    value = number(row[args.protein_quantity], args.protein_quantity)
                    if value is not None and value < 0:
                        raise ValueError(f"Negative protein quantity: {run}")
                    value = value if value else None  # zero is missing, never log2(0)
                    feature = row["Protein.Group"]
                    if not feature:
                        raise ValueError(f"Empty Protein.Group: {run}")
                    previous = db.execute("SELECT value FROM protein WHERE feature=? AND run=?", (feature, run)).fetchone()
                    if previous and previous[0] != value:
                        raise ValueError(f"Conflicting repeated protein quantities: {feature}, {run}")
                    db.execute("INSERT OR IGNORE INTO protein VALUES (?,?,?)", (feature, run, value))
            db.commit()
    with writer(out / "msstats.original.csv.gz", headers["msstats"] + META, ",") as original, \
         writer(out / "msstats.cohort.csv.gz", MS, ",") as remapped:
        for batch in batches:
            with reader(batch["msstats"], ",") as table:
                for row in table:
                    alias = aliases.get((batch["batch"], row["Run"]))
                    if alias:
                        alias["rows"] += 1
                    s = identify(batch["batch"], "msstats_run", alias["msstats_run"] if alias else row["Run"])
                    run = s["cohort_run"]
                    if row["Fraction"] != s["fraction"]:
                        raise ValueError(f"MSstats Fraction disagrees with mapping: {run}")
                    key = json.dumps([row[f] for f in ["ProteinName", "PeptideSequence", "PrecursorCharge", "FragmentIon", "ProductCharge", "IsotopeLabelType", "Fraction"]])
                    unique("msstats", run, key)
                    intensity = number(row["Intensity"], "Intensity")
                    if intensity is not None and intensity < 0:
                        raise ValueError(f"Negative MSstats intensity: {run}")
                    counts[run]["msstats_rows"] += 1
                    if run in excluded:
                        continue
                    original.writerow(annotate(row, s))
                    if s["sample_type"] == "participant":
                        record = {f: row[f] for f in MS}
                        record.update(Run=run, BioReplicate=s["participant_id"], Condition=s["condition"])
                        remapped.writerow(record)
            db.commit()
    unused = [key for key, alias in aliases.items() if not alias["rows"]]
    if unused:
        raise ValueError(f"MSstats aliases matched no rows: {unused}")
    with writer(out / "run_stats.tsv", headers["stats"] + META) as output:
        for batch in batches:
            with reader(batch["stats"]) as table:
                for row in table:
                    s = identify(batch["batch"], "file_name", row["File.Name"])
                    unique("stats", s["cohort_run"], "stats")
                    counts[s["cohort_run"]]["stats_rows"] += 1
                    if s["cohort_run"] in excluded:
                        continue
                    output.writerow(annotate(row, s))
        for sample in included:
            if not counts[sample["cohort_run"]]["stats_rows"]:
                record = dict.fromkeys(headers["stats"], "NA")
                record["File.Name"] = sample["file_name"]
                output.writerow(annotate(record, sample))
    represented = {s["participant_id"] for s in included if s["sample_type"] == "participant" and counts[s["cohort_run"]]["report_rows"]}
    sample_fields = list(samples[0])
    # sample_metadata.tsv lists included runs only, so it always matches the matrix columns.
    with writer(out / "sample_metadata.tsv", sample_fields) as output:
        output.writerows(included)
    excluded_records = [dict(s, exclusion_reason=excluded[s["cohort_run"]],
                             **{f: counts[s["cohort_run"]][f] for f in ["report_rows", "msstats_rows", "stats_rows"]})
                        for s in samples if s["cohort_run"] in excluded]
    with writer(out / "excluded_runs.tsv", sample_fields + ["exclusion_reason", "report_rows", "msstats_rows", "stats_rows"]) as output:
        output.writerows(excluded_records)
    with writer(out / "run_coverage.tsv", ["cohort_run", "report_rows", "filtered_rows", "msstats_rows", "stats_rows", "report_status", "exclusion_reason"]) as output:
        for run, count in counts.items():
            status = "excluded" if run in excluded else "no_report_rows" if not count["report_rows"] else "no_rows_pass_filters" if not count["filtered_rows"] else "rows_pass_filters"
            output.writerow(dict(cohort_run=run, report_status=status, exclusion_reason=excluded.get(run, ""),
                                 **{f: count[f] for f in ["report_rows", "filtered_rows", "msstats_rows", "stats_rows"]}))
    runs = [s["cohort_run"] for s in included]
    participant_samples = [s for s in included if s["sample_type"] == "participant"]
    single_run = len(participant_samples) == len(participants)
    def matrix(filename, selected, log=False, participant=False):
        columns = [s["participant_id"] if participant else s["cohort_run"] for s in selected]
        with writer(out / filename, ["Protein.Group"] + columns) as output:
            cursor = db.execute("SELECT feature,run,value FROM protein ORDER BY feature,run")
            for feature, group in itertools.groupby(cursor, key=lambda r: r[0]):
                values = {run: value for _, run, value in group}
                record = {"Protein.Group": feature}
                for s, col in zip(selected, columns):
                    value = values.get(s["cohort_run"])
                    record[col] = "NA" if value is None else math.log2(value) if log else value
                output.writerow(record)
    matrix("protein_by_run.tsv", included)
    matrix("protein_by_run.log2.tsv", included, log=True)
    if single_run:
        matrix("protein_by_participant.log2.tsv", participant_samples, log=True, participant=True)
    db.commit()
    db.close()
    summary = {"script_version": VERSION, "batches": len(batches), "participants": len(participants), "runs": len(runs),
               "filters": filters, "quantity": args.protein_quantity, "participant_matrix_written": single_run,
               "manifest_participants": len(manifest_participants), "manifest_runs": len(samples),
               "excluded_runs": [{"cohort_run": r["cohort_run"], "participant_id": r["participant_id"],
                                  "reason": r["exclusion_reason"]} for r in excluded_records],
               "participants_fully_excluded": sorted(manifest_participants - participants),
               "msstats_run_aliases": list(aliases.values()),
               "participants_without_report_rows": sorted(participants - represented),
               "runs_without_report_rows": [s["cohort_run"] for s in included if not counts[s["cohort_run"]]["report_rows"]],
               "runs_without_stats_rows": [s["cohort_run"] for s in included if not counts[s["cohort_run"]]["stats_rows"]],
               "inputs": provenance, "batch_metadata": [{k: str(v) for k, v in b.items()} for b in batches],
               "manifest_sha256": {str(p.resolve()): sha256(p) for p in [args.batches, args.samples] + [p for p in [args.exclude_runs, args.msstats_run_aliases] if p]},
               "warnings": ["Quantities retain within-batch processing; no cohort normalization, batch correction, or imputation applied.",
                            "Global q-values retain their original search scope; pooled FDR is not recalculated.",
                            "MSstats intensities and upstream filtering are preserved; report filters apply only to DIA-NN derived outputs.",
                            "Protein groups use exact strings; differing groups are not merged or split.",
                            "Novel peptide claims require independent provenance/uniqueness checks."]}
    if not single_run:
        summary["warnings"].append("Multiple participant runs: participant matrix omitted; summarize fractions/replicates with an appropriate model first.")
    if summary["runs_without_report_rows"]:
        summary["warnings"].append("Manifest runs without report rows retained as NA matrix columns; inspect run_coverage.tsv. No synthetic peptide/MSstats measurements were added.")
    if excluded:
        summary["warnings"].append(f"{len(excluded)} run(s) excluded via --exclude-runs and left out of all data outputs; "
                                   "see excluded_runs.tsv. They were still part of their batch's DIA-NN search.")
    if aliases:
        summary["warnings"].append(f"{sum(a['rows'] for a in aliases.values())} MSstats row(s) reassigned via --msstats-run-aliases; "
                                   "msstats.original.csv.gz keeps the observed Run, msstats.cohort.csv.gz uses the manifest run.")
    (out / "SUCCESS.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "INCOMPLETE.txt").unlink()
    print(f"Created {out}: {len(participants)} participants, {len(runs)} runs"
          + (f" ({len(excluded)} run(s) excluded, {len(manifest_participants - participants)} participant(s) fully excluded)" if excluded else ""))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, csv.Error, sqlite3.Error) as error:
        sys.exit(f"ERROR: {error}")
