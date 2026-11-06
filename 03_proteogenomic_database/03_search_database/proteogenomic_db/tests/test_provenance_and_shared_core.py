import tempfile
import unittest
from pathlib import Path

from proteogenomic.provenance import (
    batch_from_path, load_sample_metadata, sample_provenance,
)
from proteogenomic.splice_translation import (
    build_splice_fasta_header, digest_tryptic_records,
    intersect_interval_lists, load_reference_tryptic_peptides,
    replace_interval_in_list, subtract_interval_list,
)
import rmatstoprotein as rmats
from proteogenomic.splice_reconstruction_core import (
    BoundedCache, CanonicalProteinCache, TranscriptResolver, assess_alternative_start,
    rank_compatible_transcripts,
)


class ProvenanceTests(unittest.TestCase):
    def test_batch_is_preserved_from_nfcore_path(self):
        path = "/home/user/nf_results/rnasplice/batch12/old/star_salmon/suppa/x.psi"
        self.assertEqual(batch_from_path(path), "batch12")

    def test_explicit_metadata_overrides_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.tsv"
            path.write_text("sample_id\tbatch\tcondition\nS1\tbatch7\ttumour\n", encoding="utf-8")
            lookup = load_sample_metadata(path)
            self.assertEqual(
                sample_provenance("S1", "/x/batch2/file.psi", lookup),
                {"sample_id": "S1", "batch": "batch7", "condition": "tumour", "provenance_source": "sample_metadata"},
            )

    def test_duplicate_sample_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.tsv"
            path.write_text("sample_id\nS1\nS1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate sample_id"):
                load_sample_metadata(path)


class SharedDigestionTests(unittest.TestCase):
    def test_stop_separated_positions_and_missed_cleavages(self):
        records = digest_tryptic_records("AK*RPQK", 0, 1, 20)
        self.assertEqual(
            [(x["peptide_sequence"], x["peptide_start_aa"], x["peptide_end_aa"]) for x in records],
            [("AK", 1, 2), ("RPQK", 3, 6)],
        )

    def test_shared_interval_operations(self):
        self.assertEqual(subtract_interval_list([(1, 10)], 4, 6), [(1, 3), (7, 10)])
        self.assertEqual(replace_interval_in_list([(1, 10)], 4, 6, [(20, 22)]), [(1, 3), (7, 10), (20, 22)])
        self.assertEqual(intersect_interval_lists([(1, 5), (10, 20)], [(3, 12)]), [(3, 5), (10, 12)])

    def test_reference_cache_is_invalidated_by_fasta_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            fasta = Path(tmp) / "reference.fa"
            cache = Path(tmp) / "reference.peptides.pkl"
            fasta.write_text(">a\nAKPEPTIDER\n", encoding="utf-8")
            first = load_reference_tryptic_peptides(fasta, 0, 1, 40, cache)
            fasta.write_text(">a\nMKWVTF\n", encoding="utf-8")
            second = load_reference_tryptic_peptides(fasta, 0, 1, 40, cache)
            self.assertNotEqual(first, second)

    def test_alt_start_whitelist_and_header_flag(self):
        protein, strategy, _ = rmats.translate_consequence_aware(
            "GTGAAATAA", {"start_loss": True, "region_class": "cds_overlap"},
            allow_alt_start=True, alternative_start_codons=("GTG",),
        )
        self.assertEqual((protein, strategy), ("VK", "alternative_start"))
        header = build_splice_fasta_header("rmats", 1, protein, {"mappings": [{
            "gene_symbol": "G", "database_output_tier": "alternative_start",
            "alt_start": "Yes", "organism": "Homo_sapiens",
        }]})
        self.assertIn("alt_start=Yes", header)

    def test_suppa_header_records_psi_policy(self):
        header = build_splice_fasta_header("suppa", 1, "PEPTIDE", {"mappings": [{
            "gene_symbol": "G", "source_event_id": "ENSG;SE:chr1:1-2:+",
            "psi_min_threshold": 0.05, "psi_min_samples": 3,
            "organism": "Homo_sapiens",
        }]})
        self.assertIn("source_event_id=ENSG,SE:chr1:1-2:+", header)
        self.assertIn("psi_min_threshold=0.05", header)
        self.assertIn("psi_min_samples=3", header)

    def test_rmats_header_preserves_failed_filter_audit(self):
        header = build_splice_fasta_header("rmats", 1, "PEPTIDE", {"mappings": [{
            "gene_symbol": "G", "database_output_tier": "primary_dia",
            "passed_dia_filters": False,
            "fasta_exclusion_reasons": "nmd_predicted_excluded_from_dia",
            "organism": "Homo_sapiens",
        }]})
        self.assertIn("passed_dia_filters=False", header)
        self.assertIn("fasta_exclusion_reasons=nmd_predicted_excluded_from_dia", header)


class TypedReconstructionCoreTests(unittest.TestCase):
    def test_kozak_strength_uses_minus3_and_plus4_consensus(self):
        assessment = assess_alternative_start("AAAATGG", 3)
        self.assertTrue(assessment.frame_conserved)
        self.assertEqual(assessment.kozak_strength, "strong")
        self.assertEqual((assessment.minus3_base, assessment.plus4_base), ("A", "G"))
        self.assertEqual(len(assessment.context_minus6_plus6), 13)

    def test_transcript_ranking_reports_tied_ambiguity(self):
        query = {"gene_id": "G", "chrom": "1", "strand": "+", "cds": [(1, 9, 0)], "exons": [(1, 20)]}
        candidates = [
            {**query, "transcript_id": "T1"},
            {**query, "transcript_id": "T2"},
        ]
        selected, ranking = rank_compatible_transcripts(query, candidates)
        self.assertEqual(selected["transcript_id"], "T1")
        self.assertTrue(ranking.ambiguous)
        self.assertEqual(ranking.tied_best_count, 2)

    def test_transcript_resolver_and_bounded_cache(self):
        resolver = TranscriptResolver({"ENST1.2": {"transcript_id": "ENST1.2"}})
        resolution = resolver.resolve("ENST1")
        self.assertEqual(resolution.matched_id, "ENST1.2")
        cache = BoundedCache[int](2)
        cache.put("a", 1); cache.put("b", 2); cache.put("c", 3)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(len(cache), 2)

    def test_canonical_protein_cache_computes_once(self):
        cache = CanonicalProteinCache()
        calls = []
        self.assertEqual(cache.get_or_compute("T1", lambda: calls.append(1) or "MK"), "MK")
        self.assertEqual(cache.get_or_compute("T1", lambda: calls.append(2) or "XX"), "MK")
        self.assertEqual(calls, [1])
