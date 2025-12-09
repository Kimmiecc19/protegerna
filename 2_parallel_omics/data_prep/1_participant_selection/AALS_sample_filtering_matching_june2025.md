# Filtering and sample matching AALS data

First generated: 02/06/2025

## AnswerALS

Source: <https://dataportal.answerals.org/resources>

Amyotrophic Lateral Sclerosis (ALS) is a devasting neurological disease that affects 1 in 400 people. Patients suffer a progressive loss of voluntary muscle control leading to paralysis, difficulty speaking, swallowing, and, ultimately, breathing. Over 60% of patients with ALS die within three years of clinical presentation, and 90% will die within ten years.

### Program Mission

To build the most comprehensive clinical and biological assessment of ALS in history, leading to the discovery of disease subtypes so that researchers and scientists across the globe are equipped to understand and ultimately end ALS.

### Strategy

The Answer ALS Research Program is a paradigm shift in how we study ALS and neurological disease more broadly. Unlike other tissues in the body, the brain and spinal cord cannot be biopsied without causing irreversible damage. However, recent advances in stem cell technology allow scientists to *recreate* an individual's brain and spinal cord cells in vitro.

Using cells isolated from a simple blood sample, researchers can generate lines of induced pluripotent stem cells (iPSCs). These iPSCs can then be directed to become motor neurons (MNs)—the specific cell type affected in ALS. By recreating patient-derived motor neurons, scientists can study how these cells differ from those of a healthy individual or another ALS patient.

For each enrolled participant, the program generates:

* Longitudinal clinical data
* Whole-genome sequences
* Multi-omics data (transcriptomics, epigenomics, proteomics) from iPSC-derived motor neurons

