# Stratified sampling for AnswerALS data

## Generating artificial batches for multi-omics data to reduce downstream batch effects

First generated: 12/05/2025

## Sample mapping of AnswerALS data

* This information is according to the AALS sample mapping information on Neuromine (<https://stdataportalprod.blob.core.windows.net/wp-media/Sample-Mapping-README.txt>).

### Column description of Sample-Mapping-File (not including all)

1. Participant ID: A unique identifier for the individual from whom the sample was obtained. This ID links the sample to the participant in a way that protects the individual's privacy.
2. Sample ID: A unique identifier assigned to the sample. This ID facilitates tracking the sample through its lifecycle, from collection to analysis.
3. GUID-Batch: A composite identifier combining a Globally Unique Identifier (GUID) with a batch number, aimed at improving the traceability of sample batches.
4. Batch #: The number assigned to a specific batch of samples differentiated together. Batch numbers aid in managing quality control and traceability. (BTC or BDC)
5. Shipment: Contains details regarding the shipment of samples. Samples are sent in groups of batches, typically 3 batches per shipment, and this column identifies the sequence and grouping of samples sent out.

### Recommended usage of Sample-Mapping-File

* The mapping file serves as a comprehensive tool for maintaining detailed records, ensuring each sample's traceability, and supporting quality control throughout various research phases.

1. Pre-processing Step: Before starting the analysis, use the sample mapping file to categorize my data according to the batch number. This involves segregating the cell line differentiation samples based on their batch and identifying the corresponding batch control samples.

2. Normalization and Correction: Utilize statistical methods or software tools that are designed to adjust for batch effects. Methods such as ComBat (from the sva package in R) or Limma can be applied, using the batch information from the mapping file to correct the data. The goal is to minimize the differences between batches that are not related to the biological variables of interest.

3. Quality Control: Use the mapping file to perform quality control checks. For example, ensure that batch controls behave as expected across different batches. Any inconsistency in control samples might indicate a problem with the batch effect correction process.

4. Data Analysis: Proceed with the analysis (e.g., differential expression analysis, clustering, or pathway analysis) after batch effect correction. The corrected dataset should reflect true biological variations rather than artifacts introduced by batch effects.

5. Validation and Interpretation: Finally, validate findings by checking if the observed patterns or differences remain consistent across batches after correction. This step is crucial to confirm that the results are biologically meaningful and not influenced by batch-related variations.

### Batch Technical Control

* **CTRL-NEUEU392AE8** was used as a technical batch control for transcriptomics and proteomics data.

* Therefore, AALS has MANY samples mapped to CTRL-NEUEU392AE8.

1. All CTRL-NEUEU392AE8 samples labelled BTC or BTC2 in col Batch number are the Batch Technical Controls for the experiment.

   * 2AE8iCTR-n6 line served as BTC and was produced in bulk Oct-Dec 2018. The same clone was used for bulk differentiation BTC2 in June-July 2021. Each OMICs lab receives a BTC or BTC2 pellet from these differentiations with each shipment to run with all the other vials in the shipment. This controls for Omics assay-specific variability; since BTC pellets were produced simultaneously with an SOP, a given assay should return the same results for any BTC pellet.

2. All CTRL-NEUEU392AE8 samples with an integer value in col Batch number are the Batch Differentiation Controls (BDC)

   * 2AE8iCTR-n6 line is also differentiated with every group of differentiations. This controls for inter-batch variability in differentiation. This line is thawed, expanded, differentiated, and pelleted in addition to the ALS/CTR lines in each batch. Each OMICs lab receives a BDC pellet and ALS/CTR pellets for each differentiation batch.

### NOTE: Strong batch effects identified

52 samples from release one have been found to have strong batch effects. The extent to which these samples vary from the subsequent data has led us (AnswerALS) to advise users not to utilize these samples in their analyses.

## Summary of AnswerALS omics data

Total AnswerALS cohort (as of 30 May 2025):

* 1269 Participants in total
* 939 Genomics
* 499 Proteomics
* 650 Transcriptomics

* From these 1269 participants, I performed sample matching to filter the data.
* Briefly, participants were included if they had all three omics (WGS, RNA-Seq, and proteomic) data available.
* All other participants were excluded.
* Included participants who were identified as having strong batch effects in their proteomics data, were also excluded.

## Merge matched samples and Sample-Mapping

1. 347 unique participants in Sample-Mapping-File (347 for T and 347 for P)
2. Total participants (BTC and BDC for T and P): 991
3. BTC: 67 (for CTRL-NEUEU392AE8) (T X 34,P X 33)
4. BDC: 924 (991-67) (total including CTRL-NEUEU392AE8) (T X 458,P X 466)
5. BDC: 186 for CTRL-NEUEU392AE8 (T X 93,P X 93)
6. There are two BTC samples per shipment (1X T and 1X P) - 32 shipments total with 8 X Backup Reprocessing shipment 1
7. Total number batches - 93 + BTC + BTC2

TODO: How does it go from over 450 to 347??

Steps taken thus far (May 2025):

  1. Filter participants as previously. Participants must have G AND T AND P
  2. Merge the filtered participant file with the dataportal file (too add clinical information)
  3. From the sample mapping csv -> Remove all epigenomic sample IDs
  4. Merge the resulting participant file with the filtered sample_mapping file (keeping only filtered participants from before)
  5. Generate csv with each participant's T and P sample_id (and metadata)

### TODO: Why are there multiple files for certain participants where only file name differs?

## Creating artificial batches

Since my participant data was filtered post hoc (after sequencing), I now have unbalanced batch sizes. Before filtering the batches were roughly even. After filtering, the batch sizes range from 2 to 14 for example.

## Method chosen: stratified sampling - StratifiedKFold

URL: <https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedKFold.html> AND <https://www.geeksforgeeks.org/stratified-k-fold-cross-validation/>

Stratified sampling helps ensure that biological variation is not mistaken for batch variation.

Useful when...

1. I have heterogeneous biological classes (e.g. diagnosis, sex) and want to ensure each analysis batch maintains the same class proportions.
2. I want to avoid confounding biological effects with technical variation.

## Objective

To create balanced batches (for transcriptomics and proteomics samples) from an unbalanced, pre-filtered dataset. This will...

1. Minimize the batch effects during pre-processing
2. Maintain biological variation (that I am interested in such as sex and diagnosis)
3. Will help with multi-omics integration later on  

Therefore, I need to rebalance the data with stratified sampling, using the batch # as a covariate.

NOTE: While unbalanced, the original batches may still have meaningful technical variance (e.g., same protocol/shipment day). If I ignore this, I may introduce artificial variability along with biological variability

### Chosen method - StratifiedKFold Cross-validation

StratifiedKFold is a variation of standard K-Fold cross-validation that is specifically designed to handle unbalanced class distributions. It ensures that each fold maintains the same proportion of class labels as in the full dataset.

This makes it a less biased and more reliable method for model evaluation, especially when working with classification tasks where certain classes are underrepresented.

### Why use StratifiedKFold?

* Class Balance Preserved: Each fold contains roughly the same percentage of each class label as the full dataset.
* Prevents Bias: Avoids folds with missing or underrepresented classes, which can lead to inaccurate or biased models.
* Better Generalization: Ensures the model sees representative examples of each class during training and testing.
* Improved Evaluation: Produces more consistent and trustworthy performance metrics compared to random K-Fold.

> In contrast, standard K-Fold splits data randomly, which may result in uneven class distributions—especially harmful in unbalanced datasets.

### How does it work in general?

1. Group by Class
   Samples are first grouped according to their class label (e.g., Diagnosis).

2. Divide Each Class into K Parts
   Each class's samples are split into *K* approximately equal-sized subsets (strata), even if the class count isn’t perfectly divisible.

3. Create Stratified Folds
   Each fold is formed by combining one subset (stratum) from each class. This preserves the class distribution in every fold.

4. Cross-Validation Iterations
   Perform *K* iterations: in each, one fold is used as the validation set and the remaining *K-1* folds are used for training.

   * It’s more reproducible, especially when shuffle=True and random_state is set.

### An easy example

If we are building a model to classify images of cats and dogs and we have a data set that’s comprised of 75% cat images and 25% dog images, using stratified kfold cross valuation will mean that each fold we create remains close to this 75/25 ratio. (<https://www.analyseup.com/python-machine-learning/stratified-kfold.html>)

Therefore, stratified-kfold keeps consisten ratios of classes (in each fold) as it is in the orignal full dataset.

### In my case

* StratifiedKFold gives me clean batch splits across the full dataset.
* It allows me to maintain proportional (unbiased) representation of diagnosis and sex in each artificial batch.
* It’s more reproducible (because I used a random_state)

## Choosing a batch size

### Factors to consider

1. Computational Resources
More CPUs/GPUs or a large cluster → run more samples in fewer batches -> like CHPC

2. Parallelization Limits
nf-core handles parallelization well, but it's dependent on:
How many concurrent jobs are currently running or can be run using a scheduler (CHPC PBS)

3. Pipeline Runtime and Storage
Running too many samples together may cause I/O bottlenecks or fill up disk space since some intermediate files (BAMs) are large.

Important: since I am doing multi-omics integration, I need to try to align RNA-seq and proteomics batches so they're synchronized, to avoid introducing unnecessary variability.

Therefore, I must assign the same samples to matching batches across both omics layers.
This will help ensure that any downstream differences reflect biological variation rather than batch effects introduced by processing the omics separately (keeping batch effects low).

## What about Batch Technical Control?

### Purpose of BTC samples

* Reference samples (e.g. pooled controls, technical replicates)
* Used to assess technical variability, batch effects, and pipeline consistency

Not biologically meaningful on their own, but important for quality control (QC) and normalization

  1. Should not be included in the stratified sampling
    Don’t contribute to biological signal (they are from the same clone)
    Serve as QC benchmarks across batches
  2. Can be assigned to the artificial batches after stratification
  3. BTCs are excluded from downstream analyses (e.g. DGE) because
  Are not part of the biological hypothesis
  Can distort group comparisons due to their clone-specific behavior

## Include BTCs or exclude? - in my study context

## Reasons to include BTCs in nf-core pipelines

1. Quality Control & Consistency Checks to assess:

   * Mapping/variant calling consistency in sarek
   * Alignment/quantification consistency in rnaseq/quantms
   * Splice/fusion detection noise or artifacts in rnasplice/rnafusion
   * Useful for identifying batch-related drift or technical artifacts.

2. Normalization and Batch Correction

   * BTCs can anchor batch effect correction (using ComBat, limma, SVA etc.)
   * In proteomics, BTCs are critical for intensity normalization and missing value imputation.
   * In RNA-Seq, BTCs allow for modeling unwanted variation.

3. Pipeline Optimization

   * BTCs can highlight technical issues in pipelines (e.g. read quality, adapter contamination, missed junctions)
   * Allow for tuning parameters before processing participant samples.

## Reasons to exclude BTCs in nf-core pipelines

1. Computational Cost

   * Unnecessary resources spent on non-biological samples (compute time, storage).

2. Downstream Analysis Complexity

   * Confound clustering/PCAs if not handled properly
   * Skew differential expression or abundance if included as "samples" if not handled properly
   * Requires careful filtering/exclusion after preprocessing.

## What should I do then?

### Run BTCs through pipelines — but handle them separately

* Running through pipelines will support QC, normalization, and batch correction
* Must not be included in downstream biological analyses.

Include BTCs for:

* My nf-core pipelines (before integration)
* QC and batch correction

They can be used for:

* Plotting technical replicability across batches
* Calibrating thresholds for detection (e.g. fusions)
* Normalizing protein/RNA intensities across runs

BUT... They MUST be filtered before DE analysis, correlation, or multi-omics integration.

## During stratification then?

### Why should BTCs be included during stratification?

1. Maintains Batch Balance
   My stratification process aims to distribute samples across batches in a balanced way (e.g. by diagnosis, sex, sequencing batch). Excluding BTCs here could:

   * Lead to unbalanced batches
   * Undermine the ability to later correct for batch effects
   * Make downstream normalization less stable (especially for proteomics)

2. Technical Controls Are Essential for Batch Correction
   Many batch correction methods (e.g. ComBat, limma, RUV) benefit from having reference samples (like BTCs) in every batch.
   My current script (below) assigns BTCs in round-robin fashion eunsuring that BTCs are evenly spread, allowing robust estimation of batch effects later.

### Later on...after running nf-core pipelines

* I need to remove the BTCs before multi-omics integration (e.g. MOFA, SNF, WGCNA, etc.) or biological inference (e.g. correlation) to avoid contaminating the analysis with non-biological variance.

### Strategy

1. Have a csv with the following for T and P: participant, diagnosis, sex, is_BTC, shipment, sample_id (T/P)
2. Exclude BTCs from stratified sampling and add back after stratification (reassign based on shipment)
3. Stratification will be based on diagnosis and sex
4. Paired T and P sample_ids will be assigned the same artificial batch
5. Output: two csv files with matched artificial batches

Note: BTCs must be marked using a boolean column (is_BTC) with True or False
      shipment is used to map BTCs back to the same artificial batch as the rest of their shipment

## Assigning batches using stratification script  

Advantages of this method:

1. Stratification Level: Stratifies BDCs per participant, preserving omics
2. Preserves Multi-Omic links: both T and P samples for the same participant get the same batch
3. BTC handling: Balanced via round-robin
4. Stratification Features: Combines features from both omics with fallback
5. Flexibility: Easier to modify/scale for integration use cases

This script:

* Does stratified sampling on participants (BDC only) using StratifiedKFold.
* Ensures matched transcriptomic and proteomic samples get the same artificial batch.
* Assigns BTCs via round-robin to balance across batches.
* Creates summary reports.
* Generates visualizations of results.

## Output files

proteomic_with_batches.csv
transcriptomic_with_batches.csv
batch_summary_report.csv
proteomic_batches_BTC.csv
transcriptomic_batches_BTC.csv

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

## Validation of artificial batches

### What makes batches trustworthy

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

### Pros

1. Essential sanity check

   * Confirms that BDC (biological disease/control) and BTC (technical controls) samples are correctly split across batches.
   * Ensures stratification by diagnosis and sex is preserved, which is critical for downstream statistical power and avoiding bias.

2. Transparent batch structure

   * Helps document how artificial batches were created — important for reproducibility and debugging.
   * Makes it easier to explain my design decisions in methods sections, manuscripts, and presentations.

3. Catch early issues

   * Alerts I if a batch is unbalanced (e.g., only males or only ALS cases).
   * Flags if BTCs were not included in every batch, which could affect normalization or batch correction steps.

4. Reusable for multiple omics

   * Works across both transcriptomic and proteomic datasets.
   * Once templated, the script becomes a lightweight validation tool I can reuse for future studies.

5. Supports quality reporting

   * Easily exportable summaries that can go straight into supplementary tables or reports.

### Cons

1. Redundant if already validated upstream

   * If I've done detailed batch assignment and verified sample stratification during preprocessing (e.g., in R or Nextflow), this may feel redundant.

2. Doesn’t flag subtle imbalances

   * It won’t detect statistical imbalances (e.g., slight enrichment of males across all batches) unless I explicitly compute distributions or run tests.
   * Doesn’t check expression or intensity distributions — just metadata.

3. Scripting overhead

   * Adds another script to maintain, especially if file formats or column names change.
   * Needs consistent metadata formatting across omics, or it’ll break.

### Overall it is optional but can be worth it if

* I'm doing custom artificial batching, especially for multi-omics alignment (like in my use case).
* I plan to include this validation step in a manuscript, supplement, or pipeline audit.
* I want to proactively catch batch composition issues before integration or normalization.

### But what about my WGS data?

In most multi-omics studies, Whole Genome Sequencing data typically does not need to be batched in the same way as RNA-Seq or proteomics data. However, whether I should apply stratified sampling or batching to WGS depends on how I am using the WGS data and the context of my analysis.

### Why does WGS data have no BTC (Batch Technical Control)?

1. No per-assay variability like transcriptomics/proteomics

    WGS (especially germline variant calling) is generally more robust to batch effects because:

   * The assay is standardized and not highly dependent on reagent lots or instrument variability.
   * DNA sequences are stable and not influenced by dynamic biological states (unlike RNA or proteins).
   * Tools like GATK or nf-core/sarek are designed to handle large-scale variant calling in batches without the need for a technical control sample.

2. BTCs are used to monitor assay consistency, not biological variation

    In RNA-Seq and proteomics

   * BTCs help assess lab-specific processing noise.
   * In WGS, once DNA is extracted and sequenced, the results are generally consistent across runs, provided that quality control is enforced (e.g., coverage, base quality, duplication rate).

3. Cross-batch consistency is verified differently in WGS

    Instead of BTCs, WGS studies typically monitor:

   * Coverage statistics
   * Ti/Tv ratios
   * Variant call consistency in replicated samples (if available)
   * Concordance across pipelines or known truth sets/benchmarks

### In my case for multi-omics integration

**In most multi-omics studies**, **Whole Genome Sequencing (WGS)** data typically does **not** need to be batched in the same way as RNA-Seq or proteomics data. However, whether I should apply **stratified sampling or batching** to WGS depends on **how** I'm using the WGS data and the **context of my analysis**.

### I do not need to stratify or re-batch WGS data if

* I'm **only calling variants once per sample** (e.g., using `nf-core/sarek`), and my pipeline is **not sensitive to batch structure**.
* The **original batches are already balanced** and I'm using WGS results (e.g. VCFs) downstream without per-batch normalization. -> my batches are unbalanced because of pre-filtering (sample matching)
* I'm using WGS data mainly to annotate or interpret variation (e.g., for variant-driven protein modeling or integration), **not for differential analysis**.

### But... I may want to stratify/batch WGS data if

* My pre-filtered WGS samples no longer represent a balanced distribution of clinical variables across sequencing batches.
* I'm trying to **synchronize all omics layers** to prevent integration bias in tools like MOFA, SNF, etc.

### Best practice (multi-omics with T + P + WGS)

* If my **RNA-seq and proteomics batches are artificial**, it **may help to align WGS** into the same batch structure **for integration** — not for WGS pre-processing per se, but for consistency in **multi-omics correlation, modeling, or integration layers**.
* In this case, **map the WGS samples to the artificial `NewBatch`** using shared sample/subject IDs from T or P.

### Recommendation

I don't need to re-batch WGS data for variant calling (via `nf-core/sarek`).
But for **downstream integration and modeling**, I **should add the same `artificial batch` label** (from T or P) to the WGS metadata table so that it aligns during multi-omics integration.

* Therefore, I should ensure that my WGS data passes quality control, and then align it to my artificial batch labels ONLY for integration purposes — not for technical correction.

### Evidence in Literature

**Correcting batch effects in multi-omics:**

Yu, Y., Zhang, N., Mai, Y. et al. Correcting batch effects in large-scale multiomics studies using a reference-material-based ratio method. Genome Biol 24, 201 (2023). <https://doi.org/10.1186/s13059-023-03047-z>

Batch effects are notoriously common technical variations in multiomics data and may result in misleading outcomes if uncorrected or over-corrected. A plethora of batch-effect correction algorithms are proposed to facilitate data integration. However, their respective advantages and limitations are not adequately assessed in terms of omics types, the performance metrics, and the application scenarios.

Batch effects are notorious technical variations irrelevant to study factors of interests, but are common in transcriptomics, proteomics, metabolomics, and multiomics integration. Due to variation in experimental design, lab conditions, reagent lots, operators, and other non-biological factors, results from different batches may vary and result in misleading outcomes.

Batch effects can have a profound negative impact on study outcomes. On the one hand, the presence of batch-correlated variations can skew analysis and introduce large numbers of false-positive or false-negative findings, and even mislead conclusions.

On the other hand, systematic variations including batch effects have become one of the major causes of irreproducibility.

In summary, multiomics measurements are prone to batch effects, which, fortunately, can be effectively corrected by using ratio-based scaling of the multiomics data. Profiling common reference materials concurrently with study samples can enhance data comparability of multi-batch studies, especially for large-scale multiomics studies, helping the discovery and validation of omics-based biomarkers for precision medicine.

---

**MultiBaC package:**

Ugidos, M., Nueda, M. J., Prats-Montalbán, J. M., Ferrer, A., Conesa, A., & Tarazona, S. (2022). MultiBaC: an R package to remove batch effects in multi-omic experiments. Bioinformatics (Oxford, England), 38(9), 2657–2658. <https://doi.org/10.1093/bioinformatics/btac132>

Usually, BECAs require adequate experimental designs where the batch is known and not confounded with the effects of interest (treatment, dose, time point, etc.). However, there are few BECAs providing data corrected for systematic noise coming from an unknown source. This may happen when laboratory practices introduce an un-noticed bias that affects a subset of samples. While this variability behaves as a batch effect, it is not identified as such and therefore is invisible to many traditional BECAs. Another scenario not yet covered by BECAs is multi-omic experiments. When multi-omic datasets are created by combining different omics modalities obtained asynchronously, batch effects are confounded with the ‘omic type effect’, what hampers their removal from the data.

Uses matrix factorization

MultiBaC package is available on Bioconductor (<https://www.bioconductor.org/packages/release/bioc/html/MultiBaC.html>) and GitHub (<https://github.com/ConesaLab/MultiBaC.git>

---

**Mitigating batch effects:**

Yu, Y., Mai, Y., Zheng, Y. et al. Assessing and mitigating batch effects in large-scale omics studies. Genome Biol 25, 254 (2024). <https://doi.org/10.1186/s13059-024-03401-9>

Batch effects can introduce noise that can dilute biological signals, reduce statistical power, or even result in misleading, biased, or non-reproducible results. What is worse, batch effects can act as a paramount factor contributing to irreproducibility, resulting in retracted articles, invalidated research findings, and economic losses.

The challenges of batch effects are magnified in longitudinal and/or multi-center studies.

The third challenge is software and algorithm selection. There are various software packages and algorithms available for batch effect correction, each with different assumptions and limitations. Selecting the appropriate method for a specific dataset can be challenging, especially for non-experts.

Batch effects are not limited to quantitative omics data alone, but also affect qualitative data, such as mutations, alternative splicing events, RNA editing events, and so on. However, there is a lack of established methods to remove batch effects from qualitative data. This highlights the need for developing and validating new methods to correct batch effects in qualitative data to ensure the accuracy and reproducibility of the results.

---

## WGS data has no BTC (Batch Technical Control)

### Why WGS doesn’t need BTCs

**1. No per-assay variability like transcriptomics/proteomics**
WGS (especially germline variant calling) is generally **more robust** to batch effects because:

* The assay is standardized and **not highly dependent on reagent lots or instrument variability**.
* I'm measuring **DNA sequence**, which is stable and not influenced by dynamic biological states (unlike RNA or proteins).
* Tools like GATK or `nf-core/sarek` are designed to handle large-scale variant calling in batches **without the need for a technical control sample**.

**2. BTCs are used to monitor assay consistency**, not biological variation
In RNA-Seq and proteomics:

* BTCs (e.g., the 2AE8iCTR-n6 line) help assess **lab-specific processing noise**.
* In WGS, once DNA is extracted and sequenced, the results are generally **consistent across runs**, provided that quality control is enforced (e.g., coverage, base quality, duplication rate).

**3. Cross-batch consistency is verified differently in WGS**
Instead of BTCs, WGS projects typically monitor:

* **Coverage statistics**
* **Ti/Tv ratios**
* **Variant call consistency in replicated samples (if available)**
* **Concordance across pipelines or known truth sets**

---

### Summary

I do **not** need BTCs for WGS data. Just ensure that my WGS data passed **quality control**, and align it to my artificial batch labels **only for integration purposes** — not for technical correction.

---
