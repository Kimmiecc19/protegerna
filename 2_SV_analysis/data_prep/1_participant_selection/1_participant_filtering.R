# This script filters the metadata file so that only patients with all three data types remain.
# Also removes remaining participants with proteomic batch effects.

# Load the necessary libraries for the session
library(tidyverse)  # Data manipulation and visualization
library(tidyr)      # Tidying data

# Read in the csv file 
aals_metadata <- read_csv("aals_dataportal_datatable.csv")

# Extract necessary columns and rename them to remove blank spaces
extracted_aals_data <- aals_metadata %>% 
  select(participant = `Participant_ID`,    
         guid = `GUID`,               
         genom = `HAS_GENOMICS`,
         rna = `HAS_TRANSCRIPTOMICS`,
         prot = `HAS_PROTEOMICS`,
         sex = `SEX`,
         ethnicity = `ETHNIC_CATEGORY`,
         race = `RACE`,
         diagnosis = `SUBJECT_GROUP`,
         batch = `Batch`)         

# Filter the data to retain only rows where all three data types are marked "Yes"
aals_filtered <- extracted_aals_data %>%
  filter(genom == "Yes" & rna == "Yes" & prot == "Yes")

# Load the list of 52 proteomic samples that need to be removed
proteomic_samples <- read_csv("Proteomics_Batch_Effect_Samples_52.csv")

# Remove rows from aals_filtered where the participant matches any in the batch effect list
aals_filtered_cleaned <- aals_filtered %>%
  filter(!participant %in% proteomic_samples$participant)

# Optionally, write the cleaned data to a new CSV file
write_csv(aals_filtered_cleaned, "filtered_matched_aals.csv")