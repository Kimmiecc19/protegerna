# Combine the per-domain filter summaries into one step-by-domain table.
# Results are from the filter_biotools.R script
# Rscript combine_filter_summaries.R [--results-dir=path/to/results_filter_biotools]

main <- function() {
  suppressPackageStartupMessages({
    library(readr)
    library(dplyr)
    library(purrr)
  })

  # Works with Rscript (--file=) and source().
  script_path <- c(sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)),
    unlist(lapply(sys.frames(), function(frame) frame$ofile)))
  script_path <- tail(script_path[file.exists(script_path)], 1)
  if (!length(script_path)) stop("Run with Rscript or source() the script by its path.")
  dir_arg <- grep("^--(?:output|results)-dir=", commandArgs(trailingOnly = TRUE), value = TRUE, perl = TRUE)
  if (length(dir_arg) > 1L) stop("Supply only one results directory.")
  output_dir <- normalizePath(if (length(dir_arg)) sub("^--(?:output|results)-dir=", "", dir_arg, perl = TRUE) else
    file.path(dirname(script_path), "results_filter_biotools"), mustWork = TRUE)

  omic_files <- c(
    genomic        = file.path(output_dir, "genomics_filter_summary.tsv"),
    transcriptomic = file.path(output_dir, "transcriptomics_filter_summary.tsv"),
    proteomic      = file.path(output_dir, "proteomics_filter_summary.tsv"),
    multiomic      = file.path(output_dir, "multiomics_filter_summary.tsv")
  )
  # Canonical step order, as written by filter_biotools_final2026.R.
  steps_keep <- c("initial_load", "unique_records", "scope_included", "scope_review", "scope_out_of_scope",
    "access_and_license_eligible", "programmatic_scope", "publication_traceable", "citation_eligible", "final_candidate")

  read_omic <- function(path, omic_name) {
    summary_table <- read_tsv(path, show_col_types = FALSE)
    if (!all(c("step", "tools_remaining") %in% names(summary_table))) stop("Invalid filter summary schema: ", path)
    if (anyNA(summary_table$step) || anyDuplicated(summary_table$step) || any(!summary_table$step %in% steps_keep)) {
      stop("Invalid or duplicate filter steps: ", path)
    }
    counts <- summary_table$tools_remaining
    if (!is.numeric(counts) || anyNA(counts) || any(!is.finite(counts) | counts < 0 | counts != floor(counts))) {
      stop("Filter counts must be nonnegative integers: ", path)
    }
    transmute(summary_table, step, !!omic_name := as.integer(tools_remaining))
  }

  combined <- imap(omic_files, read_omic) |>
    reduce(full_join, by = "step") |>
    mutate(step = factor(step, levels = steps_keep)) |>
    arrange(step)
  print(combined, n = Inf)
  write_csv(combined, file.path(output_dir, "combined_filter_summaries_final.csv"))
  write_tsv(combined, file.path(output_dir, "combined_filter_summaries_final.tsv"))
}

main()
