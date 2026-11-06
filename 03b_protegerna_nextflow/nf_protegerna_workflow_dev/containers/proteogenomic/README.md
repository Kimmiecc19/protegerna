# Runtime image

From the pipeline repository root on the Linux server:

```bash
apptainer build protegerna.sif containers/proteogenomic/Apptainer.def
apptainer test protegerna.sif
```

Used on -Code WSL

```bash
sudo apptainer build protegerna.sif Apptainer.def
```

Use the resulting absolute SIF path as `proteogenomic_container`. Building requires the server's usual Apptainer build permissions; use its configured build service or fakeroot support if necessary.

The image pins Python 3.11.13 and the dependencies from the authoritative reconstruction package. Nextflow stages the bundled source into each task, so there is no unpublished Conda package or external source checkout to install. Module `environment.yml` files describe equivalent dependencies.

The matching Dockerfile is an alternative way to build the same dependency image before importing it into Apptainer. The pipeline always runs with Apptainer and the local executor; select `-profile publication` or `-profile test`.
