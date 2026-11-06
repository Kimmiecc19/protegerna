"""Regression tests for the 2026-10-12 review fixes (packaging, resume, section selection)."""
import tempfile
import tomllib
import unittest
from pathlib import Path

import proteogenomic_workflow as workflow

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.setuptools = self.project["tool"]["setuptools"]
        self.source = ROOT / self.setuptools["package-dir"][""]

    def test_declared_package_and_modules_exist(self):
        for package in self.setuptools["packages"]:
            self.assertTrue((self.source / package / "__init__.py").is_file(), package)
        for module in self.setuptools["py-modules"]:
            self.assertTrue((self.source / f"{module}.py").is_file(), module)

    def test_every_workflow_step_module_is_distributed(self):
        distributed = set(self.setuptools["py-modules"]) | set(self.setuptools["packages"])
        for module, _factory in workflow.PARSERS.values():
            self.assertIn(module.split(".")[0], distributed, module)
        for module in workflow.STEP_MODULES.values():
            self.assertIn(module, distributed, module)

    def test_console_scripts_point_to_distributed_modules(self):
        for target in self.project["project"]["scripts"].values():
            self.assertIn(target.split(":")[0], self.setuptools["py-modules"])


class ResumeTests(unittest.TestCase):
    def test_rmats_event_metadata_contents_change_the_resume_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            meta, table = Path(directory, "meta.json"), Path(directory, "SE.txt")
            table.write_text("x", encoding="utf-8")
            meta.write_text('{"a": {"batch": "b1"}}', encoding="utf-8")
            values = {"se_files": [str(table)], "event_metadata": str(meta)}
            before = workflow._manifest("rmats", values, "hash")
            meta.write_text('{"a": {"batch": "b2"}}', encoding="utf-8")
            self.assertNotEqual(before, workflow._manifest("rmats", values, "hash"))

    def test_empty_qc_directory_is_not_a_completed_run(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory, "qc")
            out.mkdir()
            values = {"outdir": str(out), "prefix": "db"}
            self.assertFalse(workflow._outputs_exist("qc", values))
            for name in workflow.QC_REPORTS:
                Path(out, f"db.{name}.tsv").write_text("x", encoding="utf-8")
            self.assertTrue(workflow._outputs_exist("qc", values))
            values["reference_proteome"] = "ref.fa"  # requests the peptide uniqueness report too
            self.assertFalse(workflow._outputs_exist("qc", values))

    def test_requested_fusion_tables_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            names = {key: str(Path(directory, key)) for key in (
                "filtered_protein_fasta", "biological_interpretation_tsv", "out_sequence_sample_tsv")}
            for key in ("filtered_protein_fasta", "biological_interpretation_tsv"):
                Path(names[key]).write_text("x", encoding="utf-8")
            self.assertFalse(workflow._outputs_exist("fusion", names))
            Path(names["out_sequence_sample_tsv"]).write_text("x", encoding="utf-8")
            self.assertTrue(workflow._outputs_exist("fusion", names))

    def test_peptide_table_required_only_when_digestion_is_on(self):
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory, "fusion.fasta")
            fasta.write_text("x", encoding="utf-8")
            values = {"filtered_protein_fasta": str(fasta), "digested_peptide_tsv": str(Path(directory, "p.tsv"))}
            self.assertTrue(workflow._outputs_exist("fusion", dict(values, digest_trypsin=False)))
            self.assertFalse(workflow._outputs_exist("fusion", dict(values, digest_trypsin=True)))


class SectionSelectionTests(unittest.TestCase):
    def test_present_empty_section_runs_unless_disabled(self):
        self.assertEqual(workflow.selected_steps({"qc": {}}, []), ["qc"])
        self.assertEqual(workflow.selected_steps({"qc": {"enabled": False}}, []), [])
        self.assertEqual(workflow.selected_steps({"merge": {}, "qc": {}}, []), ["merge", "qc"])

    def test_explicit_step_is_filtered_like_stage(self):
        import contextlib, io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workflow.selected_steps({"qc": {}}, ["rmats"]), [])
            self.assertEqual(workflow.selected_steps({"rmats": {"enabled": False}}, ["rmats"]), [])
            self.assertEqual(workflow.selected_steps({"rmats": {}, "qc": {}}, ["rmats", "rmats"]), ["rmats"])

    def test_explicit_disabled_step_aborts_main(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory, "workflow.toml")
            config.write_text("[rmats]\nenabled = false\n", encoding="utf-8")
            import contextlib, io
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ValueError):
                workflow.main([str(config), "--step", "rmats", "--dry-run"])


class RemovedCodeTests(unittest.TestCase):
    def test_broken_unused_merge_into_was_removed(self):
        from proteogenomic.proteogenomic_models import SpliceProteinResult
        self.assertFalse(hasattr(SpliceProteinResult, "merge_into"))


if __name__ == "__main__":
    unittest.main()
