import contextlib
import tempfile
import unittest
from pathlib import Path

import proteogenomic_fasta_qc as facade
from proteogenomic import qc_calculations
from proteogenomic import qc_io
from proteogenomic import qc_pipeline
from proteogenomic import qc_reporting


REPO_ROOT = Path(__file__).resolve().parents[1]


class QCGoldenEquivalenceTests(unittest.TestCase):
    # Relative to REPO_ROOT on purpose: the golden outputs record this input path.
    fixture = Path("tests/fixtures/qc_equivalence")
    outputs = (
        "golden.filtered_min6aa.fasta",
        "golden.filtered_fasta_exclusions.tsv",
        "golden.header_metadata.tsv",
        "golden.sequence_qc.tsv",
        "golden.qc_summary.tsv",
    )

    def test_compatibility_facade_exports_refactored_implementations(self):
        self.assertIs(facade.sequence_qc, qc_calculations.sequence_qc)
        self.assertIs(facade.parse_fasta, qc_io.parse_fasta)
        self.assertIs(facade.write_filtered_fasta, qc_reporting.write_filtered_fasta)
        self.assertIs(facade.main, qc_pipeline.main)

    def test_exact_fasta_header_exclusion_and_audit_equivalence(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(REPO_ROOT):
            qc_pipeline.main([
                "--fasta", str(self.fixture / "input.fasta"),
                "--labels", "synthetic",
                "--outdir", directory,
                "--prefix", "golden",
                "--write_filtered_fasta",
                "--min_protein_length", "6",
            ])
            for filename in self.outputs:
                expected = (self.fixture / "expected" / filename).read_bytes()
                observed = (Path(directory) / filename).read_bytes()
                self.assertEqual(observed, expected, filename)


if __name__ == "__main__":
    unittest.main()
