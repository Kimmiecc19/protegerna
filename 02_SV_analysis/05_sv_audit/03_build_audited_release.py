"""Reconcile the supplied saved event audit without rerunning SV calling.

Standard library only. Historical inputs are never modified. Matching is applied
symmetrically to all participants. Absence of a matched call is NOT a reference
genotype. This is a research nomination release, not clinical classification.
"""
from __future__ import annotations
import csv
import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

VERSION = '1.0.0'
STRONG = {'Definitive ALS gene', 'Strong evidence', 'Moderate evidence'}
POLICIES = {'bp10_ratio70': (10, .7), 'bp50_ratio70': (50, .7),
            'bp100_ratio70': (100, .7), 'bp50_ratio50': (50, .5)}
PRIMARY = 'bp50_ratio70'

# These values drive both calculations and release_parameters.json.
EVIDENCE_THRESHOLDS = dict(
    min_split_reads=3, min_discordant_pairs=3, min_depth_size=1000,
    del_max_depth_ratio=0.75, dup_min_depth_ratio=1.25,
    small_junction_only_max_size_exclusive=500, max_lq=0.3,
    event_min_supported_fraction=0.5, min_evidence_types=2,
    case_n=296, control_n=51, min_sv_length=50, max_sv_length=100000,
    control_count_review_threshold=3, control_frequency_review_threshold=0.05,
    cohort_frequency_review_threshold=0.10,
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', '--source', dest='input_dir', type=Path, required=True,
                        help='Absolute path to the saved audit directory containing review_events.tsv and evidence files')
    parser.add_argument('--intersection-annotations', dest='intersection_annotations_path', type=Path, required=True,
                        help='Absolute path to the intersection *.annotated.tsv file')
    parser.add_argument('--union-annotations', dest='union_annotations_path', type=Path, required=True,
                        help='Absolute path to the union-only *.annotated.tsv file')
    parser.add_argument('--out-dir', '--out', dest='out_dir', type=Path, required=True,
                        help='Absolute path to the release output directory')
    args = parser.parse_args(argv)
    for name, value in vars(args).items():
        if not value.is_absolute():
            parser.error(f'--{name.replace("_", "-")} must be an absolute path: {value}')
    input_dir = args.input_dir
    out_dir = args.out_dir
    if not input_dir.is_dir():
        parser.error(f'--input-dir directory does not exist: {input_dir}')
    required = ['review_events.tsv', 'evidence_per_event.tsv', 'evidence_per_record.tsv',
                'vcf_manifest.tsv', 'raw_record_matches.tsv', 'run_log.json', 'evidence_thresholds.json']
    missing = [str(input_dir / filename) for filename in required if not (input_dir / filename).is_file()]
    if missing:
        parser.error('Missing saved audit inputs:\n' + '\n'.join(missing))
    paths = [args.intersection_annotations_path, args.union_annotations_path]
    for path in paths:
        if not path.is_file():
            parser.error(f'Annotation file does not exist: {path}')
    if out_dir.exists() and not out_dir.is_dir():
        parser.error(f'--out-dir must be a directory: {out_dir}')
    return args

def read_tsv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))

def write_tsv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', extrasaction='raise')
        writer.writeheader()
        writer.writerows(rows)

def parse_number(value, default=0):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (ValueError, TypeError):
        return default

def parse_boolean(value):
    return str(value).lower() == 'true'

def split_sample_ids(text):
    return set(filter(None, text.split(';')))

def parse_info(text):
    return dict(item.split('=', 1) if '=' in item else (item, True) for item in text.split(';') if item)

def is_complete_alternate_gt(gt):
    alleles = re.split(r'[/|]', gt)
    return bool(alleles) and all(allele.isdigit() for allele in alleles) and any(int(allele) > 0 for allele in alleles)

