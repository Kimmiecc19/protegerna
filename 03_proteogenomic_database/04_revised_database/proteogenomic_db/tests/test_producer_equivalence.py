import tempfile, unittest
from pathlib import Path

from proteogenomic.fusion_reporting import (
    prepare_ranking_dataframe, write_filtered_fasta_outputs,
)
from proteogenomic.splice_translation import write_consequence_tsv, write_protein_fasta


def _mapping(source):
    return {"MPEPTIDEK": {"mappings": [{
        "database_output_tier": "primary", "gene_symbol": "GENE1",
        "gene_id": "ENSG1", "tx": "ENST1",
        "event_type": "SE" if source == "rmats" else "A3",
        "event_id": "EVENT1", "variant": "alternative", "sample_id": "S1",
        "batch": "B1", "condition": "CASE", "annotation_release": "GENCODE_46",
        "organism": "Homo_sapiens", "translation_strategy": "annotated_start",
        "translation_note": "complete", "transcript_selection_rank": 1,
        "transcript_candidate_count": 2, "transcript_selection_ambiguous": False,
    }]}}


def generate(directory):
    root = Path(directory); root.mkdir(parents=True, exist_ok=True)
    write_protein_fasta(_mapping("rmats"), root / "rmats.fasta", "rmats")
    write_protein_fasta(_mapping("suppa"), root / "suppa.fasta", "suppa")
    row = {
        "source_file": "synthetic", "event_type": "SE", "event_id": "EVENT1",
        "gene_id": "ENSG1", "gene_symbol": "GENE1", "tx": "ENST1",
        "variant": "alternative", "frame_status": "FRAMESHIFT",
        "nmd_predicted": True, "protein_sequence": "MPEPTIDEK", "protein_length": 9,
        "protein_in_fasta": False, "database_output_tier": "excluded",
        "fasta_exclusion_reasons": "nmd_predicted",
    }
    write_consequence_tsv([row], root / "rmats.audit.tsv")
    write_consequence_tsv([{**row, "event_type": "A3"}], root / "suppa.audit.tsv")
    fusion = prepare_ranking_dataframe([{
        "protein_sequence": "MPEPTIDEK", "cds_sequence": "ATGCCGGAACCGACCATTGATGAAAAA",
        "fusion_name": "GENE1--GENE2", "pair_token": "F1", "gene_1_id": "ENSG1",
        "gene_2_id": "ENSG2", "donor_tid": "ENST1", "acceptor_tid": "ENST2",
        "frame_status": "INFRAME", "sample_id": "S1", "batch": "B1",
        "condition": "CASE", "annotation_release": "GENCODE_46",
        "database_output_tier": "primary",
    }])
    fusion.to_csv(root / "fusion.audit.tsv", sep="\t", index=False, lineterminator="\n")
    with (root / "fusion.cds.fasta").open("w", encoding="utf-8", newline="\n") as cds, \
         (root / "fusion.fasta").open("w", encoding="utf-8", newline="\n") as protein:
        write_filtered_fasta_outputs(fusion, cds, protein, "Homo_sapiens")

class ProducerGoldenEquivalenceTests(unittest.TestCase):
    expected=Path(__file__).resolve().parent/"fixtures"/"producer_equivalence"/"expected"
    def test_exact_producer_fastas_headers_exclusions_and_audits(self):
        with tempfile.TemporaryDirectory() as directory:
            generate(directory)
            for expected in sorted(self.expected.iterdir()):
                self.assertEqual((Path(directory)/expected.name).read_bytes(),expected.read_bytes(),expected.name)

if __name__=="__main__":unittest.main()
