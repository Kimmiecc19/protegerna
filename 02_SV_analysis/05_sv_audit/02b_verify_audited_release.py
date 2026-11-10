"""Independent checks of audit outputs and important scientific edge cases."""
import csv
import argparse
import hashlib
import importlib
import json
from collections import Counter
from pathlib import Path

# Module name starts with a digit, so it cannot be imported with a plain import statement.
release_builder = importlib.import_module('02a_build_audited_release')

def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_table(out_dir, name):
    with (out_dir / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def parse_args(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', '--out', dest='out_dir', type=Path, required=True, help='Absolute path to the release output directory')
    parser.add_argument('--input-dir', '--source', dest='input_dir', type=Path, required=True,
                        help='Absolute path to the original saved audit input directory passed to '
                             '02a_build_audited_release.py --input-dir (not the release output directory)')
    parser.add_argument('--expected-case-n', type=int, default=release_builder.EVIDENCE_THRESHOLDS['case_n'])
    parser.add_argument('--expected-control-n', type=int, default=release_builder.EVIDENCE_THRESHOLDS['control_n'])
    parser.add_argument('--skip-study-expectations', action='store_true',
                        help='Run general consistency checks without enforcing the fixed study cohort')
    args=parser.parse_args(argv)
    if args.expected_case_n < 0 or args.expected_control_n < 0:
        parser.error('Expected cohort counts must be non-negative')
    for name,path in (('out-dir', args.out_dir), ('input-dir', args.input_dir)):
        if not path.is_absolute() or not path.is_dir():
            parser.error(f'--{name} must be an existing absolute directory: {path}')
    out_dir, input_dir=args.out_dir, args.input_dir
    required=[out_dir/name for name in ('audited_candidates.tsv', 'participant_support.tsv',
              'integration_pairs.tsv', 'primary_candidates.tsv', 'sample_manifest.tsv', 'input_checksums.json')]
    required.extend(input_dir/name for name in ('evidence_per_record.tsv', 'review_events.tsv'))
    missing=[str(path) for path in required if not path.is_file()]
    if missing:
        parser.error('Missing verification inputs:\n'+'\n'.join(missing)+
                     '\n--input-dir must be the original audit input directory used by '
                     '02a_build_audited_release.py; --out-dir must be its release output directory.')
    return args


def validate_consistency(events, pairs, integration, primary, manifest, source_events):
    event_ids = {event['review_event_id'] for event in events}
    require(event_ids == {event['review_event_id'] for event in source_events},
            'Release event set differs from supplied audit source')
    require(bool(events) and len(event_ids) == len(events) and all(event_ids),
            'Audited candidates require unique, nonempty review_event_id values')
    sample_ids = {record['sample_id'] for record in manifest}
    require(bool(manifest) and len(sample_ids) == len(manifest) and all(sample_ids),
            'Sample manifest requires unique, nonempty sample_id values')
    expected_pairs = len(events) * len(manifest)
    require(len(pairs) == expected_pairs,
            f'Expected {expected_pairs} participant/event rows; found {len(pairs)}')
    actual_keys = {(record['review_event_id'], record['sample_id']) for record in pairs}
    expected_keys = {(event_id, sample_id) for event_id in event_ids for sample_id in sample_ids}
    require(actual_keys == expected_keys, 'Participant/event keys do not cover the complete manifest and event set')
    counts = Counter(record['review_event_id'] for record in pairs
                     if record['audited_call_state'] == 'alternate_call_recorded')
    support = Counter(record['review_event_id'] for record in pairs if record['support_rule_met'] == 'True')
    for event in events:
        review_event_id = event['review_event_id']
        expected_carriers = int(event['audited_case_carriers']) + int(event['audited_control_carriers'])
        require(counts[review_event_id] == expected_carriers,
                f'Carrier count mismatch for {review_event_id}: event={expected_carriers}, participant rows={counts[review_event_id]}')
        require(support[review_event_id] == int(event['audited_n_supported']),
                f'Supported participant count mismatch for {review_event_id}')
    require({event['review_event_id'] for event in primary} == {record['review_event_id'] for record in integration},
            'Primary candidate events disagree with integration event IDs')
    require(all(record['support_rule_met'] == 'True' and record['matching_support_stable'] == 'True' for record in integration),
            'Integration pairs include unsupported or matching-sensitive calls')
    require(not any(record['low_mapping_quality'] == 'True' or record['shared_raw_allele_across_nominations'] == 'True'
                    for record in integration), 'Integration pairs include low-quality or shared raw alleles')
    require(not any(event['str_loci_nearby'] or event['hold_reasons'] for event in primary),
            'Primary candidates include unresolved hold reasons or repeat context')
    return event_ids


def validate_study_expectations(manifest, expected_case_n, expected_control_n):
    expected = {'CASE': expected_case_n, 'CTRL': expected_control_n}
    actual = Counter(record['sample_id'].split('-')[0] for record in manifest)
    require(actual == expected, f'Study cohort mismatch: expected {expected}, found {dict(actual)}')


def verify_raw_format(raw, event_ids):
    # Re-parse the caller evidence from its original FORMAT values, independently of
    # the cached evidence columns used by the builder.
    raw = [record for record in raw if record['review_event_id'] in event_ids]
    parse_number = release_builder.parse_number
    for record in raw:
        label = f"{record.get('sample_id')}/{record.get('ID')}"
        mismatch = f'Raw FORMAT evidence mismatch for {label}'
        sample_fields = dict(zip(record['FORMAT'].split(':'), record['SAMPLE_VALUES'].split(':')))
        present = lambda key: key in sample_fields and sample_fields[key] not in ('.', '')  # noqa: E731
        require('GT' in sample_fields, f'Missing original FORMAT/GT for {label}')
        require(record['caller'] in ('Manta', 'TIDDIT'), f'Unknown caller: {record["caller"]}')
        require(record['gt'] == sample_fields['GT'], mismatch)
        if record['caller'] == 'Manta':
            for key, column in [('SR', 'manta_sr_alt'), ('PR', 'manta_pr_alt')]:
                if present(key):
                    counts = sample_fields[key].split(',')
                    require(len(counts) == 2, f'Expected reference/alternate {key} counts for {label}')
                    require(parse_number(record[column]) == float(counts[1]), mismatch)
            require(record['manta_ft'] == sample_fields.get('FT', ''), mismatch)
        else:
            for key, column in [('RV', 'tiddit_rv'), ('DV', 'tiddit_dv')]:
                if present(key):
                    require(parse_number(record[column]) == float(sample_fields[key]), mismatch)
            if present('COV'):
                coverage = sample_fields['COV'].split(',')
                require(len(coverage) == 3, f'Expected three COV values for {label}')
                left_depth, middle_depth, right_depth = map(float, coverage)
                if left_depth + right_depth > 0:
                    expected_ratio = middle_depth / ((left_depth + right_depth) / 2)
                    require(abs(float(record['tiddit_depth_ratio']) - expected_ratio) < 1e-10, mismatch)
    return len(raw)


def verify_scientific_edge_cases():
    # Shared reads reported by two callers must count as ONE evidence type.
    event=dict(sv_type='DEL',sv_length_bp='600',chrom='1',start='1000',end='1600')
    base=dict(raw_start='1000',raw_end='1600',raw_svlen='600',REF='N',ALT='<DEL>',
        raw_sv_type='DEL',event_chrom='1',INFO='',sample_id='CASE-test',gt='0/1',FILTER='PASS',ID='test')
    manta_record=dict(base,caller='Manta',manta_sr_alt='5',manta_pr_alt='0',manta_imprecise='False',manta_ft='PASS')
    tiddit_record=dict(base,caller='TIDDIT',tiddit_rv='5',tiddit_dv='0')
    evaluation=release_builder.evaluate_evidence(event,[manta_record,tiddit_record])
    require(evaluation['n_evidence_types']==1 and not evaluation['support_rule_met'] and evaluation['both_callers'], 'Caller split reads must be pooled into one evidence type; two callers alone do not establish support')
    require(not release_builder.passes_quality(dict(manta_record,FILTER='.')), 'Missing FILTER must fail strict caller quality checks')
    require(not release_builder.passes_quality(dict(manta_record,manta_ft='MinGQ')), 'Manta MinGQ must fail caller quality checks')
    require(not release_builder.passes_quality(dict(manta_record,gt='0/.')), 'Partial reference genotype must fail carrier quality checks')
    require(not release_builder.matches_event(event,dict(manta_record,raw_start='1400',raw_end='2000'),50,.7), 'Calls outside the coordinate tolerance must not match the event')
    require(not release_builder.matches_event(event,dict(manta_record,raw_svlen='50'),50,.7), 'Calls with incompatible sizes must not match the event')
    small=dict(event,sv_length_bp='100',end='1100')
    evaluation=release_builder.evaluate_evidence(small,[dict(manta_record,raw_svlen='100',raw_end='1100')])
    require(evaluation['support_category']=='precise_junction_only_small_sv' and evaluation['n_evidence_types']==1, 'Small precise junction-only calls must retain their distinct support category')
    require(release_builder.evaluate_evidence(event,[])['support_category']=='no_qualifying_call', 'Events without raw calls must have no qualifying support')
    require(not release_builder.is_complete_alternate_gt('0/0') and release_builder.is_complete_alternate_gt('1') and not release_builder.is_complete_alternate_gt('./1'), 'Genotype checks must exclude reference and partial calls while accepting complete haploid alternate calls')



def verify_dispositions(events):
    # Check failure dispositions for whichever nominations are present.
    require(all(event['disposition']=='held_coordinate_or_size_conflict' for event in events
               if 'coordinate_or_size_conflict' in event['hold_reasons'].split(';')), 'Coordinate or size conflicts must receive the corresponding hold disposition')
    require(all(event['old_outcome']=='excluded_failed_caller_filter'
               and int(event['audited_case_carriers'])+int(event['audited_control_carriers'])==0
               for event in events if event['disposition']=='excluded_failed_caller_filters'), 'Failed caller-filter dispositions require the previous failure outcome and zero audited carriers')


def verify_checksums(out_dir):
    for path,expected_hash in json.loads((out_dir/'input_checksums.json').read_text()).items():
        input_path=Path(path)
        if not input_path.is_absolute():
            raise ValueError(f'Checksum path must be absolute: {path}. Rebuild the release with the updated builder.')
        require(hashlib.sha256(input_path.read_bytes()).hexdigest()==expected_hash, f'Input checksum changed: {input_path}')


def main(argv=None):
    args = parse_args(argv)
    out_dir, input_dir = args.out_dir, args.input_dir
    events=load_table(out_dir, 'audited_candidates.tsv')
    pairs=load_table(out_dir, 'participant_support.tsv')
    integration=load_table(out_dir, 'integration_pairs.tsv')
    primary=load_table(out_dir, 'primary_candidates.tsv')
    manifest=load_table(out_dir, 'sample_manifest.tsv')
    source_events = release_builder.read_tsv(input_dir / 'review_events.tsv')
    event_ids = validate_consistency(events, pairs, integration, primary, manifest, source_events)
    if not args.skip_study_expectations:
        validate_study_expectations(manifest, args.expected_case_n, args.expected_control_n)
    n_raw_checked = verify_raw_format(release_builder.read_tsv(input_dir / 'evidence_per_record.tsv'), event_ids)
    verify_scientific_edge_cases()
    verify_dispositions(events)
    verify_checksums(out_dir)
    result={'status':'passed','shortlists':dict(Counter(event['shortlist'] for event in events)), 'nominations':len(events),'participant_event_rows':len(pairs),
            'primary_candidates':len(primary),'integration_pairs':len(integration),
            'cached_raw_records_independently_checked':n_raw_checked,
            'checks':['unique identifiers and count reconciliation','integration eligibility and provenance',
                      'original FORMAT evidence re-parsing','pooled caller split-read evidence',
                      'strict PASS and genotype semantics','matching boundary and size compatibility',
                      'small-event support explicitly distinguished','failure dispositions',
                      'source checksums unchanged']}
    (out_dir/'verification.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result,indent=2))



if __name__ == '__main__':
    main()
