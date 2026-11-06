"""Unit tests for the named steps of rMATS per-isoform reconstruction."""
import unittest

from proteogenomic.proteogenomic_policies import ReconstructionPolicy
from proteogenomic.splice_cli import parse_rmats_args
from proteogenomic.splice_reconstruction_core import SpliceReconstructionConfig
from rmatstoprotein import (
    _VariantFrame, _annotated_start_offset, _excluded_row, _fasta_decision,
)

CANONICAL = "MPEPTIDEKALVAGHIKAASGGGQTPRKKAVLGHPEPTIDEKAAAVVVKR"
VARIANT = "MPEPTIDEKALVAGHIKAASVLGHPEPTIDEKAAAVVVKR"


def policy_args(*extra):
    args, _ = parse_rmats_args([
        "--gtf_db", "a.db", "--genome", "g.fa", "--annotation_release", "G46",
        "--organism", "human", "--out_prot_fa", "out.fa", "--se_files", "SE.txt",
        "--reference_proteome", "ref.fa", *extra,
    ])
    args.reconstruction_policy = ReconstructionPolicy.from_namespace(args)
    args.reconstruction_config = SpliceReconstructionConfig(
        require_ri_read_evidence=args.require_ri_read_evidence,
        min_ri_inclusion_reads=args.min_ri_inclusion_reads,
        exclude_ri_nmd_from_primary=args.exclude_ri_nmd_from_primary,
        require_ri_junction_peptide=args.require_ri_junction_peptide,
    )
    return args


def decide(consequence, protein=VARIANT, strategy="annotated_start", canonical=CANONICAL,
           reference=frozenset(), args=None):
    return _fasta_decision(consequence, protein, strategy, canonical, set(reference), args or policy_args())


class FastaDecisionTests(unittest.TestCase):
    def test_clean_variant_goes_to_primary(self):
        decision = decide({"cds_completeness": "complete"})
        self.assertTrue(decision.include)
        self.assertEqual((decision.tier, decision.collector), ("primary_dia", "primary"))
        self.assertTrue(decision.has_unique_peptide)

    def test_general_dia_filter_records_reason(self):
        decision = decide({"frameshift": True}, args=policy_args("--exclude_frameshift_from_dia"))
        self.assertFalse(decision.include)
        self.assertEqual(decision.tier, "excluded")
        self.assertIn("frameshift_excluded_from_dia", decision.exclusion_reasons)

    def test_retained_intron_rules(self):
        decision = decide({
            "ri_read_evidence_supported": False, "ri_ambiguous_base_count": 2,
            "nmd_predicted": True, "ri_has_junction_spanning_searchable_peptide": False,
        })
        self.assertFalse(decision.include)
        for reason in ("ri_without_required_read_evidence", "ri_contains_ambiguous_genomic_bases",
                       "ri_nmd_predicted_excluded_from_primary", "ri_no_junction_spanning_searchable_peptide"):
            self.assertIn(reason, decision.exclusion_reasons)

    def test_ri_rules_only_apply_when_ri_evidence_was_evaluated(self):
        decision = decide({"nmd_predicted": True})  # not an RI isoform; NMD DIA filter off by default
        self.assertTrue(decision.include)

    def test_no_orf_and_identical_to_canonical(self):
        self.assertIn("no_translatable_orf", decide({}, protein=None).exclusion_reasons)
        identical = decide({}, protein=CANONICAL)
        self.assertFalse(identical.include)
        self.assertIn("protein_sequence_identical_to_canonical", identical.exclusion_reasons)

    def test_rescue_product_bypasses_primary_filters_into_its_own_tier(self):
        decision = decide({"frameshift": True}, strategy="alternative_start",
                          args=policy_args("--exclude_frameshift_from_dia"))
        self.assertTrue(decision.include)
        self.assertEqual(decision.exclusion_reasons, "")
        self.assertEqual((decision.tier, decision.collector), ("exploratory", "alternative_start"))

    def test_rescue_product_identical_to_canonical_is_still_excluded(self):
        decision = decide({}, protein=CANONICAL, strategy="alternative_orf")
        self.assertFalse(decision.include)

    def test_unique_peptide_count_against_reference(self):
        from proteogenomic.splice_translation import digest_tryptic_peptides
        reference = set(digest_tryptic_peptides(VARIANT, 3, 7, 40))
        decision = decide({}, reference=reference)
        self.assertEqual(decision.unique_peptide_count, 0)
        self.assertFalse(decision.has_unique_peptide)

    def test_require_unique_event_peptide_excludes_primary_without_reference_unique_peptide(self):
        """Regression test for the 2026-10-12 fix (tier "primary_dia" was never matched)."""
        from proteogenomic.splice_translation import digest_tryptic_peptides
        reference = set(digest_tryptic_peptides(VARIANT, 3, 7, 40))
        decision = decide({}, reference=reference, args=policy_args("--require_unique_event_peptide"))
        self.assertEqual(decision.tier, "excluded")
        self.assertFalse(decision.include)
        self.assertIsNone(decision.collector)
        self.assertIn("no_reference_unique_tryptic_peptide", decision.exclusion_reasons)
        kept = decide({}, args=policy_args("--require_unique_event_peptide"))  # has a unique peptide
        self.assertEqual(kept.tier, "primary_dia")


