# This script is used to combine tsv outputs from the json2tsv.py script
# Each omics type has several files for the search terms used (e.g. genome annotation, genome analysis, variant calling etc.)
# This script combines these files for each omics type and creates a new tsv

import os  
import pandas as pd  
import argparse 

# Function to combine all TSV files in a directory into a single dataframe
def combine_tsv(directory):
    dataframes = []  # Create an empty list to hold individual dataframes from each TSV file

    # Iterate over all files in the specified directory
    for filename in os.listdir(directory):
        # Process files with a '.tsv' extension only
        if filename.endswith(".tsv"):
            filepath = os.path.join(directory, filename)  # Combines the directory path (directory) and the filename (filename) into a complete file path (filepath)
            try:
                # Read the TSV file into a Pandas dataframe, skip over rows that cannot be parsed
                df = pd.read_csv(filepath, sep='\t', on_bad_lines='skip')

                # Add a "Source File" column if it doesn't already exist
                if "Source File" not in df.columns:
                    # Insert a new column at the first position with the filename (excluding '.tsv')
                    df.insert(0, "Source File", os.path.splitext(filename)[0])
                
                # Add the dataframe to the list
                dataframes.append(df)
            # If an error occurs while reading the file
            except Exception as e:
                # Print an error message 
                print(f"Error reading {filename}: {e}")
              # Script continues processing the remaining files

    # Combine all individual dataframes into a single dataframe
    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df

# Main function to handle command-line arguments and execute the script
def main():
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description='Combine TSV tables.')
    parser.add_argument('directory', type=str, help='The directory containing the TSV files.')  # Input directory
    parser.add_argument('output', type=str, help='The output TSV file.')  # Output file path

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the function to combine TSV files and store the result
    combined_df = combine_tsv(args.directory)

    # Save the combined dataframe as a TSV file
    combined_df.to_csv(args.output, sep='\t', index=False)

# Entry point of the script
if __name__ == "__main__":
    main()
