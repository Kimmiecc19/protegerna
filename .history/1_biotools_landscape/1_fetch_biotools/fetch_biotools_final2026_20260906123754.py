import csv
import requests
import json
import argparse
import hashlib
import logging
import platform
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from requests.exceptions import RequestException

API_PAGE_SIZE = 50  # bio.tools currently enforces a 50-record page maximum

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
    if lst is None:
        return ""
    if isinstance(lst, list):
        return ', '.join(str(item) for item in lst if item is not None)
    return str(lst)

def _concept_values(items: Any, key: str) -> Tuple[List[str], List[str]]:
    """Return EDAM term and URI values from input/output records."""
    terms: List[str] = []
    uris: List[str] = []
    if not isinstance(items, list):
        return terms, uris
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get(key, {})
        values = value if isinstance(value, list) else [value]
        for concept in values:
            if isinstance(concept, dict):
                if concept.get("term"):
                    terms.append(str(concept["term"]))
                if concept.get("uri"):
                    uris.append(str(concept["uri"]))
    return sorted(set(terms)), sorted(set(uris))

def extract_function_records(functions: Any, biotools_id: str, tool_name: str, query: str) -> List[Dict[str, Any]]:
    """Normalise bio.tools function objects without inventing functional labels."""
    if not isinstance(functions, list):
        return []
    rows: List[Dict[str, Any]] = []
    for function_index, function in enumerate(functions, start=1):
        if not isinstance(function, dict):
            continue
        operations = function.get("operation", [])
        operations = operations if isinstance(operations, list) else []
        inputs = function.get("input", []) if isinstance(function.get("input", []), list) else []
        outputs = function.get("output", []) if isinstance(function.get("output", []), list) else []
        input_data_terms, input_data_uris = _concept_values(inputs, "data")
        input_format_terms, input_format_uris = _concept_values(inputs, "format")
        output_data_terms, output_data_uris = _concept_values(outputs, "data")
        output_format_terms, output_format_uris = _concept_values(outputs, "format")
        operation_values = operations or [{}]
        for operation_index, operation in enumerate(operation_values, start=1):
            operation = operation if isinstance(operation, dict) else {}
            rows.append({
                "biotoolsID": biotools_id or "",
                "Name": tool_name,
                "Retrieval Query": query,
                "Function Index": function_index,
                "Operation Index": operation_index if operations else "",
                "Operation Term": operation.get("term", ""),
                "Operation URI": operation.get("uri", ""),
                "Input Data Terms": "; ".join(input_data_terms),
                "Input Data URIs": "; ".join(input_data_uris),
                "Input Format Terms": "; ".join(input_format_terms),
                "Input Format URIs": "; ".join(input_format_uris),
                "Output Data Terms": "; ".join(output_data_terms),
                "Output Data URIs": "; ".join(output_data_uris),
                "Output Format Terms": "; ".join(output_format_terms),
                "Output Format URIs": "; ".join(output_format_uris),
                "Input JSON": json.dumps(inputs, ensure_ascii=False, separators=(",", ":")),
                "Output JSON": json.dumps(outputs, ensure_ascii=False, separators=(",", ":")),
            })
    return rows

