"""Fetch bio.tools records with auditable publication enrichment.
This script retrieves bio.tools records matching a query, extracts and normalises
publication metadata, and optionally enriches it with citation counts from
Europe PMC, Crossref, and Dimensions. The output includes a TSV file of all
publications, with one row per registry publication, and a TSV file of all tools,
with one row per tool, including aggregated publication counts and citation totals.

Note: 
Total Citations sums available counts once per distinct linked publication from
one selected source. 
Partial totals are flagged; unknown counts remain missing.
Distinct preprints and articles are retained.
Original registry entries are retained.
Duplicate identifiers are grouped within each tool, and conflicts are flagged.
See the .publications.tsv audit table and contribution fields.

Example usage:
    python fetch_biotools.py "query1,query2" output.tsv
    or use the run_fetch_biotools.sh script to fetch multiple queries and save to a single output file.
"""


# 1. Imports and API settings -------------------------------------------------

import argparse
import csv
import hashlib
import html
import json
import logging
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple
from urllib.parse import quote

import requests
from requests.exceptions import RequestException

API_PAGE_SIZE = 50  # bio.tools currently enforces a 50-record page maximum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 2. Registry metadata and publication normalisation --------------------------

def extract_topics(topics: Any) -> str:
    """Extract topic terms and join them into a string."""
    if isinstance(topics, list):
        return ', '.join(str(topic.get("term", "")) for topic in topics if isinstance(topic, dict))
    return str(topics)


def extract_documentation(documentation: Any) -> str:
    """Extract all documentation URLs and join into a string."""
    if isinstance(documentation, list):
        urls = [doc.get("url", "") for doc in documentation if isinstance(doc, dict) and doc.get("url")]
        return ', '.join(urls)
    return str(documentation)

