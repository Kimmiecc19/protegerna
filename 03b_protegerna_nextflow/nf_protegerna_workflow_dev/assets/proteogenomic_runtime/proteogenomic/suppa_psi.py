"""SUPPA PSI loading and event-evidence evaluation."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
from .provenance import sample_provenance
from .suppa_parsing import normalise_event_id


def evaluate_psi_event(
    event_id: str,
    psi_lookup: Optional[Dict[str, Dict]],
    min_psi: float,
    min_samples: int,
    keep_events_missing_psi: bool = False,
) -> Tuple[bool, Dict]:
    """Evaluate whether one IOE event satisfies the optional PSI filter.

    An event passes when at least ``min_samples`` non-missing PSI observations
    are greater than or equal to ``min_psi``. When no lookup is supplied, PSI
    filtering is disabled and every event is retained.
    """
    event_id = normalise_event_id(event_id)

    if psi_lookup is None:
        return True, {
            "psi_filter_applied": False,
            "psi_found": None,
            "psi_mean": None,
            "psi_max": None,
            "psi_valid_samples": None,
            "psi_total_samples": None,
            "psi_samples_passing": None,
            "psi_min_threshold": min_psi,
            "psi_min_samples": min_samples,
            "passed_filter": True,
            "reason": "psi_filter_not_applied",
        }

    stats = psi_lookup.get(event_id) if event_id else None
    if stats is None:
        keep = bool(keep_events_missing_psi)
        return keep, {
            "psi_filter_applied": True,
            "psi_found": False,
            "psi_mean": None,
            "psi_max": None,
            "psi_valid_samples": 0,
            "psi_total_samples": stats.get("n_total", 0) if stats else 0,
            "psi_samples_passing": 0,
            "psi_min_threshold": min_psi,
            "psi_min_samples": min_samples,
            "passed_filter": keep,
            "reason": (
                "event_missing_from_psi_kept"
                if keep
                else "event_missing_from_psi"
            ),
        }

    values = [
        float(value)
        for value in stats.get("values", [])
        if value is not None and not pd.isna(value)
    ]
    passing = sum(value >= min_psi for value in values)
    keep = passing >= min_samples

    return keep, {
        "psi_filter_applied": True,
        "psi_found": True,
        "psi_mean": stats.get("mean"),
        "psi_max": stats.get("max"),
        "psi_valid_samples": len(values),
        "psi_total_samples": stats.get("n_total", len(values)),
        "psi_samples_passing": passing,
        "psi_min_threshold": min_psi,
        "psi_min_samples": min_samples,
        "passed_filter": keep,
        "reason": "passed_psi_filter" if keep else "insufficient_psi_support",
    }


def load_psi_files(psi_files, sample_metadata=None):
    """
    Load and combine one or more SUPPA PSI matrices.

    SUPPA PSI matrices contain event IDs in an unlabeled first column,
    followed by one column per sample. The first column must therefore
    be read as the DataFrame index.

    PSI values from all supplied files are pooled by event ID.

    Parameters
    ----------
    psi_files : sequence of str or pathlib.Path
        Paths to SUPPA PSI matrix files.

    Returns
    -------
    dict
        Dictionary keyed by SUPPA event ID. Each value contains:

        - values: all non-missing PSI values pooled across files
        - mean: mean PSI across non-missing observations
        - max: maximum observed PSI
        - n_observed: number of non-missing PSI observations
        - n_total: total number of sample positions across the files
        - source_files: files in which the event occurred
    """
    pooled_values = {}
    total_sample_counts = {}
    source_files = {}
    sample_details = {}

    if not psi_files:
        return {}

    for psi_file in psi_files:
        psi_path = Path(psi_file)

        if not psi_path.exists():
            logging.warning("PSI file not found: %s", psi_path)
            continue

        logging.info("Loading PSI matrix: %s", psi_path)

        try:
            psi_df = pd.read_csv(
                psi_path,
                sep="\t",
                index_col=0,
                na_values=["nan", "NaN", "NA", ""],
                keep_default_na=True,
            )
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            logging.warning(
                "Could not read PSI file %s: %s",
                psi_path,
                exc,
            )
            continue

        if psi_df.empty:
            logging.warning("PSI matrix is empty: %s", psi_path)
            continue

        if psi_df.shape[1] == 0:
            logging.warning(
                "PSI matrix contains no sample columns: %s",
                psi_path,
            )
            continue

        # Ensure all sample columns are numeric. Invalid entries become NaN.
        psi_df = psi_df.apply(pd.to_numeric, errors="coerce")

        n_samples = psi_df.shape[1]

        logging.info(
            "Read %d events across %d samples from %s",
            psi_df.shape[0],
            n_samples,
            psi_path,
        )

        for raw_event_id, row in psi_df.iterrows():
            event_id = normalise_event_id(raw_event_id)

            if event_id is None:
                continue

            values = row.dropna().astype(float).tolist()

            pooled_values.setdefault(event_id, []).extend(values)
            total_sample_counts[event_id] = (
                total_sample_counts.get(event_id, 0) + n_samples
            )
            source_files.setdefault(event_id, []).append(str(psi_path))
            details = sample_details.setdefault(event_id, {})
            for sample_name, value in row.items():
                if pd.isna(value):
                    continue
                provenance = sample_provenance(sample_name, psi_path, sample_metadata)
                details[provenance["sample_id"]] = provenance

    psi_lookup = {}

    for event_id, values in pooled_values.items():
        psi_lookup[event_id] = {
            "values": values,
            "mean": (
                sum(values) / len(values)
                if values
                else None
            ),
            "max": max(values) if values else None,
            "n_observed": len(values),
            "n_total": total_sample_counts.get(event_id, 0),
            "source_files": source_files.get(event_id, []),
            "sample_details": list(sample_details.get(event_id, {}).values()),
        }

    logging.info(
        "Loaded PSI values for %d unique events",
        len(psi_lookup),
    )

    return psi_lookup


def write_psi_filter_summary(rows, out_path):
    """Write one event-level record for each PSI filtering decision."""
    if not out_path:
        return

    preferred = [
        "source_file",
        "sample_id",
        "batch",
        "condition",
        "event_type",
        "event_id",
        "psi_filter_applied",
        "psi_found",
        "psi_mean",
        "psi_max",
        "psi_valid_samples",
        "psi_total_samples",
        "psi_samples_passing",
        "psi_min_threshold",
        "psi_min_samples",
        "passed_filter",
        "reason",
    ]

    df = pd.DataFrame(rows or [], columns=preferred if not rows else None)
    if not df.empty:
        ordered = [column for column in preferred if column in df.columns]
        ordered.extend(column for column in df.columns if column not in ordered)
        df = df[ordered]

    df.to_csv(out_path, sep="\t", index=False)
    logging.info(
        "Wrote PSI filter summary to %s (%d events; %d passed)",
        out_path,
        len(df),
        int(df["passed_filter"].fillna(False).astype(bool).sum())
        if "passed_filter" in df.columns
        else 0,
    )
