#!/usr/bin/env python3
"""
rMATS -> peptide FASTA:
Parse rMATS event files and generate variant protein and junction peptide FASTA files.

Usage example:
python parse_rmats_18112025.py \
   --gtf /home/kcoetzer/nf/nf_references/GRCh38/gencode_v46/gencode/Homo_sapiens_GRCh38_46.gtf \
    --genome /home/kcoetzer/nf/nf_references/GRCh38/gencode_v46/gencode/Homo_sapiens_GRCh38_46_dna_primary_assembly.fa \
    --se_files /home/kcoetzer/nf/nf_results/rnasplice/batch3/star_salmon/rmats/CASE-CTRL/rmats_post/SE.MATS.JC.txt \
    --a3ss_files /home/kcoetzer/nf/nf_results/rnasplice/batch3/star_salmon/rmats/CASE-CTRL/rmats_post/A3SS.MATS.JC.txt \
    --a5ss_files /home/kcoetzer/nf/nf_results/rnasplice/batch3/star_salmon/rmats/CASE-CTRL/rmats_post/A5SS.MATS.JC.txt \
    --mxe_files /home/kcoetzer/nf/nf_results/rnasplice/batch3/star_salmon/rmats/CASE-CTRL/rmats_post/MXE.MATS.JC.txt \
    --ri_files /home/kcoetzer/nf/nf_results/rnasplice/batch3/star_salmon/rmats/CASE-CTRL/rmats_post/RI.MATS.JC.txt \
                --translation_mode longest_orf \
                    --pad_partial_codons \
                --gtf_db /home/kcoetzer/objective_four/db_cache/Homo_sapiens_GRCh38_46.gtf.db \
                    --out_prot_fa rmats_proteins_18112025.fa \
                        --out_junc_fa rmats_junctions_18112025.fa \
                            --short_junction_peptides \
                                --junction_max_flank 15 \
                                    --junction_min_flank 7
"""
import argparse
from pathlib import Path
import re
import time
import logging
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

import pandas as pd
import gffutils
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
from tqdm import tqdm

from typing import NamedTuple

Interval = Tuple[int, int]

class CDSSegment(NamedTuple):
    start: int
    end: int
    frame: int

# pyfaidx for indexed FASTA access
try:
    from pyfaidx import Fasta
except Exception as e:
    raise SystemExit("Error: pyfaidx is required. Install with `pip install pyfaidx`") from e

# --------------------------- HELPERS: INTERVALS AND OVERLAPS ---------------------------
def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return not (a_end < b_start or b_end < a_start)

def subtract_interval_list(intervals: List[Tuple[int,int]], rem_start: int, rem_end: int) -> List[Tuple[int,int]]:
    out = []
    for s,e in intervals:
        if e < rem_start or s > rem_end:
            out.append((s,e))
        else:
            if s < rem_start:
                out.append((s, rem_start-1))
            if e > rem_end:
                out.append((rem_end+1, e))
    return out

def replace_interval_in_list(intervals: List[Tuple[int,int]], target_start:int, target_end:int, replacement_intervals:List[Tuple[int,int]]) -> List[Tuple[int,int]]:
    """Replace the region in `intervals` that overlaps [target_start,target_end] with `replacement_intervals`. The replacement is inserted only once (first time an overlapping interval is found). Any contiguous intervals merged after replacement to keep the list minimal."""
    out = []
    repl = list(replacement_intervals)
    for s,e in intervals:
        if e < target_start or s > target_end:
            out.append((s,e))
        else:
            if s < target_start:
                out.append((s, target_start-1))
            if repl:
                out.extend(repl)
                repl = []
            if e > target_end:
                out.append((target_end+1, e))
    # merge contiguous intervals
    out_sorted = sorted(out, key=lambda x: x[0])
    merged = []
    for s,e in out_sorted:
        if not merged:
            merged.append((s,e))
        else:
            ps,pe = merged[-1]
            if s <= pe+1:
                merged[-1] = (ps, max(pe,e))
            else:
                merged.append((s,e))
    return merged

def merge_intervals(intervals: List[Tuple[int,int]]) -> List[Tuple[int,int]]:
    # A minimal merge utility used by other helpers that need it in future.
    if not intervals:
        return []
    iv = sorted(intervals, key=lambda x: x[0])
    merged = [iv[0]]
    for s,e in iv[1:]:
        ps,pe = merged[-1]
        if s <= pe+1:
            merged[-1] = (ps, max(pe,e))
        else:
            merged.append((s,e))
    return merged

# --------------------------- FASTA handling (pyfaidx) ---------------------------
def open_genome_index(genome: str):
    return Fasta(genome, sequence_always_upper=True, rebuild=False)

