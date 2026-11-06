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
from proteogenomic.splice_cli import parse_rmats_args, parse_suppa_args
from proteogenomic.fusion_cli import parse_arguments as parse_fusion_args
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
    def test_publication_policy_is_the_default_and_explicit_false_survives(self):
        common = ["--gtf_db", "a.db", "--genome", "g.fa", "--annotation_release", "G46", "--organism", "human"]
        splice = [*common, "--out_prot_fa", "out.fa"]
        rmats, _ = parse_rmats_args([*splice, "--se_files", "SE.txt"])
        self.assertTrue(rmats.quantms_conservative)
        self.assertTrue(rmats.rmats_conservative_event_filter)
        suppa, _ = parse_suppa_args([*splice, "--event_files", "e.ioe"])
        self.assertTrue(suppa.quantms_conservative)
        fusion = parse_fusion_args([*common, "--fusioninspector", "f.tsv"])
        self.assertTrue(fusion.quantms_conservative)
        explicit, _ = parse_rmats_args([*splice, "--se_files", "SE.txt", "--no-quantms_conservative",
                                        "--no-rmats_conservative_event_filter", "--no-exclude_incomplete_cds"])
        self.assertFalse(explicit.quantms_conservative)
        self.assertFalse(explicit.rmats_conservative_event_filter)
        self.assertFalse(explicit.exclude_incomplete_cds)

    def test_rescue_tiers_derive_separate_outputs(self):
        document = {"suppa": {"out_prot_fa": "results/events.fasta", "allow_alt_start": True, "allow_longest_orf": True}}
        values = resolved_step(document, "suppa")
        self.assertEqual(Path(values["out_alt_start_prot_fa"]), Path("results/events.alternative_start.fasta"))
        self.assertEqual(Path(values["out_exploratory_orf_fa"]), Path("results/events.exploratory_orf.fasta"))
        tokens = build_step_arguments({"rmats": {"quantms_conservative": False}}, "rmats")
        self.assertIn("--no-quantms_conservative", tokens)

    def test_non_publication_profiles_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.toml"
            path.write_text('[workflow]\nprofile = "exploratory"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Only the publication policy"):
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
        document = {"workflow": {"output_dir": "release"}, "rmats": {"min_fdr": 0.01}}
        stream = io.StringIO()
        with redirect_stdout(stream):
            explain(document, ["rmats"])
        rendered = stream.getvalue()
        self.assertIn("min_fdr = 0.01  # configuration", rendered)
        self.assertIn("# output-directory convention", rendered)

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
            from proteogenomic_workflow import _output_fingerprint
            state.parent.mkdir(parents=True)
            # A success record must also fingerprint the outputs it vouches for.
            state.write_text(json.dumps({**_manifest("report", values, digest),
                                         "output_sha256": _output_fingerprint("report", values)}), encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream): self.assertEqual(main([str(config)]), 0)
            self.assertIn("SKIP report", stream.getvalue())
            source.write_text("caller\tframe_status\nrmats\tFRAMESHIFT\n", encoding="utf-8")
            with redirect_stdout(stream): self.assertEqual(main([str(config), "--dry-run"]), 0)
            self.assertIn("release_report", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
