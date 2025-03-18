# Tips for Common RNAfusion Problems
##  This markdown document provides tips and solutions for common problems encountered with RNAfusion pipelines.


## Rebuild Indices

### Error: Missing Output Files

If you encounter the following error message:

```
Error executing process > 'NFCORE_RNAFUSION:RNAFUSION:FUSIONREPORT_WORKFLOW:FUSIONREPORT (ERR315432)'
Caused by:
  Missing output file(s) `*_*.html` expected by process `NFCORE_RNAFUSION:RNAFUSION:FUSIONREPORT_WORKFLOW:FUSIONREPORT (ERR315432)`

OR

Fatal INPUT FILE error, no valid exon lines in the GTF file: Homo_sapiens.GRCh38.102.chr.gtf
  Solution: check the formatting of the GTF file. One likely cause is the difference in chromosome naming between GTF and FASTA file.
```

#### Command executed:

```bash
fusion_report run ERR315432 . fusion_report_db --allow-multiple-gene-symbols --export csv --tool-cutoff 2
mv fusion_list.tsv ERR315432.fusionreport.tsv
mv fusion_list_filtered.tsv ERR315432.fusionreport_filtered.tsv
[ ! -f fusions.csv ] || mv fusions.csv ERR315432.fusions.csv
[ ! -f fusions.json ] || mv fusions.json ERR315432.fusions.json

cat <<-END_VERSIONS > versions.yml
"NFCORE_RNAFUSION:RNAFUSION:FUSIONREPORT_WORKFLOW:FUSIONREPORT":
    fusion_report: $(fusion_report --version | sed 's/fusion-report //')
    fusion_report DB retrieval: $(cat fusion_report_db/DB-timestamp.txt)
END_VERSIONS

OR

Command error:
        STAR --genomeDir star --readFilesIn input1/CASE-NEUAF553MJ3-5884-T_P96_1.fastq.gz input2/CASE-NEUAF553MJ3-5884-T_P96_2.fastq.gz --runThreadN 10 --outFileNamePrefix CASE-NEUAF553MJ3-5884-T. --sjdbGTFfile Homo_sapiens.GRCh38.102.chr.gtf --outSAMattrRGline ID:CASE-NEUAF553MJ3-5884-T SM:CASE-NEUAF553MJ3-5884-T --twopassMode Basic --outReadsUnmapped None --readFilesCommand zcat --outSAMtype BAM SortedByCoordinate --outSAMstrandField intronMotif --outSAMunmapped Within --chimSegmentMin 12 --chimJunctionOverhangMin 8 --chimOutJunctionFormat 1 --alignSJDBoverhangMin 10 --alignMatesGapMax 100000 --alignIntronMax 100000 --alignSJstitchMismatchNmax 5 -1 5 5 --chimMultimapScoreRange 3 --chimScoreJunctionNonGTAG -4 --chimMultimapNmax 20 --chimNonchimScoreDropMin 10 --peOverlapNbasesMin 12 --peOverlapMMp 0.1 --alignInsertionFlush Right --alignSplicedMateMapLminOverLmate 0 --alignSplicedMateMapLmin 30 --chimOutType Junctions --quantMode GeneCounts
        STAR version: 2.7.10a   compiled: 2022-01-14T18:50:00-05:00 :/home/dobin/data/STAR/STARcode/STAR.master/source
  Mar 17 09:52:46 ..... started STAR run
  Mar 17 09:52:46 ..... loading genome
  Mar 17 09:53:15 ..... processing annotations GTF
```

#### Solution:

First, check if it is a memory issue (because of error 104). Try adding the following to the config file (depending on the error):
```bash
process {
    withName: 'NFCORE_RNAFUSION:RNAFUSION:STARFUSION_WORKFLOW:STAR_FOR_STARFUSION' {
        memory = 200.GB  // Increase this value as needed
    }
}
```

If that doesn't work...

Rebuilding indices may resolve this issue. Visit [this link](https://github.com/STAR-Fusion/STAR-Fusion/wiki/rebuild_ctat_genome_lib_indices) for more details.

---

### Error: Missing File

If you encounter the following error message:

```
ERROR:
Command exit status:
  2
Command output:
  (empty)
Command error:
  ** Error, not able to find file: fusion_annot_lib.idx **  at /usr/local/src/STAR-Fusion/util/validate_ctat_genome_lib.pl line 28.
```

#### Solution:

You may need to rebuild the CTAT genome library indices. Visit [this link](https://github.com/STAR-Fusion/STAR-Fusion/wiki/rebuild_ctat_genome_lib_indices) for detailed instructions.

---

### Rebuilding CTAT Genome Library Indices

To rebuild the indices locally using STAR-Fusion and ctat_genome_lib:

1. Download the latest STAR-Fusion release from [here](https://github.com/STAR-Fusion/STAR-Fusion/releases). OR https://data.broadinstitute.org/Trinity/CTAT_SINGULARITY/STAR-Fusion/star-fusion.v1.13.0.simg (singularity image seems to work better)

2. Go to STAR-Fusion directory and run make

3. Download the CTAT genome library files:
   - [GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz](https://data.broadinstitute.org/Trinity/CTAT_RESOURCE_LIB/GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz)

4. Verify the integrity of the downloaded files using their MD5 checksums.

5. Unpack the data resources and index them as follows:

```bash
tar xvf GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz

# Change directory to the CTAT genome lib dir:
cd /path/to/your/GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play/ctat_genome_lib_build_dir/

# Rebuild the indices:
${STAR_Fusion_BASEDIR}/ctat-genome-lib-builder/util/rebuild_indices.pl .
OR
singularity exec -e star-fusion.v1.13.0.simg STAR-Fusion.v1.14.0/ctat-genome-lib-builder/util/rebuild_indices.pl .
```
Don't forget the final dot in the rebuild command!
This step will take several minutes

```





