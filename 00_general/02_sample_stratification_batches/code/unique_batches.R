library(dplyr)
library(readr)
library(stringr)

prot_batch <- read_csv("proteomic_batches_BTC.csv")
trans_batch <- read_csv("transcriptomic_batches_BTC.csv")

# 423
unique_sample_prot <- prot_batch %>%
  distinct(sample_id, .keep_all = TRUE)

# 412
unique_sample_trans <- trans_batch %>%
  distinct(sample_id, .keep_all = TRUE)

#347
unique_participant_prot <- prot_batch %>%
  distinct(participant, .keep_all = TRUE)

# 347
unique_participant_trans <- trans_batch %>%
  distinct(participant, .keep_all = TRUE)
