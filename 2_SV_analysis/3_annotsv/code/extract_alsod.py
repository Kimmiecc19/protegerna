import requests
import pandas as pd
from bs4 import BeautifulSoup

URL = "https://alsod.ac.uk/"

headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(URL, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

rows = soup.find_all("tr", class_="clickable-row")

data = []

for row in rows:
    cells = row.find_all("td")
    
    if len(cells) < 4:
        continue

    gene_symbol = cells[1].get_text(strip=True)
    gene_name = cells[2].get_text(strip=True)
    category = cells[3].get_text(strip=True)

    data.append({
        "Gene symbol": gene_symbol,
        "Gene name": gene_name,
        "Category": category
    })

df = pd.DataFrame(data)

print(f"Extracted {len(df)} genes")

df.to_csv("alsod_gene_list.csv", index=False)
print("Saved alsod_gene_list.csv")