These data, along with associated bio-resources (including patient-derived biofluids, iPSC lines, and—for some participants—autopsy tissue), are standardized and made available to the global research community through the [Answer ALS Data Portal](https://data.answerals.org).

Combined with the wealth of data collected via a custom mobile app—designed for frequent, at-home assessments to monitor disease progression—and integrated multi-omics analyses, Answer ALS provides an immense body of knowledge and resources for the scientific community. By openly sharing data, samples, and findings, the program aims to have a global impact on ALS research.

Although focused on ALS, the Answer ALS Research Program is increasingly being recognized as a model for collaborative research in other neurological diseases. It represents a unique and necessary partnership across institutions, disciplines, and technologies, all united by a single mission: to answer ALS.

## Identifying which samples I will use

Source: <https://dataportal.answerals.org/data-information>

The clinical data tables and files included in the download package are essential resources for researchers seeking to gain insights. These tables and files contain detailed information about patient demographics and medical histories. Researchers can use this data to conduct analyses, generate statistics, and develop models to better understand disease progression and treatment effectiveness.

Included in the folder:

Not important:

* Clinical_Dictionary_v2_2023.csv – A reformatted and curated clinical dictionary for easier analysis. Download the file here.

* Clinical_Dictionary.csv – Raw data dictionary.

* Clinical Folder – This folder holds 33 csv files containing clinical measurements from de-identified participant visits.

* aals_participants v2.csv – A list of participants by ID indicating cohort group.

Most important:

* aals_dataportal_datatable.csv – A table view of high-level summary information keyed by participant ID. Information includes demographics, cell line QC and availability.

All columns: Participant_ID,GUID,NYGC_CGND_ID,HAS_GENOMICS,HAS_EPIGENOMICS,HAS_TRANSCRIPTOMICS,HAS_PROTEOMICS,Number_of_Visits,SEX,ETHNIC_CATEGORY,RACE,SUBJECT_GROUP,SUBJECT_SUBGROUP,REVISED_EL_ESCORIAL_CRITERIA,Site_of_Onset,Bulbar_Onset,Axial_Onset,Limb_Onset,Other_Onset,AGE_AT_SYMPTOM_ONSET,AGE_AT_DEATH,ALSFRS_R_Baseline_Value,ALSFRS_R_Latest_Value,ALSFRS_R_PROGRESSION_SLOPE,CBS_Baseline_Value,CBS_Latest_Value,COGNITIVE_PROGRESSION_SLOPE,HasIPSC,HasDIMN,root_iPSC_Line,iPSCLine,diMNs_line,Primary_Tissue,Age_at_First_PBMC_Collection,Batch,PCT_SMI32,PCT_ISL1,PCT_NKX61,PCT_TUJ1,PCT_S100b,PCT_Nestin,Staining_Details,ClinReport_Mutations_Details,HasVariant,EH_C9orf72,EH_ATXN2,C9orf72_repeat_length,ATXN2_repeat_length,WGS_Sequencing_Protocol_Used,Genomic_Sequencing_DNA_Source,External_Control

Relevant columns: Participant_ID,GUID,HAS_GENOMICS,HAS_TRANSCRIPTOMICS,HAS_PROTEOMICS,SEX,ETHNIC_CATEGORY,RACE

* aals_released_files.csv – A list of released files with the data path and size of each indicated.

All columns: Participant_ID,omic,CGND_ID,iPSC_Line,line,differentiation,data_level,experiment,path,size in bytes

Relevant columns: Participant_ID,omic,data_level,experiment,path

Additional data files available (<https://dataportal.answerals.org/data-information>):

1. Sample mapping information

* The use of a sample mapping file in controlling pipeline analysis for batch effects plays a crucial role in ensuring the reliability and reproducibility of results, especially in complex biological experiments like cell line differentiation studies.
* Batch effects can significantly skew data interpretation because they introduce variation that is not related to the biological variables being studied.

* sample_mapping_README.txt
* Sample-Mapping-File-Feb-2024.csv

All columns: Participant ID,Sample ID,GUID-Batch,GUID,Cell Line,Batch #,Vial ID,Site,Shipment

Relevant columns: Participant ID,Sample ID,GUID-Batch,Batch #,Shipment

1. Proteomic batch effects

52 samples from release one have been found to have strong batch effects. The extent to which these samples vary from the subsequent data has led us to advise users not to utilize these samples in their analyses.

* Proteomics_Batch_Effect_Samples_52.csv (list of participants with proteomic batch effects)

### Recommended usage of Sample-Mapping-File for pre-processing

* Before starting the analysis, use the sample mapping file to categorize my data according to the batch number. This involves segregating the cell line differentiation samples based on their batch and identifying the corresponding batch control samples.

## Filtering and Sample matching scripts

The following R scripts were used to prepare files for stratification for artificial batch generation.

* From these 1269 AnswerALS participants, I performed sample matching to filter the data.
* Briefly, participants were included if they had all three omics (WGS, RNA-Seq, and proteomic) data available.
* All other participants were excluded.
* Included participants who were identified as having strong batch effects in their proteomics data, were also excluded.
* Remaining participants were matched to the sample mapping file
* Epigenomic samples were removed
* The mapped sample file was split into BTC and BDC
* Filtered participants were merged with the dataportal table and released files

1. Participant filtering

Goal: Filter out participants who do not have all three omics types
Input: aals_dataportal_datatable.csv AND Proteomics_Batch_Effect_Samples_52.csv
Output: filtered_matched_aals.csv

```r
# 1_participant_filtering.R
# This script filters the metadata file so that only patients with all three data types remain.
# Also removes remianing participants with proteomic batch effects.

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

# Write the cleaned data to a new CSV file
write_csv(aals_filtered_cleaned, "filtered_matched_aals.csv")
```

* After filtering participants based on matched omics data, I was left with **347** unique participants left.

1. Sample mapping of filtered participants

Goal: Filter the Sample-Mapping-File-Feb-2024.csv to remove epigenomic data and merge it with the extracted columns from the large merged file.

Input: merged_aals_data.csv AND Sample-Mapping-File-Feb-2024.csv
Output: merged_mapping_TP_data.csv

```r
# 2_merged_tp_mapping.R
# Load necessary libraries
library(dplyr)
library(readr)
library(purrr)

# Load filtered and matched AALS data (script 1)
filtered_matched <- read_csv("filtered_matched_aals.csv")

# Load sample mapping file
sample_mapping <- read_csv("Sample-Mapping-File-Feb-2024.csv")

# Extract necessary columns and rename them to remove blank spaces
filtered_matched <- filtered_matched %>% 
  select(participant,sex,ethnicity,race,diagnosis)

sample_mapping <- sample_mapping %>% 
  select(
    participant = `Participant ID`,
    sample_id = `Sample ID`,
    guid_batch = `GUID-Batch`,
    seq_batch = `Batch #`,
    shipment = `Shipment`
  )

# Filter sample_mapping to only keep participants found in filter_matched file
sample_mapping_filtered <- sample_mapping %>%
  filter(participant %in% filtered_matched$participant)

# Remove epigenomics samples (sample IDs ending in "-E")
tp_sample_mapping <- sample_mapping_filtered %>%
  filter(!grepl("-E$", sample_id))

# Join filtered_matched and TP samples on participant
# inner_join() keeps only rows with matching participant values in both dataframes
filter_mapping <- filtered_matched %>%
  inner_join(tp_sample_mapping, by = "participant")

# Save full table 
write_csv(filter_mapping, "filtered_mapping_data.csv")
```

1. Extracting BDC vs BTC

Goal: Prepare a csv file that separates BDC and BTC samples
Input: filtered_mapping_data.csv
Output: stratify_bdc.csv AND stratify_btc.csv

```r
# 3_split_bcd_btc.R
# Load necessary libraries
library(dplyr)
library(readr)

# Load your data
mapping_data <- read_csv("filtered_mapping_data.csv")

# Separate BTC (seq_batch == "BTC") and BDC (numeric seq_batch)
btc <- mapping_data %>%
  filter(seq_batch == "BTC")

bdc <- mapping_data %>%
  filter(grepl("^\\d+$", seq_batch))  # keeps rows where seq_batch is all digits

# Save to CSV
write_csv(btc, "stratify_btc.csv")
write_csv(bdc, "stratify_bdc.csv")
```

1. Metadata merge

Goal: Generate a large merged csv file containing the metadata for the 347 participants
Input: filtered_matched_aals.csv AND aals_released_files.csv AND aals_dataportal_datatable.csv
Output: merged_aals_data.csv (full table) AND genomic_data_level2.csv, transcriptomic_data_level1.csv, proteomic_data_level1.csv (omic type tables)

```r
# 4_aals_full_merge.R
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
```

## Notes for downloading AnswerALS data from Neuromine using CLI

### Data Level Descriptions

-Level 1 data is raw, immutable data coming off an instrument (e.g. a sequencer). For genomics, we only provide data corresponding to this level upon special request.
-Level 2 data is raw data mapped against the appropriate reference. Genomics (wgs) uses hg38 as a reference.
-Level 3 data the most processed form of patient-specific data.
-Level 4 data is attained from the joining of a cohort of patients’ level 3 data from a particular assay.
-Level 5 data is comparative data between two specific cohorts typically labelled as differentially expressed genes (DESeq) or proteins or enriched sites within the genome (DiffBind)

### Chosen data levels

**Proteomics:** raw data coming off a mass spectrometer is called a wiff file: ~2.5GB/individual - TODO: changed to mzML files

**Genomics:** raw, immutable data coming off an instrument (e.g. a sequencer) called a FASTQ file. FASTQ is a text-based sequencing data file format that stores both raw sequence data and quality scores: ~54.5 GB/individual

**Transcriptomics:** raw data coming off an instrument (e.g. a sequencer) is also called a FASTQ file. FASTQ is a text-based sequencing data file format that stores both raw sequence data and quality scores: ~5GB/individual  1

---

### Data Selection

Total sizes of all files in downloaded level:

1269 participants total

* Genomics: 18TB (939 participants)
* Transcriptomics: 3.9TB (650 participants)
* Proteomics: 488GB (499 participants)
* Total: 23TB

However, I am only using 347 participants (after filtering - see below)

* Genomics: 6.7TB
* Transcriptomics: 2.1TB
* Proteomics: 340GB
* Total: 9.2TB

---

## Data Download from Neuromine

### AnswerALS Download Tool

* On Neuromine data search page, download the Linux version of Download Tool (answer-als-download-tool-linux-x64)
* Extract folder and transfer to hemera using rsync

```bash
rsync -avP answer-als-download-tool-linux-x64/ kcoetzer@hemera.mb.sun.ac.za:/home/kcoetzer/
```

### Install tool on hemera and download files

```bash
# These steps are done on hemera
# Use tmux for large downloads 

# Install the tool
cd /home/kcoetzer/answer-als-download-tool-linux-x64/CLI
./downloadtool

# Login to Neuromine to Activate CLI
# NOTE: -c (access code) is temporary and must be activated every two minutes from: https://dataportal.answerals.org/activate
./downloadtool login -u kimberlycoetzer@gmail.com -c 396714

# Configure the download location 
./downloadtool config -s LocalDownloadPath "/home/kcoetzer/DATA/"

# View list of available saved search results with list command. 
./downloadtool list

# Example output
# SEARCH ID                SEARCH NAME         TIMESTAMP                DOWNLOAD SIZE
# g8ZW+mmAqkyKf2bwuc4bzQ   wiff_aals           06/02/2025 10:39:58      488 GB
# n4Ag2_5hx0iWW5GATIEZTg   level4_aals         06/02/2025 10:39:44      319 MB

# Start the data download 
# -n is the search name chosen on the Neuromine website
./downloadtool start -n level4_aals 
```

### OPTIONAL: Unpack DATA subdirectories

* The download files from Neuromine typically appear as a folder with many subdirectories
* For example: /home/kcoetzer/DATA/genomics/2_cram/CASE-NEUZY975XKL/CASE-NEUZY975XKL-01338-G/CASE-NEUZY975XKL-01338-G_1.final.cram
* In some cases, it can be helpful to unpack the files so that the path is not as long
* For example: /home/kcoetzer/DATA/genomics/CASE-NEUZY975XKL-01338-G/CASE-NEUZY975XKL-01338-G_1.final.cram is better.

```py
# unpack_dir.py
import os
import shutil
import argparse

def unpack_files(main_dir):
    # Traverse the directory
    for subdir, _, files in os.walk(main_dir):
        for file in files:
            # Create full path to the file
            file_path = os.path.join(subdir, file)
            # Move file to the main directory
            shutil.move(file_path, main_dir)

    # Remove empty subdirectories
    for subdir, dirs, _ in os.walk(main_dir, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(subdir, dir)
            try:
                os.rmdir(dir_path)
            except OSError:
                # Directory is not empty
                pass

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Unpack files from subdirectories into a main directory.")
    parser.add_argument("main_directory", type=str, help="Path to the main directory containing subdirectories.")
    # Parse arguments
    args = parser.parse_args()

    # Call the unpack function with the provided directory
    unpack_files(args.main_directory)
```

### Renaming data files

* Some file names are inconsistent. For example: fastq vs. fq
* To make things easier and ensure that pipelines run smoothly, it is helpful to rename all the files to be the same.
* This should only be an issue with the transcriptomics files since the other data types are .cram and .wiff files with consistent naming conventions.

```python
# rename_fastq.py
import os
import re

# Directory containing the files to edit
directory = '/home/kcoetzer/DATA/'

# Function to rename files
def rename_files(directory):
    # Use os.walk to iterate over directories and subdirectories
    for root, _, files in os.walk(directory):
        # Iterate over all files in each directory
        for filename in files:
            # Looks for files with 'fastq.gz' extension
            if re.match(r'.*\.fastq\.gz$', filename):
                # If the file already has the correct extension, don't do anything
                continue
            elif re.match(r'.*\.fq$', filename):  # Looks for files with fq extension
                new_filename = filename + '.gz'  # Adds .gz to the files with .fq extension
            elif re.match(r'.*\.fq\.gz$', filename):  # Looks for files with fq.gz extension
                new_filename = re.sub(r'\.fq\.gz$', '.fastq.gz', filename)  # Changes fq.gz to fastq.gz
            else:
                # Skip files with other extensions
                continue

            # Full paths for the old and new filenames
            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_filename)  # Rename the file with its new path
            os.rename(old_path, new_path)
            print(f'Renamed: {old_path} to {new_path}')  # Optional: Print the change

# Call the function to start
rename_files(directory)
```

### Move multiple files to a directory

* Helpful when moving a large number of folders or files to a directory

```bash
# move_files.sh
#!/bin/bash

# Define the destination directory
DEST_DIR="/home/kcoetzer/DATA/transcriptomics/1_fastq/rna_samples/batch1"

# Iterate moving over multiple files
while IFS= read -r file; do
  mv "$file" "$DEST_DIR"
done < "batch1.txt" # one file or directorie to move per line
```

### Rewrite file as csv

* Easy way to safely convert a txt file to a csv file

```python
# txt_2_csv.py
import csv

# Open the text file for reading
with open('rna_data.txt', 'r') as txt_file:
    lines = txt_file.readlines()

# Open the CSV file for writing
with open('rna_data.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)

    for line in lines:
        # Split each line by spaces or tabs, adjust as needed
        row = line.strip().split()
        writer.writerow(row)
```

### Keep participants of interest

* As mentioned previously, only 347 out of over 1000 participants are being used.

```bash
# keep_matched_samples.sh
#!/bin/bash

while IFS= read -r line; do
  mv "$line" /home/kcoetzer/DATA/transcriptomics/1_fastq/rna_samples
done < "participants.txt" # one participant per line
```

### Next.... sample stratification to generate artificial batches