def citation_count(value):
    """Missing/invalid counts are unknown, never zero."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def normalize_doi(value):
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
        "",
        str(value or "").strip(),
        flags=re.I).lower()


def plain_text(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", str(value or ""))).split())


def publication_metadata_status(publication):
    """Describe coverage of the title, abstract and publication date."""
    present = [bool(publication.get(field)) for field in ("title", "abstract", "date")]
    if all(present):
        return "complete"
    return "partial" if any(present) else "missing"


def extract_publications(publications, retrieved_at=""):
    """Keep every registry publication, including PMID/PMCID-only entries."""
    extracted = []
    for index, raw in enumerate(publications if isinstance(publications, list) else [], 1):
        publication = raw if isinstance(raw, dict) else {}
        metadata = publication.get("metadata") or {}
        metadata = metadata if isinstance(metadata, dict) else {}
        count = citation_count(metadata.get("citationCount"))
        date = metadata.get("date") or metadata.get("publicationYear") or ""
        if isinstance(date, list):
            date = "; ".join(str(item) for item in date)
        record = {
            "publication_index": index,
            "doi": normalize_doi(publication.get("doi")),
            "pmid": str(publication.get("pmid") or "").strip(),
            "pmcid": str(publication.get("pmcid") or "").strip().upper(),
            "type": publication.get("type") or [], "note": publication.get("note") or "",
            "version": publication.get("version") or "",
            "title": plain_text(metadata.get("title")),
            "abstract": plain_text(metadata.get("abstract")), "date": str(date),
            "biotools_citation_count": count,
            "biotools_retrieved_at_utc": retrieved_at,
            "dimensions_citation_count": None,
            "dimensions_status": "not_requested",
            "citation_count": count, "citation_source": "bio.tools" if count is not None else "",
            "citation_status": "available" if count is not None else "missing",
            "citation_retrieved_at_utc": retrieved_at if count is not None else "",
            "metadata_sources": {}, "lookups": [], "registry_publication": raw,
        }
        record["metadata_sources"] = {
            key: {"source": "bio.tools", "retrieved_at_utc": retrieved_at}
            for key in ("doi", "pmid", "pmcid", "title", "abstract", "date") if record[key]
        }
        record["metadata_status"] = publication_metadata_status(record)
        extracted.append(record)
    return extracted


# 3. Publication enrichment and persistent response cache ---------------------

class PublicationClient:
    """Exact identifier enrichment; bounded retries and a dated response cache.

    Europe PMC and Crossref supply bibliographic metadata only. Citation counts
    are never silently substituted from those providers. Dimensions is opt-in;
    its terms are at https://www.dimensions.ai/policies/terms/metrics/.
    """

    def __init__(self, cache_path=None, cache_days=1, timeout=30, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "biotools-publication-audit/1.0",
            "Accept": "application/json"})
        self.cache_path = Path(cache_path) if cache_path else None
        self.cache_days = cache_days
        self.timeout = timeout
        self.cache = {}
        self.last_request = 0.0
        if self.cache_path and self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if data.get("schema_version") == 1:
                    self.cache = data.get("responses", {})
            except (OSError, ValueError, AttributeError) as exc:
                logging.warning("Ignoring unreadable publication cache: %s", exc)

    def get(self, url, params=None):
        key = json.dumps([url, params], sort_keys=True)
        cached = self.cache.get(key)
        if isinstance(cached, dict):
            try:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["retrieved_at_utc"])).total_seconds()
                if 0 <= age < self.cache_days * 86400:
                    return cached
            except (KeyError, TypeError, ValueError):
                pass
        result = {"url": url, "params": params, "status": "error", "data": {}}
        for attempt in range(3):
            time.sleep(max(0, 0.2 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            retry_after = 0
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                result["http_status"] = response.status_code
                if response.status_code == 404:
                    result["status"] = "not_found"
                    break
                if response.status_code == 429 or response.status_code >= 500:
                    try:
                        retry_after = min(60, max(0, float(response.headers.get("Retry-After", 0))))
                    except (TypeError, ValueError):
                        pass
                    result["status"] = "http_error"
                elif not response.ok:
                    result["status"] = "http_error"
                    break
                else:
                    data = response.json()
                    if not isinstance(data, dict):
                        raise ValueError("Expected a JSON object")
                    result.update(status="ok", data=data)
                    break
            except (RequestException, ValueError) as exc:
                result["error"] = str(exc)
            if attempt < 2:
                time.sleep(max(retry_after, 2 ** attempt))
        result["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
        # Only successful responses and definitive 404s survive future runs.
        if result["status"] in ("ok", "not_found"):
            self.cache[key] = result
        return result

    def save(self):
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
            temporary.write_text(json.dumps({"schema_version": 1, "responses": self.cache}, ensure_ascii=False),
                encoding="utf-8")
            temporary.replace(self.cache_path)

    @staticmethod
    def record_lookup(publication, source, result, match_status=""):
        publication["lookups"].append({"source": source,
            **{k: v for k, v in result.items() if k != "data"},
            "match_status": match_status})

    @staticmethod
    def fill(publication, values, source, timestamp):
        for key, value in values.items():
            if value and not publication[key]:
                publication[key] = value
                publication["metadata_sources"][key] = {"source": source, "retrieved_at_utc": timestamp}

    def enrich(self, publication, source="biotools"):
        if (any(not publication[field] for field in ("title", "abstract", "date"))
                or (not publication["doi"] and not publication["pmid"])):
            for kind in ("doi", "pmid", "pmcid"):
                value = publication[kind]
                if not value:
                    continue
                query = {"doi": f'DOI:"{value}"',
                    "pmid": f'EXT_ID:{value} AND SRC:MED',
                    "pmcid": f'PMCID:{value}'}[kind]
                result = self.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                    {"query": query, "format": "json", "resultType": "core", "pageSize": 25})
                candidates = (result["data"].get("resultList") or {}).get("result") or []
                matches = []
                for item in candidates:
                    if not isinstance(item, dict):
                        continue
                    ids = {"doi": normalize_doi(item.get("doi")),
                        "pmid": str(item.get("pmid") or (item.get("id") if item.get("source") == "MED" else "") or ""),
                        "pmcid": str(item.get("pmcid") or "").upper()}
                    if ids[kind] == value and all(not publication[k] or not ids[k] or publication[k] == ids[k] for k in ids):
                        matches.append((item, ids))
                self.record_lookup(publication,
                    "Europe PMC",
                    result,
                    "matched" if len(matches) == 1 else "ambiguous" if matches else "unmatched")
                if len(matches) == 1:
                    item, ids = matches[0]
                    self.fill(publication,
                        {**ids, "title": plain_text(item.get("title")), "abstract": plain_text(item.get("abstractText")), "date": str(item.get("firstPublicationDate") or item.get("pubYear") or "")},
                        "Europe PMC",
                        result["retrieved_at_utc"])
                    break
            if publication["doi"] and any(not publication[field] for field in ("title", "abstract", "date")):
                result = self.get("https://api.crossref.org/works/" + quote(publication["doi"], safe=""))
                item = result["data"].get("message", {})
                matched = isinstance(item, dict) and normalize_doi(item.get("DOI")) == publication["doi"]
                self.record_lookup(publication, "Crossref", result, "matched" if matched else "unmatched")
                if matched:
                    dates = (item.get("published") or item.get("issued") or {}).get("date-parts", [])
                    date = "-".join(str(v) for v in dates[0]) if dates else ""
                    title = item.get("title") or []
                    self.fill(publication,
                        {"title": plain_text(title[0] if isinstance(title, list) and title else title), "abstract": plain_text(item.get("abstract")), "date": date},
                        "Crossref",
                        result["retrieved_at_utc"])
        publication["metadata_status"] = publication_metadata_status(publication)
        if source == "dimensions":
            publication.update(citation_count=None,
                citation_source="",
                citation_status="missing",
                citation_retrieved_at_utc="",
                dimensions_status="no_supported_identifier")
            for kind in ("doi", "pmid"):
                if not publication[kind]:
                    continue
                result = self.get(f"https://metrics-api.dimensions.ai/{kind}/" + quote(publication[kind], safe=""))
                item = result["data"]
                # Some responses omit the queried identifier; if supplied it must agree.
                returned = normalize_doi(item.get("doi")) if kind == "doi" else str(item.get("pmid") or "")
                mismatch = bool(returned and returned != publication[kind])
                count = citation_count(item.get("times_cited")) if result["status"] == "ok" and not mismatch else None
                status = "available" if count is not None else "identifier_mismatch" if mismatch else "missing_count" if result["status"] == "ok" else result["status"]
                self.record_lookup(publication, "Dimensions", result, status)
                publication["dimensions_status"] = status
                publication["dimensions_license"] = item.get("license", "")
                if count is not None:
                    publication.update(dimensions_citation_count=count,
                        citation_count=count,
                        citation_source="Dimensions",
                        citation_status="available",
                        citation_retrieved_at_utc=result["retrieved_at_utc"])
                    break
            if publication["citation_count"] is None:
                publication["citation_status"] = publication["dimensions_status"]
        return publication


# 4. Publication identity groups and citation contributions -------------------
# Retain original entries while counting each linked publication group once.

def audit_publication_duplicates(publication_records):
    """Group matching identifiers within one tool; retain every original row.
    Each group has one representative row, which receives the total citation 
    contribution from one selected source. Conflicts are flagged.
    """
    parents = list(range(len(publication_records)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    identifiers = []
    for i, publication in enumerate(publication_records):
        ids = {"doi": normalize_doi(publication.get("doi")),
               "pmid": str(publication.get("pmid") or "").strip(),
               "pmcid": str(publication.get("pmcid") or "").strip().upper()}
        identifiers.append(ids)
        for kind, value in ids.items():
            if not value:
                continue
            key = (kind, value)
            if key in seen:
                parents[root(i)] = root(seen[key])
            else:
                seen[key] = i
    groups = {}
    for i in range(len(publication_records)):
        groups.setdefault(root(i), []).append(i)
    for members in groups.values():
        representative = members[0]
        identity_conflict = any(len({identifiers[i][k] for i in members if identifiers[i][k]}) > 1
                                for k in ("doi", "pmid", "pmcid"))
        selected = {citation_count(publication_records[i].get("citation_count")) for i in members} - {None}
        registry = {citation_count(publication_records[i].get("biotools_citation_count")) for i in members} - {None}
        selected_value = next(iter(selected)) if len(selected) == 1 and not identity_conflict else None
        registry_value = next(iter(registry)) if len(registry) == 1 and not identity_conflict else None
        for i in members:
            publication_records[i].update({
                "publication_group": representative + 1,
                "duplicate_of_publication_index": representative + 1 if i != representative else "",
                "duplicate_status": "identifier_conflict" if identity_conflict else "duplicate" if i != representative else "representative" if len(members) > 1 else "unique",
                "citation_count_conflict": len(selected) > 1,
                "biotools_citation_count_conflict": len(registry) > 1,
                "citation_total_contribution": selected_value if i == representative else None,
                "biotools_total_contribution": registry_value if i == representative else None,
            })
    return len(groups)


def update_publication_columns(tool, source="biotools"):
    publication_records = tool.get("_publication_records", [])
    distinct_count = audit_publication_duplicates(publication_records)
    for column, key in (("publication_doi", "doi"), ("publication_pmid", "pmid"),
                        ("publication_pmcid", "pmcid"), ("publication_title", "title"),
                        ("publication_abstract", "abstract"), ("publication_date", "date"),
                        ("publication_citations", "citation_count")):
        # Preserve one slot per registry publication, even when a field is missing.
        tool[column] = "; ".join("NA" if publication.get(key) in (None, "") else str(publication[key]) for publication in publication_records)
    counts = [publication["citation_total_contribution"] for publication in publication_records if publication["citation_total_contribution"] is not None]
    registry_counts = [publication["biotools_total_contribution"] for publication in publication_records if publication["biotools_total_contribution"] is not None]
    def coverage(values):
        return "no_publications" if not publication_records else "complete" if len(values) == distinct_count else "partial" if values else "unavailable"
    tool.update({"publication_count": len(publication_records), "publications_with_citation_counts": len(counts),
        "distinct_publication_count": distinct_count,
        "duplicate_publication_entries": sum(p["duplicate_status"] == "duplicate" for p in publication_records),
        "publication_conflict_groups": len({p["publication_group"] for p in publication_records if p["duplicate_status"] == "identifier_conflict" or p["citation_count_conflict"] or p["biotools_citation_count_conflict"]}),
        "total_citations": sum(counts) if counts else "", "citation_coverage": coverage(counts),
        "citation_source": "Dimensions" if source == "dimensions" else "bio.tools",
        "bio_tools_total_citations": sum(registry_counts) if registry_counts else "",
        "bio_tools_citation_coverage": coverage(registry_counts),
        "publication_metadata_json": json.dumps(publication_records, ensure_ascii=False, separators=(",", ":"))})


# 5. Publication audit exports ------------------------------------------------

def _write_tsv_rows(output_path, fields, rows):
    """Write projected audit rows in their original order and return the count."""
    count = 0
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})
            count += 1
    return count


PUBLICATION_FILE_COLUMNS = [
    'biotools_id', 'name', 'retrieval_query', 'publication_index', 'doi', 'pmid', 'pmcid',
    'type', 'note', 'version', 'title', 'abstract', 'date', 'metadata_status',
    'metadata_sources', 'biotools_citation_count', 'biotools_retrieved_at_utc',
    'dimensions_citation_count', 'dimensions_status', 'dimensions_license', 'citation_count',
    'citation_source', 'citation_status', 'citation_retrieved_at_utc', 'lookups',
    'registry_publication', 'publication_group', 'duplicate_of_publication_index', 'duplicate_status',
    'citation_count_conflict', 'biotools_citation_count_conflict',
    'citation_total_contribution', 'biotools_total_contribution',
]


def save_publication_file(tools, output_path):
    """One row per registry publication; nested values are written as JSON."""
    def rows():
        for tool in tools:
            for publication in tool.get("_publication_records", []):
                row = {**publication, **{k: tool.get(k, "") for k in ("biotools_id", "name", "retrieval_query")}}
                yield {key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                       for key, value in row.items()}
    return _write_tsv_rows(output_path, PUBLICATION_FILE_COLUMNS, rows())


# 6. Flatten registry lists and preserve function annotations -----------------

def safe_join(values: Any) -> str:
    """Join all list elements into a string."""
    if values is None:
        return ""
    if isinstance(values, list):
        return ', '.join(str(item) for item in values if item is not None)
    return str(values)

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

def extract_function_records(functions: Any,
    biotools_id: str,
    tool_name: str,
    query: str) -> List[Dict[str, Any]]:
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
        io_columns = {}
        for direction, items in (("input", inputs), ("output", outputs)):
            for kind in ("data", "format"):
                terms, uris = _concept_values(items, kind)
                io_columns[f"{direction}_{kind}_terms"] = "; ".join(terms)
                io_columns[f"{direction}_{kind}_uris"] = "; ".join(uris)
        operation_values = operations or [{}]
        for operation_index, operation in enumerate(operation_values, start=1):
            operation = operation if isinstance(operation, dict) else {}
            rows.append({
                "biotools_id": biotools_id or "",
                "name": tool_name,
                "retrieval_query": query,
                "function_index": function_index,
                "operation_index": operation_index if operations else "",
                "operation_term": operation.get("term", ""),
                "operation_uri": operation.get("uri", ""),
                **io_columns,
                "input_json": json.dumps(inputs, ensure_ascii=False, separators=(",", ":")),
                "output_json": json.dumps(outputs, ensure_ascii=False, separators=(",", ":")),
            })
    return rows


# 7. Retrieve and normalise paginated bio.tools records -----------------------

def extract_year(date_str):
    """Return the first four-digit date part, else the first four digits."""
    if not date_str:
        return ""
    for part in str(date_str).split("-"):
        if part.isdigit() and len(part) == 4:
            return part
    # fallback: first 4 digits if present
    digits = ''.join([c for c in str(date_str) if c.isdigit()])
    return digits[:4] if len(digits) >= 4 else ""


def convert_registry_record(tool, query, retrieval_timestamp):
    """Convert one raw registry record without making network requests."""
    biotools_id = tool.get("biotoolsID")
    publications = extract_publications(tool.get("publication", []), retrieval_timestamp)

    added_year = extract_year(tool.get("additionDate", ""))
    updated_year = extract_year(tool.get("lastUpdate", ""))
    raw_functions = tool.get("function", [])
    function_records = extract_function_records(raw_functions,
        biotools_id or "",
        tool.get("name", ""),
        query)
    operation_terms = sorted({r["operation_term"] for r in function_records if r["operation_term"]})
    operation_uris = sorted({r["operation_uri"] for r in function_records if r["operation_uri"]})

    tool_record = {
        "biotools_id": biotools_id or "",
        "bio_tools_url": f"https://bio.tools/{biotools_id}" if biotools_id else "",
        "retrieval_query": query,
        "retrieval_timestamp_utc": retrieval_timestamp,
        "name": tool.get("name", ""),
        "homepage": tool.get("homepage", ""),
        "description": tool.get("description", "").replace('\n', ' '),
        "version": safe_join(tool.get("version", [])),
        "tool_type": safe_join(tool.get("toolType", [])),
        "topic": extract_topics(tool.get("topic")),
        "function_count": len(raw_functions) if isinstance(raw_functions, list) else 0,
        "function_metadata_status": (
            "Operation annotated" if operation_uris else
            "Function present; operation missing" if function_records else
            "Function metadata missing"
        ),
        "edam_operation_terms": "; ".join(operation_terms),
        "edam_operation_uris": "; ".join(operation_uris),
        "function_metadata_json": json.dumps(raw_functions, ensure_ascii=False, separators=(",", ":")),
        "documentation": extract_documentation(tool.get("documentation", [])),
        "operating_system": safe_join(tool.get("operatingSystem", [])),
        "language": safe_join(tool.get("language", [])),
        "accessibility": safe_join(tool.get("accessibility", [])),
        "license": safe_join(tool.get("license", [])),
        "added": added_year,
        "updated": updated_year,
        "_publication_records": publications,
        "_function_records": function_records,
    }

    update_publication_columns(tool_record)
    return tool_record


def iter_biotools_pages(query: str, max_retries: int = 3, timeout: int = 30) -> Iterator[List[Dict[str, Any]]]:
    """Yield raw API pages with retries, timeouts and pagination checks."""
    url = "https://bio.tools/api/tool/"
    params = {"q": query, "format": "json", "page_size": API_PAGE_SIZE}
    page = 1
    records_received = 0
    expected_count = None
    effective_page_size = None
    previous_response_indicated_next = None

    session = requests.Session()
    try:
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
                    # bio.tools returns 404 when requesting a page beyond the last paginator page, 
                    # even if the previous page was full. If we have already received all expected 
                    # records, treat this as a successful end-of-query signal.
                    count_outstanding = expected_count is not None and records_received < expected_count
                    if (status_code == 404 and page > 1 and records_received > 0
                            and previous_response_indicated_next is not True
                            and not count_outstanding):
                        logging.info(
                            "Completed query %r at API page boundary: %s records across %s page(s)",
                            query, records_received, page - 1,
                        )
                        return
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

            yield tools_on_page

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
    finally:
        session.close()


def fetch_biotools(query: str, max_retries: int = 3, timeout: int = 30) -> List[Dict[str, Any]]:
    """Retrieve pages, then convert and deduplicate tool records for one query."""
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()
    records = []
    tool_ids = set()
    for page_records in iter_biotools_pages(query, max_retries, timeout):
        for tool in page_records:
            biotools_id = tool.get("biotoolsID")
            if biotools_id in tool_ids:
                continue
            tool_ids.add(biotools_id)
            records.append(convert_registry_record(tool, query, retrieval_timestamp))
    return records


# 8. Merge retrieval provenance for repeated tool records ---------------------

def merge_query_provenance(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge repeat query hits by bio.tools' canonical identifier.

    Records without a biotoolsID are retained individually. Missing URLs are never
    treated as evidence that records are duplicates.
    """
    merged: Dict[str, Dict[str, Any]] = {}
    unresolved: List[Dict[str, Any]] = []
    for tool in tools:
        tool_id = str(tool.get("biotools_id", "")).strip()
        if tool_id in merged:
            current = merged[tool_id]
            combined = current.get("retrieval_query", "") + "; " + tool.get("retrieval_query", "")
            queries = {q.strip() for q in combined.split(";") if q.strip()}
            current["retrieval_query"] = "; ".join(sorted(queries, key=str.lower))
            current["retrieval_query_count"] = len(queries)
        elif tool_id:
            merged[tool_id] = {**tool, "retrieval_query_count": 1}
        else:
            unresolved.append({**tool, "retrieval_query_count": 1})
    return list(merged.values()) + unresolved


