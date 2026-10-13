#!/usr/bin/env python3
"""Build and reconcile one row per participant and intersection SV.

Participants with no qualifying SV remain in the validation counts and a separate
zero-SV table; no artificial variant rows are added to the main table.
"""
import argparse
import csv
import hashlib
import importlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# Same genotype policy as the prioritisation step (module name starts with a digit).
is_non_reference_gt = importlib.import_module('02_annotsv_prioritization').is_non_reference_gt

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('/home/kcoetzer/objective_two/run_annotsv/results')
FILTERED = BASE / 'octopusv_intersect_cohort_filtered_08102026/manta_tiddit.intersect.cohort.annotated.tsv'
UNFILTERED = BASE / 'octopusv_intersect_cohort_unfiltered_08102026/manta_tiddit.intersect.cohort.annotated.tsv'
TABLE_COLUMNS = ['Participant', 'SV ID', 'Coordinates', 'SV type', 'Caller support',
                 'Affected gene', 'Predicted consequence', 'ALS/HPO annotation']
MISSING_VALUES = {'', '.', 'NA'}


def key(row):
    return tuple(row[field] for field in ('SV_chrom', 'SV_start', 'SV_end', 'SV_type', 'ID'))


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        yield from csv.DictReader(handle, delimiter='\t')


def sample_columns(header):
    """Validate the sample block bounded by FORMAT and Annotation_mode."""
    if len(header) != len(set(header)):
        raise ValueError('Duplicate annotation column names')
    for boundary in ('FORMAT', 'Annotation_mode'):
        if boundary not in header:
            raise ValueError(f'Missing sample-column boundary: {boundary}')
    start, end = header.index('FORMAT') + 1, header.index('Annotation_mode')
    samples = header[start:end]
    if start >= end or any(not sample_id.startswith(('CASE-', 'CTRL-')) for sample_id in samples):
        raise ValueError('Expected CASE-/CTRL- sample columns between FORMAT and Annotation_mode')
    return samples


def load_annotations(source, filtered_tsv):
    enrich = {}
    for row in read(filtered_tsv):
        if row['Annotation_mode'] == 'split':
            enrich[key(row), row['Gene_name'], row['Tx']] = row
    with source.open(encoding='utf-8-sig', newline='') as handle:
        header = next(csv.reader(handle, delimiter='\t'), [])
    samples = sample_columns(header)
    sample_set = set(samples)
    full, splits = {}, defaultdict(list)
    for row in read(source):
        event_key = key(row)
        slim = {field: value for field, value in row.items() if field not in sample_set}
        if row['Annotation_mode'] == 'split':
            splits[event_key].append(slim)
            continue
        if row['Annotation_mode'] != 'full':
            raise ValueError(f'Unsupported Annotation_mode for {event_key}: {row["Annotation_mode"]}')
        if event_key in full:
            raise ValueError(f'Duplicate full annotation: {event_key}')
        format_keys = row['FORMAT'].split(':')
        if 'GT' not in format_keys:
            raise ValueError(f'Missing FORMAT/GT for {event_key}')
        gt_index = format_keys.index('GT')
        carriers = []
        for sample_id in samples:
            values = row[sample_id].split(':')
            if gt_index >= len(values):
                raise ValueError(f'Missing GT value for {event_key}, {sample_id}')
            if is_non_reference_gt(values[gt_index]):
                carriers.append(sample_id)
        recorded = set() if row['Samples_ID'] in MISSING_VALUES else set(filter(None, re.split('[,;]', row['Samples_ID'])))
        if set(carriers) != recorded:
            raise ValueError(f'GT carriers disagree with Samples_ID for {event_key}')
        full[event_key] = slim, carriers
    if set(splits) - set(full):
        raise ValueError('Split annotations without corresponding full rows')
    return samples, full, splits, enrich


CONSEQUENCE_FIELDS = [('Location', 'Location'), ('Location2', 'Region'),
                      ('Overlapped_CDS_length', 'CDS overlap (bp)'), ('Frameshift', 'AnnotSV frameshift'),
                      ('Dist_nearest_SS', 'Nearest splice-site distance (bp)')]
PHENOTYPE_FIELDS = [('Exomiser_gene_pheno_score', 'Exomiser phenotype score'),
                    ('Human_pheno_evidence', 'Human phenotype evidence'),
                    ('Mouse_pheno_evidence', 'Mouse phenotype evidence'),
                    ('Fish_pheno_evidence', 'Fish phenotype evidence')] + [
                   (field, field) for field in ('P_gain_hpo', 'P_loss_hpo', 'P_ins_hpo', 'po_P_gain_hpo', 'po_P_loss_hpo')]


