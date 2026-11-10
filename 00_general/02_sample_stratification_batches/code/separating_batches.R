library(dplyr)
library(readr)
library(purrr)

# Step 1: Read the CSV
trans_batch <- read_csv("transcriptomic_batches_BTC.csv")
prot_batch <- read_csv("proteomic_batches_BTC.csv")

# Step 2: Select relevant columns and remove duplicates
prot_batch_min <- prot_batch %>%
  select(participant, sample_id, artificial_batch) %>%
  distinct()

# Step 2: Select relevant columns and remove duplicates
trans_batch_min <- trans_batch %>%
  select(participant, sample_id, artificial_batch) %>%
  distinct()

write_csv(trans_batch_min, "transcriptomic_batches.csv")
write_csv(prot_batch_min, "proteomic_batches.csv")

# Step 3: Split by artificial_batch
trans_batches_split <- split(trans_batch_min, trans_batch_min$artificial_batch)

# Step 3: Split by artificial_batch
prot_batches_split <- split(prot_batch_min, prot_batch_min$artificial_batch)

# Step 4: Write each artificial batch to a separate CSV
walk2(
  trans_batches_split,
  names(trans_batches_split),
  ~ write_csv(.x, paste0("artificial_trans_batch_", .y, ".csv"))
)

walk2(
  prot_batches_split,
  names(prot_batches_split),
  ~ write_csv(.x, paste0("artificial_prot_batch_", .y, ".csv"))
)
