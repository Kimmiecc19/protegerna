# This R script is used to filter the bio.tools output from the fetch_biotools.py -> json2tsv.py script
# Terms specific to the data type are kept and unrelated terms are filtered out
# Tools are removed using specific criteria (license, tool type, DOI etc.)
# This script is for RNA-Seq tools, however, the same script applies to genomic, proteomic and multi-omic tools

# Load necessary libraries
library(dplyr)
library(httr) # For checking URL responses


# Read in the TSV file
tools_df <- read.csv("combined_rna_tools.tsv", sep = "\t", header = TRUE, stringsAsFactors = FALSE)
file1 <- readLines("transcriptomics_filter.tsv") # Assuming each line contains a filter term
file2 <- readLines("transcriptomics_keep.tsv")  # Assuming each line contains a keyword to keep

# Filter tools that are open source or have no entry in the License column
tools_filtered <- tools_df %>%
  filter(grepl("Open access|None", Accessibility, ignore.case = TRUE) | License == "")

# Keep tools with the words from file2 in the Topic column
tools_filtered <- tools_filtered %>%
  filter(grepl(paste(file2, collapse = "|"), Topic, ignore.case = TRUE))

# Remove tools that are web applications in the Tool Type column
tools_filtered <- tools_filtered %>%
  filter(!grepl("web application|desktop application", Tool.Type, ignore.case = TRUE))

# Remove tools with specific words from file1 in the Topic column
tools_filtered <- tools_filtered %>%
  filter(!grepl(paste(file1, collapse = "|"), Topic, ignore.case = TRUE))

# Remove tools with no DOI available
tools_filtered <- tools_filtered %>%
  filter(!grepl("None", DOI, ignore.case = TRUE))


# Function to check if a URL is valid (i.e., does not return a 404 error)
check_url <- function(url) {
  if (is.na(url) || url == "") {
    return(FALSE) # Treat empty or missing URLs as invalid
  }
  response <- try(GET(url), silent = TRUE) # Try to connect to the URL
  if (inherits(response, "try-error")) {
    return(FALSE) # If an error occurs during the connection, treat it as invalid
  }
  return(status_code(response) != 404) # Return TRUE if the status code is not 404 (i.e., valid URL)
}

# Check homepage URLs for validity (remove tools with invalid URLs or 404 errors)
tools_filtered <- tools_filtered %>%
  rowwise() %>%
  filter(check_url(Homepage)) %>% # Apply the URL check on the homepage column
  ungroup()

# Write the filtered data to a new TSV file
write.table(tools_filtered, "filtered_transcriptomic_tools_no404.tsv", sep = "\t", row.names = FALSE, quote = FALSE)

