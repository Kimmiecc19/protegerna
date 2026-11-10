#!/usr/bin/env python3
"""
check_custom_only_peptides.py - which V5 peptides are absent from every reference sequence set (Chapter 5).

A V5 peptide is "custom-only" if every protein id it maps to in the V5 search is a splice- or fusion-derived
entry (rmats, suppa, fusioninspector in v5_id_source.tsv). Each custom-only peptide from Batches 1-6
(rows passing all four 1% q-value filters, i.e. the *.pass.tsv.gz tables) is then searched, with isoleucine
and leucine treated as identical, as a substring of:
  REFDB    the reference-only search database (human_reference_deduplicated.fasta; Swiss-Prot with isoforms + cRAP)
  UNIPROT  UniProt UP000005640 canonical (UP000005640_9606.fasta.gz) and additional sequences
           (UP000005640_9606_additional.fasta.gz: Swiss-Prot isoforms and unreviewed TrEMBL entries)
  GENCODE  GENCODE v46 protein-coding translations (gencode.v46.pc_translations.fa.gz)
and against the peptides identified in any of the six reference-only searches.

A peptide absent from REFDB, UNIPROT and GENCODE is a novel candidate (the definition shared by Chapters 5 and 6).

Usage: python check_custom_only_peptides.py SIX_BATCH_DIR REFDB UNIPROT_CANONICAL UNIPROT_ADDITIONAL GENCODE OUT.tsv
"""
import sys, os, re, gzip
import pandas as pd

# The "six-batch" folder may hold the 01a/01b/01c outputs side by side, or be this step's folder,
# where they sit in their own result subfolders. Look in the folder first, then in those subfolders.
SIX_SUBDIRS = ("01a_extract_passing_rows", "01b_make_sequence_source_table",
               "01c_collect_diann_summary_tables", "02d_summarise_fusion_peptides")


def six_path(root, *parts):
    flat = os.path.join(root, *parts)
    if os.path.exists(flat):
        return flat
    for sub in SIX_SUBDIRS:
        candidate = os.path.join(root, sub, *parts)
        if os.path.exists(candidate):
            return candidate
    return flat


D, REFDB, UPC, UPA, GEN, OUT = sys.argv[1:7]
idrx = re.compile(r"PGDB_[UC]\d+")
src = pd.read_csv(six_path(D, "v5_id_source.tsv"), sep="\t", header=None, names=["id", "source", "gene"])
src["custom"] = src.source.str.split(";").map(lambda s: all(x in ("rmats", "suppa", "fusioninspector") for x in s))
CUSTOM = set(src.loc[src.custom, "id"]); SRC = dict(zip(src.id, src.source)); GENE = dict(zip(src.id, src.gene))


def fasta(path):
    op = gzip.open if path.endswith(".gz") else open
    seqs, cur = [], []
    with op(path, "rt") as f:
        for line in f:
            if line.startswith(">"):
                if cur: seqs.append("".join(cur))
                cur = []
            else:
                cur.append(line.strip())
    if cur: seqs.append("".join(cur))
    return "#".join(s.replace("I", "L") for s in seqs)


ref_ident, rows = set(), {}
for b in range(1, 7):
    r = pd.read_csv(six_path(D, f"ref_b{b}.pass.tsv.gz"), sep="\t", header=None, usecols=[2], names=["pep"], dtype=str)
    ref_ident |= {p.replace("I", "L") for p in r.pep.unique()}
    v = pd.read_csv(six_path(D, f"v5_b{b}.pass.tsv.gz"), sep="\t", header=None, usecols=[0, 1, 2],
                    names=["file", "ids", "pep"], dtype=str)
    g = v.groupby("pep").agg(ids=("ids", lambda s: set(idrx.findall(";".join(s)))), files=("file", "nunique"))
    for pep, r_ in g.iterrows():
        if r_.ids and r_.ids <= CUSTOM:
            d = rows.setdefault(pep, dict(peptide=pep, ids=set(), batches={}))
            d["ids"] |= r_.ids; d["batches"][b] = int(r_.files)

refdb, upc, upa, gen = fasta(REFDB), fasta(UPC), fasta(UPA), fasta(GEN)
out = []
for pep, d in rows.items():
    q = pep.replace("I", "L")
    out.append(dict(peptide=pep, length=len(pep),
                    sources=";".join(sorted({x for i in d["ids"] for x in SRC[i].split(";")})),
                    genes=";".join(sorted({str(GENE[i]) for i in d["ids"]})),
                    batches=";".join(f"B{b}:{n}" for b, n in sorted(d["batches"].items())),
                    n_batches=len(d["batches"]),
                    identified_in_reference_search=q in ref_ident,
                    in_reference_db=q in refdb, in_uniprot_canonical=q in upc, in_uniprot_additional=q in upa,
                    in_gencode_v46=q in gen))
o = pd.DataFrame(out)
o["novel"] = ~(o.in_reference_db | o.in_uniprot_canonical | o.in_uniprot_additional | o.in_gencode_v46)
o["novel_ch5_rule_without_gencode"] = ~(o.in_reference_db | o.in_uniprot_canonical | o.in_uniprot_additional)
o = o.sort_values(["novel", "n_batches"], ascending=[False, False])
o.to_csv(OUT, sep="\t", index=False)
print(len(o), "custom-only peptides in Batches 1-6;", int(o.novel.sum()), "novel;",
      int(o.novel_ch5_rule_without_gencode.sum()), "absent from the reference DB and UniProt;",
      int((o.novel_ch5_rule_without_gencode & o.in_gencode_v46).sum()), "of those found in GENCODE v46")
print(o[o.novel_ch5_rule_without_gencode | o.peptide.isin(["SPSVAAMASPQLCR", "DNEESQAAPR", "SRSPESQVIGENTK",
      "LPASPGPGPGTMSEK", "EQMYNILMWIHDNYSR"])].drop(columns=["sources"]).to_string(index=False))
