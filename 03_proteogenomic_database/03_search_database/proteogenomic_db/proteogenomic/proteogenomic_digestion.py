"""Sole tryptic-digestion implementation for every pipeline."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .proteogenomic_policies import DigestionPolicy


@dataclass(frozen=True)
class TrypticPeptide:
    peptide_sequence: str
    peptide_length: int
    peptide_start_aa: int
    peptide_end_aa: int
    missed_cleavages: int


def digest_records(sequence: str, policy: DigestionPolicy = DigestionPolicy()) -> list[TrypticPeptide]:
    normalized = re.sub(r"[^A-Za-z*]", "", str(sequence or "").upper())
    output: list[TrypticPeptide] = []
    aa_offset = 0
    for segment in (part for part in normalized.split("*") if part):
        cuts = [0]
        cuts.extend(
            index + 1 for index, aa in enumerate(segment)
            if aa in {"K", "R"} and (index + 1 == len(segment) or segment[index + 1] != "P")
        )
        if cuts[-1] != len(segment):
            cuts.append(len(segment))
        for start_index in range(len(cuts) - 1):
            max_end = min(len(cuts) - 1, start_index + policy.max_missed_cleavages + 1)
            for end_index in range(start_index + 1, max_end + 1):
                start, end = cuts[start_index], cuts[end_index]
                peptide = segment[start:end]
                if not (policy.min_peptide_length <= len(peptide) <= policy.max_peptide_length):
                    continue
                if "X" in peptide:
                    continue
                missed = sum(
                    aa in {"K", "R"} and peptide[index + 1] != "P"
                    for index, aa in enumerate(peptide[:-1])
                )
                output.append(TrypticPeptide(
                    peptide, len(peptide), aa_offset + start + 1,
                    aa_offset + end, missed,
                ))
        aa_offset += len(segment)
    return output


def digest_record_dicts(sequence: str, policy: DigestionPolicy = DigestionPolicy()) -> list[dict]:
    return [asdict(record) for record in digest_records(sequence, policy)]


def digest_sequences(sequence: str, policy: DigestionPolicy = DigestionPolicy()) -> set[str]:
    return {record.peptide_sequence for record in digest_records(sequence, policy)}

