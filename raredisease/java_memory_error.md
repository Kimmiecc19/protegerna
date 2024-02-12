# Java memory issue

This error was encountered on the hemera server while running nf-core/raredisease with one WES file as input

```

**ERROR ~ Error executing process > 'NFCORE_RAREDISEASE:RAREDISEASE:QC_BAM:PICARD_COLLECTHSMETRICS (SRR15174692)'**

**Caused by:**
  Process `NFCORE_RAREDISEASE:RAREDISEASE:QC_BAM:PICARD_COLLECTHSMETRICS (SRR15174692)` terminated with an error exit status (1)

**Command executed:**

picard \
    -Xmx4915M \
    CollectHsMetrics \
     \
    --REFERENCE_SEQUENCE genome.fa \
    --BAIT_INTERVALS home_bait.intervals_list \
    --TARGET_INTERVALS home_target.interval_list \
    --INPUT SRR15174692_sorted_md.bam \
    --OUTPUT SRR15174692_hsmetrics.CollectHsMetrics.coverage_metrics

cat <<-END_VERSIONS > versions.yml
"NFCORE_RAREDISEASE:RAREDISEASE:QC_BAM:PICARD_COLLECTHSMETRICS":
    picard: $(echo $(picard CollectHsMetrics --version 2>&1) | grep -o 'Version:.*' | cut -f2- -d:)
END_VERSIONS

**Command exit status:**
  1

**Command output:**
  (empty)

**Command error:**
  - INFO: Environment variable SINGULARITYENV_NXF_TASK_WORKDIR is set, but APPTAINERENV_NXF_TASK_WORKDIR is preferred
  - INFO: Environment variable SINGULARITYENV_NXF_DEBUG is set, but APPTAINERENV_NXF_DEBUG is preferred
  - /usr/local/bin/picard: line 5: warning: setlocale: LC_ALL: cannot change locale (en_US.UTF-8): No such file or directory
  - 06:41:17.612 INFO  NativeLibraryLoader - Loading libgkl_compression.so from jar:file:/usr/local/share/picard-3.0.0-1/picard.jar!/com/intel/gkl/native/libgkl_compression.so
  - [Mon Feb 12 06:41:17 GMT 2024] CollectHsMetrics --BAIT_INTERVALS home_bait.intervals_list --TARGET_INTERVALS home_target.interval_list --INPUT SRR15174692_sorted_md.bam --OUTPUT SRR15174692_hsmetrics.CollectHsMetrics.coverage_metrics --REFERENCE_SEQUENCE genome.fa --METRIC_ACCUMULATION_LEVEL ALL_READS --NEAR_DISTANCE 250 --MINIMUM_MAPPING_QUALITY 20 --MINIMUM_BASE_QUALITY 20 --CLIP_OVERLAPPING_READS true --INCLUDE_INDELS false --COVERAGE_CAP 200 --SAMPLE_SIZE 10000 --ALLELE_FRACTION 0.001 --ALLELE_FRACTION 0.005 --ALLELE_FRACTION 0.01 --ALLELE_FRACTION 0.02 --ALLELE_FRACTION 0.05 --ALLELE_FRACTION 0.1 --ALLELE_FRACTION 0.2 --ALLELE_FRACTION 0.3 --ALLELE_FRACTION 0.5 --VERBOSITY INFO --QUIET false --VALIDATION_STRINGENCY STRICT --COMPRESSION_LEVEL 5 --MAX_RECORDS_IN_RAM 500000 --CREATE_INDEX false --CREATE_MD5_FILE false --help false --version false --showHidden false --USE_JDK_DEFLATER false --USE_JDK_INFLATER fals
  - [Mon Feb 12 06:41:17 GMT 2024] Executing as kcoetzer@hemera on Linux 5.15.0-94-generic amd64; OpenJDK 64-Bit Server VM 17.0.3-internal+0-adhoc..src; Deflater: Intel; Inflater: Intel; Provider GCS is not available; Picard version: Version:3.0.0
  - [Mon Feb 12 06:41:19 GMT 2024] picard.analysis.directed.CollectHsMetrics done. Elapsed time: 0.03 minutes.
  - Runtime.totalMemory()=5154799616
  - To get help, see http://broadinstitute.github.io/picard/index.html#GettingHelp
  - Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
    - at picard.analysis.directed.TargetMetricsCollector$Coverage.<init>(TargetMetricsCollector.java:962)
    - at picard.analysis.directed.TargetMetricsCollector.<init>(TargetMetricsCollector.java:307)
    - at picard.analysis.directed.HsMetricCollector.<init>(HsMetricCollector.java:79)
    - at picard.analysis.directed.CollectHsMetrics.makeCollector(CollectHsMetrics.java:173)
    - at picard.analysis.directed.CollectHsMetrics.makeCollector(CollectHsMetrics.java:86)
    - at picard.analysis.directed.CollectTargetedMetrics.doWork(CollectTargetedMetrics.java:142)
    - at picard.cmdline.CommandLineProgram.instanceMain(CommandLineProgram.java:289)
    - at picard.cmdline.PicardCommandLine.instanceMain(PicardCommandLine.java:104)
    - at picard.cmdline.PicardCommandLine.main(PicardCommandLine.java:114)

```

# Possible Solutions

**1. ADD:** `export _JAVA_OPTIONS="-Xms32g -Xmx32g"` before running command or add to config file. -> Did not work

**2. ADD:** `NXF_OPTS='-Xms1g -Xmx16g'` to ~/.bashrc file -> Did not work

**3. ADD:** `process {
    executor = 'local'
    max_memory = '100 GB'
    max_cpus = '8'
}` To config file -> Did not work

**4. ADD:** from: ~/nf/nf-core-raredisease_1.1.1/configs/conf/pipeline/raredisease/hasta.config add the following to personal config file before running again

```
process {
    withName:'DEEPVARIANT' {
        cpus   = { check_max( 16      * task.attempt, 'cpus' ) }
        memory = { check_max( 80.GB   * task.attempt, 'memory' ) }
    }
     // Java memory fixes
    withName:'QUALIMAP_BAMQC' {
        cpus   = { check_max( 16      * task.attempt, 'cpus' ) }
        memory = { check_max( 80.GB   * task.attempt, 'memory' ) }
    }
    withName:'PICARD_MARKDUPLICATES' {
         cpus   = { check_max( 16      * task.attempt, 'cpus' ) }
        memory = { check_max( 80.GB   * task.attempt, 'memory' ) }
    }
}
```

```
