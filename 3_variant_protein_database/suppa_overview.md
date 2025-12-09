
---

# **1. Interval Arithmetic Layer**

### **What it does**

This layer supplies all the operations needed to manipulate genomic intervals (exons, introns, CDS fragments).
Functions include overlap checks, interval subtraction, interval replacement, interval merging, and intersections.

### **Why it is included**

Alternative splicing is fundamentally an operation on **genomic intervals**:

* Skipped exons require removing intervals.
* A3/A5 events require trimming or extending terminal exon boundaries.
* MXE requires swapping intervals.
* Intron retention requires inserting intronic intervals.

Accurate interval logic is absolutely essential because **protein variants depend on exact genomic coordinates**. These functions enforce correctness in exon-chain reconstruction and prevent misordered, overlapping, or biologically impossible structures.

---

# **2. Transcript and Event Interpretation Layer**

This layer integrates *annotation* (GTF) and *splicing events* (SUPPA).

## **2.1 Transcript Model Construction**

The script reads the GTF (via gffutils) to create a complete model for each transcript:

* gene metadata
* strand
* ordered exon coordinates
* CDS coordinates and codon phases
* versionless aliases for transcript IDs

### **Why it is included**

Proteogenomics requires precise knowledge of:

* where CDS starts and stops,
* which exons comprise a transcript,
* how many nucleotides precede the first coding position (for frame),
* which transcript corresponds to which SUPPA entry.

Accurate CDS/phasing information is indispensable for deriving correct ORFs. The gffutils approach ensures no loss of annotation detail and resolves ID inconsistencies.

---

## **2.2 SUPPA Event Parsing**

The script interprets SUPPA’s event_id strings to extract:

* event type (SE, A3, A5, MXE, RI)
* genomic coordinates
* event strand
* transcript sets supporting each isoform

### **Why this is included**

SUPPA encodes alternative splicing outcomes in a compressed format. To modify exon chains, the script must translate these identifiers into concrete coordinate operations. Without this parsing, no event-driven reconstruction is possible.

---

# **3. Variant Exon-Chain Reconstruction Layer**

For each transcript implicated in an event, the script generates **modified exon chains** describing the splicing outcome.

### **What it does**

Implements biological definitions:

* **SE:** remove middle exon → “skipped” isoform
* **A3/A5:** adjust either splice acceptor or donor boundary → “long” vs “short” isoforms
* **MXE:** replace exon group A with group B
* **RI:** extend exon chain to include an intron

Each variant exon chain is a list of genomic intervals that fully reflects the structure of an alternative transcript.

### **Why it is included**

This is the **core biological transformation**.
Proteogenomic variant sequences only differ if the exon structure changes.
Thus, the script must explicitly build exon chains representing each possible splice outcome exactly as they occur in RNA.

This ensures:

* realistic ORF changes
* correct junction sequences
* correct amino-acid differences
* no artificial models or mis-spliced constructs

---

# **4. CDS Intersection, Frame Computation, and ORF Construction**

### **What it does**

* Intersects variant exon chains with annotated CDS regions.
* Determines which parts of the variant chain are actually coding.
* Computes how many CDS nucleotides precede the first altered region.
* Calculates codon frame at every variant boundary.
* Trims/pads nucleotides to maintain codon alignment.

### **Why it is included**

This layer guarantees biological correctness of the coding sequence:

* **Frame preservation** is mandatory: any frame shift misrepresents the biological protein.
* Trimming/padding ensures translation begins on an actual codon boundary.
* Determining exactly which variant regions intersect the CDS prevents generating proteins from noncoding events.
* Many events—especially A3/A5 and SE—cause partial-codon disruptions; the script resolves this explicitly.

In proteogenomics, small frame errors propagate into incorrect peptides that invalidate mass-spec identification. This layer prevents that outcome.

---

# **5. Sequence Extraction and Translation Layer**

### **What it does**

* Extracts NT sequence for the variant exons from the indexed FASTA.
* Applies strand correction (reverse complement if needed).
* Performs ORF calling using several modes:

  * canonical annotated start
  * first ATG
  * longest ORF

### **Why it is included**

Proteogenomics needs protein sequences, not just RNA structures.
However, alternative splicing can:

* remove the annotated start codon
* introduce upstream ATGs
* create novel ORFs
* shift N-terminal structure

