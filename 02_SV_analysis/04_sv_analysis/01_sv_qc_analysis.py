#!/usr/bin/env python3
"""Per-VCF SV QC and carrier burden. No pooling of overlapping callers/callsets.

Defaults: PASS, 50 <= length <= 100000 bp, unknown lengths and BND/TRA excluded,
genotype interpretation disabled (enable with --genotypes caller-reported).
Participants are grouped by sample prefix: CASE- -> case, CTRL- -> control,
anything else -> unknown.

Each VCF is streamed twice: a light first pass validates the file and resolves
record IDs and breakend pairs, and a second pass reads genotypes one record at
a time, so memory does not grow with the number of samples x records.
Uses Python's standard library only.
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

GENOTYPE_OUTPUTS = ['genotype_counts', 'genotype_qc', 'per_sample_call_counts', 'record_carriers',
                    'participant_burden', 'burden_by_svtype', 'burden_by_size', 'event_recurrence']


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def parse_info(text):
    info = dict(x.split('=', 1) if '=' in x else (x, True)
                for x in text.split(';') if x and x != '.')
    # variantconvert may retain original VCF INFO inside an INFO field.
    nested = info.get('INFO', '')
    if isinstance(nested, str):
        for item in nested.split('|'):
            if '=' in item:
                key, value = item.split('=', 1)
                if key in {'SVTYPE', 'SVLEN', 'END'}:
                    info.setdefault(key, value)
    return info


def open_vcf(path):
    return gzip.open(path, 'rt', encoding='utf-8-sig') if str(path).endswith('.gz') else open(path, encoding='utf-8-sig')


def is_breakend(info, alt):
    return info.get('SVTYPE') in {'BND', 'TRA'} or '[' in alt or ']' in alt or alt.startswith('.') or alt.endswith('.')


def get_svlen(pos, info, ref, alt):
    if is_breakend(info, alt):
        return None
    if ',' in alt:  # A single record length cannot represent multiple alleles.
        return None
    try:
        if 'SVLEN' in info:
            return abs(int(info['SVLEN']))
        # END cannot measure the inserted sequence of a symbolic insertion.
        if 'END' in info and info.get('SVTYPE') != 'INS':
            return abs(int(info['END']) - pos)
        if re.fullmatch('[ACGTNacgtn]+', ref) and re.fullmatch('[ACGTNacgtn]+', alt):
            return abs(len(ref) - len(alt))
    except (ValueError, TypeError):
        pass
    return None


def size_bin(length):
    if length is None:
        return 'unknown'
    for high, label in [(50, '<50bp'), (100, '50-<100bp'), (500, '100-<500bp'),
                        (1000, '500bp-<1kb'), (10000, '1-<10kb'),
                        (100000, '10-<100kb'), (1000000, '100kb-<1Mb')]:
        if length < high:
            return label
    return '>=1Mb'


def record_size_bin(record):
    return 'not_applicable_breakend' if record['bnd'] else size_bin(record['svlen'])


def condition(sample_id):
    return 'case' if sample_id.startswith('CASE-') else 'control' if sample_id.startswith('CTRL-') else 'unknown'


def parse_genotype(format_text, sample_values, alt_count, min_gq=None, min_dp=None, require_ft=False, partial_gt='complete'):
    """Return class, carrier state (True/False/None), and QC status.

    The default partial_gt='complete' requires a complete genotype to count a
    carrier. Under 'alternate-known', a partial GT such as 1/. counts as a
    carrier, but is never assigned a complete zygosity. A partial reference GT
    such as 0/. has unknown carrier state under either policy.
    """
    keys = format_text.split(':')
    values = sample_values.split(':')
    data = dict(zip(keys, values))
    if 'GT' not in keys:
        return 'no_GT', None, 'no_GT'
    gt = data.get('GT', '.')
    alleles = re.split(r'[/|]', gt)
    if not alleles or any(allele != '.' and (not allele.isdigit() or int(allele) > alt_count) for allele in alleles):
        return 'invalid', None, 'invalid_GT'
    known = [int(allele) for allele in alleles if allele != '.']
    if not known:
        genotype_class, carrier = 'missing', None
    elif len(known) != len(alleles):
        genotype_class, carrier = 'partial_missing', True if any(known) else None
    elif len(known) == 1:
        genotype_class, carrier = ('haploid_alt' if known[0] else 'haploid_ref'), bool(known[0])
    elif len(known) == 2:
        genotype_class = 'het' if known[0] != known[1] else ('hom_ref' if known[0] == 0 else 'hom_alt')
        carrier = any(known)
    else:
        genotype_class = 'polyploid_ref' if not any(known) else ('polyploid_alt_uniform' if len(set(known)) == 1 else 'polyploid_mixed')
        carrier = any(known)
    if carrier is True and genotype_class == 'partial_missing' and partial_gt == 'complete':
        carrier = None
    if require_ft and data.get('FT') != 'PASS':
        return genotype_class, None, 'FT_not_PASS_or_missing'
    for field, threshold in [('GQ', min_gq), ('DP', min_dp)]:
        if threshold is not None:
            try:
                value = float(data[field])
                if not value >= threshold:
                    return genotype_class, None, field + '_below_threshold'
            except (KeyError, ValueError):
                return genotype_class, None, field + '_missing_or_invalid'
    return genotype_class, carrier, 'pass'


def data_lines(path):
    """Yield (line number, fields) for the #CHROM line and every data line."""
    with open_vcf(path) as handle:
        for lineno, line in enumerate(handle, 1):
            if line.startswith('##') or not line.strip():
                continue
            yield lineno, line.rstrip('\r\n').split('\t')