# Function to fetch bio.tools tools based on a query
#def fetch_biotools(query):
def fetch_biotools(query: str, max_retries: int = 3, timeout: int = 30) -> List[Dict[str, Any]]:
    """Fetch bio.tools tools using API based on a query, with retries and timeout."""
    url = "https://bio.tools/api/tool/"
    params = {"q": query, "format": "json", "page_size": API_PAGE_SIZE}
    tool_ids = set()
    all_tools = []
    page = 1
    records_received = 0
    expected_count = None
    effective_page_size = None
    previous_response_indicated_next = None

    session = requests.Session()
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    while True:
        response = None
        for attempt in range(1, max_retries + 1):
            try:
                params["page"] = page
                response = session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                break
            except RequestException as e:
                status_code = getattr(getattr(e, "response", None), "status_code", None)
                # bio.tools returns 404 when requesting a page beyond the last
                # page. Treat it as an end boundary only if the prior response
                # did not explicitly promise another page and no advertised
                # total remains outstanding.
                count_outstanding = expected_count is not None and records_received < expected_count
                if (status_code == 404 and page > 1 and records_received > 0
                        and previous_response_indicated_next is not True
                        and not count_outstanding):
                    logging.info(
                        "Completed query %r at API page boundary: %s records across %s page(s)",
                        query, records_received, page - 1,
                    )
                    return all_tools
                logging.warning(
                    "Query %r page %s attempt %s/%s failed: %s",
                    query, page, attempt, max_retries, e,
                )
                if attempt < max_retries:
                    time.sleep(min(2 ** (attempt - 1), 8))
        if response is None or not response.ok:
            raise RuntimeError(
                f"Incomplete retrieval: query={query!r}, page={page}, "
                f"failed after {max_retries} attempts"
            )

    #    TODO: try logging.info(f"All tools found up to page {page}")

        data = response.json()
        tools_on_page = data.get("list", [])

        if not tools_on_page:
            break

        records_received += len(tools_on_page)
        if effective_page_size is None:
            # bio.tools may enforce a server-side maximum smaller than the
            # requested page_size (currently often 50). Use the observed first
            # page size when detecting a genuinely short final page.
            effective_page_size = len(tools_on_page)
        try:
            expected_count = int(data.get("count")) if data.get("count") is not None else expected_count
        except (TypeError, ValueError):
            logging.warning("Query %r returned an invalid count value: %r", query, data.get("count"))

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
            raw_functions = tool.get("function", [])
            function_records = extract_function_records(raw_functions, biotools_id or "", tool.get("name", ""), query)
            operation_terms = sorted({r["Operation Term"] for r in function_records if r["Operation Term"]})
            operation_uris = sorted({r["Operation URI"] for r in function_records if r["Operation URI"]})

            # Publication years and citations as comma-separated lists, handle missing gracefully
            # Publication fields: always output whatever is available, field by field
            pub_dois = ', '.join(pub.get("doi", "") for pub in publications if pub.get("doi", ""))
            pub_titles = ', '.join(pub.get("title", "") for pub in publications if pub.get("title", ""))
            pub_abstracts = ', '.join(pub.get("abstract", "") for pub in publications if pub.get("abstract", ""))
            pub_years = ', '.join(
                ', '.join(str(y) for y in pub.get("date", []) if y) for pub in publications if pub.get("date", [])
            )
            pub_citations = ', '.join(str(pub.get("citation_count", "")) for pub in publications if pub.get("citation_count", "") not in [None, ""])

            filtered_tool = {
                "biotoolsID": biotools_id or "",
                "Bio.tools URL": f"https://bio.tools/{biotools_id}" if biotools_id else "",
                "Retrieval Query": query,
                "Retrieval Timestamp UTC": retrieval_timestamp,
                "Name": tool.get("name", ""),
                "Homepage": tool.get("homepage", ""),
                "Description": tool.get("description", "").replace('\n', ' '),
                "Version": safe_join(tool.get("version", [])),
                "Tool Type": safe_join(tool.get("toolType", [])),
                "Topic": extract_topics(tool.get("topic")),
                "Function Count": len(raw_functions) if isinstance(raw_functions, list) else 0,
                "Function Metadata Status": (
                    "Operation annotated" if operation_uris else
                    "Function present; operation missing" if function_records else
                    "Function metadata missing"
                ),
                "EDAM Operation Terms": "; ".join(operation_terms),
                "EDAM Operation URIs": "; ".join(operation_uris),
                "Function Metadata JSON": json.dumps(raw_functions, ensure_ascii=False, separators=(",", ":")),
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
                "Total Citations": total_citations if total_citations > 0 else "",
                "_function_records": function_records,
            }

            all_tools.append(filtered_tool)

        # bio.tools can return HTTP 404 for a page beyond the final paginator
        # page instead of returning an empty list. Stop using positive evidence
        # from the successful response so an unexpected mid-retrieval 404 still
        # raises the incomplete-retrieval error above.
        count_reached = expected_count is not None and records_received >= expected_count
        short_page = effective_page_size is not None and len(tools_on_page) < effective_page_size
        next_exhausted = "next" in data and not data.get("next")
        previous_response_indicated_next = bool(data.get("next")) if "next" in data else None
        if count_reached or short_page or next_exhausted:
            logging.info(
                "Completed query %r: %s API records received across %s page(s)%s",
                query, records_received, page,
                f" (API count={expected_count})" if expected_count is not None else "",
            )
            break

        page += 1  # moves to next page

    return all_tools

