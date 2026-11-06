"""Run two copies of rmatstoprotein.py on identical synthetic inputs and compare every output byte.

    python tests/differential/compare_rmats.py --old ../code_proteogenomic_database_v6 \
        --new . --workdir /tmp/rmats_diff --seeds 11 23 37 51

Each seed generates a synthetic genome, GTF and SE/A3SS/A5SS/MXE/RI tables
(gen_rmats_fixture.py); each is run under five option sets. Run configs are
compared after removing directory-specific paths and the hash over them.
"""
import argparse, filecmp, json, shutil, subprocess, sys
from pathlib import Path
import gffutils
cli = argparse.ArgumentParser()
cli.add_argument('--old', type=Path, required=True)
cli.add_argument('--new', type=Path, required=True)
cli.add_argument('--workdir', type=Path, required=True)
cli.add_argument('--seeds', type=int, nargs='+', default=[11, 23, 37, 51])
opts = cli.parse_args()
OLD, NEW, ROOT = opts.old.resolve(), opts.new.resolve(), opts.workdir.resolve()
GENERATOR = Path(__file__).resolve().with_name('gen_rmats_fixture.py')
COMBOS = {
    'cli_defaults': [],
    'publication_v5': ['--max_fdr', '1.0', '--min_abs_inc_level_difference', '0.0',
                       '--min_inclusion_junction_reads', '3', '--min_skipping_junction_reads', '3',
                       '--min_ri_inclusion_reads', '3', '--no-quantms_conservative',
                       '--exclude_nmd_from_dia', '--exclude_start_loss_from_dia', '--require_ri_orf_preserved',
                       '--include_failed_filter_proteins', '--require_unique_event_peptide', '--no-exclude_ri_nmd_from_primary'],
    'exploratory': ['--allow_alt_start', '--allow_longest_orf', '--alternative_start_codons', 'ATG', 'CTG', 'GTG',
                    '--short_junction_peptides', '--no-quantms_conservative', '--no-rmats_conservative_event_filter',
                    '--pad_partial_codons', '--include_failed_filter_proteins'],
    'permissive': ['--no-quantms_conservative', '--no-rmats_conservative_event_filter', '--no-exclude_incomplete_cds',
                   '--no-require_ri_read_evidence', '--no-require_ri_junction_peptide', '--exclude_frameshift_from_dia',
                   '--exclude_premature_stop_from_dia', '--min_ri_inclusion_reads', '1'],
    'strict_ri': ['--exclude_ri_nmd_from_primary', '--min_ri_inclusion_reads', '10', '--require_unique_event_peptide',
                  '--allow_alt_start', '--short_junction_peptides'],
}
OUTPUT_FLAGS = {'--allow_alt_start': ('--out_alt_start_prot_fa', 'alt.fasta'),
                '--allow_longest_orf': ('--out_exploratory_orf_fa', 'orf.fasta'),
                '--short_junction_peptides': ('--out_junc_fa', 'junc.fasta')}

def run(code, fixture, combo, args, out):
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(code / 'rmatstoprotein.py'), '--gtf_db', str(fixture / 'annotation.db'),
            '--genome', str(fixture / 'genome.fa'), '--reference_proteome', str(fixture / 'reference.fa'),
            '--annotation_release', 'SYN_1', '--organism', 'Synthetic',
            '--out_prot_fa', str(out / 'primary.fasta'), '--out_consequence_tsv', str(out / 'consequences.tsv'),
            '--out_event_summary_tsv', str(out / 'events.tsv'), '--workers', '1']
    for kind in ('se', 'a3ss', 'a5ss', 'mxe', 'ri'):
        cmd += [f'--{kind}_files', str(fixture / 'CASE-CTRL' / f'{kind.upper()}.MATS.JC.txt')]
    cmd += args
    for flag, (opt, name) in OUTPUT_FLAGS.items():
        if flag in args:
            cmd += [opt, str(out / name)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=out)
    (out / 'stderr.log').write_text(result.stdout + result.stderr)
    return result.returncode

def normalised(path, out):
    data = json.loads(path.read_text().replace(str(out), 'OUT'))
    data.pop('configuration_sha256', None)  # hash over the (directory-specific) arguments
    return data

summary = []
shutil.rmtree(ROOT, ignore_errors=True)
for seed in opts.seeds:
    fixture = ROOT / f'fixture_{seed}'
    subprocess.run([sys.executable, str(GENERATOR), str(fixture), str(seed)], check=True)
    gffutils.create_db(str(fixture / 'annotation.gtf'), dbfn=str(fixture / 'annotation.db'), force=True,
                       keep_order=True, merge_strategy='merge', sort_attribute_values=True)
    for combo, args in COMBOS.items():
        outs = {}
        for label, code in (('old', OLD), ('new', NEW)):
            outs[label] = ROOT / f'{seed}_{combo}_{label}'
            rc = run(code, fixture, combo, args, outs[label])
            outs[label + '_rc'] = rc
        old_files = sorted(p.name for p in outs['old'].iterdir() if p.is_file() and p.name != 'stderr.log')
        new_files = sorted(p.name for p in outs['new'].iterdir() if p.is_file() and p.name != 'stderr.log')
        diffs = [n for n in old_files if n in new_files and not n.endswith('run_config.json')
                 and not filecmp.cmp(outs['old'] / n, outs['new'] / n, shallow=False)]
        diffs += [n for n in old_files if n.endswith('run_config.json')
                  and normalised(outs['old'] / n, outs['old']) != normalised(outs['new'] / n, outs['new'])]
        rows = sum(1 for _ in open(outs['old'] / 'consequences.tsv')) - 1 if (outs['old'] / 'consequences.tsv').exists() else 0
        fasta = sum(l.startswith('>') for l in open(outs['old'] / 'primary.fasta')) if (outs['old'] / 'primary.fasta').exists() else 0
        summary.append(dict(seed=seed, combo=combo, rc=(outs['old_rc'], outs['new_rc']), files=len(old_files),
                            same_file_set=old_files == new_files, differing=diffs, audit_rows=rows, primary_proteins=fasta))
for s in summary:
    print(json.dumps(s))
ok = all(s['rc'][0] == s['rc'][1] == 0 and s['same_file_set'] and not s['differing'] for s in summary)
print('ALL IDENTICAL' if ok else 'DIFFERENCES FOUND')
sys.exit(0 if ok else 1)