Multiple translation strategies accommodate these biological cases and preserve detection of:

* noncanonical peptides
* N-terminally truncated proteins
* alternative translation initiation sites

Extracting sequence directly from FASTA ensures the protein database aligns exactly with the genome version used in RNA/protein pipelines.

---

# **6. Junction-Peptide Generation Layer (Optional)**

### **What it does**

Constructs codon-aligned AA windows around the splice junctions and outputs them as short peptides.

### **Why it is included**

In proteomics, **junction peptides** are the most distinctive evidence for splice variants.
By generating them directly and in-frame, the script supports:

* targeted MS search
* validation of variant exon usage
* detection of novel isoforms even when full-length proteins are difficult to detect

This dramatically increases sensitivity to splicing-driven proteomic diversity.

---

# **7. Event-Processing Loop and FASTA Output**

### **What it does**

For every event and every transcript:

1. Parse event
2. Get transcript model
3. Build variant exon chains
4. Intersect with CDS
5. Extract sequence
6. Translate to protein
7. Generate optional junction peptides
8. Add sequences to FASTA output with rich metadata

### **Why it is included**

This is the orchestration layer. It ensures the entire workflow is applied consistently across many event types and transcripts, yielding reproducible, annotation-aware proteogenomic outputs.

---






# SUPPA

# **Brief Overview of Steps**

This script implements a full alternative-splicing-aware proteogenomic reconstruction workflow:

1. Parse SUPPA events and transcript models.
2. Construct variant exon structures per transcript.
3. Identify CDS-overlapping segments and correct frames.
4. Extract genomic sequence.
5. Translate variant CDS into protein sequences.
6. Optionally produce codon-aware junction peptides.
7. Prepare FASTA outputs for proteomics.



## **1. Inputs and Outputs**

1. **Reference genome FASTA**
   Parsed with *pyfaidx* for efficient interval-based sequence extraction.

2. **Reference annotation GTF (optional)**
   Parsed via a **prebuilt gffutils database**.
   Allows extraction of transcripts, exons, CDS features, strand, and genomic coordinates.
   If not provided, the script can build one from a GTF file (will take longer).

3. **Optional prebuilt gffutils DB path**
   To skip rebuilding the database from GTF on each run.

4. **Event files**
   `events.ioe` file (SE, A3SS, A5SS, MXE, RI).
   Columns include:
   * `event_id` (SUPPA encoded string containing event type, chrom, genomic coordinates, strand)
   * `alternative_transcripts`
   * `total_transcripts`

5. **Optional arguments**

   * Translation method: `first_atg` (default) or `longest_orf`.
   * Padding of partial codons with `N` before translation.
   * Output paths for FASTA files.

5. **Output**

   * `prot_info`: stores full-length protein sequences derived from variant CDS with an annotated header.
   * `junction_recs`: optional list of junction peptides (for MS search).

Modules:

1. **Interval utilities**
2. **FASTA extraction**
3. **Transcript-model building**
4. **SUPPA event parsing**
5. **Variant exon-chain reconstruction**
6. **CDS intersection and frame computation**
7. **Sequence trimming, padding, translation**
8. **Junction peptide generation**
9. **Event file processing loop**



# 3. LOGIC AND FUNCTIONAL FLOW

## 3.1 Interval Helper Utilities

### `overlaps(a_start, a_end, b_start, b_end)`

Boolean intersection check.
Simple boolean test for interval overlap.

### `subtract_interval_list(intervals, rem_start, rem_end)`

Removes a sub-interval from a list of intervals and returns the remaining parts.
Given exon intervals and a region to remove:

* If an exon lies fully outside, keep it.
* If an exon overlaps the removal region, trim the overlapping part(s).
  Used for building skipped exons (e.g., SE-skipped).

### `replace_interval_in_list(intervals, target_start, target_end, replacement_intervals)`

Removes a target interval from a set of exon intervals and inserts new intervals (used for A3/A5/MXE/RI event modeling).
Replaces a genomic interval with a new interval sequence.
Used for **alternative 3' or 5' splice site events** where a region is replaced with a shorter or longer exon end.

### `merge_intervals`, `intersect_interval_lists`

