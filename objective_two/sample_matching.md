# Sample matching of patient data

This is to ensure that for each patient, genomic, transcriptomics and proteomic data is available.

AnswerALS informs participants of 52 samples with strong batch effects (https://dataportal.answerals.org/data-information). Their recommendation is removing them. 

```R

# Load the necessary libraries for the session
library(tidyverse)  # Data manipulation and visualization
library(tidyr)      # Tidying data

# Set the working directory 
setwd("~/als-metadata") 

# Read in the tab-delimited text file 
aals_metadata <- read_csv("aals_dataportal_datatable.csv")

# Select the three relevant columns that I need and rename them to remove blank spaces
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

# Load the list of 50 proteomic samples that need to be removed
proteomic_samples <- read_csv("Proteomics_Batch_Effect_Samples_52.csv")

# Remove rows from filtered_aals where the participant matches any in the list
aals_filtered_cleaned <- aals_filtered %>%
  filter(!participant %in% proteomic_samples$participant)

# Optionally, write the cleaned data to a new CSV file
write_csv(aals_filtered_cleaned, "filtered_aals_cleaned.csv")

# Write the filtered data to a new file
write.table(aals_filtered_cleaned, "filtered_aals_cleaned.txt", sep = "\t", row.names = FALSE, quote = FALSE)

# Genome data (keeping genom and other relevant columns)
write_csv(aals_filtered_cleaned, "genome_data.csv")

# RNA data (keeping rna and other relevant columns)
write_csv(aals_filtered_cleaned, "rna_data.csv")

# Proteome data (keeping prot and other relevant columns)
write_csv(aals_filtered_cleaned, "proteome_data.csv")

```
