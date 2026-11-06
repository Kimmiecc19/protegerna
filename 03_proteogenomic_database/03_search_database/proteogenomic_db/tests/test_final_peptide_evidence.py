from pathlib import Path
import unittest

from merge_proteogenomic_database import (
    ParsedRecord, ProteinFilterConfig, SequenceAggregate,
    final_database_peptide_rows, sequence_hashes,
)


def aggregate(sequence, source, record_id):
    md5, sha = sequence_hashes(sequence)
    record = ParsedRecord(
        input_file=str(Path("input.fa")), original_id=record_id,
        original_description=record_id, sequence=sequence,
        sequence_md5=md5, sequence_sha256=sha, source=source,
        record_type="protein",
    )
    value = SequenceAggregate(sequence, md5, sha)
    value.add(record)
    return value


class FinalPeptideEvidenceTests(unittest.TestCase):
    def test_exact_and_il_equivalent_uniqueness_are_recomputed(self):
        left = aggregate("MPEPTIDEKAAAAAAK", "rmats", "left")
        right = aggregate("MPEPTLDEKCCCCCCK", "reference", "right")
        config = ProteinFilterConfig({"protein"}, 6, None, "warn", 5, 40, 0)
        rows = final_database_peptide_rows(
            [left, right], {left.sequence_sha256: "P1", right.sequence_sha256: "P2"}, config
        )
        left_row = next(row for row in rows if row["sequence_id"] == "P1" and "PEPTIDE" in row["peptide_sequence"])
        self.assertTrue(left_row["unique_complete_target_exact"])
        self.assertFalse(left_row["unique_complete_target_il_equivalent"])
        self.assertIn("distinguishing_fragment_ion_count", left_row)


if __name__ == "__main__":
    unittest.main()