def read_sites(path):
    """First pass: validate the VCF and keep only per-record site information."""
    samples, records = None, []
    for lineno, fields in data_lines(path):
        if fields[0] == '#CHROM':
            samples = fields[9:]
            if len(set(samples)) != len(samples):
                raise ValueError(f'{path}: duplicate sample names')
            continue
        if samples is None or len(fields) < 8 or (samples and len(fields) != 9 + len(samples)):
            raise ValueError(f'{path}:{lineno}: malformed VCF/header/sample count')
        chrom, pos, rid, ref, alt, _qual, filt, info_text = fields[:8]
        info = parse_info(info_text)
        if info.get('AnnotSV_ID') and info.get('Annotation_mode') not in {'full', 'split'}:
            raise ValueError('Annotated VCF requires Annotation_mode=full or split')
        bnd = is_breakend(info, alt)
        records.append(dict(chrom=chrom, pos=int(pos), id=rid, alt=alt, filter=filt, mateid=info.get('MATEID'),
                            split_row=info.get('Annotation_mode') == 'split',
                            svtype=info.get('SVTYPE', 'BND' if bnd else 'UNKNOWN'),
                            bnd=bnd, svlen=get_svlen(int(pos), info, ref, alt)))
    if samples is None:
        raise ValueError(f'{path}: missing #CHROM header')
    return samples, records


def exclusion(record, args):
    if record['split_row']:
        return 'annotation_split_row'
    if ',' in record['alt']:
        return 'multiallelic_excluded'
    if args.filter_policy == 'pass' and record['filter'] != 'PASS':
        return 'filter_not_PASS'
    if args.sv_types and record['svtype'] not in args.sv_types:
        return 'SVTYPE_excluded'
    if record['bnd']:
        return '' if args.breakends == 'include' else 'breakend_excluded'
    if record['svlen'] is None:
        return '' if args.unknown_size == 'include' else 'unknown_size'
    if record['svlen'] < args.min_svlen or record['svlen'] > args.max_svlen:
        return 'outside_size_range'
    return ''


def assign_event_keys(records):
    """Counting units: one per record, except explicit, unique, reciprocal MATEID pairs.

    EVENT can name multi-junction events and is deliberately not used to merge.
    """
    ids = defaultdict(list)
    for index, record in enumerate(records):
        record.update(index=index, event_key=f'record:{index+1}', breakend_status='not_breakend')
        if record['id'] != '.':
            ids[record['id']].append(record)
    for record in records:
        if not record['bnd']:
            continue
        record['breakend_status'] = 'unpaired_or_ambiguous'
        mate = ids.get(record['mateid'], [])
        if len(ids.get(record['id'], [])) == 1 and len(mate) == 1:
            other = mate[0]
            if other is not record and other['bnd'] and other['mateid'] == record['id']:
                record['breakend_status'] = 'reciprocal_pair'
                record['event_key'] = f"bnd_pair:{min(record['index'], other['index'])+1}"


def write_tsv(path, rows, columns):
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter='\t', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def site_outputs(path, prefix, records, args):
    """Variant-level table and filter/type/size counts (no genotypes needed)."""
    rows = []
    for record in records:
        row = {k: record[k] for k in ['chrom', 'pos', 'id', 'filter', 'svtype', 'svlen', 'event_key',
                                      'breakend_status', 'exclusion']}
        row.update(vcf_file=str(path), caller=args.caller, callset=args.callset,
                   included=not record['exclusion'], size_bin=record_size_bin(record))
        rows.append(row)
    write_tsv(f'{prefix}.variant_level_stats.tsv', rows,
              ['vcf_file', 'caller', 'callset', 'chrom', 'pos', 'id', 'filter', 'svtype', 'svlen', 'size_bin',
               'included', 'exclusion', 'event_key', 'breakend_status'])
    for field, suffix in [('filter', 'filter_counts'), ('svtype', 'svtype_counts'), ('size_bin', 'size_bins')]:
        result = []
        for scope in ['input', 'included']:
            counter = Counter(row[field] for row in rows if scope == 'input' or row['included'])
            result.extend(dict(scope=scope, category=k, records=v) for k, v in sorted(counter.items()))
        write_tsv(f'{prefix}.{suffix}.tsv', result, ['scope', 'category', 'records'])


