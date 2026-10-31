"""Benchmark reconstructed variants against a small curated truth table."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd


KEYS = ("event_id", "tx", "variant")
FIELDS = ("protein_sequence", "frame_status", "premature_stop")


def benchmark(actual: pd.DataFrame, truth: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Match truth records by event/transcript/variant and score core biology."""
    required = set(KEYS) | {"protein_sequence"}
    for label, table in (("actual", actual), ("truth", truth)):
        missing = required - set(table.columns)
        if missing:
            raise ValueError(f"{label} table missing columns: {', '.join(sorted(missing))}")
    available = [field for field in FIELDS if field in actual.columns and field in truth.columns]
    joined = truth.merge(actual, on=list(KEYS), how="left", suffixes=("_expected", "_observed"), indicator=True)
    for field in available:
        expected = joined[f"{field}_expected"].fillna("").astype(str)
        observed = joined[f"{field}_observed"].fillna("").astype(str)
        joined[f"{field}_correct"] = expected.eq(observed)
    joined["record_reconstructed"] = joined["_merge"].eq("both")
    joined["all_assessed_fields_correct"] = joined["record_reconstructed"] & joined[
        [f"{field}_correct" for field in available]
    ].all(axis=1)
    total = len(joined)
    summary = {"truth_records": total, "reconstructed_records": int(joined["record_reconstructed"].sum()),
               "fully_correct_records": int(joined["all_assessed_fields_correct"].sum())}
    summary["reconstruction_recall"] = summary["reconstructed_records"] / total if total else 0.0
    summary["exact_record_accuracy"] = summary["fully_correct_records"] / total if total else 0.0
    for field in available:
        summary[f"{field}_accuracy"] = float(joined[f"{field}_correct"].mean()) if total else 0.0
    return joined.drop(columns=["_merge"]), summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark variant reconstruction against curated expected variants")
    parser.add_argument("--actual", required=True, help="Produced consequence/evidence TSV")
    parser.add_argument("--truth", required=True, help="Curated TSV with event_id, tx, variant, and expected protein_sequence")
    parser.add_argument("--out_tsv", required=True, help="Per-record comparison TSV")
    parser.add_argument("--out_json", required=True, help="Aggregate benchmark metrics JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    details, summary = benchmark(pd.read_csv(args.actual, sep="\t"), pd.read_csv(args.truth, sep="\t"))
    Path(args.out_tsv).parent.mkdir(parents=True, exist_ok=True)
    details.to_csv(args.out_tsv, sep="\t", index=False)
    Path(args.out_json).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