def raw_sv_length(record):
    length_bp = abs(parse_number(record['raw_svlen']))
    record_info = parse_info(record['INFO'])
    if not length_bp and record['raw_sv_type'] == 'INS':
        length_bp = abs(parse_number(record_info.get('SVINSLEN')))
        if not length_bp and re.fullmatch('[ACGTNacgtn]+', record['ALT']):
            length_bp = abs(len(record['ALT']) - len(record['REF']))
    if not length_bp and record['raw_sv_type'] != 'INS':
        length_bp = abs(parse_number(record['raw_end']) - parse_number(record['raw_start']))
    return length_bp

def passes_quality(record):
    # FILTER='.' means not filtered, never PASS. Sample FT failures also excluded.
    return (record['FILTER'] == 'PASS' and record.get('manta_ft', '') in ('', '.', 'PASS')
            and is_complete_alternate_gt(record['gt']))

def is_compatible(event, record):
    # An isolated BND is not sufficient to identify an inversion allele.
    return record['raw_sv_type'] == event['sv_type'] and record['event_chrom'] == event['chrom']

def matches_event(event, record, breakpoint_tolerance, ratio):
    if not is_compatible(event, record):
        return False
    if abs(parse_number(record['raw_start']) - int(event['start'])) > breakpoint_tolerance:
        return False
    if event['sv_type'] != 'INS' and abs(parse_number(record['raw_end']) - int(event['end'])) > breakpoint_tolerance:
        return False
    event_length, record_length = abs(parse_number(event['sv_length_bp'])), raw_sv_length(record)
    return event_length > 0 and record_length > 0 and min(event_length, record_length) / max(event_length, record_length) >= ratio

def record_fingerprint(record):
    return (record['sample_id'], record['caller'], record['CHROM'], record['POS'], record['ID'], record['REF'], record['ALT'])

def evaluate_evidence(event, rows):
    """Evidence TYPES are pooled across callers. Caller agreement is separate."""
    manta_records = [record for record in rows if record['caller'] == 'Manta']
    tiddit_records = [record for record in rows if record['caller'] == 'TIDDIT']
    split_read_count = max([parse_number(record.get('manta_sr_alt')) for record in manta_records] + [parse_number(record.get('tiddit_rv')) for record in tiddit_records] + [0])
    pair_count = max([parse_number(record.get('manta_pr_alt')) for record in manta_records] + [parse_number(record.get('tiddit_dv')) for record in tiddit_records] + [0])
    junction = any(not parse_boolean(record.get('manta_imprecise')) and parse_number(record.get('manta_sr_alt')) >= EVIDENCE_THRESHOLDS['min_split_reads'] for record in manta_records)
    ratios = [parse_number(record.get('tiddit_depth_ratio'), None) for record in tiddit_records]
    ratios = [depth_ratio for depth_ratio in ratios if depth_ratio is not None]
    depth = 'not_assessable'
    if event['sv_type'] in ('DEL', 'DUP') and abs(parse_number(event['sv_length_bp'])) >= EVIDENCE_THRESHOLDS['min_depth_size'] and ratios:
        ok = [depth_ratio <= EVIDENCE_THRESHOLDS['del_max_depth_ratio'] if event['sv_type'] == 'DEL' else depth_ratio >= EVIDENCE_THRESHOLDS['dup_min_depth_ratio'] for depth_ratio in ratios]
        depth = 'consistent' if all(ok) else 'contradictory_or_mixed'
    low = any(parse_number(record.get('tiddit_lq_max')) > EVIDENCE_THRESHOLDS['max_lq'] for record in tiddit_records)
    # Distinct same-caller alleles are unresolved; do not select the strongest one.
    alleles = defaultdict(set)
    for record in rows:
        alleles[record['caller']].add((record['raw_start'], record['raw_end'], raw_sv_length(record), record['REF'], record['ALT']))
    ambiguous = any(len(caller_alleles) > 1 for caller_alleles in alleles.values())
    types = int(split_read_count >= EVIDENCE_THRESHOLDS['min_split_reads']) + int(pair_count >= EVIDENCE_THRESHOLDS['min_discordant_pairs']) + int(depth == 'consistent')
    if not rows:
        label = 'no_qualifying_call'
    elif ambiguous:
        label = 'ambiguous_multiple_raw_alleles'
    elif depth == 'contradictory_or_mixed':
        label = 'depth_conflict'
    elif types >= EVIDENCE_THRESHOLDS['min_evidence_types']:
        label = 'multiple_evidence_types'
    elif abs(parse_number(event['sv_length_bp'])) < EVIDENCE_THRESHOLDS['small_junction_only_max_size_exclusive'] and junction:
        label = 'precise_junction_only_small_sv'
    else:
        label = 'below_support_rule'
    supported = label in ('multiple_evidence_types', 'precise_junction_only_small_sv')
    return dict(support_category=label, support_rule_met=supported,
                n_evidence_types=types, split_reads_max=split_read_count, discordant_pairs_max=pair_count,
                read_depth_status=depth, precise_manta_junction=junction,
                both_callers=bool(manta_records and tiddit_records), low_mapping_quality=low,
                ambiguous_same_caller_alleles=ambiguous,
                selected_raw_records=';'.join(sorted({record['caller'] + ':' + record['ID'] for record in rows})),
                raw_genotypes=';'.join(sorted({record['caller'] + ':' + record['gt'] for record in rows})),
                depth_ratios=';'.join(str(depth_ratio) for depth_ratio in ratios))

