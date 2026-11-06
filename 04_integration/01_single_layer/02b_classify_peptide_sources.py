#!/usr/bin/env python3
"""
06_peptide_source_classification.py  -  Objective 3 / 4, proteogenomic evidence

Classifies every DIA-NN precursor identified with the v5 proteogenomic database:

  1. which database sources explain it (UniProt reference, SUPPA, rMATS, FusionInspector,
     cRAP) using the v5 proteogenomic_mapping.tsv;
  2. for precursors explained ONLY by non-reference entries ("variant-only"), whether the
     peptide is a known isoform (UniProt canonical + isoform FASTA), annotated in GENCODE
     protein translations but absent from UniProt, or not found in either (novel candidate).
     I and L are treated as identical (indistinguishable by mass).

Inputs
  --pr-matrix     one or more diann_report.pr_matrix.tsv files (one per batch; v5 searches only)
  --batch-names   matching names (e.g. batch4 batch5 batch6)
  --mapping       v5 proteogenomic_mapping.tsv
  --uniprot       UniProt canonical FASTA and the *_additional (isoform) FASTA (.fa or .gz)
  --gencode       gencode.v46.pc_translations.fa (.fa or .gz)
  --exclude-runs-regex  runs to ignore (default: the technical control line CTRL-NEUEU392AE8)
  --outdir        new folder

Outputs
  precursor_sources.tsv          every precursor: batch, source category, runs detected
  variant_only_peptides.tsv      one row per variant-only peptide: sources, genes, class,
                                 batches, runs/participants detected (out of total)
  summary.json                   counts per batch and combined (precursors, peptides,
                                 intensity share), class breakdown
"""
import argparse, gzip, json, os, re, sys
import pandas as pd

CTRL_LINE = r"CTRL-NEUEU392AE8"


