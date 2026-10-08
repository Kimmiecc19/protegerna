# Troubleshooting for common `nf-core/rnafusion` errors

## Overview

This document provides tips and solutions for common problems encountered with nf-core/rnafusion.

---

## Rebuild Indices

### Error: Missing Output Files

If you encounter the following error message:

```Groovy
ERROR:
Command exit status:
  2
Command output:
  (empty)
Command error:
  ** Error, not able to find file: fusion_annot_lib.idx **  at /usr/local/src/STAR-Fusion/util/validate_ctat_genome_lib.pl line 28.
```

**OR:**

```groovy
Fatal INPUT FILE error, no valid exon lines in the GTF file: Homo_sapiens.GRCh38.102.chr.gtf
Solution: Check the formatting of the GTF file. One likely cause is the difference in chromosome naming between the GTF and FASTA file.
```

#### Solution 1

1. Check if it is a memory issue (e.g., error 104). Try adding the following to the config file:

  ```groovy
  process {
      withName:     'NFCORE_RNAFUSION:RNAFUSION:STARFUSION_WORKFLOW:STAR_FOR_STARFUSION' {
        memory = 200.GB  // Increase this value as needed
      }
  }
  ```

2. If that doesn't work, try rebuilding indices. Visit [this link](https://github.com/STAR-Fusion/STAR-Fusion/wiki/rebuild_ctat_genome_lib_indices) for more details.

---

### Rebuilding CTAT Genome Library Indices

To rebuild the indices locally using STAR-Fusion and ctat_genome_lib:

1. Download the latest STAR-Fusion release from [GitHub](https://github.com/STAR-Fusion/STAR-Fusion/releases) or use the [Singularity image](https://data.broadinstitute.org/Trinity/CTAT_SINGULARITY/STAR-Fusion/star-fusion.v1.13.0.simg) (recommended).

2. Navigate to the STAR-Fusion directory and run `make` in the base directory. Install missing R packages if needed:

```bash
spack install r-ranger
spack load r-ranger

spack install r-tidyverse
spack load r-tidyverse

# After installing packages
make clean
make
```

3. Download the CTAT genome library files:
   - [GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz](https://data.broadinstitute.org/Trinity/CTAT_RESOURCE_LIB/GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz) (MUST be the plug-n-play version)

4. Verify the integrity of the downloaded files using their MD5 checksums.

5. Unpack the data resources and index them as follows:

```bash
tar xvf GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play.tar.gz

# Change directory to the CTAT genome lib dir:
cd /path/to/your/GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play/ctat_genome_lib_build_dir/

# Rebuild the indices:
${STAR_Fusion_BASEDIR}/ctat-genome-lib-builder/util/rebuild_indices.pl .

# OR using Singularity:
singularity exec -e star-fusion.v1.13.0.simg STAR-Fusion.v1.14.0/ctat-genome-lib-builder/util/rebuild_indices.pl .
```

**Don't forget the final dot (`.`) in the rebuild command!**

This step can take over an hour.

After re-running nf-core/rnafusion, if you get the error:

```groovy
Command error:
  Error, cannot locate genome_lib_dir: ctat_genome_lib_build_dir at /usr/local/src/STAR-Fusion/STAR-Fusion line 508.
```

#### Solution 2

Manually move the correct reference to a new directory named `starfusion`:

```bash
cd fusion_ref # base genome directory
mkdir starfusion
cd GRCh38_gencode_v37_CTAT_lib_Mar012021.plug-n-play
cp -r ctat_genome_lib_build_dir/ ../starfusion/
```

Re-run the pipeline.

---
