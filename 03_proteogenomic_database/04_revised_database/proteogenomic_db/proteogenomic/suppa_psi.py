"""SUPPA PSI loading and event-evidence evaluation."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from collections import Counter
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

    An event passes when at least ``min_samples`` distinct samples have a
    non-missing PSI greater than or equal to ``min_psi``. When no lookup is supplied, PSI
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
            "psi_total_samples": 0,
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


# Cell values that mean "PSI not defined" (SUPPA writes nan). Anything else must
# parse as a finite number in [0, 1]; malformed cells are errors, never "missing".
MISSING_PSI_TOKENS = frozenset({"", "nan", "-nan", "na", "n/a", "null", "none", "#n/a", "<na>"})
# Exact spellings handed to the CSV parser (the common case); other spellings or
# padded tokens are still recognised by the text check in _validated_psi_values.
_MISSING_PSI_NA_VALUES = MISSING_PSI_TOKENS | {
    "NaN", "NAN", "-NaN", "NA", "N/A", "NULL", "Null", "None", "#N/A", "<NA>",
}
PSI_TOLERANCE = 1e-9
_MAX_REPORTED_PROBLEMS = 5


def _validated_psi_values(psi_df: pd.DataFrame, psi_path: Path) -> pd.DataFrame:
    """Return a float PSI matrix, rejecting malformed and out-of-range cells.

    Declared missing tokens are NaN. Non-numeric cells, infinities and values
    outside 0-1 raise ``ValueError`` naming the file, event, sample and value,
    because silently dropping them would change an event's sample support.
    Columns the CSV parser already read as numbers (the normal case) are not
    re-parsed, so validation adds little cost to large matrices.
    """
    numeric_columns = {}
    for position, column in enumerate(psi_df.columns):
        series = psi_df.iloc[:, position]
        if pd.api.types.is_numeric_dtype(series):
            numeric_columns[position] = series.to_numpy(dtype=float)
            continue
        text = series.astype(object)
        values = np.array(pd.to_numeric(text, errors="coerce"), dtype=float)
        unparsed = np.flatnonzero(np.isnan(values))
        tokens = text.iloc[unparsed].map(lambda value: "" if value is None or value != value else str(value))
        missing = tokens.str.strip().str.lower().isin(MISSING_PSI_TOKENS).to_numpy()
        _raise_psi_problem(psi_df, psi_path, unparsed[~missing], position, "non-numeric")
        numeric_columns[position] = values
    matrix = np.column_stack([numeric_columns[i] for i in range(psi_df.shape[1])]) if psi_df.shape[1] else np.empty((len(psi_df), 0))
    with np.errstate(invalid="ignore"):
        out_of_range = ~np.isnan(matrix) & (
            ~np.isfinite(matrix) | (matrix < -PSI_TOLERANCE) | (matrix > 1 + PSI_TOLERANCE)
        )
    if out_of_range.any():
        rows, columns = np.nonzero(out_of_range)
        examples = "; ".join(
            f"event {psi_df.index[r]!s} sample {psi_df.columns[c]!s} = {float(matrix[r, c])}"
            for r, c in list(zip(rows, columns))[:_MAX_REPORTED_PROBLEMS]
        )
        raise ValueError(f"PSI matrix {psi_path} has {len(rows)} outside 0-1 value(s), e.g. {examples}")
    return pd.DataFrame(matrix, index=psi_df.index, columns=psi_df.columns)


def _raise_psi_problem(psi_df, psi_path, rows, position, label):
    if len(rows):
        examples = "; ".join(
            f"event {psi_df.index[r]!s} sample {psi_df.columns[position]!s} = {psi_df.iat[r, position]!r}"
            for r in rows[:_MAX_REPORTED_PROBLEMS]
        )
        raise ValueError(f"PSI matrix {psi_path} has {len(rows)} {label} value(s), e.g. {examples}")


def _raw_sample_columns(psi_path: Path, n_samples: int) -> list[str]:
    """Sample names exactly as written in the PSI header (before pandas de-duplication).

    SUPPA headers list only the samples (the event-ID column is unlabelled);
    labelled matrices carry one extra leading field. The last ``n_samples``
    fields are the sample columns in both layouts.
    """
    with psi_path.open("r", encoding="utf-8-sig") as handle:
        header = handle.readline().rstrip("\r\n").split("\t")
    if len(header) < n_samples:
        raise ValueError(f"PSI header has fewer fields than sample columns: {psi_path}")
    return [name.strip() for name in header[len(header) - n_samples:]]


def load_psi_files(psi_files, sample_metadata=None):
    """
    Load and combine one or more SUPPA PSI matrices.

    SUPPA PSI matrices contain event IDs in an unlabeled first column,
    followed by one column per sample. The first column must therefore
    be read as the DataFrame index.

    PSI values from all supplied files are pooled by event ID and canonical
    sample ID, so support is counted over distinct samples. A sample observed
    for the same event in more than one matrix must carry the same PSI value;
    conflicting duplicates are an error rather than being double counted.

    Every supplied file must be readable and contain at least one event and
    one sample column: a requested PSI filter never silently degrades into
    "no filter" or into partial evidence.

    Parameters
    ----------
    psi_files : sequence of str or pathlib.Path
        Paths to SUPPA PSI matrix files.

    Returns
    -------
    dict
        Dictionary keyed by SUPPA event ID. Each value contains:

        - values: one non-missing PSI value per distinct sample
        - mean: mean PSI across distinct samples with a value
        - max: maximum observed PSI
        - n_observed: number of distinct samples with a non-missing value
        - n_total: number of distinct samples in matrices containing the event
        - source_files: files in which the event occurred
    """
    pooled_values = {}
    sample_universe = {}
    source_files = {}
    sample_details = {}

    if not psi_files:
        return {}

    for psi_file in psi_files:
        psi_path = Path(psi_file)

        if not psi_path.is_file():
            raise FileNotFoundError(f"PSI file not found: {psi_path}")

        logging.info("Loading PSI matrix: %s", psi_path)

        try:
            # Declared missing tokens become NaN; any other non-numeric cell makes
            # its column non-numeric and is rejected by _validated_psi_values.
            psi_df = pd.read_csv(
                psi_path,
                sep="\t",
                index_col=0,
                na_values=sorted(_MISSING_PSI_NA_VALUES),
                keep_default_na=False,
            )
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            raise ValueError(f"Could not read PSI file {psi_path}: {exc}") from exc

        if psi_df.shape[1] == 0:
            raise ValueError(f"PSI matrix contains no sample columns: {psi_path}")

        if psi_df.empty:
            raise ValueError(f"PSI matrix contains no events: {psi_path}")

        # pandas silently renames duplicate headers (S1, S1.1), which would count
        # one sample twice towards --min_psi_samples. Validate the raw header.
        raw_samples = _raw_sample_columns(psi_path, psi_df.shape[1])
        duplicates = sorted(name for name, count in Counter(raw_samples).items() if count > 1)
        if duplicates:
            raise ValueError(
                f"PSI matrix has duplicate sample columns {duplicates}: {psi_path}"
            )
        psi_df.columns = raw_samples

        psi_df = _validated_psi_values(psi_df, psi_path)

        n_samples = psi_df.shape[1]

        logging.info(
            "Read %d events across %d samples from %s",
            psi_df.shape[0],
            n_samples,
            psi_path,
        )

        provenances = {
            column: sample_provenance(column, psi_path, sample_metadata)
            for column in psi_df.columns
        }
        canonical = [provenances[column]["sample_id"] for column in psi_df.columns]
        repeated = sorted(name for name, count in Counter(canonical).items() if count > 1)
        if repeated:
            raise ValueError(
                f"PSI matrix columns map to the same sample {repeated} "
                f"(after sample-metadata resolution): {psi_path}"
            )

        # Iterate a float matrix rather than DataFrame.iterrows(), which builds a
        # Series per event and dominates load time for large PSI matrices.
        column_provenance = [provenances[column] for column in psi_df.columns]
        matrix = psi_df.to_numpy(dtype=float)
        for raw_event_id, row in zip(psi_df.index, matrix):
            event_id = normalise_event_id(raw_event_id)

            if event_id is None:
                continue

            event_values = pooled_values.setdefault(event_id, {})
            sample_universe.setdefault(event_id, set()).update(canonical)
            source_files.setdefault(event_id, []).append(str(psi_path))
            details = sample_details.setdefault(event_id, {})
            for provenance, value in zip(column_provenance, row):
                if value != value:  # NaN
                    continue
                sample_id = provenance["sample_id"]
                value = float(value)
                previous = event_values.get(sample_id)
                if previous is not None and abs(previous - value) > 1e-9:
                    raise ValueError(
                        f"Conflicting PSI values for event {event_id} and sample "
                        f"{sample_id}: {previous} vs {value} (in {psi_path})"
                    )
                event_values[sample_id] = value
                details[sample_id] = provenance

    psi_lookup = {}

    for event_id, by_sample in pooled_values.items():
        values = list(by_sample.values())
        psi_lookup[event_id] = {
            "values": values,
            "mean": (
                sum(values) / len(values)
                if values
                else None
            ),
            "max": max(values) if values else None,
            "n_observed": len(values),
            "n_total": len(sample_universe.get(event_id, ())),
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

    df.to_csv(out_path, sep="\t", index=False, lineterminator="\n")
    logging.info(
        "Wrote PSI filter summary to %s (%d events; %d passed)",
        out_path,
        len(df),
        int(df["passed_filter"].fillna(False).astype(bool).sum())
        if "passed_filter" in df.columns
        else 0,
    )
