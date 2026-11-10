from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------
# CONFIG
# ------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
# Inputs: written by 00_general/01_filtering_matching_patients/03_split_bcd_btc.R
COHORT_DIR = REPO / "00_general" / "01_filtering_matching_patients"
BDC_FILE = COHORT_DIR / "stratify_bdc.csv"
BTC_FILE = COHORT_DIR / "stratify_btc.csv"
N_PER_BATCH = 50
# Outputs
OUT_DIR = HERE / "01_results_stratified_batches" / "batch_files"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR = HERE / "01_results_stratified_batches" / "batch_figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PROT = OUT_DIR / "proteomic_batches.csv"
OUTPUT_TRANS = OUT_DIR / "transcriptomic_batches.csv"
SUMMARY_REPORT = OUT_DIR / "batch_summary_report_17062025.csv"
OUTPUT_PROT_BTC = OUT_DIR / "proteomic_batches_BTC.csv"
OUTPUT_TRANS_BTC = OUT_DIR / "transcriptomic_batches_BTC.csv"

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
plt.savefig(FIG_DIR / "batch_assignments.png")
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
plt.savefig(FIG_DIR / "sampletype_batch_distribution.png")
plt.close()
print("Saved: sampletype_batch_distribution.png")

# Heatmap: artificial_batch × diagnosis × sex
pivot = final.groupby(["artificial_batch", "diagnosis", "sex"]).size().unstack(fill_value=0)
plt.figure(figsize=(12, 6))
sns.heatmap(pivot, annot=True, fmt="d", cmap="Blues")
plt.title("Batch Composition by Diagnosis and Sex")
plt.tight_layout()
plt.savefig(FIG_DIR / "batch_heatmap_diagnosis_sex.png")
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
plt.savefig(FIG_DIR / "batch_diagnosis_proportion.png")
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
plt.savefig(FIG_DIR / "batch_sex_proportion.png")
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
plt.savefig(FIG_DIR / "batch_omic_proportion.png")
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
plt.savefig(FIG_DIR / "batch_shipment_proportion_stacked.png")
plt.close()
print("Saved: batch_shipment_proportion_stacked.png")

# Relative proportions by sequence batch in each batch
grouped_seq_batch = final.groupby(["artificial_batch", "seq_batch"]).size()
prop_seq_batch = grouped_seq_batch.groupby(level=0).transform(lambda x: x / x.sum())
prop_seq_batch_df = grouped_seq_batch.to_frame("count")
prop_seq_batch_df["proportion"] = prop_seq_batch
prop_seq_batch_df = prop_seq_batch_df.reset_index()

