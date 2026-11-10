from pathlib import Path

import pandas as pd

# Configuration: inputs and outputs are in 01_results_stratified_batches/batch_files/ (written by 01a)
OUT_DIR = Path(__file__).resolve().parent / "01_results_stratified_batches" / "batch_files"
prot_file = OUT_DIR / "proteomic_batches_BTC.csv"
trans_file = OUT_DIR / "transcriptomic_batches_BTC.csv"

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

prot_stats_all.to_csv(OUT_DIR / "proteomic_batch_stats_all.csv")
prot_stats_bdc.to_csv(OUT_DIR / "proteomic_batch_stats_bdc.csv")
prot_stats_btc.to_csv(OUT_DIR / "proteomic_batch_stats_btc.csv")

trans_stats_all = get_batch_stats(trans_df, "Transcriptomic")
trans_stats_bdc = get_batch_stats(trans_df, "Transcriptomic", source="BDC")
trans_stats_btc = get_batch_stats(trans_df, "Transcriptomic", source="BTC")

trans_stats_all.to_csv(OUT_DIR / "transcriptomic_batch_stats_all.csv")
trans_stats_bdc.to_csv(OUT_DIR / "transcriptomic_batch_stats_bdc.csv")
trans_stats_btc.to_csv(OUT_DIR / "transcriptomic_batch_stats_btc.csv")

# Get and save validation tables
prot_validation = get_validation_tables(prot_df, "Proteomic")
for name, df in prot_validation.items():
    df.to_csv(OUT_DIR / f"proteomic_{name}.csv")

trans_validation = get_validation_tables(trans_df, "Transcriptomic")
for name, df in trans_validation.items():
    df.to_csv(OUT_DIR / f"transcriptomic_{name}.csv")
