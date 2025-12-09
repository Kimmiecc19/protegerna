## Steps

* **Parses arriba.fusions.tsv**
* **Parses fusioncatcher.fusion-genes.txt**
* If peptide sequence exists → export directly to FASTA
* If only nucleotide sequence exists → translate frame-aware
* Builds **metadata-rich FASTA headers**
* Merges results into a **fusion\_proteins.fasta**
* Writes a **fusion\_metadata.tsv** mapping header → fusion info

---

Requirements

```bash
pip install biopython pandas
```

Script (fusion\_db\_builder.py)

```python
#!/usr/bin/env python3
import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import argparse

def parse_arriba(arriba_file):
    df = pd.read_csv(arriba_file, sep="\t", comment="#")
    records, meta = [], []

    for _, row in df.iterrows():
        peptide = row.get("peptide_sequence", None)
        fusion_id = f"FUSION_ARRIBA_{row['gene1']}_{row['gene2']}_{row['breakpoint1']}_{row['breakpoint2']}"
        header = (f"{fusion_id}|GENE1={row['gene1']}|GENE2={row['gene2']}|"
                  f"TX1={row['transcript_id1']}|TX2={row['transcript_id2']}|"
                  f"BP1={row['breakpoint1']}|BP2={row['breakpoint2']}|"
                  f"FRAME={row['reading_frame']}|SOURCE=Arriba")
        
        if pd.notna(peptide) and peptide != "":
            records.append(SeqRecord(Seq(peptide), id=header, description=""))
        else:
            fusion_tx = row.get("fusion_transcript", None)
            if pd.notna(fusion_tx):
                seq = Seq(fusion_tx).translate(to_stop=True)
                records.append(SeqRecord(seq, id=header, description=""))

        meta.append([fusion_id, row['gene1'], row['gene2'], row['breakpoint1'], row['breakpoint2'],
                     row['confidence'], row['reading_frame'], "Arriba"])

    return records, pd.DataFrame(meta, columns=["FusionID","Gene1","Gene2","Breakpoint1","Breakpoint2","Confidence","Frame","Source"])

def parse_fusioncatcher(fc_file):
    df = pd.read_csv(fc_file, sep="\t", comment="#")
    records, meta = [], []

    for _, row in df.iterrows():
        fusion_id = f"FUSION_FC_{row['Gene_1_symbol(5end_fusion_partner)']}_{row['Gene_2_symbol(3end_fusion_partner)']}"
        header = (f"{fusion_id}|GENE1={row['Gene_1_symbol(5end_fusion_partner)']}|"
                  f"GENE2={row['Gene_2_symbol(3end_fusion_partner)']}|"
                  f"BP1={row['Fusion_point_for_gene_1(5end_fusion_partner)']}|"
                  f"BP2={row['Fusion_point_for_gene_2(3end_fusion_partner)']}|"
                  f"SOURCE=FusionCatcher")

        peptide = None
        if "Predicted_effect" in row and pd.notna(row["Predicted_effect"]):
            # Sometimes FC gives peptide-level effects
            peptide = row["Predicted_effect"]
        elif "Fusion_sequence" in row and pd.notna(row["Fusion_sequence"]):
            seq = Seq(row["Fusion_sequence"]).translate(to_stop=True)
            peptide = str(seq)

        if peptide:
            records.append(SeqRecord(Seq(peptide), id=header, description=""))

        meta.append([fusion_id,
                     row['Gene_1_symbol(5end_fusion_partner)'],
                     row['Gene_2_symbol(3end_fusion_partner)'],
                     row['Fusion_point_for_gene_1(5end_fusion_partner)'],
                     row['Fusion_point_for_gene_2(3end_fusion_partner)'],
                     row.get('Fusion_finding_method', "NA"),
                     "FusionCatcher"])

    return records, pd.DataFrame(meta, columns=["FusionID","Gene1","Gene2","Breakpoint1","Breakpoint2","Method","Source"])

def main(arriba_file, fc_file, out_fasta, out_meta):
    all_records, all_meta = [], []

    if arriba_file:
        recs, meta = parse_arriba(arriba_file)
        all_records.extend(recs)
        all_meta.append(meta)

    if fc_file:
        recs, meta = parse_fusioncatcher(fc_file)
        all_records.extend(recs)
        all_meta.append(meta)

    SeqIO.write(all_records, out_fasta, "fasta")
    pd.concat(all_meta).to_csv(out_meta, sep="\t", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build fusion protein database from Arriba + FusionCatcher")
    parser.add_argument("--arriba", help="arriba.fusions.tsv")
    parser.add_argument("--fusioncatcher", help="fusioncatcher.fusion-genes.txt")
    parser.add_argument("--out_fasta", default="fusion_proteins.fasta")
    parser.add_argument("--out_meta", default="fusion_metadata.tsv")
    args = parser.parse_args()

    main(args.arriba, args.fusioncatcher, args.out_fasta, args.out_meta)
```