def extract_sequence_from_indexed_genome(fa_index, chrom: str, segments: List[Tuple[int,int]], strand: str) -> Optional[str]:
    """Fetch concatenated sequence for segments from pyfaidx Fasta object.
    segments are 1-based inclusive coordinates list of (start,end)."""
    # Normalize chromosome name to match keys in pyfaidx index ('chrN' or 'N')
    if chrom not in fa_index:
        alt = None
        if chrom.startswith("chr"):
            alt = chrom[3:] if chrom[3:] in fa_index else None
        else:
            alt = "chr"+chrom if ("chr"+chrom) in fa_index else None
        if not alt:
            return None
        chrom = alt
    seq_parts = []
    for s,e in segments:
        if s <= 0 or e < s:
            continue
        try:
            # pyfaidx uses 1-based inclusive coordinates; Python slicing
            # with pyfaidx expects 0-based start index, so use [s-1:e]
            seq_parts.append(str(fa_index[chrom][s-1:e]))
        except Exception:
            return None
    if not seq_parts:
        return None
    full = "".join(seq_parts)
    if strand == "-":
        return str(Seq(full).reverse_complement())
    return full

# --------------------------- TRANSCRIPT ID RESOLUTION AND PARSE GTF---------------------------
def match_transcript_id(tx_id: str, transcripts: dict) -> Optional[str]:
    """Resolve transcript identifier to a key present in `transcripts`.
    Accepts IDs with or without version suffixes (e.g. ENST00000312345.1 vs ENST00000312345) and will try to find the best match. Returns the matching transcript key from `transcripts` or None if not found.
    """
    logger = logging.getLogger(__name__)
    if not tx_id:
        return None
    # direct match
    if tx_id in transcripts:
        return tx_id
    # strip version suffix if present
    base = tx_id.split('.', 1)[0]
    if base in transcripts:
        return base
    # try to find a transcript key that starts with the base (e.g. stored as ENST... .1)
    for k in transcripts.keys():
        if k.startswith(base + '.'):
            return k
    # try the reverse: if provided tx lacks version but transcripts use versionless names
    for k in transcripts.keys():
        if k.split('.', 1)[0] == base:
            return k
    logger.warning("match_transcript_id: no match for %s", tx_id)
    return None

# --------------------------- BUILD TRANSCRIPTS MODEL (gene -> transcripts) -----------
def build_transcript_models(gtf_path: Optional[str] = None, prebuilt_db: Optional[str] = None) -> Dict[str, Dict]:
    """Build transcript models using a gffutils DB.
    If `prebuilt_db` is provided it will be opened. Otherwise `gtf_path` must be provided and a gffutils DB will be created alongside the GTF file (filename: `<gtf>+.db`) if it does not already exist.
    """
    logger = logging.getLogger(__name__)
    db = None
    if prebuilt_db:
        prebuilt_path = Path(prebuilt_db)
        if not prebuilt_path.exists():
            raise ValueError(f"Prebuilt gffutils DB not found: {prebuilt_db}")
        logger.info("Opening gffutils DB at %s", prebuilt_path)
        t0 = time.time()
        db = gffutils.FeatureDB(str(prebuilt_path), keep_order=True)
        logger.info("Loaded gffutils DB in %.2fs", time.time() - t0)
    else:
        if not gtf_path:
            raise ValueError("Either --gtf_db or --gtf must be provided")
        gtf_p = Path(gtf_path)
        if not gtf_p.exists():
            raise ValueError(f"GTF file not found: {gtf_path}")
        dbfn = str(gtf_p) + ".db"
        db_path = Path(dbfn)
        if not db_path.exists():
            logger.info("Creating gffutils DB at %s from %s (this may take a while)", dbfn, gtf_path)
            t0 = time.time()
            gffutils.create_db(str(gtf_p), dbfn, force=False, keep_order=True, merge_strategy='merge')
            logger.info("Created gffutils DB in %.2fs", time.time() - t0)
        else:
            logger.info("Using existing gffutils DB at %s", dbfn)
        db = gffutils.FeatureDB(str(db_path), keep_order=True)

    # Extract transcript models (exons, CDS, frames) from gffutils DB.
    transcripts = {}
    for tx in db.features_of_type("transcript"):
        tid = tx.attributes.get("transcript_id", [tx.id])[0]
        gene_id = tx.attributes.get("gene_id", ["NA"])[0]
        # gene name / symbol
        gene_name = None
        for k in ("gene_name","gene_symbol","gene"):
            if k in tx.attributes:
                gene_name = tx.attributes.get(k, [None])[0]
                if gene_name:
                    break
        chrom = tx.chrom
        strand = tx.strand
        exons = [(int(e.start), int(e.end)) for e in db.children(tx, featuretype="exon", order_by="start")]
        cds = []
        for c in db.children(tx, featuretype="CDS", order_by="start"):
            frame = 0
            try:
                if hasattr(c, 'frame') and c.frame and c.frame != '.':
                    frame = int(c.frame)
            except Exception:
                frame = 0
            cds.append((int(c.start), int(c.end), frame))
        transcripts[tid] = {
            "transcript_id": tid,
            "gene_id": gene_id,
            "gene_name": gene_name,
            "chrom": chrom,
            "strand": strand,
            "exons": sorted(exons, key=lambda x: x[0]),
            "cds": sorted(cds, key=lambda x: x[0]),
        }

    # aliases: versionless transcript IDs (make copies with correct transcript_id)
    orig_keys = list(transcripts.keys())
    for tid in orig_keys:
        if '.' in tid:
            base = tid.split('.',1)[0]
            if base not in transcripts:
                transcripts[base] = dict(transcripts[tid])
                transcripts[base]['transcript_id'] = base
    logger.info("Parsed %d transcripts (including aliases).", len(transcripts))
    return transcripts