def genotype_outputs(path, prefix, samples, records, args):
    """Second pass: carrier states, per-sample burden and per-record recurrence."""
    selected = {record['index']: record for record in records if not record['exclusion']}
    id_counts = Counter(record['id'] for record in records if not record['split_row'])
    genotype_counts, genotype_qc, known_states, unknown = Counter(), Counter(), Counter(), Counter()
    units = {sample_id: set() for sample_id in samples}
    by_type, by_size = defaultdict(set), defaultdict(set)
    carrier_rows, events = [], []
    index = -1
    for _, fields in data_lines(path):
        if fields[0] == '#CHROM':
            continue
        index += 1
        record = selected.get(index)
        if record is None:
            continue
        alt_count = len(record['alt'].split(','))
        carriers, missing, groups = 0, 0, Counter()
        for sample_id, value in zip(samples, fields[9:]):
            genotype_class, carrier, qc = parse_genotype(fields[8], value, alt_count, args.min_gq, args.min_dp,
                                                         args.require_ft_pass, args.partial_gt)
            genotype_counts[genotype_class] += 1
            genotype_qc[qc] += 1
            if carrier is None:
                missing += 1
                unknown[sample_id] += 1
                continue
            known_states[sample_id] += 1
            if carrier:
                carriers += 1
                groups[condition(sample_id)] += 1
                units[sample_id].add(record['event_key'])
                by_type[sample_id, record['svtype']].add(record['event_key'])
                by_size[sample_id, record_size_bin(record)].add(record['event_key'])
        carrier_rows.append(dict(vcf_file=str(path), record_index=index + 1, id=record['id'],
                                 case_carriers=groups['case'], control_carriers=groups['control'],
                                 unclassified_carriers=groups['unknown'], unknown_carrier_state=missing))
        event_id = record['id']
        events.append(dict(record_key=f'vcf_record_{index+1:09d}', event_id=event_id, event_key=record['event_key'],
                           id_status='missing' if event_id == '.' else 'duplicate' if id_counts[event_id] > 1 else 'unique',
                           chrom=record['chrom'], pos=record['pos'], svtype=record['svtype'], svlen=record['svlen'],
                           recorded_carriers=carriers, unknown_gt=missing,
                           reference_coded=len(samples) - missing - carriers, recurrent_recorded=carriers >= 2))

    write_tsv(f'{prefix}.genotype_counts.tsv',
              [dict(genotype_class=k, sample_records=v) for k, v in sorted(genotype_counts.items())],
              ['genotype_class', 'sample_records'])
    write_tsv(f'{prefix}.genotype_qc.tsv', [dict(status=k, sample_records=v) for k, v in sorted(genotype_qc.items())],
              ['status', 'sample_records'])
    write_tsv(f'{prefix}.per_sample_call_counts.tsv',
              [dict(sample=s, condition=condition(s), called_units=len(units[s]),
                    records_with_known_carrier_state=known_states[s]) for s in samples],
              ['sample', 'condition', 'called_units', 'records_with_known_carrier_state'])
    write_tsv(f'{prefix}.record_carriers.tsv', carrier_rows,
              ['vcf_file', 'record_index', 'id', 'case_carriers', 'control_carriers', 'unclassified_carriers',
               'unknown_carrier_state'])
    write_tsv(f'{prefix}.participant_burden.tsv',
              [dict(sample=s, condition=condition(s), callset=args.callset, total_recorded_sv=len(units[s]),
                    records_with_unknown_gt=unknown[s]) for s in samples],
              ['sample', 'condition', 'callset', 'total_recorded_sv', 'records_with_unknown_gt'])
    for suffix, counter, categories in [
            ('svtype', by_type, sorted({record['svtype'] for record in selected.values()})),
            ('size', by_size, sorted({record_size_bin(record) for record in selected.values()}))]:
        write_tsv(f'{prefix}.burden_by_{suffix}.tsv',
                  [dict(sample=s, category=k, recorded_sv_count=len(counter.get((s, k), ())))
                   for s in samples for k in categories],
                  ['sample', 'category', 'recorded_sv_count'])
    write_tsv(f'{prefix}.event_recurrence.tsv', events,
              ['record_key', 'event_id', 'event_key', 'id_status', 'chrom', 'pos', 'svtype', 'svlen',
               'recorded_carriers', 'unknown_gt', 'reference_coded', 'recurrent_recorded'])


