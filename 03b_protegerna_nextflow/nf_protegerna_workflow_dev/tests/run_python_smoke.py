"""Run every pipeline stage through the task adapter on the synthetic fixture, without Nextflow."""
from pathlib import Path
import base64, csv, json, os, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/data/smoke'
RUNTIME=ROOT/'assets/proteogenomic_runtime'
DEFAULTS=json.loads((ROOT/'assets/resolved_publication_defaults.json').read_text())

def execute(folder, stage, payload):
    """Run one stage exactly as a Nextflow task does: adapter + base64 payload on stdin."""
    folder.mkdir(parents=True,exist_ok=True)
    shutil.copytree(RUNTIME,folder/'runtime',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    encoded=base64.b64encode(json.dumps(payload).encode())
    with (folder/'task.log').open('w') as log:
        result=subprocess.run([sys.executable,'-B','runtime/nextflow_adapter.py',stage],input=encoded,cwd=folder,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print((folder/'task.log').read_text()[-12000:])
        raise RuntimeError(f'{stage} failed: {folder / "task.log"}')
    print(f'PASS {stage}')

def run(out):
    out=out.resolve()
    execute(out/'db','gtfdb',dict(options={},inputs=dict(gtf=str(FIXTURE/'annotation.gtf')),process='CREATE_GENCODE_DB'))
    db=str(out/'db/gencode.gtf.db')
    references=dict(gtf_db=db,genome=str(FIXTURE/'genome.fa'),reference_proteome=str(FIXTURE/'reference.fa'))
    execute(out/'validate','validate',dict(options=DEFAULTS['validate'],inputs={k:v for k,v in references.items() if k!='reference_proteome'}|dict(gencode_protein_fasta=str(FIXTURE/'gencode.fa')),process='VALIDATE',cpus=1))
    gate=json.loads((out/'validate/gencode_translation_concordance.json').read_text())
    execute(out/'cache','cache',dict(options=dict(min_peptide_length=7,max_peptide_length=40,max_missed_cleavages=3),inputs=dict(reference_proteome=str(FIXTURE/'reference.fa')),process='CACHE',cpus=1))
    references['reference_peptide_cache']=str(out/'cache/reference_tryptic_peptides.cache')
    rows=list(csv.DictReader((FIXTURE/'samplesheet.csv').open()))
    modules=['fusion','rmats','suppa']
    for stage in modules:
        selected=[row for row in rows if row['tool']==stage]
        options=DEFAULTS[stage]|dict(annotation_release='GENCODE_46',organism='Homo_sapiens',workers=1)
        execute(out/stage,stage,dict(options=options,inputs=references,process=stage,cpus=1,rows=selected,files=[str(FIXTURE/row['path']) for row in selected]))
    options=DEFAULTS['merge']|dict(annotation_release='GENCODE_46',organism='Homo_sapiens')
    execute(out/'merge','merge',dict(options=options,inputs=dict(inputs=[str(out/stage/f'{stage}.primary.fasta') for stage in modules],reference_fasta=[str(FIXTURE/'reference.fa')],gencode_concordance_summary=str(out/'validate/gencode_translation_concordance.json')),process='MERGE',cpus=1))
    execute(out/'qc','qc',dict(options=DEFAULTS['qc'],inputs=dict(fasta=[str(out/'merge/proteogenomic_database.fasta')],metadata=[str(out/'merge/proteogenomic_metadata.tsv')],reference_proteome=str(FIXTURE/'reference.fa')),process='QC',cpus=1))
    counts={stage:(out/stage/f'{stage}.primary.fasta').read_text().count('>') for stage in modules}
    counts['merged']=(out/'merge/proteogenomic_database.fasta').read_text().count('>')
    if any(counts[stage]<1 for stage in modules) or counts['merged']<3:
        raise AssertionError(f'Smoke fixture must exercise retained variants: {counts}')
    versions_dir=out/'versions'
    for i,stage in enumerate(['db','validate','cache','fusion','rmats','suppa','merge','qc'],1):
        destination=versions_dir/f'versions{i:04d}'
        destination.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(out/stage/'versions.yml',destination/'versions.yml')
    execute(versions_dir,'versions',{})
    assert len(json.loads((versions_dir/'software_versions.yml').read_text()))==8
    print(json.dumps(counts,sort_keys=True))
    (out/'result.json').write_text(json.dumps({'fasta_records':counts,'concordance':gate},indent=2)+'\n')

if __name__=='__main__':
    run(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'testing/python_smoke')
