# bio.tools Omics Landscape - FULL RETRIEVED POPULATION -----------------------
# Age-citation and registration analyses

# Purpose: Rerun the age-citation and registration analyses of
#          01_visualize_biotools.R on the full retrieved (unfiltered)
#          population instead of the filtered adoption-candidate population.
#
# Input:   <stem>_all_records_quality_flags.rds (or .tsv) written by
#          filter_biotools.R, i.e. every retrieved record before
#          any eligibility gate (populations$full_suffix in the config).
#
# Configuration, palette, publication metrics, trend helpers and figure builders
# are shared with 01_visualize_biotools.R so the two sets of outputs are
# directly comparable. The only differences are:
#   * figure titles say "retrieved" instead of "candidate", and the trend
#     caption does not claim that the citation filter created the step at the
#     boundary (no filter is applied to this population);
#   * a registration-delay summary table is written (it supports the
#     publication-vs-registration table in the chapter);
#   * `populations.registration_population` in YAML controls which records enter
#     the registration analyses: "all_records" uses every retrieved record
#     (default); "with_citations" requires an eligible citation count and
#     publication year. Age-citation analyses require both under either setting.
#
# Run: Rscript 03_visualize_age_registration_full_population.R [--config=path/to/visualize_config.yaml]

main <- function() {

  # 1. Packages, configuration and shared helpers -------------------------------

  pkgs <- c("tidyverse", "jsonlite", "yaml", "glue", "scales", "ggrepel", "patchwork", "lubridate", "conflicted")
  missing_pkgs <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing_pkgs)) {
    stop("Missing required R packages: ", paste(missing_pkgs, collapse = ", "),
      ". Install them in the project environment before running this analysis.")
  }
  invisible(lapply(pkgs, library, character.only = TRUE))
  conflicts_prefer(dplyr::filter, .quiet = TRUE)
  conflicts_prefer(dplyr::lag, .quiet = TRUE)

  script_path <- c(sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)),
    unlist(lapply(sys.frames(), function(frame) frame$ofile)))
  script_path <- normalizePath(tail(script_path[file.exists(script_path)], 1), winslash = "/")
  if (!length(script_path)) stop("Run with Rscript or source() the script by its path.")
  script_dir <- dirname(script_path)
  config_arg <- grep("^--config=", commandArgs(trailingOnly = TRUE), value = TRUE)
  config_file <- normalizePath(if (length(config_arg)) sub("^--config=", "", config_arg[[1]]) else
    file.path(script_dir, "visualize_config.yaml"), winslash = "/", mustWork = TRUE)

  helper_paths <- file.path(script_dir, c("analysis_helpers.R", "landscape_plot_helpers.R", "thesis_palette.R"))
  for (path in helper_paths) source(path, local = TRUE)
  set_thesis_geom_defaults()
  config <- validate_visualize_config(yaml::read_yaml(config_file))
  registration_population <- config$populations$registration_population
  expected_citation_source <- config$citations$source
  analysis_date <- as.Date(config$analysis_date)
  current_year <- lubridate::year(analysis_date)
  citation_filter_year <- as.integer(config$candidate_filter$no_threshold_from_year)

  run_date <- Sys.Date()
  run_tag <- format(run_date, "%Y%m%d")
  output_dir <- file.path(script_dir, "results_tool_analysis", paste0("output_visualizations_full_population_", run_tag))
  dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)
  exporters <- make_analysis_exporters(output_dir, run_tag, plot_saver = save_thesis_plot)
  save_output <- exporters$save_output
  save_plot <- exporters$save_plot

  options(stringsAsFactors = FALSE, readr.show_col_types = FALSE, scipen = 999)
  set.seed(as.integer(config$random_seed))

  axis_labels <- list(
    year_added = "Year added to bio.tools",
    age = "Years since earliest linked publication",
    citations_log = "Dimensions citations (complete coverage; log1p)",
    tool_count = "Tool-domain records",
    tool_share = "Share of records added that year"
  )
  legend_labels <- list(omics = "Omics domain", status = "Outlier status")
  title_suffix <- " (full retrieved population)"
  name_suffix <- "_full_population"

  # 2. Input: the full retrieved population -----------------------------------------

  filter_results_dir <- resolve_config_path(config$inputs$filter_results_dir, config_file, must_work = TRUE)
  omic_files <- population_files(filter_results_dir, unlist(config$populations$domains, use.names = TRUE),
    config$populations$full_suffix)
  tools_full <- prepare_publication_analysis(read_omic_tables(omic_files), expected_citation_source)

  # The audit file keeps flagged duplicates; the full retrieved population used
  # in the chapter is one record per biotools_id and domain.
  if ("flag_duplicate_record" %in% names(tools_full)) {
    tools_full <- tools_full %>% filter(!(flag_duplicate_record %in% TRUE))
  }
  tools_full <- tools_full %>%
    filter(!is.na(biotools_id), nzchar(trimws(biotools_id))) %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE)
  save_output(publication_coverage_summary(tools_full), "full_population_citation_coverage")
  message(glue("Full retrieved population: {scales::comma(nrow(tools_full))} tool-domain records, ",
    "{scales::comma(n_distinct(tools_full$biotools_id))} distinct registry entries"))

  # Derived fields (same definitions as the candidate analysis), applied to every record.
  df_all <- derive_publication_metrics(tools_full, analysis_date, names(omic_palette))
  # Age-citation analyses require eligible citations and a publication year.
  df_for_plots <- df_all %>% filter(!is.na(total_citations), !is.na(publication_year))
  df_registration <- if (registration_population == "all_records") df_all else df_for_plots
  message(glue("Registration analyses use {scales::comma(nrow(df_registration))} records ({registration_population}); ",
    "age-citation analyses use {scales::comma(nrow(df_for_plots))} records with citations and a publication year."))

  filter_boundary_age <- current_year - citation_filter_year + 0.5
  # No citation filter is applied to this population, so the caption does not
  # attribute the step at the boundary to the filter.
  trend_caption <- glue(
    "Dotted line: publication year {citation_filter_year}, the boundary used by the candidate citation filter. No citation filter is applied to this population; ",
    "trends are fitted separately either side of the boundary, as in the candidate analysis, so the two sets of figures are comparable.\n",
    "Lines: LOESS (span {config$trend$span}) with 95% CI; straight line where a side has < {config$trend$min_loess_n} records; ",
    "lines end at the {round(100 * as.numeric(config$trend$tail_quantile))}th percentile of age."
  )

  # 3. Registration: records added to bio.tools per year ------------------------

  added_per_year <- df_registration %>%
    filter(!is.na(added)) %>%
    count(added = as.integer(added), omic_type) %>%
    arrange(added)
  save_output(added_per_year, "added_per_year_full_population")
  save_plot(build_added_year_plot(added_per_year, axis_labels, nrow(df_registration),
      "retrieved tool-domain records", title_suffix),
    "tools_added_per_year_by_omics_full_population", width = 10, height = 8, dpi = 300)

  added_per_year_pct <- added_per_year %>% group_by(added) %>% mutate(pct_within_year = n / sum(n)) %>% ungroup()
  save_output(added_per_year_pct, "added_per_year_pct_full_population")
  save_plot(build_added_year_pct_plot(added_per_year_pct, axis_labels, title_suffix),
    "tools_added_per_year_by_omics_pct_full_population", width = 10, height = 8, dpi = 300)

  # 4. Publication year vs year added to bio.tools ------------------------------

  df_pub_added <- publication_vs_added_records(df_registration)
  save_plot(build_pub_vs_added_plot(df_pub_added, current_year, title_suffix),
    "publication_vs_year_added_scatter_full_population", width = 10, height = 6, dpi = 300)

  # Registration delay summary (supports the publication-vs-registration table).
  registration_delay <- df_pub_added %>%
    mutate(delay = added - publication_year,
      publication_period = cut(publication_year, breaks = c(-Inf, 2009, 2014, 2019, Inf),
        labels = c("Before 2010", "2010-2014", "2015-2019", "2020 onward")))
  summarise_delay <- function(d) {
    d %>% summarise(
      n = n(),
      median_delay_years = median(delay),
      registered_same_year = mean(delay == 0),
      registered_within_1_year = mean(abs(delay) <= 1),
      registered_before_publication = mean(delay < 0),
      registered_after_publication = mean(delay > 0),
      .groups = "drop"
    )
  }
  registration_delay_summary <- bind_rows(
    registration_delay %>% group_by(omic_type = "All domains", publication_period = as.character(publication_period)) %>% summarise_delay(),
    registration_delay %>% group_by(omic_type = "All domains", publication_period = "All periods") %>% summarise_delay(),
    registration_delay %>% group_by(omic_type = as.character(omic_type), publication_period = "All periods") %>% summarise_delay()
  )
  save_output(registration_delay_summary, "registration_delay_summary_full_population")

  # 5. Age vs citations (same analysis and figures as the candidate workflow) ----

  age_citations <- age_citation_analysis(df_for_plots, current_year, filter_boundary_age, config$trend)
  save_output(bind_rows(age_citations$trend_all %>% mutate(omic_type = "All domains"),
    age_citations$trend_by_omic %>% mutate(omic_type = as.character(omic_type))),
    "age_citation_trends_full_population")
  save_output(age_citations$outliers, "age_citation_outliers_full_population")
  message(glue("Identified {nrow(age_citations$outliers)} outliers (|residual| > {round(age_citations$threshold, 2)})"))
  save_age_citation_figures(age_citations, save_plot, axis_labels, legend_labels, trend_caption,
    boundary = filter_boundary_age, boundary_label = "Candidate-filter boundary (not applied)",
    records_label = "retrieved tool-domain records with a citation count and publication year",
    title_suffix = title_suffix, name_suffix = name_suffix)

  # 6. Spearman correlation and citation summary by publication band -------------

  stats_base <- df_for_plots %>%
    mutate(total_citations = as.numeric(total_citations),
      filter_band = if_else(publication_year >= citation_filter_year,
        glue("Published >= {citation_filter_year}"), glue("Published < {citation_filter_year}")))
  save_output(age_citation_spearman(stats_base), "stats_age_citations_full_population")

  summarise_citations <- function(d) {
    summarise(d, n = n(), median_total_citations = median(total_citations),
      q1 = quantile(total_citations, 0.25), q3 = quantile(total_citations, 0.75), .groups = "drop")
  }
  citation_summary <- bind_rows(
    stats_base %>% group_by(group = as.character(filter_band)) %>% summarise_citations(),
    stats_base %>% summarise_citations() %>% mutate(group = "All records", .before = 1)
  )
  save_output(citation_summary, "citation_summary_full_population")

  # 7. Figure audit and reproducibility manifest -------------------------------

  full_audit <- function(figure_name, plotted_records) {
    df_all %>% count(omic_type, name = "eligible_tools") %>% transmute(
      figure_name = figure_name, population = "Full retrieved population",
      omic_type = as.character(omic_type), eligible_tools,
      plotted_tools = map_int(omic_type, ~ sum(plotted_records$omic_type == .x, na.rm = TRUE)),
      missing_or_unobserved = eligible_tools - plotted_tools)
  }
  figure_audit <- bind_rows(
    full_audit("age_vs_citations_combined_full_population", age_citations$data),
    full_audit("tools_added_per_year_by_omics_full_population", filter(df_registration, !is.na(added))),
    full_audit("publication_vs_year_added_scatter_full_population", df_pub_added)
  ) %>% mutate(audit_date = as.character(analysis_date), registration_population = registration_population)
  if (any(figure_audit$missing_or_unobserved < 0)) stop("Assertion failed: negative missingness in figure audit.")
  save_output(figure_audit, "figure_level_audit_full_population")

  input_paths <- c(prefer_rds_population(unname(omic_files)), script_path, helper_paths, config_file)
  manifest <- list(
    pipeline = "bio.tools age-citation and registration analyses, full retrieved population",
    analysis_date = as.character(analysis_date),
    run_date = as.character(run_date),
    population_unit = "biotools_id + omic_type tool-domain record",
    citation_policy = list(source = expected_citation_source,
      coverage = "complete and conflict-free for citation analyses; registration retains all records",
      raw_total = "total_citations_reported", age_denominator = "Years since earliest available linked publication, inclusive"),
    registration_population = registration_population,
    counts = list(
      full_retrieved_records = nrow(df_all),
      unique_biotools_entries = n_distinct(df_all$biotools_id),
      records_with_citations_and_publication_year = nrow(df_for_plots),
      registration_records = nrow(df_registration),
      publication_vs_added_records = nrow(df_pub_added),
      age_citation_outliers = nrow(age_citations$outliers),
      outlier_threshold_log1p = age_citations$threshold
    ),
    trend = list(span = config$trend$span, boundary_publication_year = citation_filter_year,
      min_loess_n = as.integer(config$trend$min_loess_n),
      tail_quantile = as.numeric(config$trend$tail_quantile)),
    inputs = lapply(normalizePath(input_paths, winslash = "/"), function(p) list(path = p, md5 = unname(tools::md5sum(p)))),
    software = list(R = R.version.string, platform = R.version$platform,
      packages = as.list(vapply(c("dplyr", "readr", "ggplot2", "tidyr", "purrr", "yaml", "lubridate",
        "glue", "scales", "ggrepel", "patchwork"),
        function(pkg) as.character(utils::packageVersion(pkg)), character(1)))),
    outputs = lapply(sort(list.files(output_dir, pattern = paste0("_", run_tag, "\\.(csv|png)$"), full.names = TRUE)),
      function(p) list(file = basename(p), md5 = unname(tools::md5sum(p))))
  )
  jsonlite::write_json(manifest,
    file.path(output_dir, paste0("reproducibility_manifest_full_population_", run_tag, ".json")),
    pretty = TRUE, auto_unbox = TRUE, na = "null")
  message(glue("Done. Outputs written to {normalizePath(output_dir, winslash = '/')}"))
}

main()
