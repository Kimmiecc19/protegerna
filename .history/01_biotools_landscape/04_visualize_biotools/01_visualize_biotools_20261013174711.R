# bio.tools Omics Landscape ------------------------------------------------

# Purpose: Visually investigate the omics tool landscape
# Run: Rscript visualize_biotools.R [--config=path/to/visualize_config.yaml]
# GitHub authentication is read from the configured environment variable.
# Frozen-cache runs use previously retrieved repository metadata.

# Sys.setenv(
#   GITHUB_TOKEN = rstudioapi::askForPassword("")
# )
# nzchar(Sys.getenv("GITHUB_TOKEN"))

main <- function() {

  # 1. Packages, configuration and shared helpers -------------------------------
  # Load required R packages and set up the analysis environment.

  pkgs <- c("tidyverse", "httr", "jsonlite", "yaml", "glue", "scales", "ggrepel", "patchwork",
    "lubridate", "ggridges", "conflicted")
  missing_pkgs <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing_pkgs)) {
    stop("Missing required R packages: ", paste(missing_pkgs, collapse = ", "),
      ". Install them in the project environment before running this analysis.")
  }
  invisible(lapply(pkgs, library, character.only = TRUE))
  conflicts_prefer(dplyr::filter, .quiet = TRUE)
  conflicts_prefer(dplyr::lag, .quiet = TRUE)

  # Works with Rscript (--file=) and source().
  script_path <- c(sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)),
    unlist(lapply(sys.frames(), function(frame) frame$ofile)))
  script_path <- normalizePath(tail(script_path[file.exists(script_path)], 1), winslash = "/")
  if (!length(script_path)) stop("Run with Rscript or source() the script by its path.")
  script_dir <- dirname(script_path)
  config_arg <- grep("^--config=", commandArgs(trailingOnly = TRUE), value = TRUE)
  config_file <- normalizePath(if (length(config_arg)) sub("^--config=", "", config_arg[[1]]) else
    file.path(script_dir, "visualize_config.yaml"), winslash = "/", mustWork = TRUE)

  helper_paths <- file.path(script_dir, c("analysis_helpers.R", "landscape_plot_helpers.R",
    "github_helpers.R", "edam_curation_analysis.R", "thesis_palette.R"))
  for (path in helper_paths) source(path, local = TRUE)
  set_thesis_geom_defaults()
  config <- validate_visualize_config(yaml::read_yaml(config_file))
  expected_citation_source <- config$citations$source
  analysis_date <- as.Date(config$analysis_date)
  current_year <- lubridate::year(analysis_date)
  # First publication year kept without a citation threshold by the candidate filter.
  citation_filter_year <- as.integer(config$candidate_filter$no_threshold_from_year)
  domain_levels <- names(omic_palette)

  # 2. Output paths and exporters ------------------------------------------------
  # Create a timestamped output folder and define functions to save plots and tables with consistent naming. The exporters also record the paths of all written outputs for later reference.

  run_date <- Sys.Date()
  run_tag <- format(run_date, "%Y%m%d")
  output_dir <- file.path(script_dir, "results_tool_analysis", paste0("output_visualizations_URL_", run_tag))
  dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

  written_output_paths <- character()
  record_output <- function(path) {
    written_output_paths <<- unique(c(written_output_paths, normalizePath(path, winslash = "/", mustWork = TRUE)))
    invisible(path)
  }
  exporters <- make_analysis_exporters(output_dir, run_tag,
    plot_saver = save_thesis_plot, record_output = record_output,
    companion_tables = c("tool_domain_records", "filtered_adoption_candidate_population", "top_by_score_git"))
  save_output <- exporters$save_output
  save_plot <- exporters$save_plot

  # 3. Load the candidate population --------------------------------------------
  # Load the candidate tool-domain population from the filter results, augment it with GitHub metadata, and save intermediate tables for later analysis.

  filter_results_dir <- resolve_config_path(config$inputs$filter_results_dir, config_file, must_work = TRUE)
  domain_map <- unlist(config$populations$domains, use.names = TRUE)
  omic_files <- population_files(filter_results_dir, domain_map, config$populations$candidate_suffix)

  tools_combined <- prepare_publication_analysis(read_omic_tables(omic_files), expected_citation_source)
  save_output(publication_coverage_summary(tools_combined), "candidate_citation_coverage")

  tools_cleaned <- derive_publication_metrics(distinct(tools_combined, biotools_id, omic_type, .keep_all = TRUE), analysis_date)
  save_output(tools_cleaned, "tools_cleaned_cache", "rds")

  # 4. GitHub metadata -------------------------------------------------------------
  # Augment the candidate population with GitHub metadata, using a cached retrieval if available. The cache is updated with any new repositories found in the candidate population.

  tools_with_github <- tools_cleaned %>%
    mutate(github_url = str_extract(paste(homepage, documentation, sep = " "), "https?://github\\.com/[^/\\s]+/[^/\\s]+"),
      github_repo = str_remove(github_url, "https?://github\\.com/"))

  cache_file <- resolve_config_path(config$inputs$github_cache, config_file)
  cache_df <- update_github_cache(tools_with_github, config, cache_file)

  # Reference date for commit-recency status. It must not be earlier than the
  # latest GitHub retrieval, otherwise pushes made after the reference date
  # produce negative ages and are silently classed as Active.
  maintenance_ref_date <- as.Date(config$maintenance$reference_date)
  github_retrieval_dates <- suppressWarnings(as.Date(cache_df$retrieved_at))
  github_retrieval_range <- if (all(is.na(github_retrieval_dates))) c(NA_character_, NA_character_) else
    as.character(range(github_retrieval_dates, na.rm = TRUE))
  n_pushes_after_reference_date <- sum(suppressWarnings(as.Date(cache_df$last_push_at)) > maintenance_ref_date, na.rm = TRUE)
  if (n_pushes_after_reference_date > 0L) {
    warning(glue("{n_pushes_after_reference_date} cached repositories have a last push after the commit-recency reference date ",
      "({maintenance_ref_date}). Set maintenance.reference_date to the final GitHub retrieval date."), call. = FALSE)
  }
  message(glue("Commit-recency reference date: {maintenance_ref_date}; GitHub retrieval range: ",
    "{github_retrieval_range[1]} to {github_retrieval_range[2]}; rows without retrieval date: ",
    "{sum(is.na(github_retrieval_dates))}"))

  tools_augmented_github <- tools_with_github %>%
    left_join(cache_df, by = "github_repo") %>%
    mutate(last_push_at = as.Date(last_push_at), last_push_year = year(last_push_at),
      across(c(stars, forks, watchers, open_issues), as.numeric))
  save_output(tools_augmented_github, "tools_augmented_github_full", "rds")
  save_output(tools_augmented_github, "tools_augmented_github_full")

  options(stringsAsFactors = FALSE, readr.show_col_types = FALSE, scipen = 999)
  set.seed(as.integer(config$random_seed))

  # 5. Figure wording and palettes -------------------------------------------------
  # Define consistent axis and legend labels for all figures, and save the color palettes used in the analysis for reproducibility. 
  # The palettes include colors for omics domains, license classes, maintenance status, and primary/secondary thesis colors.

  # Axis wording used by every figure. log1p = log(1 + x).
  axis_labels <- list(
    publication_year = "Publication year",
    year_added = "Year added to bio.tools",
    age = "Years since earliest linked publication",
    citations_log = "Dimensions citations (complete coverage; log1p)",
    citations_per_year_log = "Citations / years since earliest linked publication (log1p)",
    tool_count = "Tool-domain records",
    tool_share = "Share of records added that year",
    share = "Share of tool-domain records",
    composite_score = "Composite score (0-1)",
    github_engagement_log = "GitHub stars + forks + watchers (log1p)"
  )
  legend_labels <- list(omics = "Omics domain", maintenance = "Commit-recency status", status = "Outlier status")

  palette_path <- file.path(output_dir, "palettes.rds")
  saveRDS(list(omic_type = omic_palette, license = license_palette, maintenance = maintenance_palette,
    primary = thesis_primary, secondary = thesis_secondary, neutral = thesis_neutral), palette_path)
  record_output(palette_path)
  message(glue("Wrote palettes → {basename(palette_path)}"))

  # 6. Working tables ------------------------------------------------------------------
  # Create working tables for the analysis. These get referenced in the figures and tables of the dissertation. 
  # The tables include the candidate tool-domain records, the filtered adoption candidate population, and the top tools by composite score (GitHub-observable records only).

  # One row per tool-domain record. The listed columns are moved to the end.
  df_for_plots <- tools_augmented_github %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    select(-any_of(c("github_repo", "publication_abstract", "publication_title", "homepage", "documentation")), everything())
  if (any(is.na(df_for_plots$biotools_id) | !nzchar(trimws(df_for_plots$biotools_id)))) {
    stop("Assertion failed: candidate tool-domain population contains missing biotools_id values.")
  }

  tool_domain_records <- df_for_plots %>%
    transmute(biotools_id, omic_type, name, citation_coverage, citation_source, citation_analysis_eligible,
      total_citations_reported, total_citations = as.numeric(total_citations),
      publication_year = as.integer(publication_year),
      stars = as.numeric(stars), forks = as.numeric(forks), watchers = as.numeric(watchers),
      open_issues = as.numeric(open_issues), last_push_year = as.integer(last_push_year), last_push_at) %>%
    arrange(biotools_id, omic_type)
  save_output(tool_domain_records, "tool_domain_records")
  save_output(df_for_plots, "df_for_plots")

  # Consistent domain order across plots (left-to-right).
  df_for_plots <- df_for_plots %>% mutate(omic_type = factor(omic_type, levels = domain_levels))
  domain_sizes <- df_for_plots %>% distinct(biotools_id, omic_type) %>% count(omic_type, name = "denominator")

  df_license <- df_for_plots %>%
    mutate(license_class = factor(classify_license(license), levels = names(license_palette))) %>%
    distinct(biotools_id, omic_type, license_class) %>%
    count(license_class, .drop = FALSE) %>%
    mutate(denominator = sum(n), pct = n / denominator) %>%
    arrange(desc(n))
  save_output(df_license, "license_counts")

  df_lang_prep <- df_for_plots %>%
    separate_rows(language, sep = ",|;|\\\\|\\n") %>%
    mutate(language = if_else(is.na(language) | language == "", "Unknown", trimws(language)),
      language_group = map_chr(language, map_language_group)) %>%
    distinct(biotools_id, omic_type, language_group) %>%
    count(language_group, name = "n") %>%
    arrange(desc(n))
  save_output(df_lang_prep, "language_groups")

  # Each record belongs to exactly one domain, so the domain memberships are
  # the record keys themselves.
  df_expanded_omics <- df_for_plots %>% select(biotools_id, name, omic_type)
  save_output(df_expanded_omics, "expanded_omics")

  # 7. Registration figures --------------------------------------------------------
  # Create figures showing the number of candidate tool-domain records added to bio.tools per year, both as counts and percentages, and a scatter plot comparing publication year to year added. The figures are saved with consistent naming and dimensions.

  added_per_year <- df_for_plots %>%
    filter(!is.na(added)) %>%
    count(added = as.integer(added), omic_type) %>%
    arrange(added)
  save_plot(build_added_year_plot(added_per_year, axis_labels, nrow(df_for_plots),
      "candidate tool-domain records"),
    "tools_added_per_year_by_omics", width = 10, height = 8, dpi = 300)

  added_per_year_pct <- added_per_year %>% group_by(added) %>% mutate(pct_within_year = n / sum(n)) %>% ungroup()
  save_plot(build_added_year_pct_plot(added_per_year_pct, axis_labels),
    "tools_added_per_year_by_omics_pct", width = 10, height = 8, dpi = 300)

  save_plot(build_pub_vs_added_plot(publication_vs_added_records(df_for_plots), current_year),
    "publication_vs_year_added_scatter", width = 10, height = 6, dpi = 300)

  # 8. Age-citation figures -----------------------------------------------------------
  # Create figures showing the relationship between the age of a tool-domain record (years since earliest linked publication) and its citation count, both as raw counts and normalized by age. The figures include LOESS trend lines fitted separately on either side of the citation-filter boundary, with 95% confidence intervals. Outliers are identified and reported.

  # The candidate filter keeps every record published from citation_filter_year
  # onward regardless of citations, but applies a citation threshold to older
  # records. This creates a genuine step in the data at the boundary, so trends
  # are fitted separately on each side of it with a fixed, moderate span, and the
  # boundary is drawn as a dotted vertical line.
  filter_boundary_age <- current_year - citation_filter_year + 0.5   # plots use age = current_year - publication_year
  trend_caption <- glue(
    "Dotted line: citation-filter boundary. The step in the points at {current_year - citation_filter_year}-{current_year - citation_filter_year + 1} years is created by the candidate filter, ",
    "not by citation behaviour: records published {citation_filter_year} onward have no citation threshold; older thresholds are {config$candidate_filter$middle_min_citations}, {config$candidate_filter$older_min_citations} and {config$candidate_filter$earliest_min_citations}. Lines: LOESS (span {config$trend$span}) with 95% CI, fitted separately either side of the boundary; ",
    "straight line where a side has < {config$trend$min_loess_n} records; lines end at the ",
    "{round(100 * as.numeric(config$trend$tail_quantile))}th percentile of age."
  )

  age_citations <- age_citation_analysis(df_for_plots, current_year, filter_boundary_age, config$trend)
  message(glue("Identified {nrow(age_citations$outliers)} outliers (|residual| > {round(age_citations$threshold, 2)})"))
  print(age_citations$outliers)
  save_age_citation_figures(age_citations, save_plot, axis_labels, legend_labels, trend_caption,
    boundary = filter_boundary_age, boundary_label = "Citation-filter boundary",
    records_label = "candidate tool-domain records")

  # 9. Tool types ------------------------------------------------------------------------
  # Create figures showing the distribution of tool types across omics domains, including prevalence and bar plots. 

  # "Ontology" describes a data resource, not software, so it is not shown.
  tools_type <- df_for_plots %>%
    clean_tool_type() %>%
    distinct(biotools_id, omic_type, tool_type, .keep_all = TRUE) %>%
    filter(!is.na(tool_type), tool_type != "Ontology") %>%
    count(omic_type, tool_type) %>%
    left_join(domain_sizes, by = "omic_type") %>%
    mutate(prevalence = n / denominator) %>%
    bind_cols(wilson_ci(.$n, .$denominator)) %>%
    group_by(tool_type) %>%
    mutate(max_prevalence = max(prevalence)) %>%
    ungroup()
  save_output(tools_type, "tool_type_prevalence_by_omics")
  missing_tool_type <- function(x) is.na(x) | !nzchar(trimws(as.character(x)))
  tool_type_labels <- df_for_plots %>% group_by(omic_type) %>%
    summarise(eligible = n_distinct(biotools_id), missing = sum(missing_tool_type(tool_type)), .groups = "drop") %>%
    mutate(label = paste0(omic_type, " (n = ", scales::comma(eligible), "; no type = ", scales::comma(missing), ")")) %>%
    { setNames(.$label, .$omic_type) }
  save_plot(build_tool_dist_plot(axis_labels, tool_type_labels, tools_type),
    "tool_type_distribution_by_omics", width = 12, height = 8, dpi = 300)

  tool_type_bar_order <- tools_type %>% distinct(tool_type, max_prevalence) %>%
    arrange(max_prevalence, tool_type) %>% pull(tool_type)
  tools_type_bars <- tidyr::expand_grid(omic_type = domain_levels, tool_type = tool_type_bar_order) %>%
    left_join(tools_type %>% select(omic_type, tool_type, n), by = c("omic_type", "tool_type")) %>%
    left_join(domain_sizes, by = "omic_type") %>%
    mutate(n = replace_na(n, 0L), prevalence = n / denominator,
      tool_type = factor(tool_type, levels = tool_type_bar_order),
      omic_type = factor(omic_type, levels = domain_levels))
  save_plot(build_tool_dist_bars_plot(axis_labels, tool_type_labels, tools_type_bars),
    "tool_type_distribution_by_omics_bars", width = 12, height = 9, dpi = 300)

  # 10. Licence, language and operating system ---------------------------------------
  # Create figures showing the distribution of licence classes, programming languages, and operating systems across omics domains.

  p_license <- ggplot(df_license, aes(x = fct_reorder(license_class, pct), y = pct, fill = license_class)) +
    geom_col(show.legend = FALSE) +
    geom_text(aes(label = glue("{scales::percent(pct, accuracy = 0.1)} ({n}/{denominator})")), hjust = -0.05, size = 3.2) +
    labs(title = "Licence declared in bio.tools",
      subtitle = glue("n = {scales::comma(unique(df_license$denominator))} tool-domain records; 'Other specified' = less common named licences"),
      x = NULL, y = axis_labels$share) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.35))) +
    coord_flip(clip = "off") +
    theme_thesis(base_size = 11) +
    scale_fill_manual(values = license_palette)
  save_plot(p_license, "license_distribution", width = 7.5, height = 6, dpi = 300)

  # Top five languages and top three operating systems; the rest are "Other".
  lang_df_pie <- summarise_multivalue(df_for_plots, language, 5)
  os_df_pie <- summarise_multivalue(df_for_plots, operating_system, 3)
  save_output(lang_df_pie, "language_multivalue_prevalence")
  save_output(os_df_pie, "operating_system_multivalue_prevalence")
  p_lang <- build_feature_prevalence_plot(axis_labels, lang_df_pie, unknown_facet_labels(lang_df_pie), "Programming language")
  p_os <- build_feature_prevalence_plot(axis_labels, os_df_pie, unknown_facet_labels(os_df_pie), "Operating system")
  save_plot(p_lang + p_os + patchwork::plot_layout(ncol = 2), "language_os_pies", width = 12, height = 6, dpi = 300)

  p_lang_faceted_bars <- make_stack_faceted_bars(lang_df_pie, "Programming language", domain_sizes)
  p_os_faceted_bars <- make_stack_faceted_bars(os_df_pie, "Operating system", domain_sizes)
  save_plot(build_language_os_faceted_bars_plot(p_lang_faceted_bars, p_os_faceted_bars),
    "language_os_faceted_bars", width = 14, height = 8, dpi = 300)

  # Licence class by domain, in the same faceted-bar layout as language and OS.
  # "No licence declared" is treated as missing (shown in the panel heading).
  license_by_omic <- df_for_plots %>%
    mutate(label = classify_license(license),
      label = if_else(label == "No licence declared", "Unknown", label)) %>%
    distinct(biotools_id, omic_type, label) %>%
    mutate(omic_type = as.character(omic_type)) %>%
    count(omic_type, label, name = "n") %>%
    left_join(domain_sizes %>% mutate(omic_type = as.character(omic_type)), by = "omic_type") %>%
    mutate(prevalence = n / denominator)
  save_output(license_by_omic, "license_by_omic")
  p_license_faceted_bars <- make_stack_faceted_bars(license_by_omic, "Licence class", domain_sizes) +
    labs(x = "Records declaring this licence class (%)")
  save_plot(p_license_faceted_bars +
      patchwork::plot_annotation(caption = paste0(
        "Denominator: all records in each domain. Not reported = no licence declared in bio.tools. ",
        "Permissive: MIT, BSD, Apache, CC0, ISC; copyleft: GPL family; other specified: less common named licences."),
      theme = theme(plot.caption = element_text(hjust = 0, size = 9))),
    "license_faceted_bars", width = 8, height = 7, dpi = 300)

  save_plot(build_tech_stack_faceted_plot(p_lang_faceted_bars, p_license_faceted_bars, p_os_faceted_bars),
    "technical_stack_faceted", width = 14, height = 14, dpi = 300)

  # Heatmap: rows are licence classes, languages and operating systems; columns
  # are domains; cells are the share of each domain's records declaring the value.
  # Rows within each feature: most common first, then "Other" and "Not reported".
  tech_heat_df <- bind_rows(
    license_by_omic %>% mutate(feature = "Licence"),
    lang_df_pie %>% mutate(feature = "Programming language"),
    os_df_pie %>% mutate(feature = "Operating system")
  ) %>%
    mutate(omic_type = factor(as.character(omic_type), levels = domain_levels),
      label = if_else(label == "Unknown", "Not reported", label),
      feature = factor(feature, levels = c("Licence", "Programming language", "Operating system"))) %>%
    select(feature, label, omic_type, n, denominator, prevalence)
  tech_heat_order <- tech_heat_df %>%
    group_by(feature, label) %>% summarise(total = sum(n), .groups = "drop") %>%
    mutate(rank_key = case_when(label == "Not reported" ~ -2, label == "Other" ~ -1, TRUE ~ total)) %>%
    arrange(feature, rank_key) %>%
    mutate(row_id = paste(feature, label, sep = "___"))
  tech_heat_df <- tech_heat_df %>%
    mutate(row_id = factor(paste(feature, label, sep = "___"), levels = tech_heat_order$row_id))
  save_output(tech_heat_df %>% mutate(row_id = as.character(row_id)), "technical_stack_heatmap")
  # Each column shades from white to its own domain colour on one shared scale
  # (0 to the largest share). Percentages are printed because gold reads lighter
  # than blue at the same value.
  tech_heat_max <- max(tech_heat_df$prevalence, na.rm = TRUE)
  tech_heat_df <- tech_heat_df %>%
    group_by(omic_type) %>%
    mutate(cell_fill = scales::col_numeric(c("#FFFFFF", omic_palette[[as.character(first(omic_type))]]),
      domain = c(0, tech_heat_max))(prevalence)) %>%
    ungroup() %>%
    mutate(text_col = ink_on(cell_fill))
  domain_n <- tech_heat_df %>% distinct(omic_type, denominator) %>% arrange(omic_type)
  domain_col_labels <- setNames(paste0(domain_n$omic_type, "\n(n = ", scales::comma(domain_n$denominator), ")"),
    as.character(domain_n$omic_type))
  save_plot(build_tech_heat_plot(domain_col_labels, tech_heat_df), "technical_stack_heatmap", width = 9, height = 8, dpi = 300)

  save_plot(build_tech_stack_combined_plot(p_lang, p_license, p_os), "technical_stack_combined", width = 14, height = 12, dpi = 300)

  # 11. Exploratory composite score (GitHub-observable records only) -------------

  # Registry curation/update fields are deliberately excluded so this score
  # remains independent of curation outcomes. GitHub engagement excludes open
  # issues and is log1p-transformed before rescaling, as in every other
  # engagement figure, because the raw sum is extremely skewed.
  scored_tools_git <- df_for_plots %>%
    filter(citation_analysis_eligible, !is.na(publication_year),
      !is.na(github_repo), if_any(c(stars, forks, watchers), ~ !is.na(.x))) %>%
    mutate(
      age_adjusted_citation_score = safe_rescale(log1p(citations_per_year)),
      commit_recency_score = safe_rescale(last_push_year),
      github_engagement_score = safe_rescale(log1p(replace_na(stars, 0) + replace_na(forks, 0) + replace_na(watchers, 0))),
      composite_score = rowMeans(cbind(age_adjusted_citation_score, commit_recency_score, github_engagement_score), na.rm = FALSE)
    )
  top_by_score_git <- scored_tools_git %>%
    group_by(omic_type) %>%
    filter(is.finite(composite_score)) %>%
    slice_max(order_by = composite_score, n = 10, with_ties = FALSE) %>%
    ungroup() %>%
    mutate(name = as.character(name))
  save_output(top_by_score_git, "top_by_score_git")

  if (nrow(top_by_score_git) > 0L) {
    # Each bar is split into the three equally weighted components (each / 3),
    # so the figure shows why a tool ranks highly. Names are made unique per
    # domain so a tool in several domains is ordered correctly within each panel.
    component_labels <- c(age_adjusted_citation_score = "Citations per year",
      commit_recency_score = "Commit recency", github_engagement_score = "GitHub engagement")
    component_palette <- setNames(unname(thesis_secondary[c("crimson", "mint", "flame")]), unname(component_labels))
    comp_plot_df <- top_by_score_git %>%
      mutate(name_in_domain = fct_reorder(paste(name, omic_type, sep = "___"), composite_score, .na_rm = TRUE))
    comp_parts_df <- comp_plot_df %>%
      select(omic_type, name_in_domain, all_of(names(component_labels))) %>%
      pivot_longer(all_of(names(component_labels)), names_to = "component", values_to = "value") %>%
      mutate(contribution = value / 3,
        component = factor(unname(component_labels[component]), levels = rev(unname(component_labels))))
    p_tool_comp_git <- ggplot(comp_parts_df, aes(x = contribution, y = name_in_domain, fill = component)) +
      geom_col(width = 0.75) +
      geom_text(data = comp_plot_df, aes(x = composite_score, y = name_in_domain, label = sprintf("%.2f", composite_score)),
        inherit.aes = FALSE, hjust = -0.15, size = 2.8, colour = thesis_neutral[["ink"]]) +
      facet_wrap(~omic_type, scales = "free_y") +
      scale_y_discrete(labels = function(x) sub("___.*$", "", x)) +
      scale_x_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.25), expand = expansion(mult = c(0, 0.02))) +
      scale_fill_manual(values = component_palette, breaks = unname(component_labels), name = "Component (each one third)") +
      labs(title = "Top 10 tools by exploratory composite score",
        subtitle = "GitHub-observable records; bars split into the three equally weighted components; common 0-1 scale",
        x = axis_labels$composite_score, y = NULL) +
      theme_thesis(legend.position = "bottom")
    save_plot(p_tool_comp_git, "top_10_git_tools_composite", width = 10, height = 8, dpi = 300)
  } else {
    warning("Skipping top_10_git_tools_composite: the configured GitHub cache contains no usable stars, forks, or watchers metadata.",
      call. = FALSE)
  }

  # 12. EDAM Operation coverage and independent curation analysis ---------------
  # The EDAM curation analysis is independent of the candidate filter and uses the full population of bio.tools records with EDAM Operation annotations. It is run in a separate script (02_edam_curation_analysis.R) and the results are saved in the output folder. 
  # The analysis includes a summary of EDAM Operation coverage, a heatmap of EDAM Operation prevalence by omics domain, and a comparison of curation outcomes between the candidate filter and independent EDAM curation.

  edam_results <- run_edam_curation_analysis(config, config_file, save_output, save_plot)

  # 13. UpSet plot for omic overlap (https://upset.app/advanced/) ------------------

  # Drawn with ggplot2 + patchwork so the matrix dots use the domain colours.
  # Counts are unique bio.tools records.
  set_membership <- df_expanded_omics %>%
    distinct(biotools_id, omic_type) %>%
    mutate(omic_type = as.character(omic_type), member = TRUE) %>%
    pivot_wider(names_from = omic_type, values_from = member, values_fill = FALSE)
  for (set_name in setdiff(domain_levels, names(set_membership))) set_membership[[set_name]] <- FALSE
  set_membership$combination <- apply(as.matrix(set_membership[domain_levels]), 1,
    function(r) paste(domain_levels[r], collapse = " & "))
  upset_intersections <- set_membership %>%
    count(combination, name = "n") %>%
    arrange(desc(n)) %>%
    mutate(combination = factor(combination, levels = combination))
  upset_matrix <- tidyr::expand_grid(combination = upset_intersections$combination, set = domain_levels) %>%
    mutate(member = purrr::map2_lgl(as.character(combination), set, ~ .y %in% strsplit(.x, " & ", fixed = TRUE)[[1]]),
      set = factor(set, levels = rev(domain_levels)))
  upset_set_sizes <- tibble(set = factor(domain_levels, levels = rev(domain_levels)),
    n = vapply(domain_levels, function(x) sum(set_membership[[x]]), integer(1)))
  p_upset <- patchwork::plot_spacer() + build_upset_bars_plot(upset_intersections) +
    build_upset_sets_plot(upset_set_sizes) + build_upset_matrix_plot(upset_matrix) +
    patchwork::plot_layout(ncol = 2, widths = c(1, 3), heights = c(2, 1)) +
    patchwork::plot_annotation(title = "Overlap of bio.tools records between omics domains",
      subtitle = "Each column is one combination of domains; dots show which domains it includes")
  save_plot(p_upset, "upset_tools_per_omic", width = 9, height = 6, dpi = 300)
  write.csv(tibble::enframe(setNames(upset_set_sizes$n, domain_levels), name = "set", value = "size"),
    file = file.path(output_dir, paste0("upset_omics_counts_", run_tag, ".csv")), row.names = FALSE)
  save_output(upset_intersections %>% mutate(combination = as.character(combination)), "upset_intersections")

  # 14. Repository commit-recency status ---------------------------------------------

  # Source field: GitHub API pushed_at (most recent push to any branch).
  # Thresholds (calendar months before maintenance_ref_date) come from the config:
  #   Active   = last push within recently_active_months
  #   Stale    = more than that, up to intermediate_activity_months
  #   Inactive = more than intermediate_activity_months
  #   Unknown  = no usable GitHub repository or push date
  # This is the ONLY place status is assigned.
  active_months <- as.numeric(config$maintenance$recently_active_months)
  stale_months <- as.numeric(config$maintenance$intermediate_activity_months)
  df_for_maint_github <- tools_augmented_github %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    mutate(omic_type = factor(omic_type, levels = domain_levels))
  months_since_push <- lubridate::time_length(lubridate::interval(
    suppressWarnings(as.Date(df_for_maint_github$last_push_at)), maintenance_ref_date), "months")
  df_for_maint_github$maintenance <- case_when(
    is.na(months_since_push) ~ "Unknown",
    months_since_push <= active_months ~ "Active",   # includes pushes after ref_date (warned above)
    months_since_push <= stale_months ~ "Stale",
    TRUE ~ "Inactive")
  df_for_maint_github$maintenance_ref_date <- maintenance_ref_date
  save_output(df_for_maint_github, "df_for_maint_github_full", "rds")
  save_output(df_for_maint_github, "df_for_maint_github_full")

  allowed_statuses <- names(maintenance_palette)
  maintenance_order <- c("Active", "Stale", "Inactive")
  df_for_maint <- df_for_maint_github %>% mutate(maintenance = factor(maintenance, levels = allowed_statuses))
  status_counts <- df_for_maint %>%
    count(maintenance) %>%
    tidyr::complete(maintenance = factor(allowed_statuses, levels = allowed_statuses), fill = list(n = 0))

  # 15. Descriptive summaries and rank correlations -----------------------------
  # Status summaries use the same maintenance column as the figures.

  stats_base <- df_for_maint %>%
    mutate(total_citations = as.numeric(total_citations),
      citations_per_year = as.numeric(citations_per_year),
      engagement = log1p(stars + forks + watchers),
      cpy_log = log1p(citations_per_year),
      filter_band = if_else(publication_year >= citation_filter_year,
        glue("Published >= {citation_filter_year} (no citation threshold)"),
        glue("Published < {citation_filter_year} (citation threshold applied)")))
  stats_paths <- save_output(age_citation_spearman(stats_base), "stats_age_citations")

  # Citations per year by commit-recency status (GitHub-observable only).
  stats_obs <- stats_base %>%
    filter(maintenance %in% maintenance_order, is.finite(citations_per_year)) %>%
    mutate(maintenance = droplevels(maintenance))
  stats_cpy_by_status <- stats_obs %>%
    group_by(maintenance) %>%
    summarise(n = n(), median_cpy = median(citations_per_year),
      q1 = quantile(citations_per_year, 0.25), q3 = quantile(citations_per_year, 0.75),
      median_total_citations = median(total_citations, na.rm = TRUE),
      median_age = median(years_since_pub, na.rm = TRUE), .groups = "drop")
  stats_paths <- c(stats_paths, save_output(stats_cpy_by_status, "stats_cpy_by_status"))

  # Citations per year vs GitHub engagement, per domain and pooled.
  eng_row <- function(d) {
    d <- d %>% filter(is.finite(cpy_log), is.finite(engagement))
    spearman_row(d$cpy_log, d$engagement)
  }
  stats_cit_vs_engagement <- bind_rows(
    eng_row(stats_obs) %>% mutate(group = "All domains"),
    stats_obs %>% group_by(group = as.character(omic_type)) %>% group_modify(~ eng_row(.x)) %>% ungroup()
  ) %>% select(group, everything())
  stats_paths <- c(stats_paths, save_output(stats_cit_vs_engagement, "stats_cit_vs_engagement"))

  # 16. Commit-recency figures ------------------------------------------------------

  # Full candidate population; records without an observable GitHub repository
  # remain explicitly Unknown.
  maintenance_distribution <- df_for_maint %>%
    count(omic_type, maintenance, name = "n") %>%
    group_by(omic_type) %>%
    mutate(denominator = sum(n), proportion = n / denominator) %>% ungroup()
  save_output(maintenance_distribution, "maintenance_distribution_all_candidates")
  save_plot(build_maintenance_distribution_plot(axis_labels, legend_labels, maintenance_distribution, maintenance_ref_date),
    "maintenance_distribution_all_candidates", width = 10, height = 6, dpi = 300)

  # GitHub-observable records (Unknown excluded) with complete citations.
  df_maint_citations <- df_for_maint %>%
    mutate(citations_log = log1p(as.numeric(total_citations)),
      maintenance = factor(maintenance, levels = maintenance_order)) %>%
    filter(maintenance %in% maintenance_order, is.finite(citations_log))

  if (nrow(df_maint_citations) > 0) {
    df_age_maint <- df_maint_citations %>%
      mutate(age = current_year - as.integer(publication_year)) %>%
      filter(!is.na(age))
    if (nrow(df_age_maint) > 0) {
      status_trend <- function(d) build_banded_trend(d, "age", "citations_log", group_col = "maintenance",
        boundary = filter_boundary_age, span = config$trend$span,
        min_loess_n = config$trend$min_loess_n, tail_quantile = config$trend$tail_quantile)
      age_by_status_plot <- function(d, title, subtitle) {
        ggplot(d, aes(x = age, y = citations_log, color = maintenance)) +
          jittered_points("maintenance") +
          facet_wrap(~maintenance, ncol = 4) +
          banded_trend_layers(status_trend(d), boundary = filter_boundary_age) +
          labs(title = title, subtitle = subtitle, caption = trend_caption,
            x = axis_labels$age, y = axis_labels$citations_log, fill = legend_labels$maintenance) +
          scale_fill_manual(values = maintenance_palette_points, name = legend_labels$maintenance) +  # points: full strength
          landscape_plot_theme(legend.position = "none") +
          theme(strip.text = element_text(face = "bold", size = 11))
      }
      save_plot(age_by_status_plot(df_age_maint,
          "Years since publication vs total citations by commit-recency status", "GitHub-observable candidate records"),
        "maintenance_age_vs_citations_faceted", width = 14, height = 5, dpi = 300)

      # Companion plot with status-specific outliers (2.5 SD) hidden for display.
      df_age_maint_clean <- df_age_maint %>%
        group_by(maintenance) %>%
        group_modify(~ {
          .x$predicted_log <- predict_banded(.x$age, .x$citations_log, boundary = filter_boundary_age, span = config$trend$span)
          .x$residual <- .x$citations_log - .x$predicted_log
          resid_sd <- sd(.x$residual, na.rm = TRUE)
          .x$is_outlier <- if (!is.finite(resid_sd) || resid_sd <= 0) FALSE else abs(.x$residual) > (2.5 * resid_sd)
          .x
        }) %>%
        ungroup()
      save_plot(age_by_status_plot(df_age_maint_clean,
          "Years since publication vs total citations by commit-recency status, extreme points hidden",
          glue("{sum(df_age_maint_clean$is_outlier, na.rm = TRUE)} extreme records hidden for display (2.5 SD within each status)")) +
          coord_cartesian(ylim = range(df_age_maint_clean$citations_log[!df_age_maint_clean$is_outlier], na.rm = TRUE)),
        "maintenance_age_vs_citations_faceted_clean", width = 14, height = 5, dpi = 300)
    }

    save_plot(build_status_ridge_plot(df_maint_citations, "citations_log", "Total citations by commit-recency status",
        "GitHub-observable candidate records; curves show the distribution of citations in each group",
        axis_labels$citations_log, legend_labels),
      "maintenance_citations_ridge", width = 10, height = 6, dpi = 300)

    df_age_maint_ridge <- df_for_maint %>%
      transmute(biotools_id, omic_type, age = current_year - as.integer(publication_year),
        maintenance = factor(maintenance, levels = maintenance_order)) %>%
      filter(!is.na(age), age > 0, maintenance %in% maintenance_order)
    if (nrow(df_age_maint_ridge) > 0) {
      p_ridge_age <- build_status_ridge_plot(df_age_maint_ridge, "age", "Years since publication by commit-recency status",
        "GitHub-observable candidate records; curves show the distribution of age in each group",
        axis_labels$age, legend_labels)
      save_plot(p_ridge_age, "maintenance_age_ridge", width = 10, height = 6, dpi = 300)

      df_maint_age_adjusted <- df_for_maint %>%
        select(biotools_id, omic_type, maintenance, publication_year, total_citations) %>%
        derive_publication_metrics(analysis_date = analysis_date) %>%
        mutate(cpy_log = log1p(citations_per_year), maintenance = factor(maintenance, levels = maintenance_order)) %>%
        filter(is.finite(cpy_log), maintenance %in% maintenance_order)
      p_cpy_by_maintenance <- patchwork::plot_spacer()
      if (nrow(df_maint_age_adjusted) > 0) {
        p_cpy_by_maintenance <- ggplot(df_maint_age_adjusted, aes(x = maintenance, y = cpy_log, fill = maintenance)) +
          geom_violin(alpha = 0.85, trim = FALSE, color = thesis_neutral[["outline"]], linewidth = 0.3) +
          geom_jitter(width = 0.12, shape = 21, fill = "white", colour = grDevices::adjustcolor(thesis_neutral[["ink"]], alpha.f = 0.35),
            stroke = 0.25, alpha = 0.5, size = 1) +
          labs(title = "Citations per year by commit-recency status",
            subtitle = "GitHub-observable candidate records; violins show distributions, points individual records",
            x = NULL, y = axis_labels$citations_per_year_log, fill = legend_labels$maintenance) +
          scale_fill_manual(values = maintenance_palette, name = legend_labels$maintenance) +
          scale_x_discrete(labels = status_n_labels(df_maint_age_adjusted)) +
          landscape_plot_theme(legend.position = "none")
        save_plot(p_cpy_by_maintenance, "maintenance_citations_per_year", width = 10, height = 6, dpi = 300)
      }

      # Main dissertation figure: (A) age distribution and (B) citations per year by status.
      p_maintenance_combined <- patchwork::wrap_plots(
        p_ridge_age + labs(title = NULL, subtitle = NULL),
        p_cpy_by_maintenance + labs(title = NULL, subtitle = NULL),
        ncol = 1
      ) +
        patchwork::plot_annotation(
          title = "Commit-recency status, tool age and age-adjusted citations",
          subtitle = "GitHub-observable candidate records (Unknown excluded); curves and violins show the distribution in each group",
          tag_levels = list(c("A  Years since publication", "B  Citations per year")),
          theme = theme(plot.title = element_text(hjust = 0, size = 14, face = "bold"),
            plot.subtitle = element_text(hjust = 0, size = 11))
        ) &
        theme(plot.tag = element_text(size = 12, face = "bold"), plot.tag.position = "topleft")
      save_plot(p_maintenance_combined, "maintenance_impact_combined", width = 11, height = 10, dpi = 300)
    }
  }

  # Records by omics domain, tool type (five most common) and commit-recency status.
  tool_types_long <- df_for_maint_github %>%
    clean_tool_type() %>%
    distinct(biotools_id, omic_type, tool_type, .keep_all = TRUE)
  tool_type_totals <- tool_types_long %>%
    filter(!is.na(tool_type)) %>%
    count(tool_type, name = "total_by_tool") %>%
    arrange(desc(total_by_tool))
  tool_status_count <- tool_types_long %>%
    mutate(tool_type = coalesce(tool_type, "Unknown"),
      # Legend and stacking in status order (Active, Stale, Inactive, Unknown).
      maintenance = factor(maintenance, levels = allowed_statuses)) %>%
    count(omic_type, tool_type, maintenance, name = "n") %>%
    left_join(tool_type_totals, by = "tool_type") %>%
    mutate(total_by_tool = tidyr::replace_na(total_by_tool, 0)) %>%
    make_top_tool_status(tool_type_totals, top_n = 5L)
  tool_status_labels <- tool_status_count %>%
    group_by(omic_type, tool_type) %>%
    summarise(total_in_panel = sum(n), .groups = "drop")
  save_plot(build_tool_status_count_plot(axis_labels, legend_labels, tool_status_count, tool_status_labels),
    "tool_type_status", width = 10, height = 8, dpi = 300)

  # Same data as shares within each bar, so status differences between tool
  # types are visible even where counts are small.
  tool_status_pct <- tool_status_count %>%
    group_by(omic_type, tool_type) %>%
    mutate(bar_n = sum(n), share = n / bar_n) %>%
    ungroup()
  save_output(tool_status_pct, "tool_type_status_pct")
  save_plot(build_tool_status_pct_plot(axis_labels, legend_labels, tool_status_pct,
      tool_status_pct %>% distinct(omic_type, tool_type, bar_n)),
    "tool_type_status_pct", width = 11, height = 8, dpi = 300)

  # 17. Citation visibility versus GitHub engagement ----------------------------------
  # The main figure shows the log1p-transformed citations per year (age-adjusted) versus the log1p-transformed sum of GitHub stars, forks and watchers. 
  # The companion figure shows the same data with a loess trend line and 95% confidence interval.

  engagement_df <- df_for_maint %>%
    transmute(biotools_id, omic_type, name, maintenance, github_repo,
      publication_year = as.integer(publication_year), total_citations = as.numeric(total_citations),
      stars = as.numeric(stars), forks = as.numeric(forks), watchers = as.numeric(watchers)) %>%
    derive_publication_metrics(analysis_date = analysis_date) %>%
    mutate(
      citation_visibility_log = log1p(citations_per_year),
      github_metrics_observed = !is.na(github_repo) & if_any(c(stars, forks, watchers), ~ !is.na(.x)),
      github_engagement_log = if_else(github_metrics_observed,
        log1p(replace_na(stars, 0) + replace_na(forks, 0) + replace_na(watchers, 0)), NA_real_))
  engagement_axis_limits <- engagement_df %>%
    filter(is.finite(citation_visibility_log), is.finite(github_engagement_log)) %>%
    summarise(x_min = min(citation_visibility_log), x_max = max(citation_visibility_log),
      y_min = min(github_engagement_log), y_max = max(github_engagement_log))
  engagement_plots <- domain_levels[domain_levels %in% engagement_df$omic_type] %>%
    map(plot_citation_engagement, df = engagement_df, axis_limits = engagement_axis_limits,
      axis_labels = axis_labels, legend_labels = legend_labels) %>%
    purrr::discard(is.null)
  save_plot(build_engagement_combined_plot(engagement_plots), "citation_visibility_vs_github_engagement",
    width = 14, height = 10, dpi = 300)

  # 18. Figure-level audit and reproducibility manifest ---------------------------
  # The figure-level audit records the number of plotted records per omics domain for each figure, and the number of missing or unobserved records. 
  # The reproducibility manifest records the inputs used to generate the figures and tables, including the script path, helper paths, configuration file, population files, and cache file.

  # Records per domain where condition holds.
  count_by_domain <- function(df, condition) {
    df %>% mutate(.hit = {{ condition }}) %>% group_by(omic_type) %>%
      summarise(n = sum(.hit, na.rm = TRUE), .groups = "drop") %>%
      right_join(domain_sizes %>% select(omic_type), by = "omic_type") %>%
      mutate(n = as.integer(coalesce(n, 0L))) %>% { setNames(.$n, as.character(.$omic_type)) }
  }
  candidate_audit <- function(figure_name, plotted, missing = NULL) {
    domain_sizes %>% transmute(figure_name = figure_name, population = "Filtered adoption-candidate population",
      omic_type, eligible_tools = denominator,
      plotted_tools = if (is.null(plotted)) eligible_tools else unname(plotted[as.character(omic_type)]),
      missing_or_unobserved = if (is.null(missing)) eligible_tools - plotted_tools else unname(missing[as.character(omic_type)]))
  }
  is_blank <- function(x) is.na(x) | !nzchar(trimws(as.character(x)))
  figure_audit <- bind_rows(
    edam_results$figure_audit,
    candidate_audit("citation_visibility_vs_github_engagement",
      count_by_domain(engagement_df, is.finite(citation_visibility_log) & is.finite(github_engagement_log))),
    maintenance_distribution %>% group_by(omic_type) %>% summarise(
      figure_name = "maintenance_distribution_all_candidates",
      population = "Filtered adoption-candidate population",
      eligible_tools = unique(denominator), plotted_tools = unique(denominator),
      missing_or_unobserved = sum(n[as.character(maintenance) == "Unknown"]), .groups = "drop"),
    candidate_audit("tool_type_distribution_by_omics", NULL, count_by_domain(df_for_plots, is_blank(tool_type))),
    candidate_audit("technical_stack_combined", NULL,
      count_by_domain(df_for_plots, is_blank(language) | is_blank(operating_system) | is_blank(license))),
    candidate_audit("age_vs_citations_combined", count_by_domain(age_citations$data, TRUE))
  ) %>%
    mutate(audit_date = as.character(analysis_date)) %>%
    arrange(figure_name, omic_type)
  if (any(figure_audit$plotted_tools > figure_audit$eligible_tools, na.rm = TRUE)) {
    stop("Assertion failed: a figure audit reports more plotted than eligible tool-domain records.")
  }
  if (any(figure_audit$missing_or_unobserved < 0, na.rm = TRUE)) {
    stop("Assertion failed: a figure audit reports negative missingness.")
  }
  save_output(figure_audit, "figure_level_audit")

  # Record the same population file format preferred by the loading helpers.
  manifest_inputs <- unique(c(
    script_path, normalizePath(helper_paths, winslash = "/"), config_file,
    normalizePath(prefer_rds_population(unname(omic_files)), winslash = "/", mustWork = TRUE),
    normalizePath(prefer_rds_population(unname(population_files(filter_results_dir, domain_map, config$populations$full_suffix))),
      winslash = "/", mustWork = TRUE),
    resolve_config_path(config$inputs$mapped_operations, config_file, must_work = TRUE),
    resolve_config_path(config$edam$ontology_snapshot, config_file, must_work = TRUE),
    cache_file
  ))
  manifest_inputs <- manifest_inputs[!is.na(manifest_inputs) & file.exists(manifest_inputs)]

  reproducibility_manifest <- list(
    pipeline = "bio.tools landscape visualisation with EDAM Operation analysis",
    analysis_date = as.character(analysis_date),
    run_date = as.character(run_date),
    population_unit = "biotools_id + omic_type tool-domain record",
    citation_policy = list(source = expected_citation_source, coverage = "complete and conflict-free for citation statistics and scores",
      raw_total = "total_citations_reported", age_denominator = "Years since earliest available linked publication, inclusive; not software release age"),
    population_source_format = "RDS preferred; sanitized TSV fallback",
    populations = list(full_retrieved = nrow(edam_results$full_population),
      filtered_adoption_candidate = nrow(edam_results$candidate_population)),
    edam = list(valid_status = config$edam$valid_status, aggregation_depth = config$edam$aggregation_depth),
    github = list(
      engagement_components = unname(config$github$engagement_components),
      open_issues_included = isTRUE(config$github$include_open_issues_in_engagement),
      missing_treatment = config$github$missing_github_treatment,
      status_measure = "Repository commit-recency status",
      status_source_field = "GitHub API pushed_at (most recent push to any branch)",
      status_reference_date = as.character(maintenance_ref_date),
      active_months = active_months,
      stale_months = stale_months,
      retrieval_date_range = github_retrieval_range,
      rows_without_retrieval_date = sum(is.na(github_retrieval_dates)),
      pushes_after_reference_date = n_pushes_after_reference_date,
      cache_frozen = isTRUE(config$github$freeze_cache),
      status_counts = as.list(setNames(status_counts$n, as.character(status_counts$maintenance)))
    ),
    composite_score = list(
      role = "exploratory supplementary ranking only",
      components = c("rescale(log1p(citations per year))", "rescale(commit year)", "rescale(log1p(stars + forks + watchers))"),
      weighting = "unweighted mean of the three components",
      validated_measure_of_quality_or_adoption = FALSE
    ),
    loess = list(role = "descriptive visualisation only", candidate_exclusion = FALSE),
    inputs = lapply(manifest_inputs, function(path) list(
      path = path, md5 = unname(tools::md5sum(path)), bytes = unname(file.info(path)$size))),
    software = list(R = R.version.string, platform = R.version$platform,
      packages = as.list(vapply(c("dplyr", "readr", "ggplot2", "tidyr", "purrr", "yaml", "lubridate",
        "httr", "jsonlite", "glue", "scales", "ggrepel", "patchwork", "ggridges"),
        function(pkg) as.character(utils::packageVersion(pkg)), character(1)))),
    outputs = list(
      directory = normalizePath(output_dir, winslash = "/", mustWork = TRUE),
      figure_audit_rows = nrow(figure_audit),
      # Every file this run wrote (figures, tables, statistics), with checksums.
      files = lapply(sort(written_output_paths), function(path) list(
        file = basename(path), md5 = unname(tools::md5sum(path)), bytes = unname(file.info(path)$size))),
      statistics = basename(stats_paths)
    )
  )
  jsonlite::write_json(reproducibility_manifest,
    file.path(output_dir, paste0("reproducibility_manifest_", run_tag, ".json")),
    pretty = TRUE, auto_unbox = TRUE, na = "null")
}

main()
