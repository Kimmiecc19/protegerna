"""Generate a caller-stratified final proteogenomic release audit."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

REASON_COLUMNS = ("exclusion_reason_codes", "fasta_exclusion_reasons", "dia_exclusion_reasons", "exclusion_reason")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, help="Producer/merge biological TSV files")
    parser.add_argument("--out_tsv", required=True)
    parser.add_argument("--out_json", required=True)
    return parser


def _truth(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _caller(row, path):
    return str(row.get("source") or row.get("caller") or Path(path).stem.split(".")[0] or "unknown")


def _positive_number(value):
    try:
        return float(value or 0) > 0
    except (TypeError, ValueError):
        return False


def _has_peptide_evidence(row):
    return (
        _truth(row.get("has_reference_unique_tryptic_peptide"))
        or _truth(row.get("has_unique_junction_peptide"))
        or _positive_number(row.get("n_eligible_tryptic_peptides"))
    )


def summarize(paths):
    counters = defaultdict(Counter)
    for path in paths:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                counter = counters[_caller(row, path)]
                counter["records"] += 1
                if _truth(row.get("transcript_selection_ambiguous")):
                    counter["transcript_ambiguous"] += 1
                counter[f"frame:{row.get('frame_status') or 'NA'}"] += 1
                if _truth(row.get("nmd_predicted")):
                    counter["nmd_predicted"] += 1
                if _has_peptide_evidence(row):
                    counter["peptide_evidence"] += 1
                reasons = next((str(row[c]) for c in REASON_COLUMNS if row.get(c)), "")
                for reason in filter(None, reasons.split(";")):
                    counter[f"exclusion:{reason}"] += 1
    return {caller: dict(sorted(values.items())) for caller, values in sorted(counters.items())}


def main(argv=None):
    args = build_parser().parse_args(argv)
    summary = summarize(args.inputs)
    rows = [
        {"caller": caller, "metric": metric, "count": count}
        for caller, metrics in summary.items() for metric, count in metrics.items()
    ]
    with Path(args.out_tsv).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["caller", "metric", "count"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    Path(args.out_json).write_text(
        json.dumps({"schema_version": "pgdb-release-report-v1", "callers": summary}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
