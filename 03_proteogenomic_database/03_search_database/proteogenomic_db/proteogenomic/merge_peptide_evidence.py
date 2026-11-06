"""Post-merge peptide uniqueness and fragment evidence."""
from __future__ import annotations
from typing import Dict, List, Set
from collections import Counter
from .merge_models import ProteinFilterConfig, SequenceAggregate, clean_value
from .splice_translation import digest_tryptic_records


def il_equivalent(peptide: str) -> str:
    """Normalize leucine/isoleucine, which are isobaric in standard MS/MS."""
    return str(peptide).upper().replace("I", "J").replace("L", "J")

def _fragment_labels(peptide: str) -> Set[str]:
    """Return sequence-defined b/y fragment labels (charge-neutral proxy)."""
    return {
        *(f"b:{peptide[:index]}" for index in range(1, len(peptide))),
        *(f"y:{peptide[index:]}" for index in range(1, len(peptide))),
    }

def final_database_peptide_rows(
    aggregates: Sequence[SequenceAggregate], id_map: Dict[str, str], config: ProteinFilterConfig
) -> List[Dict[str, object]]:
    """Reassess peptide evidence only after the complete target DB is known."""
    exact_owners: Dict[str, Set[str]] = {}
    il_owners: Dict[str, Set[str]] = {}
    pg_exact_owners: Dict[str, Set[str]] = {}
    pg_il_owners: Dict[str, Set[str]] = {}
    records_by_hash: Dict[str, List[Dict[str, object]]] = {}
    pg_hashes = {
        aggregate.sequence_sha256 for aggregate in aggregates
        if any(source not in {"reference", "crap", "contaminant"} for source in aggregate.sources)
    }
    for aggregate in aggregates:
        peptide_records = digest_tryptic_records(
            aggregate.sequence, config.max_missed_cleavages,
            config.min_peptide_length, config.max_peptide_length,
        )
        records_by_hash[aggregate.sequence_sha256] = peptide_records
        for record in peptide_records:
            peptide = str(record["peptide_sequence"])
            exact_owners.setdefault(peptide, set()).add(aggregate.sequence_sha256)
            il_owners.setdefault(il_equivalent(peptide), set()).add(aggregate.sequence_sha256)
            if aggregate.sequence_sha256 in pg_hashes:
                pg_exact_owners.setdefault(peptide, set()).add(aggregate.sequence_sha256)
                pg_il_owners.setdefault(il_equivalent(peptide), set()).add(aggregate.sequence_sha256)

    all_peptides = set(exact_owners)
    fragment_competitors = {peptide: _fragment_labels(peptide) for peptide in all_peptides}
    fragment_owner_counts = Counter(
        fragment for fragments in fragment_competitors.values() for fragment in fragments
    )
    rows: List[Dict[str, object]] = []
    for aggregate in aggregates:
        sequence_id = id_map[aggregate.sequence_sha256]
        junctions = set()
        for record in aggregate.records:
            raw = record.metadata.get("junction_aa") or record.metadata.get("fusion_junction_aa")
            try:
                if raw and clean_value(raw).lower() != "na":
                    junctions.add(int(float(raw)))
            except (TypeError, ValueError):
                pass
        for record in records_by_hash[aggregate.sequence_sha256]:
            peptide = str(record["peptide_sequence"])
            own_fragments = fragment_competitors[peptide]
            start = int(record["peptide_start_aa"])
            end = int(record["peptide_end_aa"])
            rows.append({
                "sequence_id": sequence_id,
                **record,
                "il_equivalent_sequence": il_equivalent(peptide),
                "unique_complete_target_exact": len(exact_owners[peptide]) == 1,
                "unique_complete_target_il_equivalent": len(il_owners[il_equivalent(peptide)]) == 1,
                "unique_proteogenomic_exact": len(pg_exact_owners.get(peptide, set())) == 1,
                "unique_proteogenomic_il_equivalent": len(pg_il_owners.get(il_equivalent(peptide), set())) == 1,
                "crosses_defining_junction": any(start - 1 < junction < end for junction in junctions) if junctions else "unknown",
                "distinguishing_fragment_ion_count": sum(
                    fragment_owner_counts[fragment] == 1 for fragment in own_fragments
                ),
                "fragment_ion_model": "theoretical_unmodified_b_y_sequence_proxy",
            })
    return rows