def assign_tier(event, samples):
    case_count = sum(sample_id.startswith('CASE-') for sample_id in samples)
    control_count = len(samples) - case_count
    case_n, control_n = EVIDENCE_THRESHOLDS['case_n'], EVIDENCE_THRESHOLDS['control_n']
    if (not samples or control_count >= EVIDENCE_THRESHOLDS['control_count_review_threshold']
            or control_count / control_n >= EVIDENCE_THRESHOLDS['control_frequency_review_threshold']
            or (case_count + control_count) / (case_n + control_n) >= EVIDENCE_THRESHOLDS['cohort_frequency_review_threshold']
            or (control_count and control_count / control_n >= case_count / case_n)):
        return 4
    if control_count:
        return 3
    return 1 if event['highest_alsod_evidence'] in STRONG else 2

def load_release_inputs(input_dir, annotation_paths):
    events = read_tsv(input_dir / 'review_events.tsv')
    event_ids = [event['review_event_id'] for event in events]
    duplicates = [review_event_id for review_event_id, count in Counter(event_ids).items() if count > 1]
    if not events or len(set(event_ids)) != len(events) or not all(event_ids):
        raise ValueError(f'{input_dir / "review_events.tsv"}: expected a nonempty table with unique, nonempty review_event_id values; '
                         f'found {len(events)} rows and {len(set(event_ids))} unique IDs. '
                         f'Shortlists: {dict(Counter(event["shortlist"] for event in events))}. '
                         f'Duplicate IDs: {duplicates[:10]}.')
    unknown_shortlists = {event['shortlist'] for event in events} - {'intersection', 'union_only'}
    if unknown_shortlists:
        raise ValueError(f'Unsupported shortlist values: {sorted(unknown_shortlists)}')
    old = {record['review_event_id']: record for record in read_tsv(input_dir / 'evidence_per_event.tsv')}
    selected_event_ids = set(event_ids)
    records = [record for record in read_tsv(input_dir / 'evidence_per_record.tsv')
               if record['review_event_id'] in selected_event_ids]
    manifest = read_tsv(input_dir / 'vcf_manifest.tsv')
    samples = sorted({record['sample_id'] for record in manifest})
    missing_prior = set(event_ids) - set(old)
    if missing_prior:
        raise ValueError(f'Events missing from evidence_per_event.tsv: {sorted(missing_prior)}')
    require(len(samples) == len(manifest) == EVIDENCE_THRESHOLDS['case_n'] + EVIDENCE_THRESHOLDS['control_n'], "Release validation failed: len(samples) == len(manifest) == EVIDENCE_THRESHOLDS['case_n'] + EVIDENCE_THRESHOLDS['control_n']")
    require(Counter(sample_id.split('-')[0] for sample_id in samples) == {'CASE': EVIDENCE_THRESHOLDS['case_n'], 'CTRL': EVIDENCE_THRESHOLDS['control_n']}, "Release validation failed: Counter(sample_id.split('-')[0] for sample_id in samples) == {'CASE': EVIDENCE_THRESHOLDS['case_n'], 'CTRL': EVIDENCE_THRESHOLDS['control_n']}")
    require(not (set(record['sample_id'] for record in records) - set(samples)), "Release validation failed: not (set(record['sample_id'] for record in records) - set(samples))")
    grouped = defaultdict(list)
    seen = set()
    for i, record in enumerate(records):
        key = (record['review_event_id'], record_fingerprint(record))
        if key in seen:
            continue
        seen.add(key)
        record['_key'] = f'R{i+1:05d}'
        grouped[record['review_event_id']].append(record)

    annotations = {}
    for label, path in zip(('intersection', 'union_only'), annotation_paths):
        for record in read_tsv(path):
            if record['Annotation_mode'] == 'full':
                annotations[label, record['AnnotSV_ID']] = record

    return dict(events=events, samples=samples, records=records, manifest=manifest,
                grouped=grouped, annotations=annotations, old=old)


