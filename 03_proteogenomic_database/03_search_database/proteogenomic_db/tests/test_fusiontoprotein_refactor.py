"""Focused regression tests for the current fusiontoprotein production module."""

from __future__ import annotations

import argparse
import unittest
from types import SimpleNamespace

import pandas as pd

import fusiontoprotein as fusion


class ParsingRegressionTests(unittest.TestCase):
    def test_parser_does_not_mutate_input_dataframe(self) -> None:
        source = pd.DataFrame(
            {
                "LeftBreakpoint": ["chr1:10"],
                "RightBreakpoint": ["2:20"],
                "LeftGene": ["TP53^ENSG00000141510.18"],
                "RightGene": ["ALK^ENSG00000171094.15"],
                "JunctionReadCount": [5],
                "SpanningFragCount": [3],
            }
        )
        before = source.copy(deep=True)

        parsed = fusion.parse_fusioninspector(source)

        pd.testing.assert_frame_equal(source, before)
        self.assertEqual(list(parsed.columns), fusion.PARSED_FUSION_COLUMNS)
        self.assertEqual(parsed.loc[0, "gene_1_symbol"], "TP53")
        self.assertEqual(parsed.loc[0, "gene_1_id"], "ENSG00000141510.18")
        self.assertEqual(parsed.loc[0, "chrom1"], "chr1")
        self.assertEqual(parsed.loc[0, "breakpoint2"], 20)

    def test_normalizers_preserve_existing_placeholder_rules(self) -> None:
        for value in (None, "", ".", "NA", "N/A", "None", "nan"):
            self.assertIsNone(fusion.normalize_text_or_none(value))
        self.assertEqual(fusion.normalize_gene_id("x|ENSG000001.12|y"), "ENSG000001")
        self.assertEqual(fusion.normalize_transcript_id("ENST00001.4"), "ENST00001")


