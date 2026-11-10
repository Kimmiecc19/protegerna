#!/usr/bin/env python3
"""
01d_filter_fusions.py  -  Objective 4, fusion evidence

Builds a cohort fusion catalogue from nf-core/rnafusion outputs, applies
pre-declared filters, and tests whether individual fusions (and genes
involved in fusions) are more frequent in ALS than in healthy controls.

Primary evidence = FusionInspector (present for all six batches). Discovery-
caller support (arriba / STAR-Fusion / FusionCatcher) is read from the
fusion-report `*.fusions.csv` files where they exist (batch 4 has none, so
caller support is "unknown" there and the >=2-caller tier is a sensitivity
analysis only). Arriba strand consistency is summarised per sample as a check
that the `strandedness: forward` setting did not affect fusion calling.

Inputs
  --rnafusion-root   folder containing rnafusion_analysis_batch*/fusioninspector
                     and required_outputs_rnafusion_batch*/{fusionreport,arriba}
  --covariates       transcriptomic_batches_covariate_info.csv
                     (participant, sample_id, seq_batch, sex, source, ...)
  --coldata          remove_btc_coldata_filtered.csv (rownames = samples with
                     '_' separators; column 'diagnosis')
  --als-genes        optional text file, one gene symbol per line (added to the
                     built-in list of established ALS genes)
  --outdir           new output folder

Filters (defaults; change only before looking at results and record why)
  F1  FusionInspector JunctionReadCount >= 2
  F2  FFPM >= 0.1
  F3  LargeAnchorSupport == YES
  F4  not annotated as NEIGHBORS (read-through of adjacent genes)
  F5  not in a normal-tissue / artefact list in `annots`
      (GTEx recurrent, BodyMap, *_Normal, DGD_PARALOGS, HGNC_GENEFAM,
       ConjoinG) -> see ARTEFACT_TAGS
  F6  gene pair not seen in any technical-control-line sample
      (CTRL-NEUEU392AE8: BTC/BTC2/BDC_CTRL) - recurrent there = artefact/line
  F7  (sensitivity tier only) >= 2 discovery callers

Test population: one sample per participant, ALS vs Healthy Control only
(BTC/BDC control-line samples, non-ALS MND and asymptomatic carriers excluded).

Outputs
  fusion_calls_all.tsv            every FusionInspector row with filter flags
  fusion_calls_pass.tsv           rows passing F1-F6
  fusion_recurrence_tests.tsv     per gene pair: n ALS / n HC carriers, Fisher, BH
  fusion_gene_tests.tsv           per gene (either partner): same test
  als_gene_fusions.tsv            passing calls involving an ALS gene
  arriba_strand_check.tsv         per-sample arriba gene/fusion strand agreement
  caller_support_summary.tsv      passing calls by number of discovery callers
  sample_manifest.tsv, summary.json
"""
import argparse, csv, glob, json, os, re, sys
import pandas as pd
from scipy.stats import fisher_exact

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from common import bh

ARTEFACT_TAGS = ["GTEx", "BodyMap", "Babiceanu_Normal", "Greger_Normal", "DGD_PARALOGS",
                 "HGNC_GENEFAM", "ConjoinG", "Normal"]
ALS_GENES = {"SOD1", "C9orf72", "TARDBP", "FUS", "TBK1", "OPTN", "VCP", "UBQLN2", "SQSTM1", "PFN1",
             "TUBA4A", "MATR3", "CHCHD10", "KIF5A", "NEK1", "ANXA11", "TIA1", "HNRNPA1", "HNRNPA2B1",
             "ATXN2", "SETX", "ALS2", "VAPB", "ANG", "SPG11", "FIG4", "CHMP2B", "DCTN1", "ERBB4",
             "CCNF", "UNC13A", "STMN2", "C21orf2", "CFAP410", "TAF15", "EWSR1", "SIGMAR1", "GLE1",
             "NEFH", "PRPH", "DAO", "SARM1", "TP73", "SPTLC1", "CAV1", "GLT8D1", "ACSL5", "DNAJC7"}
CONTROL_LINE = "CTRL-NEUEU392AE8"


def sample_from_path(p):
    return os.path.basename(p).split(".")[0].replace("_", "-")


def participant_of(sample):
    m = re.match(r"^((CASE|CTRL)-NEU[A-Z0-9]+)", sample)
    return m.group(1) if m else sample


