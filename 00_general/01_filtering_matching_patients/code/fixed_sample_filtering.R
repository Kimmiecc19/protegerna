# Load necessary libraries
library(dplyr)
library(readr)
library(tidyverse)

# Load your data
mapping_data <- read_csv("filtered_mapping_data.csv")

# Load AALS released files data
aals_files <- read_csv("aals_released_files.csv")