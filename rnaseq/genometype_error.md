# Error with GenomeType during STAR_ALIGN

```
ERROR ~ Error executing process > 'NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN_IGENOMES (SRR10202022)'

Caused by:
  Process `NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN_IGENOMES (SRR10202022)` terminated with an error exit status (102)

Command executed:

  STAR \
      --genomeDir star_index_2.7.11b \
      --readFilesIn SRR10202022_1_val_1.fq.gz SRR10202022_2_val_2.fq.gz  \
      --runThreadN 12 \
      --outFileNamePrefix SRR10202022. \
       \
      --sjdbGTFfile genome.filtered.gtf \
      --outSAMattrRGline ID:SRR10202022 'SM:SRR10202022'   \
      --quantMode TranscriptomeSAM --twopassMode Basic --outSAMtype BAM Unsorted --readFilesCommand zcat --runRNGseed 0 --outFilterMultimapNmax 20 --alignSJDBoverhangMin 1 --outSAMattributes NH HI AS NM MD --quantTranscriptomeBan Singleend --outSAMstrandField intronMotif



  if [ -f SRR10202022.Unmapped.out.mate1 ]; then
      mv SRR10202022.Unmapped.out.mate1 SRR10202022.unmapped_1.fastq
      gzip SRR10202022.unmapped_1.fastq
  fi
  if [ -f SRR10202022.Unmapped.out.mate2 ]; then
      mv SRR10202022.Unmapped.out.mate2 SRR10202022.unmapped_2.fastq
      gzip SRR10202022.unmapped_2.fastq
  fi

  cat <<-END_VERSIONS > versions.yml
  "NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN_IGENOMES":
      star: $(STAR --version | sed -e "s/STAR_//g")
      samtools: $(echo $(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*$//')
      gawk: $(echo $(gawk --version 2>&1) | sed 's/^.*GNU Awk //; s/, .*$//')
  END_VERSIONS

Command exit status:
  102

Command output:
  Feb 23 12:43:21 ..... started STAR run
  Feb 23 12:43:21 ..... loading genome

Command error:
  WARNING: Skipping mount /opt/spack/opt/spack/linux-ubuntu22.04-icelake/gcc-11.4.0/apptainer-1.1.9-d4ijqkq2sll3iknqos3gvgu4n4n447ow/var/apptainer/mnt/session/etc/resolv.conf [files]: /etc/resolv.conf doesn't exist in container
  Feb 23 12:43:21 ..... started STAR run
  Feb 23 12:43:21 ..... loading genome

  EXITING: FATAL INPUT ERROR: unrecoginzed parameter name "genomeType" in input "genomeParameters.txt"
  SOLUTION: use correct parameter name (check the manual)

  Feb 23 12:43:21 ...... FATAL ERROR, exiting
```

# Solution

Go to workflow/rnaseq.nf and change the following (only works if pipeline downloaded):

```
// Check if an AWS iGenome has been provided to use the appropriate version of STAR
def is_aws_igenome = false
if (params.fasta && params.gtf) {
    if ((file(params.fasta).getName() - '.gz' == 'genome.fa') && (file(params.gtf).getName() - '.gz' == 'genes.gtf')) {
        is_aws_igenome = true
    }
}
```

to ->

```
// Check if an AWS iGenome has been provided to use the appropriate version of STAR
def is_aws_igenome = false
if (params.fasta && params.gtf) {
    if ((file(params.fasta).getName() - '.gz' == 'genome.fa') && (file(params.gtf).getName() - '.gz' == 'genes.gtf')) {
        is_aws_igenome = false
    }
}
```
