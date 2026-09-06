import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

BASE_URL = "https://alsod.ac.uk"
GENE_LIST_URL = BASE_URL + "/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_gene_list():
    """Extract gene symbol, name, category, and detail link."""
    resp = requests.get(GENE_LIST_URL, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = soup.find_all("tr", class_="clickable-row")

    genes = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        gene_symbol = cells[1].get_text(strip=True)
        gene_name = cells[2].get_text(strip=True)
        category = cells[3].get_text(strip=True)

        # Extract link
        detail_path = row.get("data-href")
        if detail_path:
            detail_url = BASE_URL + detail_path + gene_symbol
        else:
            detail_url = None

        genes.append({
            "Gene symbol": gene_symbol,
            "Gene name": gene_name,
            "Category": category,
            "Detail URL": detail_url
        })

    return pd.DataFrame(genes)


def parse_gene_metadata(url):
    """Extract structured metadata from individual gene page."""
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    metadata = {}

    # ALSoD gene pages typically use definition tables
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                metadata[key] = value

    return metadata


if __name__ == "__main__":
    print("Fetching ALSoD gene list...")
    gene_df = get_gene_list()
    print(f"Found {len(gene_df)} genes")

    gene_df.to_csv("alsod_gene_list.csv", index=False)
    print("Saved alsod_gene_list.csv")

    print("Fetching per-gene metadata...")

    metadata_records = []

    for i, row in gene_df.iterrows():
        symbol = row["Gene symbol"]
        url = row["Detail URL"]

        if not url:
            continue

        print(f"[{i+1}/{len(gene_df)}] Processing {symbol}")

        try:
            metadata = parse_gene_metadata(url)
            metadata["Gene symbol"] = symbol
            metadata_records.append(metadata)
            time.sleep(1)  # polite delay
        except Exception as e:
            print(f"Failed for {symbol}: {e}")

    metadata_df = pd.DataFrame(metadata_records)

    metadata_df.to_csv("alsod_gene_metadata.csv", index=False)
    print("Saved alsod_gene_metadata.csv")
