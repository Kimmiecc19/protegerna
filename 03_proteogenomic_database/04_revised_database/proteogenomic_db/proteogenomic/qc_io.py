"""Deterministic QC FASTA/TSV input and table output."""
from __future__ import annotations
import csv
import re
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence
from .qc_models import FastaRecord


def parse_fasta(path: Path, label: str) -> Iterator[FastaRecord]:
    """Parse FASTA without external dependencies."""
    header: Optional[str] = None
    seq_parts: List[str] = []
    ordinal = 0

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n\r")
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    ordinal += 1
                    yield FastaRecord(
                        label,
                        path.as_posix(),
                        header,
                        "".join(seq_parts).upper(),
                        ordinal,
                    )
                header = line[1:].strip()
                seq_parts = []
            else:
                seq_parts.append(re.sub(r"\s+", "", line))

        if header is not None:
            ordinal += 1
            yield FastaRecord(label, path.as_posix(), header, "".join(seq_parts).upper(), ordinal)

def parse_all_fastas(fasta_paths: Sequence[Path], labels: Optional[Sequence[str]]) -> List[FastaRecord]:
    if labels and len(labels) != len(fasta_paths):
        raise ValueError("--labels must have the same number of values as --fasta")

    records: List[FastaRecord] = []
    for i, path in enumerate(fasta_paths):
        label = labels[i] if labels else path.stem
        if not path.exists():
            raise FileNotFoundError(f"FASTA not found: {path}")
        records.extend(parse_fasta(path, label))
    return records

def write_tsv(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Optional[Sequence[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        fieldnames = keys

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def read_tsv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for row in reader]
