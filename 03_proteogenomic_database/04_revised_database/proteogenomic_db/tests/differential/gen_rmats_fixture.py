"""Synthetic genome + GTF + rMATS tables (SE, A3SS, A5SS, MXE, RI) for differential testing.

Coding sequences are built codon by codon (ATG ... stop, no internal stops) so the
annotated proteins are valid; event boundaries are randomly shifted so altered
isoforms cover in-frame, frameshift, premature-stop, NMD and retained-intron cases.
"""
import random
import sys
from pathlib import Path

BASES = "ACGT"
STOPS = {"TAA", "TAG", "TGA"}
SENSE = [a + b + c for a in BASES for b in BASES for c in BASES if a + b + c not in STOPS]
COMP = str.maketrans("ACGTN", "TGCAN")


def revcomp(s):
    return s.translate(COMP)[::-1]


def main(out, seed):
    rnd = random.Random(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    chroms = {"chr1": list(rnd.choice(BASES) for _ in range(160000)),
              "chrM": list(rnd.choice(BASES) for _ in range(8000))}
    gtf, proteins = [], {}
    events = {k: [] for k in ("SE", "A3SS", "A5SS", "MXE", "RI")}
    pos = {"chr1": 1000, "chrM": 200}
    gene_specs = [("chr1", i) for i in range(40)] + [("chrM", 40)]
    for chrom, g in gene_specs:
        strand = rnd.choice("+-")
        n_exons = rnd.randint(4, 7)
        exons, cur = [], pos[chrom]
        for _ in range(n_exons):
            length = rnd.randint(45, 180)
            exons.append([cur, cur + length - 1])
            cur += length + rnd.randint(90, 400)
        pos[chrom] = cur + 500
        # CDS: starts inside first exon (transcript order), ends inside last exon.
        order = exons if strand == "+" else exons[::-1]
        first_len = order[0][1] - order[0][0] + 1
        utr5 = first_len + rnd.randint(3, 20) if rnd.random() < 0.3 else rnd.randint(3, 20)
        utr3 = rnd.randint(3, 20)
        tx_len = sum(e - s + 1 for s, e in exons)
        cds_len = (tx_len - utr5 - utr3) // 3 * 3
        codons = ["ATG"] + [rnd.choice(SENSE) for _ in range(cds_len // 3 - 2)] + [rnd.choice(sorted(STOPS))]
        cds_seq = "".join(codons)
        tx_seq = "".join(rnd.choice(BASES) for _ in range(utr5)) + cds_seq
        tx_seq += "".join(rnd.choice(BASES) for _ in range(tx_len - len(tx_seq)))
        # Lay the transcript sequence onto the genome in transcript order.
        offset = 0
        cds_parts = []
        for s, e in order:
            length = e - s + 1
            piece = tx_seq[offset:offset + length]
            genomic = piece if strand == "+" else revcomp(piece)
            chroms[chrom][s - 1:e] = list(genomic)
            lo, hi = max(offset, utr5), min(offset + length, utr5 + cds_len)
            if lo < hi:
                if strand == "+":
                    cds_parts.append((s + lo - offset, s + hi - offset - 1, lo - utr5))
                else:
                    cds_parts.append((e - (hi - offset) + 1, e - (lo - offset), lo - utr5))
            offset += length
        for (s1, e1), (s2, e2) in zip(exons, exons[1:]):
            if rnd.random() < 0.15 and s2 - e1 > 20:
                n_at = rnd.randint(e1 + 3, s2 - 8)
                chroms[chrom][n_at - 1:n_at + 2] = list("NNN")
        gid, tid = f"ENSG{g:011d}", f"ENST{g:011d}"
        attrs = f'gene_id "{gid}"; gene_name "GENE{g}"; gene_type "protein_coding";'
        tattrs = attrs + f' transcript_id "{tid}"; transcript_type "protein_coding";'
        gtf.append((chrom, "gene", exons[0][0], exons[-1][1], strand, ".", attrs))
        gtf.append((chrom, "transcript", exons[0][0], exons[-1][1], strand, ".", tattrs))
        for s, e in exons:
            gtf.append((chrom, "exon", s, e, strand, ".", tattrs))
        corrupt = rnd.random() < 0.1
        for k, (s, e, done) in enumerate(cds_parts):
            phase = (3 - done % 3) % 3
            if corrupt and k == len(cds_parts) // 2:
                phase = (phase + 1) % 3
            gtf.append((chrom, "CDS", s, e, strand, str(phase), tattrs))
        proteins[tid] = cds_seq
        # A second, exon-skipping isoform for some genes (transcript ambiguity).
        if n_exons >= 5 and rnd.random() < 0.4:
            tid2 = f"ENST{g:011d}".replace("ENST", "ENSTB")
            t2 = attrs + f' transcript_id "{tid2}"; transcript_type "protein_coding";'
            keep = [x for i, x in enumerate(exons) if i != 2]
            gtf.append((chrom, "transcript", keep[0][0], keep[-1][1], strand, ".", t2))
            for s, e in keep:
                gtf.append((chrom, "exon", s, e, strand, ".", t2))
            skip_lo, skip_hi = exons[2]
            alt_tx = "".join(tx_seq[o:o + (e - s + 1)] for o, (s, e) in zip(
                [sum(ee - ss + 1 for ss, ee in order[:j]) for j in range(len(order))], order)
                if (s, e) != (skip_lo, skip_hi))
            proteins[tid2] = alt_tx[utr5:]  # transcript orientation; translated to the first stop
            for s, e, done in cds_parts:
                if (s, e) != tuple(exons[2]) and not (exons[2][0] <= s <= exons[2][1]):
                    gtf.append((chrom, "CDS", s, e, strand, str((3 - done % 3) % 3), t2))

        def counts():
            a, b = rnd.randint(0, 30), rnd.randint(0, 30)
            return [f"{a},{rnd.randint(0, 30)}", f"{b},{rnd.randint(0, 30)}",
                    f"{rnd.randint(0, 30)},{rnd.randint(0, 30)}", f"{rnd.randint(0, 30)},{rnd.randint(0, 30)}",
                    "150", "100", f"{rnd.random():.4f}", f"{rnd.random():.4f}",
                    "0.7,0.8", "0.4,0.5", f"{rnd.uniform(-0.5, 0.5):.3f}"]
        head = [gid, f"GENE{g}", chrom, strand]
        for i in range(1, n_exons - 1):
            up, ex, dn = exons[i - 1], exons[i], exons[i + 1]
            events["SE"].append(head + [ex[0] - 1, ex[1], up[0] - 1, up[1], dn[0] - 1, dn[1]] + counts())
            events["RI"].append(head + [up[0] - 1, ex[1], up[0] - 1, up[1], ex[0] - 1, ex[1]] + counts())
            d = rnd.choice([3, 6, 7, 10, 12, 20])
            if ex[1] - ex[0] > d + 10:
                # Alternative boundary on the exon's 3' (genomic end) or 5' side.
                long_e, short_e = [ex[0], ex[1]], [ex[0], ex[1] - d]
                flank = dn
                kind_end = "A5SS" if strand == "+" else "A3SS"
                events[kind_end].append(head + [long_e[0] - 1, long_e[1], short_e[0] - 1, short_e[1], flank[0] - 1, flank[1]] + counts())
                long_s, short_s = [ex[0], ex[1]], [ex[0] + d, ex[1]]
                kind_start = "A3SS" if strand == "+" else "A5SS"
                events[kind_start].append(head + [long_s[0] - 1, long_s[1], short_s[0] - 1, short_s[1], up[0] - 1, up[1]] + counts())
            if i + 2 < n_exons:
                x1, x2, dn2 = exons[i], exons[i + 1], exons[i + 2]
                events["MXE"].append(head + [x1[0] - 1, x1[1], x2[0] - 1, x2[1], up[0] - 1, up[1], dn2[0] - 1, dn2[1]] + counts())

    with (out / "genome.fa").open("w") as handle:
        for chrom, seq in chroms.items():
            handle.write(f">{chrom}\n")
            s = "".join(seq)
            for i in range(0, len(s), 60):
                handle.write(s[i:i + 60] + "\n")
    with (out / "annotation.gtf").open("w") as handle:
        for chrom, feat, s, e, strand, phase, attrs in gtf:
            handle.write(f"{chrom}\tsynthetic\t{feat}\t{s}\t{e}\t.\t{strand}\t{phase}\t{attrs}\n")
    from Bio.Seq import Seq
    with (out / "reference.fa").open("w") as handle:
        for i, (tid, cds) in enumerate(sorted(proteins.items())):
            if i % 3 == 0 and not tid.startswith("ENSTB"):
                continue  # leave some proteins out so unique-peptide checks vary
            table = 2 if "00000000040" in tid else 1
            cds = cds[:len(cds) // 3 * 3]
            protein = str(Seq(cds).translate(table=table, to_stop=True))
            if protein:
                handle.write(f">sp|P{i:05d}|{tid}\n{protein}\n")
    counts_head = ["IJC_SAMPLE_1", "SJC_SAMPLE_1", "IJC_SAMPLE_2", "SJC_SAMPLE_2", "IncFormLen",
                   "SkipFormLen", "PValue", "FDR", "IncLevel1", "IncLevel2", "IncLevelDifference"]
    base = ["ID", "GeneID", "geneSymbol", "chr", "strand"]
    cols = {
        "SE": ["exonStart_0base", "exonEnd", "upstreamES", "upstreamEE", "downstreamES", "downstreamEE"],
        "RI": ["riExonStart_0base", "riExonEnd", "upstreamES", "upstreamEE", "downstreamES", "downstreamEE"],
        "A3SS": ["longExonStart_0base", "longExonEnd", "shortES", "shortEE", "flankingES", "flankingEE"],
        "A5SS": ["longExonStart_0base", "longExonEnd", "shortES", "shortEE", "flankingES", "flankingEE"],
        "MXE": ["1stExonStart_0base", "1stExonEnd", "2ndExonStart_0base", "2ndExonEnd",
                "upstreamES", "upstreamEE", "downstreamES", "downstreamEE"],
    }
    for kind, rows in events.items():
        comparison = out / "CASE-CTRL"
        comparison.mkdir(exist_ok=True)
        with (comparison / f"{kind}.MATS.JC.txt").open("w") as handle:
            handle.write("\t".join(base + cols[kind] + counts_head) + "\n")
            for n, row in enumerate(rows, 1):
                handle.write("\t".join(map(str, [n] + row)) + "\n")
    print({k: len(v) for k, v in events.items()})


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
