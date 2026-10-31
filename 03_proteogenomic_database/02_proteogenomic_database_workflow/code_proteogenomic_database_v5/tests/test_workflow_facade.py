import tempfile
import unittest
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from proteogenomic_workflow import (
    _hash_json, _manifest, build_step_arguments, explain, load_workflow, main,
    resolved_step, selected_steps, run_logged_command,
)
from proteogenomic.workflow_architecture import WORKFLOW_STAGES, implementations_for


class WorkflowFacadeTests(unittest.TestCase):
    def test_stage_log_captures_both_streams_failure_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "logs" / "stage_02_suppa.log"
            command = [sys.executable, "-u", "-c",
                       "import sys; print('PSI loaded'); print('warning example', file=sys.stderr); sys.exit(3)"]
            options = dict(stage=WORKFLOW_STAGES[1], step="suppa",
                           values={"psi_files": ["batch1.psi"]})
            terminal = io.StringIO()
            with redirect_stdout(terminal):
                self.assertEqual(run_logged_command(command, path, **options), 3)
                self.assertEqual(run_logged_command(command, path, skip=True, **options), 0)
            saved = path.read_text(encoding="utf-8")
            self.assertIn("PSI loaded", terminal.getvalue())
            self.assertIn("warning example", terminal.getvalue())
            for expected in ("PSI loaded", "warning example", "exit_status=3", "batch1.psi",
                             "Working directory:", "Command:", "SKIPPED:"):
                self.assertIn(expected, saved)
            self.assertEqual(saved.count("STAGE 2:"), 2)

    def test_public_architecture_has_six_stages(self):
        self.assertEqual([stage.number for stage in WORKFLOW_STAGES], list(range(1, 7)))
        self.assertEqual(
            implementations_for(["reconstruct_proteins"]),
            ["rmats", "suppa", "fusion"],
        )
        self.assertEqual(
            implementations_for(["merge_proteins", "filter_for_dia_suitability"]),
            ["merge"],
        )
    def test_policy_values_are_read_from_toml_without_profile_defaults(self):
        document = {"rmats": {"quantms_conservative": True,
                              "rmats_conservative_event_filter": True,
                              "allow_alt_start": True,
                              "out_alt_start_prot_fa": "results/alt.fasta"}}
        values = resolved_step(document, "rmats")
        self.assertEqual(values["quantms_conservative"], True)
        self.assertEqual(values["rmats_conservative_event_filter"], True)
        self.assertEqual(values["allow_alt_start"], True)
        self.assertEqual(values["out_alt_start_prot_fa"], "results/alt.fasta")
        self.assertNotIn("allow_longest_orf", values)

    def test_profile_setting_is_rejected_as_unknown_workflow_option(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.toml"
            path.write_text('[workflow]\nprofile = "conservative"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"Unknown workflow option \[workflow\]\.profile"):
                load_workflow(path)

    def test_common_values_are_routed_only_to_compatible_steps(self):
        document = {
            "common": {"gtf_db": "annotation.db", "annotation_release": "G46", "organism": "human"},
            "merge": {"inputs": ["events.fa"], "gencode_concordance_summary": "gate.json"},
        }
        tokens = build_step_arguments(document, "merge")
        self.assertNotIn("--gtf_db", tokens)
        self.assertIn("--annotation_release", tokens)

    def test_disabled_steps_are_not_selected(self):
        document = {"fusion": {"enabled": True}, "rmats": {"enabled": False}}
        self.assertEqual(selected_steps(document, []), ["fusion"])

    def test_unknown_top_level_section_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.toml"
            path.write_text("[typo]\nvalue = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown top-level"):
                load_workflow(path)

    def test_misspelled_step_key_reports_exact_section_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.toml"
            path.write_text("[rmats]\nmax_fdrr = 0.05\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"\[rmats\]\.max_fdrr.*max_fdr"):
                load_workflow(path)

    def test_output_directory_supplies_step_filenames(self):
        document = {"workflow": {"output_dir": "release"}, "rmats": {}}
        values = resolved_step(document, "rmats")
        self.assertEqual(Path(values["out_prot_fa"]), Path("release/rmats.primary.fasta"))
        self.assertEqual(Path(values["out_consequence_tsv"]), Path("release/rmats.consequences.tsv"))

    def test_explain_identifies_configuration_sources(self):
        document = {"rmats": {"min_fdr": 0.01, "quantms_conservative": True}}
        stream = io.StringIO()
        with redirect_stdout(stream):
            explain(document, ["rmats"])
        rendered = stream.getvalue()
        self.assertIn("quantms_conservative = True  # configuration", rendered)
        self.assertIn("min_fdr = 0.01  # configuration", rendered)

    def test_resume_requires_matching_config_inputs_and_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "audit.tsv"
            source.write_text("caller\tframe_status\nrmats\tINFRAME\n", encoding="utf-8")
            config = root / "workflow.toml"
            config.write_text(
                f'[workflow]\noutput_dir = "{(root / "out").as_posix()}"\nresume = true\n'
                f'[report]\ninputs = ["{source.as_posix()}"]\n', encoding="utf-8",
            )
            document = load_workflow(config); values = resolved_step(document, "report")
            for key in ("out_tsv", "out_json"):
                Path(values[key]).parent.mkdir(parents=True, exist_ok=True); Path(values[key]).write_text("done", encoding="utf-8")
            digest = _hash_json({"step":"report","values":values})
            state = root / "out" / ".proteogenomic_state" / "report.json"
            state.parent.mkdir(parents=True); state.write_text(json.dumps(_manifest("report", values, digest)), encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream): self.assertEqual(main([str(config)]), 0)
            self.assertIn("SKIP report", stream.getvalue())
            source.write_text("caller\tframe_status\nrmats\tFRAMESHIFT\n", encoding="utf-8")
            with redirect_stdout(stream): self.assertEqual(main([str(config), "--dry-run"]), 0)
            self.assertIn("release_report", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
