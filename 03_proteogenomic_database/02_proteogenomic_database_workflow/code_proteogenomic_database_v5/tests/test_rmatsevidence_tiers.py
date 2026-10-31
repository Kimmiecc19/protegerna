import unittest
from argparse import Namespace

from proteogenomic.rmats_evidence import finalise_primary_event_peptide_evidence


class RmatsEvidenceTierTests(unittest.TestCase):
    def test_primary_dia_rows_rebuild_the_primary_fasta(self):
        args = Namespace(
            max_missed_cleavages=0,
            min_database_peptide_length=2,
            max_database_peptide_length=40,
            require_unique_event_peptide=False,
            include_failed_filter_proteins=False,
            organism="Homo_sapiens",
            annotation_release="GENCODE_46",
        )
        rows = [{
            "protein_sequence": "MPEPTIDEK", "variant": "included",
            "database_output_tier": "primary_dia", "protein_in_fasta": True,
            "source_file": "SE.MATS.JC.txt", "event_type": "SE", "event_id": "1",
        }]
        proteins = {"stale": {"mappings": []}}
        finalise_primary_event_peptide_evidence(rows, proteins, args)
        self.assertIn("MPEPTIDEK", proteins)
        self.assertNotIn("stale", proteins)
        self.assertEqual(
            proteins["MPEPTIDEK"]["mappings"][0]["database_output_tier"],
            "primary_dia",
        )


if __name__ == "__main__":
    unittest.main()
