# Building `nf-core/rnafusion` References

## Automatically Build References with `nf-core`

Use the `--build_references` flag to trigger a parallel workflow that builds all references, which is **required** before running the pipeline.

```bash
nextflow run nf-core/rnafusion \
  --build_references --all \
  --cosmic_username <EMAIL> --cosmic_passwd <PASSWORD> \
  --genomes_base <PATH/TO/REFERENCES> \
  --outdir <PATH/TO/REFERENCES>
```

> ⚠️ **NOTE:**
>
> 1. Reference building is not supported on **CHPC** – build them elsewhere and transfer.
> 2. Reference building on **hemera** often fails due to data intensity, especially for **STAR-Fusion**.

---

## Manually Building References (version < 4.0.0)

According to [`nf-core/rnafusion`](https://github.com/nf-core/rnafusion), you need the following:

1. Download Ensembl FASTA and GTF files
2. Create a STAR index
3. Download **Arriba** references
4. Download **FusionCatcher** references
5. Download and build **STAR-Fusion** references
6. Download **fusion-report** databases

---

## COSMIC Database

* [COSMIC Download Page](https://cancer.sanger.ac.uk/cosmic/download/cosmic)
* Account reactivated: 6 June 2025
* Register using your university email at: [COSMIC Registration](https://cancer.sanger.ac.uk/cosmic/register)

> The account is activated only after clicking the confirmation link in your email.

---

## Ensembl FASTA & GTF Files

```text
FASTA: https://ftp.ensembl.org/pub/current_fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz  
GTF:   https://ftp.ensembl.org/pub/current_gtf/homo_sapiens/Homo_sapiens.GRCh38.114.gtf.gz
```

---

## STAR Index

* [STAR Manual (PDF)](https://github.com/alexdobin/STAR/blob/master/doc/STARmanual.pdf)
* [Publication](https://www.ncbi.nlm.nih.gov/pubmed/23104886)

```bash
# Download STAR
wget https://github.com/alexdobin/STAR/archive/2.7.11b.tar.gz
tar -xzf 2.7.11b.tar.gz
cd STAR-2.7.11b

# Or clone via Git
git clone https://github.com/alexdobin/STAR.git
cd STAR/source
make STAR
```

---

## Arriba

* [Arriba GitHub](https://github.com/suhrig/arriba)
* [Arriba Wiki](https://github.com/suhrig/arriba/wiki/01-Home)
* Uhrig *et al.*, Genome Res. 2021 [DOI:10.1101/gr.257246.119](https://doi.org/10.1101/gr.257246.119)

> ⚠️ **Do not use `git clone`**, as it excludes the blacklist.

```bash
wget https://github.com/suhrig/arriba/releases/download/v2.5.0/arriba_v2.5.0.tar.gz
tar -xzf arriba_v2.5.0.tar.gz
cd arriba_v2.5.0 && make
```

---

## FusionCatcher

* [FusionCatcher GitHub](https://github.com/ndaniel/fusioncatcher)
* [Manual](https://github.com/ndaniel/fusioncatcher/blob/master/doc/manual.md)
* Nicorici *et al.*, bioRxiv, 2014 [DOI:10.1101/011650](https://doi.org/10.1101/011650)

> ⚠️ Reference build is only supported for **Ensembl v102**.

### Install & Download Options

#### Method 1: Python Bootstrap

```bash
wget http://sf.net/projects/fusioncatcher/files/bootstrap.py -O bootstrap.py
python bootstrap.py -t --download
```

#### Method 2: Conda

```bash
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
conda create -n fusioncatcher fusioncatcher
source activate fusioncatcher
download-human-db.sh
```

#### Method 3: GitHub Clone

```bash
git clone https://github.com/ndaniel/fusioncatcher
cd fusioncatcher/tools/
./install_tools.sh
cd ../data
./download-human-db.sh
```

---

## STAR-Fusion

* [STAR-Fusion GitHub](https://github.com/STAR-Fusion/STAR-Fusion)
* [Manual](https://github.com/STAR-Fusion/STAR-Fusion/wiki)
* [Haas *et al.*, Genome Biol. 2019](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-019-1842-9)

### Download & Install

#### Option 1: Recommended (FULL release with submodules)

```bash
wget https://github.com/STAR-Fusion/STAR-Fusion/releases/download/STAR-Fusion-v1.15.0/STAR-Fusion.v1.15.0.FULL.tar.gz
tar -xzf STAR-Fusion.v1.15.0.FULL.tar.gz
cd STAR-Fusion.v1.15.0
make
```

#### Option two: From GitHub Clone

```bash
git clone --recursive https://github.com/STAR-Fusion/STAR-Fusion.git
cd STAR-Fusion
make
```

> `--recursive` is **required** to fetch submodules.

### Option three: Singularity Image

```bash
singularity pull https://data.broadinstitute.org/Trinity/CTAT_SINGULARITY/STAR-Fusion/star-fusion.v1.15.0.simg
```

---

## CTAT Genome Lib

### Download & Unpack

```bash
wget https://data.broadinstitute.org/Trinity/CTAT_RESOURCE_LIB/GRCh38_gencode_v44_CTAT_lib_Oct292023.plug-n-play.tar.gz
tar xvf CTAT_resource_lib.tar.gz
```

> **Important:** Remember to update `AnnotFilterRule.pm` for proper filtering.

### Rebuild CTAT Indices

#### Local

```bash
cd /path/to/your/ctat_genome_lib_build_dir
/path/to/STAR-Fusion/ctat-genome-lib-builder/util/rebuild_indices.pl . # Don't forget the dot!
```

#### Singularity

```bash
cd /path/to/your/ctat_genome_lib_build_dir
singularity exec -e STAR-Fusion.simg /usr/local/src/STAR-Fusion/ctat-genome-lib-builder/util/rebuild_indices.pl . # Don't forget the dot!
```

---

## Fusion-report

* [Fusion-report GitHub](https://github.com/Clinical-Genomics/fusion-report)
* Documentation: *Unavailable* ([broken link](https://matq007.github.io/fusion-report/))

### Install via Conda

```bash
conda install -c bioconda fusion-report=2.1.4
```

---

## Extra

1. HGNC (Gene Symbols)

  [HGNC Download Page](https://www.genenames.org/download/)

  > Complete set old TSV   ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt
  > Complete set new TSV   storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt

1. convert2bed: Homo_sapiens.GRCh38.102.bed

2. rrna: Homo_sapiens.GRCh38.102_rrna_intervals.gtf

3. GATK: Homo_sapiens.GRCh38.102.all.dict

---

## Manually Building References (version 4.0.0)

Download the references from the S3 bucket (recommended)

> Important: this has to be done with each new release

```bash
conda activate whatever_env

# https://github.com/aws/aws-cli
pip install awscli 

aws --no-sign-request s3 sync s3://nf-core-awsmegatests/rnafusion/references/ <path_to_references>
```

The `<path_to_references>` can then be provided to the pipeline with the --genomes_base parameter.

---
