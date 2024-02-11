# Tips for Common RNAfusion Problems
##  This markdown document provides tips and solutions for common problems encountered with RNAfusion pipelines.


## Rebuild Indices

### Error: Missing Output Files

If you encounter the following error message:

```
Error executing process > 'NFCORE_RNAFUSION:RNAFUSION:FUSIONREPORT_WORKFLOW:FUSIONREPORT (ERR315432)'
Caused by:
  Missing output file(s) `*_*.html` expected by process `NFCORE_RNAFUSION:RNAFUSION:FUSIONREPORT_WORKFLOW:FUSIONREPORT (ERR315432)`
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
```

#### Solution:

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

1. Download the latest STAR-Fusion release from [here](https://github.com/STAR-Fusion/STAR-Fusion/releases).

2. Download the CTAT genome library files:
   - [GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz](https://data.broadinstitute.org/Trinity/CTAT_RESOURCE_LIB/GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz)

3. Verify the integrity of the downloaded files using their MD5 checksums.

4. Unpack the data resources and index them as follows:

```bash
tar xvf CTAT_resource_lib.tar.gz 
tar xvf GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz

# Change directory to the CTAT genome lib dir:
cd /path/to/your/GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play/ctat_genome_lib_build_dir/

# Rebuild the indices:
${STAR_Fusion_BASEDIR}/ctat-genome-lib-builder/util/rebuild_indices.pl .
```

Don't forget the final dot in the rebuild command!
```