# --------------------------- PROCESS GENE IDs -----------
def canonicalize_gene_field(raw_gene: str) -> str:
    """Used for build_transcripts_lookup.
    Return canonical forms to try to match GTF db keys: prefer ENSEMBL base id (no version),
    but preserve symbol otherwise. Caller should probe transcripts_lookup with multiple variants.
    """
    if raw_gene is None:
        return ""
    g = str(raw_gene).strip()
    if g == "":
        return ""
    # if ENSG, ENSMUSG or similar, strip version
    if re.match(r"^ENS[A-Z0-9]+", g, flags=re.IGNORECASE):
        return g.split('.',1)[0]
    # else return symbol as-is
    return g

def generate_gene_id_candidates(raw_gene: Optional[str]) -> List[str]:
    """Return ordered, deduplicated candidate keys to probe `transcripts_lookup`.
    Produces variants (raw, stripped ENSEMBL base id, upper/lower, spaceless, versionless) to increase chance of matching keys stored in the GTF DB.
    """
    if raw_gene is None:
        return ["NA"]
    g = str(raw_gene).strip()
    if g == "":
        return ["NA"]

    candidates = []
    # original form
    candidates.append(g)
    # canonical ENSEMBL base id
    base = canonicalize_gene_field(g)
    if base and base != g:
        candidates.append(base)
    # versionless form
    versionless = g.split('.', 1)[0]
    if versionless and versionless not in candidates:
        candidates.append(versionless)
    # case variants
    candidates.append(g.upper())
    candidates.append(g.lower())
    # spaceless symbol
    spaceless = g.replace(" ", "")
    if spaceless not in candidates:
        candidates.append(spaceless)

    # deduplicate preserving order
    seen = set()
    out = []
    for x in candidates:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

