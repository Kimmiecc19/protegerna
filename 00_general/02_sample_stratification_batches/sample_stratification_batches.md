# Stratified Sampling for AnswerALS Multi-Omics Data

📅 **Created**: 12 May 2025
🎯 **Purpose**: Create artificial batches for transcriptomic and proteomic data to minimize downstream batch effects.

---

## 🔍 Overview

This repository describes how AnswerALS samples were pre-processed and stratified to reduce technical batch effects prior to multi-omics integration.

---

## 📋 Sample Mapping: Summary

Based on Neuromine sample mapping (see [README](https://stdataportalprod.blob.core.windows.net/wp-media/Sample-Mapping-README.txt)).

### Key Columns

* `Participant ID`: Anonymized ID for the subject
* `Sample ID`: Unique sample identifier
* `Batch #`: Indicates batch (e.g. BTC, BDC)
* `Shipment`: Shipment number (each has \~3 batches)

### Recommended Use

Use the mapping file to:

1. Group samples by batch for normalization
2. Perform batch correction (e.g., ComBat, limma)
3. Perform QC by monitoring consistency of batch controls
4. Validate findings across batches

---

## 🧪 Batch Technical Control (BTC) vs Batch Differentiation Control (BDC)

* `CTRL-NEUEU392AE8` is the control line used for **BTC** and **BDC**
* **BTC**: Clone produced in bulk for consistent omics assay comparison (Oct–Dec 2018 & Jun–Jul 2021)
* **BDC**: Same clone, differentiated with each batch to assess inter-batch variability

⚠️ **52 samples** from release one had strong batch effects. Recommended to exclude these from analysis.

---

## 📊 AnswerALS Omics Dataset (as of 30 May 2025)

* 1269 total participants
* 939 genomics, 650 transcriptomics, 499 proteomics
* 347 participants with all 3 omics layers (WGS, RNA-Seq, proteomics)
* After QC and filtering, only those without strong batch effects were retained

---

## 🧩 Merging Metadata & Omics Samples

Steps:

1. Filter for participants with all 3 omics layers
2. Merge with Neuromine metadata
3. Remove epigenomics entries
4. Merge with filtered sample mapping
5. Extract metadata + transcriptomic & proteomic sample IDs

Result:

* 991 total participants (BTC + BDC across T and P)
* BTC: 67 samples (T x 34, P x 33)
* BDC: 924 (T x 458, P x 466), of which 186 are for CTRL-NEUEU392AE8

---

## 🧪 Creating Artificial Batches

**Problem**: Filtering by available omics and batch quality left batches unbalanced (some with 2–14 samples).

**Solution**: Use **StratifiedKFold** to create artificial, biologically balanced batches across transcriptomics and proteomics data.

🔗 [StratifiedKFold docs](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedKFold.html)

---

## ⚖️ Why StratifiedKFold?

Benefits:

* Preserves class distribution (e.g., sex, diagnosis)
* Reduces bias from imbalanced splits
* Enhances reproducibility (with `shuffle=True` and `random_state`)

**Method**:

1. Group by class (e.g. diagnosis)
2. Split each class into *k* folds
3. Combine one fold from each class → balanced batches

---

## 📌 Important Considerations

* Batches should align across omics layers to reduce integration noise
* Must consider compute/storage limits when choosing number of batches

---

## 🤖 BTC Samples – Include or Exclude?

| Step                    | Recommendation                                 |
| ----------------------- | ---------------------------------------------- |
| **Preprocessing**       | ✅ Include for pipeline QC + normalization      |
| **Stratified Sampling** | ❌ Exclude (not biologically meaningful)        |
| **Downstream Analysis** | ❌ Exclude (can skew biological interpretation) |

BTC samples:

* Aid normalization (e.g., ComBat)
* Help detect pipeline artifacts
* Serve as reference for technical variability

---

## ✅ Final Strategy

* ✅ **Run BTCs through nf-core pipelines**
* ❌ **Exclude BTCs from biological downstream analyses**

BTCs support:

* QC reports
* Assay normalization
* Artifact detection
* Cross-batch consistency

---

## 📝 TODOs

* [ ] Clarify discrepancy between 458+466 BDC vs 347 unique participants
* [ ] Assign stratified batches (with matched T & P samples)
* [ ] Investigate multiple files per participant (filename-only differences)

---

## Script: stratify_june2025_BTC_2.py

## Input files:

BDC_FILE = "bdc.csv"
BTC_FILE = "btc.csv"

## Output files:

OUTPUT_PROT = "proteomic_with_batches.csv"
OUTPUT_TRANS = "transcriptomic_with_batches.csv"
SUMMARY_REPORT = "batch_summary_report.csv"
OUTPUT_PROT_BTC = "proteomic_batches_BTC.csv"
OUTPUT_TRANS_BTC = "transcriptomic_batches_BTC.csv"

Number of samples per batch set to 50

```python 
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------
# CONFIG
# ------------------------------
BDC_FILE = "bdc.csv"
BTC_FILE = "btc.csv"
N_PER_BATCH = 50
OUTPUT_PROT = "proteomic_with_batches.csv"
OUTPUT_TRANS = "transcriptomic_with_batches.csv"
SUMMARY_REPORT = "batch_summary_report.csv"
OUTPUT_PROT_BTC = "proteomic_batches_BTC.csv"
OUTPUT_TRANS_BTC = "transcriptomic_batches_BTC.csv"

# ------------------------------
# LOAD DATA
# ------------------------------
bdc = pd.read_csv(BDC_FILE)
btc = pd.read_csv(BTC_FILE)

# Tag omic types
bdc["omic"] = bdc["sample_id"].apply(lambda x: "P" if x.endswith("-P") else "T")
btc["omic"] = btc["sample_id"].apply(lambda x: "P" if x.endswith("-P") else "T")

# Split data: stratifiable vs control participant
bdc_case = bdc[bdc["participant"] != "CTRL-NEUEU392AE8"].copy()
bdc_ctrl = bdc[bdc["participant"] == "CTRL-NEUEU392AE8"].copy()

# Tag sample types (CTRL vs non-CTRL)
bdc_case["source"] = "BDC"
bdc_ctrl["source"] = "BDC_CTRL"
btc["source"] = "BTC"

# ------------------------------
# STRATIFY MAIN PARTICIPANTS
# ------------------------------
# Pivot to align T & P for each participant
pivot = bdc_case.pivot_table(
    index="participant",
    columns="omic",
    values=["sample_id", "sex", "diagnosis", "seq_batch", "shipment"],
    aggfunc="first"
)
pivot.columns = ['_'.join(col).strip() for col in pivot.columns.values]
pivot.reset_index(inplace=True)

# Create strata key
pivot["strata"] = (
    pivot["sex_P"].fillna(pivot["sex_T"]).astype(str) + "_" +
    pivot["diagnosis_P"].fillna(pivot["diagnosis_T"]).astype(str) + "_" +
    pivot["seq_batch_P"].fillna(pivot["seq_batch_T"]).astype(str)
)

# Determine number of batches
n_participants = len(pivot)
n_batches = max(1, n_participants // N_PER_BATCH)

# Assign batches using StratifiedKFold
skf = StratifiedKFold(n_splits=n_batches, shuffle=True, random_state=42)
for batch_num, (_, test_idx) in enumerate(skf.split(pivot, pivot["strata"])):
    pivot.loc[test_idx, "artificial_batch"] = batch_num + 1

# ------------------------------
# ROUND-ROBIN of CTRL-NEUEU392AE8 (BDC and BTC)
# ------------------------------
# Group by sequencing batch
grouped = bdc_ctrl.groupby("seq_batch")
grouped_btc = btc.groupby("seq_batch")

# Round-robin assignment for BDC
bdc_ctrl["artificial_batch"] = -1
i = 0
for _, group in grouped:
    for idx in group.index:
        bdc_ctrl.loc[idx, "artificial_batch"] = (i % n_batches) + 1
        i += 1

# Round-robin batch assignment for BTC
btc["artificial_batch"] = -1
i = 0
for _, group in grouped_btc:
    for idx in group.index:
        btc.loc[idx, "artificial_batch"] = (i % n_batches) + 1
        i += 1

# MERGE & EXPORT RESULTS
# ------------------------------

# Add artificial_batch to stratified participants
bdc = bdc_case.merge(pivot[["participant", "artificial_batch"]], on="participant", how="left")

# Combine all sample source types
combined = pd.concat([bdc, bdc_ctrl, btc], ignore_index=True)

# Combine back control and rest of the participants
final = pd.concat([bdc_ctrl, bdc], ignore_index=True).sort_values("participant")

# Combine BTC samples with final dataset
final = pd.concat([final, btc], ignore_index=True).sort_values("participant")

# Sanity check
assert final["artificial_batch"].isnull().sum() == 0, "Some samples were not assigned to a batch!"

# Separate omics and export
prot = final[final["sample_id"].str.endswith("-P")]
trans = final[final["sample_id"].str.endswith("-T")]

prot_btc = final[final["sample_id"].str.endswith("-P")]
trans_btc = final[final["sample_id"].str.endswith("-T")]

prot.to_csv(OUTPUT_PROT, index=False)
trans.to_csv(OUTPUT_TRANS, index=False)

prot_btc.to_csv(OUTPUT_PROT_BTC, index=False)
trans_btc.to_csv(OUTPUT_TRANS_BTC, index=False)

# Summary report
summary = final.groupby(["artificial_batch", "diagnosis", "sex"]).size().reset_index(name="count")
summary.to_csv(SUMMARY_REPORT, index=False)
print("Yay! Files written:")
print(f" - {OUTPUT_PROT}")
print(f" - {OUTPUT_TRANS}")
print(f" - {SUMMARY_REPORT}")

# Graph of overall sample distributions over batches
sns.countplot(data=final, x="artificial_batch", hue="omic")
plt.title("Sample counts per artificial batch")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("batch_assignments.png")
plt.close()

# Stacked bar chart showing sample types count per batch
grouped_counts = combined.groupby(["artificial_batch", "source"]).size().unstack(fill_value=0)
# Sort by batch number
grouped_counts = grouped_counts.sort_index()

plt.figure(figsize=(10, 6))
grouped_counts.plot(kind="bar", stacked=True, colormap="Set2")
plt.title("Sample Type Distribution per Artificial Batch")
plt.xlabel("Artificial Batch")
plt.ylabel("Number of Samples")
plt.xticks(rotation=0)
plt.legend(title="Sample Source", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.savefig("sampletype_batch_distribution.png")
plt.close()
print("Saved: sampletype_batch_distribution.png")

# Heatmap: artificial_batch × diagnosis × sex
pivot = final.groupby(["artificial_batch", "diagnosis", "sex"]).size().unstack(fill_value=0)
plt.figure(figsize=(12, 6))
sns.heatmap(pivot, annot=True, fmt="d", cmap="Blues")
plt.title("Batch Composition by Diagnosis and Sex")
plt.tight_layout()
plt.savefig("batch_heatmap_diagnosis_sex.png")
plt.close()
print("Saved: batch_heatmap_diagnosis_sex.png")

# Relative proportions by diagnosis in each batch
grouped_diag = final.groupby(["artificial_batch", "diagnosis"]).size()
prop_diag = grouped_diag.groupby(level=0).transform(lambda x: x / x.sum())
prop_diag_df = grouped_diag.to_frame("count")
prop_diag_df["proportion"] = prop_diag
prop_diag_df = prop_diag_df.reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(data=prop_diag_df, x="artificial_batch", y="proportion", hue="diagnosis")
plt.title("Relative Diagnosis Composition per Batch")
plt.ylabel("Proportion")
plt.xlabel("Artificial Batch")
plt.tight_layout()
plt.savefig("batch_diagnosis_proportion.png")
plt.close()
print("Saved: batch_diagnosis_proportion.png")

# Relative proportions by sex in each batch
grouped_sex = final.groupby(["artificial_batch", "sex"]).size()
prop_sex = grouped_sex.groupby(level=0).transform(lambda x: x / x.sum())
prop_sex_df = grouped_sex.to_frame("count")
prop_sex_df["proportion"] = prop_sex
prop_sex_df = prop_sex_df.reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(data=prop_sex_df, x="artificial_batch", y="proportion", hue="sex")
plt.title("Relative Sex Composition per Batch")
plt.ylabel("Proportion")
plt.xlabel("Artificial Batch")
plt.tight_layout()
plt.savefig("batch_sex_proportion.png")
plt.close()
print("Saved: batch_sex_proportion.png")

# Relative proportions by omic in each batch
grouped_omic = final.groupby(["artificial_batch", "omic"]).size()
prop_omic = grouped_omic.groupby(level=0).transform(lambda x: x / x.sum())
prop_omic_df = grouped_omic.to_frame("count")
prop_omic_df["proportion"] = prop_omic
prop_omic_df = prop_omic_df.reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(data=prop_omic_df, x="artificial_batch", y="proportion", hue="omic")
plt.title("Relative Omic Composition per Batch")
plt.ylabel("Proportion")
plt.xlabel("Artificial Batch")
plt.tight_layout()
plt.savefig("batch_omic_proportion.png")
plt.close()
print("Saved: batch_omic_proportion.png")

# Relative proportions by shipment in each batch
grouped_shipment = final.groupby(["artificial_batch", "shipment"]).size()
prop_shipment = grouped_shipment.groupby(level=0).transform(lambda x: x / x.sum())
prop_shipment_df = grouped_shipment.to_frame("count")
prop_shipment_df["proportion"] = prop_shipment
prop_shipment_df = prop_shipment_df.reset_index()

# Pivot to get shipments as columns (proportions) and plot
shipment_pivot = prop_shipment_df.pivot(index="artificial_batch", columns="shipment", values="proportion")
shipment_pivot = shipment_pivot.fillna(0).sort_index()
shipment_pivot.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="tab20")
plt.title("Shipment Composition per Batch")
plt.ylabel("Proportion")
plt.xlabel("Artificial Batch")
plt.legend(title="Shipment", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.savefig("batch_shipment_proportion_stacked.png")
plt.close()
print("Saved: batch_shipment_proportion_stacked.png")
```

# Validation of artificial batches 

# What makes batches trustworthy?
1. Even total sample counts across batches (n_samples)
2. Even diagnosis composition (using crosstab and stacked bar)
3. Even sex distribution (using crosstab and stacked bar)
4. Balanced original seq_batch (using seq_batch crosstab)
5. BTCs separated or distributed (BTC count per batch)
6. Unique participants per batch (n_participants)  
7. Visual inspection for imbalance (using stacked plots)           

```python
import pandas as pd

# Configuration
prot_file = "proteomic_batches_BTC.csv"
trans_file = "transcriptomic_batches_BTC.csv"

# Load data
prot_df = pd.read_csv(prot_file)
trans_df = pd.read_csv(trans_file)

# Validation stats for both omics

# Check how many BTCs in batches
print("BTCs in proteomic batches:", prot_df.query("source == 'BTC'").shape[0])
print("BTCs in transcriptomic batches:", trans_df.query("source == 'BTC'").shape[0])

# Check how many BDCs in batches
print("BDCs in proteomic batches:", prot_df.query("source == 'BDC'").shape[0])
print("BDCs in transcriptomic batches:", trans_df.query("source == 'BDC'").shape[0])

# Batch stats (combined)
def get_batch_stats(df, omic_type, source=None):
    if source:
        df = df[df["source"] == source]
    stats = df.groupby("artificial_batch").agg(
        n_samples=("sample_id", "count"),
        n_participants=("participant", pd.Series.nunique),
        n_btc=("source", lambda x: (x == "BTC").sum()),
        n_bdc=("source", lambda x: (x == "BDC").sum()),
        n_case=("diagnosis", lambda x: (x == "ALS").sum()),
        n_control=("diagnosis", lambda x: (x == "Healthy Control").sum()),
        n_female=("sex", lambda x: (x == "Female").sum()),
        n_male=("sex", lambda x: (x == "Male").sum()),
        n_batches=("seq_batch", pd.Series.nunique),
    )
    return stats


# Validate distributions across batches
def get_validation_tables(df, omic_type):
    bdc = df[df["source"] == "BDC"]

    return {
        "bdc_count_per_batch": bdc["artificial_batch"].value_counts().sort_index().rename("n_bdc"),
        "sex_distribution": pd.crosstab(bdc["artificial_batch"], bdc["sex"]),
        "diagnosis_distribution": pd.crosstab(bdc["artificial_batch"], bdc["diagnosis"]),
        "seq_batch_distribution": pd.crosstab(bdc["artificial_batch"], bdc["seq_batch"]),
    }

# Execution and export
# Get and save batch stats
prot_stats_all = get_batch_stats(prot_df, "Proteomic")
prot_stats_bdc = get_batch_stats(prot_df, "Proteomic", source="BDC")
prot_stats_btc = get_batch_stats(prot_df, "Proteomic", source="BTC")

prot_stats_all.to_csv("proteomic_batch_stats_all.csv")
prot_stats_bdc.to_csv("proteomic_batch_stats_bdc.csv")
prot_stats_btc.to_csv("proteomic_batch_stats_btc.csv")

trans_stats_all = get_batch_stats(trans_df, "Transcriptomic")
trans_stats_bdc = get_batch_stats(trans_df, "Transcriptomic", source="BDC")
trans_stats_btc = get_batch_stats(trans_df, "Transcriptomic", source="BTC")

trans_stats_all.to_csv("transcriptomic_batch_stats_all.csv")
trans_stats_bdc.to_csv("transcriptomic_batch_stats_bdc.csv")
trans_stats_btc.to_csv("transcriptomic_batch_stats_btc.csv")

# Get and save validation tables
prot_validation = get_validation_tables(prot_df, "Proteomic")
for name, df in prot_validation.items():
    df.to_csv(f"proteomic_{name}.csv")

trans_validation = get_validation_tables(trans_df, "Transcriptomic")
for name, df in trans_validation.items():
    df.to_csv(f"transcriptomic_{name}.csv")
```
---

### ✅ Pros

1. **Essential sanity check**

   * Confirms that BDC (biological disease/control) and BTC (technical control) samples are correctly split across batches.
   * Ensures stratification by diagnosis and sex is preserved — crucial for statistical power and avoiding bias downstream.

2. **Transparent batch structure**

   * Documents how artificial batches were created — important for reproducibility and troubleshooting.
   * Makes it easier to justify and describe design choices in methods sections, manuscripts, or presentations.

3. **Catches early issues**

   * Flags unbalanced batches (e.g., all males or all ALS cases).
   * Alerts if BTCs are missing from a batch, which could affect normalization or batch correction later.

4. **Reusable across omics**

   * Can be applied to both transcriptomic and proteomic datasets.
   * Once templated, becomes a lightweight validation script for future studies.

5. **Supports quality reporting**

   * Can generate summary stats or tables ready for inclusion in reports or supplementary material.

---

### ❌ Cons

1. **Redundant if already validated upstream**

   * If batch assignment and sample stratification were handled during preprocessing (e.g., in R or Nextflow), this check may be redundant.

2. **Doesn’t detect subtle imbalances**

   * Won’t flag statistical trends (e.g., mild male enrichment across all batches) unless distributions are explicitly tested.
   * Doesn’t assess expression or intensity distributions — only metadata.

3. **Scripting overhead**

   * Adds another script to maintain, especially if formats or column names vary between omics layers.
   * Requires consistent metadata structure, or it’ll break.

---

### ✅ When it *is* worth it:

* If you’re doing custom artificial batching — especially for aligning transcriptomics and proteomics in multi-omics studies.
* If you plan to document this step in a manuscript, supplement, or reproducibility audit.
* If you want to proactively catch batch composition issues *before* normalization or integration.

---

## 🧬 But what about my **WGS** data?

In most multi-omics studies, **whole genome sequencing (WGS)** does **not** require batching in the same way as RNA-seq or proteomics. Whether stratified sampling or artificial batching is necessary depends on how you’re using the WGS data.

---

### ❓ Why doesn’t WGS have BTCs?

1. **Minimal per-assay variability**

   * WGS, especially germline variant calling, is robust to batch effects:

     * The assay is standardized and less sensitive to reagent or instrument variability.
     * DNA is stable — unlike RNA or proteins, it doesn't change with biological state.
     * Tools like GATK or `nf-core/sarek` are designed to scale across sequencing runs without needing technical controls.

2. **BTCs target assay noise — not needed for WGS**

   * BTCs in RNA-seq or proteomics help assess lab-specific variability.
   * In WGS, quality metrics (coverage, duplication, base quality) suffice to monitor performance.

3. **Batch consistency is evaluated differently**

   * WGS studies rely on:

     * Coverage uniformity
     * Ti/Tv ratios
     * Concordance in replicates (if any)
     * Comparison to benchmarks or truth sets

---

## 🧩 In my case (multi-omics integration)...

### 🚫 I do **not** need to stratify or re-batch WGS if:

* I’m only calling variants once per sample (e.g., using `nf-core/sarek`), and batch structure doesn’t affect the pipeline.
* The WGS results (VCFs) are used downstream without batch-based normalization.
* WGS is used mainly for annotation, modeling, or integration (e.g., for variant-driven protein structure prediction).

➡️ *In my case*, **WGS batches became unbalanced after pre-filtering** (due to sample matching), but this doesn't impact variant calling.

---

### ✅ I *may* want to align WGS batches if:

* My filtered WGS sample set no longer reflects a balanced distribution across diagnosis/sex.
* I want to align all omics layers to avoid integration bias (e.g., for tools like MOFA, SNF, WGCNA).

---

## ✔️ Best practice for T + P + WGS integration:

* If RNA-seq and proteomics batches are artificial, I can map **WGS** samples to those batches based on shared participant/sample IDs.
* This is **not** for technical correction during variant calling — only to ensure consistency during integration.

---

### 🧠 Bottom line:

* ✅ No need to re-batch WGS for `sarek` or variant calling.
* ✅ Yes — assign the **same artificial batch labels** to WGS metadata **for integration purposes only**.
* ✅ Make sure WGS QC is passed (coverage, Ti/Tv, etc.).
* ❌ Don’t apply batch correction to WGS the same way as RNA/protein data.

---

## 📚 Evidence in Literature: Correcting Batch Effects in Multi-Omics

---

### **1. Ratio-Based Scaling with Reference Materials**

**Yu et al. (2023)**
*Correcting batch effects in large-scale multiomics studies using a reference-material-based ratio method.*
[Genome Biology, 24, 201](https://doi.org/10.1186/s13059-023-03047-z)

* Batch effects are **pervasive across omics layers** (transcriptomics, proteomics, metabolomics).
* Introduced by lab conditions, reagents, operators, etc., and are **unrelated to biological factors**.
* Can lead to **false positives/negatives**, **misleading results**, and **irreproducibility**.
* **Ratio-based scaling** using common **reference materials** enhances comparability across batches in **large-scale multi-omics** studies.

---

### **2. MultiBaC: Matrix Factorization for Multi-Omics**

**Ugidos et al. (2022)**
*MultiBaC: an R package to remove batch effects in multi-omic experiments.*
[Bioinformatics, 38(9), 2657–2658](https://doi.org/10.1093/bioinformatics/btac132)
[Bioconductor](https://www.bioconductor.org/packages/release/bioc/html/MultiBaC.html) | [GitHub](https://github.com/ConesaLab/MultiBaC)

* Most batch correction algorithms (**BECAs**) assume **known batches** and clean designs.
* Few methods correct for **unknown or latent sources of systematic noise**.
* In **multi-omic experiments**, batch effects often **confound with omic type effects**, complicating correction.
* **MultiBaC** addresses this using **matrix factorization**, separating biological signal from unwanted noise across modalities.

---

### **3. Limitations and Future Needs**

**Yu et al. (2024)**
*Assessing and mitigating batch effects in large-scale omics studies.*
[Genome Biology, 25, 254](https://doi.org/10.1186/s13059-024-03401-9)

* Batch effects reduce signal, introduce bias, and contribute to **non-reproducible or retracted studies**.
* Especially problematic in **longitudinal** or **multi-center** studies.
* Current tools vary widely in assumptions—**method selection remains a challenge** for non-experts.
* Most tools focus on **quantitative data**, leaving **qualitative omics** (e.g., splicing events, mutations) under-addressed.
* Emphasizes need for **novel correction methods for qualitative omics**.

---

### ✅ Takeaway:

* **Batch effects affect all omics layers**—transcriptomics, proteomics, metabolomics, and multi-omics integration.
* **Reference material-based methods** and tools like **MultiBaC** are effective, especially when omics are acquired asynchronously.
* There's a growing need for **robust tools that handle both known and unknown sources of variation**, and support **qualitative data correction**.

---
