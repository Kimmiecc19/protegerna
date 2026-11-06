"""Regressions for resume integrity, PSI sample identity and release binding (2026-10-13 review)."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import proteogenomic_workflow as workflow
from proteogenomic.release_validation import check_concordance_binding
from proteogenomic.suppa_psi import evaluate_psi_event, load_psi_files


def _report_config(root, resume=True):
    source = root / "audit.tsv"
    source.write_text("caller\tframe_status\nrmats\tINFRAME\n", encoding="utf-8")
    config = root / "workflow.toml"
    config.write_text(
        f'[workflow]\noutput_dir = "{(root / "out").as_posix()}"\nresume = {str(resume).lower()}\n'
        f'[report]\ninputs = ["{source.as_posix()}"]\n', encoding="utf-8",
    )
    return config


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = workflow.main(argv)
    return code, out.getvalue()


class ResumeIntegrityTests(unittest.TestCase):
    def test_failed_rerun_is_never_resumed_from_old_success_state(self):
        with tempfile.TemporaryDirectory() as directory:
            config = _report_config(Path(directory), resume=False)
            code, _ = _run([str(config)])
            self.assertEqual(code, 0)
            state = Path(directory) / "out" / ".proteogenomic_state" / "report.json"
            out_tsv = Path(directory) / "out" / "release_report.tsv"
            self.assertTrue(state.is_file())

            def crash(command, log_path, **kwargs):  # partial overwrite, then failure
                out_tsv.write_text("partial", encoding="utf-8")
                return 1

            with mock.patch.object(workflow, "run_logged_command", side_effect=crash):
                code, _ = _run([str(config), "--step", "report"])
            self.assertEqual(code, 1)
            self.assertFalse(state.exists())                       # success record invalidated
            self.assertFalse(out_tsv.exists())                     # partial output not left in place
            self.assertTrue(out_tsv.with_name(out_tsv.name + ".incomplete").is_file())

            code, output = _run([str(config), "--resume"])        # resume must re-run, not skip
            self.assertEqual(code, 0)
            self.assertNotIn("SKIP report", output)
            self.assertNotEqual(out_tsv.read_text(encoding="utf-8"), "partial")

    def test_modified_output_invalidates_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            config = _report_config(Path(directory))
            self.assertEqual(_run([str(config)])[0], 0)
            self.assertIn("SKIP report", _run([str(config)])[1])
            (Path(directory) / "out" / "release_report.tsv").write_text("edited", encoding="utf-8")
            self.assertNotIn("SKIP report", _run([str(config)])[1])

    def test_merge_fingerprint_includes_producer_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "rmats.primary.fasta"
            fasta.write_text(">a\nMPEPTIDEK\n", encoding="utf-8")
            values = {"inputs": [str(fasta)]}
            absent = workflow._input_fingerprint("merge", values)
            sidecar = Path(f"{fasta}.run_config.json")
            sidecar.write_text('{"arguments": {}}', encoding="utf-8")
            first = workflow._input_fingerprint("merge", values)
            sidecar.write_text('{"arguments": {"genome": "other.fa"}}', encoding="utf-8")
            second = workflow._input_fingerprint("merge", values)
            self.assertIsNone(absent[str(sidecar)])
            self.assertNotEqual(absent, first)
            self.assertNotEqual(first, second)


class PsiSampleIdentityTests(unittest.TestCase):
    def test_duplicate_raw_sample_columns_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            psi = Path(directory) / "dup.psi"
            psi.write_text("sampleA\tsampleA\nEVENT1\t0.5\t0.6\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate sample columns"):
                load_psi_files([psi])

    def test_distinct_samples_still_count(self):
        with tempfile.TemporaryDirectory() as directory:
            psi = Path(directory) / "ok.psi"
            psi.write_text("sampleA\tsampleB\nEVENT1\t0.5\t0.6\n", encoding="utf-8")
            keep, record = evaluate_psi_event("EVENT1", load_psi_files([psi]), 0.1, 2)
            self.assertTrue(keep)
            self.assertEqual(record["psi_samples_passing"], 2)


class ReleaseBindingTests(unittest.TestCase):
    SUMMARY = {"reference": {"annotation_release": "GENCODE_46",
                             "gtf_db": {"sha256": "a" * 64}, "genome": {"sha256": "b" * 64}}}

    def _fasta_with_manifest(self, directory, manifest):
        fasta = Path(directory) / "x.fasta"
        fasta.write_text(">a\nM\n", encoding="utf-8")
        Path(f"{fasta}.run_config.json").write_text(json.dumps(manifest), encoding="utf-8")
        return fasta

    def test_manifest_without_reference_paths_is_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = self._fasta_with_manifest(directory, {"arguments": {"annotation_release": "GENCODE_46"}})
            with self.assertRaisesRegex(RuntimeError, "does not record --gtf_db"):
                check_concordance_binding(self.SUMMARY, "GENCODE_46", [fasta])

    def test_manifest_without_reference_checksums_is_not_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = self._fasta_with_manifest(directory, {
                "arguments": {"annotation_release": "GENCODE_46", "gtf_db": "g.db", "genome": "g.fa"},
                "input_sha256": {"g.db": "a" * 64},
            })
            with self.assertRaisesRegex(RuntimeError, "no checksum for genome"):
                check_concordance_binding(self.SUMMARY, "GENCODE_46", [fasta])

    def test_complete_matching_manifest_is_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = self._fasta_with_manifest(directory, {
                "arguments": {"annotation_release": "GENCODE_46", "gtf_db": "g.db", "genome": "g.fa"},
                "input_sha256": {"g.db": "a" * 64, "g.fa": "b" * 64},
            })
            self.assertEqual(check_concordance_binding(self.SUMMARY, "GENCODE_46", [fasta])["checked"], [str(fasta)])


if __name__ == "__main__":
    unittest.main()


class ProducerManifestTimingTests(unittest.TestCase):
    def test_manifest_is_published_only_after_success(self):
        from types import SimpleNamespace
        from proteogenomic.splice_translation import prepare_run_manifest, publish_run_manifest
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "rmats.primary.fasta"
            sidecar = Path(f"{fasta}.run_config.json")
            sidecar.write_text("stale", encoding="utf-8")
            args = SimpleNamespace(out_prot_fa=str(fasta), annotation_release="GENCODE_46")
            manifest = prepare_run_manifest(args, fasta, "rmatstoprotein.py")
            self.assertFalse(sidecar.exists())          # stale manifest removed at start
            args.sequence_cache = object()               # run-time attributes are not recorded
            publish_run_manifest(manifest)
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertNotIn("sequence_cache", payload["arguments"])

    def test_merge_can_require_producer_manifests(self):
        import merge_proteogenomic_database as merge
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fasta = root / "rmats.primary.fasta"
            fasta.write_text(">a\nMPEPTIDEKAAAAAR\n", encoding="utf-8")
            summary = root / "summary.json"
            summary.write_text(json.dumps({
                "total": 1, "mismatch_rate": 0, "max_mismatch_rate": 0, "unexplained_complete_mismatch_count": 0,
                "required_coverage": {k: True for k in ("positive_strand", "negative_strand", "partial_cds",
                                                         "multi_exon_cds", "nonzero_leading_phase")},
                "reference": ReleaseBindingTests.SUMMARY["reference"],
            }), encoding="utf-8")
            argv = ["--gencode_concordance_summary", str(summary), "--inputs", str(fasta),
                    "--annotation_release", "GENCODE_46", "--organism", "Homo_sapiens",
                    "--out_fasta", str(root / "db.fasta"), "--out_metadata", str(root / "m.tsv"),
                    "--out_mapping", str(root / "map.tsv"), "--out_peptide_evidence", str(root / "p.tsv"),
                    "--out_biological_interpretation", str(root / "b.tsv"),
                    "--out_summary_tsv", str(root / "s.tsv"), "--out_summary_json", str(root / "s.json")]
            with redirect_stderr(io.StringIO()):
                self.assertEqual(merge.main(argv + ["--require_producer_manifests"]), 1)
                self.assertFalse((root / "db.fasta").exists())


class PsiValueValidationTests(unittest.TestCase):
    def _load(self, body):
        with tempfile.TemporaryDirectory() as directory:
            psi = Path(directory) / "m.psi"
            psi.write_text(body, encoding="utf-8")
            return load_psi_files([psi])

    def test_malformed_value_is_an_error_not_missing(self):
        with self.assertRaisesRegex(ValueError, r"non-numeric value\(s\).*EVENT1 sample S2 = '0..5'"):
            self._load("S1\tS2\tS3\nEVENT1\t0.5\t0..5\t0.7\n")

    def test_out_of_range_and_infinite_values_are_errors(self):
        for bad in ("1.2", "-0.1", "inf"):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "outside 0-1"):
                self._load(f"S1\tS2\nEVENT1\t0.5\t{bad}\n")

    def test_declared_missing_values_stay_missing(self):
        lookup = self._load("S1\tS2\tS3\tS4\nEVENT1\tnan\tNA\t\t1\nEVENT2\t0\t0.25\t1e-1\tNaN\n")
        self.assertEqual(lookup["EVENT1"]["values"], [1.0])
        self.assertEqual(sorted(lookup["EVENT2"]["values"]), [0.0, 0.1, 0.25])

    def test_many_sample_columns_are_checked_quickly(self):
        import time
        names = [f"S{i}" for i in range(20000)]
        started = time.perf_counter()
        lookup = self._load("\t".join(names) + "\nEVENT1\t" + "\t".join(["0.5"] * len(names)) + "\n")
        self.assertEqual(lookup["EVENT1"]["n_observed"], len(names))
        self.assertLess(time.perf_counter() - started, 20)


class ChecksumCacheTests(unittest.TestCase):
    def test_same_size_same_mtime_replacement_is_rehashed(self):
        import os
        from proteogenomic.provenance import sha256_file
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.bin"
            path.write_bytes(b"AAAA")
            first = sha256_file(path)
            stat = path.stat()
            replacement = Path(directory) / "new.bin"
            replacement.write_bytes(b"BBBB")
            os.utime(replacement, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            os.replace(replacement, path)                # same size, same mtime, new file
            self.assertEqual(path.stat().st_mtime_ns, stat.st_mtime_ns)
            self.assertNotEqual(sha256_file(path), first)

    def test_uncached_hash_always_rereads(self):
        from proteogenomic.provenance import sha256_file
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.bin"
            path.write_bytes(b"AAAA")
            self.assertEqual(sha256_file(path, use_cache=False), hashlib.sha256(b"AAAA").hexdigest())