def read_fasta_seqs(paths):
    seqs = []
    for p in paths:
        op = gzip.open if p.endswith(".gz") else open
        buf = []
        with op(p, "rt") as fh:
            for line in fh:
                if line.startswith(">"):
                    if buf: seqs.append("".join(buf)); buf = []
                else:
                    buf.append(line.strip())
        if buf: seqs.append("".join(buf))
    return seqs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pr-matrix", nargs="+", required=True)
    ap.add_argument("--batch-names", nargs="+", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--uniprot", nargs="+", required=True)
    ap.add_argument("--gencode", required=True)
    ap.add_argument("--exclude-runs-regex", default=CTRL_LINE)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    if len(a.pr_matrix) != len(a.batch_names): sys.exit("--pr-matrix and --batch-names differ in length")
    if os.path.exists(a.outdir): sys.exit(f"Output folder exists: {a.outdir}")
    os.makedirs(a.outdir)
    out = lambda f: os.path.join(a.outdir, f)

    m = pd.read_csv(a.mapping, sep="\t", dtype=str, usecols=["sequence_id", "source", "gene_symbols"])
    src = m.groupby("sequence_id").source.apply(set).to_dict()
    gsym = m.dropna(subset=["gene_symbols"]).groupby("sequence_id").gene_symbols.apply(lambda x: set(";".join(x).split(";"))).to_dict()
    def genes_from_ids(ids):   # fallback when DIA-NN did not annotate genes (batch 4 library had 0 genes)
        g = set()
        for i in str(ids).split(";"):
            g |= gsym.get(i.split("|")[1] if "|" in i else i, set())
        return ";".join(sorted(g - {"", "NA"}))

    rx_part = re.compile(r"(CASE|CTRL)-NEU[A-Z0-9]+")
    frames, per_batch = [], {}
    for path, b in zip(a.pr_matrix, a.batch_names):
        d = pd.read_csv(path, sep="\t", low_memory=False)
        runs = [c for c in d.columns if c.endswith("mzML") and not re.search(a.exclude_runs_regex, c)]
        q = d[runs].apply(pd.to_numeric, errors="coerce")
        def cat(ids):
            S = set()
            for i in str(ids).split(";"):
                pid = i.split("|")[1] if "|" in i else i
                S |= src.get(pid, {"UNKNOWN"})
            if S & {"reference", "crap"}: return "reference-explained", S
            if "UNKNOWN" in S: return "unknown_id", S
            return "variant-only", S
        cs = d["Protein.Ids"].map(cat)
        x = pd.DataFrame({
            "batch": b, "Precursor.Id": d["Precursor.Id"], "Stripped.Sequence": d["Stripped.Sequence"],
            "Protein.Ids": d["Protein.Ids"],
            "Genes": [g.replace("GN=", "") if isinstance(g, str) and g.strip() else genes_from_ids(i) for g, i in
                      zip(d["Genes"] if "Genes" in d else [""] * len(d), d["Protein.Ids"])],
            "category": cs.map(lambda t: t[0]), "sources": cs.map(lambda t: "+".join(sorted(t[1] - {"crap"})) or "crap"),
            "n_runs_detected": q.notna().sum(axis=1), "n_runs_total": len(runs), "total_intensity": q.sum(axis=1)})
        x["participants_detected"] = [";".join(sorted({rx_part.search(r).group(0) for r, v in zip(runs, row) if pd.notna(v) and rx_part.search(r)}))
                                      for row in q.itertuples(index=False)]
        per_batch[b] = dict(runs=len(runs))
        frames.append(x)
    pr = pd.concat(frames, ignore_index=True)
    pr.drop(columns=["participants_detected"]).to_csv(out("precursor_sources.tsv"), sep="\t", index=False)

    # ---- classify variant-only peptides against UniProt (+isoforms) and GENCODE
    L = lambda s: s.replace("I", "L")
    uni = "#".join(L(s) for s in read_fasta_seqs(a.uniprot))
    gen = "#".join(L(s) for s in read_fasta_seqs([a.gencode]))
    v = pr[pr.category == "variant-only"]
    pep_rows = []
    for pep, g in v.groupby("Stripped.Sequence"):
        in_u, in_g = L(pep) in uni, L(pep) in gen
        parts = set(";".join(g.participants_detected).split(";")) - {""}
        pep_rows.append(dict(
            peptide=pep, genes=";".join(sorted(set(g.Genes) - {""})), sources=";".join(sorted(set(g.sources))),
            peptide_class="known UniProt isoform" if in_u else ("GENCODE-annotated, not in UniProt" if in_g else "novel candidate (not in UniProt or GENCODE)"),
            batches=";".join(sorted(set(g.batch))), n_precursors=len(g),
            max_runs_detected=int(g.n_runs_detected.max()), runs_total_in_batch=int(g.n_runs_total.max()),
            max_fraction_runs_detected=round(float((g.n_runs_detected / g.n_runs_total).max()), 3),
            n_participants_detected=len(parts), participants=";".join(sorted(parts))))
    peps = pd.DataFrame(pep_rows).sort_values(["peptide_class", "n_participants_detected"], ascending=[False, False]) if pep_rows else pd.DataFrame()
    peps.to_csv(out("variant_only_peptides.tsv"), sep="\t", index=False)

    # ---- summaries
    def summarise(df):
        tot_i = df.total_intensity.sum()
        return dict(precursors=int(len(df)), peptides=int(df["Stripped.Sequence"].nunique()),
                    precursors_by_category={k: int(n) for k, n in df.category.value_counts().items()},
                    intensity_share_pct={k: round(100 * float(i) / float(tot_i), 3) for k, i in df.groupby("category").total_intensity.sum().items()},
                    variant_only_by_sources={k: int(n) for k, n in df[df.category == "variant-only"].sources.value_counts().items()})
    summ = {b: dict(per_batch[b], **summarise(pr[pr.batch == b])) for b in a.batch_names}
    summ["combined"] = summarise(pr)
    summ["combined"]["variant_only_unique_peptides"] = int(len(peps))
    if len(peps):
        summ["combined"]["peptide_class"] = {k: int(n) for k, n in peps.peptide_class.value_counts().items()}
        summ["combined"]["variant_peptides_detected_in_>=50pct_of_runs_of_a_batch"] = int((peps.max_fraction_runs_detected >= 0.5).sum())
        summ["combined"]["genes_with_variant_only_peptides"] = int(len({x.replace("GN=", "") for x in ";".join(peps.genes).split(";")} - {""}))
    json.dump(summ, open(out("summary.json"), "w"), indent=2)
    print(json.dumps(summ["combined"], indent=2))


if __name__ == "__main__":
    main()