def match_events(events, samples, grouped, annotations, old):
    # Compute all policies independently with the same quality/support rule.
    states, sensitivity, record_audit, failure_rows = {}, [], [], []
    for event in events:
        review_event_id = event['review_event_id']
        raw = grouped[review_event_id]
        recorded = split_sample_ids(event['case_carriers']) | split_sample_ids(event['control_carriers'])
        require(recorded <= set(samples), 'Release validation failed: recorded <= set(samples)')
        annotation = annotations.get((event['shortlist'], event['event_id']))
        require(annotation is not None, ('Missing full annotation', review_event_id))
        annotation_info = parse_info(annotation['INFO'])
        coordinate_problem = (parse_number(annotation_info.get('END'), int(event['end'])) < int(event['start'])
                              or not EVIDENCE_THRESHOLDS['min_sv_length'] <= abs(parse_number(event['sv_length_bp'])) <= EVIDENCE_THRESHOLDS['max_sv_length'])
        for policy, (breakpoint_tolerance, ratio) in POLICIES.items():
            accepted = [record for record in raw if passes_quality(record) and matches_event(event, record, breakpoint_tolerance, ratio)]
            by_sample = defaultdict(list)
            for record in accepted:
                by_sample[record['sample_id']].append(record)
            evaluations = {sample_id: evaluate_evidence(event, sample_records) for sample_id, sample_records in by_sample.items()}
            carriers = set(by_sample)
            n_supported = sum(evaluation_result['support_rule_met'] for evaluation_result in evaluations.values())
            event_supported = bool(carriers) and n_supported >= math.ceil(len(carriers) * EVIDENCE_THRESHOLDS['event_min_supported_fraction'])
            states[review_event_id, policy] = dict(rows=accepted, by_sample=by_sample, evaluations=evaluations,
                carriers=carriers, tier=assign_tier(event, carriers), supported=event_supported,
                n_supported=n_supported, coordinate_problem=coordinate_problem)
            sensitivity.append(dict(review_event_id=review_event_id, policy=policy, case_carriers=sum(sample_id.startswith('CASE') for sample_id in carriers),
                control_carriers=sum(sample_id.startswith('CTRL') for sample_id in carriers),
                supported_participants=n_supported, tier=assign_tier(event, carriers),
                event_support_rule_met=event_supported, additions_vs_original=len(carriers-recorded),
                removed_vs_original=len(recorded-carriers)))
        for record in raw:
            sample_records = dict(raw_record_key=record['_key'], review_event_id=review_event_id, sample_id=record['sample_id'],
                original_carrier=record['recorded_carrier'], caller=record['caller'], raw_id=record['ID'],
                raw_start=record['raw_start'], raw_end=record['raw_end'], raw_length=raw_sv_length(record),
                raw_filter=record['FILTER'], sample_ft=record.get('manta_ft',''), raw_gt=record['gt'],
                strict_quality_pass=passes_quality(record), source_record_id_matches=record['id_matches_octopusv_record'])
            sample_records.update({path: matches_event(event, record, *threshold) for path, threshold in POLICIES.items()})
            record_audit.append(sample_records)

        strict = states[review_event_id, PRIMARY]
        missing = strict['carriers'] - recorded
        missing_both = {sample_id for sample_id in missing if strict['evaluations'][sample_id]['both_callers']}
        exact_missing = {record['sample_id'] for record in strict['rows'] if record['sample_id'] in missing
                         and int(record['raw_start']) == int(event['start'])
                         and (event['sv_type']=='INS' or int(record['raw_end']) == int(event['end']))}
        old_failed = old[review_event_id]['suggested_outcome'] == 'excluded_failed_caller_filter'
        original_rows = [record for record in raw if record['recorded_carrier']=='yes']
        failure_rows.append(dict(review_event_id=review_event_id, genes=event['genes'], original_n_carriers=len(recorded),
            strict_n_carriers=len(strict['carriers']), added_carriers=len(missing),
            added_with_both_callers=len(missing_both),
            added_with_exact_breakpoints=len(exact_missing), removed_original_carriers=len(recorded-strict['carriers']),
            previous_filter_failure=old_failed,
            original_carrier_raw_filters=';'.join(sorted({record['FILTER'] for record in original_rows})),
            all_original_raw_records_failed=bool(original_rows) and all(record['FILTER']!='PASS' for record in original_rows),
            consolidated_filter=annotation['FILTER'], original_annotation_start=event['start'], original_annotation_end=event['end'],
            original_annotation_length=event['sv_length_bp'], consolidated_info_end=annotation_info.get('END',''),
            consolidated_info_svlen=annotation_info.get('SVLEN',''), coordinate_hold=coordinate_problem,
            cause_status='coordinate aggregation inconsistency; exact generating step unverified' if coordinate_problem else
            'PASS provenance violation; generating step unverified' if old_failed else
            'added single-caller observations outside original intersection definition; not proof of genotype loss'
                if missing and event['shortlist']=='intersection' and not missing_both else
            'union identifier under-representation or allele splitting; generating step unverified'
                if missing else 'no failure established by this check'))

    return states, sensitivity, record_audit, failure_rows


