"""Post-merge peptide uniqueness and fragment evidence.

Memory design (outputs are identical to the original set-based implementation):

* Ownership: each peptide maps to the index of its single owning protein, or to
  ``SHARED`` once a second distinct protein contains it. "Unique" only ever asks
  whether exactly one protein owns a peptide, so the owner sets are not kept.
* Fragments: a b-ion label is a proper prefix of the peptide and a y-ion label
  a proper suffix. Rather than materialising every prefix/suffix string
  (O(L^2) characters per peptide), the number of a peptide's prefixes shared
  with any other peptide is derived from its longest common prefix with its
  neighbours in sorted order (suffixes: the same on reversed sequences).
* Rows: proteins are re-digested in a second pass and rows are yielded one at a
  time, so digested records and output rows are never all held at once.
"""
from __future__ import annotations
from typing import Dict, Iterable, Iterator, List, Mapping, Sequence, Set
from .merge_models import ProteinFilterConfig, SequenceAggregate, clean_value
from .splice_translation import digest_tryptic_records

SHARED = -1
NON_TARGET_SOURCES = frozenset({"reference", "crap", "contaminant"})


def il_equivalent(peptide: str) -> str:
    """Normalize leucine/isoleucine, which are isobaric in standard MS/MS."""
    return str(peptide).upper().replace("I", "J").replace("L", "J")


def _fragment_labels(peptide: str) -> Set[str]:
    """Return sequence-defined b/y fragment labels (charge-neutral proxy).

    Kept as the reference definition; the merge uses ``distinguishing_fragment_counts``.
    """
    return {
        *(f"b:{peptide[:index]}" for index in range(1, len(peptide))),
        *(f"y:{peptide[index:]}" for index in range(1, len(peptide))),
    }


def _common_prefix_length(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    return index


def _unique_prefix_counts(peptides: Sequence[str]) -> Dict[str, int]:
    """For each distinct peptide, count its proper prefixes owned by no other peptide.

    In sorted order, peptides sharing a prefix ``p`` (length k) are contiguous.
    Another peptide carries ``p`` as a *proper* prefix only if it is longer than
    k, so the shared prefix lengths of P are 1..max(lcp(next), min(lcp(prev),
    len(prev) - 1)). A preceding neighbour equal to ``p`` itself does not carry
    ``p`` as a fragment; a following neighbour is never a prefix of P.
    """
    ordered = sorted(set(peptides))
    counts: Dict[str, int] = {}
    for position, peptide in enumerate(ordered):
        shared = 0
        if position > 0:
            previous = ordered[position - 1]
            shared = min(_common_prefix_length(previous, peptide), len(previous) - 1)
        if position + 1 < len(ordered):
            shared = max(shared, _common_prefix_length(peptide, ordered[position + 1]))
        fragments = max(len(peptide) - 1, 0)
        counts[peptide] = fragments - min(shared, fragments)
    return counts


def distinguishing_fragment_counts(peptides: Iterable[str]) -> Dict[str, int]:
    """Number of each peptide's b/y fragment labels that no other peptide shares."""
    distinct = set(peptides)
    prefixes = _unique_prefix_counts(list(distinct))
    reversed_counts = _unique_prefix_counts([peptide[::-1] for peptide in distinct])
    return {peptide: prefixes[peptide] + reversed_counts[peptide[::-1]] for peptide in distinct}


def _claim(owners: Dict[str, int], key: str, owner: int) -> None:
    current = owners.get(key)
    if current is None:
        owners[key] = owner
    elif current != owner:
        owners[key] = SHARED


def _is_unique(owners: Mapping[str, int], key: str) -> bool:
    value = owners.get(key)
    return value is not None and value != SHARED


def _digest(aggregate: SequenceAggregate, config: ProteinFilterConfig):
    return digest_tryptic_records(
        aggregate.sequence, config.max_missed_cleavages,
        config.min_peptide_length, config.max_peptide_length,
    )


def _defining_junctions(aggregate: SequenceAggregate) -> Set[int]:
    junctions = set()
    for record in aggregate.records:
        raw = record.metadata.get("junction_aa") or record.metadata.get("fusion_junction_aa")
        try:
            if raw and clean_value(raw).lower() != "na":
                junctions.add(int(float(raw)))
        except (TypeError, ValueError):
            pass
    return junctions


def iter_final_database_peptide_rows(
    aggregates: Sequence[SequenceAggregate], id_map: Dict[str, str], config: ProteinFilterConfig
) -> Iterator[Dict[str, object]]:
    """Reassess peptide evidence only after the complete target DB is known (streamed)."""
    exact_owners: Dict[str, int] = {}
    il_owners: Dict[str, int] = {}
    pg_exact_owners: Dict[str, int] = {}
    pg_il_owners: Dict[str, int] = {}
    for owner, aggregate in enumerate(aggregates):
        proteogenomic = any(source not in NON_TARGET_SOURCES for source in aggregate.sources)
        for record in _digest(aggregate, config):
            peptide = str(record["peptide_sequence"])
            il_key = il_equivalent(peptide)
            _claim(exact_owners, peptide, owner)
            _claim(il_owners, il_key, owner)
            if proteogenomic:
                _claim(pg_exact_owners, peptide, owner)
                _claim(pg_il_owners, il_key, owner)

    fragment_counts = distinguishing_fragment_counts(exact_owners)

    for aggregate in aggregates:
        sequence_id = id_map[aggregate.sequence_sha256]
        junctions = _defining_junctions(aggregate)
        for record in _digest(aggregate, config):
            peptide = str(record["peptide_sequence"])
            il_key = il_equivalent(peptide)
            start = int(record["peptide_start_aa"])
            end = int(record["peptide_end_aa"])
            yield {
                "sequence_id": sequence_id,
                **record,
                "il_equivalent_sequence": il_key,
                "unique_complete_target_exact": _is_unique(exact_owners, peptide),
                "unique_complete_target_il_equivalent": _is_unique(il_owners, il_key),
                "unique_proteogenomic_exact": _is_unique(pg_exact_owners, peptide),
                "unique_proteogenomic_il_equivalent": _is_unique(pg_il_owners, il_key),
                "crosses_defining_junction": any(start - 1 < junction < end for junction in junctions) if junctions else "unknown",
                "distinguishing_fragment_ion_count": fragment_counts[peptide],
                "fragment_ion_model": "theoretical_unmodified_b_y_sequence_proxy",
            }


def final_database_peptide_rows(
    aggregates: Sequence[SequenceAggregate], id_map: Dict[str, str], config: ProteinFilterConfig
) -> List[Dict[str, object]]:
    """List form of ``iter_final_database_peptide_rows`` (kept for existing callers)."""
    return list(iter_final_database_peptide_rows(aggregates, id_map, config))