def read_tsv_hash(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    if not lines:
        return pd.DataFrame()
    header = lines[0].lstrip("#").rstrip("\n").split("\t")
    rows = [l.rstrip("\n").split("\t") for l in lines[1:] if l.strip()]
    rows = [r + [""] * (len(header) - len(r)) for r in rows]
    return pd.DataFrame([r[:len(header)] for r in rows], columns=header)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rnafusion-root", required=True)
    ap.add_argument("--covariates", required=True)
    ap.add_argument("--coldata", required=True)
    ap.add_argument("--als-genes")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--min-junction-reads", type=int, default=2)
    ap.add_argument("--min-ffpm", type=float, default=0.1)
    ap.add_argument("--min-carriers-to-test", type=int, default=3)
    a = ap.parse_args()
    if os.path.exists(a.outdir):
        sys.exit(f"Output folder exists: {a.outdir} (choose a new one)")
    os.makedirs(a.outdir)
    out = lambda f: os.path.join(a.outdir, f)

    # ---------------- metadata ----------------
    cov = pd.read_csv(a.covariates, encoding="utf-8-sig")
    cov["sample"] = cov["sample_id"].str.replace("_", "-")
    col = pd.read_csv(a.coldata, index_col=0)
    col.index = col.index.str.replace("_", "-")
    cov["diagnosis"] = cov["sample"].map(col["diagnosis"])
    cov["participant"] = cov["sample"].map(participant_of)
    cov["is_control_line"] = cov["participant"].eq(CONTROL_LINE) | cov["source"].isin(["BTC", "BTC2", "BDC_CTRL"])

    als_genes = set(ALS_GENES)
    if a.als_genes:
        als_genes |= {l.strip() for l in open(a.als_genes) if l.strip()}

    # ---------------- FusionInspector (primary) ----------------
    fi_files = sorted(glob.glob(os.path.join(a.rnafusion_root, "rnafusion_analysis_batch*", "fusioninspector",
                                             "*.FusionInspector.fusions.abridged.tsv")))
    if not fi_files:
        sys.exit("No FusionInspector abridged files found")
    seen, frames, file_rows = {}, [], []
    for f in fi_files:
        s = sample_from_path(f)
        batch = re.search(r"rnafusion_analysis_(batch\d+)", f).group(1)
        if s in seen:
            file_rows.append(dict(sample=s, batch=batch, file=f, status="duplicate_sample_skipped"))
            continue
        seen[s] = f
        d = read_tsv_hash(f)
        file_rows.append(dict(sample=s, batch=batch, file=f, status="read", rows=len(d)))
        if d.empty:
            continue
        d.insert(0, "sample", s); d.insert(1, "rnafusion_batch", batch)
        frames.append(d)
    fi = pd.concat(frames, ignore_index=True)
    for c in ["JunctionReadCount", "SpanningFragCount", "FFPM"]:
        fi[c] = pd.to_numeric(fi[c], errors="coerce")
    fi["gene1"] = fi["LeftGene"].str.split("^").str[0]
    fi["gene2"] = fi["RightGene"].str.split("^").str[0]
    fi["pair"] = fi["gene1"] + "--" + fi["gene2"]
    fi["participant"] = fi["sample"].map(participant_of)

    # ---------------- discovery callers (fusion-report) ----------------
    callers = {}
    fr_samples = set()
    for f in glob.glob(os.path.join(a.rnafusion_root, "rnafusion_analysis_batch*", "fusionreport", "*.fusions.csv")):
        s = sample_from_path(f); fr_samples.add(s)
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                found = [c for c in ("arriba", "starfusion", "fusioncatcher") if (r.get(c) or "").strip()]
                callers[(s, r["Fusion"].strip())] = found
    def caller_info(row):
        if row["sample"] not in fr_samples:
            return pd.Series({"discovery_callers": "", "n_discovery_callers": pd.NA, "caller_info": "unknown_no_fusionreport"})
        c = callers.get((row["sample"], row["FusionName"]))
        if c is None:
            return pd.Series({"discovery_callers": "", "n_discovery_callers": pd.NA, "caller_info": "pair_not_in_fusionreport"})
        return pd.Series({"discovery_callers": ";".join(c), "n_discovery_callers": len(c), "caller_info": "available"})
    fi = pd.concat([fi, fi.apply(caller_info, axis=1)], axis=1)

    # ---------------- filters ----------------
    annots = fi["annots"].fillna("")
    fi["F1_junction_reads"] = fi["JunctionReadCount"] >= a.min_junction_reads
    fi["F2_ffpm"] = fi["FFPM"] >= a.min_ffpm
    fi["F3_large_anchor"] = fi["LargeAnchorSupport"].eq("YES")
    fi["F4_not_neighbors"] = ~annots.str.contains("NEIGHBORS", regex=False)
    fi["F5_not_artefact_list"] = ~annots.apply(lambda x: any(t in x for t in ARTEFACT_TAGS))
    ctrl_line_samples = set(cov.loc[cov["is_control_line"], "sample"])
    ctrl_line_pairs = set(fi.loc[fi["sample"].isin(ctrl_line_samples), "pair"])
    fi["F6_not_in_control_line"] = ~fi["pair"].isin(ctrl_line_pairs)
    fi["pass_core"] = fi[["F1_junction_reads", "F2_ffpm", "F3_large_anchor", "F4_not_neighbors",
                          "F5_not_artefact_list", "F6_not_in_control_line"]].all(axis=1)
    fi["pass_multicaller"] = fi["pass_core"] & (pd.to_numeric(fi["n_discovery_callers"], errors="coerce") >= 2)
    fi["als_gene_partner"] = fi["gene1"].isin(als_genes) | fi["gene2"].isin(als_genes)
    fi["coding_fusion"] = fi["PROT_FUSION_TYPE"].isin(["INFRAME", "FRAMESHIFT"])   # FusionInspector predicts a CDS fusion
    keep_cols = ["sample", "participant", "rnafusion_batch", "FusionName", "pair", "gene1", "gene2", "JunctionReadCount",
                 "SpanningFragCount", "FFPM", "LeftBreakpoint", "RightBreakpoint", "SpliceType", "LargeAnchorSupport",
                 "annots", "PROT_FUSION_TYPE", "FUSION_TRANSL", "discovery_callers", "n_discovery_callers", "caller_info",
                 "F1_junction_reads", "F2_ffpm", "F3_large_anchor", "F4_not_neighbors", "F5_not_artefact_list",
                 "F6_not_in_control_line", "pass_core", "pass_multicaller", "als_gene_partner", "coding_fusion"]
    keep_cols = [c for c in keep_cols if c in fi.columns]
    fi[keep_cols].to_csv(out("fusion_calls_all.tsv"), sep="\t", index=False)
    passing = fi[fi["pass_core"]]
    passing[keep_cols].to_csv(out("fusion_calls_pass.tsv"), sep="\t", index=False)
    passing[passing["als_gene_partner"]][keep_cols].to_csv(out("als_gene_fusions.tsv"), sep="\t", index=False)

    # ---------------- test population ----------------
    cov["has_fusion_output"] = cov["sample"].isin(seen)
    pop = cov[(~cov["is_control_line"]) & cov["diagnosis"].isin(["ALS", "Healthy Control"]) & cov["has_fusion_output"]]
    pop = pop.sort_values("sample").drop_duplicates("participant")      # one sample per participant
    pop[["sample", "participant", "diagnosis", "seq_batch", "sex", "source"]].to_csv(out("sample_manifest.tsv"), sep="\t", index=False)
    n_als = int((pop["diagnosis"] == "ALS").sum()); n_hc = int((pop["diagnosis"] == "Healthy Control").sum())
    dx = dict(zip(pop["sample"], pop["diagnosis"]))

    def test(table, key, label, tier_col):
        sub = table[table[tier_col] & table["sample"].isin(dx)]
        carriers = sub.groupby(key)["sample"].apply(lambda x: set(x))
        rows = []
        for k, smp in carriers.items():
            a_ = sum(dx[s] == "ALS" for s in smp); h_ = len(smp) - a_
            if a_ + h_ < a.min_carriers_to_test:
                continue
            orr, p = fisher_exact([[a_, n_als - a_], [h_, n_hc - h_]])
            rows.append({label: k, "n_ALS": a_, "n_HC": h_, "freq_ALS": a_ / n_als, "freq_HC": h_ / n_hc,
                         "odds_ratio": orr, "p_fisher": p})
        r = pd.DataFrame(rows)
        if r.empty:
            return r
        r = r.sort_values("p_fisher")
        r["padj_BH"] = bh(r["p_fisher"].values)
        return r

    pair_tests = test(passing, "pair", "fusion_pair", "pass_core")
    if not pair_tests.empty:
        pair_tests["als_gene_partner"] = pair_tests["fusion_pair"].apply(lambda p: any(g in als_genes for g in p.split("--")))
    pair_tests.to_csv(out("fusion_recurrence_tests.tsv"), sep="\t", index=False)
    multi = test(passing, "pair", "fusion_pair", "pass_multicaller")
    multi.to_csv(out("fusion_recurrence_tests_multicaller_sensitivity.tsv"), sep="\t", index=False)
    genes_long = pd.concat([passing.assign(gene=passing["gene1"]), passing.assign(gene=passing["gene2"])])
    gene_tests = test(genes_long.drop_duplicates(["sample", "gene"]), "gene", "gene", "pass_core")
    if not gene_tests.empty:
        gene_tests["als_gene"] = gene_tests["gene"].isin(als_genes)
    gene_tests.to_csv(out("fusion_gene_tests.tsv"), sep="\t", index=False)

    # ---------------- caller support summary ----------------
    cs = passing.assign(n=passing["n_discovery_callers"].astype("string").fillna("unknown")) \
                .groupby(["caller_info", "n"]).size().rename("calls").reset_index()
    cs.to_csv(out("caller_support_summary.tsv"), sep="\t", index=False)

    # ---------------- arriba strand check ----------------
    srows = []
    for f in sorted(glob.glob(os.path.join(a.rnafusion_root, "rnafusion_analysis_batch*", "arriba", "*.arriba.fusions.tsv"))):
        d = read_tsv_hash(f)
        n = cons = opp = unk = 0
        for _, r in d.iterrows():
            for k in ("strand1(gene/fusion)", "strand2(gene/fusion)"):
                g, _, fu = (r.get(k) or "./.").partition("/")
                n += 1
                if "." in (g, fu): unk += 1
                elif g == fu: cons += 1
                else: opp += 1
        known = cons + opp
        srows.append(dict(sample=sample_from_path(f), arriba_calls=len(d), breakends=n, gene_fusion_same_strand=cons,
                          gene_fusion_opposite_strand=opp, strand_unknown=unk,
                          fraction_same_strand_of_known=round(cons / known, 3) if known else None))
    sc = pd.DataFrame(srows); sc.to_csv(out("arriba_strand_check.tsv"), sep="\t", index=False)

    pd.DataFrame(file_rows).to_csv(out("input_files.tsv"), sep="\t", index=False)
    summary = dict(
        fusioninspector_samples=len(seen), samples_with_fusionreport=len(fr_samples & set(seen)),
        fusioninspector_rows=int(len(fi)), rows_passing_core=int(fi["pass_core"].sum()),
        rows_passing_multicaller=int(fi["pass_multicaller"].sum()),
        filter_failures={c: int((~fi[c]).sum()) for c in ["F1_junction_reads", "F2_ffpm", "F3_large_anchor",
                                                          "F4_not_neighbors", "F5_not_artefact_list", "F6_not_in_control_line"]},
        control_line_samples=len(ctrl_line_samples & set(seen)), control_line_pairs_excluded=len(ctrl_line_pairs),
        test_population=dict(ALS=n_als, HC=n_hc), pairs_tested=int(len(pair_tests)),
        pairs_padj_lt_0_05=int((pair_tests["padj_BH"] < 0.05).sum()) if len(pair_tests) else 0,
        genes_tested=int(len(gene_tests)),
        genes_padj_lt_0_05=int((gene_tests["padj_BH"] < 0.05).sum()) if len(gene_tests) else 0,
        als_gene_passing_calls=int(passing["als_gene_partner"].sum()),
        coding_passing_calls={k: int(v) for k, v in passing["PROT_FUSION_TYPE"].value_counts().items()},
        top_recurrent_passing_pairs={k: int(v) for k, v in passing.drop_duplicates(["participant", "pair"])["pair"].value_counts().head(15).items()},
        arriba_median_fraction_same_strand=float(sc["fraction_same_strand_of_known"].median()) if len(sc) else None,
        arriba_samples_checked=int(len(sc)),
        settings=dict(min_junction_reads=a.min_junction_reads, min_ffpm=a.min_ffpm,
                      min_carriers_to_test=a.min_carriers_to_test, artefact_tags=ARTEFACT_TAGS),
    )
    json.dump(summary, open(out("summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