Classical sorted merge operations to ensure consistent interval representation.
Collapses overlapping or directly adjacent intervals into non-redundant merged intervals.
Computes the overlap between two sets of intervals.

### Purpose:

This block provides the mathematical backbone for constructing modified exon chains.

**Biological validity:**
All interval logic accurately reflects the way exons (intervals) are manipulated in alternative splicing events.

### **Why this matters for proteogenomics:**

Proteogenomics requires exact reconstruction of **exon combinations** to derive variant coding sequences absent from canonical databases. Alternative splicing events fundamentally operate on *intervals of genomic coordinates*, so this precise manipulation is essential.

### **Why the logic works:**

* **Interval subtraction** correctly removes exons for SE (skipping), RI (retention), and spliced isoforms.
* **Interval replacement** correctly swaps long/short exons for A3/A5 and MXE events.
* **Interval merging** produces clean, non-overlapping exon chains—critical for creating realistic isoforms.
* **Intersection with reference/alternative transcript sets** allows event-centric rather than transcript-centric modeling.

This mirrors how SUPPA, rMATS, MAJIQ, or LeafCutter define event coordinates: everything is determined by genomic interval arithmetic.
The logic ensures **every variant is exactly represented in coordinate space**, preventing frame errors and artificial sequences.
---

## 3.2 FASTA handling

### `open_genome_index`

Loads pyfaidx index.
Access indexed genome FASTA sequences and extract nucleotide sequences for lists of genomic segments.

### `extract_sequence_from_indexed_genome(fa_index, chrom, segments, strand)`

Extracts concatenated genomic sequence from multiple intervals:

* Accepts 1-based inclusive coordinates.
* Handles `chr` vs. versionless chromosome naming.
* Extracts multiple segments and concatenates them.
* Reverse complements if transcript is on the negative strand.

**Biological validity:**
This correctly models transcript splicing: exons are fetched and concatenated, orientation-corrected. These functions ensure reliable access to the underlying sequence.

### **Why this matters:**

Proteogenomics databases must match the exact genome used in proteomic mapping. Using the reference FASTA via pyfaidx ensures:

* All novel peptides derive from real genomic sequence
* Strand is handled correctly
* Coordinates are respected 1-to-1
* No reliance on annotation mistakes

This prevents codon corruption and ensures peptides map unambiguously to the genome.

---

## 3.3 Transcript-model construction

### `build_transcript_models(gtf_path, prebuilt_db)`

Reads GTF via gffutils to construct a dict:

```
transcripts[transcript_id] = {
    "transcript_id",
    "gene_id",
    "gene_name",
    "chrom",
    "strand",
    "exons": [(start,end)],
    "cds": [(start,end,frame)]
}
```

   Map transcript identifiers and construct transcript annotation models from a gffutils database.

It also:

* Adds versionless aliases (`ENST00000312345` → alias for `ENST00000312345.2`)
* Maintains exon/CDS genomic ordering.

   Resolves transcript IDs with and without version numbers.
   Reads exon and CDS features, captures gene metadata, produces a dictionary of transcript models, and creates versionless aliases.

Input event files refer to transcripts using potentially inconsistent transcript naming conventions. Using a robust transcript parser ensures reliable mapping of event-associated transcripts to genomic models.

**Biological validity:**
This is the correct representation of spliced gene models and CDS frames required for correct translation.

### **Why this matters:**

Proteogenomics must preserve:

* biological exon order
* annotated CDS boundaries
* correct frame
* strand orientation
* gene and transcript identity

Using **gffutils** gives:

✔ correct exon order
✔ exact CDS start/end
✔ frames from GTF (for codon phasing)
✔ extra transcript aliases (versioned & unversioned ENST handling)

This allows correct reconstruction of CDS segments for variant isoforms.

---

## 3.4 SUPPA event parsing

### `parse_suppa_event_coords(event_id)`

Extracts:

* event type (`SE`, `A3`, `A5`, `MXE`, `RI`)
* chromosome
* genomic ranges involved
* strand
   
   Interpret SUPPA2 event identifiers and aux fields.

### `parse_range`

Parses `"start-end"`, validates numeric values, ensures start ≤ end.
Corrects 0-based values.

* Splits comma-separated transcript lists.
* Extracts event type, chromosome, coordinates, and strand from SUPPA event strings.
* Converts "start-end" text ranges to integer tuples.

