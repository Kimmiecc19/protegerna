# QC structural-refactor equivalence fixture

`input.fasta` is the frozen pre-refactor stimulus. It contains distinct headers
sharing a sequence, an internal stop, a short protein, and an invalid residue.

The files under `expected/` are frozen byte-level outputs captured before the
QC responsibilities were separated. `test_qc_equivalence.py` reruns the new
orchestrator and compares:

- filtered FASTA sequences and complete headers;
- the filtered-record exclusion table;
- parsed header metadata;
- the per-record sequence audit table; and
- the aggregate QC summary.

Changing these files is therefore a biological/output-contract change, not a
routine snapshot update, and requires an explicit review of the corresponding
FASTA, header, exclusion, and audit differences.
