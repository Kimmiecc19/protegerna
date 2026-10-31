"""Canonical typed models and policies for splice-proteoform reconstruction."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, cast, Generic, Iterable, Mapping, MutableMapping, Optional, Sequence, TypedDict, TypeVar

from .splice_translation import (
    extract_sequence_from_indexed_genome, intersect_interval_lists,
    interval_length, match_transcript_id,
)
from .proteogenomic_models import TranslationResult

class CDSSegmentModel(TypedDict):
    genomic_start: int
    genomic_end: int
    strand: str
    phase: Optional[int]
    phase_missing: bool


class TranscriptModel(TypedDict, total=False):
    transcript_id: str
    gene_id: str
    gene_name: Optional[str]
    chrom: str
    strand: str
    exons: list[tuple[int, int]]
    cds: list[tuple[int, int, Optional[int]]]
    cds_start_nf: bool
    cds_end_nf: bool
    transcript_type: Optional[str]
    tags: list[str]
    transcript_support_level: Optional[str]
    preserves_observed_event: bool
T = TypeVar("T")


@dataclass(frozen=True)
class TranscriptResolution:
    requested_id: str
    matched_id: Optional[str]
    confidence: float
    ambiguous: bool
    candidate_count: int
    reason: str


@dataclass(frozen=True)
class TranscriptRanking:
    transcript_id: Optional[str]
    score: float
    rank: int
    candidate_count: int
    ambiguous: bool
    tied_best_count: int
    cds_overlap_nt: int
    exon_overlap_nt: int
    cds_length_delta_nt: int
    reason: str
    top_candidates: tuple[str, ...] = ()
    selection_path: str = ""


@dataclass(frozen=True)
class AlternativeStartAssessment:
    codon: str
    offset_nt: int
    frame_conserved: bool
    kozak_strength: str
    kozak_score: float
    minus3_base: str
    plus4_base: str
    context_minus6_plus6: str


@dataclass(frozen=True)
class SpliceReconstructionConfig:
    """Immutable settings consumed by deep splice reconstruction helpers."""
    nmd_distance_threshold_nt: int = 55
    pad_partial_codons: bool = False
    alternative_start_codons: tuple[str, ...] = ("ATG",)
    min_alt_start_kozak_strength: str = "weak"
    max_missed_cleavages: int = 2
    min_database_peptide_length: int = 7
    max_database_peptide_length: int = 40
    require_ri_read_evidence: bool = True
    min_ri_inclusion_reads: int = 1
    exclude_ri_nmd_from_primary: bool = True
    require_ri_junction_peptide: bool = True


@dataclass
class SpliceFileResult:
    """Worker-local reconstruction outputs merged only by the parent thread."""
    proteins: dict[str, dict[str, Any]]
    alternative_start_proteins: dict[str, dict[str, Any]]
    exploratory_orf_proteins: dict[str, dict[str, Any]]
    junction_records: list[Any]
    consequence_rows: list[dict[str, Any]]
    summary_rows: list[dict[str, Any]]


class BoundedCache(Generic[T]):
    """Small deterministic LRU cache suitable for run-local sequence/lookups."""
    def __init__(self, max_entries: int = 100_000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self.max_entries = max_entries
        self._values: OrderedDict[str, T] = OrderedDict()

    def get(self, key: str) -> Optional[T]:
        value = self._values.get(key)
        if value is not None:
            self._values.move_to_end(key)
        return value

    def put(self, key: str, value: T) -> None:
        self._values[key] = value
        self._values.move_to_end(key)
        while len(self._values) > self.max_entries:
            self._values.popitem(last=False)

    def __len__(self) -> int:
        return len(self._values)


class TranscriptResolver:
    """Cache version-aware transcript resolution and expose confidence metadata."""
    def __init__(self, transcripts: Mapping[str, TranscriptModel]) -> None:
        self.transcripts = transcripts
        self._cache: dict[str, TranscriptResolution] = {}
        self._lock = RLock()

    def resolve(self, requested_id: str) -> TranscriptResolution:
        requested = str(requested_id)
        with self._lock:
            if requested in self._cache:
                return self._cache[requested]
        matched = match_transcript_id(requested, self.transcripts)
        if matched is None:
            result = TranscriptResolution(requested, None, 0.0, False, 0, "no_match")
        else:
            exact = requested == matched
            base = requested.split(".", 1)[0]
            candidates = [key for key in self.transcripts if key.split(".", 1)[0] == base]
            result = TranscriptResolution(
                requested, matched, 1.0 if exact else 0.9,
                len(candidates) > 1, max(len(candidates), 1),
                "exact_id" if exact else "stable_id_version_match",
            )
        with self._lock:
            self._cache[requested] = result
        return result


def merge_protein_mappings(target: MutableMapping[str, dict[str, Any]], source: Mapping[str, dict[str, Any]]) -> None:
    """Deterministically merge worker-local sequence-to-mapping collections."""
    for sequence, entry in source.items():
        destination = target.setdefault(sequence, {"mappings": []})
        existing = {
            tuple(sorted((str(key), str(value)) for key, value in mapping.items()))
            for mapping in destination.get("mappings", [])
        }
        for mapping in entry.get("mappings", []):
            identity = tuple(sorted((str(key), str(value)) for key, value in mapping.items()))
            if identity not in existing:
                destination["mappings"].append(dict(mapping))
                existing.add(identity)


class GenomeSequenceCache:
    """Thread-safe bounded cache for immutable genome interval extractions.

    A single pyfaidx ``Fasta`` is shared by event-file workers. pyfaidx supports
    concurrent read-only indexed access; callers must never mutate or rebuild
    the FASTA/index while reconstruction is running. The lock also prevents
    interleaved access through the shared handle.
    """
    def __init__(self, genome_index: Any, max_entries: int = 100_000) -> None:
        self.genome_index = genome_index
        self.cache: BoundedCache[Optional[str]] = BoundedCache(max_entries)
        self.lock = RLock()

    def extract(self, chrom: str, segments: Sequence[tuple[int, int]], strand: str) -> Optional[str]:
        key = f"{chrom}|{strand}|" + ";".join(f"{start}-{end}" for start, end in segments)
        with self.lock:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
            sequence = cast(Optional[str], extract_sequence_from_indexed_genome(
                self.genome_index, chrom, list(segments), strand
            ))
            self.cache.put(key, sequence)
            return sequence


class CanonicalProteinCache:
    """Thread-safe run-level cache for canonical transcript translations."""
    def __init__(self) -> None:
        self._values: dict[str, Optional[str]] = {}
        self._lock = RLock()

    def get_or_compute(self, transcript_id: str, loader: Callable[[], Optional[str]]) -> Optional[str]:
        with self._lock:
            if transcript_id not in self._values:
                self._values[transcript_id] = loader()
            return self._values[transcript_id]

    def __len__(self) -> int:
        with self._lock:
            return len(self._values)


def _interval_intersection_length(left: Iterable[Sequence[int]], right: Iterable[Sequence[int]]) -> int:
    return sum(
        end - start + 1
        for start, end in intersect_interval_lists(
            [(int(x[0]), int(x[1])) for x in left or []],
            [(int(x[0]), int(x[1])) for x in right or []],
        )
    )


def rank_compatible_transcripts(
    query: TranscriptModel,
    candidates: Iterable[TranscriptModel],
) -> tuple[Optional[TranscriptModel], TranscriptRanking]:
    """Choose a transcript using a biological, hierarchical decision path."""
    compatible = [
        model for model in candidates
        if model.get("gene_id") == query.get("gene_id")
        and model.get("chrom") == query.get("chrom")
        and model.get("strand") == query.get("strand")
    ]
    if not compatible:
        return None, TranscriptRanking(None, 0.0, 0, 0, False, 0, 0, 0, 0, "no_compatible_candidate")

    scored = []
    query_cds_len = interval_length(query.get("cds"))
    for model in compatible:
        cds_overlap = _interval_intersection_length(query.get("cds") or [], model.get("cds") or [])
        exon_overlap = _interval_intersection_length(query.get("exons") or [], model.get("exons") or [])
        length_delta = abs(query_cds_len - interval_length(model.get("cds")))
        biotype = str(model.get("transcript_type") or model.get("transcript_biotype") or "").lower()
        protein_coding = biotype == "protein_coding" or bool(model.get("cds"))
        complete_cds = protein_coding and not model.get("cds_start_nf", False) and not model.get("cds_end_nf", False)
        preserves_event = bool(model.get("preserves_observed_event", exon_overlap > 0))
        tags = {str(tag).lower() for tag in model.get("tags", [])}
        annotation_quality = 2 if tags & {"mane_select", "appris_principal_1"} else 1 if model.get("transcript_support_level") in {1, "1"} else 0
        hierarchy = (protein_coding, complete_cds, preserves_event, annotation_quality)
        score = float(sum((1000, 100, 10, 1)[i] * int(value) for i, value in enumerate(hierarchy)))
        scored.append((score, *hierarchy, cds_overlap, exon_overlap, length_delta, str(model.get("transcript_id") or ""), model))
    scored.sort(key=lambda row: (-row[1], -row[2], -row[3], -row[4], -row[5], -row[6], row[7], row[8]))
    best = scored[0]
    tied = sum(row[1:8] == best[1:8] for row in scored)
    ranking = TranscriptRanking(
        transcript_id=best[8], score=best[0], rank=1,
        candidate_count=len(scored), ambiguous=tied > 1, tied_best_count=tied,
        cds_overlap_nt=best[5], exon_overlap_nt=best[6], cds_length_delta_nt=best[7],
        reason="hierarchical_biological_selection" if tied == 1 else "ambiguous_after_hierarchical_selection",
        top_candidates=tuple(row[8] for row in scored[:3]),
        selection_path="compatible>protein_coding>complete_cds>preserves_event>annotation_quality",
    )
    return best[9], ranking


def assess_alternative_start(sequence: str, offset_nt: int) -> AlternativeStartAssessment:
    """Score the -6..+6 Kozak context, retaining the decisive -3/+4 bases.

    The weights are an interpretable heuristic, not a calibrated probability:
    -3 purine and +4 G dominate, with smaller contributions from the extended
    vertebrate consensus GCC(A/G)CCATGG.
    """
    seq = str(sequence or "").upper().replace("U", "T")
    codon = seq[offset_nt:offset_nt + 3]
    minus3 = seq[offset_nt - 3] if offset_nt >= 3 else "N"
    plus4 = seq[offset_nt + 3] if offset_nt + 3 < len(seq) else "N"
    minus3_match = minus3 in {"A", "G"}
    plus4_match = plus4 == "G"
    context = "".join(seq[index] if 0 <= index < len(seq) else "N"
                      for index in range(offset_nt - 6, offset_nt + 7))
    extended_weights = {
        0: ({"G"}, 0.25), 1: ({"C"}, 0.25), 2: ({"C"}, 0.25),
        3: ({"A", "G"}, 1.5), 4: ({"C"}, 0.25), 5: ({"C"}, 0.25),
        9: ({"G"}, 1.5),
    }
    score = sum(weight for position, (allowed, weight) in extended_weights.items()
                if context[position] in allowed)
    strength = "strong" if minus3_match and plus4_match else (
        "moderate" if minus3_match or plus4_match else "weak"
    )
    return AlternativeStartAssessment(
        codon=codon, offset_nt=offset_nt, frame_conserved=(offset_nt % 3 == 0),
        kozak_strength=strength, kozak_score=score,
        minus3_base=minus3, plus4_base=plus4,
        context_minus6_plus6=context,
    )


def validate_intervals(intervals: Sequence[tuple[int, int]]) -> None:
    """Reject inverted or overlapping closed genomic intervals."""
    ordered = sorted((int(start), int(end)) for start, end in intervals)
    for index, (start, end) in enumerate(ordered):
        if start < 1 or end < start:
            raise ValueError(f"invalid genomic interval: {start}-{end}")
        if index and start <= ordered[index - 1][1]:
            raise ValueError("genomic intervals overlap")


def transcript_to_genome(
    intervals: Sequence[tuple[int, int]], strand: str, offset_nt: int
) -> int:
    """Map a zero-based transcript offset to a one-based genomic coordinate."""
    validate_intervals(intervals)
    if strand not in {"+", "-"} or offset_nt < 0:
        raise ValueError("strand must be + or - and offset_nt must be non-negative")
    remaining = int(offset_nt)
    ordered = sorted(intervals, reverse=(strand == "-"))
    for start, end in ordered:
        length = end - start + 1
        if remaining < length:
            return start + remaining if strand == "+" else end - remaining
        remaining -= length
    raise IndexError("transcript offset lies outside the exon chain")


def genome_to_transcript(
    intervals: Sequence[tuple[int, int]], strand: str, coordinate: int
) -> int:
    """Map a one-based exonic genomic coordinate to a zero-based transcript offset."""
    validate_intervals(intervals)
    if strand not in {"+", "-"}:
        raise ValueError("strand must be + or -")
    offset = 0
    for start, end in sorted(intervals, reverse=(strand == "-")):
        if start <= coordinate <= end:
            return offset + (coordinate - start if strand == "+" else end - coordinate)
        offset += end - start + 1
    raise IndexError("coordinate is not exonic")


def junction_amino_acid_boundary(junction_nt: int, translation_start_nt: int = 0) -> int:
    """Return the zero-based AA boundary at/before a transcript junction."""
    relative = int(junction_nt) - int(translation_start_nt)
    if relative < 0:
        raise ValueError("junction precedes translation start")
    return relative // 3
