# Troubleshoot for common nf-core/rnasplice errors

Caused by:
  Process `NFCORE_RNASPLICE:RNASPLICE:ALIGN_STAR:STAR_ALIGN_IGENOMES (ERR188428)` terminated with an error exit status (102)

Command executed:

  STAR \
      --genomeDir star_index_2.7.10a \
      --readFilesIn ERR188428_1_val_1.fq.gz ERR188428_2_val_2.fq.gz  \
      --runThreadN 2 \
      --outFileNamePrefix ERR188428. \
       \
      --sjdbGTFfile genes.gtf \
      --outSAMattrRGline ID:ERR188428 'SM:ERR188428'   \
      --quantMode TranscriptomeSAM --twopassMode Basic --outSAMtype BAM Unsorted --readFilesCommand gunzip -c --runRNGseed 0 --outFi$

  if [ -f ERR188428.Unmapped.out.mate1 ]; then
      mv ERR188428.Unmapped.out.mate1 ERR188428.unmapped_1.fastq
      gzip ERR188428.unmapped_1.fastq
  fi
  if [ -f ERR188428.Unmapped.out.mate2 ]; then
      mv ERR188428.Unmapped.out.mate2 ERR188428.unmapped_2.fastq
      gzip ERR188428.unmapped_2.fastq
  fi
  cat <<-END_VERSIONS > versions.yml
  "NFCORE_RNASPLICE:RNASPLICE:ALIGN_STAR:STAR_ALIGN_IGENOMES":
        star: $(STAR --version | sed -e "s/STAR_//g")
      samtools: $(echo $(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*$//')
      gawk: $(echo $(gawk --version 2>&1) | sed 's/^.*GNU Awk //; s/, .*$//')
  END_VERSIONS

  Command exit status:
  102

Command output:
  Aug 22 10:49:28 ..... started STAR run
  Aug 22 10:49:28 ..... loading genome

Command error:
  WARNING: Skipping mount /usr/local/apps/singularity/3.5.3/var/singularity/mnt/session/etc/resolv.conf [files]: /etc/resolv.conf do$

  EXITING: FATAL INPUT ERROR: unrecoginzed parameter name "genomeType" in input "genomeParameters.txt"
  SOLUTION: use correct parameter name (check the manual)

##Other sources that mention the error:
https://github.com/alexdobin/STAR/issues/1221
https://www.biostars.org/p/9520117/
https://github.com/alexdobin/STAR/issues/1323

# Compatability issue

There seems to be a compatability issue with STAR versions and the corresponding genomes
This issue was mainly encountered on CHPC

