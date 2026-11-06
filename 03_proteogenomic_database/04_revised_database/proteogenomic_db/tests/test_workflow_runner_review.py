"""Regressions for the 2026-10-13 workflow-runner review."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import proteogenomic_workflow as workflow


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def _run(argv, cwd=None):
    out, err = io.StringIO(), io.StringIO()
    previous = os.getcwd()
    try:
        if cwd:
            os.chdir(cwd)
        with redirect_stdout(out), redirect_stderr(err):
            code = workflow.main(argv)
    finally:
        os.chdir(previous)
    return code, out.getvalue(), err.getvalue()


class ChildProcessTests(unittest.TestCase):
    def test_steps_run_from_any_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "in.tsv", "caller\tframe_status\nrmats\tINFRAME\n")
            config = _write(root / "w.toml", '[workflow]\noutput_dir = "out"\n[report]\ninputs = ["in.tsv"]\n')
            code, _, _ = _run([str(config)], cwd=root)
            self.assertEqual(code, 0)
            self.assertTrue((root / "out" / "release_report.tsv").is_file())

    def test_child_pythonpath_starts_with_code_directory(self):
        with mock.patch.dict(os.environ, {"PYTHONPATH": "/elsewhere"}):
            parts = workflow._child_environment()["PYTHONPATH"].split(os.pathsep)
        self.assertEqual(parts, [str(workflow.CODE_DIR), "/elsewhere"])


class ExpectedOutputTests(unittest.TestCase):
    def test_junction_fasta_expected_only_when_generated(self):
        for step in ("rmats", "suppa"):
            values = {"out_prot_fa": "p.fa", "out_junc_fa": "j.fa", "psi_files": ["x"]}
            off = {str(p) for p in workflow.expected_outputs(step, values)}
            on = {str(p) for p in workflow.expected_outputs(step, {**values, "short_junction_peptides": True})}
            self.assertNotIn("j.fa", off, step)
            self.assertIn("j.fa", on, step)


class OrderingTests(unittest.TestCase):
    def test_steps_run_in_pipeline_order_whatever_the_flag_order(self):
        document = {name: {} for name in ("validate", "rmats", "merge", "benchmark", "report")}
        self.assertEqual(workflow.selected_steps(document, ["report", "rmats", "validate"]),
                         ["validate", "rmats", "report"])
        self.assertEqual(workflow.selected_steps(document, []),
                         ["validate", "rmats", "merge", "benchmark", "report"])

    def test_stage_flags_follow_pipeline_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = _write(root / "w.toml",
                            '[workflow]\noutput_dir = "out"\n[report]\ninputs = ["a.tsv"]\n'
                            '[benchmark]\nactual = "a.tsv"\ntruth = "t.tsv"\n')
            _, output, _ = _run([str(config), "--dry-run", "--stage", "generate_release",
                                 "--stage", "validate_database"], cwd=root)
            self.assertLess(output.index("benchmark_variant_reconstruction"), output.index("release_report"))


class ConfigurationTypeTests(unittest.TestCase):
    def _load(self, body):
        with tempfile.TemporaryDirectory() as directory:
            return workflow.load_workflow(_write(Path(directory) / "w.toml", body))

    def test_false_for_a_value_option_is_rejected_up_front(self):
        with self.assertRaisesRegex(TypeError, r"\[merge\]\.organism takes a value"):
            self._load('[merge]\norganism = false\n')

    def test_empty_list_for_a_required_list_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"\[merge\]\.inputs must list at least one value"):
            self._load('[merge]\ninputs = []\n')

    def test_wrong_number_type_and_choice_are_rejected(self):
        with self.assertRaisesRegex(TypeError, "expects int"):
            self._load('[rmats]\nworkers = 2.5\n')
        with self.assertRaisesRegex(ValueError, "must be one of"):
            self._load('[merge]\ninvalid_sequence_policy = "ignore"\n')
        with self.assertRaisesRegex(TypeError, "must be true or false"):
            self._load('[rmats]\nallow_alt_start = "yes"\n')

    def test_valid_shipped_configurations_load(self):
        for name in ("workflow.publication.frozen.toml", "workflow.standard.example.toml"):
            workflow.load_workflow(Path(workflow.CODE_DIR) / name)


class FailureReportTests(unittest.TestCase):
    def test_failed_validation_keeps_its_reports_but_is_not_marked_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = _write(root / "w.toml",
                            '[workflow]\noutput_dir = "out"\n[validate]\ngtf_db = "g.db"\ngenome = "g.fa"\n'
                            'gencode_protein_fasta = "p.fa"\nannotation_release = "X"\n')

            def gate_fails(command, log_path, **kwargs):
                (root / "out" / "gencode_translation_concordance.json").write_text("{}", encoding="utf-8")
                (root / "out" / "gencode_translation_concordance.tsv").write_text("x", encoding="utf-8")
                return 1

            with mock.patch.object(workflow, "run_logged_command", side_effect=gate_fails):
                code, _, err = _run([str(config)], cwd=root)
            self.assertEqual(code, 1)
            self.assertTrue((root / "out" / "gencode_translation_concordance.json").is_file())
            self.assertFalse((root / "out" / ".proteogenomic_state" / "validate.json").exists())
            self.assertIn("kept for inspection", err)


class LockTests(unittest.TestCase):
    def test_second_run_on_same_output_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "in.tsv", "caller\tframe_status\nrmats\tINFRAME\n")
            config = _write(root / "w.toml", '[workflow]\noutput_dir = "out"\n[report]\ninputs = ["in.tsv"]\n')
            lock = root / "out" / ".proteogenomic_state" / "workflow.lock"
            lock.parent.mkdir(parents=True)
            import socket
            _write(lock, f"pid={os.getpid()} host={socket.gethostname()} started=now\n")  # a live process
            with self.assertRaisesRegex(RuntimeError, "Another workflow run"):
                _run([str(config)], cwd=root)
            self.assertTrue(lock.exists())

    @unittest.skipUnless(os.name == "posix", "stale-lock recovery is POSIX-only")
    def test_lock_of_a_dead_process_is_recovered(self):
        import socket, subprocess, sys
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "in.tsv", "caller\tframe_status\nrmats\tINFRAME\n")
            config = _write(root / "w.toml", '[workflow]\noutput_dir = "out"\n[report]\ninputs = ["in.tsv"]\n')
            dead = subprocess.Popen([sys.executable, "-c", "pass"]); dead.wait()
            lock = root / "out" / ".proteogenomic_state" / "workflow.lock"
            lock.parent.mkdir(parents=True)
            _write(lock, f"pid={dead.pid} host={socket.gethostname()} started=then\n")
            code, _, _ = _run([str(config)], cwd=root)
            self.assertEqual(code, 0)
            self.assertFalse(lock.exists())            # released after the run


class FusionEmptyResultTests(unittest.TestCase):
    def test_zero_fusion_proteins_is_not_a_failure(self):
        import inspect
        from proteogenomic import fusion_pipeline
        source = inspect.getsource(fusion_pipeline.main)
        self.assertNotIn('else 1', source)
        self.assertIn("No fusion proteins passed", source)


if __name__ == "__main__":
    unittest.main()