def find_shared_alleles(events, states):
    # Link nominations that reuse the same accepted raw allele. Do not silently
    # count them as independent events or merge their annotations.
    shared = defaultdict(set)
    for event in events:
        for record in states[event['review_event_id'], PRIMARY]['rows']:
            shared[record_fingerprint(record)].add(event['review_event_id'])
    event_links = defaultdict(set)
    shared_pairs = set()
    for record_key, linked_event_ids in shared.items():
        if len(linked_event_ids)>1:
            for review_event_id in linked_event_ids:
                event_links[review_event_id].update(linked_event_ids-{review_event_id})
                shared_pairs.add((review_event_id,record_key[0]))

    return event_links, shared_pairs


def assign_dispositions(events, states, old, event_links):
    final = []
    for event in events:
        review_event_id = event['review_event_id']
        primary_state = states[review_event_id, PRIMARY]
        broad = states[review_event_id, 'bp100_ratio70']
        tight = states[review_event_id, 'bp10_ratio70']
        loose_len = states[review_event_id, 'bp50_ratio50']
        prior = old[review_event_id]
        recorded = split_sample_ids(event['case_carriers']) | split_sample_ids(event['control_carriers'])
        stable_decision = (primary_state['tier']==broad['tier']==loose_len['tier']==tight['tier'] and
                           primary_state['supported']==broad['supported']==loose_len['supported']==tight['supported'])
        repeat = prior.get('str_loci_nearby','')
        unresolved_alleles = any(evaluation_result['ambiguous_same_caller_alleles'] for evaluation_result in primary_state['evaluations'].values())
        reasons = []
        if primary_state['coordinate_problem']: reasons.append('coordinate_or_size_conflict')
        if not primary_state['carriers']: reasons.append('no_strict_qualifying_raw_call')
        if repeat: reasons.append('disease_repeat_context_requires_review')
        if event_links[review_event_id]: reasons.append('raw_allele_shared_between_nominations')
        if unresolved_alleles: reasons.append('multiple_raw_alleles_within_participant')
        if not stable_decision: reasons.append('matching_sensitive_tier_or_support')
        if primary_state['tier'] in (1,2) and prior['tier_raw_recount'] in ('3','4'):
            reasons.append('promotion_depends_on_rejecting_previous_carriers')
        if not primary_state['supported']: reasons.append('event_support_rule_not_met')
        low = any(evaluation_result['low_mapping_quality'] for evaluation_result in primary_state['evaluations'].values())
        if low: reasons.append('low_mapping_quality')
        if primary_state['coordinate_problem']:
            disposition = 'held_coordinate_or_size_conflict'
        elif not primary_state['carriers']:
            disposition = ('excluded_failed_caller_filters' if prior['suggested_outcome']=='excluded_failed_caller_filter'
                           else 'held_no_strict_raw_match')
        elif primary_state['tier'] >= 3:
            disposition = 'deprioritised_shared_or_frequent'
        elif reasons:
            disposition = 'exploratory_review_only'
        else:
            disposition = 'primary_candidate'
        row = dict(release_version=VERSION, **event,
            old_tier_raw_recount=prior['tier_raw_recount'], old_outcome=prior['suggested_outcome'],
            audited_case_carriers=sum(sample_id.startswith('CASE') for sample_id in primary_state['carriers']),
            audited_control_carriers=sum(sample_id.startswith('CTRL') for sample_id in primary_state['carriers']),
            audited_tier=primary_state['tier'], audited_n_supported=primary_state['n_supported'],
            event_support_rule_met=primary_state['supported'],
            additions_vs_original=len(primary_state['carriers']-recorded), removals_vs_original=len(recorded-primary_state['carriers']),
            carrier_set_same_at_10bp=primary_state['carriers']==tight['carriers'],
            carrier_set_same_at_100bp=primary_state['carriers']==broad['carriers'],
            carrier_set_same_at_ratio50=primary_state['carriers']==loose_len['carriers'],
            decision_stable_across_all_matching_policies=stable_decision,
            str_loci_nearby=repeat, related_nomination_ids=';'.join(sorted(event_links[review_event_id])),
            disposition=disposition, hold_reasons=';'.join(reasons),
            clinical_group_status='CASE prefix includes ALS and disease controls; clinical diagnosis not reconciled')
        final.append(row)
    return final


