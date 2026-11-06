import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from proteogenomic.splice_translation import write_run_manifest


class RunManifestTests(unittest.TestCase):
    def test_manifest_has_version_configuration_and_input_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "input.tsv"
            source.write_text("event\nSE\n", encoding="utf-8")
            output = root / "events.fasta"
            manifest = Path(write_run_manifest(Namespace(event_files=[str(source)], out_prot_fa=str(output)), output, "producer.py"))
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "pgdb-producer-run-v1")
            self.assertTrue(payload["software_version"])
            self.assertEqual(len(payload["configuration_sha256"]), 64)
            self.assertEqual(len(payload["input_sha256"][str(source)]), 64)
