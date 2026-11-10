# Combine the per-domain filter summaries into one step-by-domain table.
# Results are from the 02a_filter_biotools.R script
# Rscript 02b_combine_filter_summaries.R [--results-dir=results/02a_results_filter_biotools]
#                                       [--output-dir=results/02bc_results_edam_annotation]
# Reads <omic>_filter_summary.tsv, or a single suffixed copy such as <omic>_filter_summary_jan2026.tsv.

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
  cli <- commandArgs(trailingOnly = TRUE)
  dir_option <- function(name, default) {
    hit <- grep(paste0("^--", name, "="), cli, value = TRUE)
    if (length(hit) > 1L) stop("Supply --", name, " only once.")
    if (length(hit)) sub(paste0("^--", name, "="), "", hit) else default
  }
  script_dir <- dirname(normalizePath(script_path))
  results_dir <- normalizePath(dir_option("results-dir",
    file.path(script_dir, "results", "02a_results_filter_biotools")), mustWork = TRUE)
  output_dir <- dir_option("output-dir", file.path(script_dir, "results", "02bc_results_edam_annotation"))
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  # 02a writes <omic>_filter_summary.tsv; the saved dissertation copies carry a suffix (_jan2026).
  find_summary <- function(omic) {
    exact <- file.path(results_dir, paste0(omic, "_filter_summary.tsv"))
    if (file.exists(exact)) return(exact)
    hits <- list.files(results_dir, pattern = paste0("^", omic, "_filter_summary_.*\\.tsv$"), full.names = TRUE)
    if (length(hits) != 1L) stop("Expected one ", omic, "_filter_summary*.tsv in ", results_dir, ", found ", length(hits))
    hits
  }
  omic_files <- c(
    genomic        = find_summary("genomics"),
    transcriptomic = find_summary("transcriptomics"),
    proteomic      = find_summary("proteomics"),
    multiomic      = find_summary("multiomics")
  )
  # Canonical step order, as written by filter_biotools_final2026.R.
  steps_keep <- c("initial_load", "unique_records", "scope_included", "scope_review", "scope_out_of_scope",
    "access_and_license_eligible", "programmatic_scope", "publication_traceable", "citation_eligible", "final_candidate")

  read_omic <- function(path, omic_name) {
    summary_table <- read_tsv(path, show_col_types = FALSE)
    names(summary_table) <- tolower(names(summary_table))  # the saved _jan2026 copies use a "Step" header
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