# 9. Export tool tables, function records, and manifests ----------------------

TOOL_COLUMNS = [
    'biotools_id', 'bio_tools_url', 'retrieval_query', 'retrieval_query_count',
    'retrieval_timestamp_utc', 'name', 'homepage', 'documentation', 'description',
    'tool_type', 'topic', 'function_count', 'function_metadata_status',
    'edam_operation_terms', 'edam_operation_uris', 'function_metadata_json',
    'language', 'operating_system', 'version', 'accessibility', 'license',
    'publication_doi', 'publication_title', 'publication_abstract',
    'publication_date', 'publication_citations', 'total_citations', 'added', 'updated',
    'publication_pmid', 'publication_pmcid', 'publication_count', 'distinct_publication_count',
    'duplicate_publication_entries', 'publication_conflict_groups',
    'publications_with_citation_counts', 'citation_coverage', 'citation_source',
    'bio_tools_total_citations', 'bio_tools_citation_coverage', 'publication_metadata_json',
]

FUNCTION_COLUMNS = [
    'biotools_id', 'name', 'retrieval_query', 'function_index', 'operation_index',
    'operation_term', 'operation_uri', 'input_data_terms', 'input_data_uris',
    'input_format_terms', 'input_format_uris', 'output_data_terms', 'output_data_uris',
    'output_format_terms', 'output_format_uris', 'input_json', 'output_json',
]


