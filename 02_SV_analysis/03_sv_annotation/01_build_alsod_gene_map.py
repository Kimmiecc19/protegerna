"""Build the ALSoD gene list and its Ensembl gene/transcript map.

1. Scrape the ALSoD gene table (symbol, name, category, detail URL)
   -> alsod_gene_list.csv
2. Look up each symbol in Ensembl release 112 (May 2024; = GENCODE v46)
   -> alsod_gene_transcript_map_gencode_v46.csv  (input to 02_annotsv_prioritization.py)
3. Optional (--metadata): scrape each gene's ALSoD detail page
   -> alsod_gene_metadata.csv

Usage: python 01_build_alsod_gene_map.py [--out-dir DIR] [--metadata]
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ALSOD_URL = "https://alsod.ac.uk"
ENSEMBL_SERVER = "https://may2024.rest.ensembl.org"  # Ensembl 112; jul2023 would be release 110
ENSEMBL_RELEASE = "v112"


def fetch_html(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_gene_list():
    """Gene symbol, name, category and detail-page link for every ALSoD gene."""
    genes = []
    for row in fetch_html(ALSOD_URL + "/").find_all("tr", class_="clickable-row"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        symbol = cells[1].get_text(strip=True)
        detail_path = row.get("data-href")
        genes.append({
            "Gene symbol": symbol,
            "Gene name": cells[2].get_text(strip=True),
            "Category": cells[3].get_text(strip=True),
            "Detail URL": ALSOD_URL + detail_path + symbol if detail_path else None,
        })
    return pd.DataFrame(genes)


def ensembl_transcripts(symbol):
    """Return (gene ID, ';'-joined transcript IDs, canonical transcript) or Nones if not found."""
    response = requests.get(f"{ENSEMBL_SERVER}/lookup/symbol/homo_sapiens/{symbol}", params={"expand": "1"},
                            headers={"Content-Type": "application/json", "Accept": "application/json"})
    if not response.ok:
        return None, None, None
    data = response.json()
    transcripts = data.get("Transcript", [])
    canonical = next((tx["id"] for tx in reversed(transcripts) if tx.get("is_canonical") == 1), None)
    return data.get("id"), ";".join(tx["id"] for tx in transcripts) or None, canonical


def gene_page_metadata(url):
    """Two-column table rows from an ALSoD gene page, as {label: value}."""
    metadata = {}
    for table in fetch_html(url).find_all("table"):
        for row in table.find_all("tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) == 2:
                metadata[cols[0].get_text(strip=True)] = cols[1].get_text(strip=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--metadata", action="store_true", help="Also scrape per-gene ALSoD detail pages")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching ALSoD gene list...")
    genes = get_gene_list()
    genes.to_csv(args.out_dir / "alsod_gene_list.csv", index=False)
    print(f"Saved alsod_gene_list.csv ({len(genes)} genes)")

    lookups = []
    for i, symbol in enumerate(genes["Gene symbol"], 1):
        print(f"[{i}/{len(genes)}] Ensembl {symbol}")
        lookups.append(ensembl_transcripts(symbol))
        time.sleep(0.2)
    gene_map = genes.copy()
    for column, values in zip(["Ensembl_Gene_ID", "All_Transcripts", "Canonical_Transcript"], zip(*lookups)):
        gene_map[f"{column}_{ENSEMBL_RELEASE}"] = list(values)
    gene_map.to_csv(args.out_dir / "alsod_gene_transcript_map_gencode_v46.csv", index=False)
    print("Saved alsod_gene_transcript_map_gencode_v46.csv")

    if args.metadata:
        records = []
        for i, (symbol, url) in enumerate(zip(genes["Gene symbol"], genes["Detail URL"]), 1):
            if not url:
                continue
            print(f"[{i}/{len(genes)}] ALSoD page {symbol}")
            try:
                records.append({**gene_page_metadata(url), "Gene symbol": symbol})
                time.sleep(1)  # polite delay
            except Exception as error:
                print(f"Failed for {symbol}: {error}")
        pd.DataFrame(records).to_csv(args.out_dir / "alsod_gene_metadata.csv", index=False)
        print("Saved alsod_gene_metadata.csv")


if __name__ == "__main__":
    main()