class CalculationRegressionTests(unittest.TestCase):
    def test_missing_cds_phase_is_preserved_not_coerced_to_zero(self) -> None:
        feature = SimpleNamespace(
            start=10, end=18, strand="+", phase=".", frame=".", score=".",
        )
        db = SimpleNamespace(children=lambda *args, **kwargs: [feature])
        interval = fusion.get_feature_intervals(db, "T1", "CDS")[0]
        self.assertIsNone(interval["phase"])
        self.assertTrue(interval["phase_missing"])

        metadata = fusion.FusionMetadata()
        fusion.update_frame_and_stop_metadata(
            metadata, "ATGAAA", [{"phase": None}], [{"phase": 0}],
            [], [], 0, 0, 30,
        )
        self.assertTrue(metadata.phase_inferred)
        self.assertEqual(metadata.frame_inference_method, "sequence_length_fallback")

    def test_breakpoint_resolution_returns_mapping(self) -> None:
        segments = fusion.build_exon_segments(
            [(100, 109, None, "+"), (200, 209, None, "+")]
        )

        exonic = fusion.resolve_breakpoint_on_exon_chain(
            segments, 105, role="donor"
        )
        intronic = fusion.resolve_breakpoint_on_exon_chain(
            segments, 150, role="acceptor"
        )
        outside = fusion.resolve_breakpoint_on_exon_chain(
            segments, 300, role="donor"
        )

        self.assertEqual(exonic["tx_offset"], 5)
        self.assertEqual(exonic["location_type"], "exonic")
        self.assertEqual(intronic["tx_offset"], 10)
        self.assertEqual(intronic["location_type"], "intronic_splice_junction")
        self.assertEqual(outside["resolved_genomic_pos"], 209)
        self.assertEqual(outside["location_type"], "outside_snapped")

    def test_inframe_and_frameshift_fusions(self) -> None:
        self.assertEqual(fusion.compute_frame_status(6, 0, 0, 0), "INFRAME")
        self.assertEqual(fusion.compute_frame_status(7, 0, 0, 0), "FRAMESHIFT")

    def test_tryptic_digest(self) -> None:
        self.assertEqual(
            fusion.digest_tryptic_peptides(
                "AKRPQKLMR", max_missed_cleavages=0, min_len=1, max_len=20
            ),
            [
                {
                    "peptide_sequence": "AK",
                    "peptide_length": 2,
                    "peptide_start_aa": 1,
                    "peptide_end_aa": 2,
                    "missed_cleavages": 0,
                },
                {
                    "peptide_sequence": "RPQK",
                    "peptide_length": 4,
                    "peptide_start_aa": 3,
                    "peptide_end_aa": 6,
                    "missed_cleavages": 0,
                },
                {
                    "peptide_sequence": "LMR",
                    "peptide_length": 3,
                    "peptide_start_aa": 7,
                    "peptide_end_aa": 9,
                    "missed_cleavages": 0,
                },
            ],
        )

    def test_cli_defaults_are_unchanged(self) -> None:
        args = fusion.parse_arguments(
            [
                "--fusioninspector",
                "input.tsv",
                "--gtf_db",
                "genes.db",
                "--genome",
                "genome.fa",
                "--annotation_release",
                "GENCODE_46",
                "--organism",
                "Homo_sapiens",
            ]
        )
        self.assertEqual(args.min_protein_length, 30)
        self.assertEqual(args.nmd_distance_threshold_nt, 55)
        self.assertEqual(args.early_stop_aa_cutoff, 30)
        self.assertEqual(args.workers, 1)
        self.assertEqual(args.max_transcripts_per_gene, 3)
        self.assertEqual(args.max_missed_cleavages, 2)
        self.assertFalse(args.quantms_conservative)

    def test_concordance_categories_are_biologically_explicit(self) -> None:
        self.assertEqual(
            fusion.classify_caller_concordance("MK", None, "INFRAME", None, "ATGAAATAA"),
            "identical_protein",
        )
        self.assertEqual(
            fusion.classify_caller_concordance("MPEPTIDEK", "PEPTIDE", "NA", None),
            "same_junction_peptide",
        )
        self.assertEqual(
            fusion.classify_caller_concordance("AAA", "BBB", "INFRAME", "in-frame"),
            "frame_agreement",
        )
        self.assertEqual(
            fusion.classify_caller_concordance("AAA", "BBB", "INFRAME", "frameshift"),
            "discordant_sequence",
        )

    def test_ranking_schema_is_unique_and_stable(self) -> None:
        self.assertEqual(len(fusion.RANKING_RECORD_COLUMNS), len(set(fusion.RANKING_RECORD_COLUMNS)))
        self.assertEqual(fusion.RANKING_RECORD_COLUMNS[0], "sample_basename")
        self.assertEqual(fusion.RANKING_RECORD_COLUMNS[-1], "cds_sequence_hash")

    def test_ranking_record_uses_declared_schema(self) -> None:
        args = argparse.Namespace(
            min_retained_cds_nt=30,
            min_protein_length=30,
            require_junction_peptide=False,
            require_unique_junction_peptide=False,
            exclude_frameshift_from_dia=False,
            exclude_truncated_from_dia=False,
            exclude_nmd_from_dia=False,
            include_donor_only_products=False,
            max_breakpoint_snap_distance_nt=25,
            exclude_incomplete_cds=True,
        )
        event = fusion.CandidatePairRequest(
            row={},
            sample_label="sample",
            fusion_name="A-B",
            event_index=0,
            donor_index=0,
            acceptor_index=0,
            donor={"transcript_id": "D", "cds_completeness": "complete"},
            acceptor={"transcript_id": "A", "cds_completeness": "complete"},
            breakpoint_chrom1="1",
            breakpoint_chrom2="2",
            breakpoint1=10,
            breakpoint2=20,
        )
        functional = {
            "fusion_effect_class": "test",
            "donor_cds_retained_pct": 1.0,
            "acceptor_cds_retained_pct": 1.0,
            "predicted_loss_of_function": False,
            "predicted_chimera": True,
            "early_stop_after_junction": False,
        }
        record = fusion.build_ranking_record(
            fusion.RankingRecordRequest(
                event=event,
                pair_token="0_0_0",
                fusion_cds="ATG",
                fusion_meta={},
                protein_sequence="M",
                frame_status="INFRAME",
                caller_frame_annotation=None,
                caller_peptide=None,
                concordance="no_caller_reference",
                functional=functional,
                junction_evaluation={},
                junction_peptide_unique=None,
                nmd={},
                donor_retained_cds_nt=3,
                acceptor_retained_cds_nt=0,
                protein_identical_to_reference=None,
                breakpoint_snapped_far=False,
                max_snap_distance=0,
                config=fusion.FusionFilterConfig.from_namespace(args),
            )
        )
        self.assertEqual(tuple(record), fusion.RANKING_RECORD_COLUMNS)


if __name__ == "__main__":
    unittest.main()