# Pivot to get seq_batch as columns (proportions) and plot
seq_batch_pivot = prop_seq_batch_df.pivot(index="artificial_batch", columns="seq_batch", values="proportion")
seq_batch_pivot = seq_batch_pivot.fillna(0).sort_index()
seq_batch_pivot.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="tab20")
plt.title("Sequence Batch Composition per Batch")
plt.ylabel("Proportion")
plt.xlabel("Artificial Batch")
plt.legend(title="Sequence Batch", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.savefig(FIG_DIR / "batch_seq_batch_proportion_stacked.png")
plt.close()
print("Saved: batch_seq_batch_proportion_stacked.png")



# Relative proportions by sex in each seq_batch
grouped_sex = final.groupby(["seq_batch", "sex"]).size()
prop_sex = grouped_sex.groupby(level=0).transform(lambda x: x / x.sum())
prop_sex_df = grouped_sex.to_frame("count")
prop_sex_df["proportion"] = prop_sex
prop_sex_df = prop_sex_df.reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(data=prop_sex_df, x="seq_batch", y="proportion", hue="sex")
plt.title("Relative Sex Composition per Sequence Batch")
plt.ylabel("Proportion")
plt.xlabel("Sequence Batch")
plt.tight_layout()
plt.savefig(FIG_DIR / "seq_batch_sex_proportion.png")
plt.close()
print("Saved: seq_batch_sex_proportion.png")


# Relative proportions by diagnosis in each seq_batch
grouped_diag = final.groupby(["seq_batch", "diagnosis"]).size()
prop_diag = grouped_diag.groupby(level=0).transform(lambda x: x / x.sum())
prop_diag_df = grouped_diag.to_frame("count")
prop_diag_df["proportion"] = prop_diag
prop_diag_df = prop_diag_df.reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(data=prop_diag_df, x="seq_batch", y="proportion", hue="diagnosis")
plt.title("Relative Diagnosis Composition per Sequence Batch")
plt.ylabel("Proportion")
plt.xlabel("Sequence Batch")
plt.tight_layout()
plt.savefig(FIG_DIR / "seq_batch_diagnosis_proportion.png")
plt.close()
print("Saved: seq_batch_diagnosis_proportion.png")

grouped_seq_condition = (
    final.groupby(["artificial_batch", "seq_batch", "diagnosis"])
    .size()
    .reset_index(name="count")
)

grouped_seq_condition["diagnosis_group"] = np.where(
    grouped_seq_condition["diagnosis"].astype(str).str.contains("ALS", case=False, na=False),
    "ALS",
    "Other",
)

plot_data = (
    grouped_seq_condition.groupby(["artificial_batch", "seq_batch", "diagnosis_group"])["count"]
    .sum()
    .reset_index()
)

seq_batches = sorted(plot_data["seq_batch"].dropna().unique(), key=lambda value: str(value))
artificial_batches = sorted(plot_data["artificial_batch"].dropna().unique())
diagnosis_groups = ["ALS", "Other"]
diagnosis_colors = {"ALS": "#d62728", "Other": "#1f77b4"}

fig, ax = plt.subplots(figsize=(14, 7))
bar_width = 0.8 / max(len(seq_batches), 1)

for seq_index, seq_batch in enumerate(seq_batches):
    seq_subset = plot_data[plot_data["seq_batch"] == seq_batch]
    batch_positions = np.arange(len(artificial_batches)) + (seq_index - (len(seq_batches) - 1) / 2) * bar_width

    for diagnosis_group in diagnosis_groups:
        heights = []
        for artificial_batch in artificial_batches:
            matching = seq_subset[
                (seq_subset["artificial_batch"] == artificial_batch)
                & (seq_subset["diagnosis_group"] == diagnosis_group)
            ]
            heights.append(float(matching["count"].iloc[0]) if not matching.empty else 0.0)

        if diagnosis_group == "ALS":
            ax.bar(
                batch_positions,
                heights,
                width=bar_width,
                color=diagnosis_colors[diagnosis_group],
                label=diagnosis_group if seq_index == 0 else None,
            )
        else:
            previous_heights = [
                float(
                    seq_subset[
                        (seq_subset["artificial_batch"] == artificial_batch)
                        & (seq_subset["diagnosis_group"] == "ALS")
                    ]["count"].iloc[0]
                )
                if not seq_subset[
                    (seq_subset["artificial_batch"] == artificial_batch)
                    & (seq_subset["diagnosis_group"] == "ALS")
                ].empty
                else 0.0
                for artificial_batch in artificial_batches
            ]
            ax.bar(
                batch_positions,
                heights,
                width=bar_width,
                bottom=previous_heights,
                color=diagnosis_colors[diagnosis_group],
                label=diagnosis_group if seq_index == 0 else None,
                alpha=0.75,
            )

ax.set_xticks(np.arange(len(artificial_batches)))
ax.set_xticklabels(artificial_batches)
ax.set_xlabel("Artificial Batch")
ax.set_ylabel("Count")
ax.set_title("Seq Batch Distribution per Artificial Batch, Colored by ALS vs Other")
ax.legend(title="Diagnosis Group", bbox_to_anchor=(1.02, 1), loc="upper left")
fig.tight_layout()
fig.savefig("seq_batch_diagnosis_distribution_facet.png", bbox_inches="tight")
plt.close(fig)
print("Saved: seq_batch_diagnosis_distribution_facet.png")