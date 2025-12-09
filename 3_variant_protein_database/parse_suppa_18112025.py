#!/usr/bin/env python3
"""
SUPPA -> peptide FASTA:
Parse SUPPA event definitions to generate variant protein and junction peptide FASTA files.

Usage example:
python parse_suppa_18112025.py \
    --gtf /home/kcoetzer/nf/nf_references/GRCh38/gencode_v46/gencode/Homo_sapiens_GRCh38_46.gtf \
    --genome /home/kcoetzer/nf/nf_references/GRCh38/gencode_v46/gencode/Homo_sapiens_GRCh38_46_dna_primary_assembly.fa \
    --event_files /home/kcoetzer/nf/nf_results/rnasplice/batch3/star_salmon/suppa/generate_events/per_local_event/events.ioe \
                --translation_mode longest_orf \
                    --pad_partial_codons \
                --gtf_db /home/kcoetzer/objective_four/db_cache/Homo_sapiens_GRCh38_46.gtf.db \
                    --out_prot_fa suppa_proteins_18112025.fa \
                        --out_junc_fa suppa_junctions_18112025.fa \
                            --short_junction_peptides \
                                --junction_max_flank 15 \
                                    --junction_min_flank 7
"""
import argparse
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import gffutils
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
from tqdm import tqdm

# pyfaidx for indexed FASTA access
try:
    from pyfaidx import Fasta
except Exception as e:
    raise SystemExit("Error: pyfaidx is required. Install with `pip install pyfaidx`") from e

# --------------------------- HELPERS: INTERVALS AND OVERLAPS ---------------------------
def overlaps(a_start, a_end, b_start, b_end):
    return not (a_end < b_start or b_end < a_start)

def subtract_interval_list(intervals, rem_start, rem_end):
    out = []
    for s, e in intervals:
        if e < rem_start or s > rem_end:
            out.append((s, e))
        else:
            if s < rem_start:
                out.append((s, rem_start - 1))
            if e > rem_end:
                out.append((rem_end + 1, e))
    return out

def replace_interval_in_list(intervals, target_start, target_end, replacement_intervals):
    out = []
    repl = list(replacement_intervals)
    for s, e in intervals:
        if e < target_start or s > target_end:
            out.append((s, e))
        else:
            if s < target_start:
                out.append((s, target_start - 1))
            if repl:
                out.extend(repl)
                repl = []
            if e > target_end:
                out.append((target_end + 1, e))
    out_sorted = sorted(out, key=lambda x: x[0])
    merged = []
    for s, e in out_sorted:
        if not merged:
            merged.append((s, e))
        else:
            ps, pe = merged[-1]
            if s <= pe + 1:
                merged[-1] = (ps, max(pe, e))
            else:
                merged.append((s, e))
    return merged

def merge_intervals(intervals):
    intervals = sorted(intervals, key=lambda x: x[0])
    if not intervals:
        return []
    merged = [intervals[0]]
    for s, e in intervals[1:]:
        ps, pe = merged[-1]
        if s <= pe + 1:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged

def intersect_interval_lists(a, b):
    if not a or not b:
        return []
    a = merge_intervals(a)
    b = merge_intervals(b)
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        a_s, a_e = a[i]
        b_s, b_e = b[j]
        if a_e < b_s:
            i += 1
        elif b_e < a_s:
            j += 1
        else:
            out.append((max(a_s, b_s), min(a_e, b_e)))
            if a_e < b_e:
                i += 1
            else:
                j += 1
    return out

# --------------------------- FASTA handling (pyfaidx) ---------------------------
def open_genome_index(genome: str):
    """Open pyfaidx Fasta index."""
    return Fasta(genome, sequence_always_upper=True, rebuild=False)