class StepHelperTests(unittest.TestCase):
    MODEL = {"strand": "+", "cds": [(1, 60, 0), (101, 130, 0), (201, 260, 0)]}

    def frame(self, upstream, trim=0):
        return _VariantFrame(first_overlap_position=1, upstream_cds_nt=upstream, trim=trim,
                             sequence="", trimmed=bool(trim), mismatch=False)

    def test_annotated_start_inside_altered_cds(self):
        segments = [(1, 60, 0), (201, 260, 0)]
        self.assertEqual(_annotated_start_offset(self.MODEL, segments, self.frame(0)), 0)

    def test_annotated_start_outside_altered_cds(self):
        segments = [(101, 130, 0), (201, 260, 0)]
        self.assertIsNone(_annotated_start_offset(self.MODEL, segments, self.frame(60)))
        self.assertIsNone(_annotated_start_offset({"strand": "+", "cds": []}, segments, self.frame(0)))

    def test_excluded_row_keeps_audit_column_order(self):
        row = _excluded_row({"gene_id": "G"}, {"region_class": "x"}, "MK", "1-3", "why")
        self.assertEqual(list(row), ["gene_id", "region_class", "protein_sequence", "protein_length",
                                     "coords", "protein_in_fasta", "fasta_exclusion_reasons"])
        self.assertEqual((row["protein_length"], row["protein_in_fasta"]), (2, False))



class FixRegressionTests(unittest.TestCase):
    def test_unresolved_reading_frame_leaves_an_audit_row(self):
        """2026-10-12 fix: these isoforms used to vanish from the consequence table."""
        from pathlib import Path
        from types import SimpleNamespace
        from unittest import mock
        import rmatstoprotein as rmats
        projection = SimpleNamespace(variant="skipped", exon_chain=[(1, 60)], cds_segments=[(1, 60, 0)])
        cds = rmats._VariantCds("ATG" * 20, [(1, 60)], "1-60", None)
        args = SimpleNamespace(organism="human", annotation_release="G46")
        rows, junctions = [], []
        with mock.patch.object(rmats, "build_variant_chains_for_transcript", return_value={}), \
             mock.patch.object(rmats, "project_event_variants", return_value=[projection]), \
             mock.patch.object(rmats, "_variant_cds", return_value=cds), \
             mock.patch.object(rmats, "_resolve_frame_and_trim", return_value=None):
            rmats._evaluate_rmats_variant_projections(
                "SE", {}, "E1", Path("CASE-CTRL/SE.MATS.JC.txt"),
                {"transcript_id": "T1", "gene_id": "G1", "exons": [(1, 60)], "cds": [(1, 60, 0)]},
                None, args, {}, {}, {}, None, junctions, rows, set(),
            )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["region_class"], "unresolved_reading_frame")
        self.assertEqual(rows[0]["fasta_exclusion_reasons"], "unresolved_reading_frame")
        self.assertFalse(rows[0]["protein_in_fasta"])
        self.assertEqual(rows[0]["coords"], "1-60")

    def test_rescue_products_are_capped_by_translation_strategy(self):
        """2026-10-12 fix: rMATS rescue rows carry tier 'exploratory', not the names checked before."""
        from proteogenomic.biological_evidence import score_protein_evidence
        strong = {"protein_sequence": "MPEPTIDEK", "inframe": True, "transcript_candidate_count": 1,
                  "premature_stop": False, "has_reference_unique_tryptic_peptide": True,
                  "inclusion_junction_reads": 20, "cds_completeness": "complete"}
        self.assertGreaterEqual(score_protein_evidence(strong)["confidence_score"], 80)
        rescue = dict(strong, translation_strategy="alternative_orf", database_output_tier="exploratory")
        scored = score_protein_evidence(rescue)
        self.assertLessEqual(scored["confidence_score"], 39)
        self.assertIn("alternative_start_or_uncertain_orf", scored["confidence_reasons"])


if __name__ == "__main__":
    unittest.main()