def save_tool_file(tools: List[Dict[str, Any]], output_path: str) -> None:
    _write_tsv_rows(output_path, TOOL_COLUMNS, tools)
    logging.info(f"Data saved to {output_path} (TSV)")


def save_function_file(tools: List[Dict[str, Any]], output_path: str) -> int:
    rows = ({**row, "retrieval_query": tool.get("retrieval_query", row.get("retrieval_query", ""))}
            for tool in tools for row in tool.get("_function_records", []))
    return _write_tsv_rows(output_path, FUNCTION_COLUMNS, rows)


def file_md5(output_path: str) -> str:
    digest = hashlib.md5()
    with open(output_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_manifest(output_path: str, function_output_path: str, function_rows: int,
                  queries: List[str], raw_hits: int, tools: List[Dict[str, Any]],
                  publication_output_path: str, publication_rows: int,
                  publication_parameters: Dict[str, Any]) -> None:
    manifest = {
        "pipeline": "bio.tools API retrieval",
        "script": __file__,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "api_endpoint": "https://bio.tools/api/tool/",
        "parameters": {"queries": queries, "requested_page_size": API_PAGE_SIZE,
                       "timeout_seconds": 30, "max_retries": 3},
        "counts": {
            "raw_query_hits": raw_hits, "retrieved_record_count": len(tools),
            "function_operation_rows": function_rows, "publication_rows": publication_rows,
            "citation_coverage": {status: sum(t.get("citation_coverage") == status for t in tools)
                                  for status in ("complete", "partial", "unavailable", "no_publications")},
        },
        "outputs": {
            "tools": {"path": output_path, "md5": file_md5(output_path)},
            "functions": {"path": function_output_path, "md5": file_md5(function_output_path)},
            "publications": {"path": publication_output_path, "md5": file_md5(publication_output_path)},
        },
        "function_model": "bio.tools function.operation with input/output EDAM data and format metadata; no investigator-defined categories",
        "software": {"python": sys.version, "platform": platform.platform(), "requests": requests.__version__},
        "publication_parameters": publication_parameters,
        "publication_model": "Sum one selected-provider count per distinct publication within each tool, grouped by matching normalised DOI/PMID/PMCID, including transitive matches. Original registry entries and duplicate flags retained. Conflicting identifiers or provider counts withheld and flagged for review. Publication Count counts entries; Distinct Publication Count and citation coverage use identifier groups. All publication types retained; missing is not zero; partial totals flagged; no cross-tool or unique citing-paper deduplication. Bibliographic metadata: bio.tools, then exact-identifier Europe PMC and Crossref.",
        "dimensions_attribution": "Dimensions citation data, when requested, is sourced via the Dimensions Metrics API, subject to https://www.dimensions.ai/policies/terms/metrics/. Per-response license is retained in publication records.",
    }
    with open(output_path + ".manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)


# 10. Configure and run the retrieval workflow --------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Fetch tools from bio.tools for multiple queries.')
    parser.add_argument('queries', type=str, help='Comma-separated list of search queries enclosed by "".')
    parser.add_argument('output', type=str, help='The output TSV file.')
    parser.add_argument("--citation-source", choices=("biotools", "dimensions"), default="dimensions",
        help="Source summed in Total Citations (default: Dimensions). Dimensions uses its Metrics API; organisational users must register under its terms. No mixed-source fallback.")
    parser.add_argument("--publication-cache",
        help="Reusable enrichment response cache JSON (default: beside output).")
    parser.add_argument("--cache-days", type=float, default=1,
        help="Maximum cache age in days; 0 refreshes all lookups (default: 1).")
    parser.add_argument("--no-publication-enrichment", action="store_true",
        help="Use only registry metadata; incompatible with --citation-source dimensions.")
    args = parser.parse_args()
    if args.cache_days < 0:
        parser.error("--cache-days must be nonnegative")
    if args.no_publication_enrichment and args.citation_source == "dimensions":
        parser.error("Dimensions requires publication enrichment")
    return args


def main() -> None:
    """Example: fetch_biotools.py "query1,query2" output.tsv"""
    args = parse_args()
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
    tools_deduplicated = merge_query_provenance(all_tools)
    cache_path = args.publication_cache or args.output + ".publication-cache.json"
    if not args.no_publication_enrichment:
        client = PublicationClient(cache_path, args.cache_days)
        try:
            for index, tool in enumerate(tools_deduplicated, 1):
                for publication in tool.get("_publication_records", []):
                    client.enrich(publication, args.citation_source)
                update_publication_columns(tool, args.citation_source)
                if index % 25 == 0:
                    logging.info("Enriched publications for %s/%s tools", index, len(tools_deduplicated))
                    client.save()
        finally:
            client.save()
            client.session.close()
    save_tool_file(tools_deduplicated, args.output)
    function_output = args.output + ".functions.tsv"
    function_rows = save_function_file(tools_deduplicated, function_output)
    publication_output = args.output + ".publications.tsv"
    publication_rows = save_publication_file(tools_deduplicated, publication_output)
    save_manifest(args.output, function_output, function_rows, queries, len(all_tools), tools_deduplicated,
                  publication_output, publication_rows,
                  {"citation_source": args.citation_source,
                   "enrichment_enabled": not args.no_publication_enrichment,
                   "cache_path": cache_path, "cache_days": args.cache_days})
    logging.info(f"Total {len(tools_deduplicated)} tool–domain records saved for queries: {args.queries}")


# 11. Command-line entry point ------------------------------------------------

if __name__ == "__main__":
    main()
