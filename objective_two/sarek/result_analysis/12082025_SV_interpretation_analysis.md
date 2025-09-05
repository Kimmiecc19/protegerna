# Structural Variant Annotation, Prioritization, and Interpretation

## TL;DR

I am analyzing structural variants (SVs) in ALS patients to identify variants that may contribute to disease. After running nf-core/sarek using whole genome sequencing data, I am merging SV VCF files across multiple participents with **SURVIVOR**.

Next, I am annotating and prioritizing these merged VCFs using **AnnotSV**, which integrates functional, clinical, and regulatory information to highlight potentially pathogenic variants and genes relevant to ALS.

This pipeline helps answer key research questions such as:

* Which SVs occur specifically in ALS cases and not controls?
* Are there SVs shared among patients with similar ALS subtypes?
* What genes are disrupted, especially known ALS-associated genes?
* Can SVs be linked to individual patient phenotypes?

Finally, I am visualizing the annotated SVs using an interactive shinydashboard to aid prioritization and interpretation.

This approach aims to streamline identifying and prioritizing clinically relevant SVs for further study in ALS research. It also serves as a foundation for incorporating transcriptomic and proteomic data.

---

This document outlines the method used for annotating and interpreting structural variants (SVs) in amyotrophic lateral sclerosis (ALS) patients using **SURVIVOR** and **AnnotSV**.

The goal is to identify potentially clinically significant SVs, generate a gene/protein list for further analysis, and answer key questions regarding the occurrence and significance of these variants in ALS cases compared to controls.

## Questions This Method Aims to Answer

1. Does this SV occur in ALS cases but not controls?  
2. Which participants should I investigate further?  
3. Is this SV shared among multiple patients with the same ALS subtype?  
4. What genes are disrupted in each individual? Are there any known ALS genes that are disrupted?  
5. Can a participant's SV be linked to their individual phenotype?  

---

## Contents

