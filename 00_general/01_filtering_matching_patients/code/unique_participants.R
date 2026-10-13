library(dplyr)
library(readr)

# Load your data
mapping_data <- read_csv("filtered_mapping_data.csv")

# Optional: remove duplicate rows (e.g. if there are still 253 per participant)
unique_participant_mapping <- mapping_data %>%
  distinct(participant, .keep_all = TRUE)

# Extract transcriptomics and proteomics mappings
trans_mapping <- mapping_data %>%
  filter(grepl("-T$", sample_id)) %>%
  select(participant, trans_sample_id = sample_id, trans_seq_batch = seq_batch)

prot_mapping <- mapping_data %>%
  filter(grepl("-P$", sample_id)) %>%
  select(participant, prot_sample_id = sample_id, prot_seq_batch = seq_batch)

# Optional: remove duplicate rows (e.g. if there are still 253 per participant)
unique_trans <- trans_mapping %>%
  distinct(participant, .keep_all = TRUE)

unique_prot <- prot_mapping %>%
  distinct(participant, .keep_all = TRUE)

# Repeated participants in transcriptomic data
repeated_trans_participants <- trans_mapping %>%
  count(participant) %>%
  filter(n > 1)

# Repeated participants in proteomic data
repeated_prot_participants <- prot_mapping %>%
  count(participant) %>%
  filter(n > 1)

# Repeats in both
repeated_participants <- mapping_data %>%
  count(participant) %>%
  filter(n > 1)

# How many participants are in both omics
both_prot_trans <- intersect(unique_prot$participant, unique_trans$participant)
length(both_prot_trans)  

# Who is in only one
only_prot <- setdiff(unique_prot$participant, unique_trans$participant)
only_trans <- setdiff(unique_trans$participant, unique_prot$participant)

# Summary table
tibble(
  unique_prot = nrow(unique_prot),
  unique_trans = nrow(unique_trans),
  in_both = length(both_prot_trans),
  only_prot = length(only_prot),
  only_trans = length(only_trans),
  total_unique = length(union(unique_prot$participant, unique_trans$participant))
)

# Save to CSV
write_csv(unique_participant_mapping, "participant_sample_mapping.csv")

# Keep only participants
#participant_only <- unique_prot %>% 
#  select(participant)  

#write_csv(participant_only, "participants.csv")

