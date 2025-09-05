# Load necessary libraries
library(dplyr)
library(readr)
library(purrr)

# Load filtered and matched AALS data
filtered_matched <- read_csv("filtered_matched_aals.csv")

# Load AALS dataportable datatable
aals_datatable <- read_csv("aals_dataportal_datatable.csv")

# Load AALS released files data
aals_files <- read_csv("aals_released_files.csv")

# Extract necessary columns and rename them to remove blank spaces

# Columns in filtered_matched_aals.csv are used as is

# The aals_dataportal_datatable.csv file outlines clinical information for each participant. 
aals_datatable <- aals_datatable %>% 
  select(
    participant = `Participant_ID`,
    subject_group = `SUBJECT_GROUP`,
    site_of_onset = `Site_of_Onset`,
    age_at_symptom_onset = `AGE_AT_SYMPTOM_ONSET`,
    age_at_death = `AGE_AT_DEATH`,
    ipsc_line = `iPSCLine`,
    dimns_line = `diMNs_line`,
    clinreport_mutations_details = `ClinReport_Mutations_Details`,
    hasvariant = `HasVariant`,
    eh_c9orf72 = `EH_C9orf72`,
    eh_atxn2 = `EH_ATXN2`,
    c9orf72_repeat_length = `C9orf72_repeat_length`,
    atxn2_repeat_length = `ATXN2_repeat_length`)

# The aals_released_files.csv file lists the file paths for all of the data 
aals_files <- aals_files %>% 
  select(
    participant = `Participant_ID`,    
    omic = `omic`, 
    level = `data_level`,
    file_path = `path`)

# Remove epigenomics files (not being studied)
aals_files <- aals_files %>%
  filter(tolower(omic) != "epigenomics")

# Join filtered_matched and aals_datatable on participant
# inner_join() keeps only rows with matching participant values in both dataframes
merge_table_filter <- filtered_matched %>%
  inner_join(aals_datatable, by = "participant")

# Then join with aals_files on participant
merge_aals_data <- merge_table_filter %>%
  inner_join(aals_files, by = "participant")

# Divide the data and create files for each omics type
# Get unique omic types from omic column
omics <- unique(merge_aals_data$omic)

# Filter to keep only required data level
# Define omic-specific data level filters
genomic_data <- merge_aals_data %>%
  filter(tolower(omic) == "genomics", level == 2)

transcriptomic_data <- merge_aals_data %>%
  filter(tolower(omic) == "transcriptomics", level == 1)

proteomic_data <- merge_aals_data %>%
  filter(tolower(omic) == "proteomics", level == 1)

final_merge_aals_data <- merge_aals_data %>%
  filter(
    (omic == "genomics" & level == 2) |
    (omic %in% c("transcriptomics", "proteomics") & level == 1)
  )

# Save to CSV
write_csv(genomic_data, "genomic_data_level2.csv")
write_csv(transcriptomic_data, "transcriptomic_data_level1.csv")
write_csv(proteomic_data, "proteomic_data_level1.csv")

# Save full table of all omics types
write_csv(final_merge_aals_data, "merged_aals_data.csv")