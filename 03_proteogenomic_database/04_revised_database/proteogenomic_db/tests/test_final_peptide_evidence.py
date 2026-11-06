from collections import Counter
from pathlib import Path
import random
import unittest

from proteogenomic.merge_peptide_evidence import (
    _fragment_labels, distinguishing_fragment_counts, iter_final_database_peptide_rows,
)

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
        self.assertEqual(list(iter_final_database_peptide_rows(
            [left, right], {left.sequence_sha256: "P1", right.sequence_sha256: "P2"}, config)), rows)


def reference_fragment_counts(peptides):
    """Original definition: count each peptide's b/y labels held by no other peptide."""
    labels = {peptide: _fragment_labels(peptide) for peptide in set(peptides)}
    owners = Counter(label for fragments in labels.values() for label in fragments)
    return {peptide: sum(owners[label] == 1 for label in fragments) for peptide, fragments in labels.items()}


class FragmentCountEquivalenceTests(unittest.TestCase):
    def test_edge_cases_match_reference_definition(self):
        for peptides in (["A"], ["AB", "ABC"], ["ABC", "AB", "A"], ["XAB", "YAB", "AB"],
                         ["PEPTIDEK", "PEPTLDEK", "PEPTIDE", "EPTIDEK"], ["AA", "AAA", "AAAA"]):
            self.assertEqual(distinguishing_fragment_counts(peptides), reference_fragment_counts(peptides), peptides)

    def test_random_sets_match_reference_definition(self):
        rng = random.Random(20261012)
        for _ in range(500):
            alphabet = rng.choice(["AB", "ILK", "ACDEFGHIK"])
            peptides = {"".join(rng.choice(alphabet) for _ in range(rng.randint(1, 8)))
                        for _ in range(rng.randint(1, 30))}
            self.assertEqual(distinguishing_fragment_counts(peptides), reference_fragment_counts(peptides))


if __name__ == "__main__":
    unittest.main()