def extract_sequence_from_indexed_genome(fa_index, chrom: str, segments: List[Tuple[int,int]], strand: str) -> Optional[str]:
    """Fetch concatenated sequence for segments from pyfaidx Fasta object.
    segments are 1-based inclusive coordinates list of (start,end)."""
    # normalize chrom
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
            # pyfaidx uses 1-based inclusive indexing
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

    Accepts IDs with or without version suffixes (e.g. ENST00000312345.1 vs ENST00000312345)
    and will try a few heuristics to find the best match. Returns the matching
    transcript key from `transcripts` or None if not found.
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

    If `prebuilt_db` is provided it will be opened. Otherwise `gtf_path` must
    be provided and a gffutils DB will be created alongside the GTF file
    (filename: `<gtf>+.db`) if it does not already exist.
    """
    logger = logging.getLogger(__name__)
    db_path = None
    if prebuilt_db:
        db_path = Path(prebuilt_db)
        if not db_path.exists():
            raise ValueError(f"Prebuilt gffutils DB not found: {prebuilt_db}")
        logger.info("Opening gffutils DB at %s", db_path)
        t0 = time.time()
        db = gffutils.FeatureDB(str(db_path), keep_order=True)
        logger.info("Loaded gffutils DB in %.2fs", time.time() - t0)
    else:
        if not gtf_path:
            raise ValueError("Either --gtf_db or --gtf must be provided")
        gtf_p = Path(gtf_path)
        if not gtf_p.exists():
            raise ValueError(f"GTF file not found: {gtf_path}")
        # create DB filename next to GTF: e.g. file.gtf -> file.gtf.db
        dbfn = str(gtf_p) + ".db"
        db_path = Path(dbfn)
        if not db_path.exists():
            logger.info("Creating gffutils DB at %s from %s (this may take a while)", dbfn, gtf_path)
            t0 = time.time()
            # create_db will write the sqlite DB
            gffutils.create_db(str(gtf_p), dbfn, force=False, keep_order=True, merge_strategy='merge')
            logger.info("Created gffutils DB in %.2fs", time.time() - t0)
        else:
            logger.info("Using existing gffutils DB at %s", dbfn)
        db = gffutils.FeatureDB(str(db_path), keep_order=True)

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

    # aliases: versionless transcript IDs
    orig_keys = list(transcripts.keys())
    for tid in orig_keys:
        if '.' in tid:
            base = tid.split('.',1)[0]
            if base not in transcripts:
                # copy the model and set the alias transcript_id to the base (versionless)
                transcripts[base] = dict(transcripts[tid])
                transcripts[base]['transcript_id'] = base
    logger.info("Parsed %d transcripts (including aliases).", len(transcripts))
    return transcripts

# --------------------------- SUPPA event parsing -----------
def split_list_field(val):
    if pd.isna(val):
        return []
    s = str(val).strip()
    if s in ("", "."):
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

def parse_suppa_event_coords(event_id: str):
    if not isinstance(event_id, str):
        return None
    parts = [p for p in re.split(r"[;\t]", event_id) if p]
    for p in parts:
        if "chr" in p and ":" in p:
            toks = p.split(":")
            # SUPPA event tokens have the form: TYPE:chr:range1:range2:...:strand
            # capture all intermediate range tokens (toks[2:-1]) so callers
            # can decide which ones are relevant per event type.
            if len(toks) >= 4:
                return {
                    "etype": toks[0],
                    "chrom": toks[1],
                    "ranges": toks[2:-1],
                    "strand": toks[-1],
                }
    return None

def parse_range(r):
    # TODO: what does this do?
    if isinstance(r, str) and "-" in r:
        a, b = r.split("-")
        try:
            a_i = int(a)
            b_i = int(b)
        except:
            return None
        if a_i == 0:
            a_i += 1
        if a_i > b_i:
            a_i, b_i = b_i, a_i
        return a_i, b_i
    return None

# --------------------------- BUILD VARIANT EXON CHAINS -----------
def build_variant_chains_for_transcript(event_type, row, tx_exons, parsed_coords=None, alt_merged=None, ref_merged=None):
    chains = {}
    parsed = parsed_coords or parse_suppa_event_coords(row.get("event_id") or row.get("event") or "")

    if parsed:
        etype = parsed["etype"].upper() if parsed.get("etype") else None
        # normalize common synonyms: SUPPA may use 'MX' for MXE and rMATS uses 'MXE'
        if etype == "MX":
            etype = "MXE"
        rs = parsed.get("ranges", []) if parsed else []

        if etype.startswith("SE"):
            r = parse_range(rs[0])
            if not r:
                return {}
            s, e = r
            chains["included"] = tx_exons.copy()
            chains["skipped"] = subtract_interval_list(tx_exons, s, e)

        elif etype in ("A3", "A3SS", "A5", "A5SS"):
            r1 = parse_range(rs[0])
            r2 = parse_range(rs[1])
            if not r1 or not r2:
                return {}
            long_s, long_e = r1
            short_s, short_e = r2
            chains["long"] = replace_interval_in_list(tx_exons, long_s, long_e, [(long_s, long_e)])
            chains["short"] = replace_interval_in_list(tx_exons, short_s, short_e, [(short_s, short_e)])

        elif etype == "MXE":
            # SUPPA MXE entries may include multiple range tokens; collect the
            # first two parsable ranges (a-b) and use them as the two mutually
            # exclusive exons. If fewer than two valid ranges are found, skip.
            parsed_ranges = [parse_range(x) for x in rs]
            valid = [r for r in parsed_ranges if r]
            if len(valid) < 2:
                return {}
            (s1, e1), (s2, e2) = valid[0], valid[1]
            chains["exon1"] = replace_interval_in_list(tx_exons, s1, e1, [(s1, e1)])
            chains["exon2"] = replace_interval_in_list(tx_exons, s2, e2, [(s2, e2)])

        elif etype == "RI":
            # SUPPA RI tokens sometimes place a single genomic coordinate in the
            # first token and the actual exon-range in a subsequent token. Try
            # the first parseable range token among rs.
            r = None
            for tok in rs:
                r = parse_range(tok)
                if r:
                    break
            if not r:
                return {}
            ri_s, ri_e = r
            chains["retained"] = replace_interval_in_list(tx_exons, ri_s, ri_e, [(ri_s, ri_e)])
            chains["spliced"] = subtract_interval_list(tx_exons, ri_s, ri_e)

    else:
        if alt_merged:
            a = intersect_interval_lists(tx_exons, alt_merged)
            if a:
                chains["alternative"] = a
        if ref_merged:
            r = intersect_interval_lists(tx_exons, ref_merged)
            if r:
                chains["reference"] = r

    for k in list(chains.keys()):
        chains[k] = sorted(chains[k], key=lambda x: x[0])
    return chains

# --------------------------- CDS INTERSECTION AND FRAME CALCULATION ---------------------------
def intersect_chain_with_cds(exon_chain, cds_list):
    out = []
    for c_s, c_e, frame in cds_list:
        for e_s, e_e in exon_chain:
            if overlaps(c_s, c_e, e_s, e_e):
                s = max(c_s, e_s)
                e = min(c_e, e_e)
                out.append((s, e, frame))
    return out

def compute_upstream_cds_nt(transcript_cds: List[Tuple[int,int,int]], first_overlap_pos: int, strand: str) -> int:
    """Return number of coding nucleotides from transcript CDS start up to first_overlap_pos (exclusive)."""
    if not transcript_cds:
        return 0
    # Ensure CDS list is in genomic coordinate order (ascending by start). 
    # The transcript order depends on strand: '+' uses ascending, '-' uses descending.
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

    For '+' strand this is the start coordinate of the first CDS segment; for '-'
    strand it's the end coordinate of the first CDS segment in transcript order.
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
    """Compute codon frame (0/1/2) of genomic_pos relative to transcript CDS start using CDS feature frames if available."""
    if not transcript_cds:
        return 0
    # order in transcript order
    ordered = transcript_cds if strand == '+' else list(reversed(transcript_cds))
    nt = 0
    for c_s, c_e, c_frame in ordered:
        length = c_e - c_s + 1
        # GTF frame indicates number of bases to skip at CDS feature start to reach codon boundary
        # But simpler: compute cumulative nt from transcript CDS start to genomic_pos and take mod 3
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

    Each reading frame is trimmed or padded to a multiple-of-3 before translation
    to avoid partial-codon warnings from Biopython. Pass `pad=True` to pad
    trailing Ns instead of trimming.
    """
    orfs = []
    seq_u = seq.upper().replace('U', 'T')
    n = len(seq_u)
    for frame in range(3):
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
    """
    Generate codon-aware junction peptides for MS search.
    cds_segments: list of (start,end,frame)
    tx_model: transcript model for headers (must contain 'strand','chrom','transcript_id','gene_id','gene_name')
    prot_id: unique protein ID
    var_name: variant name
    event_type: event type string
    genome_index: pyfaidx genome index (for sequence extraction)
    max_flank/min_flank: AA lengths on each side of junction
    """
    peptides = []

    # transcript-level info
    strand = tx_model["strand"]
    chrom = tx_model["chrom"]

    # Build a linear transcript CDS coordinate map (transcript-relative coordinates)
    if strand == "+":
        ordered = sorted(cds_segments, key=lambda x: x[0])
    else:
        ordered = sorted(cds_segments, key=lambda x: x[0], reverse=True)

    seg_lens = [e - s + 1 for (s, e, _) in ordered]
    total_nt = sum(seg_lens)

    transcript_seg_map = []
    cur = 0
    for (s, e, f), L in zip(ordered, seg_lens):
        transcript_seg_map.append((cur, cur + L - 1, s, e))
        cur += L

    # junction positions in transcript-relative nt coordinates (start of downstream segment)
    junction_nt_positions = [transcript_seg_map[i][0] for i in range(1, len(transcript_seg_map))]

    def map_window(win_s, win_e):
        out = []
        for t_s, t_e, g_s, g_e in transcript_seg_map:
            if win_e <= t_s or win_s > t_e:
                continue
            ov_s = max(win_s, t_s)
            ov_e = min(win_e - 1, t_e)
            off_s = ov_s - t_s
            off_e = ov_e - t_s
            gs = g_s + off_s
            ge = g_s + off_e
            out.append((gs, ge))
        return out

    for j_nt in junction_nt_positions:
        win_s = max(0, j_nt - max_flank*3)
        win_e = min(total_nt, j_nt + max_flank*3)
        if win_s % 3 != 0:
            win_s += (3 - (win_s % 3))
            if win_s >= win_e:
                continue

        aa_len = (win_e - win_s)//3
        if aa_len < (min_flank*2):
            need = (min_flank*2)*3 - (win_e - win_s)
            extra = min(total_nt - win_e, need)
            win_e = min(total_nt, win_e + extra)
            aa_len = (win_e - win_s)//3
            if aa_len < (min_flank*2):
                continue

        segments = map_window(win_s, win_e)
        if not segments:
            continue

        nt = extract_sequence_from_indexed_genome(genome_index, chrom, segments, strand)
        if not nt:
            continue

        seq_for = pad_to_codon(nt) if pad else trim_to_codon(nt)
        prot = str(Seq(seq_for).translate(to_stop=False))
        if "*" in prot:
            prot = prot.split("*")[0]
        if len(prot) < (min_flank*2):
            continue

        coords = ";".join(f"{s}-{e}" for s,e in segments)
        header = (
            f"{prot_id}|var={var_name}|gene_id={tx_model['gene_id']}"
            f"|tx={tx_model['transcript_id']}|gene_symbol={tx_model['gene_name']}"
            f"|event={event_type}|junction_nt={j_nt}|window_nt={win_s}-{win_e-1}"
            f"|coords={coords}|pep_len={len(prot)}|flank_aa={max_flank}"
        )
        peptides.append(SeqRecord(Seq(prot), id=header, description=""))

    return peptides

