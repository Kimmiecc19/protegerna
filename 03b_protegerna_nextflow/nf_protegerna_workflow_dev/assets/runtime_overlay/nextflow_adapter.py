"""Nextflow task adapter: staged inputs, explicit CLI options, and provenance.

Every pipeline process runs:  python3 -B runtime/nextflow_adapter.py <stage>
with a base64-encoded JSON payload on standard input.
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import importlib
import json
import platform
from importlib.metadata import version
import shutil
import subprocess
import sys
from pathlib import Path

STAGES = {
    'validate': ('validate_gencode_translation', 'validate_gencode_translation', 'build_parser'),
    'fusion': ('fusiontoprotein', 'fusiontoprotein', 'build_parser'),
    'rmats': ('rmatstoprotein', 'proteogenomic.splice_cli', 'build_rmats_parser'),
    'suppa': ('suppatoprotein', 'proteogenomic.splice_cli', 'build_suppa_parser'),
    'merge': ('merge_proteogenomic_database', 'merge_proteogenomic_database', 'build_parser'),
    'qc': ('proteogenomic_fasta_qc', 'proteogenomic.qc_cli', 'build_parser'),
}

def cli_arguments(parser, values):
    actions = {action.dest: action for action in parser._actions}
    tokens = []
    for key, value in values.items():
        if value is None:
            continue
        if key not in actions:
            raise ValueError(f'Unknown option: {key}')
        action = actions[key]
        flag = '--' + key
        if isinstance(value, bool):
            if isinstance(action, argparse.BooleanOptionalAction):
                tokens.append(flag if value else '--no-' + key)
            elif value:
                tokens.append(flag)
            elif action.default is not False:
                raise ValueError(f'Cannot disable {key} using this parser')
        elif isinstance(value, list):
            if value:
                tokens.extend([flag, *map(str, value)])
        else:
            tokens.extend([flag, str(value)])
    return tokens

def prepare_events(stage, rows, files):
    """Keep file identity and metadata when equal basenames occur in batches."""
    values, metadata, event_metadata = {}, {}, {}
    for row, filename in zip(rows, files, strict=True):
        path = Path(filename)
        if path.stat().st_size == 0:
            raise ValueError(f'Empty {stage} input: {row["path"]}')
        if stage == 'fusion':
            # Upstream derives sample_id from this filename.
            target = Path('events') / row['batch'] / (row['sample'] + '.FusionInspector.fusions.abridged.tsv')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            key = 'fusioninspector'
            path = target
            metadata[row['sample']] = {'sample_id': row['sample'], 'batch': row['batch'], 'condition': row['condition']}
        elif stage == 'rmats':
            key = row['event_type'].lower() + '_files'
            event_metadata[str(path.resolve())] = row
        else:
            key = 'event_files' if row['event_type'] == 'IOE' else 'psi_files'
            if key == 'psi_files':
                # PSI columns identify samples; cohort row labels must not replace them.
                with path.open(encoding='utf-8-sig') as handle:
                    columns = handle.readline().rstrip('\n\r').split('\t')
                if columns and columns[0].lower() in {'', 'event_id', 'event', 'id'}:
                    columns = columns[1:]
                for sample in columns:
                    entry = {'sample_id': sample, 'batch': row['batch'], 'condition': row['condition']}
                    if sample in metadata and metadata[sample] != entry:
                        raise ValueError(f'Conflicting SUPPA metadata for {sample}')
                    metadata[sample] = entry
        values.setdefault(key, []).append(str(path))
    if stage == 'suppa' and not values.get('event_files'):
        raise ValueError('SUPPA requires at least one IOE row')
    if event_metadata:
        Path('event_metadata.json').write_text(json.dumps(event_metadata, indent=2)+'\n', encoding='utf-8')
        values['event_metadata'] = 'event_metadata.json'
    if metadata:
        with Path('sample_metadata.tsv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=['sample_id', 'batch', 'condition'], delimiter='\t')
            writer.writeheader()
            writer.writerows(metadata.values())
        values['sample_metadata'] = 'sample_metadata.tsv'
    return values

def collect_versions():
    """Combine the per-task versions.yml files staged as versions*/versions.yml."""
    combined = {}
    for path in sorted(Path.cwd().glob('versions*/*.yml')):
        combined.update(json.loads(path.read_text()))
    Path('software_versions.yml').write_text(json.dumps(combined, indent=2)+'\n', encoding='utf-8')

def run(stage, payload):
    if stage == 'versions':
        return collect_versions()
    options = {k: v for k, v in payload['options'].items() if v is not None}
    options.update(payload.get('inputs', {}))
    if stage in {'fusion', 'rmats', 'suppa'}:
        options.update(prepare_events(stage, payload['rows'], payload['files']))
        if stage != 'rmats' and payload.get('sample_metadata'):
            from proteogenomic.provenance import load_sample_metadata
            metadata = load_sample_metadata(options.get('sample_metadata'))
            metadata.update(load_sample_metadata(payload['sample_metadata']))
            with Path('sample_metadata.tsv').open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=['sample_id','batch','condition'], delimiter='\t')
                writer.writeheader()
                writer.writerows(metadata.values())
            options['sample_metadata'] = 'sample_metadata.tsv'
        workers = options.get('workers') if options.get('workers') is not None else payload['cpus']
        if int(workers) < 1:
            raise ValueError('workers must be at least 1')
        options['workers'] = min(int(workers), int(payload['cpus']))
        # Source loaders may rebuild caches. Never modify an upstream task's symlink.
        shutil.copyfile(options['reference_peptide_cache'], 'reference.local.cache')
        options['reference_peptide_cache'] = 'reference.local.cache'
    Path('task_inputs.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    if stage == 'gtfdb':
        import gffutils
        gffutils.create_db(options['gtf'], dbfn='gencode.gtf.db', force=True,
                           keep_order=True, merge_strategy='merge', sort_attribute_values=True)
    elif stage == 'cache':
        from proteogenomic.splice_translation import load_reference_tryptic_peptides
        if payload.get('existing_cache'):
            shutil.copyfile(payload['existing_cache'], 'reference_tryptic_peptides.cache')
        load_reference_tryptic_peptides(options['reference_proteome'],
            max_missed_cleavages=options['max_missed_cleavages'],
            min_len=options['min_peptide_length'], max_len=options['max_peptide_length'],
            cache_path='reference_tryptic_peptides.cache')
    else:
        module, parser_module, factory = STAGES[stage]
        parser = getattr(importlib.import_module(parser_module), factory)()
        command = [sys.executable, str(Path(__file__).parent / (module+'.py')), *cli_arguments(parser, options)]
        Path('command.json').write_text(json.dumps(command, indent=2)+'\n', encoding='utf-8')
        subprocess.run(command, check=True)
    digest = hashlib.sha256()
    for source in sorted(Path(__file__).parent.rglob('*.py')):
        digest.update(source.relative_to(Path(__file__).parent).as_posix().encode())
        digest.update(source.read_bytes())
    versions = {payload['process']: {
        'python': platform.python_version(), 'proteogenomic_source_sha256': digest.hexdigest(),
        **{name: version(name) for name in ('biopython','gffutils','pandas','pyfaidx','tqdm')},
    }}
    # JSON is valid YAML and avoids an extra runtime dependency.
    Path('versions.yml').write_text(json.dumps(versions, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    run(sys.argv[1], json.loads(base64.b64decode(sys.stdin.read())))
