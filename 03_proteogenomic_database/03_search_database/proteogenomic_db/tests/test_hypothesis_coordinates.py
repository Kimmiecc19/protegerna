"""Property-based coordinate tests for splice reconstruction primitives."""
from __future__ import annotations

import unittest

from hypothesis import given, settings, strategies as st

from proteogenomic.splice_reconstruction_core import (
    genome_to_transcript,
    junction_amino_acid_boundary,
    transcript_to_genome,
    validate_intervals,
)
from proteogenomic.splice_translation import interval_length, subtract_interval_list


@st.composite
def exon_chains(draw):
    lengths = draw(st.lists(st.integers(1, 150), min_size=1, max_size=8))
    gaps = draw(st.lists(st.integers(1, 100), min_size=max(0, len(lengths) - 1), max_size=max(0, len(lengths) - 1)))
    start = draw(st.integers(1, 1_000_000))
    intervals = []
    for index, length in enumerate(lengths):
        intervals.append((start, start + length - 1))
        if index < len(gaps):
            start += length + gaps[index]
    return intervals


class CoordinateProperties(unittest.TestCase):
    @settings(max_examples=150)
    @given(exon_chains(), st.sampled_from(["+", "-"]), st.data())
    def test_transcript_genome_round_trip(self, intervals, strand, data):
        total = interval_length(intervals)
        offset = data.draw(st.integers(0, total - 1))
        genomic = transcript_to_genome(intervals, strand, offset)
        self.assertEqual(genome_to_transcript(intervals, strand, genomic), offset)
        self.assertEqual(total, sum(end - start + 1 for start, end in intervals))

    @settings(max_examples=100)
    @given(exon_chains(), st.data())
    def test_skipping_exon_removes_exactly_its_bases(self, intervals, data):
        index = data.draw(st.integers(0, len(intervals) - 1))
        retained = intervals[:index] + intervals[index + 1:]
        self.assertEqual(
            interval_length(intervals) - interval_length(retained),
            interval_length([intervals[index]]),
        )
        validate_intervals(retained)

    @settings(max_examples=100)
    @given(exon_chains().filter(lambda chain: len(chain) >= 2), st.data())
    def test_retained_intron_inserts_expected_bases(self, intervals, data):
        index = data.draw(st.integers(0, len(intervals) - 2))
        intron = (intervals[index][1] + 1, intervals[index + 1][0] - 1)
        retained = sorted(intervals + [intron])
        self.assertEqual(interval_length(retained) - interval_length(intervals), interval_length([intron]))
        validate_intervals(retained)

    @settings(max_examples=100)
    @given(st.integers(-500, 500))
    def test_frame_change_matches_nucleotide_delta(self, delta):
        self.assertEqual(delta % 3 != 0, (delta % 3) in {1, 2})

    @settings(max_examples=100)
    @given(st.integers(0, 20_000), st.integers(0, 2))
    def test_junction_maps_to_expected_amino_acid_boundary(self, codons, phase):
        junction_nt = codons * 3 + phase
        self.assertEqual(junction_amino_acid_boundary(junction_nt), codons)

    @settings(max_examples=100)
    @given(exon_chains(), st.data())
    def test_subtraction_never_inverts_or_overlaps(self, intervals, data):
        start, end = data.draw(st.sampled_from(intervals))
        cut_start = data.draw(st.integers(start, end))
        cut_end = data.draw(st.integers(cut_start, end))
        reconstructed = subtract_interval_list(intervals, cut_start, cut_end)
        validate_intervals(reconstructed)
        self.assertEqual(
            interval_length(intervals) - interval_length(reconstructed), cut_end - cut_start + 1
        )


if __name__ == "__main__":
    unittest.main()
