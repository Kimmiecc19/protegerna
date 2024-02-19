# NFCORE_RAREDISEASE:RAREDISEASE:ANNOTATE_SNVS:BCFTOOLS_VIEW 

## First error:

```
Command executed:

  bcftools view \
      --output SD1_rohann_vcfanno_filter.vcf.gz \
       \
       \
       \
      --output-type z --exclude "INFO/GNOMADAF > 0.70 | INFO/GNOMADAF_popmax > 0.70"  \
      --threads 3 \
      SD1.vcf.gz

  cat <<-END_VERSIONS > versions.yml
  "NFCORE_RAREDISEASE:RAREDISEASE:ANNOTATE_SNVS:BCFTOOLS_VIEW":
      bcftools: $(bcftools --version 2>&1 | head -n1 | sed 's/^.*bcftools //; s/ .*$//')
  END_VERSIONS

Command exit status:
  255

Command output:
  (empty)

Command error:
  INFO:    Environment variable SINGULARITYENV_NXF_TASK_WORKDIR is set, but APPTAINERENV_NXF_TASK_WORKDIR is preferred
  INFO:    Environment variable SINGULARITYENV_NXF_DEBUG is set, but APPTAINERENV_NXF_DEBUG is preferred
  [W::bcf_hdr_register_hrec] The definition of Flag "INFO/AZ" is invalid, forcing Number=0
  [W::bcf_hdr_register_hrec] The definition of Flag "INFO/HW" is invalid, forcing Number=0
  Error: cannot use arithmetic operators to compare strings and numbers
```

# Second error on same step:

```
Command executed:

  bcftools view \
      --output SD1_rohann_vcfanno_filter.vcf.gz \
       \
       \
       \
      --output-type z --exclude "INFO/GNOMADAF > 0.70 | INFO/GNOMADAF_popmax > 0.70"  \
      --threads 3 \
      SD1.vcf.gz

  cat <<-END_VERSIONS > versions.yml
  "NFCORE_RAREDISEASE:RAREDISEASE:ANNOTATE_SNVS:BCFTOOLS_VIEW":
      bcftools: $(bcftools --version 2>&1 | head -n1 | sed 's/^.*bcftools //; s/ .*$//')
  END_VERSIONS

Command exit status:
  255

Command output:
  (empty)
```

# Possible solutions

Command error:
  INFO:    Environment variable SINGULARITYENV_NXF_TASK_WORKDIR is set, but APPTAINERENV_NXF_TASK_WORKDIR is preferred
  INFO:    Environment variable SINGULARITYENV_NXF_DEBUG is set, but APPTAINERENV_NXF_DEBUG is preferred
  Failed to read from SD1.vcf.gz: unknown file type
```

