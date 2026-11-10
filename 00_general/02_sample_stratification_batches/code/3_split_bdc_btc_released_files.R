library(dplyr)
library(readr)
library(stringr)

# Load input files
filtered_matched <- read_csv("filtered_mapping_data.csv")
aals_files <- read_csv("aals_released_files.csv")

# Select and rename columns
df_samples <- filtered_matched %>%
  select(participant, sample_id, sex, diagnosis, seq_batch, shipment)

aals_files <- aals_files %>%
  select(
    participant = `Participant_ID`,
    omic = `omic`,
    level = `data_level`,
    file_path = `path`
  ) %>%
  filter(tolower(omic) %in% c("transcriptomics", "proteomics"), level == 1)

# Extract sample_id from file_path
aals_files <- aals_files %>%
  mutate(sample_id = str_extract(file_path, "[A-Z]+-[A-Z0-9]+-[0-9]+-[PT]"))

# Quality Check 1: any missing sample_id?
missing_sample_ids <- aals_files %>%
  filter(is.na(sample_id))

if (nrow(missing_sample_ids) > 0) {
  message("WARNING: Some file paths did not yield a sample_id. See `missing_sample_ids.csv`.")
  write_csv(missing_sample_ids, "missing_sample_ids.csv")
} else {
  message("All file paths have a valid extracted sample_id.")
}

# Perform join on participant + sample_id
merged_df <- aals_files %>%
  inner_join(df_samples, by = c("participant", "sample_id")) %>%
  select(participant, sample_id, sex, diagnosis, seq_batch, shipment, omic, file_path)

# Quality Check 2: file paths that didn't join (unmatched to sample metadata)
unmatched_files <- aals_files %>%
  anti_join(df_samples, by = c("participant", "sample_id"))

if (nrow(unmatched_files) > 0) {
  message("WARNING: Some file paths could not be matched to metadata. See `unmatched_files.csv`.")
  write_csv(unmatched_files, "unmatched_files.csv")
} else {
  message("All file paths matched to sample metadata.")
}

# Quality Check 3: sample_ids in metadata that had no corresponding files
unmatched_samples <- df_samples %>%
  anti_join(aals_files, by = c("participant", "sample_id"))

if (nrow(unmatched_samples) > 0) {
  message("WARNING: Some sample_ids had no corresponding file paths. See `unmatched_samples.csv`.")
  write_csv(unmatched_samples, "unmatched_samples.csv")
} else {
  message("All samples have matching files.")
}

# Summary
message("Merge Summary:")
message(paste0("Total sample records: ", nrow(df_samples)))
message(paste0("Total file paths: ", nrow(aals_files)))
message(paste0("Successfully merged entries: ", nrow(merged_df)))

# Split by omic
prot_mapping <- merged_df %>%
  filter(grepl("-P$", sample_id))

trans_mapping <- merged_df %>%
  filter(grepl("-T$", sample_id))

# BTC vs BDC batches
btc <- merged_df %>%
  filter(seq_batch %in% c("BTC", "BTC2"))

bdc <- merged_df %>%
  filter(grepl("^\\d+$", seq_batch))

# Save outputs
write_csv(btc, "stratify_btc.csv")
write_csv(bdc, "stratify_bdc.csv")
write_csv(merged_df, "merged_metadata_and_files.csv")


# Check participant numbers
unique_participant_bdc <- bdc %>%
  distinct(participant, .keep_all = TRUE)

unique_participant_btc <- btc %>%
  distinct(participant, .keep_all = TRUE)

unique_sample_bdc <- bdc %>%
  distinct(sample_id, .keep_all = TRUE)

unique_batch_bdc <- unique_sample_bdc %>%
  select(participant,sample_id,sex,diagnosis,seq_batch,shipment)

write_csv(unique_batch_bdc, "stratify_batch_bdc.csv")

#Each file path is mapped to the correct sample.
# Prevents cartesian inflation caused by joining on participant only.
# Handles multi-sample participants elegantly and correctly.