"""Join existing FusionReport/FusionInspector evidence without re-scoring calls."""
import argparse
import csv
import hashlib
import json
import platform
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SUFFIXES = {'fusionreport': '.fusions.csv', 'fusioninspector': '.FusionInspector.fusions.tsv'}
CALLERS = ('arriba', 'starfusion', 'fusioncatcher')

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def table(path, kind):
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=',' if kind == 'fusionreport' else '\t')
        if reader.fieldnames is None:
            raise ValueError(f'Empty file without header: {path}')
        reader.fieldnames = [k.lstrip('#') for k in reader.fieldnames]
        required = {'Fusion', *CALLERS} if kind == 'fusionreport' else {'FusionName', 'JunctionReadCount', 'SpanningFragCount'}
        if not required <= set(reader.fieldnames):
            raise ValueError(f'Missing columns {sorted(required-set(reader.fieldnames))}: {path}')
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'Malformed row {line}: {path}')
            pair = row['Fusion' if kind == 'fusionreport' else 'FusionName'].strip()
            if len(pair.split('--')) != 2 or any(not x for x in pair.split('--')):
                raise ValueError(f'Invalid ordered gene pair at {path}:{line}')
            yield line, pair, row

def write(path, rows, fields):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fields, delimiter='\t')
        w.writeheader()
        w.writerows(rows)

