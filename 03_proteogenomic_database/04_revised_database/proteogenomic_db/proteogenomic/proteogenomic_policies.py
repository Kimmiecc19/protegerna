"""Immutable policies constructed once at CLI boundaries."""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DigestionPolicy:
    max_missed_cleavages: int = 2
    min_peptide_length: int = 7
    max_peptide_length: int = 40

    @classmethod
    def from_namespace(cls, args: Any) -> "DigestionPolicy":
        return cls(
            int(getattr(args, "max_missed_cleavages", 2)),
            int(getattr(args, "min_database_peptide_length", getattr(args, "min_peptide_length", 7))),
            int(getattr(args, "max_database_peptide_length", getattr(args, "max_peptide_length", 40))),
        )


@dataclass(frozen=True)
class DiaFilterPolicy:
    exclude_incomplete_cds: bool = True
    exclude_frameshift: bool = False
    exclude_nmd: bool = False
    exclude_start_loss: bool = False
    require_unique_peptide: bool = False

    @classmethod
    def from_namespace(cls, args: Any) -> "DiaFilterPolicy":
        return cls(
            bool(getattr(args, "exclude_incomplete_cds", True)),
            bool(getattr(args, "exclude_frameshift_from_dia", False)),
            bool(getattr(args, "exclude_nmd_from_dia", False)),
            bool(getattr(args, "exclude_start_loss_from_dia", False)),
            bool(getattr(args, "require_unique_event_peptide", False)),
        )


@dataclass(frozen=True)
class ReconstructionPolicy:
    nmd_distance_threshold_nt: int = 55
    pad_partial_codons: bool = False
    digestion: DigestionPolicy = DigestionPolicy()
    dia: DiaFilterPolicy = DiaFilterPolicy()

    @classmethod
    def from_namespace(cls, args: Any) -> "ReconstructionPolicy":
        return cls(
            int(getattr(args, "nmd_distance_threshold_nt", 55)),
            bool(getattr(args, "pad_partial_codons", False)),
            DigestionPolicy.from_namespace(args),
            DiaFilterPolicy.from_namespace(args),
        )