def unique(seq):
    return list(dict.fromkeys(seq))


def consequence(row):
    parts = [f'{label}={row[field]}' for field, label in CONSEQUENCE_FIELDS if row[field] not in MISSING_VALUES]
    transcript = row['Tx'] + ('.' + row['Tx_version'] if row['Tx_version'] else '')
    return ((row['Gene_name'] or 'Unspecified gene') + (f' [{transcript}]' if transcript else '') + ': '
            + ('; '.join(parts) or 'Consequence not annotated'))


def annotations(row, enrich, genes):
    annotation = enrich.get((key(row), row['Gene_name'], row['Tx']), row)
    parts = ['In supplied ALS candidate-gene list'] if row['Gene_name'] in genes else []
    for field, label in [('GenCC_disease', 'GenCC ALS disease'), ('OMIM_phenotype', 'OMIM ALS phenotype')]:
        hits = [value for value in annotation[field].split(';') if re.search(r'amyotrophic|\bALS\b', value, re.I)]
        if hits:
            parts.append(label + '=' + '; '.join(hits))
    parts += [f'{label}={annotation[field]}' for field, label in PHENOTYPE_FIELDS
              if annotation.get(field, '') not in MISSING_VALUES]
    if not parts:
        return ''
    return (row['Gene_name'] + ': ' if row['Gene_name'] else '') + ' | '.join(parts)


def build_rows(samples, full, splits, enrich, genes):
    by_sample = {sample_id: [] for sample_id in samples}
    maxlen = 0
    for event_key, (annotation_row, carriers) in full.items():
        split_rows = splits.get(event_key, [])
        affected = '; '.join(unique(row['Gene_name'] for row in split_rows if row['Gene_name'])) or annotation_row['Gene_name'] or 'No overlapping gene annotated'
        consequences = ' || '.join(unique(consequence(row) for row in split_rows)) or 'No gene-level consequence annotated'
        annotation_text = ' || '.join(unique(value for row in (split_rows or [annotation_row]) if (value := annotations(row, enrich, genes)))) or 'No ALS/HPO annotation available in supplied sources'
        chrom = annotation_row['SV_chrom']
        info = dict(item.split('=', 1) for item in annotation_row['INFO'].split(';') if '=' in item)
        coordinates = f"GRCh38 chr{chrom}:{annotation_row['SV_start']}-{annotation_row['SV_end']}"
        partner = re.search(r'[\[\]]([^:\[\]]+):(\d+)[\[\]]', annotation_row['ALT'])
        if annotation_row['SV_type'] in {'BND', 'TRA'}:
            mate_chrom, mate_pos = partner.groups() if partner else (info.get('CHR2', chrom), info.get('END', annotation_row['SV_end']))
            coordinates = f"GRCh38 chr{chrom}:{annotation_row['SV_start']} <-> chr{mate_chrom.removeprefix('chr')}:{mate_pos}"
        row = [annotation_row['AnnotSV_ID'], coordinates, annotation_row['SV_type'],
               'Manta + TIDDIT (intersection)', affected, consequences, annotation_text]
        maxlen = max(maxlen, max(map(len, row)))
        for sample_id in carriers:
            by_sample[sample_id].append(row)
    return by_sample, maxlen


def write_table(output_path, by_sample):
    with output_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t')
        writer.writerow(TABLE_COLUMNS)
        for sample_id in sorted(by_sample):
            for row in sorted(by_sample[sample_id], key=lambda row: row[0]):
                writer.writerow([sample_id, *row])


