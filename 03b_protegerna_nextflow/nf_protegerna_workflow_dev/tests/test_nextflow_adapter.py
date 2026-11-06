import argparse
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets/proteogenomic_runtime'))
from nextflow_adapter import cli_arguments, prepare_events, STAGES
from proteogenomic.splice_cli import parse_rmats_args

class AdapterTests(unittest.TestCase):
    def test_frozen_rmats_false_overrides_publication_default(self):
        args, _ = parse_rmats_args(['--gtf_db','ref.db','--genome','ref.fa',
            '--out_prot_fa','out.fa',
            '--no-quantms_conservative','--no-exclude_incomplete_cds',
            '--annotation_release','GENCODE_46','--organism','Homo_sapiens'])
        self.assertFalse(args.quantms_conservative)
        self.assertFalse(args.exclude_incomplete_cds)
        self.assertTrue(args.rmats_conservative_event_filter)

    def test_every_config_option_is_accepted_by_actual_parser(self):
        defaults = json.loads((ROOT/'assets/resolved_publication_defaults.json').read_text())
        required = {
            'validate':dict(gtf_db='a',genome='b',gencode_protein_fasta='c'),
            'fusion':dict(gtf_db='a',genome='b',fusioninspector=['c']),
            'rmats':dict(gtf_db='a',genome='b',se_files=['c']),
            'suppa':dict(gtf_db='a',genome='b',event_files=['c']),
            'merge':dict(inputs=['a'],gencode_concordance_summary='gate.json'),
            'qc':dict(fasta=['a']),
        }
        for stage, (_, module, factory) in STAGES.items():
            with self.subTest(stage=stage):
                parser = getattr(importlib.import_module(module),factory)()
                values = defaults[stage] | required[stage]
                if stage in {'fusion','rmats','suppa','merge'}:
                    values.update(annotation_release='GENCODE_46',organism='Homo_sapiens')
                parsed = parser.parse_args(cli_arguments(parser, values))
                for key, value in values.items():
                    if value is not None:
                        actual = getattr(parsed,key)
                        self.assertEqual(str(actual) if isinstance(actual,Path) else actual, value, key)

    def test_paths_with_spaces_are_single_tokens(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--inputs',nargs='+')
        self.assertEqual(cli_arguments(parser,{'inputs':['a b.fa','c.fa']}),['--inputs','a b.fa','c.fa'])

    def test_supplied_sample_identity_survives_fusion_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                Path('upstream.tsv').write_text('header\n')
                result = prepare_events('fusion',[dict(sample='S1',batch='batch1',condition='CASE',path='original.tsv')],['upstream.tsv'])
                self.assertEqual(result['fusioninspector'],['events/batch1/S1.FusionInspector.fusions.abridged.tsv'] if os.name != 'nt' else ['events\\batch1\\S1.FusionInspector.fusions.abridged.tsv'])
                self.assertIn('S1\tbatch1\tCASE',Path('sample_metadata.tsv').read_text())
            finally:
                os.chdir(previous)

    def test_empty_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'empty.psi'
            path.touch()
            with self.assertRaisesRegex(ValueError,'Empty suppa input'):
                prepare_events('suppa',[{'path':str(path)}],[str(path)])

    def test_rmats_explicit_metadata_survives_staging(self):
        from rmatstoprotein import event_file_provenance
        path=Path('work/input/SE.MATS.JC.txt')
        row={'sample':'CASE-CTRL','batch':'cohort_alpha','condition':'case;control'}
        args=SimpleNamespace(event_metadata_lookup={str(path.resolve()):row},organism='human',annotation_release='G46')
        provenance=event_file_provenance(path,args)
        self.assertEqual(provenance['sample_id'],'NA')
        self.assertEqual(provenance['comparison'],'CASE-CTRL')
        self.assertEqual(provenance['batch'],'cohort_alpha')
        self.assertEqual(provenance['condition'],'case;control')

    def test_config_matches_v5_biological_settings(self):
        import tomllib
        frozen=tomllib.loads((ROOT/'assets/workflow.publication.v5.toml').read_text())
        defaults=json.loads((ROOT/'assets/resolved_publication_defaults.json').read_text())
        for stage,values in defaults.items():
            for key,expected in frozen[stage].items():
                if key in values and not isinstance(expected,str):
                    self.assertEqual(values[key],expected,f'{stage}.{key}')

if __name__ == '__main__':
    unittest.main()