def analyze(path, args):
    samples, records = read_sites(path)
    digest = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    prefix = f"{args.out_prefix}.{re.sub(r'[^A-Za-z0-9_.-]', '_', path.name)}.{digest}"
    Path(prefix).parent.mkdir(parents=True, exist_ok=True)
    for record in records:
        record['exclusion'] = exclusion(record, args)
    assign_event_keys(records)

    included = [record for record in records if not record['exclusion']]
    included_breakends = [record for record in included if record['bnd']]
    counts = {
        'input_records': len(records),
        'included_records': len(included),
        'excluded_records': len(records) - len(included),
        'included_counting_units': len({record['event_key'] for record in included}),
        'samples_in_header': len(samples),
        'included_breakend_records': len(included_breakends),
        'included_unpaired_breakend_records': sum(record['breakend_status'] != 'reciprocal_pair'
                                                  for record in included_breakends),
    }
    # Record tallies are only reported when non-zero.
    counts = {k: v for k, v in counts.items() if v or k not in {'input_records', 'included_records', 'excluded_records'}}
    write_tsv(f'{prefix}.summary.tsv', [dict(metric=k, value=v) for k, v in sorted(counts.items())], ['metric', 'value'])
    site_outputs(path, prefix, records, args)
    if args.genotypes == 'caller-reported':
        genotype_outputs(path, prefix, samples, records, args)
    else:
        # Do not leave genotype files from an earlier enabled run beside this run's outputs.
        for suffix in GENOTYPE_OUTPUTS:
            Path(f'{prefix}.{suffix}.tsv').unlink(missing_ok=True)
    return dict(vcf_file=str(path), output_prefix=prefix, caller=args.caller, callset=args.callset, **counts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--vcf', nargs='+', required=True, help='VCF(s); each is analysed separately')
    parser.add_argument('-o', '--out-prefix', '--outprefix', dest='out_prefix', required=True)
    parser.add_argument('--caller', default='unspecified', help='Explicit provenance label; run each caller separately')
    parser.add_argument('--callset', default='unspecified', help='Explicit provenance label, e.g. raw, union, intersection')
    parser.add_argument('--filter-policy', choices=['pass', 'all'], default='pass')
    parser.add_argument('--min-svlen', type=int, default=50)
    parser.add_argument('--max-svlen', type=int, default=100000)
    parser.add_argument('--sv-types', nargs='+')
    parser.add_argument('--unknown-size', choices=['exclude', 'include'], default='exclude')
    parser.add_argument('--breakends', choices=['exclude', 'include'], default='exclude',
                        help='Included BND/TRA bypass length thresholds and remain size-not-applicable')
    parser.add_argument('--genotypes', choices=['disabled', 'caller-reported'], default='disabled',
                        help='Enable only when original/reliably preserved caller GTs are available')
    parser.add_argument('--min-gq', type=float)
    parser.add_argument('--min-dp', type=float)
    parser.add_argument('--require-ft-pass', action='store_true')
    parser.add_argument('--partial-gt', choices=['complete', 'alternate-known'], default='complete',
                        help='Complete GT required by default; alternate-known counts 1/. as a carrier')
    args = parser.parse_args(argv)
    if args.min_svlen < 0 or args.max_svlen < args.min_svlen:
        parser.error('Require 0 <= min-svlen <= max-svlen')
    if any(v is not None and (v < 0 or not v < float('inf')) for v in [args.min_gq, args.min_dp]):
        parser.error('GQ and DP thresholds must be finite and non-negative')
    if args.genotypes == 'disabled' and (args.min_gq is not None or args.min_dp is not None or args.require_ft_pass):
        parser.error('Genotype QC options require --genotypes caller-reported')
    # Paths are recorded as given, so relative paths keep the outputs portable.
    results = [analyze(Path(path), args) for path in sorted(set(args.vcf))]
    manifest = dict(
        settings=vars(args), inputs=results,
        counting_note='Each VCF is analysed and reported separately; there is no cross-VCF or cross-caller summation. '
                      'Counting units are non-breakend records, reciprocal BND pairs or unpaired BND records. '
                      'Multiallelic and AnnotSV split rows are excluded. Partial GT policy is explicit. '
                      'GT classes precede genotype quality exclusions. Condition comes from the CASE-/CTRL- sample prefix.')
    Path(str(args.out_prefix) + '.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Processed {len(results)} VCFs separately. Manifest: {args.out_prefix}.manifest.json')


if __name__ == '__main__':
    main()