SUPPA encodes alternative splicing events in compact identifiers. To reconstruct variant exon chains, the script must interpret these identifiers into usable genomic intervals.

---

## 3.5 Variant exon-chain reconstruction

### `build_variant_chains_for_transcript(event_type, row, tx_exons, ...)`

Generate modified exon chains that correspond to each alternative splicing outcome.
Implements **splicing logic** for each event type:

#### SE (Skipping exon)

`included` = original chain
`skipped` = original minus skipped exon (subtract_interval_list)

#### A3/A5 (Alternative splice site)

Constructs:

* `long` isoform
* `short` isoform
  by replacing subregions of exons

#### MXE (Mutually exclusive exons)

Two alternative single-exon replacements.

#### RI (Retained intron)

Produces:

* `retained` (insert intron sequence)
* `spliced` (normal removal)

If no SUPPA coordinates available:

* Uses merged intervals from `alt_txs` vs `ref_txs` intersection.

**Biological validity:**
These transformations replicate canonical definitions of splicing events.

This function encodes the real biological definitions of:

* **SE (skipped exon):** remove an entire exon interval
* **A3/A5 (alternative splice site):** replace sections of exons with shorter/longer boundaries
* **MXE (mutually exclusive exons):** alternative inclusion of two exons
* **RI (intron retention):** extend exon chain into intronic region

### **Why this works:**

These definitions directly correspond to transcriptome-level alternative splicing events and generate exon chains consistent with observed RNA splicing outcomes.

This logic produces transcripts **a proteogenomics pipeline expects**: structures that may be translated into novel coding sequences producing variant peptides.
---

## 3.6 Intersect alternative exon chain with CDS

### `intersect_chain_with_cds(exon_chain, cds_list)`

Map variant exon chains to CDS regions, determine codon frame and offsets.
Identifies the coding part of each variant exon chain.
Returns list of `(start, end, frame)` intervals.

* Identify which parts of the variant exon structure fall inside annotated CDS.
* Compute how many nucleotides occur between CDS start and a variant region.
* Determine the frame at a given genomic position.
  
**Biological point:**
Variant effects only matter if modifying CDS.
If no CDS overlap → noncoding event → no protein generated.
Variant exon structures may shift reading frames. Determining where an event intersects coding regions is essential for correct translation and frame adjustment.

### **Why this matters:**

The single most important detail in proteogenomics is:

**Do the reconstructed sequences preserve reading frame?**

This script:

* Intersects variant exon chains with CDS intervals → yields variant CDS blocks only
* Computes position relative to CDS start → necessary for frame correction
* Computes upstream nucleotide offset → determines reading frame
* Realigns variants so that translation begins in the correct codon phase

This guarantees:

✔ no frame drift
✔ no artificial stop codons
✔ correct peptide interpretation
✔ correct variant ORF reconstruction
---

## 3.7 Frame logic and coordinate mapping

### `compute_upstream_cds_nt`

Computes, in transcript order, how many CDS nucleotides occur before the first altered junction.

### `first_overlap_in_cds_order`

Gets the genomic coordinate of the first CDS position in transcript order.

### `compute_frame_at_genomic_pos`

Computes codon frame modulo 3 based on transcript-order traversal.

This ensures **codon-phase correctness** when trimming variant sequences.

---

## 3.8 Sequence processing and translation

Before translation:

* The script extracts nucleotide sequence from the variant exons.
* It trims front bases so variant sequence stays in frame:

  ```
  trim = upstream_nt % 3
  seq_nt_trim = seq_nt[trim:]
  ```
* It pads incomplete codons with N if requested.

Normalize nucleotide sequences before translation.
* Remove trailing nucleotides that break codon boundaries.
* Optionally pad with “N” to complete partial codons.

Correct handling of frame ensures:

* No partial codons produce translation artefacts
* Sequences begin at true codon boundaries
* Stop codons do not propagate incorrectly

This is essential for generating biologically meaningful variant proteins.


Translation modes:

1. **Prefer annotated start**
   If enabled, attempts translation from canonical CDS first start codon offset.

2. **Mode: first_atg**
   Uses first ATG if present, else longest ORF.

3. **Mode: longest_orf**
   Finds ORF with maximal AA length by scanning all frames.

