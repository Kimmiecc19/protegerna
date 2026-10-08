# This script filters out participants from the Sample_Mapping-File of BDC and BTC participants who don't appear on the filtered patients file.
# Epigenomics samples are removed from the sample mapping.
# Output is sample mapping data for filtered participants.

# Load necessary libraries
library(dplyr)
library(readr)
library(purrr)

# Load filtered and matched AALS data (script 1)
filtered_matched <- read_csv("filtered_matched_aals.csv")

# Load sample mapping file
sample_mapping <- read_csv("Sample-Mapping-File-Feb-2024.csv")

# Extract necessary columns and rename them to remove blank spaces
filtered_matched <- filtered_matched %>% 
  select(participant,sex,ethnicity,race,diagnosis)

sample_mapping <- sample_mapping %>% 
  select(
    participant = `Participant ID`,
    sample_id = `Sample ID`,
    guid_batch = `GUID-Batch`,
    seq_batch = `Batch #`,
    shipment = `Shipment`
  )

# Filter sample_mapping to only keep participants found in filter_matched file
sample_mapping_filtered <- sample_mapping %>%
  filter(participant %in% filtered_matched$participant)

# Remove epigenomics samples (sample IDs ending in "-E")
tp_sample_mapping <- sample_mapping_filtered %>%
  filter(!grepl("-E$", sample_id))

# Join filtered_matched and TP samples on participant
# inner_join() keeps only rows with matching participant values in both dataframes
filter_mapping <- filtered_matched %>%
  inner_join(tp_sample_mapping, by = "participant")

# Save full table 
write_csv(filter_mapping, "filtered_mapping_data.csv")