def build_participant_rows(events, samples, states, final, shared_pairs):
    participant_rows = []
    final_by_id = {event['review_event_id']: event for event in final}
    for event in events:
        review_event_id = event['review_event_id']
        primary_state = states[review_event_id, PRIMARY]
        broad = states[review_event_id, 'bp100_ratio70']
        tight = states[review_event_id, 'bp10_ratio70']
        loose_len = states[review_event_id, 'bp50_ratio50']
        recorded = split_sample_ids(event['case_carriers']) | split_sample_ids(event['control_carriers'])
        disposition = final_by_id[review_event_id]['disposition']
        for sample_id in samples:
            evaluation = primary_state['evaluations'].get(sample_id, evaluate_evidence(event, []))
            broad_evaluation = broad['evaluations'].get(sample_id, evaluate_evidence(event, []))
            tight_evaluation = tight['evaluations'].get(sample_id, evaluate_evidence(event, []))
            length_evaluation = loose_len['evaluations'].get(sample_id, evaluate_evidence(event, []))
            pair_stable = (sample_id in primary_state['carriers'] and sample_id in broad['carriers'] and sample_id in loose_len['carriers'] and sample_id in tight['carriers']
                           and evaluation['support_rule_met']==broad_evaluation['support_rule_met']==length_evaluation['support_rule_met']==tight_evaluation['support_rule_met'])
            eligible = (disposition=='primary_candidate' and evaluation['support_rule_met'] and pair_stable
                        and not evaluation['low_mapping_quality'] and (review_event_id,sample_id) not in shared_pairs)
            participant_rows.append(dict(review_event_id=review_event_id,event_id=event['event_id'],genes=event['genes'],
                sample_id=sample_id, group=sample_id.split('-')[0], clinical_diagnosis='unreconciled',
                originally_recorded_carrier=sample_id in recorded,
                audited_call_state='alternate_call_recorded' if sample_id in primary_state['carriers'] else 'unknown_no_qualifying_call',
                **evaluation, call_present_at_10bp=sample_id in tight['carriers'], call_present_at_100bp=sample_id in broad['carriers'],
                call_present_at_ratio50=sample_id in loose_len['carriers'],
                shared_raw_allele_across_nominations=(review_event_id,sample_id) in shared_pairs,
                matching_support_stable=pair_stable, disposition=disposition,
                eligible_for_exploratory_molecular_integration=eligible))

    return participant_rows