# --------------------------- EVENT PROCESSING ---------------------------
def process_event_file(event_type, p: Path, transcripts, fa_index, args, prot_info, junction_recs):
    df = pd.read_csv(p, sep="\t", header=0, dtype=str)

    for rowd in tqdm(df.to_dict(orient='records'), total=len(df), desc=p.name):
        if not isinstance(rowd, dict):
            continue
        event_id = (rowd.get("event_id") or rowd.get("event") or "")
        parsed = parse_suppa_event_coords(event_id)
        alt_txs = split_list_field(rowd.get("alternative_transcripts"))
        total_txs = split_list_field(rowd.get("total_transcripts"))
        ref_txs = [t for t in total_txs if t not in alt_txs]

        alt_merged = merge_intervals(
            [ex for t in alt_txs for ex in (transcripts[match_transcript_id(t, transcripts)]["exons"]
                 if match_transcript_id(t, transcripts) else [])]
        )
        ref_merged = merge_intervals(
            [ex for t in ref_txs for ex in (transcripts[match_transcript_id(t, transcripts)]["exons"]
                 if match_transcript_id(t, transcripts) else [])]
        )

        for tx in set(alt_txs + ref_txs):
            m = match_transcript_id(tx, transcripts)
            if not m:
                continue
            txm = transcripts[m]
            exon_chain = txm["exons"]
            cds_list = txm["cds"]

            chains = build_variant_chains_for_transcript(
                (parsed["etype"] if parsed else None),
                rowd,
                exon_chain,
                parsed_coords=parsed,
                alt_merged=alt_merged,
                ref_merged=ref_merged,
            )

            for label, chain in chains.items():
                cds_intervals = intersect_chain_with_cds(chain, cds_list)
                if not cds_intervals:
                    continue

                first_ov = first_overlap_in_cds_order(cds_intervals, txm["strand"])
                upstream_nt = compute_upstream_cds_nt(cds_list, first_ov, txm["strand"])
                extract_segments = [(s,e) for (s,e,f) in cds_intervals]
                seq_nt = extract_sequence_from_indexed_genome(fa_index, txm["chrom"], extract_segments, txm["strand"])
                if not seq_nt:
                    continue

                trim = upstream_nt % 3
                trimmed = False
                if trim and len(seq_nt) > trim:
                    seq_nt_trim = seq_nt[trim:]
                    trimmed = True
                else:
                    seq_nt_trim = seq_nt

                pad_flag = args.pad_partial_codons
                pref = args.prefer_annotated_start
                mode = args.translation_mode

                prot = None
                if pref:
                    if txm["strand"] == "+":
                        canonical = min(x[0] for x in cds_list) if cds_list else None
                    else:
                        canonical = max(x[1] for x in cds_list) if cds_list else None
                    if canonical is not None:
                        canonical_up = compute_upstream_cds_nt(cds_list, canonical, txm["strand"])
                        offset = canonical_up - upstream_nt
                        if 0 <= offset < len(seq_nt_trim):
                            prot = translate_from_position(seq_nt_trim[offset:], pad=pad_flag)

                if not prot:
                    if mode == "first_atg":
                        prot = translate_from_first_atg_or_longest_orf(seq_nt_trim, pad=pad_flag)
                    else:
                        prot = translate_longest_orf_only(seq_nt_trim, pad=pad_flag)

                if not prot:
                    continue

                coords_used = ";".join(f"{s}-{e}" for s,e in extract_segments)
                header_meta = {
                    "gene_id": txm["gene_id"],
                    "tx": txm["transcript_id"],
                    "gene_symbol": txm["gene_name"],
                    "event": (parsed["etype"] if parsed else event_type),
                    "variant": label,
                    "coords": coords_used,
                    "first_overlap": str(first_ov),
                    "trim": str(trim),
                    "trimmed": str(trimmed),
                    "pad_partial_codons": str(pad_flag),
                    "translation_mode": mode,
                }
                if prot not in prot_info:
                    prot_info[prot] = (
                        header_meta["gene_id"],
                        header_meta["gene_symbol"],
                        header_meta["tx"],
                        header_meta.get("event"),
                    )

                if args.short_junction_peptides:
                    prot_id = f"{txm['transcript_id']}|{label}"
                    jrecs = generate_codon_aware_junction_peptides(
                        cds_segments=cds_intervals,
                        tx_model=txm,
                        genome_index=fa_index,
                        prot_id=prot_id,
                        var_name=label,
                        event_type=(parsed["etype"] if parsed else event_type),
                        max_flank=args.junction_max_flank,
                        min_flank=args.junction_min_flank,
                        pad=pad_flag,
                    )
                    junction_recs.extend(jrecs)