* Identify ORFs and select canonical, first-ATG, or longest-ORF translation depending on parameters.
* Handle sequences that do not begin with canonical start codons.

Why this is valid:

* **Canonical ATG preference** is standard in proteogenomics
* **Longest ORF** accommodates genuinely novel ORFs or disrupted CDS
* **Position-based translation** allows rescuing annotated ORFs upstream/downstream of events

This flexibility is required for capturing noncanonical peptides often detected in MS.


**Biological validity:**
Provides a balance between canonical translation and discovery of novel ORFs from altered splicing.
Translation requires codon-aligned sequences. Partial codons at event boundaries must be corrected to maintain biological interpretability.
Alternative splicing can shift or eliminate annotated start codons, leading to N-terminal variants. Flexible translation modes ensure accurate representation of biologically plausible peptides.

---

## 3.9 Junction peptide generation

### `generate_codon_aware_junction_peptides`

Produce short peptides spanning splice junctions for mass-spectrometry database search:

* Constructs transcript-relative coordinate maps.
* Determines junction positions.
* Extracts flanking windows centered on junctions.
* Ensures codon alignment and performs translation.
* Returns junction peptides as SeqRecord entries.

**Biological validity:**
Correct for proteogenomics.
Junctions are extracted precisely in-frame; windows enforced with min/max flanking region.
Junction peptides are among the most distinctive proteomic signatures of alternative splicing. This module ensures accurate codon-aligned windows suitable for MS proteogenomic workflows.

This is a crucial component: proteogenomics depends heavily on **junction peptides**, which uniquely identify splicing variants.

This logic ensures:

* Junctions are mapped through transcript-relative NT coordinates
* Extraction windows maintain codon alignment
* Peptides include defined flanks on both sides (MS-detectable length)
* Stop codons are handled
* Only valid ORFs survive
* FASTA headers fully encode genomic provenance

---

## 3.10 Event-file main loop

### `process_event_file`

For each row in a SUPPA event:

1. Parse event ID
2. Identify alternative vs reference transcripts
3. Build merged alternative vs reference intervals
4. For each transcript affected:

   * Resolve transcript ID
   * Retrieve exon chain with CDS
   * Build variant chains
   * Intersect chains with CDS
  * Adjusts frame and trims/pads.
   * Compute trimming offset
   * Extract sequence
   * Translate into protein using chosen mode (`prot_info`)
   * Optionally generate junction peptides (`junction_recs`)

Expected at end:

* Novel protein variants (FASTA)
* Optional peptide junction FASTA

---


---

# 5. BIOLOGICAL VALIDITY SUMMARY

The script is biologically coherent and implements a correct pipeline for splicing-aware proteogenomic sequence reconstruction:

1. **Uses real exon structures from GTF**
2. **Handles strand orientation properly**
3. **Implements exact SUPPA coordinate logic**
4. **Reconstructs biologically meaningful variant exon chains**
5. **Ensures CDS-only sequence extraction**
6. **Maintains codon frame**
7. **Provides flexible, biologically relevant translation strategies**
8. **Generates codon-aware peptides suitable for MS identification**
9. **Avoids producing sequences for events that do not affect CDS**
10. **Chrom name normalization ensures compatibility with most GRCh/GENCODE files**

# **Summary – Why the script is biologically and proteogenomically valid**

✔ Uses true genomic coordinates
✔ Reconstructs exon chains consistent with real biology
✔ Uses authoritative GTF-derived CDS & frame
✔ Ensures codon-phase correctness
✔ Accurately extracts and translates variant ORFs
✔ Generates biologically meaningful peptides
✔ Produces FASTA entries compatible with MS engines
✔ Covers all major splicing event types
✔ Implements established proteogenomics logic used in published pipelines










# 4. EXPECTED OUTPUT

### 4.1 Variant protein FASTA sequences

Each unique AA sequence associated with metadata:

* gene_id
* gene_symbol
* transcript_id
* event type
* variant label (e.g., “included”, “skipped”, “long”, “short”, “exon1”, “exon2”)
* CDS coordinates used
* translation mode, trimming, padding metadata

### 4.2 Junction peptides (optional)

List of SeqRecords with headers containing:

* protein ID
* variant name
* gene info
* event type
* junction locations
* flanking AA statistics