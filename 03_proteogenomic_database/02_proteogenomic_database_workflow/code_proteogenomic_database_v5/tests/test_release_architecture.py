import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from proteogenomic.release_validation import MergeInputContract
from merge_proteogenomic_database import ParsedRecord, aggregate_exact_sequences
from proteogenomic.pipeline_config import PipelineConfig
from proteogenomic.proteogenomic_models import (
    BreakpointResolution, DatabaseRecord, FusionCandidate, ProteinMapping,
    SpliceConsequence, TranslationResult,
)
from proteogenomic.release_validation import validate_gencode_concordance_summary
from validate_gencode_translation import load_reference
from proteogenomic.splice_translation import (
    mask_selenocysteine_stops_for_consequence, should_include_protein_in_fasta,
    translate_cds_for_model,
)


class ReleaseArchitectureTests(unittest.TestCase):
    def test_annotation_aware_translation_rules(self):
        nuclear = {"chrom": "chr1", "strand": "+", "cds": [(1, 9, 0)], "non_atg_start": True}
        self.assertEqual(translate_cds_for_model("GTGAAATAA", nuclear), "MK")
        mitochondrial = {"chrom": "chrM", "strand": "+", "cds": [(1, 9, 0)]}
        # ATT is isoleucine internally under table 2 but methionine when used
        # as an annotated mitochondrial initiation codon.
        self.assertEqual(translate_cds_for_model("ATTTGATAA", mitochondrial), "MW")
        selenoprotein = {
            "chrom": "chr1", "strand": "+", "cds": [(1, 9, 0)],
            "selenocysteine_intervals": [(4, 6)],
        }
        self.assertEqual(translate_cds_for_model("ATGTGATAA", selenoprotein), "MU")
        self.assertEqual(
            mask_selenocysteine_stops_for_consequence("ATGTGATAA", selenoprotein),
            "ATGTGCTAA",
        )

    def test_readthrough_is_audited_and_excluded(self):
        class Policy:
            exclude_incomplete_cds = True
        include, reasons = should_include_protein_in_fasta(
            {"cds_completeness": "complete", "stop_codon_readthrough": True}, Policy()
        )
        self.assertFalse(include)
        self.assertIn("readthrough", reasons)

    def test_gencode_validator_rejects_metadata_table_as_fasta(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gencode.v46.metadata.SwissProt"
            path.write_text("ENST000001\tP12345\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pc_translations FASTA"):
                load_reference(path)

    def test_validated_domain_records_serialize_only_explicitly(self):
        breakpoint = BreakpointResolution(10, 12, 4, "snapped_exon_boundary", 2)
        translation = TranslationResult("ATGAAA", "MK", "INFRAME", "annotated_start")
        candidate = FusionCandidate("S1", "A-B", "ENST1", "ENST2", breakpoint, breakpoint, translation)
        self.assertEqual(candidate.to_dict()["translation"]["protein_sequence"], "MK")
        self.assertEqual(SpliceConsequence(
            6, 6, 0, "INFRAME", False, False, True, None, None,
            False, "no_stop", None, None,
        ).altered_cds_len, 6)
        digest = hashlib.sha256(b"MK").hexdigest()
        self.assertEqual(ProteinMapping("P1", digest, "rmats").sequence_sha256, digest)
        self.assertEqual(DatabaseRecord("P1", "mk*", "rmats", "protein").sequence, "MK")
        with self.assertRaises(ValueError):
            DatabaseRecord("P1", "", "rmats", "protein")

    def test_pipeline_config_is_an_immutable_namespace_replacement(self):
        config = PipelineConfig({"workers": 2})
        self.assertEqual(config.workers, 2)
        with self.assertRaises(TypeError):
            config.values["workers"] = 3

    def test_merge_contract_rejects_incomplete_producer_header(self):
        with self.assertRaisesRegex(ValueError, "missing:event_id"):
            MergeInputContract().validate({
                "source": "rmats", "record_type": "protein", "record_id": "P1",
                "event_type": "SE", "annotation_release": "GENCODE_46",
                "database_output_tier": "primary",
            }, "rmats")

    def test_gencode_gate_requires_all_strata_and_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            coverage = {name: True for name in (
                "positive_strand", "negative_strand", "partial_cds",
                "multi_exon_cds", "nonzero_leading_phase",
            )}
            path.write_text(json.dumps({"total": 5, "required_coverage": coverage,
                                        "mismatch_rate": 0.0, "max_mismatch_rate": 0.0}))
            self.assertEqual(validate_gencode_concordance_summary(path)["total"], 5)
            coverage["negative_strand"] = False
            path.write_text(json.dumps({"total": 5, "required_coverage": coverage,
                                        "mismatch_rate": 0.0, "max_mismatch_rate": 0.0}))
            with self.assertRaises(RuntimeError):
                validate_gencode_concordance_summary(path)

    def test_exact_sequence_aggregation_preserves_all_provenance(self):
        digest = hashlib.sha256(b"MPEPTIDEK").hexdigest()
        records = []
        for source, event, transcript, sample in (
            ("rmats", "E1", "ENST1", "S1"),
            ("suppa", "E2", "ENST2", "S2"),
            ("fusioninspector", "F1", "ENST3", "S3"),
        ):
            records.append(ParsedRecord(
                input_file=f"{source}.fa", original_id=event, original_description=event,
                sequence="MPEPTIDEK", sequence_md5="x", sequence_sha256=digest,
                source=source, record_type="protein", transcripts={transcript},
                event_ids={event}, callers={source}, sample_ids={sample},
                metadata={"sample_id": sample, "batch": f"B{sample[-1]}", "condition": "CASE"},
            ))
        aggregate = aggregate_exact_sequences(records)["MPEPTIDEK"]
        self.assertEqual(aggregate.sources, {"rmats", "suppa", "fusioninspector"})
        self.assertEqual(aggregate.event_ids, {"E1", "E2", "F1"})
        self.assertEqual(aggregate.transcripts, {"ENST1", "ENST2", "ENST3"})
        self.assertEqual(aggregate.sample_ids, {"S1", "S2", "S3"})
        self.assertEqual(len(aggregate.records), 3)


if __name__ == "__main__":
    unittest.main()
