import tempfile
import unittest
from pathlib import Path

from release_report import summarize


class ReleaseReportTests(unittest.TestCase):
    def test_summary_stratifies_biology_evidence_and_stable_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.tsv"
            path.write_text(
                "caller\ttranscript_selection_ambiguous\tframe_status\tnmd_predicted\t"
                "n_eligible_tryptic_peptides\texclusion_reason_codes\n"
                "rmats\ttrue\tFRAMESHIFT\ttrue\tNA\tPGDB_EXCL_NMD_PREDICTED\n"
                "rmats\tfalse\tINFRAME\tfalse\t2\tNA\n",
                encoding="utf-8",
            )
            summary = summarize([path])["rmats"]
            self.assertEqual(summary["records"], 2)
            self.assertEqual(summary["transcript_ambiguous"], 1)
            self.assertEqual(summary["frame:FRAMESHIFT"], 1)
            self.assertEqual(summary["nmd_predicted"], 1)
            self.assertEqual(summary["peptide_evidence"], 1)
            self.assertEqual(summary["exclusion:PGDB_EXCL_NMD_PREDICTED"], 1)
