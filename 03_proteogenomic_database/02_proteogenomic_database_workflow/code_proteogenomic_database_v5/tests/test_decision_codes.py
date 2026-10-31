import json
import unittest

from proteogenomic.audit import audit_fields, exclusion_code


class DecisionCodeTests(unittest.TestCase):
    def test_stable_code_and_observation_policy_separation(self):
        self.assertEqual(exclusion_code("nmd_predicted"), "PGDB_EXCL_NMD_PREDICTED")
        fields = audit_fields({
            "frame_status": "FRAMESHIFT", "nmd_predicted": True,
            "protein_in_fasta": False, "fasta_exclusion_reasons": "nmd_predicted",
        })
        observations = json.loads(fields["biological_observations_json"])
        decisions = json.loads(fields["policy_decisions_json"])
        self.assertEqual(observations["frame_status"], "FRAMESHIFT")
        self.assertNotIn("protein_in_fasta", observations)
        self.assertFalse(decisions["protein_in_fasta"])
        self.assertNotIn("frame_status", decisions)