def reconcile_table(output_path, by_sample):
    expected = Counter({sample_id: len(rows) for sample_id, rows in by_sample.items()})
    actual = Counter(dict.fromkeys(by_sample, 0))
    seen = set()
    with output_path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        if reader.fieldnames != TABLE_COLUMNS:
            raise ValueError('Unexpected participant table columns')
        for row in reader:
            token = row['Participant'], row['SV ID']
            if token in seen:
                raise ValueError(f'Duplicate participant/SV row: {token}')
            seen.add(token)
            actual[row['Participant']] += 1
    if dict(actual) != dict(expected):
        raise ValueError('Participant output counts disagree with input carriers')
    return actual


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('filtered', 'all'), default='all')
    parser.add_argument('--filtered-tsv', type=Path, default=FILTERED)
    parser.add_argument('--unfiltered-tsv', type=Path, default=UNFILTERED)
    parser.add_argument('--genes-file', type=Path, default=ROOT / 'data_sv_analysis_final/gene_lists/ALS_candidate_gene_list.txt')
    parser.add_argument('--out-dir', type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    mode = args.mode
    source = args.filtered_tsv if mode == 'filtered' else args.unfiltered_tsv
    genes = set(args.genes_file.read_text(encoding='utf-8-sig').split())
    samples, full, splits, enrich = load_annotations(source, args.filtered_tsv)
    by_sample, maxlen = build_rows(samples, full, splits, enrich, genes)
    out_dir = args.out_dir or ROOT / f'results_participant_intersection_table_{mode}'
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f'intersection_SVs_{len(samples)}_participants' + ('_filtered' if mode == 'filtered' else '')
    output_path = out_dir / (name + '.tsv')
    write_table(output_path, by_sample)
    actual = reconcile_table(output_path, by_sample)
    zero_samples = sorted(sample_id for sample_id in samples if not actual[sample_id])
    with (out_dir / (name + '.zero_sv_participants.tsv')).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t')
        writer.writerow(['Participant', 'Qualifying SV count'])
        writer.writerows((sample_id, 0) for sample_id in zero_samples)
    n = sum(actual.values())
    summary = dict(scope=mode, participants=len(samples), participants_with_SVs=len(samples)-len(zero_samples),
                   participants_without_SVs=len(zero_samples), zero_sv_participants=zero_samples,
                   cases=sum(sample_id.startswith('CASE-') for sample_id in samples),
                   controls=sum(sample_id.startswith('CTRL-') for sample_id in samples),
                   unique_SVs=len(full), participant_SV_rows=n, SVs_per_participant_min=min(actual.values(), default=0),
                   SVs_per_participant_max=max(actual.values(), default=0), duplicate_participant_SV_rows=0,
                   max_cell_characters=maxlen, output=str(output_path),
                   sources={str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in (source, args.filtered_tsv)},
                   participant_counts=dict(sorted(actual.items())))
    (out_dir / (name + '.validation.json')).write_text(json.dumps(summary, indent=2), encoding='utf-8')
    notes = f'''# Participant intersection SV table

The table contains {n:,} participant–SV records across all {len(samples)} participants ({summary['cases']} cases, {summary['controls']} controls), representing {len(full):,} distinct cohort SV records. One row represents one carrier and one AnnotSV SV ID. All requested eight columns are retained.

Source scope: {'filtered ALS candidate-gene intersection' if mode=='filtered' else 'all unfiltered intersection SVs, enriched with matching filtered-file phenotype annotations'}. Source files: {source.name} and {args.filtered_tsv.name}. Filtered records are matched using chromosome, start, end, type, original VCF ID, gene and transcript; they are not appended as additional variants.

Participants are identified from non-reference GT alleles and checked against Samples_ID. Full and split AnnotSV rows are collapsed into one participant–SV row; multiple gene/transcript annotations are separated with ||. SV ID is AnnotSV_ID. Coordinates preserve source SV_start/SV_end values without conversion; GRCh38 is recorded in the source run logs. Breakend partner positions are taken from ALT where available, otherwise INFO CHR2/END.

Caller support is Manta + TIDDIT based on the per-participant caller-intersection workflow. INFO SUPPORT is not interpreted as a caller count. No independent review of original read alignments was performed.

Predicted consequence preserves gene/transcript Location, Location2, CDS overlap, Frameshift and splice-site distance from AnnotSV; these are predictions, not experimentally established effects. Location2=CDS alone does not imply coding bases are disrupted: inspect CDS overlap and Location together.

ALS/HPO annotation reports membership of the supplied {len(genes)}-entry ALS candidate-gene list, ALS disease text from GenCC/OMIM, and available phenotype evidence and HPO fields. Filtered-file Exomiser scores use the common cohort HPO query documented in its run log; they are not participant-specific phenotypes. Human, mouse and fish evidence remain explicitly labelled. Candidate-list inclusion, a phenotype match, and model-organism evidence do not establish that an SV causes ALS. Missing annotation is labelled unavailable, not evidence of absence. No new external clinical interpretation was added.

Validation: {len(samples)} participants reconciled ({len(zero_samples)} with zero qualifying SVs, listed separately); carrier lists agree with genotypes; no duplicate participant–SV rows; output row counts reconciled to input. SHA-256 source hashes and participant counts are saved in the adjacent validation JSON.

{'This TSV exceeds the Excel worksheet limit of 1,048,576 rows. Use a TSV-capable analysis tool or import through Excel Power Query without loading the full table into one worksheet.' if n>1048575 else 'The TSV can be imported into Excel as tab-delimited UTF-8 text.'}
'''
    (out_dir / (name + ".README.md")).write_text(notes, encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key not in ("participant_counts", "sources")}, indent=2))


if __name__ == "__main__":
    main()
