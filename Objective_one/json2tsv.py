# This script is used to convert a json formatted file to a tsv file using Python 
# Typically used after the fetch_biotools.py script

# JSON (JavaScript Object Notation) is typically used to exchange data between servers and clients. 
# TSV is a text-based data format that represents data in tabular form.

import pandas as pd  # Import for data manipulation
import json  # Import to handle JSON files
import argparse  # Import for command-line argument parsing

# Function to clean text by replacing newline characters with spaces
def clean_text(text):
    if isinstance(text, str):
        return text.replace('\n', ' ')  # Replace newlines with spaces in strings
    return text  # If the input is not a string, return it as it was

# Function to clean and format lists
def clean_list(lst):
    if isinstance(lst, list):
        # Convert each element to a string; if it's a dictionary, convert it to a JSON string
        return ', '.join([json.dumps(item) if isinstance(item, dict) else str(item) for item in lst])
    return lst  # If input is not a list, return it as-is

# Function to process each entry in the JSON data
def process_entry(entry):
    # Iterate over key-value pairs in the entry
    for key, value in entry.items():
        if isinstance(value, list):
            entry[key] = clean_list(value)  # Clean list if value is a list
        elif isinstance(value, str):
            entry[key] = clean_text(value)  # Clean text if value is a string
    return entry  # Return the processed entry

# Function to convert JSON data to a data frame and save it as a tsv file
def json_to_dataframe(json_file, tsv_file):
    # Open JSON file in read
    with open(json_file, 'r') as f:
        data = json.load(f)  # Load and parse JSON data from the file

    # Process and clean each entry in the JSON data
    processed_data = [process_entry(entry) for entry in data]

    # Initialize an empty list to store DataFrames for each entry
    dfs = []

    # Iterate over each entry in the processed data
    for entry in processed_data:
        # Convert JSON entry to a pandas DataFrame (flattens nested structures)
        df = pd.json_normalize(entry)
        # Append the resulting data frame to the list
        dfs.append(df)

    # Concatenate all data frames into a single data frame
    result_df = pd.concat(dfs, ignore_index=True)

    # Save the resulting data frame as a tab-delimited file (TSV)
    result_df.to_csv(tsv_file, sep='\t', index=False)

    print(f"File saved successfully as {tsv_file}")  # Confirm that the file was saved

# Checks if the script is being run directly or if it’s being imported into another script
if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Convert JSON data to TSV.')
    parser.add_argument('json_file', type=str, help='The input JSON file.')  # Input JSON file argument
    parser.add_argument('tsv_file', type=str, help='The output TSV file.')  # Output TSV file argument

    # Parse the provided command-line arguments
    args = parser.parse_args()

    # Run the conversion function with the provided arguments
    json_to_dataframe(args.json_file, args.tsv_file)

