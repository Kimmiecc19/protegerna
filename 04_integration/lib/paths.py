r"""Input paths and shared loaders for the Objective 4 integration pipeline (13_run_objective4.py, stages 13a-13e).

The pipeline pools the batches listed in BATCHES (RNA batch N and quantms-diann batch N contain the same participants).

Edit the values below if a file lives elsewhere, or override any of them for one run with an environment
variable called OBJ4_<NAME>, e.g.  OBJ4_GTF=/path/to/genes.gtf python 13_run_objective4.py --check
Batches can be overridden with OBJ4_BATCHES="batch4 batch5 batch6" (default: batch1 through batch6).

DIA-NN runs listed in EXCLUDE_RUNS (the same TSV given to 05_consolidate_cohort.py --exclude-runs; columns
batch, file_name, reason) are dropped from the precursor and protein matrices. Set OBJ4_EXCLUDE_RUNS= (empty) to disable.

"""
import glob, os, re

HOME = '/home/kcoetzer'
O4 = f'{HOME}/objective_four'
BATCHES = os.environ.get('OBJ4_BATCHES', 'batch1 batch2 batch3 batch4 batch5 batch6').split()
CONTROL_LINE = 'CTRL-NEUEU392AE8'          # technical control line, excluded from participant-level tests

PATHS = dict(
    # Objective 2: OctopuSV Manta+TIDDIT intersection cohort VCF
    SV_VCF=f'{HOME}/objective_two/octopusv/octopusv_merged_02092026/merged/manta_tiddit.intersect.cohort.vcf',
    # Objective 3: v5 proteogenomic database folder (metadata, mapping, fusion.* tables)
    PGDB=f'{HOME}/proteogenomic_database/results/results_proteogenomic_database_with_errors/pgdb_publication_rerun_v5',
    # nf-core/rnafusion results: folder containing rnafusion_analysis_batch1..6 (each with fusioncatcher/)
    RNAFUS_ROOT=f'{HOME}/nf/nf_results/rnafusion/rnafusion_analysis',
    # AnswerALS release 7 raw counts
    COUNTS=f'{O4}/data_ALS_integration/4_matrix_transcriptomics_answerals/AnswerALS-1276-T-v1-release7_raw-counts.csv',
    # ---- SET ME: not in the listings you sent ----
    GTF=f'{HOME}/proteogenomic_database/data/Homo_sapiens_GRCh38_46.gtf',                       # GENCODE v46 / Ensembl 112 GTF
        UNIPROT_REF=f'{HOME}/proteogenomic_database/data/UP000005640_9606.fasta.gz',                   # UniProt canonical proteome
        UNIPROT_ISO=f'{HOME}/proteogenomic_database/data/UP000005640_9606_additional.fasta.gz',             # UniProt isoforms (or varsplice)
    # folder containing pgdb_v5_batch1/ ... pgdb_v5_batch6/ (each with quant_tables/); same location as the
    # cohort_batches_1-6.tsv manifest used by 05_consolidate_cohort.py (was .../pgdb/results_quantmsdiann_pgdb for batches 4-6)
    DIA_ROOT=f'{HOME}/nf/nf_results/quantms/pgdb',
    # failed DIA-NN runs (same file as 05_consolidate_cohort.py --exclude-runs); '' = exclude nothing
    EXCLUDE_RUNS=f'{O4}/data_ALS_integration/data_consolidate_quantms/cohort_exclude_runs_1-6.tsv',
)
for _k in PATHS:
    PATHS[_k] = os.environ.get(f'OBJ4_{_k}', PATHS[_k])

def rnafus_dir(batch):
    return os.path.join(PATHS['RNAFUS_ROOT'], f'rnafusion_analysis_{batch}')

def dia_file(batch, kind):
    """kind = 'pr' (precursors) or 'pg' (protein groups)."""
    return os.path.join(PATHS['DIA_ROOT'], f'pgdb_v5_{batch}', 'quant_tables', f'diann_report.{kind}_matrix.tsv')

