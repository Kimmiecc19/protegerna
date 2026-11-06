"""Production integration smoke tests using only stable dependency names."""
import unittest
import tempfile
import inspect
from pathlib import Path

import fusiontoprotein as fusion
import merge_proteogenomic_database as merge
import proteogenomic_fasta_qc as qc
import rmatstoprotein as rmats
import suppatoprotein as suppa
from proteogenomic import fusion_parsing
from proteogenomic import fusion_reconstruction
from proteogenomic import fusion_reporting
from proteogenomic import rmats_evidence
from proteogenomic import rmats_parsing
from proteogenomic import suppa_parsing
from proteogenomic import suppa_psi
from proteogenomic.splice_cli import build_rmats_parser, build_suppa_parser
from proteogenomic.splice_annotation import build_transcript_models
from proteogenomic.splice_translation import classify_phased_junction_frame
from proteogenomic.proteogenomic_digestion import digest_records, digest_sequences
from proteogenomic.proteogenomic_policies import DigestionPolicy
from proteogenomic.splice_consequence import evaluate_shared_splice_consequence


class ProductionImportTests(unittest.TestCase):
    def test_all_production_entry_points_import_together(self):
        self.assertTrue(callable(fusion.create_fusion_cds))
        self.assertTrue(callable(rmats.build_variant_chains_for_transcript))
        self.assertTrue(callable(suppa.generate_codon_aware_junction_peptides))
        self.assertTrue(callable(merge.digest_tryptic_peptides))
        self.assertTrue(callable(qc.write_filtered_fasta))
        self.assertTrue(callable(fusion_parsing.parse_fusioninspector))
        self.assertTrue(callable(fusion_reconstruction.create_fusion_cds))
        self.assertTrue(callable(fusion_reporting.write_candidate_fastas))
        self.assertIs(rmats.build_transcript_models, build_transcript_models)
        self.assertIs(suppa.build_transcript_models, build_transcript_models)
        self.assertIs(rmats.evaluate_rmats_event, rmats_evidence.evaluate_rmats_event)
        self.assertIs(rmats.retained_intron_evidence, rmats_evidence.retained_intron_evidence)
        self.assertIs(rmats.rmats_event_intervals, rmats_parsing.rmats_event_intervals)
        self.assertIs(suppa.evaluate_psi_event, suppa_psi.evaluate_psi_event)
        self.assertIs(suppa.load_psi_files, suppa_psi.load_psi_files)
        self.assertIs(suppa.parse_suppa_event_coords, suppa_parsing.parse_suppa_event_coords)

    def test_splice_cli_defaults_remain_caller_specific(self):
        rmats_actions = {action.dest: action.default for action in build_rmats_parser()._actions}
        suppa_actions = {action.dest: action.default for action in build_suppa_parser()._actions}
        self.assertEqual(rmats_actions["alternative_start_codons"], ["ATG"])
        self.assertEqual(rmats_actions["chunksize"], 50000)
        self.assertNotIn("chunksize", suppa_actions)
        self.assertEqual(suppa_actions["min_psi"], 0.05)

    def test_fusion_uses_shared_phase_classifier(self):
        expected = classify_phased_junction_frame(6, 0, 0, 0)
        self.assertEqual(fusion.compute_frame_status(6, 0, 0, 0), expected)
        self.assertEqual(fusion.compute_frame_status(6, 0, None, 0), "NA")

    def test_qc_preserves_duplicate_sequences_for_merge_authority(self):
        records = [
            qc.FastaRecord("primary", "a.fa", "A|tier=primary", "MPEPTIDEK", 1),
            qc.FastaRecord("primary", "b.fa", "B|tier=primary", "MPEPTIDEK", 2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "filtered.fa"
            exclusions = Path(directory) / "excluded.tsv"
            summary = qc.write_filtered_fasta(
                records, output, exclusions, 1, False, 0, 7, 40,
            )
            self.assertEqual(summary["kept_records"], 2)
            self.assertEqual(output.read_text(encoding="utf-8").count(">"), 2)

    def test_shared_digestion_has_typed_and_set_views(self):
        policy = DigestionPolicy(0, 1, 20)
        records = digest_records("AK*RPQK", policy)
        self.assertEqual([record.peptide_sequence for record in records], ["AK", "RPQK"])
        self.assertEqual(digest_sequences("AK*RPQK", policy), {"AK", "RPQK"})

    def test_public_splice_processors_do_not_accept_collectors(self):
        rmats_parameters = inspect.signature(rmats.process_rmats_transcript_variants).parameters
        suppa_parameters = inspect.signature(suppa.process_suppa_row).parameters
        for collector in ("prot_info", "junction_recs", "consequence_rows"):
            self.assertNotIn(collector, rmats_parameters)
            self.assertNotIn(collector, suppa_parameters)

    def test_rmats_workers_share_the_typed_canonical_cache(self):
        run_source = inspect.getsource(rmats.run)
        # Every worker receives the single run-level cache, never a fresh dict.
        self.assertIn(
            "result.exploratory_orf_proteins,\n            canonical_cache,",
            run_source,
        )
        self.assertEqual(run_source.count("CanonicalProteinCache()"), 1)

    def test_shared_splice_consequence_is_caller_neutral(self):
        result = evaluate_shared_splice_consequence(
            [(1, 6, 0)], [(1, 6, 0)], "+", "ATGTAA", [(1, 6)]
        )
        self.assertEqual(result.frame_status, "INFRAME")
        self.assertEqual(result.cds_delta_nt, 0)

    def test_fusion_producer_does_not_deduplicate_final_sequences(self):
        frame = __import__("pandas").DataFrame([
            {"protein_sequence": "MPEPTIDE", "sample_basename": "S1"},
            {"protein_sequence": "MPEPTIDE", "sample_basename": "S2"},
        ])
        self.assertEqual(len(fusion.filter_database_isoforms(frame)), 2)

    def test_qc_is_diagnostic_by_default(self):
        args = qc.parse_args(["--fasta", "input.fa"])
        self.assertFalse(args.write_filtered_fasta)


if __name__ == "__main__":
    unittest.main()
