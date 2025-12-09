#!/usr/bin/env python3
"""
Fetch tools from bio.tools based on multiple search queries and save to a JSON or TSV file.
Usage: fetch_biotools_final2025.py "query1,query2" output.tsv --tsv
"""
 
import csv
from importlib.resources.readers import remove_duplicates
import requests
import json
import argparse
import logging
import time
from typing import List, Dict, Any, Tuple
from requests.exceptions import RequestException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract topic terms (remove URI) and concatenate them into a single string
def extract_topics(topics: Any) -> str:
    """Extract topic terms and join them into a string."""
    if isinstance(topics, list):
        return ', '.join(str(topic.get("term", "")) for topic in topics if isinstance(topic, dict))
    return str(topics)

# Function to extract documentation URL
def extract_documentation(documentation: Any) -> str:
    """Extract all documentation URLs and join into a string."""
    if isinstance(documentation, list):
        urls = [doc.get("url", "") for doc in documentation if isinstance(doc, dict) and doc.get("url")]
        return ', '.join(urls)
    return str(documentation)

# Function to extract publication details
def extract_publications(publications):
    extracted = []
    if isinstance(publications, list):
        for pub in publications:
            if isinstance(pub, dict):
                metadata = pub.get("metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {}
                raw_date = metadata.get("publicationYear") or metadata.get("date", "")
                date_list = []
                if isinstance(raw_date, list):
                    date_list = [str(d) for d in raw_date]
                elif isinstance(raw_date, str):
                    date_list = [raw_date]
                elif raw_date:
                    date_list = [str(raw_date)]
                # Always extract all metadata fields if DOI is present
                if pub.get("doi", ""):
                    citation_count = metadata.get("citationCount", "")
                    if citation_count == 0:
                        citation_count = 0
                    elif not citation_count:
                        citation_count = ""
                    extracted.append({
                        "doi": pub.get("doi", ""),
                        "title": metadata.get("title", ""),
                        "abstract": metadata.get("abstract", "").replace('\n', ' ') if isinstance(metadata.get("abstract", ""), str) else "",
                        "date": [d[:4] for d in date_list if len(d) >= 4],
                        "citation_count": citation_count
                    })
    return extracted

# Function to join all list elements into a string
def safe_join(lst: Any) -> str:
    """Join all list elements into a string."""
    if isinstance(lst, list):
        return ', '.join(str(item) for item in lst)
    return str(lst)

# Function to fetch bio.tools tools based on a query
def fetch_biotools(query: str, max_retries: int = 3, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch bio.tools tools using API based on a query, with retries and timeout."""
    url = "https://bio.tools/api/tool/"
    params = {"q": query, "format": "json", "page_size": 150}
    tool_ids = set()
    all_tools = []
    page = 1

    while True:
        try:
            params["page"] = page
            response = requests.get(url, params=params)
            response.raise_for_status()
        except RequestException as e:
            logging.error(f"Error: Failed to fetch data for page {page}: {e}")
            break

    #    TODO: try logging.info(f"All tools found up to page {page}")

        data = response.json()
        tools_on_page = data.get("list", [])

        if not tools_on_page:
            break

        for tool in tools_on_page:
            biotools_id = tool.get("biotoolsID")
            if biotools_id in tool_ids:
                continue
            tool_ids.add(biotools_id)

            publications = extract_publications(tool.get("publication", []))
            def safe_int(val):
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0
            total_citations = sum(safe_int(pub.get("citation_count", 0)) for pub in publications)

            # Helper to robustly extract year from a date string
            def extract_year(date_str):
                if not date_str:
                    return ""
                for part in str(date_str).split("-"):
                    if part.isdigit() and len(part) == 4:
                        return part
                # fallback: first 4 digits if present
                digits = ''.join([c for c in str(date_str) if c.isdigit()])
                return digits[:4] if len(digits) >= 4 else ""

            added_year = extract_year(tool.get("additionDate", ""))
            updated_year = extract_year(tool.get("lastUpdate", ""))

            # Publication years and citations as comma-separated lists, handle missing values
            # Publication fields: always output whatever is available, field by field
            pub_dois = ', '.join(pub.get("doi", "") for pub in publications if pub.get("doi", ""))
            pub_titles = ', '.join(pub.get("title", "") for pub in publications if pub.get("title", ""))
            pub_abstracts = ', '.join(pub.get("abstract", "") for pub in publications if pub.get("abstract", ""))
            pub_years = ', '.join(
                ', '.join(str(y) for y in pub.get("date", []) if y) for pub in publications if pub.get("date", [])
            )
            pub_citations = ', '.join(str(pub.get("citation_count", "")) for pub in publications if pub.get("citation_count", "") not in [None, ""])

            filtered_tool = {
                "Name": tool.get("name", ""),
                "Homepage": tool.get("homepage", ""),
                "Description": tool.get("description", "").replace('\n', ' '),
                "Version": safe_join(tool.get("version", [])),
                "Tool Type": safe_join(tool.get("toolType", [])),
                "Topic": extract_topics(tool.get("topic")),
                "Publication DOI": pub_dois,
                "Publication Title": pub_titles,
                "Publication Abstract": pub_abstracts,
                "Publication Date": pub_years,
                "Publication Citations": pub_citations,
                "Documentation": extract_documentation(tool.get("documentation", [])),
                "Operating System": safe_join(tool.get("operatingSystem", [])),
                "Language": safe_join(tool.get("language", [])),
                "Accessibility": safe_join(tool.get("accessibility", [])),
                "License": safe_join(tool.get("license", [])),
                "Added": added_year,
                "Updated": updated_year,
                "Total Citations": total_citations if total_citations > 0 else ""
            }

            all_tools.append(filtered_tool)

        page += 1  # moves to next page

    return all_tools

# Function to remove duplicate tools based on homepage and documentation URLs
def remove_duplicates(tools):
    seen = set()
    deduped = []
    for tool in tools:
        homepage = tool.get("Homepage", "")
        documentation = tool.get("Documentation", "")
        key = (homepage.strip().lower(), documentation.strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(tool)
    return deduped

def flatten_publication_field(publications, field):
    values = []
    for pub in publications:
        val = pub.get(field, "")
        if isinstance(val, list):
            val = ', '.join(str(v) for v in val)  # commas for internal list
        values.append(str(val))
    return ', '.join(values)  # commas to join multiple publications

# Function to save the fetched tools to a JSON file
def save_to_file(tools: List[Dict[str, Any]], filename: str, as_tsv: bool = False) -> None:
    """Save the fetched tools to a JSON or TSV file."""
    try:
        if as_tsv:
            # Flatten publications for TSV output (show count and DOIs)
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    "Name", "Homepage", "Documentation", "Description", "Tool Type", "Topic", "Language", "Operating System",
                    "Version", "Accessibility", "License", "Publication DOI", "Publication Title", "Publication Abstract", "Publication Date", "Publication Citations", "Total Citations", "Added", "Updated"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()
                for tool in tools:
                    writer.writerow(tool)
            logging.info(f"Data saved to {filename} (TSV)")
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tools, f, indent=4)
            logging.info(f"Data saved to {filename} (JSON)")
    except IOError as e:
        logging.error(f"Error: Could not write to file {filename}: {e}")

# Main function to parse arguments and execute the script
def main() -> None:
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(description='Fetch tools from bio.tools for multiple queries.')
    parser.add_argument('queries', type=str, help='Comma-separated list of search queries enclosed by "".')
    parser.add_argument('output', type=str, help='The output file (JSON or TSV).')
    parser.add_argument('--tsv', action='store_true', help='Save output as TSV instead of JSON.')
    args = parser.parse_args()
    
    all_tools = []
    queries = [q.strip() for q in args.queries.split(',') if q.strip()]
    for query in queries:
        logging.info(f"Fetching results for: {query}")
        tools = fetch_biotools(query)
        logging.info(f"Found {len(tools)} tools for query: '{query}'")
        if not tools:
            logging.warning(f"No results found for query: '{query}'")
        all_tools.extend(tools)

    # Remove duplicates before saving
    deduped_tools = remove_duplicates(all_tools)
    save_to_file(deduped_tools, args.output, as_tsv=args.tsv)
    logging.info(f"Total {len(deduped_tools)} unique tools saved for queries: {args.queries}")

if __name__ == "__main__":
    main()
