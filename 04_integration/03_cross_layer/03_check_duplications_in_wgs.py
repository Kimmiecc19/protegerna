# Usage: python 03_check_duplications_in_wgs.py <participant ID>     # once per carrier
# Needs the carriers' CRAM files (controlled access) and the reference they were made with; neither is in
# the repository. Set WGS_REFERENCE and CRAM_DIR (CRAMs are found as $CRAM_DIR/<participant>/*/*.cram).
import pysam, sys, json, glob, os
REF=os.environ.get('WGS_REFERENCE', '/path/to/reference/GRCh38_full_analysis_set_plus_decoy_hla.fa')
CRAM_DIR=os.environ.get('CRAM_DIR', '/path/to/genomics/cram')
S={'CASE-NEUNZ171UYF':('chr7',105529287,105549105),'CASE-NEUWY079WUH':('chr8',143972014,144013736),
'CTRL-NEUJH928PGD':('chr10',100279771,100322438),'CTRL-NEUTZ821KW9':('chr14',105362256,105402606),
'CTRL-NEUMF196GPV':('chr17',18206397,18233819),'CASE-NEUUF613PHL':('chr17',702538,793182)}
p=sys.argv[1]; c,s,e=S[p]
hits=glob.glob(os.path.join(os.path.expanduser(CRAM_DIR), p, '*', '*.cram'))
if not hits: sys.exit(f'No CRAM found under {CRAM_DIR}/{p}/*/; set CRAM_DIR')
f=hits[0]
cr=pysam.AlignmentFile(f,'rc',reference_filename=REF)
def ok(r): return not (r.is_unmapped or r.is_secondary or r.is_supplementary or r.is_duplicate or r.is_qcfail) and r.mapping_quality>=20
def count(a,b):
    n=0
    for r in cr.fetch(c,max(a,0),b):
        if ok(r) and a<=r.reference_start<b: n+=1
    return n/(b-a)
L=e-s; fl=min(L,50000)
inside=count(s,e); left=count(s-fl-1000,s-1000); right=count(e+1000,e+fl+1000)
ratio=inside/((left+right)/2)
def rfc(a,b,W=1000):
    # outward-facing pairs: read near a on the reverse strand, mate near b on the forward strand
    n=0
    for r in cr.fetch(c,a-W,a+W):
        if ok(r) and r.is_paired and not r.mate_is_unmapped and r.next_reference_name==c and b-W<=r.next_reference_start<=b+W and r.is_reverse and not r.mate_is_reverse: n+=1
    return n
# control: outward-facing pairs counted between windows with the same spacing, shifted downstream by 2 x duplication length + 5 kb
ctrl=rfc(s+2*L+5000,e+2*L+5000)
rf=rfc(s,e)
W=1000; split=0; seen=set()
for r in cr.fetch(c,s-W,s+W):
    if not ok(r): continue
    if r.has_tag('SA'):
        for sa in r.get_tag('SA').split(';'):
            if not sa: continue
            ch,pos=sa.split(',')[:2]
            if ch==c and abs(int(pos)-e)<=W and r.query_name not in seen: split+=1; seen.add(r.query_name)
for r in cr.fetch(c,e-W,e+W):
    if ok(r) and r.has_tag('SA') and r.query_name not in seen:
        for sa in r.get_tag('SA').split(';'):
            if sa and sa.split(',')[0]==c and abs(int(sa.split(',')[1])-s)<=W: split+=1; seen.add(r.query_name); break
print(json.dumps({'participant':p,'region':f'{c}:{s}-{e}','len':L,'depth_inside':round(inside*150,1),'depth_flank':round((left+right)/2*150,1),'ratio':round(ratio,2),'outward_pairs':rf,'split_reads':split,'outward_pairs_shifted_control':ctrl}))
