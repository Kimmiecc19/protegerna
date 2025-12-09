# RareDisease Pipeline Peddy Error

This is most likely an issue with the `samplesheet.csv` file.

**ERROR**:
```
Error executing process > 'NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SV:GENMOD_MODELS (SD1)'

Caused by:
  Process `NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SV:GENMOD_MODELS (SD1)` terminated with an error exit status (1)

Command executed:

  genmod \
      models \
       \
       \
      --family_file SD1.ped \
      --processes 3 \
      --outfile SD1_models.vcf \
      SD1_annotate.vcf

  cat <<-END_VERSIONS > versions.yml
  "NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SV:GENMOD_MODELS":
      genmod: $(echo $(genmod --version 2>&1) | sed 's/^.*genmod version: //' )
  END_VERSIONS

Command exit status:
  1

Command output:
  (empty)

Command error:
  INFO:    Environment variable SINGULARITYENV_NXF_TASK_WORKDIR is set, but APPTAINERENV_NXF_TASK_WORKDIR is preferred
  INFO:    Environment variable SINGULARITYENV_NXF_DEBUG is set, but APPTAINERENV_NXF_DEBUG is preferred
  Traceback (most recent call last):
    File "/usr/local/bin/genmod", line 10, in <module>
      sys.exit(cli())
    File "/usr/local/lib/python3.9/site-packages/click/core.py", line 722, in __call__
      return self.main(*args, **kwargs)
    File "/usr/local/lib/python3.9/site-packages/click/core.py", line 697, in main
      rv = self.invoke(ctx)
    File "/usr/local/lib/python3.9/site-packages/click/core.py", line 1066, in invoke
      return _process_result(sub_ctx.command.invoke(sub_ctx))
    File "/usr/local/lib/python3.9/site-packages/click/core.py", line 895, in invoke
      return ctx.invoke(self.callback, **ctx.params)
    File "/usr/local/lib/python3.9/site-packages/click/core.py", line 535, in invoke
      return callback(*args, **kwargs)
    File "/usr/local/lib/python3.9/site-packages/click/decorators.py", line 17, in new_func
      return f(get_current_context(), *args, **kwargs)
    File "/usr/local/lib/python3.9/site-packages/genmod/commands/annotate_models.py", line 128, in models
      family_parser = FamilyParser(family_file, family_type)
    File "/usr/local/lib/python3.9/site-packages/ped_parser/parser.py", line 110, in __init__
      self.families[fam].family_check()
    File "/usr/local/lib/python3.9/site-packages/ped_parser/family.py", line 98, in family_check
      raise e
    File "/usr/local/lib/python3.9/site-packages/ped_parser/family.py", line 95, in family_check
      self.check_parent(father, father=True)
    File "/usr/local/lib/python3.9/site-packages/ped_parser/family.py", line 132, in check_parent
      raise PedigreeError(self.family_id, parent_id,
  ped_parser.exceptions.PedigreeError: Parent is not in family.
```

# Possible Solutions:

```
1. Remove `case_id` from samplesheet -> Did not work
2. Add zero to `paternal_id` and `maternal_id` -> Did not work
```

# Actual Solution:

```
Change the samplesheet to: 

sample,lane,fastq_1,fastq_2,sex,phenotype,paternal_id,maternal_id,case_id
SRR15174692,1,/home/kcoetzer/SD/SRR15174692_1.fastq.gz,/home/kcoetzer/SD/SRR15174692_2.fastq.gz,other,2,0,0,SD1
```