def validate_release(events, samples, final, participant_rows):
    expected_pairs = len(events) * len(samples)
    require(len(participant_rows)==expected_pairs, 'Release validation failed: len(participant_rows)==expected_pairs')
    require(len({(record['review_event_id'],record['sample_id']) for record in participant_rows})==expected_pairs, "Release validation failed: len({(record['review_event_id'],record['sample_id']) for record in participant_rows})==expected_pairs")
    for event in final:
        sample_records=[record for record in participant_rows if record['review_event_id']==event['review_event_id']]
        require(sum(record['audited_call_state']=='alternate_call_recorded' for record in sample_records)==event['audited_case_carriers']+event['audited_control_carriers'], "Release validation failed: sum(record['audited_call_state']=='alternate_call_recorded' for record in sample_records)==event['audited_case_carriers']+event['audited_control_carriers']")
    primary = [event for event in final if event['disposition']=='primary_candidate']
    integration = [record for record in participant_rows if record['eligible_for_exploratory_molecular_integration']]
    require(all(any(record['review_event_id']==event['review_event_id'] for record in integration) for event in primary), "Release validation failed: all(any(record['review_event_id']==event['review_event_id'] for record in integration) for event in primary)")
    return primary, integration


def write_release(args, release):
    out_dir, input_dir = args.out_dir, args.input_dir
    annotation_paths = [args.intersection_annotations_path, args.union_annotations_path]
    events, samples = release['events'], release['samples']
    final, participant_rows = release['final'], release['participant_rows']
    states, sensitivity = release['states'], release['sensitivity']
    record_audit, failure_rows = release['record_audit'], release['failure_rows']
    manifest, records, event_links = release['manifest'], release['records'], release['event_links']
    primary, integration = validate_release(events, samples, final, participant_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(out_dir / 'audited_candidates.tsv',final)
    write_tsv(out_dir / 'participant_support.tsv',participant_rows)
    write_tsv(out_dir / 'primary_candidates.tsv',primary, list(final[0]))
    write_tsv(out_dir / 'integration_pairs.tsv',integration, list(participant_rows[0]))
    write_tsv(out_dir / 'matching_sensitivity.tsv',sensitivity)
    write_tsv(out_dir / 'raw_match_audit.tsv',record_audit)
    write_tsv(out_dir / 'consolidation_findings.tsv',failure_rows)
    write_tsv(out_dir / 'sample_manifest.tsv',manifest)
    summary=dict(version=VERSION, original_nominations=len(events), participants=len(samples),
        participant_event_rows=len(participant_rows), primary_candidates=len(primary),
        primary_by_provenance=dict(Counter(event['shortlist'] for event in primary)),
        integration_pairs=len(integration), integration_participants=len({record['sample_id'] for record in integration}),
        dispositions=dict(Counter(event['disposition'] for event in final)),
        audited_tiers=dict(Counter(event['audited_tier'] for event in final)),
        nominated_tier12_with_strict_calls=sum(event['audited_tier'] in (1,2) and event['audited_case_carriers']+event['audited_control_carriers']>0 for event in final),
        events_with_added_carriers=sum(record['added_carriers']>0 for record in failure_rows),
        events_with_exact_added_carriers=sum(record['added_with_exact_breakpoints']>0 for record in failure_rows),
        intersection_events_with_additions=sum(record['added_carriers']>0 and record['review_event_id'].startswith('INT-') for record in failure_rows),
        union_events_with_additions=sum(record['added_carriers']>0 and record['review_event_id'].startswith('UO-') for record in failure_rows),
        added_pairs_with_both_callers=sum(record['added_with_both_callers'] for record in failure_rows),
        previous_filter_failure_events=sum(record['previous_filter_failure'] for record in failure_rows),
        confirmed_all_original_raw_records_failed=sum(record['previous_filter_failure'] and record['all_original_raw_records_failed'] for record in failure_rows),
        strict_quality_excluded_records=sum(not passes_quality(record) for record in records),
        missing_filter_records=sum(record['FILTER']=='.' for record in records),
        nominations_sharing_raw_alleles=sum(bool(event_links[event['review_event_id']]) for event in events),
        sensitivity={path:dict(total_carrier_pairs=sum(len(states[event['review_event_id'],path]['carriers']) for event in events),
            supported_pairs=sum(states[event['review_event_id'],path]['n_supported'] for event in events),
            tier12_events=sum(states[event['review_event_id'],path]['tier'] in (1,2) for event in events),
            carrier_set_changed_vs_primary=sum(states[event['review_event_id'],path]['carriers']!=states[event['review_event_id'],PRIMARY]['carriers'] for event in events),
            tier_changed_vs_primary=sum(states[event['review_event_id'],path]['tier']!=states[event['review_event_id'],PRIMARY]['tier'] for event in events)) for path in POLICIES},
        checks=f'unique keys, {len(samples)} participants, {len(events)} nominations, all event counts reconcile to participant rows; primary events all have integration pairs')
    (out_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    inputs=[input_dir/filename for filename in ['review_events.tsv','evidence_per_record.tsv','evidence_per_event.tsv','raw_record_matches.tsv','vcf_manifest.tsv','run_log.json','evidence_thresholds.json']]+annotation_paths
    inputs.append(Path(__file__).resolve())
    hashes={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    (out_dir/'input_checksums.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
    config=dict(version=VERSION,primary_matching=PRIMARY, matching_policies=POLICIES,
        **EVIDENCE_THRESHOLDS,
        input_scope=f'Saved raw matches for {len(events)} nominated events only; no fresh whole-cohort calling or re-genotyping',
        broad_extraction='500 bp or 50% reciprocal overlap; all new matching policies are subsets',
        quality='FILTER exactly PASS, non-failing FT, complete alternate GT',
        noncarrier_semantics='unknown, never independently confirmed reference',
        release_scope='local controlled research release; not public deposition')
    (out_dir/'release_parameters.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    return summary



def main(argv=None):
    args = parse_args(argv)
    annotation_paths = [args.intersection_annotations_path, args.union_annotations_path]
    data = load_release_inputs(args.input_dir, annotation_paths)
    states, sensitivity, record_audit, failure_rows = match_events(
        data['events'], data['samples'], data['grouped'], data['annotations'], data['old'])
    event_links, shared_pairs = find_shared_alleles(data['events'], states)
    final = assign_dispositions(data['events'], states, data['old'], event_links)
    participant_rows = build_participant_rows(data['events'], data['samples'], states, final, shared_pairs)
    summary = write_release(args, dict(data, states=states, sensitivity=sensitivity,
        record_audit=record_audit, failure_rows=failure_rows, event_links=event_links,
        final=final, participant_rows=participant_rows))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
