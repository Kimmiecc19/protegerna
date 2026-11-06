"""Regressions for the code-quality review (consistency, determinism and dead-code fixes)."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

import proteogenomic_workflow as workflow
import rmatstoprotein as rmats
from proteogenomic.biological_evidence import score_protein_evidence
from proteogenomic.fusion_reporting import order_ranking_dataframe
from proteogenomic.provenance import sha256_file
from proteogenomic.qc_calculations import add_peptide_eligibility, sequence_qc
from proteogenomic.qc_models import FastaRecord
from proteogenomic.splice_consequence import evaluate_shared_splice_consequence


class ConfidenceRubricTests(unittest.TestCase):
    def test_uppercase_inframe_status_earns_frame_credit(self):
        # Producers write frame_status="INFRAME"; the credit used to require "inframe".
        score = score_protein_evidence({"protein_sequence": "MPEPTIDEK", "frame_status": "INFRAME"})
        self.assertIn("frame_preserved", score["confidence_reasons"])


class SharedConsequenceTests(unittest.TestCase):
    def test_no_altered_cds_has_no_reading_frame(self):
        result = evaluate_shared_splice_consequence([], [(1, 30, 0)], "+", None, [(1, 30)])
        self.assertEqual(result.frame_status, "NA")
        self.assertIsNone(result.frameshift)
        self.assertIsNone(result.cds_delta_nt)

    def test_rmats_consequence_class_agrees_with_reported_frame(self):
        tx = {"cds": [(1, 30, 0), (101, 130, 0)], "strand": "+", "exons": [(1, 30), (101, 130)]}
        consequence = rmats.classify_splice_consequence(
            tx, [(1, 30), (101, 130)], [(1, 30, 0), (101, 130, 0)], "ATG" + "GCC" * 18 + "TAA",
            "SE", "included",
        )
        classes = consequence["consequence_class"].split(";")
        self.assertEqual(consequence["frame_status"], "INFRAME")
        self.assertIn("inframe", classes)
        self.assertNotIn("frameshift", classes)


class JunctionPeptideTests(unittest.TestCase):
    def test_junction_peptides_follow_final_fasta_membership(self):
        kept = {"source_file": "a", "event_type": "SE", "event_id": "E1", "tx": "T1",
                "variant": "included", "protein_in_fasta": True}
        dropped = {**kept, "variant": "skipped", "protein_in_fasta": False}
        records = []
        for row in (kept, dropped):
            record = SeqRecord(Seq("PEPTIDEK"), id=row["variant"])
            record.annotations[rmats._ROW_KEY] = rmats._audit_row_key(row)
            records.append(record)
        retained = rmats.retained_junction_records(records, [kept, dropped])
        self.assertEqual([record.id for record in retained], ["included"])


class QcEligibilityTests(unittest.TestCase):
    def test_duplicate_labels_do_not_share_eligibility(self):
        # Two files with the same label both start at ordinal 1.
        records = [
            FastaRecord("x", "a.fa", "a1", "MPEPTIDEKAAAAAAAR", 1),
            FastaRecord("x", "b.fa", "b1", "MK", 1),
        ]
        rows, _duplicates, summary = sequence_qc(records)
        add_peptide_eligibility(records, rows, summary, 2, 7, 40)
        self.assertTrue(rows[0]["has_eligible_tryptic_peptide"])
        self.assertFalse(rows[1]["has_eligible_tryptic_peptide"])


class WorkflowOutputTests(unittest.TestCase):
    def test_suppa_psi_summary_expected_only_with_psi_files(self):
        base = {"out_prot_fa": "s.fa", "out_consequence_tsv": "s.tsv", "out_psi_summary_tsv": "s.psi.tsv"}
        without = {str(p) for p in workflow.expected_outputs("suppa", base)}
        with_psi = {str(p) for p in workflow.expected_outputs("suppa", {**base, "psi_files": ["x.psi"]})}
        self.assertNotIn("s.psi.tsv", without)
        self.assertIn("s.psi.tsv", with_psi)

    def test_file_hash_is_memoised_but_tracks_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.txt"
            path.write_text("a")
            first = sha256_file(path)
            self.assertEqual(first, sha256_file(path))
            path.write_text("bb")
            self.assertNotEqual(first, sha256_file(path))


class FusionOrderingTests(unittest.TestCase):
    def test_output_order_is_independent_of_optional_tables_and_stable(self):
        frame = pd.DataFrame({
            "pair_token": ["a", "b", "c"], "protein_length": [10, 30, 10],
            "split_reads_sum": [1, 1, 1], "spanning_reads_sum": [0, 0, 0],
        })
        ordered = order_ranking_dataframe(frame)
        self.assertEqual(list(ordered["pair_token"]), ["b", "a", "c"])
        args = SimpleNamespace(biological_interpretation_tsv=None)
        from proteogenomic.fusion_reporting import write_biological_interpretation_table
        self.assertEqual(list(write_biological_interpretation_table(frame, args)["pair_token"]), ["b", "a", "c"])


if __name__ == "__main__":
    unittest.main()


class FusionFollowUpTests(unittest.TestCase):
    @staticmethod
    def _candidate(exons, cds):
        from proteogenomic.fusion_coordinates import build_cds_tx_segments, build_transcript_segments
        from proteogenomic.fusion_models import TranscriptCandidate
        exon_segments = build_transcript_segments([(s, e, "+") for s, e in exons])
        cds_exons = [(s, e, 0, "+") for s, e in cds]
        return TranscriptCandidate(
            chrom="chr1", cds_segments=build_transcript_segments(cds_exons),
            exon_segments=exon_segments, cds_tx_segments=build_cds_tx_segments(cds_exons, exon_segments),
        )

    def test_breakpoint_outside_transcript_is_low_confidence(self):
        from proteogenomic.fusion_candidate_evaluation import create_fusion_cds
        genome = {"chr1": "ATG" + "GCC" * 199 + "TAA" + "A" * 400}
        donor = self._candidate([(1, 90)], [(1, 90)])
        acceptor = self._candidate([(301, 390)], [(301, 390)])
        _, exonic = create_fusion_cds(genome, donor, acceptor, 60, 330)
        _, outside = create_fusion_cds(genome, donor, acceptor, 120, 330)  # 30 nt past donor end
        self.assertFalse(exonic["low_confidence"])
        self.assertEqual(outside["donor_breakpoint_location"], "outside_snapped")
        self.assertTrue(outside["low_confidence"])

    def test_resolver_can_leave_outside_breakpoints_unresolved(self):
        from proteogenomic.fusion_coordinates import build_transcript_segments, resolve_breakpoint_on_exon_chain
        segments = build_transcript_segments([(1, 90, "+")])
        self.assertIsNone(resolve_breakpoint_on_exon_chain(segments, 120, "donor", snap_outside=False))
        self.assertEqual(resolve_breakpoint_on_exon_chain(segments, 120, "donor")["location_type"], "outside_snapped")

    def test_pair_token_is_unique_across_samples(self):
        from proteogenomic.fusion_candidate_evaluation import fusion_pair_token
        self.assertNotEqual(fusion_pair_token("S1", 0, 0, 0), fusion_pair_token("S2", 0, 0, 0))
        self.assertEqual(fusion_pair_token("CASE-S1", 3, 1, 0), "CASE-S1:3_1_0")


class SuppaRescueTests(unittest.TestCase):
    @staticmethod
    def _args(**overrides):
        values = dict(pad_partial_codons=False, allow_alt_start=False, allow_longest_orf=False,
                      alternative_start_codons=["ATG"], min_alt_start_kozak_strength="weak", min_alt_orf_aa=3)
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_annotated_translation_is_unchanged_without_flags(self):
        import suppatoprotein as suppa
        tx = {"chrom": "chr1", "strand": "+", "cds": [(1, 12, 0)], "cds_start_nf": True}
        protein, strategy, _note, alt = suppa._translate_transcript("CCCATGGCCTAA", tx, self._args())
        self.assertEqual((protein, strategy, alt), ("PMA", "annotated_cds", None))

    def test_missing_start_codon_uses_alternative_start(self):
        import suppatoprotein as suppa
        tx = {"chrom": "chr1", "strand": "+", "cds": [(1, 12, 0)], "cds_start_nf": True}
        protein, strategy, note, alt = suppa._translate_transcript(
            "CCCATGGCCTAA", tx, self._args(allow_alt_start=True))
        self.assertEqual((protein, strategy, note), ("MA", "alternative_start", "translated_from_downstream_atg_nt_3"))
        self.assertEqual(alt.codon, "ATG")

    def test_untranslatable_cds_uses_longest_orf(self):
        import suppatoprotein as suppa
        tx = {"chrom": "chr1", "strand": "+", "cds": [(1, 15, 0)]}
        protein, strategy, _note, _alt = suppa._translate_transcript(
            "TAAGCCGCCGCCGCC", tx, self._args(allow_longest_orf=True))
        self.assertEqual(strategy, "alternative_orf")
        self.assertTrue(protein)


class ReferenceAndChromosomeTests(unittest.TestCase):
    def test_mitochondrial_names_resolve_between_gencode_and_ensembl(self):
        from proteogenomic.splice_translation import extract_sequence_from_indexed_genome
        from proteogenomic.fusion_coordinates import resolve_chrom_name
        ensembl = {"MT": "ACGTACGT", "1": "GGGGCCCC"}
        gencode = {"chrM": "ACGTACGT"}
        self.assertEqual(extract_sequence_from_indexed_genome(ensembl, "chrM", [(1, 4)], "+"), "ACGT")
        self.assertEqual(extract_sequence_from_indexed_genome(ensembl, "chr1", [(1, 4)], "+"), "GGGG")
        self.assertEqual(resolve_chrom_name(gencode, "MT"), "chrM")
        self.assertIsNone(resolve_chrom_name(ensembl, "chr2"))

    def test_reference_peptides_combine_canonical_and_isoform_fastas(self):
        import gzip
        from proteogenomic.splice_translation import load_reference_tryptic_peptides
        with tempfile.TemporaryDirectory() as directory:
            canonical = Path(directory) / "canonical.fasta"
            isoforms = Path(directory) / "additional.fasta.gz"
            cache = Path(directory) / "peptides.cache"
            canonical.write_text(">sp|P1|A\nAAAAAAAK\n", encoding="utf-8")
            with gzip.open(isoforms, "wt", encoding="utf-8") as handle:
                handle.write(">sp|P1-2|A\nCCCCCCCK\n")
            one = load_reference_tryptic_peptides([str(canonical)], 2, 7, 40, cache_path=cache)
            both = load_reference_tryptic_peptides([str(canonical), str(isoforms)], 2, 7, 40, cache_path=cache)
            self.assertEqual(one, {"AAAAAAAK"})
            self.assertEqual(both, {"AAAAAAAK", "CCCCCCCK"})  # cache rebuilt for the new file list


class IncludeFailedFilterProteinsTests(unittest.TestCase):
    @staticmethod
    def _args(include_failed):
        return SimpleNamespace(
            include_failed_filter_proteins=include_failed, require_unique_event_peptide=True,
            max_missed_cleavages=2, min_database_peptide_length=7, max_database_peptide_length=40,
            exclude_incomplete_cds=True, exclude_nmd_from_dia=True,
        )

    def test_policy_failures_are_exported_with_their_reasons(self):
        consequence = {"nmd_predicted": True, "cds_completeness": "complete"}
        reference = {"PEPTIDEK"}
        kept = rmats._fasta_decision(consequence, "MAAAAAAAK", "canonical_cds", "MCCCCCCCK", reference, self._args(True))
        dropped = rmats._fasta_decision(consequence, "MAAAAAAAK", "canonical_cds", "MCCCCCCCK", reference, self._args(False))
        self.assertTrue(kept.include)
        self.assertEqual(kept.tier, "primary_dia")
        self.assertIn("nmd_predicted_excluded_from_dia", kept.exclusion_reasons)
        self.assertFalse(dropped.include)
        self.assertEqual(dropped.exclusion_reasons, kept.exclusion_reasons)

    def test_canonical_identical_proteins_are_never_exported(self):
        decision = rmats._fasta_decision({}, "MAAAAAAAK", "canonical_cds", "MAAAAAAAK", set(), self._args(True))
        self.assertFalse(decision.include)
