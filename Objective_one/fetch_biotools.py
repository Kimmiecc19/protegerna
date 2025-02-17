import requests
import json
import argparse
import logging
from requests.exceptions import RequestException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract topic terms (remove URI) and concatenate them into a single string
def extract_topics(topics):
    if isinstance(topics, list):
        return ', '.join(topic.get("term", "") for topic in topics if isinstance(topic, dict))
    return topics

# Function to extract documentation URL
def extract_documentation(documentation):
    if isinstance(documentation, list):
        for doc in documentation:
            if isinstance(doc, dict):
                return doc.get("url", "")
    return ""

# Function to extract publication details (DOI, title, abstract) and format them
def extract_publications(publications):
    if isinstance(publications, list):
        extracted = []
        citations = []
        for pub in publications:
            if isinstance(pub, dict):
                doi = pub.get("doi", "")
                metadata = pub.get("metadata", {})

                # Ensure metadata is a dictionary before accessing its fields
                if not isinstance(metadata, dict):
                    metadata = {}

                title = metadata.get("title", "")
                abstract = metadata.get("abstract", "")
                year = metadata.get("publicationYear", "")
                citation_count = metadata.get("citationCount", 0)  # Default to 0 if missing

                # Ensure abstract is a string before calling replace()
                if not isinstance(abstract, str):
                    abstract = ""

                abstract = abstract.replace('\n', ' ')

                # Add the formatted publication data
                extracted.append(f"{doi}, {title}, {abstract}")
                citations.append(str(citation_count))  # Convert citation count to string

        return ', '.join(extracted), ', '.join(citations)  # Return both publication details and citation counts
    return "", ""

# Function to join list elements into a string, handling cases where the input is not a list
def safe_join(lst):
    if isinstance(lst, list):
        return ', '.join(str(item) for item in lst)
    return str(lst)

# Function to fetch biotools tools based on a query
def fetch_biotools(query):
    url = "https://bio.tools/api/tool/"
    params = {"q": query, "format": "json", "page_size": 150}
    all_tools = []
    page = 1

    while True:
        try:
            params["page"] = page
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses
        except RequestException as e:
            logging.error(f"Error: Failed to fetch data for page {page}: {e}")
            break

        data = response.json()
        tools_on_page = data.get("list", [])

        if not tools_on_page:
            break

        for tool in tools_on_page:
            publications, citations = extract_publications(tool.get("publication", []))
            filtered_tool = {
                "Name": tool.get("name"),
                "Homepage": tool.get("homepage"),
                "Description": tool.get("description", "").replace('\n', ' '),
                "Version": tool.get("version"),
                "Tool Type": safe_join(tool.get("toolType", [])),
                "Topic": extract_topics(tool.get("topic")),
                "Publications": publications,  # Publications column
                "Citations": citations,  # Citations column
                "Documentation": extract_documentation(tool.get("documentation", [])),
                "Operating System": safe_join(tool.get("operatingSystem", [])),
                "Language": safe_join(tool.get("language", [])),
                "Accessibility": safe_join(tool.get("accessibility", "")),
                "License": safe_join(tool.get("license", []))
            }
            all_tools.append(filtered_tool)

        page += 1

    return all_tools

# Function to save the fetched tools to a JSON file
def save_to_file(tools, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(tools, f, indent=4)
        logging.info(f"Data saved to {filename}")
    except IOError as e:
        logging.error(f"Error: Could not write to file {filename}: {e}")

# Main function to parse arguments and execute the script
def main():
    parser = argparse.ArgumentParser(description='Fetch tools from bio.tools for multiple queries.')
    parser.add_argument('queries', type=str, help='Comma-separated list of search queries.')
    parser.add_argument('output', type=str, help='The output JSON file.')
    args = parser.parse_args()

    all_tools = []
    queries = args.queries.split(',')

    for query in queries:
        query = query.strip()  # Remove leading/trailing spaces
        logging.info(f"Fetching results for: {query}")
        tools = fetch_biotools(query)
        all_tools.extend(tools)  # Append results to the combined list

    save_to_file(all_tools, args.output)
    logging.info(f"Total {len(all_tools)} tools fetched for queries: {queries}")

if __name__ == "__main__":
    main()

# Commands with keywords
# python fetch_biotools.py "Proteomics, Protein structure analysis, Protein interactions, Protein modelling, Protein structure prediction, Protein secondary structure prediction, Protein folding, Protein folds and structural domains, Protein model validation, Protein feature detection, Protein sequence analysis" proteomics_biotools.json
# python fetch_biotools.py "Genomics, Sequencing quality control, Sequence assembly, Genome annotation, Comparative genomics, Genetic variation, Genotype and phenotype, Gene prediction, Genome visualisation, Sequence annotation, Sequence alignment" genomics_biotools.json
# python fetch_biotools.py "Transcriptomics, Functional analysis, Gene expression, Sequence annotation, Gene functional annotation, Structure analysis, Enrichment analysis, Systems biology, Pathway or network prediction, Pathway or network visualisation" transcriptomics_biotools.json
# python fetch_biotools.py "Multi-omics, Proteogenomics" multiomics_biotools.json