- [Structural Variant Annotation, Prioritization, and Interpretation](#structural-variant-annotation-prioritization-and-interpretation)
  - [TL;DR](#tldr)
  - [Questions This Method Aims to Answer](#questions-this-method-aims-to-answer)
  - [Contents](#contents)
  - [Brief Summary of Structural Variants](#brief-summary-of-structural-variants)
  - [General Variant Analysis Steps](#general-variant-analysis-steps)
  - [Background of Tools Used](#background-of-tools-used)
    - [SURVIVOR (StructURal Variant Majority Vote)](#survivor-structural-variant-majority-vote)
    - [AnnotSV with variantconvert](#annotsv-with-variantconvert)
  - [Overall Steps](#overall-steps)
  - [Step One: Merge SV VCFs Using SURVIVOR](#step-one-merge-sv-vcfs-using-survivor)
    - [Download and Install](#download-and-install)
    - [Prepare VCF Files for Merging](#prepare-vcf-files-for-merging)
      - [nf-core/sarek VCF Output (Example)](#nf-coresarek-vcf-output-example)
    - [Run SURVIVOR](#run-survivor)
    - [SURVIVOR Output Example](#survivor-output-example)
  - [Step Two: Annotate Merged VCF Using AnnotSV](#step-two-annotate-merged-vcf-using-annotsv)
    - [Install and Locate AnnotSV](#install-and-locate-annotsv)
    - [Download AnnotSV Human Annotations](#download-annotsv-human-annotations)
      - [Set Global Environment Variable](#set-global-environment-variable)
      - [Run AnnotSV with VCF Output](#run-annotsv-with-vcf-output)
      - [Key Parameters](#key-parameters)
    - [Adding ALS-Specific Annotations](#adding-als-specific-annotations)
      - [All Terms and Gene Associations Related to Amyotrophic Lateral Sclerosis (ALS) on HPO](#all-terms-and-gene-associations-related-to-amyotrophic-lateral-sclerosis-als-on-hpo)
        - [Genes Associated with ALS](#genes-associated-with-als)
    - [List of HPO Terms Used for AnnotSV](#list-of-hpo-terms-used-for-annotsv)
    - [Troubleshooting Errors / Issues](#troubleshooting-errors--issues)
      - [1. `variantconvert` Error](#1-variantconvert-error)
      - [2. Issue with Nested INFO Column in VCF File](#2-issue-with-nested-info-column-in-vcf-file)
      - [Example of VCF file output from AnnotSV](#example-of-vcf-file-output-from-annotsv)
      - [The Duplicated INFO](#the-duplicated-info)
      - [General commands](#general-commands)
      - [When using merged Manta file which was annotated with VEP and snpEff](#when-using-merged-manta-file-which-was-annotated-with-vep-and-snpeff)
      - [When using merged Manta file which was not annotated](#when-using-merged-manta-file-which-was-not-annotated)
      - [When trying to index the VCF](#when-trying-to-index-the-vcf)
      - [Final Combined Steps in a Single-Line Command](#final-combined-steps-in-a-single-line-command)
      - [Optional - Rewrite Headers After Removing INFO Tags](#optional---rewrite-headers-after-removing-info-tags)
    - [Re-run AnnotSV on the new stripped, sorted, and indexed VCF](#re-run-annotsv-on-the-new-stripped-sorted-and-indexed-vcf)
  - [Step Three: A shinydashboard Structural Variant Viewer](#step-three-a-shinydashboard-structural-variant-viewer)
  

## Brief Summary of Structural Variants

**What are Structural Variants (SV)?**  

- Variations in a DNA region that range from `~50` base pairs to many megabases.  
- Include several classes: deletions, duplications, insertions, inversions, translocations, complex rearrangements.  

**What are Copy Number Variations (CNV)?**  

- Deletions or duplications in the genome (unbalanced SV) ranging from `~50` base pairs to many megabases.  

**Differences Between SV and CNV**  

- CNVs are unbalanced SVs with gain or loss of genomic material.  
  
---

## General Variant Analysis Steps

1. Whole genome sequencing  
2. QC and alignment  
3. Variant calling  
4. Variant/Gene prioritization — rank candidate genes by disease relevance  
5. Variant interpretation to establish pathogenicity (Genotype/phenotype association):  
   - Pathogenic variants associated with RD phenotypes  
   - Pathogenic variants in RD-associated genes  
   - Functional variants in genes with unknown RD association  

---

## Background of Tools Used

### SURVIVOR (StructURal Variant Majority Vote)

**Purpose:**  
Simulates/evaluates SVs, merges and compares SVs within/among samples, reformats or summarizes SVs.  

- Merging is independent of variant caller.  
- Good for handling breakpoint fuzziness, but requires post-processing for multi-sample VCFs with genotypes.

**Reference:**  
Jeffares DC et al. *Nature Communications* (2017) 8:14061. DOI: [10.1038/NCOMMS14061](https://doi.org/10.1038/NCOMMS14061)  
GitHub: [https://github.com/fritzsedlazeck/SURVIVOR](https://github.com/fritzsedlazeck/SURVIVOR)  
nf-core module: [https://nf-co.re/modules/survivor_merge/](https://nf-co.re/modules/survivor_merge/)

**Alternative SV merging tools:**  

- svimmer  
- SVAnalyzer  
- bcftools merge *(not ideal for SVs)*  
- svtools  
- MetaSV  
- Jasmine *(may need post-processing)*  

**Recommended Steps:**  

1. `bgzip` and index VCFs  
2. Create `.txt` list of VCFs (`ls`)  
3. Run `SURVIVOR merge`  
4. Fix headers & sort with `bcftools sort`  
5. Normalize & left-align with `bcftools norm`  

---

### AnnotSV with variantconvert

**Purpose:**  
Annotates and ranks SVs by integrating functional, regulatory, and clinically relevant information. Aims to:

- Provide annotations useful for interpreting SV pathogenicity.
- Filter out potential false positives.

**Reference:**  
Geoffroy V et al. *Bioinformatics* (2018). DOI: [10.1093/bioinformatics/bty304](https://doi.org/10.1093/bioinformatics/bty304)  
GitHub: [https://github.com/lgmgeo/AnnotSV](https://github.com/lgmgeo/AnnotSV)  
nf-core modules:  

- [annotsv_annotsv](https://nf-co.re/modules/annotsv_annotsv/)  
- [annotsv_installannotations](https://nf-co.re/modules/annotsv_installannotations/)

- AnnotSV takes as an input file a VCF file describing the SV coordinates, as well as the patients’ phenotype (optional).
- The outputfile contains the overlaps of the SV with relevant genomic features where the genes refer to RefSeq or ENSEMBL genes (user defined).

**Annotations Provided:**  

- **Gene-based:** GenCC, OMIM, intolerance scores, haploinsufficiency  
- **Feature overlaps:** DGV, 1000 Genomes, dbVar pathogenic SVs, promoters, enhancers, TADs  
- **Breakpoint annotations:** GC content, repeats  
- **Systematic SV classification:** ACMG/ClinGen-based categories  

**Annotation Types (Mode):**  

- **Full:** Entire SV event (even if no gene overlap)  
- **Split by gene:** One annotation per overlapped gene  
- **Fullsplit:** Combines both  

**Similar Tools:**  
SVanna, ClinSV, vcfanno, gemini  

---

## Overall Steps

After running `nf-core/sarek`:

1. **SURVIVOR** — Merge SV VCFs from multiple participants for one variant caller (e.g., Manta or Delly)  
   - Preprocess: rename sample headings, unzip VCFs  
   - Input: list of unzipped annotated VCFs (VEP/snpEff)  
   - Output: merged VCF with all genotypes  

2. **AnnotSV** — Annotate merged VCF and output TSV/VCF  
   - Preprocess: remove `INFO/INFOEND` column (`bcftools annotate`), sort/index VCF  
   - Configure environment (Python path via spack to miniconda)  
   - Input: annotation directory, config, parameters, merged SURVIVOR VCF  
   - Output: clinically annotated SV VCF & TSV (note: missing genotypes)  

3. **Shinydashboard** — Structural variant viewer  
   - Input: Annotated VCF from AnnotSV + R script  
   - Output: interactive viewer with clinical significance highlights  

---

## Step One: Merge SV VCFs Using SURVIVOR

---

### Download and Install

```bash
git clone https://github.com/fritzsedlazeck/SURVIVOR.git
cd SURVIVOR/Debug
make
```

### Prepare VCF Files for Merging

1. Create a directory to store VCF files
2. Unzip the VCF files
3. Create a sample list file:

```bash
ls *vcf > sv_vcf_list.txt
```

---

#### nf-core/sarek VCF Output (Example)

> **TODO:** Compare annotated vs unannotated

```bash
# For one participant
chr1    3260742 MantaINS:11:1786:1786:0:3:0 A <INS> 999 PASS END=3260742;SVTYPE=INS;CIPOS=0,5;CIEND=0,5;HOMLEN=5;HOMSEQ=TGATG;LEFT_SVINSSEQ=TGATGGTGATGATAATGATAGTGA...;RIGHT_SVINSSEQ=TGATGGTGATGATAATGATAGTGA... GT:FT:GQ:PL:PR:SR 1/1:PASS:154:999,157,0:0,12:0,46
```

---

### Run SURVIVOR

- Input: list of VCF files from nf-core/sarek annotated/unannotated output

```bash
~/SURVIVOR/Debug/SURVIVOR merge sv_vcf_list.txt 1000 1 1 1 0 20 sample_merged_30062025.vcf
```

**Parameters Explained:**

- **1000**: Max allowed distance between breakpoints = 1 kb
- **1**: Calls supported by at least 1 caller (Having this set to one will ensure that unique participant SVs are reported.)
- **1**: Caller agreement on type required
- **1**: Caller agreement on strand required
- **0**: Inactive parameter
- **20**: SV length must be at least 20 bp

---

### SURVIVOR Output Example

```bash
0/1:NA:241312125:0,0:++:563:TRA:MantaBND_119388_0_1_0_0_0_0:NA:NA:chr1_806391-chr2_242118516
```

**Where:**

* GT = 0/1 — heterozygous for this structural variant (one ref allele, one variant allele)
* PSV = NA — no phase set variant info here
   * LN = 241312125 — the variant length is very large (241 million bp), consistent with a large translocation
* DR = 0,0 — zero supporting reads for ref and alt alleles (could indicate missing or filtered data)
* ST = ++ — both breakends are on the plus strand
* QV = 563 — quality score for this genotype call, higher is better
* TY = TRA — variant type is a translocation
* ID = MantaBND_119388_0_1_0_0_0_0 — internal Manta ID for this breakpoint
* RAL = NA — reference allele length not available
* AAL = NA — alternate allele length not available
* CO = chr1_806391-chr2_242118516 — coordinates involved in this breakpoint: chromosome 1 position 806,391 joined to chromosome 2 position 242,118,516 (typical for translocations)

**Field Descriptions:**

| Field | Meaning                             |
| ----- | ----------------------------------- |
| GT    | Genotype (e.g., 0/0, 0/1, ./.)      |
| PSV   | Phase set variant info              |
| LN    | Variant length (bp)                 |
| DR    | Read depth (ref, alt)               |
| ST    | Strand orientation (++, --, +-, -+) |
| QV    | Quality score                       |
| TY    | Variant type (e.g., TRA, DEL, INS)  |
| ID    | Internal caller ID                  |
| RAL   | Reference allele length             |
| AAL   | Alternate allele length             |
| CO    | Breakpoint coordinates              |

---

## Step Two: Annotate Merged VCF Using AnnotSV

---

### Install and Locate AnnotSV

```bash
conda install -c bioconda annotsv

find . -type f -name "AnnotSV"
./miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0/bin/AnnotSV
./miniconda3/bin/AnnotSV

cd miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0/bin/
```

### Download AnnotSV Human Annotations

```bash
cd miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0
INSTALL_annotations.sh

# Optional: Install annotations for humans explicitly
make PREFIX=. install-human-annotation
```

#### Set Global Environment Variable

```bash
# Add to .bashrc
export ANNOTSV=/miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0/bin/AnnotSV
```

---

> **Note:** Converting AnnotSV TSV to VCF
  > Requires `variantconvert` tool
  > Needs Python ≥ 3.8 and modules: **natsort**, **pandas**, **pyfaidx** (installed with AnnotSV)

#### Run AnnotSV with VCF Output

```bash
AnnotSV \
-annotationsDir /home/kcoetzer/miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0/bin/AnnotSV_annotations \
-SVinputInfo 1 \
-SVinputFile sample_merged_30062025.vcf \
-variantconvertDir /home/kcoetzer/miniconda3/share/python3/variantconvert/ \
-variantconvertMode fullsplit \
-vcf 1 >& AnnotSV.log
```

---

#### Key Parameters

**Required:**

- `-annotationsDir`: Path to annotations directory
- `-annotationMode`: `both` (default), `full`, or `split`
- `-SVinputFile`: Path to input VCF/BED (gzipped VCF supported)
- `-SVinputInfo`: Set `1` to keep correct fields (ID, QUAL, FILTER, etc.)
- `-variantconvertDir`: Path to variantconvert tool
- `-variantconvertMode`: `combined` (default), `full`, or `fullsplit`
- `-vcf`: Output VCF format (`1` = yes)

**Optional (configurable):**

- `-outputDir`: Output directory
- `-outputFile`: Output file path/name
- `-includeCI`: Include confidence intervals (CIPOS/CIEND)
- `-rankFiltering`: Select SVs by class (1–5, NA)
- `-benignAF`: Allele frequency threshold (default = 0.01)
- `-genomeBuild`: `GRCh38` (default) or `GRCh37`
- `-hpo`: HPO terms for phenotype

> **Note:** Users can choose a subset of annotation columns via the config file to reduce output size and speed up processing.

---

### Adding ALS-Specific Annotations

#### All Terms and Gene Associations Related to Amyotrophic Lateral Sclerosis (ALS) on HPO

🔗 [HPO Term HP:0007354](https://hpo.jax.org/browse/term/HP:0007354)

##### Genes Associated with ALS

```txt
CCNF, FIG4, CYLD, HNRNPA2B1, HNRNPA1, VCP, SQSTM1, CHCHD10, NEK1, NEFH, DCTN1, SOD1, PRPH, SPG11, KIF5A, PFN1, MATR3, C9orf72, TUBA4A, SETX, ANG, ERBB4, FUS, SIGMAR1, ALS2, SPTLC1, OPTN, ANXA11, PSEN1, MAPT, UBQLN2, TARDBP, TIA1, ATXN2, DAO, PON3, TREM2, UNC13A, PON1, GLE1, GLT8D1, PON2, CHMP2B, TAF15, PPARGC1A, VAPB, CFAP410, TBK1, TRPM7
```

> **Note:** The following genes were analysed by AnswerALS. This list can be used for future filtering of AnnotSV results.

```csv
ANG, ANGND, C9ORF72, C9ORFND, FUS, FUSND, MUTOT, MUTOTSP, PRGRNND, PROGRAN, SETX, SETXND, SOD1, SOD1MUTA, SOD1ND, TAU, TAUND, TDP43, TDP43ND, VAPB, VAPBND, VCP, VCPND
```

---

### List of HPO Terms Used for AnnotSV

These terms were added as a list to the config file:
`~/miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0/etc/AnnotSV`

> The full descriptions of each term can be found at the end of this document (see other document).

```txt
HP:0007354, HP:0025275, HP:0007933, HP:0006956, HP:0100960, HP:0200153, HP:0001593, HP:0000690, HP:0006342, HP:0030047, HP:0200154, HP:6001223, HP:0005090, HP:6000174, HP:0032478, HP:0010291, HP:0041210, HP:0200158, HP:0011049, HP:0011050, HP:0006397, HP:0006441, HP:6000140, HP:0031751, HP:0031750, HP:0031752, HP:0031758, HP:0033481, HP:0032030, HP:6000989, HP:0002314, HP:6001153, HP:0005338, HP:6001132, HP:0200159, HP:0001822, HP:0100952, HP:3000067, HP:3000068, HP:0031749, HP:0007299, HP:6001173, HP:0100885, HP:0100731, HP:0006290, HP:3000069, HP:0007655, HP:0006650, HP:6001155, HP:0100500, HP:0040106, HP:6001158, HP:0005325, HP:0005050, HP:0009554, HP:0006453, HP:0000895, HP:0011230, HP:0006897, HP:0001967, HP:0009175, HP:0009243, HP:0009304, HP:0009307, HP:0009313, HP:0009377, HP:0034829, HP:0006174, HP:0009454, HP:0009551, HP:0009562, HP:0009585, HP:0003034, HP:0009634, HP:0009655, HP:0009840, HP:0009848, HP:0009856, HP:0006623, HP:0010031, HP:0010081, HP:0006918, HP:0010208, HP:0003881, HP:0010352, HP:0010388, HP:0010418, HP:0020267, HP:0033491, HP:0033701, HP:0005092, HP:0008664, HP:0005652, HP:0002694, HP:0005825, HP:0004054, HP:0100463, HP:0100464, HP:0100465, HP:0100461
```

---

### Troubleshooting Errors / Issues

#### 1. `variantconvert` Error

**Command used:**

```bash
python3 /home/kcoetzer/miniconda3/share/python3/variantconvert/src/variantconvert convert \
    -i sample_merged_30062025.annotated.tsv \
    -o /home/kcoetzer/sample_merged_30062025.annotated.vcf \
    -c /home/kcoetzer/miniconda3/share/python3/variantconvert/src/variantconvert/configs/GRCh38/annotsv3_from_vcf.fullsplit.local.json
```

**Error Output:**

```bash
ModuleNotFoundError: No module named 'variantconvert'
```

**Cause:**

- `.bash_profile` had `alias python= 'python3.11'`.
- `.bashrc` has spack load which overrides the Python path to hemera version.
- AnnotSV (installed via conda) expects the conda Python environment.

> This was initially done because I had issues with the Python version in something else I was trying to run. Most likely before spack was implemented.

- Tested both hemera and miniconda Python environments:

```python
python 3.10.12 
import variantconvert
ModuleNotFoundError: No module named 'variantconvert'

python 3.11.7 (miniconda)
import variantconvert
```

- The hemera Python environment does not have the `variantconvert` module installed, but it is available in the miniconda environment.

**Fixes Attempted:**

1. **Run `variantconvert` separately** → *This worked*

   ```bash
   python /home/kcoetzer/miniconda3/share/python3/variantconvert/src/variantconvert convert \
       -i /home/kcoetzer/20250721_AnnotSV/sample_merged_30062025.annotated.tsv \
       -o /home/kcoetzer/20250721_AnnotSV/sample_merged_30062025.annotated.vcf \
       -c /home/kcoetzer/miniconda3/share/python3/variantconvert/src/variantconvert/configs/GRCh38/annotsv3_from_vcf.fullsplit.local.json
   ```

2. **Use miniconda Python 3.11.7** → *This worked*

- Changed .bashrc to stop automatically loading spack
- Added exported path for miniconda python
- Alternatively, export the path before running the AnnotSV command

```bash
# After editing and sourcing .bashrc
which python
/home/kcoetzer/miniconda3/bin/python
```

---

#### 2. Issue with Nested INFO Column in VCF File

#### Example of VCF file output from AnnotSV

```bash
1  54719 MantaINS:118961:0:0:0:0:0 T TTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTT   487     PASS    AnnotSV_ID=1_54719_54724_INS_1;SV_start=54719;INFO=SUPP=2|SUPP_VEC=00000000100001000000000000|SVLEN=60|SVTYPE=INS|SVMETHOD=SURVIVOR1.0.7|CHR2=1|END=54720|CIPOS=0,0|CIEND=0,4|STRANDS=+-;...rest of annotations...;SUPP=2;SUPP_VEC=1.00001e+17;SVLEN=60;SVTYPE=INS;SVMETHOD=SURVIVOR1.0.7;CHR2=1;END=54724;CIPOS=0,0;CIEND=0,4;STRANDS=+- GT:PSV:LN:DR:ST:QV:TY:ID:RAL:AAL:CO ./.:NaN:0:0,0:--:NaN:NaN:NaN:NAN:NAN:NAN 1/1:NA:60:0,0:+-:487:INS:MantaINS_118961_0_0_0_0_0:TC:TTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTTTCTT:chr1_54719-chr1_54720...etc...
```

#### The Duplicated INFO

```bash
# From SURVIVOR
INFO=SUPP=2|SUPP_VEC=00000000100001000000000000|SVLEN=60|SVTYPE=INS|SVMETHOD=SURVIVOR1.0.7|CHR2=1|END=54720|CIPOS=0,0|CIEND=0,4|STRANDS=+-
# From AnnotSV
SUPP=2;SUPP_VEC=1.00001e+17;SVLEN=60;SVTYPE=INS;SVMETHOD=SURVIVOR1.0.7;CHR2=1;END=54724;CIPOS=0,0;CIEND=0,4;STRANDS=+-
```

**Cause:**

- Input VCF from SURVIVOR already had an `INFO` column.
- AnnotSV appended another `INFO` block → causing it to be duplicated.

**Solution:**

- Remove the `INFO` fields from merged SURVIVOR VCF before annotation with AnnotSV.

#### General commands

```bash
bcftools annotate -x INFO input.vcf -Oz -o noINFO.vcf.gz
bcftools index noINFO.vcf.gz
```

#### When using merged Manta file which was annotated with VEP and snpEff

```bash
bcftools annotate -x INFO sample_merged_anno_30072025.vcf -Oz -o sample_mer
ged_noINFO_30072025.vcf 
[W::vcf_parse_info] INFO/END=10975 is smaller than POS at chr1:180753
```

**Cause:**

- Some SV callers (especially SURVIVOR, Manta, etc.) leave broken or placeholder END coordinates.
- AnnotSV ignores these, but bcftools is strict and gives a warning.
- It’s just a warning, not an error — bcftools will still produces the noINFO VCF.

**Solution:**

- Force bcftools to remove END tag along with the rest of INFO tags

```bash
bcftools annotate -x INFO/END,INFO sample_merged_anno_30072025.vcf -Oz -o sample_merged_noINFO_30072025.vcf
```

#### When using merged Manta file which was not annotated

```bash
bcftools annotate -x INFO sample_merged_30062025.vcf -Oz -o sample_merged_noINFO_30062025.vcf
[E::vcf_parse_format_max3] Incorrect number of FORMAT fields at HLA-DQA1*04:02:715
```

- bcftools expects every sample column to have the same number of colon‑delimited fields as declared in the FORMAT column.
- One record (at HLA-DQA1*04:02:715) has inconsistent formatting.

**Cause:**

- The unannotated VCF from SURVIVOR has messy entries that bcftools so it can't parse properly.
- Annotated VCFs are “normalized” by annotation tools like VEP or SnpEff, which fix these issues.

**When running VEP or SnpEff, they:**

- Parse the VCF.
- Add their own INFO tags.
- Re‑write the file with strict VCF formatting (validating REF/ALT, FORMAT, etc.).
- This “re‑serialization” fixes a lot of messy entries (missing FORMAT fields, broken INFO definitions, inconsistent ALT alleles).
- So, bcftools sees a “clean” annotated VCF and passes bcftools’ parser.
- The raw merged VCF from SURVIVOR is “dirty” since it merges VCFs without validating FORMAT fields line by line.

  - Annotated VCFs pass bcftools checks because VEP/SnpEff reformat them.
  - Unannotated VCFs may fail due to:

    - Missing genotype subfields
    - Inconsistent field counts per sample
    - Malformed IDs that break bcftools’ parsing expectations

**Conclusion:**

- Use **annotated (cleaned)** VCFs with fixed INFO when possible.
- If using **unannotated (raw)** VCFs, ensure they are properly formatted before running bcftools commands.

**Solution:**

- Just use the annotated VCF file for merging with SURVIVOR, strip `INFO` column, and then re-annotate with AnnotSV.

#### When trying to index the VCF

```bash
bcftools index sample_merged_anno_noINFO_head_30072025.vcf 
index: the file is not BGZF compressed, cannot index: sample_merged_anno_noINFO_head_30072025.vcf
```

**Cause:** `bcftools index` only works on **bgzip-compressed** VCFs.

**Solution:**

```bash
# Output .vcf.gz
bgzip sample_merged_anno_noINFO_head_30072025.vcf
```

Then…

```bash
bcftools index sample_merged_anno_noINFO_head_30072025.vcf.gz 
[E::hts_idx_push] Unsorted positions on sequence #1: 789494 followed by 789481
index: failed to create index for "sample_merged_anno_noINFO_head_30072025.vcf.gz"
```

**Cause:**

- The VCF is not sorted by genomic coordinates
- `bcftools` expects every line for chr1 to be in ascending order, but it found: POS = `789494`, then POS = `789481` (goes backwards).

**Solution:**

- Sort the VCF before indexing

```bash
# Sort and then index
bcftools sort sample_merged_anno_noINFO_head_30072025.vcf.gz -Oz -o sample_merged_anno_noINFO_head_30072025.sorted.vcf.gz
# Output tbi
bcftools index --tbi sample_merged_anno_noINFO_head_30072025.sorted.vcf.gz
```

#### Final Combined Steps in a Single-Line Command

```bash
bcftools annotate -x INFO/END,INFO sample_merged_anno_30072025.vcf \
| bcftools sort -Oz -o sample_merged_anno_noINFO.sorted.vcf.gz \
&& bcftools index -t sample_merged_anno_noINFO.sorted.vcf.gz
```

**What this does:**

- `bcftools annotate -x INFO` → strips the `INFO` column.
- Pipes straight into `bcftools sort` → sorts by chromosome/position and bgzips in one step (`-Oz`).
- `bcftools index` creates the `.tbi` / `.csi` index (`-t` for tbi).

#### Optional - Rewrite Headers After Removing INFO Tags

This removes `##INFO=<ID=...>` lines in header

```bash
bcftools view --header-only sample_merged_anno_noINFO_30072025.vcf \
| grep -v "##INFO=" > sample_merged_noINFO_30072025_new_header.txt
```

---

### Re-run AnnotSV on the new stripped, sorted, and indexed VCF

```bash
# First change python3 to python (if not changed in .bashrc)
export PATH=/home/kcoetzer/miniconda3/bin:$PATH 

# Run AnnotSV to output tsv and vcf
AnnotSV \
  -annotationsDir /home/kcoetzer/miniconda3/pkgs/annotsv-3.4.6-py313hdfd78af_0/bin/AnnotSV_annotations \
  -SVinputInfo 1 \
  -SVinputFile sample_merged_anno_noINFO.sorted.vcf.gz \
  -variantconvertDir /home/kcoetzer/miniconda3/share/python3/variantconvert/ \
  -variantconvertMode fullsplit \
  -vcf 1 >& AnnotSV.log
```

---

## Step Three: A shinydashboard Structural Variant Viewer

```r
# Install Required R Packages
if (!require("shiny")) install.packages("shiny")
if (!require("vcfR")) install.packages("vcfR")
if (!require("DT")) install.packages("DT")
if (!require("shinyjs")) install.packages("shinyjs")
if (!require("shinythemes")) install.packages("shinythemes")
if (!require("progress")) install.packages("progress")

### Load R Libraries
library(shiny)
library(vcfR)
library(DT)
library(shinythemes)
library(shinyjs)
library(progress)

# Define UI for the Shiny app
ui <- fluidPage(
  theme = shinytheme("flatly"), # Flatly theme for a clean look
  useShinyjs(), # JavaScript functions
  # Dashboard title
  titlePanel("Structural Variant Dashboard"),
  
  # Floating filter panel with toggle button
  tags$div(
    id = "filterPanel",
    class = "floating-filter", 
    wellPanel(
      style = "padding: 10px; margin-bottom: 0;",
      actionButton("toggle_filter", "Hide Filters", class = "btn btn-info btn-xs", style = "width:100%; margin-bottom:5px;"),
      selectizeInput(
        "gene_filter",
        "Gene(s):",
        choices = NULL,
        multiple = TRUE,
        options = list(placeholder = 'Type or select genes...')
      ),
      actionButton("clear_filter", "Clear", class = "btn btn-warning btn-xs", style = "width:100%; margin-top:5px;")
    )
  ),
  
  # Main content display 
  fluidRow(
    column(
      width = 12,
      id = "main_panel",
      tabsetPanel(
        tabPanel("Variants", DTOutput("variant_table")),
        tabPanel("Column Description",
                 tags$div(style = "padding:20px;",
                          h4("AnnotSV Column Descriptions"),
                          DT::dataTableOutput("column_description_table")
                 )
        )
      )
    )
  ),
  
  # CSS styling for the floating filter panel
  tags$style(HTML("
    .floating-filter {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 220px;
      z-index: 1001; # Ensure it is above other elements
      background: #f7f7f7;
      border-radius: 8px; # Rounded corners
      box-shadow: 0 2px 8px rgba(0,0,0,0.15); # Subtle shadow for depth
      transition: top 0.4s, opacity 0.4s; # Smooth transition
      opacity: 1;
    }
    .floating-filter.collapsed {
      top: -180px; # Move out of view when collapsed
      opacity: 0.1;
      pointer-events: none; # Disable pointer events when collapsed
    }
    #toggle_tab {
      position: fixed;
      top: 20px;
      right: 20px;
      background: #5bc0de;
      color: white;
      padding: 5px 12px;
      border-radius: 0 5px 5px 0; # Rounded corners on the left side
      font-weight: bold;
      cursor: pointer;
      z-index: 1002;
      display: none; # Initially hidden
    }
    .floating-filter.collapsed + #toggle_tab { # Show toggle tab when collapsed
      display: block !important; # Force display when filter panel is collapsed
    }
    table.dataTable td {
      white-space: normal !important;
      word-wrap: break-word; # Allow text to wrap in table cells
      max-width: 300px; # Set a max width for table cells
    }
    table.dataTable th {
      white-space: nowrap; # Prevent header text from wrapping
    }
  "))
)

server <- function(input, output, session) {
  
  # Add a floating toggle tab
  observe({ # A reactive observer that performs/triggers actions, but does not return a value
    runjs("
    # Floating toggle stays fixed on the screen regardless of scrolling
      if (!document.getElementById('toggle_tab')) { # Check if toggle tab exists
        var toggle = document.createElement('div'); # Create toggle tab
        toggle.id = 'toggle_tab';
        toggle.innerText = 'Show Filters';
        document.body.appendChild(toggle); # Append to body 
        toggle.style.display = 'none'; # Initially hidden
        toggle.addEventListener('click', function(){ 
          Shiny.setInputValue('toggle_filter', Math.random()); 
        });
      }
    ")
  })
  
 # This reactive value tracks the state of the filter panel (open/closed)
  filterPanel_state <- reactiveVal("open") # 
  # Observe the toggle button click to change the filter panel state
  observeEvent(input$toggle_filter, { # "Watch" toggle and update accordingly
    if (filterPanel_state() == "open") { 
      shinyjs::addClass(id = "filterPanel", class = "collapsed") # Collapse the filter panel
      runjs("document.getElementById('toggle_tab').style.display = 'block';") # Show the toggle tab
      filterPanel_state("closed") # Update state to closed
    } else {
      shinyjs::removeClass(id = "filterPanel", class = "collapsed")
      runjs("document.getElementById('toggle_tab').style.display = 'none';")
      filterPanel_state("open")
    }
  })
  
  #TODO: Trim columns first then add back in 

  # Read SV VCF File (From AnnotSV)
  vcf_data <- reactive({
    # Show progress while loading VCF and processing data since dashboard can't display until data is ready
    vcf <- NULL # Initialize vcf variable
    shiny::withProgress(
      message = 'Loading variants...',
      detail = 'This may take a while...',
      value = 0, # Initial progress value - change?
      {
        # Load the VCF file using vcfR
        # This is done because VCF files can be large and shiny has a size limit for uploading files
        vcf <- read.vcfR("sample_anno_merged_noINFO_05082025.annotated.vcf", verbose = TRUE)
        # Artificial delay to simulate processing (remove or adjust as needed)
        Sys.sleep(1) # Simulate loading time
        # TODO: Still not staying until loading complete.
        # TODO: test - incProgress(1, detail = "Processing VCF data...") # Increment progress bar 
      }
    )
    vcf
  })
  
  # Process SV Data
  processed_data <- reactive({
   # Ensure VCF data is loaded
    vcf <- vcf_data()
    # Extract the fixed columns (CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO) from the VCF and store them as a data frame
    fix_df <- as.data.frame(vcf@fix, stringsAsFactors = FALSE)
    # Parse the INFO field into a structured format
    # This function will split the INFO field into key-value pairs and return a list of these
    parse_info_field <- function(info) {
      # For DP=100;DB;H2: key=value pair (like DP=100) or just a key alone (like DB or H2)
      # Split INFO string into "key=value" chunks using ";"
      kvs <- unlist(strsplit(info, ";")) # [pieces: "DP=100", "DB", "H2"]
      out <- list()
      for (kv in kvs) {
         # For each chunk, split by "=" into key and value
        parts <- strsplit(kv, "=")[[1]]
        if (length(parts) == 2) { # split in two: key = "DP" and value = "100".
         # Store value in list using the key name
          out[[parts[1]]] <- parts[2]
        } else {
         # If no value (e.g., flag fields), assign NA as value
          out[[parts[1]]] <- NA # if one part like ["DB"] then no value 
        }
      }
      return(out)
    }
    
   # Apply the parsing function to every row's INFO field
   # This produces a list of named lists (one per variant)
    info_list <- lapply(fix_df$INFO, parse_info_field)
   # Get all unique INFO keys across all variants
    all_info_keys <- unique(unlist(lapply(info_list, names)))
    
    # Convert the parsed INFO list into a data frame
    # Takes the list of vectors (lapply) and binds them row-wise into a data frame where one row per variant, columns named by the keys
    info_df <- as.data.frame(do.call(rbind, lapply(info_list, function(row) {
      # all_info_keys is a vector of all unique INFO keys
      sapply(all_info_keys, function(k) ifelse(!is.null(row[[k]]), row[[k]], NA))
    })), stringsAsFactors = FALSE)
    
    # Extract the genotype (GT) and FORMAT/sample fields from the VCF
    gt <- vcf@gt
    # Keep FORMAT/sample columns as-is (do not split by ":")
    # If there are genotype/sample columns, store them; else keep NULL
    sample_df <- if (ncol(gt) > 1) as.data.frame(gt[, -1, drop = FALSE], stringsAsFactors = FALSE) else NULL
    # If sample_df exists, set its column names (skip FORMAT column name)
    colnames(sample_df) <- if (!is.null(sample_df)) colnames(gt)[-1] else character(0)
    
    # Combine all data into a single data frame
    # Combine the fixed columns, parsed INFO, and sample data together
    combined_df <- cbind(
      fix_df[, c("CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER")],
      info_df,
      if (!is.null(sample_df)) sample_df else NULL
    )
    # Replace "." or empty strings "" with NA for clarity
    combined_df[combined_df == "." | combined_df == ""] <- NA
    # Return the processed variant data frame
    combined_df
  })
  
  # Populate dropdown dynamically with gene names from processed data
  # This will update the selectize input choices based on the data
  observe({
    df <- processed_data()
    if ("Gene_name" %in% colnames(df)) {
      updateSelectizeInput(session, "gene_filter",
                           choices = sort(unique(df$Gene_name)),
                           server = TRUE)
    }
  })
  
  # This reactive expression filters the processed data based on user input
  # i.e. user selects SOD1, table filters to show only rows with SOD1 in the Gene_name column
  filtered_data <- reactive({ # special function that automatically updates when inputs change to return a new value
    df <- processed_data()
    if (!is.null(input$gene_filter) && length(input$gene_filter) > 0) {
      if ("Gene_name" %in% colnames(df)) {
        df <- df[df$Gene_name %in% input$gene_filter, ]
      }
    }
    df
  })
  
  # This observer clears the selected genes in the filter when the clear filter button is clicked
  observeEvent(input$clear_filter, {
    updateSelectizeInput(session, "gene_filter", selected = character(0))
  })
  
  # This function creates the DataTable output for the filtered variant data
  # It applies various styles and formats to the table for better visualization
  output$variant_table <- DT::renderDataTable({ 
    df <- filtered_data()
    dt <- datatable(
      df,
      escape = FALSE,
      options = list(
        scrollX = TRUE, # Set horizontal scroll
        scrollY = "600px", # Set vertical scroll height
        paging = TRUE, # Creates pages for large tables
        pageLength = 20, # Adjust as needed or add an option to select 
        fixedHeader = TRUE, # Keeps header fixed while scrolling
        searchHighlight = TRUE, # Highlights matching search term in table
        autoWidth = TRUE, # Automatically adjust column widths based on content
        dom = 'Bfrtip', # Use Buttons extension for export options
        buttons = list(
          'copy', 'csv', 'excel', # Export/copy table in two formats (current view)
          list(extend = "colvis", text = "Show/Hide Columns") # Select columns to hide or show in table
          # TODO:  Hide some columns by default (e.g., INFO, FORMAT, etc. Then let user select which to show/hide
        )
      ),
      filter = "top", # Add filter boxes to the top of each column
      rownames = FALSE, # Hide row names
      extensions = c("Buttons", "FixedHeader", "FixedColumns") # Use extensions for buttons and fixed header/columns
    )

    # Format specific columns with background colors based on values
    dt <- DT::formatStyle( 
      dt, 
      "B_loss_AFmax",
      # Use styleInterval to set background color based on value ranges
      backgroundColor = DT::styleInterval( 
        0.05, c("#FB7575", "#6FF97C") # Red for low values, Green for high values
      ) 
    )
    dt <- DT::formatStyle(
      dt,
      "B_gain_AFmax",
      backgroundColor = DT::styleInterval(
        0.05, c("#FB7575", "#6FF97C")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "ACMG_class",
      backgroundColor = DT::styleEqual(
        c("1", "4", "5"), c("#6FF97C", "#FCCF8C", "#FB7575") # Green for class 1, Yellow for class 4, Red for class 5
        # TODO: this column can be filtered when running AnnotSV with -rankFiltering option
      )
    )
    dt <- DT::formatStyle(
      dt,
      "AnnotSV_ranking_score", 
      backgroundColor = DT::styleInterval(
        0.89, c("#6FF97C", "#FB7575") # Green for scores >= 0.89, Red for scores < 0.89
      )
    )
    dt <- DT::formatStyle(
      dt,
      "OMIM_morbid",
      backgroundColor = DT::styleEqual( 
        c("no", "yes"), c("#6FF97C", "#FB7575")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "OMIM_morbid_candidate",
      backgroundColor = DT::styleEqual(
        c("no", "yes"), c("#6FF97C", "#FB7575")
      )
    )
    dt # Return the formatted DataTable
  })

  # Table of column descriptions of INFO annotations
  output$column_description_table <- DT::renderDataTable({
   # Create a data frame with column names and descriptions
    desc <- data.frame( # Column = Column, Description = Description, stringsAsFactors = FALSE)
      Column = c("AnnotSV_ID", "SV_chrom", "SV_start", "SV_end", "SV_length", "SV_type",
                 "Samples_ID", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT",
                 "Annotation_mode", "Gene_name", "Closest_left", "Closest_right", "Gene_count",
                 "Tx", "Tx_version", "Tx_start", "Tx_end", "Overlapped_tx_length", "Overlapped_CDS_length",
                 "Overlapped_CDS_percent", "Frameshift", "Exon_count", "Location", "Location2",
                 "Dist_nearest_SS", "Nearest_SS_type", "Intersect_start", "Intersect_end", "RE_gene",
                 "P_gain_phen", "P_gain_hpo", "P_gain_source", "P_gain_coord",
                 "P_loss_phen", "P_loss_hpo", "P_loss_source", "P_loss_coord",
                 "P_ins_phen", "P_ins_hpo", "P_ins_source", "P_ins_coord",
                 "po_P_gain_phen", "po_P_gain_hpo", "po_P_gain_source", "po_P_gain_coord", "po_P_gain_percent",
                 "po_P_loss_phen", "po_P_loss_hpo", "po_P_loss_source", "po_P_loss_coord", "po_P_loss_percent",
                 "P_snvindel_nb", "P_snvindel_phen",
                 "B_gain_source", "B_gain_coord", "B_gain_AFmax",
                 "B_loss_source", "B_loss_coord", "B_loss_AFmax",
                 "po_B_gain_allG_source", "po_B_gain_allG_coord",
                 "po_B_gain_someG_source", "po_B_gain_someG_coord",
                 "po_B_loss_allG_coord", "po_B_loss_someG_source", "po_B_loss_someG_coord",
                 "ACMG", "HI", "TS", "DDD_HI_percent", "NCBI_gene_ID",
                 "OMIM_ID", "OMIM_phenotype", "OMIM_inheritance", "OMIM_morbid", "OMIM_morbid_candidate",
                 "LOEUF_bin", "GnomAD_pLI", "AnnotSV_ranking_score", "AnnotSV_ranking_criteria", "ACMG_class"),
      Description = c(
        "Unique identifier for the variant",
        "Chromosome containing the structural variant",
        "Start position of the variant",
        "End position of the variant",
        "Length of the variant",
        "Type of SV (DEL, DUP, INS, INV)",
        "Sample(s) carrying this variant",
        "VCF variant ID",
        "Reference allele",
        "Alternate allele",
        "Variant quality score",
        "Filter status (e.g., PASS)",
        "VCF INFO field content",
        "VCF FORMAT field content",
        "Annotation mode used (full, split, gene)",
        "Gene affected by the SV",
        "Closest gene upstream",
        "Closest gene downstream",
        "Number of overlapping genes",
        "Transcript ID",
        "Transcript version",
        "Transcript start position",
        "Transcript end position",
        "Length of transcript affected",
        "Length of CDS affected",
        "Percent of CDS overlapped",
        "Whether the variant causes a frameshift",
        "Number of exons affected",
        "Region type (intronic, exonic, etc.)",
        "Detailed location info",
        "Distance to nearest splice site",
        "Type of nearest splice site",
        "Overlap start coordinate with gene",
        "Overlap end coordinate with gene",
        "Regulatory element gene",
        "Phenotypes associated with predicted gain",
        "HPO terms for gain",
        "Source of gain prediction",
        "Coordinates of predicted gain",
        "Phenotypes associated with predicted loss",
        "HPO terms for loss",
        "Source of loss prediction",
        "Coordinates of predicted loss",
        "Phenotypes associated with predicted insertion",
        "HPO terms for insertion",
        "Source of insertion prediction",
        "Coordinates of predicted insertion",
        "Phenotypes for partial gain overlap",
        "HPO terms for partial gain",
        "Source for partial gain",
        "Coordinates for partial gain",
        "Percent region affected by partial gain",
        "Phenotypes for partial loss",
        "HPO terms for partial loss",
        "Source for partial loss",
        "Coordinates for partial loss",
        "Percent region affected by partial loss",
        "Number of pathogenic SNVs/indels nearby",
        "Phenotypes linked to SNVs/indels",
        "Source for known pathogenic gains",
        "Coordinates for known gains",
        "Max allele frequency for gains",
        "Source for known losses",
        "Coordinates for known losses",
        "Max allele frequency for losses",
        "Partial overlap gain (all genes) source",
        "Partial overlap gain (all genes) coord",
        "Partial overlap gain (some genes) source",
        "Partial overlap gain (some genes) coord",
        "Partial overlap loss (all genes) coord",
        "Partial overlap loss (some genes) source",
        "Partial overlap loss (some genes) coord",
        "ACMG rule code",
        "Haploinsufficiency score",
        "Triplosensitivity score",
        "Deciphering Developmental Disorders (DDD) dataset haploinsufficiency %",
        "NCBI Entrez gene ID",
        "OMIM ID",
        "OMIM phenotype",
        "OMIM inheritance pattern",
        "Gene is OMIM morbid",
        "OMIM morbid candidate flag",
        "Loss-of-function constraint bin",
        "gnomAD pLI score",
        "AnnotSV ranking score",
        "Criteria supporting the ranking - based on ACMG and ClinGen criteria (Riggs et al., 2020)",
        "Final ACMG classification (1–5)"
      )
    )
    DT::datatable(desc, options = list(pageLength = 30), rownames = FALSE) # Set page length to 30 rows 
  })
}

shinyApp(ui, server)
```

---