def present(value):
    return value.strip().lower() not in ('', '.', 'na', 'nan', 'none', 'null')

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='Recursively discover reports here')
    p.add_argument('--output', type=Path, required=True, help='New output directory')
    p.add_argument('--file-manifest', type=Path, help='Optional TSV: sample_id, kind, path; replaces discovery')
    args = p.parse_args(argv)
    csv.field_size_limit(2147483647)
    if args.output.exists():
        p.error('Output already exists; choose a new directory')
    candidates = defaultdict(set)
    if args.file_manifest:
        with open(args.file_manifest, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t')
            if not {'sample_id', 'kind', 'path'} <= set(reader.fieldnames or []):
                p.error('Manifest requires sample_id, kind, path')
            for row in reader:
                if row['kind'] not in SUFFIXES or not row['sample_id'].strip():
                    p.error('Invalid manifest kind or empty sample_id')
                path = Path(row['path'])
                if not path.is_absolute():
                    path = args.file_manifest.resolve().parent / path
                candidates[row['sample_id'], row['kind']].add(path.resolve())
    else:
        if not args.input.is_dir():
            p.error('--input must be an existing directory')
        for path in args.input.resolve().rglob('*'):
            if path.is_file():
                for kind, suffix in SUFFIXES.items():
                    if path.name.endswith(suffix):
                        candidates[path.name[:-len(suffix)], kind].add(path)
    if not candidates:
        p.error('No matching report files')
    audit, selected, conflicts = [], {}, []
    for (sample, kind), paths in sorted(candidates.items()):
        hashes = {path: digest(path) for path in sorted(paths)}
        if len(set(hashes.values())) > 1:
            conflicts.append(f'{sample} / {kind}: ' + ', '.join(map(str, hashes)))
        first = next(iter(hashes))
        selected[sample, kind] = first
        for path, sha in hashes.items():
            audit.append(dict(sample_id=sample, kind=kind, path=str(path), sha256=sha, selected=path == first))
    if conflicts:
        p.error('Conflicting reruns. Select final files with --file-manifest:\n' + '\n'.join(conflicts))
    groups = defaultdict(lambda: defaultdict(list))
    totals = Counter()
    # Retain all rows, including multiple junctions per ordered gene pair.
    for (sample, kind), path in sorted(selected.items()):
        for line, pair, raw in table(path, kind):
            groups[sample, pair][kind].append(dict(source_file=str(path), source_line=line, evidence=raw))
            totals[sample, kind] += 1
    fields = ['sample_id', 'fusion_pair', 'gene1', 'gene2', 'join_status', 'report_available', 'inspector_available',
              'report_rows', 'inspector_rows', 'discovery_callers', 'n_discovery_callers', 'caller_presence_consistent',
              'fusionreport_evidence_json', 'fusioninspector_evidence_json']
    catalogue, summaries, recurrence = [], [], defaultdict(set)
    samples = sorted({sample for sample, _ in selected})
    for sample in samples:
        rows = []
        for (s, pair), sources in sorted(groups.items()):
            if s != sample:
                continue
            reports, inspectors = sources['fusionreport'], sources['fusioninspector']
            patterns = {tuple(c for c in CALLERS if present(r['evidence'][c])) for r in reports}
            callers = sorted({c for pattern in patterns for c in pattern})
            status = 'both' if reports and inspectors else 'report_only' if reports else 'inspector_only'
            row = dict(sample_id=sample, fusion_pair=pair, gene1=pair.split('--')[0], gene2=pair.split('--')[1],
                       join_status=status, report_available=(sample, 'fusionreport') in selected,
                       inspector_available=(sample, 'fusioninspector') in selected,
                       report_rows=len(reports), inspector_rows=len(inspectors), discovery_callers=';'.join(callers),
                       n_discovery_callers=len(callers) if reports else '',
                       caller_presence_consistent=len(patterns) == 1 if reports else '',
                       fusionreport_evidence_json=json.dumps(reports, sort_keys=True),
                       fusioninspector_evidence_json=json.dumps(inspectors, sort_keys=True))
            rows.append(row)
            if inspectors:
                recurrence[pair].add(sample)
        catalogue.extend(rows)
        have_report, have_inspector = [(sample, k) in selected for k in SUFFIXES]
        summary = dict(sample_id=sample, fusionreport_status='available' if have_report else 'missing',
                       fusioninspector_status='available' if have_inspector else 'missing',
                       fusionreport_rows=totals[sample, 'fusionreport'] if have_report else '',
                       fusioninspector_rows=totals[sample, 'fusioninspector'] if have_inspector else '',
                       fusionreport_pairs=sum(r['report_rows'] > 0 for r in rows) if have_report else '',
                       fusioninspector_pairs=sum(r['inspector_rows'] > 0 for r in rows) if have_inspector else '',
                       matched_pairs=sum(r['join_status'] == 'both' for r in rows) if have_report and have_inspector else '',
                       report_only_pairs=sum(r['join_status'] == 'report_only' for r in rows) if have_report and have_inspector else '',
                       inspector_only_pairs=sum(r['join_status'] == 'inspector_only' for r in rows) if have_report and have_inspector else '',
                       inconsistent_report_caller_pairs=sum(r['caller_presence_consistent'] is False for r in rows))
        for n in (0, 1, 2, 3):
            summary[f'report_pairs_{n}_discovery_callers'] = sum(r['n_discovery_callers'] == n for r in rows) if have_report else ''
            summary[f'inspector_pairs_{n}_discovery_callers'] = sum(r['inspector_rows'] > 0 and r['n_discovery_callers'] == n for r in rows) if have_report and have_inspector else ''
        summary['inspector_pairs_unknown_discovery_support'] = sum(r['inspector_rows'] > 0 and r['n_discovery_callers'] == '' for r in rows) if have_inspector else ''
        for c in CALLERS:
            summary[f'report_pairs_{c}'] = sum(c in r['discovery_callers'].split(';') for r in rows) if have_report else ''
        summaries.append(summary)
    args.output.mkdir(parents=True)
    write(args.output / 'combined_fusion_catalogue.tsv', catalogue, fields)
    write(args.output / 'per_sample_summary.tsv', summaries, list(summaries[0]))
    write(args.output / 'file_audit.tsv', audit, ['sample_id', 'kind', 'path', 'sha256', 'selected'])
    write(args.output / 'fusioninspector_pair_recurrence.tsv',
          [dict(fusion_pair=pair, n_samples=len(ids), sample_ids=';'.join(sorted(ids))) for pair, ids in sorted(recurrence.items())],
          ['fusion_pair', 'n_samples', 'sample_ids'])
    for kind in SUFFIXES:
        with open(args.output / f'{kind}_evidence.jsonl', 'w', encoding='utf-8') as f:
            for (sample, pair), sources in sorted(groups.items()):
                for r in sources[kind]:
                    f.write(json.dumps(dict(sample_id=sample, fusion_pair=pair, **r), sort_keys=True) + '\n')
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                    command=sys.argv, script_sha256=digest(Path(__file__)), inputs=audit,
                    file_manifest_sha256=digest(args.file_manifest) if args.file_manifest else None,
                    samples=len(samples), catalogue_pairs=len(catalogue),
                    join_rule='exact ordered FusionReport.Fusion = FusionInspector.FusionName',
                    filtering='none; existing outputs retained')
    (args.output / 'provenance_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Wrote {len(catalogue)} sample/pair rows for {len(samples)} samples to {args.output}')

if __name__ == '__main__':
    main()
