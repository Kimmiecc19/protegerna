# EDAM Operation coverage and independent bio.tools curation analysis.
# Sourced by visualize_biotools.R, which loads the tidyverse and
# sources analysis_helpers.R and thesis_palette.R first.

run_edam_curation_analysis <- function(config, config_file, save_output, save_plot) {

  # 1. Resolve inputs and analysis settings ------------------------------------

  filter_results_dir <- resolve_config_path(config$inputs$filter_results_dir, config_file)
  mapped_path <- resolve_config_path(config$inputs$mapped_operations, config_file)
  domains <- unlist(config$populations$domains, use.names = TRUE)
  valid_status <- config$edam$valid_status
  top_n <- as.integer(config$edam$top_groups)

  # 2. Load and validate analysis populations ----------------------------------
  # The full retrieved population is the set of all bio.tools records with EDAM Operation annotations, and the filtered adoption-candidate population is the subset of those records that passed the candidate filter. 
  # Both populations are read from the filter_biotools.R results.

  full_population <- read_population_files(
    filter_results_dir, domains, config$populations$full_suffix, "Full retrieved population"
  )
  candidate_population <- read_population_files(
    filter_results_dir, domains, config$populations$candidate_suffix, "Filtered adoption-candidate population"
  )
  save_output(full_population, "full_retrieved_population")
  save_output(candidate_population, "filtered_adoption_candidate_population")

  # 3. Validate mapped annotations and candidate keys -------------------------

  if (!file.exists(mapped_path)) stop("Mapped EDAM Operation input not found: ", mapped_path)
  mapped_operations <- readr::read_tsv(mapped_path, show_col_types = FALSE, progress = FALSE)
  required_edam <- c("biotools_id", "omic_type", "operation_annotation_status",
    "operation_group_uri", "operation_group_term")
  missing_edam <- setdiff(required_edam, names(mapped_operations))
  if (length(missing_edam)) stop("Mapped EDAM input lacks required columns: ", paste(missing_edam, collapse = ", "))

  candidate_keys <- candidate_population %>% distinct(biotools_id, omic_type)
  full_keys <- full_population %>% distinct(biotools_id, omic_type)
  orphan_candidates <- anti_join(candidate_keys, full_keys, by = c("biotools_id", "omic_type"))
  if (nrow(orphan_candidates)) stop("Assertion failed: candidate keys absent from full retrieved population: ", nrow(orphan_candidates))

  # EDAM Operation coverage: valid ontology annotations only, aggregated to
  # parent groups and deduplicated once per tool, domain and group.

  # 4. Summarise valid operation groups and Wilson confidence intervals -------------------

  valid_edam_groups <- mapped_operations %>%
    filter(operation_annotation_status == valid_status,
    !is.na(operation_group_uri), nzchar(operation_group_uri),
    !is.na(operation_group_term), nzchar(operation_group_term)) %>%
    distinct(biotools_id, omic_type, operation_group_uri, operation_group_term)

  denominators <- candidate_keys %>% count(omic_type, name = "eligible_tools")
  edam_group_by_omics <- valid_edam_groups %>%
    inner_join(candidate_keys, by = c("biotools_id", "omic_type")) %>%
    count(omic_type, operation_group_uri, operation_group_term, name = "annotated_tools") %>%
    left_join(denominators, by = "omic_type") %>%
    mutate(prevalence = annotated_tools / eligible_tools) %>%
    bind_cols(wilson_ci(.$annotated_tools, .$eligible_tools))

  overall_edam_group <- edam_group_by_omics %>%
    group_by(operation_group_uri, operation_group_term) %>%
    summarise(annotated_tools = sum(annotated_tools), .groups = "drop") %>%
    arrange(desc(annotated_tools), operation_group_term)
  top_edam_groups <- overall_edam_group %>% slice_head(n = top_n) %>% pull(operation_group_uri)

  edam_operation_group_representation_by_omic <- edam_group_by_omics %>%
    filter(operation_group_uri %in% top_edam_groups) %>%
    mutate(operation_group_term = forcats::fct_reorder(operation_group_term, prevalence, .fun = max),
    # Same panel order as every other figure (not alphabetical).
    omic_type = factor(omic_type, levels = names(omic_palette)))
  save_output(edam_group_by_omics, "edam_operation_group_prevalence_all")
  save_output(edam_operation_group_representation_by_omic,
    "edam_operation_group_representation_by_omic")

  annotated_denominators <- valid_edam_groups %>%
    inner_join(candidate_keys, by = c("biotools_id", "omic_type")) %>%
    distinct(biotools_id, omic_type) %>% count(omic_type, name = "tools_with_valid_edam")
  edam_domain_counts <- denominators %>%
    left_join(annotated_denominators, by = "omic_type") %>%
    mutate(tools_with_valid_edam = replace_na(tools_with_valid_edam, 0L),
    missing_edam = eligible_tools - tools_with_valid_edam,
    label = paste0(omic_type, " (n = ", scales::comma(eligible_tools),
      "; no valid EDAM = ", scales::comma(missing_edam), ")"))
  edam_domain_labels <- setNames(edam_domain_counts$label, edam_domain_counts$omic_type)

  # 5. Plot operation-group coverage by omics domain ---------------------------

  p_edam_omics <- ggplot(edam_operation_group_representation_by_omic,
    aes(x = prevalence, y = operation_group_term, colour = omic_type)) +
    geom_errorbar(aes(xmin = conf_low, xmax = conf_high), orientation = "y", width = 0.3,
    colour = thesis_neutral[["guide"]], linewidth = 0.4) +
    geom_point(aes(fill = omic_type), shape = 21, colour = thesis_neutral[["outline"]], stroke = 0.3, size = 2.7) +
    facet_wrap(~omic_type, ncol = 2, labeller = as_labeller(edam_domain_labels)) +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    labs(
    title = "EDAM Operation groups by omics domain",
    subtitle = "Share of records with at least one valid annotation in each group, with Wilson 95% CIs",
    x = "Share of tool-domain records", y = NULL
  ) +
    theme_thesis(base_size = 11)
  save_plot(p_edam_omics, "edam_operation_group_representation_by_omic", width = 11, height = 8, dpi = 300)

  # Curation is evaluated in the full retrieved population. Adoption visibility
  # is based only on age-adjusted citations and is not constructed from curation
  # fields, registry update status or EDAM annotations.

  # 6. Classify curation and independent citation visibility -------------------

  annotation_status_by_tool <- mapped_operations %>%
    semi_join(full_keys, by = c("biotools_id", "omic_type")) %>%
    group_by(biotools_id, omic_type) %>%
    summarise(
    has_valid = any(operation_annotation_status == valid_status, na.rm = TRUE),
    has_obsolete = any(operation_annotation_status == "Obsolete EDAM operation", na.rm = TRUE),
    has_unresolved = any(operation_annotation_status == "Operation URI unresolved in pinned EDAM version", na.rm = TRUE),
    has_missing_uri = any(operation_annotation_status == "Operation URI missing", na.rm = TRUE),
    .groups = "drop"
  )
  curation_records <- prepare_publication_analysis(full_population, config$citations$source) %>%
    derive_publication_metrics(analysis_date = config$analysis_date) %>%
    left_join(annotation_status_by_tool, by = c("biotools_id", "omic_type")) %>%
    mutate(
    across(c(has_valid, has_obsolete, has_unresolved, has_missing_uri), ~replace_na(.x, FALSE)),
    edam_curation_category = case_when(
      has_valid ~ "Valid EDAM operation annotation",
      has_obsolete ~ "Obsolete EDAM operation annotation",
      has_unresolved ~ "Unresolved EDAM operation annotation",
      TRUE ~ "Missing EDAM operation annotation"  # missing URI or function metadata
    ),
    years_since_publication = years_since_pub,
    citation_visibility = if_else(!is.na(citations_per_year), log1p(citations_per_year), NA_real_)
  ) %>%
    group_by(omic_type) %>%
    mutate(
    visibility_threshold = if_else(any(!is.na(citation_visibility)),
      as.numeric(stats::quantile(citation_visibility, 0.75, na.rm = TRUE)), NA_real_),
    adoption_visibility_group = case_when(
      is.na(citation_visibility) ~ "Complete citation visibility unavailable",
      citation_visibility >= visibility_threshold ~ "Higher age-adjusted citation visibility",
      TRUE ~ "Other observable citation visibility"
    )
  ) %>% ungroup()
  save_output(curation_records, "independent_edam_curation_records")

  # 7. Summarise curation within visibility groups -----------------------------

  curation_summary <- curation_records %>%
    count(omic_type, adoption_visibility_group, edam_curation_category, name = "n") %>%
    group_by(omic_type, adoption_visibility_group) %>%
    mutate(denominator = sum(n), proportion = n / denominator) %>% ungroup()
  save_output(curation_summary, "edam_curation_by_independent_adoption_visibility")

  curation_domain_labels <- curation_summary %>% group_by(omic_type) %>% summarise(
    eligible = sum(n), missing_visibility = sum(n[adoption_visibility_group == "Complete citation visibility unavailable"]),
    .groups = "drop") %>%
    mutate(label = paste0(omic_type, " (n = ", scales::comma(eligible), "; no citation data = ",
      scales::comma(missing_visibility), ")")) %>%
    { setNames(.$label, .$omic_type) }

  # 8. Comparison of upper-quartile and median thresholds ----------------------------

  curation_sensitivity <- curation_records %>%
    group_by(omic_type) %>%
    mutate(median_visibility = if_else(any(!is.na(citation_visibility)),
      as.numeric(stats::median(citation_visibility, na.rm = TRUE)), NA_real_)) %>%
    ungroup() %>%
    transmute(
    biotools_id, omic_type, edam_curation_category,
    primary_upper_quartile = adoption_visibility_group,
    sensitivity_median = case_when(
      is.na(citation_visibility) ~ "Complete citation visibility unavailable",
      citation_visibility >= median_visibility ~ "Higher age-adjusted citation visibility",
      TRUE ~ "Other observable citation visibility"
    )
  ) %>%
    pivot_longer(c(primary_upper_quartile, sensitivity_median),
    names_to = "threshold_definition", values_to = "adoption_visibility_group") %>%
    count(threshold_definition, omic_type, adoption_visibility_group,
    edam_curation_category, name = "n") %>%
    group_by(threshold_definition, omic_type, adoption_visibility_group) %>%
    mutate(denominator = sum(n), proportion = n / denominator) %>% ungroup()
  save_output(curation_sensitivity, "edam_curation_adoption_threshold_sensitivity")

  # 9. Plot annotation gaps and uncertainty ------------------------------------

  visibility_levels <- c(
    "Higher age-adjusted citation visibility" = "Top 25%\ncitations/year",
    "Other observable citation visibility" = "Other\n(bottom 75%)",
    "Complete citation visibility unavailable" = "Incomplete/missing\ncitation data"
  )
  curation_reason_labels <- c(
    "Missing EDAM operation annotation" = "Missing",
    "Obsolete EDAM operation annotation" = "Obsolete term",
    "Unresolved EDAM operation annotation" = "Unresolved term"
  )
  curation_reason_palette <- c(
    "Missing" = thesis_neutral[["unknown"]],
    "Obsolete term" = thesis_secondary[["flame"]],
    "Unresolved term" = thesis_secondary[["crimson"]]
  )
  curation_plot_df <- curation_summary %>%
    filter(edam_curation_category != "Valid EDAM operation annotation") %>%
    mutate(
    omic_type = factor(omic_type, levels = names(omic_palette)),
    visibility = factor(unname(visibility_levels[adoption_visibility_group]), levels = unname(visibility_levels)),
    edam_curation_category = factor(unname(curation_reason_labels[edam_curation_category]),
      levels = names(curation_reason_palette))
  )
  curation_totals <- curation_summary %>%
    group_by(omic_type, adoption_visibility_group) %>%
    summarise(not_valid = sum(n[edam_curation_category != "Valid EDAM operation annotation"]),
    denominator = first(denominator), .groups = "drop") %>%
    mutate(share_not_valid = not_valid / denominator) %>%
    bind_cols(wilson_ci(.$not_valid, .$denominator)) %>%
    mutate(omic_type = factor(omic_type, levels = names(omic_palette)),
    visibility = factor(unname(visibility_levels[adoption_visibility_group]), levels = unname(visibility_levels)))
  save_output(curation_totals, "edam_curation_not_valid_share")

  p_curation <- ggplot(curation_plot_df, aes(x = visibility, y = proportion, fill = edam_curation_category)) +
    geom_col(width = 0.65) +
    geom_errorbar(data = curation_totals, aes(x = visibility, ymin = conf_low, ymax = conf_high),
    inherit.aes = FALSE, width = 0.18, colour = thesis_neutral[["ink"]], linewidth = 0.4) +
    geom_text(data = curation_totals,
    aes(x = visibility, y = conf_high, label = scales::percent(share_not_valid, accuracy = 0.1)),
    inherit.aes = FALSE, vjust = -0.6, size = 3, colour = thesis_neutral[["ink"]]) +
    facet_wrap(~omic_type, ncol = 2, labeller = as_labeller(curation_domain_labels)) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.15))) +
    scale_fill_manual(values = curation_reason_palette, name = "No valid EDAM Operation:") +
    labs(
    title = "Records without a valid EDAM Operation annotation",
    subtitle = "Full retrieved population, grouped by within-domain citations per year; error bars: Wilson 95% CI on the total",
    x = NULL, y = "Share of tool-domain records"
  ) +
    theme_thesis(base_size = 11, legend.position = "bottom")
  save_plot(p_curation, "edam_curation_by_citation_visibility", width = 11, height = 8, dpi = 300)

  # 1.0 Export figure denominators and return analysis results -----------------

  edam_figure_audit <- bind_rows(
    denominators %>% transmute(
      figure_name = "edam_operation_group_representation_by_omic", population = "Filtered adoption-candidate population",
      omic_type, eligible_tools, plotted_tools = eligible_tools,
      missing_or_unobserved = edam_domain_counts$missing_edam
    ),
    curation_records %>% group_by(omic_type) %>% summarise(
      figure_name = "edam_curation_by_citation_visibility", population = "Full retrieved population",
      eligible_tools = n(), plotted_tools = n(),
      missing_or_unobserved = sum(adoption_visibility_group == "Complete citation visibility unavailable"), .groups = "drop"
    )
  )
  save_output(edam_figure_audit, "edam_figure_audit")

  invisible(list(full_population = full_population, candidate_population = candidate_population,
    figure_audit = edam_figure_audit))
}
