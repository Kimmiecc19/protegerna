#!/usr/bin/env python3
"""Cache PASS SV records carried by pooled-batch participants from the OctopuSV
Manta+TIDDIT intersection cohort VCF, with cohort-wide carrier counts. Usage: 02_extract_sv_carriers.py OUT"""
import sys, os, csv
OUT = sys.argv[1]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from common import part
from paths import PATHS as C, CONTROL_LINE, rna_samples as pooled_rna_samples
participants = {part(s) for s in pooled_rna_samples()} - {None, CONTROL_LINE}
vcf = C['SV_VCF']
with open(vcf) as f, open(os.path.join(OUT, 'sv_carriers.tsv'), 'w', newline='') as o:
    w = csv.writer(o, delimiter='\t')
    w.writerow(['participant', 'sv_id', 'chrom', 'pos', 'end', 'chr2', 'svtype', 'svlen', 'n_cohort_carriers', 'gt'])
    for l in f:
        if l.startswith('##'): continue
        t = l.rstrip('\n').split('\t')
        if l.startswith('#'):
            cols = [part(c) for c in t[9:]]; keep = {i for i, c in enumerate(cols) if c in participants}; continue
        if t[6] != 'PASS': continue
        gts = [g.split(':', 1)[0] for g in t[9:]]
        car = [i for i, g in enumerate(gts) if g not in ('0/0', './.', '.', '0|0')]
        if not any(i in keep for i in car): continue
        info = dict(x.split('=', 1) for x in t[7].split(';') if '=' in x)
        for i in car:
            if i in keep:
                w.writerow([cols[i], t[2], t[0], t[1], info.get('END', t[1]), info.get('CHR2', t[0]), info.get('SVTYPE'), info.get('SVLEN', ''), len(car), gts[i]])
print('done')
