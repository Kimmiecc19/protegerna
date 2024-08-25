import requests  # Library to handle HTTP requests
import json  # Library to handle JSON data
import argparse  # Library to handle command-line arguments


# Code to prepare certain columns for extracting information from bio.tools
# Function to extract topic terms (remove URI) and concatenate them into a single string
def extract_topics(topics):
    if isinstance(topics, list):  # Check if topics is a list
        # Join all topic terms with a comma, ensuring each topic is now a dictionary
        return ', '.join(topic.get("term", "") for topic in topics if isinstance(topic, dict))
    return topics  # Return topics as is if it's not a list

# Function to extract documentation URL (usually empty for most entries)
def extract_documentation(documentation):
    if isinstance(documentation, list):  # Check if documentation is a list
        for doc in documentation:
            if isinstance(doc, dict):  
                return doc.get("url", "")  # Return the URL if present
    return ""  # Return an empty string if documentation is not a list or if no URL is found


# Function to extract publication details (DOI, title, and abstract) and format them instead of having all of the details
def extract_publications(publications):
    if isinstance(publications, list):  # Check if publications is a list
        extracted = [] # Create an empty list
        for pub in publications:  # Iterate over each publication
            if isinstance(pub, dict):  # Check if each publication is a dictionary
                doi = pub.get("doi", "")  # Get the DOI, default to an empty string if not present
                metadata = pub.get("metadata", {})  # Get the metadata, default to an empty dictionary if not present
                # Ensure metadata is a dictionary and get the title and abstract from the metadata
                title = metadata.get("title", "") if isinstance(metadata, dict) else ""
                # Abstract obtained from metadata and is formatted as a single line
                abstract = metadata.get("abstract", "").replace('\n', ' ') if isinstance(metadata, dict) else ""
                # Append formatted publication details to the list
                extracted.append(f"{doi}, {title}, {abstract}")
        # Join all extracted publication details with a semicolon
        return '; '.join(extracted)
    return publications  # Return publications as is if it's not a list

# In general
# Function to join list elements into a string, handling cases where the input is not a list
def safe_join(lst):
    if isinstance(lst, list):  # Check if lst is a list
        return ', '.join(str(item) for item in lst)  # Join list elements with a comma
    return str(lst)  # Convert non-list input to a string

# Function to fetch biotools tools based on a query from its API (https://biotools.readthedocs.io/en/latest/api_reference.html)
def fetch_biotools(query):
    url = "https://bio.tools/api/tool/"  # Base URL of the API
    params = {
        "q": query,  # Search query parameter
        "format": "json",  # Response format
        "page_size": 100,  # Number of results per page
    }

    all_tools = []  # Empty list to store all fetched tools
    page = 1  # Initial page number

    while True:
        params["page"] = page  # Set the current page number in the request parameters
        response = requests.get(url, params=params)  # Make the API request

      #Error handling
        if response.status_code != 200:  # Check if the request was successful
            print(f"Error: Failed to fetch data for page {page}")
            break

        data = response.json()  # Parse the JSON response
        tools_on_page = data.get("list", [])  # Get the list of tools on the current page (1)

        if not tools_on_page:  # Break the loop if no more tools are found
            break

        for tool in tools_on_page:  # Iterate over each tool
            # Filter only the required columns and clean the data as done above
            filtered_tool = {
                "Name": tool.get("name"),
                "Homepage": tool.get("homepage"),
                "Description": tool.get("description", "").replace('\n', ' '),  # Remove newlines from the description so that it is one paragraph
                "Version": tool.get("version"),
                "Tool Type": safe_join(tool.get("toolType", [])),
                "Topic": extract_topics(tool.get("topic")),
                "Publications": extract_publications(tool.get("publication")),
                "Operation": safe_join(tool.get("operation", [])),
                "Documentation": extract_documentation(tool.get("documentation", [])),
                "Operating System": safe_join(tool.get("operatingSystem", [])),
                "Language": safe_join(tool.get("language", [])),
                "License": safe_join(tool.get("license", []))
            }
            all_tools.append(filtered_tool)  # Add the filtered tool to the list

        page += 1  # Move to the next page. Will iterate over page 2 and so on.

    return all_tools  # Return the list of all fetched tools

# Function to save the fetched tools to a JSON file
def save_to_file(tools, filename):
    with open(filename, 'w') as f:  # Open the file in write mode
        json.dump(tools, f, indent=4)  # Write the tools to the file in JSON format with indentation

# Argument parsing
# Checks if the script is being run directly by Python interpreter as main program or if imported as a module into another script
if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Fetch tools from bio.tools.')
    parser.add_argument('query', type=str, help='The search query string.')  # Argument for the search query
    parser.add_argument('output', type=str, help='The output JSON file.')  # Argument for the output file

    args = parser.parse_args()  # Parse the command-line arguments

    # Fetch the tools using the provided query and save them to the specified output file
    biotools = fetch_biotools(args.query)
    save_to_file(biotools, args.output)
    print(f"Total {len(biotools)} analysis tools fetched.")  # Print the total number of fetched tools