# --------------------------- BUILD TRANSCRIPTS LOOKUP (gene -> transcripts) -----------
def build_transcripts_lookup(transcripts: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Create mapping from gene_id/gene_name (+variants) to transcript list. 
    Not in SUPPA since the events.ioe files give transcript IDs already.
    """
    lookup = defaultdict(list)
    for tid, info in transcripts.items():
        gid = info.get("gene_id")
        gname = info.get("gene_name")
        if gid:
            base = str(gid).split('.',1)[0]
            lookup[gid].append(tid)
            lookup[base].append(tid)
        if gname:
            lookup[gname].append(tid)
            lookup[gname.upper()].append(tid)
            lookup[gname.lower()].append(tid)
    # deduplicate preserving order
    for k,v in list(lookup.items()):
        seen = set()
        out = []
        for x in v:
            if x not in seen:
                seen.add(x)
                out.append(x)
        lookup[k] = out
    return lookup

# --------------------------- BUILD VARIANT EXON CHAINS ---------------------------
def build_variant_chains_for_transcript(event_type: str, row: dict, tx_exons: List[Tuple[int,int]]) -> Dict[str, List[Tuple[int,int]]]:
    """Construct exon chains for a transcript given an rMATS event row.
    Interpret rMATS coordinate columns with names containing '_0base' as 0-based starts and convert them to 1-based.
    """
    def safe_int(val):
        try:
            return int(val)
        except Exception:
            return None

    def get_int(names, zero_based=False):
        for n in names:
            if n in row and pd.notna(row[n]):
                v = safe_int(row[n])
                if v is None:
                    return None
                # rMATS sometimes reports 0-based starts (column name includes
                # '_0base'). If `zero_based` is True convert to 1-based coords
                # consistent with GTF/pyfaidx expectations.
                return v + 1 if zero_based else v

        return None

    chains = {}

    # SE
    if event_type == "SE":
        exon_s = get_int(['exonStart_0base'], zero_based=True)
        exon_e = get_int(['exonEnd'], zero_based=False)
        if exon_s is None or exon_e is None:
            identifier = row.get('ID') or row.get('Event') or row.get('GeneID') or row.get('geneSymbol') or ''
            logging.warning("Missing coordinates for SE event; skipping (id=%s)", identifier)
            return {}
        chains['included'] = tx_exons.copy()
        chains['skipped'] = subtract_interval_list(tx_exons, exon_s, exon_e)

    # A3SS / A5SS
    elif event_type in ("A3SS", "A5SS"):
        long_s = get_int(['longExonStart_0base', 'longExonStart'], zero_based=True)
        long_e = get_int(['longExonEnd', 'longExonEnd_0base'], zero_based=False)
        short_s = get_int(['shortES', 'flankingES', 'shortExonStart_0base', 'shortExonStart'], zero_based=True)
        short_e = get_int(['shortEE', 'flankingEE', 'shortExonEnd', 'shortExonEnd_0base'], zero_based=False)
        if None in (long_s, long_e, short_s, short_e):
            identifier = row.get('ID') or row.get('Event') or row.get('GeneID') or row.get('geneSymbol') or ''
            logging.warning("Missing coordinates for %s event; skipping (id=%s)", event_type, identifier)
            return {}
        chains['long'] = replace_interval_in_list(tx_exons, long_s, long_e, [(long_s, long_e)])
        chains['short'] = replace_interval_in_list(tx_exons, short_s, short_e, [(short_s, short_e)])

    # MXE
    elif event_type == "MXE":
        x1_s = get_int(['1stExonStart_0base', 'X1stExonStart_0base'], zero_based=True)
        x1_e = get_int(['1stExonEnd', 'X1stExonEnd'], zero_based=False)
        x2_s = get_int(['2ndExonStart_0base', 'X2ndExonStart_0base'], zero_based=True)
        x2_e = get_int(['2ndExonEnd', 'X2ndExonEnd'], zero_based=False)
        if None in (x1_s, x1_e, x2_s, x2_e):
            identifier = row.get('ID') or row.get('Event') or row.get('GeneID') or row.get('geneSymbol') or ''
            logging.warning("Missing coordinates for MXE event; skipping (id=%s)", identifier)
            return {}
        chains['exon1'] = replace_interval_in_list(tx_exons, x1_s, x1_e, [(x1_s, x1_e)])
        chains['exon2'] = replace_interval_in_list(tx_exons, x2_s, x2_e, [(x2_s, x2_e)])

    # RI
    elif event_type == "RI":
        ri_s = get_int(['riExonStart_0base'], zero_based=True)
        ri_e = get_int(['riExonEnd'], zero_based=False)
        up_e = get_int(['upstreamEE'], zero_based=False)
        down_s = get_int(['downstreamES'], zero_based=False)
        if ri_s is None or ri_e is None:
            return {}
        up_e = up_e if up_e is not None else ri_s - 1
        down_s = down_s if down_s is not None else ri_e + 1
        chains['retained'] = replace_interval_in_list(tx_exons, up_e + 1, down_s - 1, [(up_e + 1, down_s - 1)])
        chains['spliced'] = subtract_interval_list(tx_exons, up_e + 1, down_s - 1)

    # sort
    for k in list(chains.keys()):
        chains[k] = sorted(chains[k], key=lambda x: x[0])
    return chains

# --------------------------- CDS INTERSECTION AND FRAME CALCULATION ---------------------------
def intersect_chain_with_cds(exon_chain: List[Interval], cds_list: List[CDSSegment]) -> List[CDSSegment]:
    """Intersect exon_chain with cds_list and return list of (start,end,frame)."""
    cds_segs = []
    for c_s,c_e,c_frame in cds_list:
        for e_s,e_e in exon_chain:
            if overlaps(e_s,e_e,c_s,c_e):
                ov_s = max(e_s,c_s)
                ov_e = min(e_e,c_e)
                if ov_s <= ov_e:
                    cds_segs.append((ov_s, ov_e, c_frame))
    return sorted(cds_segs, key=lambda x: x[0])

def compute_upstream_cds_nt(transcript_cds: List[Tuple[int,int,int]], first_overlap_pos: int, strand: str) -> int:
    """Return number of coding nucleotides from transcript CDS start up to first_overlap_pos.
    Ensure CDS list is in genomic coordinate order
    Transcript order (the order nucleotides appear in the mRNA) depends on strand: '+' uses ascending genomic coordinates, '-' uses descending.
    """
    if not transcript_cds:
        return 0

    cds_sorted = sorted(transcript_cds, key=lambda x: x[0])
    if strand == '+':
        ordered = cds_sorted
    else:
        ordered = list(reversed(cds_sorted))

    total = 0
    for c_s, c_e, _ in ordered:
        if strand == '+':
            if first_overlap_pos > c_e:
                total += (c_e - c_s + 1)
            else:
                if first_overlap_pos <= c_s:
                    return total
                return total + (first_overlap_pos - c_s)
        else:
            if first_overlap_pos < c_s:
                total += (c_e - c_s + 1)
            else:
                if first_overlap_pos >= c_e:
                    return total
                return total + (c_e - first_overlap_pos)
    return total

def first_overlap_in_cds_order(cds_segments: List[Tuple[int,int,int]], strand: str) -> Optional[int]:
    """Return the genomic coordinate of the first overlap position in transcript order.
    For '+' strand this is the start coordinate of the first CDS segment; for '-' strand it's the end coordinate of the first CDS segment in transcript order.
    Returns None if `cds_segments` is empty.
    """
    if not cds_segments:
        return None
    cds_sorted = sorted(cds_segments, key=lambda x: x[0])
    if strand == '+':
        s, e, f = cds_sorted[0]
        return s
    else:
        s, e, f = cds_sorted[-1]
        return e

def compute_frame_at_genomic_pos(transcript_cds: List[Tuple[int,int,int]], genomic_pos: int, strand: str) -> int:
    """Compute codon frame (0/1/2) of genomic_pos relative to transcript CDS start using CDS feature frames if available.
    GTF `frame` field can indicate how CDS features align to codon boundaries.
    Instead of relying solely on feature frames we compute cumulative coding nucleotides from the transcript CDS start up to `genomic_pos` and take mod 3. This is robust when CDS features are contiguous; callers may still prefer GTF-provided frame where available.
    """
    if not transcript_cds:
        return 0
    # order in transcript order
    ordered = transcript_cds if strand == '+' else list(reversed(transcript_cds))
    nt = 0
    for c_s, c_e, c_frame in ordered:
        length = c_e - c_s + 1
        
        if strand == '+':
            if genomic_pos > c_e:
                nt += length
            else:
                if genomic_pos <= c_s:
                    return nt % 3
                return (nt + (genomic_pos - c_s)) % 3
        else:
            if genomic_pos < c_s:
                nt += length
            else:
                if genomic_pos >= c_e:
                    return nt % 3
                return (nt + (c_e - genomic_pos)) % 3
    return nt % 3

# --------------------------- TRIM/PAD ---------------------------
def trim_to_codon(seq: str) -> str:
    rem = len(seq) % 3
    return seq if rem==0 else seq[:-rem]

def pad_to_codon(seq: str) -> str:
    rem = len(seq) % 3
    return seq if rem == 0 else seq + ("N" * (3 - rem))

# --------------------------- TRANSLATION HELPERS ---------------------------
def find_orfs(seq: str, pad: bool = False):
    """Find ORFs in `seq` returning tuples (start_nt, end_nt, aa_seq).
    Each reading frame is trimmed or padded to a multiple-of-3 before translation to avoid partial-codon warnings from Biopython. Pass `pad=True` to pad trailing Ns instead of trimming.
    """
    orfs = []
    seq_u = seq.upper().replace('U', 'T')
    n = len(seq_u)
    for frame in range(3):
        # Ensure sequence for this frame is codon-aligned
        seq_frame = seq_u[frame:]
        seq_frame = pad_to_codon(seq_frame) if pad else trim_to_codon(seq_frame)
        if not seq_frame:
            continue
        prot = str(Seq(seq_frame).translate(to_stop=False))
        for i, aa in enumerate(prot):
            if aa == 'M':
                j = prot.find('*', i)
                if j != -1:
                    start_nt = frame + i*3
                    end_nt = frame + j*3
                    aa_seq = prot[i:j]
                    orfs.append((start_nt, end_nt, aa_seq))
                else:
                    start_nt = frame + i*3
                    end_nt = n
                    aa_seq = prot[i:]
                    orfs.append((start_nt, end_nt, aa_seq))
    return orfs

def translate_from_first_atg_or_longest_orf(cds_seq: str, pad: bool=False) -> Optional[str]:
    if not cds_seq:
        return None
    cds = cds_seq.upper().replace('U','T')
    pos = cds.find('ATG')
    if pos != -1:
        seq_for = cds[pos:]
        seq_for = pad_to_codon(seq_for) if pad else trim_to_codon(seq_for)
        aa = str(Seq(seq_for).translate(to_stop=False))
        return aa[:-1] if aa.endswith('*') else aa
    longest = ""
    for frame in range(3):
        seq_frame = pad_to_codon(cds[frame:]) if pad else trim_to_codon(cds[frame:])
        if not seq_frame:
            continue
        prot = str(Seq(seq_frame).translate(to_stop=False))
        orfs = prot.split('*')
        best = max(orfs, key=len) if orfs else ""
        if len(best) > len(longest):
            longest = best
    return longest if longest else None

def translate_from_position(cds_seq: str, pad: bool=False) -> Optional[str]:
    if not cds_seq:
        return None
    seq_proc = cds_seq.upper().replace('U','T')
    seq_proc = pad_to_codon(seq_proc) if pad else trim_to_codon(seq_proc)
    aa = str(Seq(seq_proc).translate(to_stop=False))
    if not aa:
        return None
    return aa[:-1] if aa.endswith('*') else aa

def translate_longest_orf_only(cds_seq: str, pad: bool=False) -> Optional[str]:
    if not cds_seq:
        return None
    cds = cds_seq.upper().replace('U','T')
    longest = ""
    for frame in range(3):
        seq_frame = pad_to_codon(cds[frame:]) if pad else trim_to_codon(cds[frame:])
        if not seq_frame:
            continue
        orfs = find_orfs(seq_frame, pad=pad)
        if not orfs:
            continue
        best_aa = max(orfs, key=lambda x: len(x[2]))[2]
        if len(best_aa) > len(longest):
            longest = best_aa
    return longest if longest else None

# --------------------------- CODON-AWARE SHORT JUNCTION PEPTIDE GENERATION ---------------------------
def generate_codon_aware_junction_peptides(cds_segments: List[Tuple[int,int,int]], tx_model: Dict,
                                           prot_id: str, var_name: str, event_type: str,
                                           genome_index, max_flank: int = 15, min_flank: int = 7,
                                           pad: bool = False) -> List[SeqRecord]:
    """ Generate codon-aware junction peptides for MS search.
    """
    peptides = []
    # transcript info
    strand = tx_model.get('strand')
    # Build a linear transcript CDS coordinate map
    nt_cum = 0
    junction_nt_positions = []
    ordered_cds = cds_segments if strand == '+' else list(reversed(cds_segments))
    for i, (s, e, f) in enumerate(ordered_cds):
        length = e - s + 1
        if i > 0:
            # junction at start of this CDS relative to transcript
            junction_nt_positions.append(nt_cum)
        nt_cum += length

    # Generate peptides around each junction
    for j_nt in junction_nt_positions:
        # compute codon-aware start/end in nt
        start_nt = max(0, j_nt - max_flank*3)
        end_nt = min(nt_cum, j_nt + max_flank*3)
        # adjust start_nt to codon boundary
        frame_at_start = j_nt % 3
        if frame_at_start != 0:
            start_nt += (3 - frame_at_start)
        # ensure peptide covers minimum length
        if (end_nt - start_nt)//3 < min_flank*2:
            continue

        """Naive mapping: treat the ordered CDS segments as a single concatenated coding region and map transcript-relative nucleotide offsets into genomic segments by walking CDS segments in order."""
        
        # extract genomic segments corresponding to start_nt:end_nt
        remaining_nt_start = start_nt
        remaining_nt_end = end_nt
        segments_to_fetch = []
        for s, e, f in ordered_cds:
            seg_len = e - s + 1
            if remaining_nt_end <= 0:
                break
            if remaining_nt_start < seg_len:
                seg_start = s + remaining_nt_start
                seg_end = min(e, s + remaining_nt_end - 1)
                segments_to_fetch.append((seg_start, seg_end))
            remaining_nt_start -= seg_len
            remaining_nt_end -= seg_len
            if remaining_nt_start < 0:
                remaining_nt_start = 0

        if not segments_to_fetch:
            continue
        pep_seq_nt = extract_sequence_from_indexed_genome(genome_index, tx_model['chrom'], segments_to_fetch, strand)
        if not pep_seq_nt:
            continue
        # trim or pad to codon boundary to avoid Biopython partial-codon warnings
        seq_for = pad_to_codon(pep_seq_nt) if pad else trim_to_codon(pep_seq_nt)
        prot = str(Seq(seq_for).translate(to_stop=False))
        if '*' in prot:
            prot = prot.split('*')[0]

        header = (
            f"{prot_id}|var={var_name}|gene_id={tx_model.get('gene_id','NA')}|"
            f"tx={tx_model.get('transcript_id','NA')}|gene_symbol={tx_model.get('gene_name','NA')}|"
            f"event={event_type}|junction_nt={j_nt}|pep_len={len(prot)}|flank_aa={max_flank}"
        )
        peptides.append(SeqRecord(Seq(prot), id=header, description=""))
    return peptides

# --------------------------- EVENT PROCESSING ---------------------------
def process_event_file(event_type: str, p: Path, transcripts: Dict[str, Dict], transcripts_lookup: Dict[str, List[str]], fa_index, args, prot_info: Dict[str, Tuple[str, Optional[str], str, Optional[str]]], junction_recs: Optional[List[SeqRecord]] = None):
    """Process a single rMATS event file and populate `prot_info` with unique proteins.
    `junction_recs` collects optional short junction peptide SeqRecords.
    """
    df = pd.read_csv(p, sep="\t", comment="#", low_memory=False)
    total = len(df)
    # iterate using record dicts to preserve original column names 
    for rid, rowd in enumerate(tqdm(df.to_dict(orient='records'), total=total, desc=p.name)):
        # `rowd` is already a plain dict mapping original column names -> values
        if not isinstance(rowd, dict):
            try:
                rowd = dict(rowd)
            except Exception:
                rowd = {}

        # --- canonicalize gene field from rMATS to match transcripts_lookup keys ---
        raw_gene = None
        for col in ('GeneID','gene_id','geneSymbol','geneSymbol.1','gene_id.1','gene_id.0'):
            if col in rowd and pd.notna(rowd[col]):
                raw_gene = str(rowd[col]).strip()
                break
        if raw_gene is None:
            raw_gene = 'NA'

        # produce ordered, deduplicated candidate keys to probe `transcripts_lookup`
        cand_ids = generate_gene_id_candidates(raw_gene)

        # find transcript list by probing lookup with candidates
        tx_list = []
        for c in cand_ids:
            if c in transcripts_lookup:
                tx_list = transcripts_lookup[c]
                break

        if not tx_list:
            # last resort: try gene symbol without spaces
            gnospace = raw_gene.replace(" ","")
            tx_list = transcripts_lookup.get(gnospace, [])

        if not tx_list:
            logging.debug("No transcripts found in lookup for gene identifier candidates: %s", cand_ids)
            continue

        # iterate candidate transcripts
        for tx in tx_list:
            m = match_transcript_id(tx, transcripts)
            if not m:
                logging.warning("Transcript resolution failed for %s (gene %s)", tx, raw_gene)
                continue

            # use resolved transcript key 'm' everywhere
            tx_model = transcripts[m]
            chains = build_variant_chains_for_transcript(event_type, rowd, tx_model['exons'])
            for var_name, chain_exons in chains.items():
                cds_segments = intersect_chain_with_cds(chain_exons, tx_model['cds'])
                if not cds_segments:
                    continue

                # ensure segments are sorted by transcript genomic order
                segments_for_extraction = [(s, e) for s, e, _ in cds_segments]

                seq_nt = extract_sequence_from_indexed_genome(fa_index, tx_model['chrom'], segments_for_extraction, tx_model['strand'])
                if not seq_nt:
                    logging.debug("Sequence extraction failed for %s %s", m, segments_for_extraction)
                    continue

                # ---- strand-aware first_overlap_pos selection ----
                # Use helper that returns the genomic coordinate corresponding to the
                # first position in transcript order (start for '+', end for '-').
                first_overlap_pos = first_overlap_in_cds_order(cds_segments, tx_model['strand'])
                if first_overlap_pos is None:
                    # no CDS segments -> skip
                    continue

                # ---- compute upstream_nt in transcript order ----
                upstream_nt = compute_upstream_cds_nt(tx_model['cds'], first_overlap_pos, tx_model['strand'])

                # ---- compute/check frame from GTF and prefer that if mismatch ----
                gtf_frame = compute_frame_at_genomic_pos(tx_model['cds'], first_overlap_pos, tx_model['strand'])
                inferred_frame = upstream_nt % 3
                if gtf_frame != inferred_frame:
                    logging.debug("Frame mismatch for %s at %d: gtf_frame=%d inferred=%d. Using gtf_frame.",
                                  m, first_overlap_pos, gtf_frame, inferred_frame)
                    trim = gtf_frame
                else:
                    trim = inferred_frame

                # trim/pad region to codon boundary
                trimmed = False
                if trim and len(seq_nt) > trim:
                    seq_untrimmed = seq_nt
                    seq_nt = seq_nt[trim:]
                    trimmed = True
                else:
                    seq_untrimmed = seq_nt

                # If --prefer_annotated_start selected, try to start from canonical start
                canonical_included = False
                cds_list = tx_model['cds']
                if tx_model['strand'] == '+':
                    canonical_start = min((c[0] for c in cds_list), default=None)
                else:
                    canonical_start = max((c[1] for c in cds_list), default=None)

                if canonical_start is not None:
                    canonical_upstream = compute_upstream_cds_nt(cds_list, canonical_start, tx_model['strand'])
                    total_nt = sum((e - s + 1) for s,e,_ in cds_segments)
                    if canonical_upstream >= upstream_nt and canonical_upstream < (upstream_nt + total_nt):
                        canonical_included = True

                pad_flag = args.pad_partial_codons
                pref = args.prefer_annotated_start
                mode = args.translation_mode

                prot = None
                if args.prefer_annotated_start and canonical_included:
                    canonical_upstream = compute_upstream_cds_nt(cds_list, canonical_start, tx_model['strand'])
                    offset_untrimmed = canonical_upstream - upstream_nt
                    offset_trimmed = offset_untrimmed - trim
                    start_idx = 0 if offset_trimmed < 0 else offset_trimmed
                    if start_idx < len(seq_nt):
                        seq_for_trans = seq_nt[start_idx:]
                        prot = translate_from_position(seq_for_trans, pad=args.pad_partial_codons)

                if not prot:
                    if mode == "first_atg":
                        prot = translate_from_first_atg_or_longest_orf(seq_nt, pad=pad_flag)
                    else:
                        prot = translate_longest_orf_only(seq_nt, pad=pad_flag)

                if not prot:
                    continue

                coords_used = ";".join(f"{s}-{e}" for s, e in segments_for_extraction)
                header_meta = {
                    "gene_id": tx_model.get("gene_id"),
                    "tx": tx_model.get("transcript_id"),
                    "gene_symbol": tx_model.get("gene_name"),
                    "event": event_type,
                    "variant": var_name,
                    "coords": coords_used,
                    "first_overlap": str(first_overlap_pos),
                    "trim": str(trim),
                    "trimmed": str(trimmed),
                    "pad_partial_codons": str(pad_flag),
                    "translation_mode": mode,
                }
                # Use amino-acid sequence as the unique key for proteins.
                # This deduplicates identical protein sequences that may arise
                # from different transcripts/variants; header metadata is
                # stored in the mapping value for downstream reporting.
                if prot not in prot_info:
                    prot_info[prot] = (
                        header_meta["gene_id"],
                        header_meta["gene_symbol"],
                        header_meta["tx"],
                        header_meta.get("event"),
                    )
                else:
                    # keep existing mapping
                    pass

                # Optionally generate short junction peptides for MS search
                if args.short_junction_peptides:
                    prot_id = f"{tx_model.get('transcript_id','NA')}|{var_name}"
                    jrecs = generate_codon_aware_junction_peptides(
                        cds_segments=cds_segments,
                        tx_model=tx_model,
                        genome_index=fa_index,
                        prot_id=prot_id,
                        var_name=var_name,
                        event_type=event_type,
                        max_flank=args.junction_max_flank,
                        min_flank=args.junction_min_flank,
                        pad=args.pad_partial_codons,
                    )
                    junction_recs.extend(jrecs)

# --------------------------- FASTA WRITERS ---------------------------
def write_protein_fasta(prot_info, out_path):
    seq_records = []
    i = 1
    for prot, (gene_id, gene_symbol, tx, event) in prot_info.items():
        gene_symbol = gene_symbol if gene_symbol is not None else 'NA'
        gene_id = gene_id if gene_id is not None else 'NA'
        tx = tx if tx is not None else 'NA'
        event = event if event is not None else 'NA'
        seq_id = f"rMATS_seq_{i}|gene_id={gene_id}|gene_symbol={gene_symbol}|tx={tx}|event={event}|len={len(prot)}"
        seq_records.append(SeqRecord(Seq(prot), id=seq_id, description=""))
        i += 1

    logging.info("Writing FASTA to %s (unique sequences: %d)", out_path, len(seq_records))
    SeqIO.write(seq_records, out_path, "fasta")

def write_junction_fasta(junction_recs, out_path):
    uniq = {}
    for rec in junction_recs:
        key = str(rec.seq)
        if key not in uniq:
            uniq[key] = rec
    SeqIO.write(list(uniq.values()), out_path, "fasta")

# --------------------------- ARGUMENTS ---------------------------
def main():
    ap = argparse.ArgumentParser(description="rMATS → protein FASTA + codon-aware junction peptides")
    ap.add_argument("--gtf", help="GTF file path used to build gffutils DB (optional)")
    ap.add_argument("--gtf_db", help="gffutils DB created from GTF (optional)")
    ap.add_argument("--genome", required=True, help="Genome FASTA (indexed by pyfaidx)")
    ap.add_argument("--se_files", nargs="*", help="SE event files (rMATS)")
    ap.add_argument("--a3ss_files", nargs="*", help="A3SS event files (rMATS)")
    ap.add_argument("--a5ss_files", nargs="*", help="A5SS event files (rMATS)")
    ap.add_argument("--mxe_files", nargs="*", help="MXE event files (rMATS)")
    ap.add_argument("--ri_files", nargs="*", help="RI event files (rMATS)")

    ap.add_argument("--out_prot_fa", required=True)
    ap.add_argument("--out_junc_fa", required=True)

    ap.add_argument("--translation_mode", choices=["first_atg", "longest_orf"], default="longest_orf")
    ap.add_argument("--pad_partial_codons", action="store_true")
    ap.add_argument("--prefer_annotated_start", action="store_true")

    ap.add_argument("--short_junction_peptides", action="store_true")
    ap.add_argument("--junction_max_flank", type=int, default=15)
    ap.add_argument("--junction_min_flank", type=int, default=7)

    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not args.gtf_db and not args.gtf:
        ap.error("Either --gtf_db or --gtf must be provided")

    # Main work to run() 
    run(args)

# --------------------------- MAIN LOGIC ---------------------------
def run(args):
    """Run processing given parsed `args`"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # normalize file lists
    event_files = {
        "SE": args.se_files or [],
        "A3SS": args.a3ss_files or [],
        "A5SS": args.a5ss_files or [],
        "MXE": args.mxe_files or [],
        "RI": args.ri_files or []
    }
    for k,v in list(event_files.items()):
        if isinstance(v, str) and v:
            event_files[k] = [x for x in re.split(r'[,\s]+', v) if x]
        else:
            event_files[k] = v or []
            
    
    logging.info("Loading GTF DB or building from GTF if needed")
    transcripts = build_transcript_models(args.gtf, args.gtf_db)
    transcripts_lookup = build_transcripts_lookup(transcripts)

    # open pyfaidx genome index
    logging.info("Loading genome via pyfaidx: %s", args.genome)
    fa_index = open_genome_index(args.genome)

    prot_info: Dict[str, Tuple[str, Optional[str], str, Optional[str]]] = {}
    # collect short junction peptides if requested
    junction_recs: List[SeqRecord] = []

    for event_type, files in event_files.items():
        for fpath in files:
            if not fpath:
                continue
            p = Path(fpath)
            if not p.exists():
                logging.warning("Event file not found: %s", p)
                continue
            process_event_file(event_type, p, transcripts, transcripts_lookup, fa_index, args, prot_info, junction_recs)

    # write fasta of unique proteins
    write_protein_fasta(prot_info, args.out_prot_fa)

    if args.short_junction_peptides:
        write_junction_fasta(junction_recs, args.out_junc_fa)

if __name__ == "__main__":
    main()