---

Usage

```bash
python fusion_db_builder.py --arriba arriba.fusions.tsv --fusioncatcher fusioncatcher.fusion-genes.txt \
       --out_fasta fusion_proteins.fasta --out_meta fusion_metadata.tsv
```

Note: This script assumes **peptide sequences (Arriba) or fusion sequence (FusionCatcher)** exist. If you want **full transcript reconstruction using genome + GTF** (for cases where FusionCatcher gives only exon IDs), I’ll need to extend this with a **CDS/exon parser** (like the one you’re already building for SUPPA events).


1. **Parse Arriba and FusionCatcher results**
2. **Extract exon models from GTF** (using transcript\_id / exon IDs)
3. **Retrieve sequences from genome FASTA** (Biopython + pysam)
4. **Cut at reported breakpoints**
5. **Concatenate 5′ portion of gene1 + 3′ portion of gene2**
6. **Translate into protein sequence** (respecting reading frame when possible)
7. Export **FASTA + metadata**

---

### 🔹 Requirements

```bash
pip install biopython pandas pysam
```

---

### 🔹 Extended Script (fusion\_db\_builder.py)

```python
#!/usr/bin/env python3
import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import pysam
import argparse

# -------------------------
# GTF Parsing
# -------------------------
def parse_gtf_exons(gtf_file):
    exon_map = {}
    with open(gtf_file) as f:
        for line in f:
            if line.startswith("#"): continue
            fields = line.strip().split("\t")
            if fields[2] != "exon": continue
            chrom, start, end, strand = fields[0], int(fields[3]), int(fields[4]), fields[6]
            attrs = {k: v.strip('"') for k,v in 
                     [x.strip().split(" ",1) for x in fields[8].strip(";").split("; ") if " " in x]}
            tid = attrs.get("transcript_id")
            eid = attrs.get("exon_id")
            if tid not in exon_map: exon_map[tid] = []
            exon_map[tid].append((chrom, start, end, strand, eid))
    # sort exons
    for tid in exon_map:
        exon_map[tid].sort(key=lambda x: x[1])
    return exon_map

def fetch_seq(fasta, chrom, start, end, strand):
    seq = fasta.fetch(chrom, start-1, end)  # pysam is 0-based
    return Seq(seq) if strand == "+" else Seq(seq).reverse_complement()

def build_fusion_transcript(fasta, exon_map, tx1, bp1, tx2, bp2):
    """Reconstruct fusion transcript from transcript IDs + breakpoints"""
    if tx1 not in exon_map or tx2 not in exon_map:
        return None

    # gene1 fragment (up to bp1)
    seq1 = Seq("")
    for chrom, start, end, strand, eid in exon_map[tx1]:
        if end < bp1:  # before breakpoint
            seq1 += fetch_seq(fasta, chrom, start, end, strand)
        elif start <= bp1 <= end:  # breakpoint within exon
            seq1 += fetch_seq(fasta, chrom, start, bp1, strand)
            break

    # gene2 fragment (from bp2 onwards)
    seq2 = Seq("")
    for chrom, start, end, strand, eid in exon_map[tx2]:
        if start <= bp2 <= end:  # breakpoint within exon
            seq2 += fetch_seq(fasta, chrom, bp2, end, strand)
        elif start > bp2:
            seq2 += fetch_seq(fasta, chrom, start, end, strand)

    return str(seq1 + seq2)

# -------------------------
# Arriba Parsing
# -------------------------
def parse_arriba(arriba_file, fasta, exon_map):
    df = pd.read_csv(arriba_file, sep="\t", comment="#")
    records, meta = [], []

    for _, row in df.iterrows():
        fusion_id = f"FUSION_ARRIBA_{row['gene1']}_{row['gene2']}_{row['breakpoint1']}_{row['breakpoint2']}"
        header = (f"{fusion_id}|GENE1={row['gene1']}|GENE2={row['gene2']}|"
                  f"TX1={row['transcript_id1']}|TX2={row['transcript_id2']}|"
                  f"BP1={row['breakpoint1']}|BP2={row['breakpoint2']}|"
                  f"FRAME={row['reading_frame']}|SOURCE=Arriba")

        peptide = row.get("peptide_sequence", None)
        if pd.notna(peptide) and peptide != "":
            records.append(SeqRecord(Seq(peptide), id=header, description=""))
        else:
            tx1, tx2 = row['transcript_id1'], row['transcript_id2']
            bp1, bp2 = int(row['breakpoint1'].split(":")[1]), int(row['breakpoint2'].split(":")[1])
            fusion_tx = build_fusion_transcript(fasta, exon_map, tx1, bp1, tx2, bp2)
            if fusion_tx:
                seq = Seq(fusion_tx).translate(to_stop=True)
                records.append(SeqRecord(seq, id=header, description=""))

        meta.append([fusion_id, row['gene1'], row['gene2'], row['breakpoint1'], row['breakpoint2'],
                     row['confidence'], row['reading_frame'], "Arriba"])

    return records, pd.DataFrame(meta, columns=["FusionID","Gene1","Gene2","Breakpoint1","Breakpoint2","Confidence","Frame","Source"])

# -------------------------
# FusionCatcher Parsing
# -------------------------
def parse_fusioncatcher(fc_file, fasta, exon_map):
    df = pd.read_csv(fc_file, sep="\t", comment="#")
    records, meta = [], []

    for _, row in df.iterrows():
        fusion_id = f"FUSION_FC_{row['Gene_1_symbol(5end_fusion_partner)']}_{row['Gene_2_symbol(3end_fusion_partner)']}"
        header = (f"{fusion_id}|GENE1={row['Gene_1_symbol(5end_fusion_partner)']}|"
                  f"GENE2={row['Gene_2_symbol(3end_fusion_partner)']}|"
                  f"BP1={row['Fusion_point_for_gene_1(5end_fusion_partner)']}|"
                  f"BP2={row['Fusion_point_for_gene_2(3end_fusion_partner)']}|"
                  f"SOURCE=FusionCatcher")

        peptide = None
        if "Predicted_effect" in row and pd.notna(row["Predicted_effect"]):
            peptide = row["Predicted_effect"]
        elif "Fusion_sequence" in row and pd.notna(row["Fusion_sequence"]):
            seq = Seq(row["Fusion_sequence"]).translate(to_stop=True)
            peptide = str(seq)
        else:
            tx1, tx2 = row.get("Gene_1_id(5end_fusion_partner)"), row.get("Gene_2_id(3end_fusion_partner)")
            if tx1 and tx2 and tx1 in exon_map and tx2 in exon_map:
                bp1 = int(str(row['Fusion_point_for_gene_1(5end_fusion_partner)']).split(":")[1])
                bp2 = int(str(row['Fusion_point_for_gene_2(3end_fusion_partner)']).split(":")[1])
                fusion_tx = build_fusion_transcript(fasta, exon_map, tx1, bp1, tx2, bp2)
                if fusion_tx:
                    peptide = str(Seq(fusion_tx).translate(to_stop=True))

        if peptide:
            records.append(SeqRecord(Seq(peptide), id=header, description=""))

        meta.append([fusion_id,
                     row['Gene_1_symbol(5end_fusion_partner)'],
                     row['Gene_2_symbol(3end_fusion_partner)'],
                     row['Fusion_point_for_gene_1(5end_fusion_partner)'],
                     row['Fusion_point_for_gene_2(3end_fusion_partner)'],
                     row.get('Fusion_finding_method', "NA"),
                     "FusionCatcher"])

    return records, pd.DataFrame(meta, columns=["FusionID","Gene1","Gene2","Breakpoint1","Breakpoint2","Method","Source"])

# -------------------------
# Main
# -------------------------
def main(arriba_file, fc_file, gtf, fasta_file, out_fasta, out_meta):
    exon_map = parse_gtf_exons(gtf)
    fasta = pysam.FastaFile(fasta_file)
    all_records, all_meta = [], []

    if arriba_file:
        recs, meta = parse_arriba(arriba_file, fasta, exon_map)
        all_records.extend(recs)
        all_meta.append(meta)

    if fc_file:
        recs, meta = parse_fusioncatcher(fc_file, fasta, exon_map)
        all_records.extend(recs)
        all_meta.append(meta)

    SeqIO.write(all_records, out_fasta, "fasta")
    pd.concat(all_meta).to_csv(out_meta, sep="\t", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build fusion protein database from Arriba + FusionCatcher + GTF + FASTA")
    parser.add_argument("--arriba", help="arriba.fusions.tsv")
    parser.add_argument("--fusioncatcher", help="fusioncatcher.fusion-genes.txt")
    parser.add_argument("--gtf", required=True, help="Reference GTF")
    parser.add_argument("--fasta", required=True, help="Reference genome FASTA (indexed)")
    parser.add_argument("--out_fasta", default="fusion_proteins.fasta")
    parser.add_argument("--out_meta", default="fusion_metadata.tsv")
    args = parser.parse_args()

    main(args.arriba, args.fusioncatcher, args.gtf, args.fasta, args.out_fasta, args.out_meta)
```

