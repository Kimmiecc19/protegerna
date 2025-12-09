# Load the wrapper function script if it's in a file
source("filter_biotools_18June2025.R")

filter_biotools(
  input_file = "proteomics_may2025.tsv",
  keep_file = "proteomic_keep_june2025.tsv",
  filter_file = "general_filter_june2025.tsv",
  function_file = "general_functions.csv",
  filter_summary_tool = "proteomics_filter_summary.tsv",
  output_file = "proteomic_annotated_filtered_tools.tsv",
  output_file_rds = "proteomic_annotated_filtered_tools.rds"
)

filter_biotools(
  input_file = "multiomics_may2025.tsv",
  keep_file = "multiomic_keep_june2025.tsv",
  filter_file = "general_filter_june2025.tsv",
  function_file = "general_functions.csv",
  filter_summary_tool = "multiomics_filter_summary.tsv",
  output_file = "multiomic_annotated_filtered_tools.tsv",
  output_file_rds = "multiomic_annotated_filtered_tools.rds"
)


filter_biotools(
  input_file = "transcriptomics_may2025.tsv",
  keep_file = "transcriptomic_keep_june2025.tsv",
  filter_file = "general_filter_june2025.tsv",
  function_file = "general_functions.csv",
  filter_summary_tool = "transcriptomics_filter_summary.tsv",
  output_file = "transcriptomic_annotated_filtered_tools.tsv",
  output_file_rds = "transcriptomic_annotated_filtered_tools.rds"
)


filter_biotools(
  input_file = "genomics_may2025.tsv",
  keep_file = "genomic_keep_june2025_3.tsv",
  filter_file = "general_filter_june2025.tsv",
  function_file = "general_functions.csv",
  filter_summary_tool = "genomics_filter_summary.tsv",
  output_file = "genomic_annotated_filtered_tools.tsv",
  output_file_rds = "genomic_annotated_filtered_tools.rds"
)