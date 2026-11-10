# Proteogenomic database: design logic and methodological considerations

This page explains **why** the [Objective 3](Objective-3-Proteogenomic-Database) proteogenomic database workflow is built
the way it is. It covers the assumptions it makes, the rules that decide what enters the database, and how its outputs
should (and should not) be interpreted. It summarises Chapter 5 of the dissertation (Sections 5.1, 5.2.5–5.2.11 and
5.4) and Appendix 5A.4. For how to run the workflow, see [Objective 3](Objective-3-Proteogenomic-Database) and the
[nf-core/protegerna pipeline](nf-core-protegerna-Pipeline).

**Contents**
1. [What the workflow is for](#1-what-the-workflow-is-for)
2. [Why a new workflow: gaps in existing tools](#2-why-a-new-workflow-gaps-in-existing-tools)
3. [Translation rules treated as explicit assumptions](#3-translation-rules-treated-as-explicit-assumptions)
4. [Workflow overview](#4-workflow-overview)
5. [Core design principles](#5-core-design-principles)
6. [Splice branches: rMATS and SUPPA](#6-splice-branches-rmats-and-suppa)
7. [Fusion branch: FusionInspector](#7-fusion-branch-fusioninspector)
8. [Inclusion policies: what enters the search database](#8-inclusion-policies-what-enters-the-search-database)
9. [Merge, deduplication and quality control](#9-merge-deduplication-and-quality-control)
10. [Searching the database: DIA design](#10-searching-the-database-dia-design)
11. [Search database (v5) vs revised database (v7)](#11-search-database-v5-vs-revised-database-v7)
12. [Key parameters](#12-key-parameters)
13. [How to interpret the outputs](#13-how-to-interpret-the-outputs)
14. [Limitations and future directions](#14-limitations-and-future-directions)

---

## 1. What the workflow is for

The workflow links **RNA-level event detection** to **peptide-level investigation**. It takes alternative-splicing
events (rMATS, SUPPA) and gene-fusion candidates (FusionInspector) called from RNA-seq. It works out which of them could
plausibly change a protein-coding sequence, reconstructs and translates those sequences, and packages them with a
reference proteome as a database for data-independent acquisition (DIA) mass-spectrometry searches.

Within the PhD, it serves three purposes:

1. **Translate cohort RNA variation into searchable protein sequences**, in a biologically informed way.
2. **Provide a reproducible, auditable framework** for asking whether predicted splice- and fusion-derived proteins yield
   peptides distinguishable from the canonical proteome.
3. **Test whether transcriptome-informed candidates change the interpretation** of ALS DIA proteomics relative to a
   conventional reference-only search.

> **The scope is deliberately hypothesis-generating.** A sequence in the database means that an RNA event *could*
> plausibly encode a searchable protein product. It does not show that the protein is translated, stable or expressed.
> Protein-level support needs identification of suitable peptides under controlled false-discovery-rate (FDR) criteria.
> The strongest evidence comes from peptides that distinguish the reconstructed proteoform from canonical proteins and
> from other database entries.

The database is **cohort-informed** only in the sense that its candidate sequences were proposed from events called in
these samples. It is one pooled cohort-level database, searched against every proteomic run.

## 2. Why a new workflow: gaps in existing tools

Existing tools were reviewed to **identify gaps, not to benchmark** (Section 5.2.1; Appendix Table 5A.1). Candidates came
from the bio.tools proteomics (9,577) and multi-omics (9,007) records retrieved in [Objective 1](Objective-1-Biotools-Landscape).
They were searched for terms covering proteogenomic or custom database construction and classified manually. This found
14 database-construction tools and 24 related tools. moPepGen, too recent for bio.tools, was also reviewed. **The tools
were not run on the study data**, so the gaps below are a design rationale, not evidence of better performance.

The review found four recurring gaps:

| Gap in existing tools | Design response in this workflow |
| --- | --- |
| The link between a FASTA entry and the RNA evidence that produced it is often weak or lost | Every entry carries per-record provenance: caller, event, gene, transcript, sample/batch/condition, read support, frame, NMD status, peptide evidence and a stable inclusion/exclusion code |
| Heterogeneous callers are reduced to one generic junction or transcript representation | Caller-specific parsing of rMATS, SUPPA and FusionInspector, feeding shared reconstruction and translation code |
| Transcript choice and the reasons for keeping or excluding a candidate are rarely explicit | Transcript ambiguity is recorded and ranked; every exclusion gets a reason code |
| Database size is seldom controlled against what a bottom-up DIA search could actually detect | Candidates are judged by the tryptic peptides a DIA search could observe |

None of the reviewed database-construction tools reported direct use of FusionInspector, rMATS **and** SUPPA outputs, or a
design for cohort-scale DIA. How individual tools informed the design (Table 5.13):

| Tool or strategy | Design focus | What this workflow does differently | What remains stronger in the existing tool |
| --- | --- | --- | --- |
| customProDB | Databases from RNA-seq variants and novel junctions | Per-record provenance, caller-specific evidence rules, DIA-oriented filtering and release gates | SNV and indel incorporation |
| PGA | RNA-seq-to-database and search, incl. multi-frame translation | Annotation-aware reconstruction (multi-frame translation enlarges the search space) with explicit exclusion accounting | Tighter integration with searching and novel-peptide reporting |
| ProteomeGenerator / PG2 | Alignment, transcript assembly, ORF prediction, search | Keeps event-level evidence; models transcript choice explicitly | Starts from raw reads; complete sample-specific transcriptomes; more mature containerised execution |
| moPepGen | Graph-based enumeration of variant combinations | Prioritises traceability and controlled release for rMATS, SUPPA and FusionInspector evidence | Far broader event support, combinatorial variants, multiple proteases, stronger benchmarking |
| Naive junction / ORF FASTA | Simple, sensitive enumeration | Annotation-, frame- and peptide-aware filtering to avoid a large, uninterpretable search space | May keep genuine unexpected ORFs that conservative rules exclude |

The workflow therefore occupies a **deliberately narrower position** than moPepGen in particular. Its contribution is
evidence-aware reconstruction, traceability, release checks and explicit rules for what enters the searchable
database, not breadth of event enumeration.

## 3. Translation rules treated as explicit assumptions

Several translation rules decide which predicted products are plausible. The workflow makes them explicit assumptions
of database construction (Section 5.1):

- **The start codon sets the reading frame.** It is normally the first AUG in a favourable Kozak context. Leaky scanning
  and non-AUG initiation can give N-terminally different products, but the search-database build **does not model
  these** (alternative-start rescue was disabled).
- **Where an event falls decides whether the frame is preserved.** A skipped or deleted segment whose length isn't a
  multiple of three, a retained intron, or an out-of-frame fusion shifts the downstream frame and usually reaches a
  premature stop codon.
- **Nonsense-mediated decay (NMD).** A premature stop more than ~50–55 nt upstream of the last exon–exon junction
  typically triggers NMD. A stop in the last exon, or within that distance of the last junction, can give a truncated
  protein.
- **A novel product is detectable only through a peptide that spans its novel junction and is released by the protease.**
  Trypsin cleaves after K/R (not before P). A junction far from such sites, or inside a peptide too short or too long to
  detect, cannot be observed however abundant the protein is.
- **Breakpoint precision matters for translation, not just for detection.** An imprecise breakpoint makes the junction
  sequence, and so the predicted peptide, uncertain.

## 4. Workflow overview

A configuration-driven Python workflow (TOML settings) runs six stages (Section 5.2.6; Figures 5.1–5.3):

```text
                 GRCh38 genome + GENCODE v46 annotation (same releases as the RNA-seq calling)
                                         |
 (1) VALIDATE   reproduce GENCODE v46 protein translations  ── release gate: must pass before the merge
                                         |
 (2) RECONSTRUCT (independent producers, shared transcript-model / translation / consequence / peptide code)
        rMATS  ── project local event onto every compatible exon chain, event-type rules
        SUPPA  ── translate the complete annotated CDS of each listed isoform
        FusionInspector ── up to 3 ranked transcripts per partner, breakpoint resolution, junction translation
                                         |
        each producer: primary FASTA + audit tables (every candidate, kept or excluded, with reason codes)
                                         |
 (3) MERGE      + UniProt UP000005640 (canonical) + cRAP; exact-sequence deduplication, provenance aggregated
 (4) DIA FILTER (within the merge) ≥ 6 aa; ≥ 1 tryptic peptide of 7–40 aa, ≤ 3 missed cleavages
 (5) FASTA QC   sequence integrity, metadata consistency, searchability, strict quantmsdiann validation
 (6) REPORT     caller-stratified release report: ambiguity, frame, NMD, peptide evidence, exclusion codes
```

Code locations: stage 1 is `validate_gencode_translation.py`; stage 2 is `rmatstoprotein.py`, `suppatoprotein.py` and
`fusiontoprotein.py` (modules `proteogenomic/rmats_*`, `suppa_*`, `splice_*`, `fusion_*`); stages 3–4 are
`merge_proteogenomic_database.py` (`merge_*`); stage 5 is `proteogenomic_fasta_qc.py` (`qc_*`); stage 6 is
`release_report.py`. All are in `03_proteogenomic_database/03_search_database/proteogenomic_db/`, orchestrated by
`proteogenomic_workflow.py` and the TOML in `config/`.

## 5. Core design principles

### 5.1 Release gated on reference validation
Before any event-derived protein is built, the shared coordinate, CDS-phase, sequence-extraction and translation code
must **reproduce the GENCODE v46 protein translations**. Concordance is stratified by strand, complete/partial CDS,
single/multi-exon CDS and leading phase. The gate requires positive- and negative-strand, partial-CDS, multi-exon and
non-zero-phase models to be represented, and **zero unexplained mismatches**. The merge cannot run until this passes.
Known special cases are handled and recorded separately rather than counted as errors: non-ATG starts are normalised to
M, mitochondrial CDSs use the vertebrate mitochondrial code, selenocysteine is written as U, and partial CDS, missing
phase and readthrough candidates are tracked.

*Why:* it tests the coordinate, strand and phase implementation against a trusted reference before it is applied to
novel events, which greatly reduces avoidable software-induced translation errors.
*What it does not do:* it validates annotated-CDS reconstruction only, **not** the projection of rMATS events or fusion
breakpoints onto transcripts. Those were checked only by regression tests on synthetic events and, for fusions, by
agreement with FusionInspector. That agreement is consistency between two computational methods, not validation.

### 5.2 Caller-specific modelling of evidence
rMATS, SUPPA and FusionInspector report fundamentally different observations:

| Caller | What it reports | How the workflow treats it |
| --- | --- | --- |
| rMATS | Local event coordinates with junction counts and differential statistics, per batch CASE–CTRL comparison | Projected onto compatible annotated exon chains with event-type-specific rules |
| SUPPA | Annotated event structures naming the transcripts on each side (`events.ioe`), with per-sample PSI | The listed annotated isoforms are translated whole; no exon-chain editing |
| FusionInspector | Per-sample breakpoints, junction/spanning reads and predicted coding effect (after Arriba, STAR-Fusion and FusionCatcher merging and fusion-report scoring) | Reconstructed from the genome and annotation on ranked transcripts; caller predictions used only as a post hoc check |

Avoiding a single generic "novel junction" representation lets each caller's biological meaning inform reconstruction
and filtering. FusionInspector was chosen as the fusion input because it is one per-sample list combining the evidence
of all three callers, with read support quantified the same way for every fusion. It also provides the breakpoint
coordinates and coding annotations that reconstruction and the concordance check need.

### 5.3 Annotation-aware reconstruction, not multi-frame or ORF enumeration
Proteins are reconstructed from **GENCODE transcript models and the reference genome** (the same GRCh38 and GENCODE v46
used to call the events), not by translating assembled transcripts or all frames. Frames come from **GTF CDS phases**,
not from changes in CDS length. Translation is **consequence-aware**: each product is classified for start-codon
retention, frame, premature termination and predicted NMD before the translation strategy is chosen.
*Why:* broad multi-frame or ORF translation enlarges the search space and makes it harder to interpret.

### 5.4 Explicit management of transcript ambiguity
Splice events and breakpoints often fit several annotated transcripts. Rather than silently picking one:
- **rMATS:** every compatible transcript is reconstructed and ranked. Ties at the top are flagged as ambiguous.
- **SUPPA:** every transcript in the event is translated and compared with the closest transcript of the opposite group.
- **Fusions:** up to three ranked transcripts per partner are reconstructed (up to nine combinations), and combinations
  not evaluated because of the cap are counted.

The selected transcript, number of compatible and tied candidates, and top three ranked models are recorded. The search
database flagged 490,058 rMATS and 65,718 SUPPA records as transcript-ambiguous.

### 5.5 Separation of reconstruction, biological annotation and inclusion policy
The workflow answers three questions separately:
1. *Can* the protein be reconstructed?
2. *What* biological properties does it have (frame, NMD, start codon, peptide uniqueness)?
3. *Should* it enter the DIA database (a configurable policy)?

A reconstructable candidate can be excluded, for example for an incomplete CDS, no observable unique peptide, being
reference-equivalent, failing read-support thresholds or being a rescue-tier product. **Exclusion never deletes it from
the audit outputs**, and every exclusion carries a **stable reason code**. *Why:* attrition becomes reproducible and
reportable, avoiding both silently discarding candidates and treating successful translation as biological validity.
Lower-confidence alternative-start and ORF rescue products are kept in separate tiers (disabled in the search database).

### 5.6 Control of database expansion for bottom-up DIA
Candidates are judged by the peptides that could contribute to a DIA search. These include tryptic length,
missed-cleavage policy, uniqueness against the reference (also with I/L treated as equivalent), junction- or
breakpoint-spanning peptides, and exact-sequence redundancy. *Why:* a predicted protein that can't yield a
discriminating peptide enlarges the database (and the hypothesis space) without adding identification power.

### 5.7 Deduplication without loss of provenance
Identical protein sequences can come from different callers, events, transcripts, genes, samples and conditions. Exact
duplicates are collapsed **only once, in the authoritative merge**, and all contributing provenance is aggregated.
This keeps the many-to-one relationship between RNA events and protein products. It avoids both duplicated FASTA entries
and keeping only the first accession encountered.

### 5.8 Built as a releasable, reproducible workflow
TOML configurations are validated before a run. Each run writes a manifest with the resolved configuration, software
versions and input checksums (event files given as patterns are recorded by path only). Coordinate and translation code
is covered by unit and regression tests. The merge refuses to run unless validation passed and every input header has the
expected format. The Nextflow version runs every step in one pinned container. This reproducibility applies to the
workflow **as now implemented**, not retrospectively to the search database (see [Section 11](#11-search-database-v5-vs-revised-database-v7)).

## 6. Splice branches: rMATS and SUPPA

Both branches share GENCODE transcript-model loading, genome extraction, annotation-aware translation, consequence
classification and tryptic-peptide evidence. Transcript models are built once from a gffutils database of the GENCODE v46
GTF and indexed by versioned and unversioned IDs, gene IDs and symbols. They keep the GENCODE tags the inclusion rules
need (`cds_start_NF`, `cds_end_NF`, `non_ATG_start`, `stop_codon_readthrough`, selenocysteine). The branches differ in how
proteins are derived.

### 6.1 Event selection: called, not differentially spliced
The rnasplice quantification was **not** used to select events for the search database:
- **rMATS:** no FDR or inclusion-level-difference threshold (configured as max FDR 1.0, min |ΔPSI| 0). The only rule was
  at least **3 inclusion and 3 skipping junction reads** summed across samples, a minimal check that both isoforms were
  observed.
- **SUPPA:** a PSI filter (PSI ≥ 0.10 in ≥ 3 samples) is configured, but the PSI files supplied contained no values, so
  **no event was filtered**.

The filters are implemented and configurable, so restricting the database to quantitatively supported events needs only a
configuration change. In the search database, the splice component is therefore **annotation-compatible events called in
the cohort**, not events shown to be differentially spliced.

### 6.2 rMATS: event-specific reconstruction
- **Coordinates:** rMATS exon starts are 0-based half-open (BED-like) and GENCODE is 1-based closed, so starts are
  increased by 1 before comparison.
- **Compatible transcripts:** all transcripts of the gene are queried. One is kept only if its exon structure represents
  the event and, except for RI, the event interval overlaps the CDS. Transcripts are ranked by event nucleotides
  overlapping the CDS, and ties are flagged.
- **Event-type rules:**

| Event | Reconstruction |
| --- | --- |
| SE (skipped exon) | Included isoform keeps the exon chain; skipped isoform removes the exon. Events entirely in UTRs are dropped |
| A3SS / A5SS | Replace the affected exon boundary to make long and short splice-site isoforms |
| MXE | One exon chain per exon choice, so only one mutually exclusive exon is present; models already containing both are skipped |
| RI (retained intron) | Isoforms with and without the intron; retained coding sequence can extend, frameshift or prematurely stop the CDS |

- **Coding span:** each chain is clipped to the annotated coding span (start- to stop-codon coordinates), so altered
  sequence inside it is kept and UTRs are excluded. *Consequence:* translation can't run past the annotated stop. A
  frameshifted product with no in-frame stop inside the span ends at an **artificial terminus**, so the database lacks
  peptides from the true 3′-UTR extension.
- **Frame:** set from the GTF phase at the first reconstructed coding position, otherwise inferred from upstream coding
  length, with disagreements recorded (`frame_mismatch`). When the annotated start codon is kept, translation is anchored
  to it. **If the start codon is lost, the candidate is not translated** (Kozak-scored downstream-start and longest-ORF
  rescue were disabled).
- **Comparison:** each isoform is compared with its transcript's canonical CDS. Products identical to that CDS or
  protein are excluded.

### 6.3 SUPPA: annotated isoforms
SUPPA events list complete annotated transcripts (`alternative_transcripts`; reference = in `total_transcripts` but not
in the alternative list), so **no exon-chain editing is needed**. Each transcript with a CDS is translated in full from
its own start codon. It is compared with the **closest opposite-group transcript**, chosen by coding status, CDS
completeness, exon overlap, annotation quality (MANE Select / APPRIS principal, then TSL 1), CDS overlap and
length difference, with ties flagged. *Consequence:* the SUPPA branch can contribute **only annotated isoforms**.
Annotated non-coding transcripts that might contain unannotated ORFs are not represented.

### 6.4 Consequence assessment (both branches)
Frame status is assigned by comparing **codon phase at shared genomic positions** (for rMATS, where the altered chain
rejoins the CDS; for SUPPA, positions shared with the opposite isoform), not by the total change in CDS length. NMD is
predicted when the last nucleotide of a premature stop lies **≥ 55 nt upstream of the nearest downstream exon–exon
junction**, including 3′-UTR junctions.

## 7. Fusion branch: FusionInspector

The fusion branch **reconstructs coding sequences from the genome and GENCODE** rather than translating
FusionInspector's predicted transcripts. That keeps reconstruction independent of the caller's own model, which in turn
makes the post hoc concordance check meaningful.

1. **Parsing and aggregation.** The 411 per-sample abridged files are grouped by sample (ID from the file name). Within a
   sample, records with identical genes, chromosomes and breakpoints are merged into one event (max and summed reads
   kept).
2. **Transcript selection (per partner).** Transcripts are retrieved by gene ID (with or without version), then symbol.
   Off-chromosome transcripts are discarded if any lie on the breakpoint chromosome. Candidates are ranked by chromosome
   concordance, **CDS completeness**, exon support and CDS length. **FusionInspector's transcript is only a final
   tiebreaker**, and breakpoint position is not used in ranking. Compatibility with the breakpoint is tested afterwards.
   The top **three CDS-containing** transcripts per partner are kept, giving up to nine combinations.
3. **Breakpoint resolution in transcript space.** Genomic breakpoints can't be applied directly to mature transcripts
   (introns, strand, CDS boundaries). Exonic breakpoints are mapped directly, intronic ones are snapped to the nearest
   splice junction, and those outside the transcript to the nearest boundary. Original and resolved positions and the snap
   distance are kept. A **snap > 25 nt** (or a fallback-only placement) makes the reconstruction **low-confidence**. Short
   split reads place breakpoints at base resolution, so a large snap more likely means an intronic or unannotated splice
   site than alignment error. The 25-nt default (`max_breakpoint_snap_distance_nt`) is heuristic and comparable to JAFFAL's
   20-bp rule. Snapped breakpoints also need **≥ 2 junction reads**, because the reconstructed junction isn't directly
   observed.
4. **CDS assembly.** Donor CDS from the annotated start to the donor breakpoint, joined to the acceptor CDS from its
   breakpoint to the annotated stop (UTRs excluded; negative strands reverse-complemented). Assembly is at the nucleotide
   level, so **hybrid codons** spanning the breakpoint are read directly, and donor/acceptor nucleotide contributions are
   recorded.
5. **Frame classification.** Donor phase plus retained donor coding length is compared with acceptor phase plus upstream
   acceptor length (mod 3). Frame is **recorded, never "corrected"**: no breakpoint moves or inserted nucleotides. In the
   search database all 392,851 frame calls came from GTF phases.
6. **Translation and product classes.** Translation runs from the donor start to the **first in-frame stop**, never forced
   through the junction, because a ribosome stops at the first stop codon.

   | Product class | Meaning |
   | --- | --- |
   | Junction-spanning | Contains donor- and acceptor-derived residues; a true chimeric protein that can yield junction peptides |
   | Donor-only | Translation stops before the junction; a valid fusion transcript but no chimeric protein |
   | Early-stop | Frameshift whose first stop is ≤ 30 aa past the junction (`early_stop_aa_cutoff`; heuristic). Such tails can hold at most four searchable tryptic peptides, and frameshift truncations are often unstable |

7. **NMD.** As for splice products, but only junctions between retained coding segments count (UTRs aren't
   reconstructed), and stops in the last coding segment aren't NMD-competent.
8. **Junction peptides.** In silico tryptic digestion finds peptides containing at least one donor- and one acceptor-derived
   residue, or the hybrid residue. These are compared with the reference proteome for fusion specificity.
9. **Concordance with FusionInspector (post hoc only).** Categories: identical protein, same junction peptide, frame
   agreement only, discordant, no caller reference (Tables 5.3–5.4).

## 8. Inclusion policies: what enters the search database

All criteria are evaluated by each producer. Failures become exclusion codes, and the merge doesn't re-apply them.

**Splice products (rMATS and SUPPA)** enter the primary FASTA only if they are:
1. not predicted NMD;
2. retaining the annotated start codon;
3. for RI, in frame with no premature stop (plus ≥ 3 inclusion reads, no ambiguous bases, and a searchable peptide
   spanning the intron boundary);
4. not from a stop-codon-readthrough transcript (or, for altered rMATS CDSs, a selenocysteine transcript);
5. not from a `cds_start_NF` / `cds_end_NF` (incomplete) model;
6. carrying at least one tryptic peptide absent from the reference proteome (trypsin, 7–40 aa, ≤ 3 missed cleavages).

SUPPA candidates also need a peptide **absent from the closest opposite-group isoform**. A peptide shared with the
other side of the event can't show which splice choice was translated. Frameshift and premature-stop splice products
are **not** excluded.

**Fusion products** are ineligible if they are any of the following: low-confidence, unknown frame, failed splice-type
check, frameshift, predicted NMD, truncated, early-stop, donor-only, identical to a UniProt protein, from a partner with
incomplete CDS or < 30 retained coding nt, shorter than 30 aa, a snapped breakpoint with < 2 junction reads, a
selenocysteine/readthrough/mitochondrial partner, or **lacking a reference-unique junction-spanning peptide**.

**Why the fusion policy is stricter.** The parts of a fusion protein either side of the junction are just partner-protein
sequence, so **only the junction can distinguish a fusion product**. Out-of-frame or truncated fusion products are also
unlikely to be stable. Splice products need only a reference-unique peptide anywhere in the protein.

> **Search-database deviations** (corrected in the revised code; see [Section 11](#11-search-database-v5-vs-revised-database-v7)):
> criterion 6 was **not applied to rMATS** (1,514 of 18,809 distinct rMATS sequences lacked a reference-unique peptide).
> rMATS candidates failing the opposite-isoform peptide check (6,571 records) were still written to the FASTA with a flag,
> and 636 sequences shared with the reference proteome stayed in the database.

## 9. Merge, deduplication and quality control

**Merge (stages 3–4).** It runs only if GENCODE validation passed and every input header has the expected format.
Producer FASTAs are combined with **UniProt UP000005640** (canonical, 20,663 entries) and **cRAP** (116 entries). The
database is **target-only**: DIA-NN generates decoys internally, and any decoy-style identifier stops the merge. Rescue
tiers are removed, empty or invalid sequences stop the run, proteins < 6 aa are dropped, and only proteins with ≥ 1
tryptic peptide (7–40 aa, ≤ 3 missed cleavages) are kept. Sequences are normalised and indexed by MD5 and SHA-256.
Identical sequences are collapsed into one `PGDB_U…` entry that aggregates genes, transcripts, events, sources and
samples. Peptide evidence is then **recalculated for the whole merged database**: uniqueness in the full target
database and among proteogenomic entries (exact and I/L-equivalent), junction crossing, and number of distinguishing b/y
ions.

**QC (stage 5).** Checks for empty sequences, invalid residues, internal or terminal stops, duplicate IDs and sequences,
length distributions, and theoretical tryptic searchability. QC *reports* duplicates but deliberately doesn't collapse
them, because collapsing belongs to the merge. A strict quantmsdiann validation checks unique accessions, no duplicates
or decoys, valid residues, protein record type, no rescue tiers, and organism annotation.

**Report (stage 6).** Per caller: records, transcript ambiguity, frame status, predicted NMD, peptide evidence and the
frequency of each exclusion code.

In the search database, 157,726 of 157,792 input records passed DIA filters (56 lacked an eligible peptide, 10 were too
short). Exact-sequence aggregation reduced them to **80,657 unique sequences** (48.9% redundancy).

## 10. Searching the database: DIA design

The database was searched with **bigbio/quantmsdiann 2.2.0 (DIA-NN 1.8.1)** on all 417 DIA runs (six batches). Each
batch was also searched against a **reference-only** database, with spectra, digestion, modifications, tolerances,
DIA-NN settings, FDR control and sample inclusion all held constant.

Design points to keep in mind:
- **The comparison is confounded.** The reference-only database (all reviewed Swiss-Prot human entries with isoforms,
  plus cRAP) was built before the workflow existed. The proteogenomic database's reference component is the canonical
  proteome **without** the ~22,000 isoforms. Differences therefore reflect both the added sequences and the missing
  isoforms. A matched-reference search would be needed to separate them.
- **FDR is whole-search.** Results use 1% precursor and protein-group q-values from DIA-NN target–decoy competition. That
  doesn't give the error rate within the small non-reference subset, which can be higher. Class-specific FDR and entrapment
  searches were feasible but not implemented, so **non-canonical peptides are candidates, not error-controlled
  identifications**.
- **Novel peptide definition (shared with Objective 4):** passes the FDR filters, is contained only in splice- or
  fusion-derived entries, and is absent (I = L) from UniProt UP000005640 canonical plus additional isoforms and from
  GENCODE v46 translations. In Chapter 5 it must also be absent from the reference-only database and pass run-level
  protein-group q ≤ 0.01.
- **Failed runs** (< 1,000 precursors) stay in their batch's search but are excluded from Objective 4's biological analyses.
- **Replicate structure.** Repeated measurements of the recurring control line CTRL-NEUEU392AE8 (BDC/BTC) are processed
  with each batch but **never counted as independent participants**.

## 11. Search database (v5) vs revised database (v7)

Two builds exist, and the distinction matters for interpreting every result:

| | Search database (v5) | Revised database (v7) |
| --- | --- | --- |
| Used for | **Every proteomic search and peptide result** in Chapters 5 and 6 | Composition comparison only; **never searched** |
| Status | Superseded: fusion reconstruction found internally inconsistent | Built with corrected code and mostly stricter filters |
| Size | 80,657 sequences | 30,031 sequences |
| Config | `03_search_database/config/workflow.publication.v5.toml` | `04_revised_database/config/workflow.publication.frozen.toml` |

Same genome, annotation, GENCODE check, digestion rules, fusion parameters and merge rules. The revised code differs in
six ways:

1. **Explicit conservative rules for every producer** (`quantms_conservative = true` for rMATS). This made the existing
   behaviour explicit rather than changing it.
2. **rMATS failures excluded** (`include_failed_filter_proteins = false`), and the reference-unique peptide requirement
   (previously never applied to rMATS) is enforced.
3. **Retained introns** need ≥ 1 inclusion read rather than 3 (the one relaxed rule).
4. **Fusion reproducibility.** v5 collected parallel-worker results in finishing order and restarted event IDs per sample,
   so fusion output depended on worker timing (the likely reason repeated builds differed). v7 sorts by sample and uses
   sample-qualified event IDs. Out-of-span breakpoints are always low-confidence.
5. **Annotated isoforms aren't counted as novel.** Uniqueness is assessed against canonical plus additional UniProt
   isoforms. This alone shrank SUPPA from 40,320 to 104 sequences, showing that most SUPPA entries offered no peptide
   beyond annotated isoforms.
6. **Input handling.** SUPPA `events.ioe` is read once, not six times (consequence records fell from 7,541,514 to
   1,250,303, without changing the search space). Producer FASTAs must carry a run manifest bound to the validated
   genome and annotation, and chrM and MT are both recognised.

*Lesson:* the definition of a "reference-unique" peptide largely decides database size, so **releases should be compared at
the sequence level, not by entry counts**. The corrected code does not retrospectively validate any v5 peptide assignment.
The Nextflow pipeline bundles the revised code, so it isn't expected to reproduce the 80,657 v5 sequences exactly.

## 12. Key parameters

Search-database settings (`workflow.publication.v5.toml`; workflow version 0.1.0):

| Setting | Value |
| --- | --- |
| Genome / annotation | GRCh38 primary assembly (Ensembl 112) / GENCODE v46 |
| GENCODE concordance | 0 unexplained mismatches |
| rMATS FDR / \|ΔPSI\| filter | Not applied (1.0 / 0) |
| rMATS junction reads | ≥ 3 inclusion and ≥ 3 skipping (summed); RI ≥ 3 inclusion |
| SUPPA PSI filter | Configured (PSI ≥ 0.10 in ≥ 3 samples) but no PSI values supplied, so not applied |
| Reference-unique peptide | Required for SUPPA; **not applied to rMATS**; junction-spanning required for fusions |
| Fusion transcripts per partner | 3 |
| Max breakpoint snap distance | 25 nt |
| Junction reads for snapped breakpoints | ≥ 2 |
| Min retained coding nt per partner | 30 |
| Early-stop cutoff | 30 aa |
| Excluded for all sources | Incomplete CDS (`cds_start_NF` / `cds_end_NF`), predicted NMD |
| Rescue tiers | Disabled |
| Digestion | Trypsin, 7–40 aa, ≤ 3 missed cleavages |
| Minimum protein length at merge | 6 aa |
| Reference / contaminants | UniProt UP000005640 release 2026_01 (canonical) / cRAP (2023-07-04, 116 entries) |

## 13. How to interpret the outputs

Chapter 5 uses **three levels of evidential strength**. Keep them distinct:

| Level | Definition | What it supports |
| --- | --- | --- |
| **Predicted protein** | A sequence reconstructed from RNA-level evidence (every database entry) | A hypothesis only |
| **Peptide-supported sequence** | A predicted protein to which at least one observed peptide maps | Consistent with the prediction, but the peptide may be shared with other proteins |
| **Uniquely inferred proteoform** | Supported by peptide evidence that discriminates it from the reference proteome and other candidates | The strongest claim; ideally also needs orthogonal confirmation |

Two kinds of non-reference peptide are also distinguished:
- **Reference-unique peptide:** absent from the reference proteome but need not cross the altered sequence. It can support
  the predicted protein without demonstrating the event.
- **Event-defining peptide:** crosses the altered splice junction or fusion breakpoint, so it distinguishes the event
  product from the unaltered partner proteins.

Other points for interpretation:
- **A pooled database decouples peptide from participant.** Detecting a peptide in a file doesn't mean the event was called
  in that participant's RNA. Provenance tables keep fusion sample IDs and rMATS batches (SUPPA carries none), so matched-RNA
  support can be checked, which [Objective 4](Objective-4-Multi-Omics-Integration) does (Table 5.11).
- **Splice-derived peptides can't be attributed to their predicted event.** The libraries were reverse-stranded but
  processed as forward-stranded in nf-core/rnasplice, which invalidated the Salmon, SUPPA and rMATS quantification
  (Section 7.3.3). Splice entries therefore lack valid RNA support in these samples.
- **What the results showed.** The workflow built a traceable, size-controlled database that a standard DIA pipeline could
  search. Adding ~60,000 event-derived sequences changed distinct precursors by −1.6% to +0.3% across batches. Most
  custom-only peptides came from annotated UniProt isoforms. Only six distinct peptides were absent from both the
  reference-only searches and UniProt. Over 99% of peptides mapping to fusion sequences also mapped to reference proteins.
  Specific protein identifications per file fell by ~28%, which can't be attributed to the added sequences alone (see the
  confounded comparison above). **No disease-related conclusion is drawn.**
- **Before interpreting any candidate,** it needs spectral and chromatographic inspection, event-discriminating fragment
  ions, comparison with a synthetic peptide or targeted assay, and RNA support in the matching samples. Fusion candidates
  also need a repeat revised-database build to confirm between-run reproducibility.

## 14. Limitations and future directions

**Inherent to short-read RNA-seq and bottom-up DIA**
- rMATS and SUPPA events are local and projected onto annotated models, so complete transcripts and the phasing of several
  events on one molecule can't be established. Reconstruction depends on the GENCODE release, so unannotated exons, starts
  and ORFs are missed. Fusion proteins are conditional on the caller, the breakpoint and the transcripts chosen.
- Genuine events may yield no detectable tryptic peptide, so absence of a peptide isn't absence of translation.
- Every added sequence enlarges the hypothesis space. A cohort-level database also weakens sample-level RNA–protein
  concordance.
- The reanalysed Answer ALS DIA data (wide SWATH windows, no sample access, no DDA runs) ruled out targeted,
  synthetic-peptide and DIA–DDA confirmation.

**Deliberately narrow event scope**
- Splicing and fusions only: no SNVs, indels, RNA editing, circular RNAs or upstream ORFs. Mutant ALS proteins (e.g. SOD1,
  TARDBP, FUS) are detectable only through peptides shared with the wild type.
- The workflow inherits the callers' biases, and rMATS–SUPPA agreement is supporting rather than independent evidence.

**Appropriate use.** The workflow suits building an **auditable, rule-limited database** from splice- and fusion-caller
outputs for DIA, where traceability and search-space control are priorities (the limits themselves haven't been
optimised). It suits exhaustive discovery of variant-combination peptides less well; broader tools such as moPepGen fit
that better. Nothing in it is ALS-specific: any cohort with rMATS, SUPPA and FusionInspector outputs, a GENCODE annotation
and a UniProt proteome could use it, with thresholds suited to its proteomic depth (not yet tested beyond Answer ALS).

**Future directions** (Section 5.4.10)
1. **First priority:** rebuild with the rMATS FDR, inclusion-level and SUPPA PSI filters enabled, so splice entries need
   quantitative support (a configuration change only).
2. Integrate long-read RNA-seq to constrain transcript structure and phasing.
3. Evaluate tiered or sample-specific databases with separate FDR control.
4. Add event classes selectively, where they can be validated against a reference.
5. Develop targeted assays for the highest-confidence event-defining peptides.
6. Admit unannotated or non-reference sequence (genome-guided or long-read assembly with StringTie, IsoQuant or FLAIR
   classified by gffcompare or SQANTI3; participant-specific genomes via PrecisionProDB or pypgatk) in a **separate tier
   with its own FDR assessment**.
7. Establish cohort-scale reproducibility and maintenance of the Nextflow pipeline, compared at the sequence level with a
   standalone release.

## Key literature

The published work behind this design, and what each work justifies, is listed in
[Literature and method justification](Literature-and-Method-Justification#objective-3-proteogenomic-database).
