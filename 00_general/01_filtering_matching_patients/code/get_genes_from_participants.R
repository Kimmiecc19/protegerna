# This script filters the filtered participants to get their gene variant information (for presentation)

# Load the necessary libraries for the session
library(tidyverse)  # Data manipulation and visualization
library(tidyr)      # Tidying data

# Read in the csv file 
aals_metadata <- read_csv("merged_aals_data.csv")
aals_gene <- read_csv("ALS_Gene_Mutations.csv")

# Extract necessary columns and rename them to remove blank spaces
extracted_aals_data <- aals_metadata %>% 
  select(participant,sex,race,diagnosis,clinreport_mutations_details,hasvariant,eh_c9orf72,eh_atxn2,c9orf72_repeat_length,atxn2_repeat_length)

extracted_aals_gene <- aals_gene %>% 
  mutate(participant = `Participant_ID`) %>%
  select(participant,ang,c9orf72,fus,mutot,progran,setx,sod1,tau,tdp43,vapb,vcp) 
  
# Join on participant
# inner_join() keeps only rows with matching participant values in both dataframes
filtered_gene_data <- extracted_aals_gene %>%
  inner_join(extracted_aals_data, by = "participant")


# Write the cleaned data to a new CSV file
write_csv(filtered_gene_data, "filtered_genes_aals.csv")
