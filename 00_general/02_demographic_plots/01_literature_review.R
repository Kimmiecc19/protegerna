# Run with this script's folder as the working directory.
# In RStudio: Session > Set Working Directory > To Source File Location.
csv_path <- file.path("..", "01_filtering_matching_patients", "data", "aals_metadata_neuromine",
  "aals_dataportal_datatable.csv")
source("thesis_palette.R")
source("plot_helpers.R")
participants <- read_cohort(csv_path)
make_plots(participants, participants, "figures_literature_review", "Full portal cohort")
