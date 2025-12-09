# Alternative Splicing — Protein Database Generation
  
Last modified: 18/11/2025 by K. Coetzer
  
**Objective:** Translate rMATS/SUPPA alternative-splicing events from nf-core/rnasplice into biologically valid protein isoforms and codon‑aware junction peptides for peptide identification and protein inference.
  
<img src="image-7.png" alt="Gene Structure">
  
<img src="image-9.png" alt="Alternative Splicing to Protein">
  
## Table of contents
  
- [Alternative Splicing — Protein Database Generation](#alternative-splicing--protein-database-generation)
  - [Table of contents](#table-of-contents)
  - [Definitions](#definitions)
  - [Alternative Splicing Theory Overview](#alternative-splicing-theory-overview)
  - [Different Types of Alternative Splicing (AS) Event (variants)](#different-types-of-alternative-splicing-as-event-variants)
  - [Inclusion vs Exclusion](#inclusion-vs-exclusion)
  - [Identifying AS events from nf-core/rnasplice](#identifying-as-events-from-nf-corernasplice)
    - [SUPPA outputs](#suppa-outputs)
    - [rMATS outputs](#rmats-outputs)
  - [Script: rMATS/SUPPA to protein](#script-rmatssuppa-to-protein)
  - [Inputs and Outputs](#inputs-and-outputs)
    - [1. Interval and Exon-Chain Manipulation Utilities](#1-interval-and-exon-chain-manipulation-utilities)
    - [**`overlaps(a_start, a_end, b_start, b_end)`**](#overlapsa_start-a_end-b_start-b_end)
    - [**`subtract_interval_list(intervals, rem_start, rem_end)`**](#subtract_interval_listintervals-rem_start-rem_end)
    - [**`replace_interval_in_list(intervals, target_start, target_end, replacement_intervals)`**](#replace_interval_in_listintervals-target_start-target_end-replacement_intervals)
    - [**`merge_intervals(intervals)`**](#merge_intervalsintervals)
    - [2. Genome FASTA Handling](#2-genome-fasta-handling)
    - [`open_genome_index` and `extract_sequence_from_indexed_genome`](#open_genome_index-and-extract_sequence_from_indexed_genome)
    - [3. Transcript Parsing and Resolution](#3-transcript-parsing-and-resolution)
    - [`parse_suppa_event_coords(event_id)` - **SUPPA ONLY**](#parse_suppa_event_coordsevent_id---suppa-only)
    - [`parse_range`](#parse_range)
    - [**`match_transcript_id`**](#match_transcript_id)
    - [**`build_transcript_models`**](#build_transcript_models)
    - [**`canonicalize_gene_field`** - **rMATS ONLY**](#canonicalize_gene_field---rmats-only)
    - [**`build_transcripts_lookup`** - **rMATS ONLY**](#build_transcripts_lookup---rmats-only)
    - [4. Variant Exon Chain Construction](#4-variant-exon-chain-construction)
      - [SE (Skipped Exon) - skipped exon removed](#se-skipped-exon---skipped-exon-removed)
      - [A3SS/A5SS (Alternative 3' or 5' splice site) - long vs. short exon variants](#a3ssa5ss-alternative-3-or-5-splice-site---long-vs-short-exon-variants)
      - [MXE (Mutually exclusive exons) - alternative single exon replacement](#mxe-mutually-exclusive-exons---alternative-single-exon-replacement)
      - [RI (Retained Intron) - intron retained or spliced](#ri-retained-intron---intron-retained-or-spliced)
    - [5. CDS Intersection and Frame Calculation](#5-cds-intersection-and-frame-calculation)
    - [**`intersect_chain_with_cds`**](#intersect_chain_with_cds)
    - [**`first_overlap_in_cds_order`**](#first_overlap_in_cds_order)
    - [**`compute_upstream_cds_nt`**](#compute_upstream_cds_nt)
    - [**`compute_frame_at_genomic_pos`**](#compute_frame_at_genomic_pos)
    - [6. Codon-Aware Translation](#6-codon-aware-translation)
    - [7. Codon-Aware Short Junction Peptides](#7-codon-aware-short-junction-peptides)
    - [**`generate_codon_aware_junction_peptides`**](#generate_codon_aware_junction_peptides)
    - [8. Event Processing](#8-event-processing)
    - [`process_event_file`](#process_event_file)
    - [Limitations in Current Approach](#limitations-in-current-approach)
    - [Special Considerations](#special-considerations)
    - [Future Improvements](#future-improvements)
      - [1. Filtering Options prior to building the database](#1-filtering-options-prior-to-building-the-database)
      - [2. Reannotate fasta files with UniProt IDs and gene symbols](#2-reannotate-fasta-files-with-uniprot-ids-and-gene-symbols)
      - [3. Frame classification](#3-frame-classification)
      - [4. Visualizations to add](#4-visualizations-to-add)
    - [Final Step before nf-core/quantms](#final-step-before-nf-corequantms)
    - [Sources](#sources)
  
## Definitions
  
Definitions adapted from Zhu et al., 2025 (moPepGen):
  
- **Canonical database:** Reference protein sequences derived from well-annotated protein-coding transcripts (no variants or modifications).
- **Non-canonical peptides:** Peptides absent from the canonical database. Sources include genomic variants (SNPs, SNVs, indels), transcriptomic events (alternative splicing, fusions, RNA editing, circRNAs), translation-level changes (e.g., selenocysteine), and peptides from novel ORFs in nominally noncoding transcripts.
- **Variant peptides:** Subset of non-canonical peptides that contain genomic and/or transcriptomic variants in protein-coding transcripts.
- **Non-canonical database:** FASTA of sequences derived from variants and novel/transcriptomic events, produced so it does not overlap the canonical database.
- **Proteoform:** A distinct molecular form of a protein with a unique amino-acid sequence arising from genetic, transcriptional, translational, or post-translational processes.
  
Reference: Zhu C., Liu L.Y., Ha A. et al., Identification of non-canonical peptides with moPepGen. Nat Biotechnol (2025). [https://doi.org/10.1038/s41587-025-02701-0](https://doi.org/10.1038/s41587-025-02701-0 )
  
## Alternative Splicing Theory Overview
  
## Different Types of Alternative Splicing (AS) Event (variants)
  
<img src="image-3.png" alt="Splice Event Types">
  
1. Alternative 3' Splice Site (A3SS)
2. Alternative 5' Splice Site (A5SS)
3. Retained Intron (RI)
4. Skipped Exon (SE)
5. Mutually Exclusive Exons (MXE)
6. Alternative Last Exon (ALE) -> detected by SUPPA only
  
## Inclusion vs Exclusion
  
<img src="image-4.png" alt="Inclusion and Exclusion">
  
**Inclusion Alternative Splicing**
The alternative exon and its flanking introns are all incorporated into the initial transcript, and the exon's coding sequence is retained in the final mature mRNA product. The spliceosome recognizes the splice sites flanking the exon, leading to its inclusion.
Outcome -> This results in a protein isoform that contains the amino acid sequence encoded by the included exon.
  
**Exclusion Alternative Splicing**
The alternative exon (also referred to as a cassette exon) is skipped, meaning the spliceosome joins the upstream and downstream flanking exons, effectively removing the internal exon along with the introns.
Outcome -> This results in a protein isoform that lacks the amino acid sequence encoded by the skipped exon.
  
## Identifying AS events from nf-core/rnasplice
  
### SUPPA outputs
  
**"SUper fast Processing of alternative splicing events"** (SUPPA) ([https://github.com/comprna/SUPPA](https://github.com/comprna/SUPPA )) is a popular **alternative splicing analysis tool** used to **quantify, compare, and visualize splicing events** across samples using transcript-level abundance estimates.
  
- It takes **transcript annotations** (e.g., from a GTF file) and **transcript expression values** (from quantifiers like Salmon or Kallisto) to:
  
  1. Identify and define **alternative splicing (AS) events**
  2. **Quantify** them using **Percent Spliced In (PSI, Ψ)**
  3. **Compare** splicing between conditions using **ΔPSI (dPSI)** and **statistical significance**
  
<img src="image-11.png" alt="SUPPA Overview">
  
1. star_salmon/suppa/generate_events/per_local_event/`events.ioe`
  
    * This file is a combination of all events_*_strict.ioe (Input Overlap Event) files generated by SUPPA
    * It defines the coordinates and transcript models for each event (e.g., SE, A5, A3, MXE, RI).
    * There are files that give per-sample PSI values and differential splicing results between conditions which could be used to filter events of interest.
    * Describes the structure of every AS event, including which transcripts and exons are included or skipped. 
    * It forms the blueprint for reconstructing novel isoform sequences and predicting variant protein products.
    * This is a **cohort-level** file containing all detected alternative splicing events across all samples.
  
   ```bash
   seqname gene_id event_id alternative_transcripts total_transcripts
   chr1 ENSG00000228794.12 ENSG00000228794.12;A3:chr1:847806-849484:847806-850178:+ ENST00000610067.7 ENST00000610067.7,ENST00000688008.2
   chr1 ENSG00000228794.12 ENSG00000228794.12;A3:chr1:847806-849484:847806-850181:+ ENST00000610067.7 ENST00000610067.7,ENST00000448975.6
   chr1 ENSG00000228794.12 ENSG00000228794.12;A3:chr1:847806-850178:847806-850181:+ ENST00000688008.2 ENST00000448975.6,ENST00000688008.2
   ```
  
1. star_salmon/suppa/diffsplice/per_local_event/`CASE-CTRL_local_diffsplice.dpsi`
  
    * Differential splicing results file showing ΔPSI (ΔΨ) values — the difference in Percent Spliced In between two conditions.
    * It includes the local dPSI values and p-values for each event.
    * Quantifies how much each AS event changes between conditions (e.g., control vs. disease).
    * Helps identify splicing events that may alter coding potential or protein isoforms relevant to disease mechanisms.
    * **Cohort-level** differential splicing results between specified conditions.
  
    ```bash
    local_CASE-local_CTRL_dPSI local_CASE-local_CTRL_p-val
    ENSG00000000003.16;A5:chrX:100635746-100636191:100635746-100636608:- nan 1.0
    ENSG00000000003.16;A5:chrX:100635746-100636608:100635746-100636793:- nan 1.0
    ```
  
2. star_salmon/suppa/psi_per_local_event/`suppa_local.psi`
  
    * This file contains Percent Spliced In (PSI) values for each local event across all samples.
    * Each column corresponds to a sample, and each row corresponds to an event.
    * Indicates how strongly an exon or splice variant is expressed in each sample, revealing isoform usage patterns that may correspond to protein-level differences.
    * Can be used for filtering events based on inclusion levels in specific samples or conditions.
    * **Participant-specific** events
  
    ```bash
    CASE_NEUAE993EPR_6287_T CASE_NEUAK321NN1_9362_T CASE_NEUAW717TN6_6315_T CASE_NEUBA169GXD_6024_T CASE_NEUBN979ZZ5_7603_T CASE_NEUCC219HJC_7743_T CASE_NEUCP218XVV_7631_T CASE_NEUCU076ADN_7708_T CASE_NEUCV578DFJ_7547_T CASE_NEUDE902GCT_5719_T CASE_NEUDH063DEA_6825_T CASE_NEUDM949BAR_6734_T CASE_NEUEE624VCY_8639_T CASE_NEUEL515MZ3_7375_T CASE_NEUET956RE3_7876_T CASE_NEUGD965XVD_5975_T CASE_NEUGP781PDU_5740_T CASE_NEUGU254CLF_8093_T CASE_NEUGW340YEB_6473_T CASE_NEUHB491NGF_6185_T CASE_NEUHL814WMU_7806_T CASE_NEUHR975AFM_7347_T CASE_NEUHW530WD8_6515_T CASE_NEUHY206ZEQ_6955_T CASE_NEUJH436DPG_6624_T CASE_NEUJT708HZL_8387_T CASE_NEUJX780XXK_6094_T CASE_NEUJY536DKF_6466_T CASE_NEUKA429GAC_8289_T CASE_NEULM691PBK_7102_T CASE_NEULP953KE7_8177_T CASE_NEUMT422NBX_7869_T CASE_NEUNJ938DUL_7445_T CASE_NEUNR118PKF_8674_T CASE_NEUPM937TMY_7130_T CASE_NEUPR357AUF_6543_T CASE_NEURJ448YCV_7207_T CASE_NEURT008RBN_8576_T CASE_NEUUF177PR6_7792_T CASE_NEUVR711TBR_8009_T CASE_NEUWJ389FC7_6406_T CASE_NEUWL486NRA_7242_T CASE_NEUXG265ME9_6635_T CASE_NEUXW790VZK_8653_T CASE_NEUYC303AJY_6997_T CASE_NEUYD306HAB_7848_T CASE_NEUYZ462TBW_9523_T CASE_NEUZT902WVB_6660_T CASE_NEUZW291KJY_9453_T CTRL_NEUAA485DZL_7575_T CTRL_NEUCA748GF2_6003_T CTRL_NEUDM126GNG_5691_T CTRL_NEUEU392AE8_10505_T CTRL_NEUEU392AE8_11121_T CTRL_NEUEU392AE8_5190_T CTRL_NEUEU392AE8_5206_T CTRL_NEUEU392AE8_8436_T CTRL_NEUEU392AE8_8702_T CTRL_NEUEU392AE8_9193_T CTRL_NEUEU392AE8_9796_T CTRL_NEUHE723FGT_5933_T CTRL_NEUNC876ZB2_7498_T CTRL_NEUPW536ZKZ_6983_T CTRL_NEURV546WMW_7158_T CTRL_NEUXP955XW7_7431_T CTRL_NEUZR532AA4_8345_T
    ENSG00000000003.16;A5:chrX:100635746-100636191:100635746-100636608:- 1.0 0.0 nan 0.0 nan 0.0 1.0 1.0 nan 1.0 nan 1.0 0.0 nan nan 1.0 nan 0.0 0.0 1.0 nan 1.0 nan 1.0 0.0 0.0 nan nan 0.0 nan 0.0 nan 0.0 nan nan 0.0 nan nan nan 1.0 0.0 1.0 nan 0.0 0.6813295556006821 0.0 0.0 0.0 1.0 nan 0.811872287389845 nan nan nan 1.0 nan nan 0.0 1.0 nan nan 0.0 0.0 nan nan nan
    ```
  
---
  
### rMATS outputs
  
rMATS ([rmats-turbo v4.1.0](https://github.com/Xinglab/rmats-turbo/tree/v4.1.0 )) is a widely used **statistical tool for detecting differential alternative splicing** between two conditions using RNA-Seq data, with or without replicates.
  
rMATS aligns RNA-Seq reads to a reference genome and counts reads that support either exon inclusion or skipping. It models variability across replicates and calculates the significance of splicing differences between groups.
  
<img src="image-10.png" alt="rMATS Output">
  
1. `fromGTF.[AS_Event].txt` — **Essential**
  
   - Contains the mapping between the AS event and annotated transcript/exon coordinates from the GTF.
   - Can be used to reconstruct full exon models (which exon(s) to include or skip) from known transcripts.
  
2. `fromGTF.novelJunction.[AS_Event].txt` — **Very important for novel isoforms built from novel exon–exon combinations.**
  
   - Captures events that join annotated splice sites in novel combinations (i.e., novel exon–exon joins).
   - Important for novel junction-derived proteins that reuse known splice sites but in new order/combinations.
  
3. `fromGTF.novelSpliceSite.[AS_Event].txt`
  
   - Contains events with unannotated splice sites.
   - These can generate novel coding sequence (CDS) changes or frameshifts.
  
4. `[AS_Event].MATS.JC.txt` and `[AS_Event].MATS.JCEC.txt` — Very useful for prioritization and quantification
  
   - These are the final event lists with inclusion/exclusion counts and statistical measures (PSI/ΔPSI, p-value, FDR).
   - JCEC (junction + exon body) for more conservative, higher-sensitivity quantification -> detection of events
   - JC for junction-only support (stricter evidence for a splice junction) -> junction-confirmed events
  
`[AS_Event].MATS.JC*.txt` contain columns:
  
- All: ID, GeneID, geneSymbol, chr, strand, ID, IJC_SAMPLE_1, SJC_SAMPLE_1, IJC_SAMPLE_2, SJC_SAMPLE_2, IncFormLen, SkipFormLen, PValue, FDR, IncLevel1, IncLevel2, IncLevelDifference
  
  - A3/A5: longExonStart_0base, longExonEnd, shortES, shortEE, flankingES, flankingEE
  
  - SE/MXE/RI: 1stExonStart_0base, 1stExonEnd, 2ndExonStart_0base, 2ndExonEnd, upstreamES, upstreamEE, downstreamES, downstreamEE
  
---
  
## Script: rMATS/SUPPA to protein
  
**High-level steps:**
  
1. Load transcript/CDS models from a gffutils DB (or build from a GTF).
2. Build transcript lookup structures (gene_id/gene_symbol → transcripts).
3. For each event, resolve candidate transcripts.
4. Construct variant exon chains representing each splice outcome.
5. Intersect exon chains with CDS annotations to get variant CDS segments and frames.
6. Extract nucleotide sequence from the genome (pyfaidx), handling strand.
7. Trim/pad to codon boundaries and translate using chosen strategy.
8. Optionally generate codon-aware junction peptides centered on exon–exon junctions.
9. Write unique protein FASTA (`--out_prot_fa`) and optional junction FASTA (`--out_junc_fa`).
  
---
  
## Inputs and Outputs
  
1. **Reference genome FASTA (indexed by pyfaidx)** - `--genome`
  
   - Used for efficient interval-based sequence extraction.
  
2. **GTF-derived gffutils DB (optional)** - `--gtf` OR `--gtf_db`
  
   - A prebuilt annotation database.
   - Used to extract transcripts, exon structures, CDS coordinates, frames, strand, and gene metadata.
   - If not provided, the script can build one from a GTF file (will take longer).
  
3. **Event files** - `--se_files, --a3ss_files, --a5ss_files, --mxe_files, --ri_files`
  
    These are the files that have been used to test this script.
  
**3.1. SUPPA:**
  `events.ioe` file
  
**Columns include:**
  
- `event_id` (SUPPA encoded string containing event type, chrom, genomic coordinates, strand)
- `alternative_transcripts`
- `total_transcripts`
  
**3.2. rMATS:**
    `[AS_Event].MATS.JC.txt` - one file per event type (SE, MXE, A3SS, A5SS, RI) -> junction-confirmed events
  
**Columns of interest include:**
  
- Columns are different per event type but generally include:
  - `gene_id`
  - `gene_symbol`
  - `chr`
  - `strand`
  - Event-specific genomic coordinates:
        - A3/A5: longExonStart_0base, longExonEnd, shortES, shortEE, flankingES, flankingEE
        - SE/MXE/RI: 1stExonStart_0base, 1stExonEnd, 2ndExonStart_0base, 2ndExonEnd, upstreamES, upstreamEE, downstreamES, downstreamEE
  
1. **Optional arguments**
  
   - `--prefer_annotated_start` with:
     - `--translation_mode`: `first_atg` (default) or `longest_orf`.
   - Padding of partial codons with `N` before translation - `--pad_partial_codons`
   - `--short_junction_peptides` with:
     - `--junction_max_flank` default=15
     - `--junction_min_flank` default=7
  
2. **Output**
  
   - `--out_prot_fa`: stores full-length protein sequences derived from variant CDS with an annotated header.
   - `--out_junc_fa`: optional list of junction peptides.
  
---
  
### 1. Interval and Exon-Chain Manipulation Utilities
  
> NOTE: Alternative splicing alters the exon structure as determined by a change in genomic intervals.
> Therefore, since alternative splicing is fundamentally an operation on **genomic intervals**, it is important that **every variant is exactly represented in coordinate space** to prevent frame errors and artificial sequences.
  
These functions manipulate exon chains as lists of genomic intervals `(start,end)` to model alternative splicing events.
  
- Currently works for: exon skipping (SE), alternative splice site adjustments (A3SS/A5SS), mutually exclusive exon swapping (MXE), and intron retention (RI).
  
### **`overlaps(a_start, a_end, b_start, b_end)`**
  
- Checks whether two intervals overlap.
- Returns `True` if two genomic intervals overlap.
- Used in CDS/exon intersection for determining which CDS segments overlap variant exon chains.
  
### **`subtract_interval_list(intervals, rem_start, rem_end)`**
  
- Removes a sub-interval `(rem_start, rem_end)` from a list of intervals, potentially splitting intervals.
- Given exon intervals and a region to remove:
  - If an exon lies fully outside, keep it.
  - If an exon overlaps the removal region, trim the overlapping part(s).
- Used to generate exon chains for skipped-exon (SE) or spliced-out sequences (e.g., spliced version of retained intron).
  
### **`replace_interval_in_list(intervals, target_start, target_end, replacement_intervals)`**
  
- Removes a target interval from a set of exon intervals and inserts new intervals (used for A3/A5/MXE/RI event modeling).
- Replaces a specific exon region with a new interval set, while preserving non-overlapping regions.
- Used for:
  
  - A3SS/A5SS (short vs long isoforms)
  - MXE (mutually exclusive exons) where one exon is swapped with an alternative region
  
### **`merge_intervals(intervals)`**
  
- Generic utility for merging contiguous intervals (coalesces overlapping/adjacent intervals).
- Ensures exon chains stay normalized after replacements.
- Collapses overlapping or directly adjacent intervals into non-redundant merged intervals.
- Computes the overlap between two sets of intervals.
- Produces clean, non-overlapping exon chains—critical for creating realistic isoforms.
  
---
  
### 2. Genome FASTA Handling
  
### `open_genome_index` and `extract_sequence_from_indexed_genome`
  
- These functions retrieve nucleotide sequences corresponding to built exon or CDS chains.
- Allows efficient random access to genomic intervals.
- Accepts 1-based inclusive coordinates.
- Handles `chr` vs. versionless chromosome naming.
- Extracts multiple segments and concatenates them.
- Reverse complements if transcript is on the negative strand.
  
---
  
### 3. Transcript Parsing and Resolution
  
### `parse_suppa_event_coords(event_id)` - **SUPPA ONLY**
  
The SUPPA `events.ioe`file is parsed to extract:
  
- event type (`SE`, `A3`, `A5`, `MXE`, `RI`)
- genomic coordinates
- event strand
- transcript sets supporting each isoform
  
### `parse_range`
  
Parses `"start-end"`, validates numeric values, ensures start ≤ end.
Corrects 0-based values.
  
- Splits comma-separated transcript lists.
- Extracts event type, chromosome, coordinates, and strand from SUPPA event strings.
- Converts "start-end" text ranges to integer tuples.
  
SUPPA encodes alternative splicing events in compact identifiers. These identifiers need to be interpreted into usable genomic intervals to reconstruct variant exon chains
  
These functions map rMATS gene/transcript identifiers to transcript models derived from the GTF.
  
### **`match_transcript_id`**
  
- Matches transcript IDs with or without version suffixes, ENSEMBL or non-ENSEMBL.
- Critical when rMATS or GTF use inconsistent naming.
  
### **`build_transcript_models`**
  
- Loads transcript → {exons, CDS segments, strand, gene info} models from a gffutils DB (ideally prebuilt).
- Uses **gffutils** and stores per-transcript:
  
  - gene_id
  - gene_name
  - chrom
  - strand
  - ordered exon coordinates
  - Exact CDS coordinates
  - Frames from GTF (for codon phasing)
  
This allows correct reconstruction of CDS segments for variant isoforms.
  
### **`canonicalize_gene_field`** - **rMATS ONLY**
  
- Normalizes raw gene IDs (e.g. ENSG000…, removes versions).
- Handles gene symbols as fallback.
- rMATS may output gene identifiers inconsistently. Needed for matching genes to transcripts.
  
### **`build_transcripts_lookup`** - **rMATS ONLY**
  
Alternative splicing events (e.g. from rMATS) reference transcript IDs and gene IDs that may not map 1:1 to GTF annotations (versioned vs unversioned IDs, symbol ambiguities). Accurate mapping of events to real transcript models is required.
  
rMATS provides gene_id and gene_symbol per event, but not explicit transcript lists. Therefore, to construct variant chains, it is necessary to resolve transcripts based on gene identifiers. This is done by:
  
- Building a dictionary (lookup): **gene_id/gene_symbol → list of transcript IDs** for fast searching
- Supports uppercase, lowercase, and version-stripped (original) IDs.
  
This reduces false negatives and ensures each event is tied to a structurally accurate transcript model.
  
> NOTE: This step is not done for SUPPA since SUPPA provides explicit transcript lists per event.
  
---
  
### 4. Variant Exon Chain Construction
  
This module transforms canonical transcript exon lists into event-specific exon chains for each rMATS event type. It rewrites exon structures around alternative junctions exactly as each event type dictates, reflecting real biological splicing outcomes.
  
- `build_variant_chains_for_transcript` reconstructs modified exon chains that correspond to each alternative splicing outcome.
  
Implements biological definitions:
  
- **SE:** remove middle exon → “skipped” isoform
- **A3/A5:** adjust either splice acceptor or donor boundary → “long” vs “short” isoforms
- **MXE:** replace exon group A with group B
- **RI:** extend exon chain to include an intron
  
Each variant exon chain is a list of genomic intervals that fully reflects the structure of an alternative transcript.
  
Implements **splicing logic** for each event type:
  
#### SE (Skipped Exon) - skipped exon removed
  
- `included` = full exon chain
- `skipped` = exon chain with SE region removed
  
#### A3SS/A5SS (Alternative 3' or 5' splice site) - long vs. short exon variants
  
- `long` = chain where longer exon is inserted
- `short` = chain where shorter exon is inserted
- Achieved using `replace_interval_in_list`.
  
#### MXE (Mutually exclusive exons) - alternative single exon replacement
  
- `exon1` and `exon2` variants, each replacing the MXE interval.
  
#### RI (Retained Intron) - intron retained or spliced
  
- `retained` = intron inserted as exon
- `spliced` = intron removed
- Correct upstream/downstream boundaries based on rMATS columns.
  
- rMATS uses transcripts_lookup to create transcript lists
- SUPPA uses merged intervals from `alt_txs` vs `ref_txs` to create transcript lists
- All outputs are sorted lists of `(start,end)`.
  
Thus, the exon chains should accurately represent transcript variants resulting from alternative splicing.
  
---
  
### 5. CDS Intersection and Frame Calculation
  
- Together these functions determine how variant exon chains intersect with annotated CDS regions and compute codon frames accordingly:
- `intersect_chain_with_cds`: identifies coding segments within variant exon chains.
- `first_overlap_in_cds_order`: finds the first genomic position overlapping CDS.
- `compute_upstream_cds_nt`: counts upstream coding nucleotides.
- `compute_frame_at_genomic_pos`: computes codon frame at a genomic position.
  
### **`intersect_chain_with_cds`**
  
- Identify which parts of the variant exon structure fall (intersects) inside annotated CDS.
- Compute how many nucleotides occur between CDS start and a variant region.
- Determine the frame at a given genomic position.
- Identifies the coding part of each variant exon chain into coding segments `(start,end,frame)`.
  
### **`first_overlap_in_cds_order`**
  
- Determines the first genomic coordinate participating in variant CDS (different for ± strands) by:
  - Iterating through variant exon chain in transcript order
  - Finding first overlap with any CDS segment
  - Overlaps the rebuilt exon chain with annotated CDS segments
  - Returning that genomic position
  - Preserves frame information from the GTF
  
This produces biologically valid CDS sequences by computing upstream coding nucleotides and ensuring proper frame alignment.
  
### **`compute_upstream_cds_nt`**
  
Counts how many CDS nucleotides occur before a given genomic coordinate (in transcript order), reporting the upstream nucleotide count and the implied reading-frame offset; strand-aware.
  
- Calculates number of CDS nucleotides before a given genomic coordinate in **transcript order**.
- Calculates reading frame relative to variant (first altered) junction.
- Strand-aware.
  
### **`compute_frame_at_genomic_pos`**
  
- Determines codon frame using GTF CDS phase/offsets plus the upstream nucleotide count to compute the codon frame at a specific genomic position.
  
- This ensures **codon-phase correctness** when trimming or padding variant sequences.
- Frame correctness is crucial since:
  - Misaligned frames would generate invalid protein sequences and lead to unusable search database entries.
  - This ensures translation starts in the correct reading frame even if inferred frame disagrees with GTF annotation.
  
> **NOTE on considering the frame:**
> > Only coding regions contribute to the protein
> > * If no CDS overlap → noncoding event → no protein generated.
> > * Variant exon structures may shift reading frames.
> > * Determining where an event intersects coding regions is essential for correct translation and frame adjustment.
> > * This ensures variant CDS follows biologically valid translated regions.
  
> **ALSO:** Many events—especially A3/A5 and SE—cause **partial**-codon disruptions
> > * Intersection with reference/alternative transcript sets allows event-centric rather than transcript-centric modeling.
> > * Many splicing events affect UTRs or introns; without careful CDS intersection, the script could translate non-coding regions incorrectly.
  
### 6. Codon-Aware Translation
  
Alternative splicing can disrupt canonical ORFs. Flexible translation strategies ensure variant proteins are biologically valid and likely detectable in MS database searches.
  
- Normalize nucleotide sequences before translation. using `trim_to_codon`, `pad_to_codon`:
  
  - Trim/pad sequences to complete codons or pad with N’s.
  - Prevents translation errors and premature truncation.
  - Translate CDS into proteins using flexible strategies (first ATG, longest ORF).
  
Alternative splicing often changes the start codon or shifts ORFs. MS databases must support alternative translations such as:
  
- Using the first in-frame ATG
- Longest ORF downstream
  
These translation functions ensure:
  
- No partial codons produce translation artefacts
- Sequences begin at true codon boundaries
- Non-canonical start codons and novel ORFs are represented
- Truncated or extended proteins are captured
- Stop codons are properly removed
  
Correct handling of frame ensures:
  
- `find_orfs`:
  - Extracts ORFs for scanning translation.
  - Supports alternative translation rules (e.g., longest ORF approach).
  
- Select canonical, first-ATG, or longest-ORF translation mode (`translate_from_first_atg_or_longest_orf`, `translate_from_position`, `translate_longest_orf_only`)
  
  - Different strategies for translating nucleotide sequences into protein sequences.
  - Needed because many alternative isoforms break canonical ORF structure; these utilities provide fallback translation approaches.
  
**Translation modes:**
  
`--prefer_annotated_start`:
  
   If enabled, attempts translation from canonical CDS first start codon offset using `translate_from_position`.
   Does not search for ATG or ORFs.
  
`--translation_mode` using: `translate_from_first_atg_or_longest_orf`:
  
1. **`first_atg`**
   Uses first ATG if present, else longest ORF.
  
2. **`longest_orf`** - uses `translate_longest_orf_only` and `find_orfs`
   Finds ORF with max amino acid length by scanning all frames.
  
* A flexible translation mode is required for capturing noncanonical peptides often detected in MS and therefore ensures accurate representation of biologically plausible peptides.
  
---
  
### 7. Codon-Aware Short Junction Peptides
  
### **`generate_codon_aware_junction_peptides`**
  
Enabled with `--short_junction_peptides` to generate codon-aware short peptides centered on exon–exon junctions.
  
Produce short peptides spanning splice junctions:
  
- Determines nucleotide positions of exon–exon boundaries.
- Extracts variable-length flanking regions around junctions (configure using --junction_max_flank and --junction_min_flank).
- Ensures peptide boundaries fall on codons.
- Retrieves nucleotide sequence via genome FASTA.
- Translates junction peptide while enforcing codon boundaries.
- Returns list of `SeqRecord` entries with metadata-rich FASTA headers.
  
`--junction_max_flank`: Maximum amino acids on each side of the junction to include in the peptide window. Nucleotide window of size max_flank * 3 on each side (so default = 15 AA each side → up to ~30 AA peptide), then maps that window back to genomic segments and translates it.
  
`--junction_min_flank`: Minimum amino acids required on each side of the junction. If the initial window (max_flank) yields fewer than min_flank amino acids per side, the code will try to expand the window (within transcript CDS bounds) to reach at least min_flank per side. Junction is skipped if it can't.
  
Codon-aware extraction ensures:
  
- Junction peptides reflect true sequence across variant boundaries
- Flanking regions have minimum length for detectability
- Frames are correctly maintained across junctions
- Only valid genomic segments are retrieved and translated
- Duplicate peptide sequences are deduplicated when writing --out_junc_fa (one SeqRecord per unique amino-acid sequence).
  
This is essential for identifying variant-specific peptides especially since junction peptides are among the most distinctive proteomic signatures of alternative splicing.
  
> NOTE: Translation stops at the first stop (*) in the windowed peptide; only the portion before the stop is kept.
  
---
  
### 8. Event Processing
  
### `process_event_file`
  
- For SUPPA
  - Parse each `event_id` to extract event type, coordinates, and strand.
  - Identify reference vs alternative regions and build merged alternative/reference intervals suitable for exon-chain edits.
  
- For rMATS
  - Identify gene IDs and resolve candidate transcripts (gene_id/gene_symbol lookup) using the transcript lookup built from the GTF/gffutils DB.
  
- For each candidate transcript:
  - Match the transcript ID (handle versioned/unversioned IDs).
  - Retrieve the canonical exon chain and CDS segments.
  - Build variant exon chains reflecting the event (SE, A3/A5, MXE, RI) using the interval utilities.
  - Intersect the variant exon chains with annotated CDS to identify coding segments and compute frames.
  - Adjust frames by trimming/padding to maintain codon boundaries where possible.
  - Extract the nucleotide sequence from the indexed genome and translate into protein using the chosen translation mode (`first_atg` / `longest_orf`).
  - Optionally generate codon-aware junction peptides for MS searches.
  - Store resulting proteins in `prot_info` (with informative headers) and append junction records to `junction_recs` if requested.
  
---
  
### Limitations in Current Approach
  
- Does not model UTR changes unless included in rMATS coordinates.
- Does not handle complex multi-event interactions across overlapping events.
- ORF inference may diverge from biological translation initiation if non-ATG start sites exist.
- The script does not perform any filtering or validation of splice events; it simply combines the data as-is.
- The script does not handle potential duplicates sequences arising from different transcripts producing identical protein sequences or between the two tools.
- SUPPA script currently does not include AL event types.
- rMATS script has not been tested on all output files. Currently only tested on CASE-CTRL/rmats_post/<event_type>.MATS.JC.txt files.
  
---
  
### Special Considerations
  
- **Frame-aware translation:** If an event is known to alter the reading frame, I must translate accordingly and note if a premature stop codon is introduced.
- **MS detectability:** simulate tryptic digestion and flag unique peptides (≥7 aa) that distinguish the novel isoform from canonical proteins.
- **Redundancy:** multiple AS events can produce identical protein sequences. I need to merge identical sequences while retaining metadata about all contributing events.
- **Transcript selection:** An event may affect many transcripts within the same gene. I should prioritize those most relevant to ALS by looking at expression data or known functional annotations. Alternatively, I can include all affected transcripts but annotate them accordingly (currently done in this script).
- **Participant-specific vs cohort-specific databases:** participant-specific databases are tailored to individual samples, while cohort-specific databases aggregate data across multiple samples, providing a broader context for analysis. SUPPA and rMATS are typically used for cohort-level analyses, so databases built from their outputs are cohort-specific. In contrast, fusion detection tools like FusionCatcher, FusionInspector, Arriba, and STAR-Fusion often generate results specific to individual samples, making participant-specific databases possible.
- **CASE vs. CTRL database:** Should I combine CASE and CTRL files into one file or separate files? -> ALL CASE fusions/splicing vs ALL CTRL fusions/splicing? Only use CASE files to build a CASE-specific database? -> would then be disease-relevant and will exclude proteins not involved in disease.
  
---
  
### Future Improvements
  
#### 1. Filtering Options prior to building the database
  
To reduce false positives
    * Use: PSI, p-value, FDR, read support (junction reads, spanning reads)
  
1. PSI (Percent Spliced In)
    - PSI is the ratio of normalized read counts indicating inclusion of a transcript element over the total normalized reads for that event (both inclusion and exclusion reads). This helps determine the relative inclusion level of a splicing event.
    - Example: A PSI value of .8 for an exon skip event would indicate that the exon is included in approximately 80% of the transcripts in the sample.
    - For rMATS, first estimate PSI ([rMATS-STAT](https://github.com/Xinglab/rMATS-STAT/ ))
  
2. **Statistical significance**
  
   - FDR ≤ 0.05 (or FDR ≤ 0.1 for higher sensitivity) *and* P Value < 0.05 to select events with strong evidence of differential splicing.
   - Found in `[AS_Event].MATS.JC.txt` and `[AS_Event].MATS.JCEC.txt` files.
  
3. **Length filter** -> optional since it could exclude biologically relevant isoforms
  
   - Exclude predicted peptides shorter than a certain length for MS (e.g., < 7–8 aa), but include anything that produces unique tryptic peptides of ≥7 aa.
  
4. **Redundancy**
  
   - Merge identical protein sequences (keep one and aggregate metadata file of all events).
  
#### 2. Reannotate fasta files with UniProt IDs and gene symbols
  
Reannotate FASTA peptide sequence headings for consistency between tools and to add helpful metadata for downstream analyses.
  
- Current header:
  
    >rMATS_seq_3|gene_id=ENSG00000130826.19|gene_symbol=DKC1|tx=ENST00000696575.1|event=A3SS|len=509
    >same for SUPPA
  
- Ideal header:
  
    >SUPPA_seq_1|gene_id|gene_symbol|ENST|EVENT_ID|ENSP|PValue|dpsi|LEN|FRAME(class)
    >rMATS_seq_1|gene_id|gene_symbol|ENST|EVENT_ID|ENSP|PValue|FDR|LEN|FRAME(class)
  
  - Use UniProt to annotate: <https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz>
  
> **NOTE:** UniProt ID mapping can only be done using ENSG and ENST identifiers. This must be checked again since I am now using GENCODE46 instead of Ensembl.
  
#### 3. Frame classification
  
A previous iteration of this script classifed events based on whether they preserve or disrupt the reading frame.
  
- Frameshifts lead to premature stop codons or altered protein sequences.
- This classification can help prioritize events for downstream analysis, as frame-disrupting events may have more significant functional consequences.
  
#### 4. Visualizations to add
  
- Summary statistics of event types, counts, and distributions.
- Barchart of classifications (`identical`, `frameshift`, `premature_stop`, `extended`, `in_frame_change`, `other`).
- Plot of protein length distribution (ref vs alt) colored by classification.
- Top genes by isoform count (bar chart) to show genes with most alternative splicing.
- PSI (dPSI) distributions across samples.
- Venn diagrams of overlapping events between CASE and CTRL.
- A network mapping genes to their alternative isoforms and proteins.
- Functional impact domain barplot using proportion of lost/altered Pfam domains across all proteins -> rMATS gives Pfam domain impact predictions.
  
---
  
### Final Step before nf-core/quantms
  
* Add in common contaminants (cRAP) and
* Optionally reference proteome sequences to create a final combined fasta file for peptide identification.
  
```bash
>P00761 SWISS-PROT:P00761|TRYP_PIG Trypsin - Sus scrofa (Pig).
FPTDDDDKIVGGYTCAANSIPYQVSLNSGSHFCGGSLINSQWVVSAAHCYKSRIQVRLGE
HNIDVLEGNEQFINAAKIITHPNFNGNTLDNDIMLIKLSSPATLNSRVATVSLPRSCAAA
GTECLISGWGNTKSSGSSYPSLLQCLKAPVLSDSSCKSSYPGQITGNMICVGFLEGGKDS
CQGDSGGPVVCNGQLQGIVSWGYGCAQKNKPGVYTKVCNYVNWIQQTIAAN
  
>Q32MB2 TREMBL:Q32MB2;Q86Y46 Tax_Id=9606 Gene_Symbol=KRT73 Keratin-73
MSRQFTYKSGAAAKGGFSGCSAVLSGGSSSSYRAGGKGLSGGFSSRSLYSLGGARSISFN
VASGSGWAGGYGFGRGRASGFAGSMFGSVALGSVCPSLCPPGGIHQVTINKSLLAPLNVE
LDPEIQKVRAQEREQIKVLNNKFASFIDKVRFLEQQNQVLETKWELLQQLDLNNCKNNLE
PILEGYISNLRKQLETLSGDRVRLDSELRSVREVVEDYKKRYEEEINKRTTAENEFVVLK
KDVDAAYTSKVELQAKVDALDGEIKFFKCLYEGETAQIQSHISDTSIILSMDNNRNLDLD
SIIAEVRAQYEEIARKSKAEAEALYQTKFQELQLAAGRHGDDLKHTKNEISELTRLIQRL
RSEIESVKKQCANLETAIADAEQRGDCALKDARAKLDELEGALQQAKEELARMLREYQEL
LSVKLSLDIEIATYRKLLEGEECRMSGEYTNSVSISVINSSMAGMAGTGAGFGFSNAGTY
GYWPSSVSGGYSMLPGGCVTGSGNCSPRGEARTRLGSASEFRDSQGKTLALSSPTKKTMR
```
  
---
  
### Sources
  
This is not a full list!
  
1. <https://github.com/tjcreedy/biotools/blob/main/translate.py> (more complicated)
2. <https://github.com/tjcreedy/biotools/blob/main/split_fasta_by_label.py>
3. <https://github.com/tjcreedy/biotools/blob/main/filter_fasta_by_fasta.py> (find unique peptides between two fastas)
4. <https://biopython.org/docs/1.75/api/Bio.Seq.html> (Bio.Seq manual)
5. <https://biopython.org/wiki/SeqIO> (SeqIO manual)
6. <https://github.com/uclahs-cds/package-moPepGen> (MoPepGen - similar peptide generation from variants)
7. <https://github.com/NKI-TGO/SPLICIFY> (Splicify - alternative splicing to protein sequences)
8. <https://github.com/Xinglab/rmats-turbo/tree/v4.1.0> (rMATS-turbo - alternative splicing detection)
  
---
  
  ![alt text](image-12.png)

  ![ORF vs CDS](image-13.png)

  ![alt text](image-14.png)
  http://bch709.plantgenomicslab.org/fig/rnaseq.png

  ![alt text](image-15.png)

  https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.nature.com%2Fscitable%2Fcontent%2Finfluence-of-structural-variants-on-phenotype-4355%2F&psig=AOvVaw2dae91iREImKcI9SnmzRNr&ust=1763657936912000&source=images&cd=vfe&opi=89978449&ved=2ahUKEwjlvvn31_6QAxVLdkEAHV1APMAQjhx6BAgAEBs

  ![alt text](image-16.png)
  https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs41576-019-0180-9&psig=AOvVaw0Be9VTB6VVQC7Q3ZTCh3Bn&ust=1763657901202000&source=images&cd=vfe&opi=89978449&ved=2ahUKEwiL9fXm1_6QAxXec0EAHRKgMokQjhx6BAgAEBs
  ![alt text](image-17.png)
  https://gatk.broadinstitute.org/hc/article_attachments/26023438671003

  ![alt text](image-18.png)
  https://www.google.com/url?sa=i&url=https%3A%2F%2Fuw.pressbooks.pub%2Ffmrmolbio%2Fchapter%2Fday-1-hour-3-transcription-and-translation%2F&psig=AOvVaw3K1PC3DiE7tEtPNaxKywo6&ust=1763657862345000&source=images&cd=vfe&opi=89978449&ved=2ahUKEwiAqLLU1_6QAxUbZkEAHX7RKSgQjhx6BAgAEBs

  https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.cell.com%2Ffulltext%2FS2211-1247%252817%252930991-9&psig=AOvVaw1dsZv_8--antGdJZvmS8Qg&ust=1763657789618000&source=images&cd=vfe&opi=89978449&ved=2ahUKEwiKrtux1_6QAxVIbkEAHUiyNwMQjhx6BAgAEBs
  ![alt text](image-19.png)
  ![alt text](image-20.png)
  https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.sciencedirect.com%2Fscience%2Farticle%2Fpii%2FS2211124717309919&psig=AOvVaw1joW6r0lyRXOuvHZU2EgCB&ust=1763657747288000&source=images&cd=vfe&opi=89978449&ved=2ahUKEwj_38Od1_6QAxXHdkEAHbBrL9YQjhx6BAgAEBs