# Function to remove duplicate tools based on homepage or documentation URLs
def merge_query_provenance(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge repeat query hits by bio.tools' canonical identifier.

    Records without a biotoolsID are retained individually. Missing URLs are never
    treated as evidence that records are duplicates.
    """
    merged: Dict[str, Dict[str, Any]] = {}
    unresolved: List[Dict[str, Any]] = []
    for tool in tools:
        tool_id = str(tool.get("biotoolsID", "")).strip()
        if not tool_id:
            copy = dict(tool)
            copy["Retrieval Query Count"] = 1
            unresolved.append(copy)
            continue
        if tool_id not in merged:
            copy = dict(tool)
            copy["Retrieval Query Count"] = 1
            merged[tool_id] = copy
            continue
        current = merged[tool_id]
        queries = {
            q.strip()
            for q in (current.get("Retrieval Query", "") + ", " + tool.get("Retrieval Query", "")).split(",")
            if q.strip()
        }
        current["Retrieval Query"] = "; ".join(sorted(queries, key=str.lower))
        current["Retrieval Query Count"] = len(queries)
    return list(merged.values()) + unresolved

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
                    "biotoolsID", "Bio.tools URL", "Retrieval Query", "Retrieval Query Count", "Retrieval Timestamp UTC",
                    "Name", "Homepage", "Documentation", "Description", "Tool Type", "Topic",
                    "Function Count", "Function Metadata Status", "EDAM Operation Terms", "EDAM Operation URIs", "Function Metadata JSON",
                    "Language", "Operating System",
                    "Version", "Accessibility", "License", "Publication DOI", "Publication Title", "Publication Abstract", "Publication Date", "Publication Citations", "Total Citations", "Added", "Updated"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()
                for tool in tools:
                    writer.writerow({key: tool.get(key, "") for key in fieldnames})
            logging.info(f"Data saved to {filename} (TSV)")
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([{k: v for k, v in tool.items() if k != "_function_records"} for tool in tools], f, indent=4)
            logging.info(f"Data saved to {filename} (JSON)")
    except IOError as e:
        logging.error(f"Error: Could not write to file {filename}: {e}")

def file_md5(filename: str) -> str:
    digest = hashlib.md5()
    with open(filename, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def save_function_file(tools: List[Dict[str, Any]], filename: str) -> int:
    fieldnames = ["biotoolsID", "Name", "Retrieval Query", "Function Index", "Operation Index",
        "Operation Term", "Operation URI", "Input Data Terms", "Input Data URIs",
        "Input Format Terms", "Input Format URIs", "Output Data Terms", "Output Data URIs",
        "Output Format Terms", "Output Format URIs", "Input JSON", "Output JSON"]
    count = 0
    with open(filename, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for tool in tools:
            for row in tool.get("_function_records", []):
                copy = dict(row)
                copy["Retrieval Query"] = tool.get("Retrieval Query", copy.get("Retrieval Query", ""))
                writer.writerow({key: copy.get(key, "") for key in fieldnames})
                count += 1
    return count

def save_manifest(filename: str, function_filename: str, function_rows: int,
                  queries: List[str], raw_hits: int, tools: List[Dict[str, Any]]) -> None:
    manifest = {
        "pipeline": "bio.tools API retrieval",
        "script": __file__,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "api_endpoint": "https://bio.tools/api/tool/",
        "parameters": {"queries": queries, "requested_page_size": API_PAGE_SIZE,
                       "timeout_seconds": 30, "max_retries": 3},
        "counts": {"raw_query_hits": raw_hits, "unique_biotools_records": len(tools),
                   "normalised_function_operation_rows": function_rows},
        "outputs": {
            "tools": {"path": filename, "md5": file_md5(filename)},
            "functions": {"path": function_filename, "md5": file_md5(function_filename)},
        },
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "requests": requests.__version__,
        },
    }
    with open(filename + ".manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

# Main function to parse arguments and execute the script
def main() -> None:
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(description='Fetch tools from bio.tools for multiple queries.')
    parser.add_argument('queries', type=str, help='Comma-separated list of search queries enclosed by "".')
    parser.add_argument('output', type=str, help='The output file (JSON or TSV).')
    parser.add_argument('--tsv', action='store_true', help='Save output as TSV instead of JSON.')
    args = parser.parse_args()

    # Example: fetch_biotools_september2025.py "query1,query2" output.tsv --tsv
    
    all_tools = []
    queries = [q.strip() for q in args.queries.split(',') if q.strip()]
    for query in queries:
        logging.info(f"Fetching results for: {query}")
        tools = fetch_biotools(query)
        logging.info(f"Found {len(tools)} tools for query: '{query}'")
        if not tools:
            logging.warning(f"No results found for query: '{query}'")
        all_tools.extend(tools)

    # Merge repeat search hits using the registry's canonical identifier while
    # preserving every query that retrieved the tool.
    deduped_tools = merge_query_provenance(all_tools)
    save_to_file(deduped_tools, args.output, as_tsv=args.tsv)
    function_output = args.output + ".functions.tsv"
    function_rows = save_function_file(deduped_tools, function_output)
    save_manifest(args.output, function_output, function_rows, queries, len(all_tools), deduped_tools)
    logging.info(f"Total {len(deduped_tools)} unique tools saved for queries: {args.queries}")

if __name__ == "__main__":
    main()
