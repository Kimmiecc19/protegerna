"""QC domain records and header normalization."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import Dict, Tuple
from .pgdb_header import PGDBHeader, sequence_hashes


VALID_AA = set("ACDEFGHIKLMNPQRSTVWYBXZUOJ*")

STOP = "*"

@dataclass
class FastaRecord:
    source_label: str
    source_file: str
    header: str
    sequence: str
    ordinal: int
    identifier: str = field(init=False)
    metadata: Dict[str, str] = field(init=False, repr=False)
    _sequence_hash: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.identifier, self.metadata = parse_pgdb_header(self.header)
        self._sequence_hash = sequence_hashes(self.sequence)[1]

    @property
    def sequence_hash(self) -> str:
        return self._sequence_hash

def parse_pgdb_header(header: str) -> Tuple[str, Dict[str, str]]:
    """Parse a pipe-delimited PGDB FASTA header into identifier and key=value fields.

    Headers that do not use the PGDB key=value convention remain valid; their
    full first token is returned as the identifier and the metadata dictionary
    is empty or partially populated.
    """
    parsed = PGDBHeader.parse(header)
    metadata = dict(parsed.metadata)
    # Preserve the established QC output columns while the canonical parser
    # uses lowercase keys internally.
    if "gn" in metadata:
        metadata["GN"] = metadata["gn"]
    if "os" in metadata:
        metadata["OS"] = metadata["os"]
    return parsed.record_id, metadata

@dataclass
class MetadataCounts:
    frame_statuses: Counter = field(default_factory=Counter)
    premature_stops: Counter = field(default_factory=Counter)
    nmd_predictions: Counter = field(default_factory=Counter)
    start_losses: Counter = field(default_factory=Counter)
    retained_intron_orfs: Counter = field(default_factory=Counter)
    utr_or_noncoding: Counter = field(default_factory=Counter)
    frame_mismatches: Counter = field(default_factory=Counter)
    ri_boundary_fallbacks: Counter = field(default_factory=Counter)
    fusion_gene_id_collisions: Counter = field(default_factory=Counter)
    contributing_caller_counts: Counter = field(default_factory=Counter)
