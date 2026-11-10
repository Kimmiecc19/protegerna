# nf-core/protegerna (Nextflow implementation of Objective Three)

**Objective:** package the proteogenomic database workflow of Objective Three as an nf-core-style Nextflow DSL2 pipeline.

**Dissertation:** Chapter 5, Sections 5.2.10 and 5.3.13; Table 5.12 (end-to-end test on the synthetic dataset). The pipeline was
also run once on one participant (CASE-NEUWY079WUH FusionInspector calls with the cohort rMATS and SUPPA outputs). No database
searched in Chapters 5 or 6 was built with the pipeline.

The pipeline code is in [`nf_protegerna_workflow_dev/`](nf_protegerna_workflow_dev/README.md), whose README explains the
parameters, profiles and containers. It is also published at
[github.com/Kimmiecc19/nf_protegerna](https://github.com/Kimmiecc19/nf_protegerna).

## Runs reported in the dissertation

| Run | Command | Result |
| --- | --- | --- |
| 19 Oct 2026 (`tender_poincare`) | `nextflow run main.nf -profile test,docker --outdir results/test_yay` | Table 5.12: 6 synthetic records merged into 4 unique sequences; `results/test_yay/pipeline_info/` |
| 2 Nov 2026 (`grave_pauling`) | `nextflow run main.nf -profile publication ...` | 61,800 unique sequences; text after Table 5.12 |

The `work/` folders inside `nf_protegerna_workflow_dev/` are Nextflow working directories and should not be committed.
