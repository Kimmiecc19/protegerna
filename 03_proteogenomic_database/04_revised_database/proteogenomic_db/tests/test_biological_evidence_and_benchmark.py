import unittest

import pandas as pd

from benchmark_variant_reconstruction import benchmark
from proteogenomic.biological_evidence import score_protein_evidence, simplified_consequence
from proteogenomic.splice_reconstruction_core import rank_compatible_transcripts


class BiologicalEvidenceTests(unittest.TestCase):
    def test_high_confidence_combines_biology_and_experimental_support(self):
        result = score_protein_evidence({
            "protein_sequence": "MPEPTIDE", "inframe": True,
            "transcript_candidate_count": 7, "transcript_selection_ambiguous": False,
            "premature_stop": False, "has_reference_unique_tryptic_peptide": True,
            "psi_max": 0.4, "database_output_tier": "primary",
        })
        self.assertEqual(result["confidence"], "High confidence")
        self.assertEqual(result["confidence_score"], 100)

    def test_no_assessed_peptide_is_rejected(self):
        result = score_protein_evidence({
            "protein_sequence": "MPEPTIDE", "has_reference_unique_tryptic_peptide": False,
        })
        self.assertEqual(result["confidence"], "Rejected")

    def test_reader_facing_consequences_use_six_categories(self):
        base = {"protein_sequence": "MP"}
        self.assertEqual(simplified_consequence({**base, "cds_delta_nt": 0}), "Canonical")
        self.assertEqual(simplified_consequence({**base, "cds_delta_nt": 3}), "Altered protein")
        self.assertEqual(simplified_consequence({**base, "frameshift": True}), "Frameshift")
        self.assertEqual(simplified_consequence({**base, "premature_stop": True}), "Premature stop")
        self.assertEqual(simplified_consequence({**base, "nmd_predicted": True}), "NMD candidate")
        self.assertEqual(simplified_consequence({"protein_sequence": None}), "Ambiguous")

    def test_top_three_transcripts_are_reported(self):
        query = {"gene_id": "G", "chrom": "1", "strand": "+", "cds": [(1, 30, 0)], "exons": [(1, 50)]}
        candidates = [{**query, "transcript_id": f"T{i}", "cds": [(1, 30 - i, 0)]} for i in range(1, 5)]
        _, ranking = rank_compatible_transcripts(query, candidates)
        self.assertEqual(ranking.candidate_count, 4)
        self.assertEqual(ranking.top_candidates, ("T1", "T2", "T3"))
        self.assertEqual(ranking.reason, "hierarchical_biological_selection")
        self.assertEqual(
            ranking.selection_path,
            "compatible>protein_coding>complete_cds>preserves_event>annotation_quality",
        )


class ReconstructionBenchmarkTests(unittest.TestCase):
    def test_reports_exact_accuracy_and_missing_reconstruction(self):
        truth = pd.DataFrame([
            {"event_id": "E1", "tx": "T1", "variant": "included", "protein_sequence": "MP", "frame_status": "inframe", "premature_stop": False},
            {"event_id": "E2", "tx": "T2", "variant": "skipped", "protein_sequence": "MK", "frame_status": "frameshift", "premature_stop": True},
        ])
        actual = truth.iloc[:1].copy()
        _, summary = benchmark(actual, truth)
        self.assertEqual(summary["truth_records"], 2)
        self.assertEqual(summary["reconstruction_recall"], 0.5)
        self.assertEqual(summary["exact_record_accuracy"], 0.5)


if __name__ == "__main__":
    unittest.main()