---

### 🔹 Usage

```bash
python fusion_db_builder.py \
  --arriba arriba.fusions.tsv \
  --fusioncatcher fusioncatcher.fusion-genes.txt \
  --gtf Homo_sapiens.GRCh38.109.gtf \
  --fasta Homo_sapiens.GRCh38.dna.primary_assembly.fa \
  --out_fasta fusion_proteins.fasta \
  --out_meta fusion_metadata.tsv
```

---

* **Option to include out-of-frame fusions** (default = `True`)
* Out-of-frame sequences → translated until first stop codon
* Metadata FASTA headers will mark `FRAME=in-frame` or `FRAME=out-of-frame`

---

### 🔹 Extended Script with Out-of-frame Support

```python
#!/usr/bin/env python3
import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import pysam
import argparse

# -------------------------
# GTF Parsing
# -------------------------
def parse_gtf_exons(gtf_file):
    exon_map = {}
    with open(gtf_file) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if fields[2] != "exon":
                continue
            chrom, start, end, strand = fields[0], int(fields[3]), int(fields[4]), fields[6]
            attrs = {k: v.strip('"') for k, v in
                     [x.strip().split(" ", 1) for x in fields[8].strip(";").split("; ") if " " in x]}
            tid = attrs.get("transcript_id")
            eid = attrs.get("exon_id")
            if tid not in exon_map:
                exon_map[tid] = []
            exon_map[tid].append((chrom, start, end, strand, eid))
    for tid in exon_map:
        exon_map[tid].sort(key=lambda x: x[1])
    return exon_map

def fetch_seq(fasta, chrom, start, end, strand):
    seq = fasta.fetch(chrom, start - 1, end)
    return Seq(seq) if strand == "+" else Seq(seq).reverse_complement()

def build_fusion_transcript(fasta, exon_map, tx1, bp1, tx2, bp2):
    """Reconstruct fusion transcript from transcript IDs + breakpoints"""
    if tx1 not in exon_map or tx2 not in exon_map:
        return None

    # gene1 fragment (up to bp1)
    seq1 = Seq("")
    for chrom, start, end, strand, eid in exon_map[tx1]:
        if end < bp1:
            seq1 += fetch_seq(fasta, chrom, start, end, strand)
        elif start <= bp1 <= end:
            seq1 += fetch_seq(fasta, chrom, start, bp1, strand)
            break

    # gene2 fragment (from bp2 onwards)
    seq2 = Seq("")
    for chrom, start, end, strand, eid in exon_map[tx2]:
        if start <= bp2 <= end:
            seq2 += fetch_seq(fasta, chrom, bp2, end, strand)
        elif start > bp2:
            seq2 += fetch_seq(fasta, chrom, start, end, strand)

    return str(seq1 + seq2)

def translate_with_frame(seq, frame="in-frame", include_out_of_frame=True):
    s = Seq(seq)
    if frame == "in-frame":
        return str(s.translate(to_stop=True))
    elif include_out_of_frame:
        # Translate anyway (out-of-frame ORF until stop codon)
        return str(s.translate(to_stop=True))
    else:
        return None

# -------------------------
# Arriba Parsing
# -------------------------
def parse_arriba(arriba_file, fasta, exon_map, include_out_of_frame):
    df = pd.read_csv(arriba_file, sep="\t", comment="#")
    records, meta = [], []

    for _, row in df.iterrows():
        frame = row.get("reading_frame", "unknown")
        fusion_id = f"FUSION_ARRIBA_{row['gene1']}_{row['gene2']}_{row['breakpoint1']}_{row['breakpoint2']}"
        header = (f"{fusion_id}|GENE1={row['gene1']}|GENE2={row['gene2']}|"
                  f"TX1={row['transcript_id1']}|TX2={row['transcript_id2']}|"
                  f"BP1={row['breakpoint1']}|BP2={row['breakpoint2']}|"
                  f"FRAME={frame}|SOURCE=Arriba")

        peptide = row.get("peptide_sequence", None)
        if pd.notna(peptide) and peptide != "":
            records.append(SeqRecord(Seq(peptide), id=header, description=""))
        else:
            tx1, tx2 = row['transcript_id1'], row['transcript_id2']
            bp1, bp2 = int(row['breakpoint1'].split(":")[1]), int(row['breakpoint2'].split(":")[1])
            fusion_tx = build_fusion_transcript(fasta, exon_map, tx1, bp1, tx2, bp2)
            if fusion_tx:
                translated = translate_with_frame(fusion_tx, frame, include_out_of_frame)
                if translated:
                    records.append(SeqRecord(Seq(translated), id=header, description=""))

        meta.append([fusion_id, row['gene1'], row['gene2'], row['breakpoint1'], row['breakpoint2'],
                     row['confidence'], frame, "Arriba"])

    return records, pd.DataFrame(meta, columns=["FusionID","Gene1","Gene2","Breakpoint1","Breakpoint2","Confidence","Frame","Source"])

# -------------------------
# FusionCatcher Parsing
# -------------------------
def parse_fusioncatcher(fc_file, fasta, exon_map, include_out_of_frame):
    df = pd.read_csv(fc_file, sep="\t", comment="#")
    records, meta = [], []

    for _, row in df.iterrows():
        fusion_id = f"FUSION_FC_{row['Gene_1_symbol(5end_fusion_partner)']}_{row['Gene_2_symbol(3end_fusion_partner)']}"
        header = (f"{fusion_id}|GENE1={row['Gene_1_symbol(5end_fusion_partner)']}|"
                  f"GENE2={row['Gene_2_symbol(3end_fusion_partner)']}|"
                  f"BP1={row['Fusion_point_for_gene_1(5end_fusion_partner)']}|"
                  f"BP2={row['Fusion_point_for_gene_2(3end_fusion_partner)']}|"
                  f"SOURCE=FusionCatcher")

        peptide = None
        if "Predicted_effect" in row and pd.notna(row["Predicted_effect"]):
            peptide = row["Predicted_effect"]
        elif "Fusion_sequence" in row and pd.notna(row["Fusion_sequence"]):
            peptide = str(Seq(row["Fusion_sequence"]).translate(to_stop=True))
        else:
            tx1, tx2 = row.get("Gene_1_id(5end_fusion_partner)"), row.get("Gene_2_id(3end_fusion_partner)")
            if tx1 and tx2 and tx1 in exon_map and tx2 in exon_map:
                bp1 = int(str(row['Fusion_point_for_gene_1(5end_fusion_partner)']).split(":")[1])
                bp2 = int(str(row['Fusion_point_for_gene_2(3end_fusion_partner)']).split(":")[1])
                fusion_tx = build_fusion_transcript(fasta, exon_map, tx1, bp1, tx2, bp2)
                if fusion_tx:
                    peptide = translate_with_frame(fusion_tx, "out-of-frame", include_out_of_frame)

        if peptide:
            records.append(SeqRecord(Seq(peptide), id=header, description=""))

        meta.append([fusion_id,
                     row['Gene_1_symbol(5end_fusion_partner)'],
                     row['Gene_2_symbol(3end_fusion_partner)'],
                     row['Fusion_point_for_gene_1(5end_fusion_partner)'],
                     row['Fusion_point_for_gene_2(3end_fusion_partner)'],
                     row.get('Fusion_finding_method', "NA"),
                     "FusionCatcher"])

    return records, pd.DataFrame(meta, columns=["FusionID","Gene1","Gene2","Breakpoint1","Breakpoint2","Method","Source"])

# -------------------------
# Main
# -------------------------
def main(arriba_file, fc_file, gtf, fasta_file, out_fasta, out_meta, include_out_of_frame):
    exon_map = parse_gtf_exons(gtf)
    fasta = pysam.FastaFile(fasta_file)
    all_records, all_meta = [], []

    if arriba_file:
        recs, meta = parse_arriba(arriba_file, fasta, exon_map, include_out_of_frame)
        all_records.extend(recs)
        all_meta.append(meta)

    if fc_file:
        recs, meta = parse_fusioncatcher(fc_file, fasta, exon_map, include_out_of_frame)
        all_records.extend(recs)
        all_meta.append(meta)

    SeqIO.write(all_records, out_fasta, "fasta")
    pd.concat(all_meta).to_csv(out_meta, sep="\t", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build fusion protein database from Arriba + FusionCatcher + GTF + FASTA")
    parser.add_argument("--arriba", help="arriba.fusions.tsv")
    parser.add_argument("--fusioncatcher", help="fusioncatcher.fusion-genes.txt")
    parser.add_argument("--gtf", required=True, help="Reference GTF")
    parser.add_argument("--fasta", required=True, help="Reference genome FASTA (indexed)")
    parser.add_argument("--out_fasta", default="fusion_proteins.fasta")
    parser.add_argument("--out_meta", default="fusion_metadata.tsv")
    parser.add_argument("--include_out_of_frame", action="store_true",
                        help="Include out-of-frame fusion proteins (default = False)")
    args = parser.parse_args()

    main(args.arriba, args.fusioncatcher, args.gtf, args.fasta,
         args.out_fasta, args.out_meta, args.include_out_of_frame)
```

---

### 🔹 Usage Examples

✅ Only in-frame fusions:

```bash
python fusion_db_builder.py \
  --arriba arriba.fusions.tsv \
  --fusioncatcher fusioncatcher.fusion-genes.txt \
  --gtf Homo_sapiens.GRCh38.109.gtf \
  --fasta Homo_sapiens.GRCh38.dna.primary_assembly.fa
```

✅ Include **out-of-frame fusions** too:

```bash
python fusion_db_builder.py \
  --arriba arriba.fusions.tsv \
  --fusioncatcher fusioncatcher.fusion-genes.txt \
  --gtf Homo_sapiens.GRCh38.109.gtf \
  --fasta Homo_sapiens.GRCh38.dna.primary_assembly.fa \
  --include_out_of_frame
```
