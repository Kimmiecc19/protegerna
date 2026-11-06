"""Small synthetic regression suite for coordinate, translation, and event logic."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import rmatstoprotein as rmats
import suppatoprotein as suppa
from proteogenomic.splice_translation import (
    CONSEQUENCE_TSV_COLUMNS,
    _translate_until_first_stop,
    cds_completeness,
    extract_sequence_from_indexed_genome,
    nmd_prediction,
    open_genome_index,
    cds_frame_at_genomic_position,
    should_include_protein_in_fasta,
    write_consequence_tsv,
)


class SharedTranslationTests(unittest.TestCase):
    def test_three_exon_sequence_on_both_strands(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "genome.fa"
            fasta.write_text(">chr1\nATGAAACCCGGGTTTAAACCCGGGTTT\n", encoding="ascii")
            index = open_genome_index(str(fasta))
            try:
                segments = [(1, 3), (7, 9), (13, 15)]
                self.assertEqual(extract_sequence_from_indexed_genome(index, "chr1", segments, "+"), "ATGCCCTTT")
                self.assertEqual(extract_sequence_from_indexed_genome(index, "chr1", segments, "-"), "AAAGGGCAT")
            finally:
                index.close()

    def test_translation_stops_at_first_stop(self):
        self.assertEqual(_translate_until_first_stop("ATGAAATAAGGG"), "MK")

    def test_nmd_55_nt_rule(self):
        self.assertEqual(nmd_prediction(10, [70])[0], True)
        self.assertEqual(nmd_prediction(10, [60])[0], False)
        # Stop starts at 10 and ends at 12: junction 67 is exactly 55 nt away.
        self.assertEqual(nmd_prediction(10, [67]), (True, 'ptc_far_upstream_of_downstream_junction', 67, 55))
        self.assertEqual(nmd_prediction(10, [66])[0], False)

    def test_cds_completeness_labels(self):
        self.assertEqual(cds_completeness(False, False), "complete")
        self.assertEqual(cds_completeness(True, False), "partial_start")
        self.assertEqual(cds_completeness(False, True), "partial_end")
        self.assertEqual(cds_completeness(True, True), "partial_start_and_end")

    def test_missing_cds_completeness_is_unknown_but_not_explicitly_incomplete(self):
        args = SimpleNamespace(exclude_incomplete_cds=True)
        self.assertEqual(should_include_protein_in_fasta({"frameshift": False}, args), (True, ""))
        self.assertEqual(
            should_include_protein_in_fasta({"cds_completeness": "partial_start"}, args),
            (False, "incomplete_cds_excluded_from_dia"),
        )

    def test_shared_frame_mapping_accounts_for_gtf_phase_on_both_strands(self):
        cds = [(1, 3, 1), (10, 15, 0)]
        self.assertEqual(cds_frame_at_genomic_position(cds, 10, "+"), 2)
        minus_cds = [(1, 6, 0), (10, 15, 1)]
        self.assertEqual(cds_frame_at_genomic_position(minus_cds, 15, "-"), 2)

    def test_overlapping_cds_boundaries_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlapping CDS segments"):
            cds_frame_at_genomic_position([(1, 6, 0), (6, 9, 0)], 6, "+")

    def test_consequence_schema_is_fixed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out.tsv"
            write_consequence_tsv([{"event_id": "E1"}], output, CONSEQUENCE_TSV_COLUMNS)
            self.assertEqual(list(pd.read_csv(output, sep="\t").columns)[:len(CONSEQUENCE_TSV_COLUMNS)], CONSEQUENCE_TSV_COLUMNS)


class RmatsEventTests(unittest.TestCase):
    exons = [(1, 9), (21, 29), (41, 49), (61, 69)]

    def test_coordinate_lookup_converts_every_declared_zero_based_start(self):
        for column, base in rmats.RMATS_COORDINATE_BASE.items():
            observed = rmats._row_int_auto({column: 20}, [column])
            self.assertEqual(observed, 21 if base == 0 else 20, column)

    def test_unknown_coordinate_column_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, "Unknown rMATS coordinate column"):
            rmats._rmats_start_1based({"novelStart": 20}, ["novelStart"])

    def test_se(self):
        chains = rmats.build_variant_chains_for_transcript("SE", {"exonStart_0base": 20, "exonEnd": 29}, self.exons)
        self.assertNotIn((21, 29), chains["skipped"])

    def test_a3ss(self):
        chains = rmats.build_variant_chains_for_transcript("A3SS", {"longExonStart_0base": 20, "longExonEnd": 35, "shortES": 20, "shortEE": 29}, self.exons)
        self.assertEqual(set(chains), {"long", "short"})

    def test_a5ss(self):
        chains = rmats.build_variant_chains_for_transcript("A5SS", {"longExonStart_0base": 20, "longExonEnd": 35, "shortES": 20, "shortEE": 29}, self.exons)
        self.assertEqual(set(chains), {"long", "short"})

    def test_mxe(self):
        one_mxe_isoform = [(1, 9), (21, 29), (61, 69)]
        chains = rmats.build_variant_chains_for_transcript("MXE", {"1stExonStart_0base": 20, "1stExonEnd": 29, "2ndExonStart_0base": 40, "2ndExonEnd": 49}, one_mxe_isoform)
        self.assertEqual(set(chains), {"exon1", "exon2"})

    def test_mxe_transcript_containing_both_alternatives_is_rejected(self):
        row = {"1stExonStart_0base": 20, "1stExonEnd": 29,
               "2ndExonStart_0base": 40, "2ndExonEnd": 49}
        self.assertEqual(rmats.build_variant_chains_for_transcript("MXE", row, self.exons), {})

    def test_ri(self):
        chains = rmats.build_variant_chains_for_transcript("RI", {"riExonStart_0base": 20, "riExonEnd": 49, "upstreamEE": 9, "downstreamES": 60}, self.exons)
        self.assertEqual(set(chains), {"retained", "spliced"})

    def test_ri_single_base_fallback_is_nonempty_and_normalized(self):
        chains = rmats.build_variant_chains_for_transcript(
            "RI", {"riExonStart_0base": 20, "riExonEnd": 21}, [(1, 9), (31, 39)]
        )
        self.assertIn((21, 21), chains["retained"])

    def test_minus_strand_upstream_offsets_are_deterministic_at_boundaries(self):
        cds = [(1, 3, 0), (10, 12, 0)]
        self.assertEqual(rmats.compute_upstream_cds_nt(cds, 12, "-"), 0)
        self.assertEqual(rmats.compute_upstream_cds_nt(cds, 10, "-"), 2)
        self.assertEqual(rmats.compute_upstream_cds_nt(cds, 3, "-"), 3)

    def test_intronic_insertion_boundaries_map_to_upstream_cds_length(self):
        cds = [(1, 3, 0), (10, 12, 0)]
        self.assertEqual(rmats.compute_upstream_cds_nt(cds, 5, "+"), 3)
        self.assertEqual(rmats.compute_upstream_cds_nt(cds, 5, "-"), 3)

    def test_versionless_transcript_alias_is_not_ranked_as_second_isoform(self):
        model = {
            "transcript_id": "ENST000001.2", "gene_id": "ENSG000001.1",
            "gene_name": "GENE1", "chrom": "chr1", "strand": "+",
            "exons": [(1, 12)], "cds": [(1, 12, 0)],
        }
        alias = dict(model, transcript_id="ENST000001")
        lookup = rmats.build_transcripts_lookup({
            "ENST000001.2": model,
            "ENST000001": alias,
        })
        self.assertEqual(lookup["ENSG000001.1"], ["ENST000001.2"])

    def test_suppa_junction_window_extends_left_near_cds_end(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "junction.fa"
            fasta.write_text(">chr1\n" + "ATG" * 20 + "\n", encoding="ascii")
            index = open_genome_index(str(fasta))
            try:
                records = suppa.generate_codon_aware_junction_peptides(
                    [(1, 27, 0), (31, 33, 0)],
                    {"strand": "+", "chrom": "chr1", "gene_id": "G",
                     "transcript_id": "T", "gene_name": "G"},
                    "P", "variant", "SE", index, max_flank=2, min_flank=2,
                )
                self.assertEqual(len(records), 1)
                self.assertGreaterEqual(len(records[0].seq), 4)
            finally:
                index.close()



if __name__ == "__main__":
    unittest.main()
