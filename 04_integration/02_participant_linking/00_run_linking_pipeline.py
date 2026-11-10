#!/usr/bin/env python3
"""Run the Objective 4 integration pipeline end to end, pooled over quantms-diann/RNA batches (lib/paths.py BATCHES).

Stages (order matters; later stages read files written by earlier ones):
  1   01_link_peptides_to_events.py   peptide->event (E1), variant->event (E2), chains, novel peptides
  1b  02_extract_sv_carriers.py       PASS SVs carried by participants of the pooled batches
  2   03_link_svs_to_events.py        E2 + chains rebuilt with 'relation'/'rare' (overwrites stage-1 E2, chains, summary.json)
  (3  carrier_effect.py               REMOVED Oct 2026 - used strand-affected SUPPA PSI)
  4   04_test_rare_sv_rna_protein.py  SV carriers vs non-carriers: gene RNA + protein, evidence tiers
  5   05_permutation_null.py          carrier-label permutation null for stage 4

Input paths are set in lib/paths.py (resolved from this repository; the GTF is external); edit that file or set
OBJ4_<NAME> environment variables, not the stages.

Usage (from the 04_integration folder):
  python 02_participant_linking/00_run_linking_pipeline.py --check          # verify inputs and Python packages
  python 02_participant_linking/00_run_linking_pipeline.py --nperm 600      # full run -> 02_participant_linking/02_results_participant_linking/b1to6_<date>
  python 02_participant_linking/00_run_linking_pipeline.py --from-stage 4 --out <folder>   # resume
"""
import argparse, datetime as dt, hashlib, json, platform, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE
LIB = HERE.parent / 'lib'
sys.path.insert(0, str(LIB))
from paths import required_files, BATCHES
DEFAULT_RESULTS = HERE / '02_results_participant_linking'

STAGES = [  # (id, script, outputs it must produce)
    ('1',  '01_link_peptides_to_events.py',  ['novel_peptides_detected.tsv', 'links_peptide_event.tsv']),
    ('1b', '02_extract_sv_carriers.py',      ['sv_carriers.tsv']),
    ('2',  '03_link_svs_to_events.py',       ['links_variant_event.tsv', 'chains_variant_event_peptide.tsv', 'summary.json']),
    ('4',  '04_test_rare_sv_rna_protein.py', ['variant_gene_rna_protein.tsv', 'variant_gene_rna_protein_summary.json']),
    ('5',  '05_permutation_null.py',         ['permutation_null_summary.json']),
]
ORDER = [s[0] for s in STAGES]

def check():
    ok = True
    print('Inputs (edit lib/paths.py or set OBJ4_<NAME> to change):')
    for name, path in required_files().items():
        p = Path(path)
        found = p.exists()
        ok &= found
        print(f"  [{'ok' if found else 'MISSING'}] {name}: {p}")
    for mod in ('numpy', 'pandas', 'scipy'):
        try:
            m = __import__(mod); print(f'  [ok] python package {mod} {getattr(m, "__version__", "")}')
        except ImportError:
            ok = False; print(f'  [MISSING] python package {mod}  ->  pip install {mod}')
    for script in [SCRIPTS / s for _, s, _ in STAGES] + [LIB / f for f in ('rna_answerals.py', 'paths.py', 'common.py')]:
        if not script.exists():
            ok = False; print(f'  [MISSING] script {script}')
    return ok

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', help='output folder (default: 02_participant_linking/02_results_participant_linking/b<BATCHES>_<YYYYMMDD>)')
    ap.add_argument('--nperm', type=int, default=600, help='permutations for stage 5 (default 600, as in the feasibility run)')
    ap.add_argument('--from-stage', choices=ORDER, default='1', help='resume from this stage (needs earlier outputs in --out)')
    ap.add_argument('--to-stage', choices=ORDER, default='5', help='stop after this stage')
    ap.add_argument('--check', action='store_true', help='only check inputs and packages, then exit')
    a = ap.parse_args()

    out = Path(a.out).resolve() if a.out else DEFAULT_RESULTS / f"b{'to'.join([BATCHES[0].replace('batch', ''), BATCHES[-1].replace('batch', '')])}_{dt.date.today():%Y%m%d}"
    if not check():
        sys.exit('\nSome inputs are missing - set their paths in lib/paths.py (or OBJ4_<NAME>) before running.')
    if a.check:
        print('\nAll inputs found.'); return

    out.mkdir(parents=True, exist_ok=True)
    i0, i1 = ORDER.index(a.from_stage), ORDER.index(a.to_stage)
    if i0 == 0 and (out / 'links_peptide_event.tsv').exists():
        print(f'\nNote: {out} already has links_peptide_event.tsv; stage 1 will REUSE it (delete it to rebuild E1).')
    log_path = out / 'run.log'
    manifest = dict(batches=BATCHES, started_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), out=str(out),
                    python=sys.version.split()[0], platform=platform.platform(), command=' '.join(sys.argv),
                    nperm=a.nperm, stages=[], script_sha256={s: sha(SCRIPTS / s) for _, s, _ in STAGES})
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"\n===== run started {manifest['started_utc']} =====\n")
        for sid, script, expected in STAGES[i0:i1 + 1]:
            cmd = [sys.executable, str(SCRIPTS / script), str(out)] + ([str(a.nperm)] if sid == '5' else [])
            print(f'\n--- Stage {sid}: {script}'); log.write(f'\n--- Stage {sid}: {" ".join(cmd)}\n'); log.flush()
            t = time.time()
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            secs = round(time.time() - t, 1)
            print(r.stdout[-3000:]); log.write(r.stdout); log.write(f'[exit {r.returncode}, {secs}s]\n'); log.flush()
            missing = [f for f in expected if not (out / f).exists()]
            manifest['stages'].append(dict(stage=sid, script=script, exit=r.returncode, seconds=secs, missing_outputs=missing))
            if sid == '1' and (out / 'summary.json').exists():   # stage 2 overwrites summary.json - keep stage-1 version
                shutil.copy(out / 'summary.json', out / 'summary_stage1_feasibility.json')
            if r.returncode != 0 or missing:
                manifest['status'] = f'failed at stage {sid}'
                json.dump(manifest, open(out / 'run_manifest.json', 'w'), indent=2)
                sys.exit(f'\nStage {sid} failed (exit {r.returncode}, missing {missing}). See {log_path}. '
                         f'Fix and resume with: --from-stage {sid} --out "{out}"')
    manifest['status'] = 'completed'
    manifest['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    json.dump(manifest, open(out / 'run_manifest.json', 'w'), indent=2)
    print(f'\nDone. Results in {out}')

if __name__ == '__main__':
    main()
