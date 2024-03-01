# SyncManager error running Genmod:

The following error was on hemera:
```
ERROR ~ Error executing process > 'NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SNV:GENMOD_MODELS (SD1)'

Caused by:
  Process `NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SNV:GENMOD_MODELS (SD1)` terminated with an error exit status (1)

Command executed:

  genmod \
      models \
       --whole_gene  \
       \
      --family_file SD1.ped \
      --processes 3 \
      --outfile SD1_models.vcf \
      SD1_annotate.vcf

  cat <<-END_VERSIONS > versions.yml
  "NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SNV:GENMOD_MODELS":
      genmod: $(echo $(genmod --version 2>&1) | sed 's/^.*genmod version: //' )
  END_VERSIONS

Command exit status:
  1

Command output:
  (empty)

Command error:
  Process SyncManager-1:
  Traceback (most recent call last):
    File "/usr/local/lib/python3.9/multiprocessing/process.py", line 315, in _bootstrap
      self.run()
    File "/usr/local/lib/python3.9/multiprocessing/process.py", line 108, in run
      self._target(*self._args, **self._kwargs)
    File "/usr/local/lib/python3.9/multiprocessing/managers.py", line 583, in _run_server
      server = cls._Server(registry, address, authkey, serializer)
    File "/usr/local/lib/python3.9/multiprocessing/managers.py", line 156, in __init__
      self.listener = Listener(address=address, backlog=16)
    File "/usr/local/lib/python3.9/multiprocessing/connection.py", line 453, in __init__
      self._listener = SocketListener(address, family, backlog)
    File "/usr/local/lib/python3.9/multiprocessing/connection.py", line 596, in __init__
      self._socket.bind(address)
  OSError: [Errno 98] Address already in use

  Aborted!
```

# Solution:

There is an issue with version 3.7.4 of Genmod (https://github.com/Clinical-Genomics/genmod/blob/master/CHANGELOG.md)

Update to the new container: 3.8.2 (https://depot.galaxyproject.org/singularity/genmod:3.8.2--pyhdfd78af_0)

This can be specified as the following in the config file:

```
withName: 'NFCORE_RAREDISEASE:RAREDISEASE:RANK_VARIANTS_SNV:GENMOD_MODELS' {
    container = "biocontainers/genmod:3.8.2--pyhdfd78af_0"
}
```

Or the main.nf script in modules/nf-core/genmod/models can be changed to the following:

```
 conda "bioconda::genmod=3.8.2"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/genmod:3.8.2--pyhdfd78af_0':
        'biocontainers/genmod:3.8.2--pyhdfd78af_0' }"
```