def excluded_runs():
    """{(batch, mzML file name)} of failed DIA-NN runs to drop (empty if EXCLUDE_RUNS is unset)."""
    if not PATHS['EXCLUDE_RUNS']:
        return set()
    import csv
    with open(PATHS['EXCLUDE_RUNS'], encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    if rows and not {'batch', 'file_name', 'reason'} <= set(rows[0]):
        raise ValueError(f"{PATHS['EXCLUDE_RUNS']}: needs columns batch, file_name, reason")
    return {(r['batch'], r['file_name']) for r in rows}

def dia_runs(batch, columns):
    """Run columns of a DIA-NN matrix to use: mzML runs, minus the technical control line and excluded runs.
    Raises if an excluded run of this batch is not among the columns (catches name mismatches)."""
    drop = {f for b, f in excluded_runs() if b == batch}
    runs = [c for c in columns if str(c).endswith('mzML')]
    names = {re.split(r'[\\/]', str(c))[-1] for c in runs}
    if drop - names:
        raise ValueError(f'Excluded runs not found in {batch} DIA-NN matrix: {sorted(drop - names)}')
    return [c for c in runs if CONTROL_LINE not in c and re.split(r'[\\/]', str(c))[-1] not in drop]

def rna_samples():
    """RNA sample IDs (without -T suffix) with FusionCatcher output in the pooled batches."""
    out = set()
    for b in BATCHES:
        for f in glob.glob(os.path.join(rnafus_dir(b), 'fusioncatcher', '*')):
            out.add(re.sub(r'-T$', '', os.path.basename(f).split('.')[0]))
    return sorted(out)

def load_protein_by_gene():
    """Participant-level protein abundance (gene x participant), pooled over BATCHES.
    log2 PG.MaxLFQ from each batch's pg_matrix, protein groups mapped to genes through the v5 PGDB metadata
    (batch 4's DIA-NN run annotated no gene names), unambiguous genes only, median-centred per run,
    runs of one participant averaged, technical control line excluded."""
    import numpy as np, pandas as pd
    meta = pd.read_csv(os.path.join(PATHS['PGDB'], 'proteogenomic_metadata.tsv'), sep='\t', dtype=str, usecols=['sequence_id', 'gene'])
    id2gene = dict(zip(meta.sequence_id, meta.gene))
    def pg_gene(pg):
        g = {id2gene.get(i) for i in re.findall(r'PGDB_U\d+', str(pg))} - {None, 'NA', ''}
        return g.pop() if len(g) == 1 else None
    mats = []
    for b in BATCHES:
        pg = pd.read_csv(dia_file(b, 'pg'), sep='\t', low_memory=False)
        runs = dia_runs(b, pg.columns)
        m = pg[runs].apply(pd.to_numeric, errors='coerce')
        m[m <= 0] = np.nan
        m = np.log2(m); m = m - m.median()
        m.index = [pg_gene(x) for x in pg['Protein.Group']]
        m = m[m.index.notna()].groupby(level=0).mean()
        m.columns = [part(c) for c in m.columns]
        mats.append(m.T.groupby(level=0).mean().T)
    return pd.concat(mats, axis=1)


DESCRIPTIONS = dict(SV_VCF='SV cohort VCF (OctopuSV Manta+TIDDIT intersection)', PGDB='Proteogenomic database v5 folder',
                    COUNTS='AnswerALS raw counts (release 7)', GTF='GENCODE/Ensembl GTF',
                    UNIPROT_REF='UniProt reference FASTA', UNIPROT_ISO='UniProt isoform FASTA')

def required_files():
    """Every file/folder the stages read, for the --check step."""
    p = PATHS
    req = {DESCRIPTIONS['SV_VCF']: p['SV_VCF'], DESCRIPTIONS['PGDB']: p['PGDB']}
    for f in ('proteogenomic_metadata.tsv', 'proteogenomic_mapping.tsv', 'fusion.metadata.tsv', 'fusion.sequence_samples.tsv'):
        req[f'PGDB {f}'] = os.path.join(p['PGDB'], f)
    req[DESCRIPTIONS['COUNTS']] = p['COUNTS']
    for k in ('GTF', 'UNIPROT_REF', 'UNIPROT_ISO'):
        req[DESCRIPTIONS[k]] = p[k]
    if p['EXCLUDE_RUNS']:
        req['Failed DIA-NN runs to exclude'] = p['EXCLUDE_RUNS']
    for b in BATCHES:
        req[f'rnafusion {b} / fusioncatcher'] = os.path.join(rnafus_dir(b), 'fusioncatcher')
        req[f'DIA-NN precursor matrix, v5 {b}'] = dia_file(b, 'pr')
        req[f'DIA-NN protein-group matrix, v5 {b}'] = dia_file(b, 'pg')
    return req