# --------------------------- FASTA WRITERS ---------------------------
def write_protein_fasta(prot_info, out_path):
    seq_records = []
    i = 1
    for prot, (gid, gname, tid, event) in prot_info.items():
        event = event if event is not None else 'NA'
        seq_id = f"SUPPA_seq_{i}|gene_id={gid}|gene_symbol={gname}|tx={tid}|event={event}|len={len(prot)}"
        seq_records.append(SeqRecord(Seq(prot), id=seq_id, description=""))
        i += 1
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
    ap = argparse.ArgumentParser(description="SUPPA → protein FASTA + codon-aware junction peptides")
    ap.add_argument("--gtf_db", help="gffutils DB created from GTF (optional)")
    ap.add_argument("--gtf", help="GTF file to build gffutils DB if --gtf_db not provided")
    ap.add_argument("--genome", "--genome-fasta", dest="genome", required=True, help="Genome FASTA (indexed by pyfaidx). Alias: --genome")
    ap.add_argument("--event_files", nargs="+", required=True, help="SUPPA event .ioe or .txt files")
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
    """Run processing given parsed `args` (keeps CLI parsing in `main`)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    logging.info("Loading genome via pyfaidx: %s", args.genome)
    fa_index = open_genome_index(args.genome)

    logging.info("Loading GTF DB or building from GTF if needed")
    transcripts = build_transcript_models(args.gtf, args.gtf_db)

    prot_info = {}
    junction_recs = []

    for p in args.event_files:
        pth = Path(p)
        event_type = pth.stem
        process_event_file(event_type, pth, transcripts, fa_index, args, prot_info, junction_recs)

    write_protein_fasta(prot_info, args.out_prot_fa)

    if args.short_junction_peptides:
        write_junction_fasta(junction_recs, args.out_junc_fa)

if __name__ == "__main__":
    main()