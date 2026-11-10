#!/usr/bin/env python3
"""
01_cross_omics_agreement.py  -  Objective 4, cross-omics interpretation

Brings the per-layer results together at gene level and asks what combining layers adds:

  A. Cohort-level gene evidence matrix (ALS vs healthy control)
       DNA      Objective 2 prioritised SV candidates (primary_candidates.tsv) + ALSoD category
       RNA      DREAM results on AnswerALS counts            (01_rna_dream_answerals.R)
       Protein  limma results, consortium protein matrix     (07_protein_differential_abundance.R)
       Fusion   filtered fusions / fusion gene tests         (12_fusion_filter_als_test.py)
       Isoform  variant-only (isoform / novel) peptides       (06_peptide_source_classification.py)
     -> gene_evidence_matrix.tsv, layer_intersections.tsv (UpSet-style counts)

  B. RNA-protein agreement of ALS-vs-HC effects for genes measured in both
     -> rna_protein_concordance.tsv, rna_protein_concordance_summary.json, scatter PNG

  C. Carrier-level DNA -> RNA -> protein for every prioritised SV candidate
     (audited carriers from participant_support.tsv): carrier vs non-carrier gene
     expression (AnswerALS log2 CPM, all RNA participants) and protein abundance
     (07 gene x participant matrix, or the consolidated v5 matrix)
     -> sv_candidate_carrier_effects.tsv

  D. Fusion -> peptide chains: filtered fusions whose fusion peptide was detected
     in the same participant -> fusion_peptide_chains.tsv

Thresholds are declared in SETTINGS below. "supported" = FDR < 0.05; an exploratory
tier uses nominal p < 0.01 and is labelled as such everywhere.
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr, mannwhitneyu

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from common import part, load_v5_protein_by_gene
from rna_answerals import load_rna_log2cpm

FDR, NOMINAL_P = 0.05, 0.01
RNA_MIN_CPM = 1.0


def load_results(path, label):
    d = pd.read_csv(path, sep=None, engine="python")
    need = {"gene_name", "logFC", "P.Value", "adj.P.Val"}
    if not need <= set(d.columns):
        sys.exit(f"{label}: {path} lacks columns {need - set(d.columns)}")
    if "gene_mapping" in d.columns:
        # FIX 15 Oct 2026: the protein limma output labels symbols "uniprot_to_symbol" (and "entry_name" where no
        # symbol was found), never "unique_gene", so every protein was dropped. Keep rows mapped to a gene symbol.
        d = d[d.gene_mapping.isin(["unique_gene", "uniprot_to_symbol"])]
    d = d.dropna(subset=["gene_name"])
    d = d.loc[d.groupby("gene_name")["P.Value"].idxmin()]          # one row per gene (best)
    d = d.set_index("gene_name")[["logFC", "P.Value", "adj.P.Val"] + (["t"] if "t" in d.columns else [])]
    return d.add_prefix(f"{label}_")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rna-results", required=True)
    ap.add_argument("--protein-results", required=True)
    ap.add_argument("--fusion-dir", required=True, help="output folder of 12_fusion_filter_als_test.py")
    ap.add_argument("--peptide-dir", required=True, help="output folder of 06_peptide_source_classification.py")
    ap.add_argument("--sv-primary", required=True, help="Objective 2 primary_candidates.tsv")
    ap.add_argument("--sv-support", required=True, help="Objective 2 participant_support.tsv")
    ap.add_argument("--alsod", help="ALSoD gene list CSV (Gene symbol, Category)")
    ap.add_argument("--rna-counts", required=True, help="AnswerALS raw-count CSV (release 7)")
    ap.add_argument("--rna-coldata", required=True, help="remove_btc_raw_coldata_filtered (2).csv (336 ALS/HC samples)")
    ap.add_argument("--gtf", required=True, help="GENCODE v46 GTF, or a 2-column ENSG<TAB>symbol map (ensg_symbol.tsv)")
    ap.add_argument("--protein-gene-matrix", help="07 output protein_by_participant_gene.log2.tsv (gene x participant); "
                                                  "use this OR the three v5 options below")
    ap.add_argument("--protein-matrix", help="v5: 05_consolidate_cohort.py protein_by_run.log2.tsv")
    ap.add_argument("--protein-samples", help="v5: 05_consolidate_cohort.py sample_metadata.tsv")
    ap.add_argument("--pgdb-metadata", help="v5: proteogenomic_metadata.tsv")
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.outdir): sys.exit(f"Output folder exists: {a.outdir}")
    os.makedirs(a.outdir); out = lambda f: os.path.join(a.outdir, f)

    # ---------------- per-layer cohort results ----------------
    rna = load_results(a.rna_results, "rna")
    prot = load_results(a.protein_results, "prot")
    genes = pd.DataFrame(index=sorted(set(rna.index) | set(prot.index)))
    genes = genes.join(rna).join(prot)

    sv = pd.read_csv(a.sv_primary, sep="\t")
    sv_genes = {}
    for r in sv.itertuples():
        for g in str(r.genes).split(";"):
            sv_genes.setdefault(g, []).append(r.event_id)
    fus_pass = pd.read_csv(os.path.join(a.fusion_dir, "fusion_calls_pass.tsv"), sep="\t")
    fus_genes = set(fus_pass.gene1) | set(fus_pass.gene2)
    fgt_path = os.path.join(a.fusion_dir, "fusion_gene_tests.tsv")
    fgt = pd.read_csv(fgt_path, sep="\t") if os.path.getsize(fgt_path) > 1 else pd.DataFrame(columns=["gene", "padj_BH"])
    peps = pd.read_csv(os.path.join(a.peptide_dir, "variant_only_peptides.tsv"), sep="\t")
    iso_genes, novel_genes = set(), set()
    for r in peps.itertuples():
        gs = {x.replace("GN=", "") for x in str(r.genes).split(";") if x and x != "nan"}
        (novel_genes if str(r.peptide_class).startswith("novel") else iso_genes).update(gs)

    allg = sorted(set(genes.index) | set(sv_genes) | fus_genes | iso_genes | novel_genes)
    genes = genes.reindex(allg)
    genes["DNA_prioritised_SV"] = genes.index.isin(sv_genes)
    genes["DNA_sv_events"] = [";".join(sv_genes.get(g, [])) for g in genes.index]
    genes["RNA_FDR"] = genes["rna_adj.P.Val"] < FDR
    genes["RNA_nominal"] = genes["rna_P.Value"] < NOMINAL_P
    genes["PROT_FDR"] = genes["prot_adj.P.Val"] < FDR
    genes["PROT_nominal"] = genes["prot_P.Value"] < NOMINAL_P
    genes["FUSION_filtered_call"] = genes.index.isin(fus_genes)
    genes["FUSION_ALS_vs_HC_FDR"] = genes.index.isin(set(fgt.loc[fgt.padj_BH < FDR, "gene"]))
    genes["ISOFORM_peptide"] = genes.index.isin(iso_genes)
    genes["NOVEL_peptide"] = genes.index.isin(novel_genes)
    if a.alsod:
        al = pd.read_csv(a.alsod)
        genes["ALSoD_category"] = genes.index.astype(str).str.upper().map(  # case-insensitive: ALSoD writes e.g. 'EphA3'
            dict(zip(al["Gene symbol"].astype(str).str.upper(), al["Category"])))
    strict = ["DNA_prioritised_SV", "RNA_FDR", "PROT_FDR", "FUSION_ALS_vs_HC_FDR", "ISOFORM_peptide", "NOVEL_peptide"]
    explor = ["DNA_prioritised_SV", "RNA_nominal", "PROT_nominal", "FUSION_filtered_call", "ISOFORM_peptide", "NOVEL_peptide"]
    genes["n_layers_strict"] = genes[strict].fillna(False).astype(bool).sum(axis=1)
    genes["n_layers_exploratory"] = genes[explor].fillna(False).astype(bool).sum(axis=1)
    genes["same_direction_rna_prot"] = np.sign(genes["rna_logFC"]) == np.sign(genes["prot_logFC"])
    genes.index.name = "gene"
    genes.sort_values(["n_layers_strict", "n_layers_exploratory"], ascending=False).to_csv(out("gene_evidence_matrix.tsv"), sep="\t")

    def intersections(cols, label):
        b = genes[cols].fillna(False).astype(bool)
        b = b[b.any(axis=1)]
        key = b.apply(lambda r: "+".join(c for c in cols if r[c]), axis=1)
        return key.value_counts().rename_axis("layer_combination").reset_index(name="genes").assign(tier=label)
    pd.concat([intersections(strict, "strict_FDR"), intersections(explor, "exploratory_nominal")]).to_csv(
        out("layer_intersections.tsv"), sep="\t", index=False)

    # ---------------- B. RNA-protein agreement ----------------
    both = genes.dropna(subset=["rna_logFC", "prot_logFC"])
    rho, p_rho = spearmanr(both["rna_logFC"], both["prot_logFC"]) if len(both) > 10 else (np.nan, np.nan)
    sig = both[(both["rna_P.Value"] < NOMINAL_P) & (both["prot_P.Value"] < NOMINAL_P)]
    conc = dict(genes_in_both=int(len(both)), spearman_rho_logFC=float(rho), spearman_p=float(p_rho),
                both_nominal_p_lt_0_01=int(len(sig)), of_which_same_direction=int(sig.same_direction_rna_prot.sum()),
                both_FDR=int(((both["rna_adj.P.Val"] < FDR) & (both["prot_adj.P.Val"] < FDR)).sum()),
                note="RNA and protein come from different differentiations/runs of the same participants; agreement is expected to be modest.")
    both[["rna_logFC", "rna_P.Value", "rna_adj.P.Val", "prot_logFC", "prot_P.Value", "prot_adj.P.Val", "same_direction_rna_prot"]] \
        .to_csv(out("rna_protein_concordance.tsv"), sep="\t")
    json.dump(conc, open(out("rna_protein_concordance_summary.json"), "w"), indent=2)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(both["rna_logFC"], both["prot_logFC"], s=4, alpha=0.4, color="#4c72b0")
        ax.scatter(sig["rna_logFC"], sig["prot_logFC"], s=10, color="#c44e52", label="both p < 0.01")
        ax.axhline(0, lw=0.5, color="grey"); ax.axvline(0, lw=0.5, color="grey")
        ax.set_xlabel("RNA log2FC (ALS vs HC)"); ax.set_ylabel("Protein log2FC (ALS vs HC)")
        ax.set_title(f"Spearman rho = {rho:.2f} (n = {len(both)})"); ax.legend(frameon=False)
        fig.tight_layout(); fig.savefig(out("rna_protein_concordance.png"), dpi=300); plt.close(fig)
    except Exception as e:
        print("plot skipped:", e)

    # ---------------- C. carrier-level DNA -> RNA -> protein ----------------
    col = pd.read_csv(a.rna_coldata, index_col=0)
    rna_parts = {part(s) for s in col.index}
    rmat = load_rna_log2cpm(None, a.gtf, rna_parts, counts_path=a.rna_counts)
    if a.protein_gene_matrix:                                       # consortium protein layer (07, gene x participant)
        pm = pd.read_csv(a.protein_gene_matrix, sep="\t", index_col=0, na_values=["NA", ""])
        pm.columns = [part(c) for c in pm.columns]
    else:                                                           # v5 protein groups (05 + PGDB metadata)
        if not (a.protein_matrix and a.protein_samples and a.pgdb_metadata):
            sys.exit("give --protein-gene-matrix, or all of --protein-matrix --protein-samples --pgdb-metadata")
        pm = load_v5_protein_by_gene(a.protein_matrix, a.protein_samples, a.pgdb_metadata)

    sup = pd.read_csv(a.sv_support, sep="\t", dtype=str)
    sup = sup[sup.support_rule_met.str.lower() == "true"]
    rows = []
    for r in sv.itertuples():
        car = {part(s) for s in sup.loc[sup.event_id == r.event_id, "sample_id"]} - {None}
        for g in str(r.genes).split(";"):
            row = dict(event_id=r.event_id, sv_type=r.sv_type, gene=g, alsod=r.highest_alsod_evidence,
                       n_audited_carriers=len(car))
            for lay, mat, min_expr in (("rna", rmat, RNA_MIN_CPM), ("prot", pm, None)):
                if g not in mat.index:
                    row[f"{lay}_status"] = "not_measured"; continue
                x = mat.loc[g].dropna()
                if lay == "rna" and (2 ** x - 1).median() < min_expr:
                    row[f"{lay}_status"] = "not_expressed"; continue
                c, n = x[x.index.isin(car)], x[~x.index.isin(car)]
                row[f"{lay}_n_carriers_measured"] = len(c)
                if len(c) == 0:
                    row[f"{lay}_status"] = "no_carrier_measured"; continue
                med, mad = n.median(), 1.4826 * (n - n.median()).abs().median()
                row.update({f"{lay}_status": "tested", f"{lay}_carrier_median_minus_noncarrier": float(c.median() - med),
                            f"{lay}_robust_z": float((c.median() - med) / mad) if mad > 0 else np.nan,
                            f"{lay}_p_mwu": float(mannwhitneyu(c, n).pvalue) if len(c) >= 2 else np.nan})
            rows.append(row)
    pd.DataFrame(rows).to_csv(out("sv_candidate_carrier_effects.tsv"), sep="\t", index=False)

    # ---------------- D. fusion -> peptide chains ----------------
    fus_pep = peps[peps.sources.str.contains("fusioninspector", na=False)]
    ch = []
    for r in fus_pep.itertuples():
        pp = set(str(r.participants).split(";"))
        gs = {x.replace("GN=", "") for x in str(r.genes).split(";")}
        hit = fus_pass[fus_pass.participant.isin(pp) & (fus_pass.gene1.isin(gs) | fus_pass.gene2.isin(gs) |
                       fus_pass.pair.str.replace("--", "-").isin(gs))]
        for h in hit.itertuples():
            ch.append(dict(peptide=r.peptide, peptide_class=r.peptide_class, participant=h.participant, fusion_pair=h.pair,
                           junction_reads=h.JunctionReadCount, ffpm=h.FFPM))
    pd.DataFrame(ch).to_csv(out("fusion_peptide_chains.tsv"), sep="\t", index=False)

    summary = dict(
        genes_in_matrix=int(len(genes)),
        strict_layer_counts={c: int(genes[c].fillna(False).astype(bool).sum()) for c in strict},
        exploratory_layer_counts={c: int(genes[c].fillna(False).astype(bool).sum()) for c in explor},
        genes_with_ge2_layers_strict=int((genes.n_layers_strict >= 2).sum()),
        genes_with_ge2_layers_exploratory=int((genes.n_layers_exploratory >= 2).sum()),
        rna_protein=conc, sv_candidate_gene_rows=len(rows), fusion_peptide_chains=len(ch),
        thresholds=dict(FDR=FDR, NOMINAL_P=NOMINAL_P, RNA_MIN_CPM=RNA_MIN_CPM))
    json.dump(summary, open(out("summary.json"), "w"), indent=2, default=str)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
