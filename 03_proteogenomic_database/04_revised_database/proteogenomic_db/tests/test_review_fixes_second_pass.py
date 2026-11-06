"""Regressions for the second 2026-10-12 review (sample identity, PSI, resume, release binding)."""
import json
import tempfile
import unittest
from pathlib import Path

import proteogenomic_workflow as workflow
from proteogenomic.fusion_orchestration import (
    derive_sample_label, fusioninspector_input_matches, group_fusioninspector_inputs,
)
from proteogenomic.release_validation import check_concordance_binding
from proteogenomic.suppa_parsing import expand_file_patterns
from proteogenomic.suppa_psi import evaluate_psi_event, load_psi_files


class FusionSampleIdentityTests(unittest.TestCase):
    def test_tumour_and_normal_samples_stay_distinct(self):
        self.assertEqual(derive_sample_label("CASE1-T.fusioninspector.fusions.tsv"), "CASE1-T")
        self.assertEqual(derive_sample_label("CASE1-N.fusioninspector.fusions.tsv"), "CASE1-N")

    def test_every_accepted_suffix_maps_to_the_same_sample(self):
        for suffix in (".fusions.tsv", ".fusions.abridged.tsv",
                       ".fusions.filtered.tsv", ".fusions.abridged.filtered.tsv"):
            name = f"CASE1.fusioninspector{suffix}"
            self.assertTrue(fusioninspector_input_matches(name), name)
            self.assertEqual(derive_sample_label(name), "CASE1", name)
        self.assertFalse(fusioninspector_input_matches("CASE1.fusioninspector.tsv"))

    def test_grouping_keeps_tumour_normal_and_merges_filtered_variants(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("CASE1-T.fusioninspector.fusions.tsv", "CASE1-N.fusioninspector.fusions.tsv",
                         "CASE2.fusioninspector.fusions.tsv", "CASE2.fusioninspector.fusions.abridged.filtered.tsv"):
                Path(directory, name).write_text("x", encoding="utf-8")
            groups = group_fusioninspector_inputs([directory])
        self.assertEqual(sorted(groups), ["CASE1-N", "CASE1-T", "CASE2"])
        self.assertEqual(len(groups["CASE2"]["fusioninspector"]), 2)


class PsiEvidenceTests(unittest.TestCase):
    def _write(self, directory, name, text):
        path = Path(directory, name); path.write_text(text, encoding="utf-8"); return path

    def test_support_counts_distinct_samples_not_observations(self):
        with tempfile.TemporaryDirectory() as d:
            a = self._write(d, "a.psi", "SAMPLE1\nEV1\t0.8\n")
            b = self._write(d, "b.psi", "SAMPLE1\nEV1\t0.8\n")
            lookup = load_psi_files([a, b])
        keep, info = evaluate_psi_event("EV1", lookup, min_psi=0.5, min_samples=2)
        self.assertFalse(keep)
        self.assertEqual(info["psi_samples_passing"], 1)
        self.assertEqual(info["psi_total_samples"], 1)

    def test_distinct_samples_across_files_are_pooled(self):
        with tempfile.TemporaryDirectory() as d:
            a = self._write(d, "a.psi", "SAMPLE1\nEV1\t0.8\n")
            b = self._write(d, "b.psi", "SAMPLE2\nEV1\t0.9\n")
            lookup = load_psi_files([a, b])
        keep, info = evaluate_psi_event("EV1", lookup, min_psi=0.5, min_samples=2)
        self.assertTrue(keep)
        self.assertEqual(info["psi_total_samples"], 2)

    def test_conflicting_duplicate_observations_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a = self._write(d, "a.psi", "SAMPLE1\nEV1\t0.8\n")
            b = self._write(d, "b.psi", "SAMPLE1\nEV1\t0.1\n")
            with self.assertRaisesRegex(ValueError, "Conflicting PSI"):
                load_psi_files([a, b])

    def test_requested_psi_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                expand_file_patterns([str(Path(d, "*.psi"))], "PSI", require_each=True)
            with self.assertRaises(FileNotFoundError):
                load_psi_files([Path(d, "missing.psi")])
            empty = self._write(d, "empty.psi", "SAMPLE1\n")
            with self.assertRaises(ValueError):
                load_psi_files([empty])

    def test_none_lookup_still_means_filter_deliberately_omitted(self):
        keep, info = evaluate_psi_event("EV1", None, 0.5, 1)
        self.assertTrue(keep)
        self.assertFalse(info["psi_filter_applied"])


class ResumeFingerprintTests(unittest.TestCase):
    def test_glob_inputs_are_hashed_and_track_membership(self):
        with tempfile.TemporaryDirectory() as d:
            first = Path(d, "a.ioe"); first.write_text("one", encoding="utf-8")
            values = {"event_files": [str(Path(d, "*.ioe"))]}
            before = workflow._manifest("suppa", values, "h")
            self.assertEqual(list(before["input_sha256"]), [str(first)])
            first.write_text("changed", encoding="utf-8")
            changed = workflow._manifest("suppa", values, "h")
            self.assertNotEqual(before["input_sha256"], changed["input_sha256"])
            Path(d, "b.ioe").write_text("two", encoding="utf-8")
            added = workflow._manifest("suppa", values, "h")
            self.assertEqual(len(added["input_sha256"]), 2)

    def test_expected_outputs_include_parser_default_outputs(self):
        values = {"out_fasta": "final.fasta"}
        names = {p.name for p in workflow.expected_outputs("merge", values)}
        self.assertIn("final.fasta", names)
        self.assertIn("proteogenomic_record_mapping.tsv", names)
        self.assertIn("proteogenomic_final_peptide_evidence.tsv", names)

    def test_manifest_includes_source_digest_and_round_trips(self):
        manifest = workflow._manifest("merge", {"out_fasta": "x.fasta"}, "h")
        self.assertRegex(manifest["source_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("parser_defaults", manifest)
        self.assertEqual(json.loads(json.dumps(manifest, default=str)), manifest)
        self.assertTrue(any(p.name == "merge_aggregation.py" for p in workflow._source_files("merge")))


class ConcordanceBindingTests(unittest.TestCase):
    def _summary(self, release="GENCODE_46", gtf="g" * 64, genome="f" * 64):
        return {"reference": {"annotation_release": release,
                              "gtf_db": {"path": "a.db", "sha256": gtf},
                              "genome": {"path": "g.fa", "sha256": genome}}}

    def _producer(self, directory, release="GENCODE_46", gtf="g" * 64, genome="f" * 64):
        fasta = Path(directory, "rmats.primary.fasta"); fasta.write_text(">x\nM\n", encoding="utf-8")
        Path(f"{fasta}.run_config.json").write_text(json.dumps({
            "arguments": {"annotation_release": release, "gtf_db": "a.db", "genome": "g.fa"},
            "input_sha256": {"a.db": gtf, "g.fa": genome},
        }), encoding="utf-8")
        return fasta

    def test_summary_without_reference_identity_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "does not identify"):
            check_concordance_binding({}, "GENCODE_46")

    def test_summary_for_another_release_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "GENCODE_45"):
            check_concordance_binding(self._summary("GENCODE_45"), "GENCODE_46")

    def test_producer_built_from_different_genome_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            fasta = self._producer(d, genome="0" * 64)
            with self.assertRaisesRegex(RuntimeError, "genome"):
                check_concordance_binding(self._summary(), "GENCODE_46", [fasta])

    def test_matching_release_and_producers_pass(self):
        with tempfile.TemporaryDirectory() as d:
            fasta = self._producer(d)
            other = Path(d, "external.fasta"); other.write_text(">y\nM\n", encoding="utf-8")
            result = check_concordance_binding(self._summary(), "GENCODE_46", [fasta, other])
        self.assertEqual(result["checked"], [str(fasta)])
        self.assertEqual(result["without_manifest"], [str(other)])


if __name__ == "__main__":
    unittest.main()
