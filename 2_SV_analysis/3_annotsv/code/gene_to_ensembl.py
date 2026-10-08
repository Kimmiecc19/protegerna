import requests
import pandas as pd
import time

INPUT_FILE = "alsod_gene_list.csv"
OUTPUT_FILE = "alsod_gene_transcript_map_gencode_v46.csv"

# Ensembl Release 112 (July 2023)
ENSEMBL_SERVER = "https://jul2023.rest.ensembl.org"


headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_gene_transcripts(symbol):
    endpoint = f"/lookup/symbol/homo_sapiens/{symbol}"
    params = {"expand": "1"}

    response = requests.get(
        ENSEMBL_SERVER + endpoint,
        headers=headers,
        params=params
    )

    if not response.ok:
        return None, None, None

    data = response.json()

    gene_id = data.get("id")
    canonical = None
    all_transcripts = []

    for tx in data.get("Transcript", []):
        all_transcripts.append(tx["id"])
        if tx.get("is_canonical") == 1:
            canonical = tx["id"]

    return gene_id, all_transcripts, canonical


def main():
    df = pd.read_csv(INPUT_FILE)

    gene_ids = []
    tx_ids = []
    canonical_ids = []

    for i, row in df.iterrows():
        symbol = row["Gene symbol"]
        print(f"[{i+1}/{len(df)}] {symbol}")

        gene_id, transcripts, canonical = get_gene_transcripts(symbol)

        gene_ids.append(gene_id)
        tx_ids.append(";".join(transcripts) if transcripts else None)
        canonical_ids.append(canonical)

        time.sleep(0.2)

    df["Ensembl_Gene_ID_v112"] = gene_ids
    df["All_Transcripts_v112"] = tx_ids
    df["Canonical_Transcript_v112"] = canonical_ids

    df.to_csv(OUTPUT_FILE, index=False)
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
