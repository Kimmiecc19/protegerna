# Load necessary libraries
library(dplyr)
library(readr)
library(tidyverse)

# Load your data
# Run from 00_general/01_filtering_matching_patients/. Answer ALS portal tables are read from
# data/aals_metadata_neuromine/; outputs are written to the working folder.
data_dir <- file.path("data", "aals_metadata_neuromine")
mapping_data <- read_csv("filtered_mapping_data.csv")  # from 02_merged_tp_mapping.R

# Load AALS released files data
aals_files <- read_csv(file.path(data_dir, "aals_released_files.csv"))

aals_files_filtered <- aals_files %>%
  select(
    omic = `omic`,
    level = `data_level`,
    file_path = `path`
  ) %>%
  mutate(
    sample_id = str_extract(file_path, "(CASE|CTRL)-[^/]+-[^/_]+-[A-Z]")
  )

# Then join with aals_files on participant
merge_sample_data <- mapping_data %>%
  inner_join(aals_files_filtered, by = "sample_id")

# Get unique omic types from omic column
omics <- unique(merge_sample_data$omic)

# Filter to keep only required data level
# Define omic-specific data level filters
transcriptomic_data <- merge_sample_data %>%
  filter(tolower(omic) == "transcriptomics", level == 1)

proteomic_data <- merge_sample_data %>%
  filter(tolower(omic) == "proteomics", level == 2)

final_aals_sample_data <- merge_sample_data %>%
  filter(
    (omic == "proteomics" & level == 2) |
      (omic == "transcriptomics" & level == 1)
  )

# Separate BTC and BTC2 from BDC (in seq_batch)
btc <- final_aals_sample_data %>%
  filter(seq_batch %in% c("BTC", "BTC2"))

# Keep all BDC samples
bdc <- final_aals_sample_data %>%
  filter(grepl("^\\d+$", seq_batch))  # keeps rows where seq_batch is all digits

# # Split BDC to trans
# bdc_t <- trans_mapping %>%
#   filter(grepl("^\\d+$", seq_batch))  # keeps rows where seq_batch is all digits
# 
# # Split BDC to prot
# bdc_p <- prot_mapping %>%
#   filter(grepl("^\\d+$", seq_batch))  # keeps rows where seq_batch is all digits

# Keep only control participant from BDC + BTC
#ctrl_bdc <- bdc %>%
#  filter(participant == "CTRL-NEUEU392AE8")
# 


# Check for unique participants
# Optional: remove duplicate rows (e.g. if there are still 253 per participant)
unique_participants <- final_aals_sample_data %>%
  distinct(participant, .keep_all = TRUE)

# Keep unique samples
unique_samples <- final_aals_sample_data %>%
  distinct(sample_id, .keep_all = TRUE)

# Double-check
unique_participant_samples <- unique_samples %>%
  distinct(participant, .keep_all = TRUE)

# Separate BTC and BTC2 from BDC (in seq_batch)
strat_btc <- unique_samples %>%
  filter(seq_batch %in% c("BTC", "BTC2"))

# Keep all BDC samples
strat_bdc <- unique_samples %>%
  filter(grepl("^\\d+$", seq_batch))

# Save to CSV
write_csv(final_aals_sample_data, "samples_with_paths.csv")
write_csv(strat_btc, "stratify_btc.csv")
write_csv(strat_bdc, "stratify_bdc.csv")
write_csv(ctrl_bdc, "stratify_bdc_ctrl.csv")


# BTC validation
# map_test <- read_csv("Sample-Mapping-File-Feb-2024.csv")
# 
# unique_test <- map_test %>%
#   distinct(`Sample ID`, .keep_all = TRUE)
# 
# # Separate BTC and BTC2 from BDC (in seq_batch)
# btc_test <- unique_test %>%
#   filter(`Batch #` %in% c("BTC", "BTC2"))
# 
# btc_mapping <- btc_test %>%
#   filter(!grepl("-E$", `Sample ID`))
# 
# btc_only <- btc_mapping %>%
#   filter(`Participant ID` == "CTRL-NEUEU392AE8")
# 
# btc_only_test <- btc_test %>%
#   filter(`Batch #` %in% c("BTC", "BTC2"))