# EDAM Operation coverage and independent bio.tools curation analysis.
# This module expects tidyverse, yaml, scales and ggplot2 to be loaded and the
# calling visualization script to have defined params, outdir and save_output().

resolve_config_path <- function(path, config_file) {
  if (is.null(path) || !nzchar(path)) stop("A required path is missing from visualize_config.yaml.")
  if (grepl("^(?:[A-Za-z]:[/\\\\]|/)", path)) return(normalizePath(path, winslash = "/", mustWork = FALSE))
  normalizePath(file.path(dirname(normalizePath(config_file, winslash = "/", mustWork = TRUE)), path),
                winslash = "/", mustWork = FALSE)
}

read_population_files <- function(results_dir, domains, suffix, population_name) {
  purrr::imap_dfr(domains, function(omic_type, stem) {
    path <- file.path(results_dir, paste0(stem, suffix))
    if (!file.exists(path)) stop("Population input not found: ", path)
    # RDS is lossless for embedded tabs/newlines. The TSV remains a portable
    # fallback, but cannot faithfully represent unescaped tabs in free text.
    rds_path <- sub("\\.tsv$", ".rds", path, ignore.case = TRUE)
    population <- if (file.exists(rds_path)) readRDS(rds_path) else
      readr::read_tsv(path, show_col_types = FALSE, progress = FALSE)
    required_population <- c("biotools_id", "canonical_record_id", "publication_year")
    missing_population <- setdiff(required_population, names(population))
    if (length(missing_population)) {
      stop("Population input lacks required columns: ", paste(missing_population, collapse = ", "))
    }
    population %>%
      # `.env` is required here: an input column named `omic_type` would
      # otherwise mask the function argument and can leak NA into the facets.
      mutate(omic_type = .env$omic_type, population = population_name)
  }) %>%
    filter(!is.na(biotools_id), nzchar(stringr::str_trim(biotools_id))) %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE)
}

wilson_interval <- function(successes, n, conf.level = 0.95) {
  z <- stats::qnorm(1 - (1 - conf.level) / 2)
  p <- successes / n
  denominator <- 1 + z^2 / n
  centre <- (p + z^2 / (2 * n)) / denominator
  half_width <- z * sqrt((p * (1 - p) / n) + z^2 / (4 * n^2)) / denominator
  tibble(conf_low = pmax(0, centre - half_width), conf_high = pmin(1, centre + half_width))
}

cohen_kappa <- function(x, y) {
  keep <- !is.na(x) & nzchar(x) & !is.na(y) & nzchar(y)
  x <- x[keep]
  y <- y[keep]
  if (length(x) == 0L) return(NA_real_)
  levels_all <- union(unique(x), unique(y))
  observed <- mean(x == y)
  expected <- sum(prop.table(table(factor(x, levels = levels_all))) *
                    prop.table(table(factor(y, levels = levels_all))))
  if (isTRUE(all.equal(expected, 1))) return(NA_real_)
  (observed - expected) / (1 - expected)
}

run_edam_curation_analysis <- function(params, config_file, outdir, omic_palette) {
  results_dir <- resolve_config_path(params$inputs$filter_results_dir, config_file)
  mapped_path <- resolve_config_path(params$inputs$mapped_operations, config_file)
  validation_path <- resolve_config_path(params$inputs$validation_sample, config_file)
  domains <- unlist(params$populations$domains, use.names = TRUE)
  valid_status <- params$edam$valid_status %||% "Valid EDAM operation"
  missing_label <- params$edam$missing_label %||% "No valid EDAM operation annotation"
  top_n <- as.integer(params$edam$top_groups %||% 12L)

  full_population <- read_population_files(
    results_dir, domains, params$populations$full_suffix, "Full retrieved population"
  )
  candidate_population <- read_population_files(
    results_dir, domains, params$populations$candidate_suffix, "Filtered adoption-candidate population"
  )
  expected_domains <- unname(domains)
  if (any(is.na(full_population$omic_type)) ||
      !all(full_population$omic_type %in% expected_domains)) {
    stop("Full population contains an invalid omics domain after source assignment.")
  }
  if (any(is.na(candidate_population$omic_type)) ||
      !all(candidate_population$omic_type %in% expected_domains)) {
    stop("Candidate population contains an invalid omics domain after source assignment.")
  }
  save_output(full_population, "full_retrieved_population")
  save_output(candidate_population, "filtered_adoption_candidate_population")

  if (!file.exists(mapped_path)) stop("Mapped EDAM Operation input not found: ", mapped_path)
  mapped_operations <- readr::read_tsv(mapped_path, show_col_types = FALSE, progress = FALSE)
  required_edam <- c("biotools_id", "omic_type", "operation_annotation_status",
                     "operation_group_uri", "operation_group_term")
  missing_edam <- setdiff(required_edam, names(mapped_operations))
  if (length(missing_edam)) stop("Mapped EDAM input lacks required columns: ", paste(missing_edam, collapse = ", "))

  candidate_keys <- candidate_population %>% distinct(biotools_id, omic_type)
  full_keys <- full_population %>% distinct(biotools_id, omic_type)
  if (anyDuplicated(full_keys)) stop("Assertion failed: duplicate biotools_id + omic_type keys in full population.")
  if (anyDuplicated(candidate_keys)) stop("Assertion failed: duplicate biotools_id + omic_type keys in candidate population.")
  orphan_candidates <- anti_join(candidate_keys, full_keys, by = c("biotools_id", "omic_type"))
  if (nrow(orphan_candidates)) stop("Assertion failed: candidate keys absent from full retrieved population: ", nrow(orphan_candidates))

  # EDAM Operation coverage: valid ontology annotations only, aggregated to
  # parent groups and deduplicated once per tool, domain and group.
  valid_edam_groups <- mapped_operations %>%
    filter(operation_annotation_status == valid_status,
           !is.na(operation_group_uri), nzchar(operation_group_uri),
           !is.na(operation_group_term), nzchar(operation_group_term)) %>%
    distinct(biotools_id, omic_type, operation_group_uri, operation_group_term)
  if (any(is.na(valid_edam_groups$operation_group_uri) | !nzchar(valid_edam_groups$operation_group_uri))) {
    stop("Assertion failed: valid EDAM group rows contain blank parent-group URIs.")
  }

  denominators <- candidate_keys %>% count(omic_type, name = "eligible_tools")
  edam_group_by_omics <- valid_edam_groups %>%
    inner_join(candidate_keys, by = c("biotools_id", "omic_type")) %>%
    count(omic_type, operation_group_uri, operation_group_term, name = "annotated_tools") %>%
    left_join(denominators, by = "omic_type") %>%
    mutate(
      prevalence = annotated_tools / eligible_tools,
      ci_z = stats::qnorm(0.975),
      ci_denominator = 1 + ci_z^2 / eligible_tools,
      ci_centre = (prevalence + ci_z^2 / (2 * eligible_tools)) / ci_denominator,
      ci_half_width = ci_z * sqrt((prevalence * (1 - prevalence) / eligible_tools) +
                                    ci_z^2 / (4 * eligible_tools^2)) / ci_denominator,
      conf_low = pmax(0, ci_centre - ci_half_width),
      conf_high = pmin(1, ci_centre + ci_half_width)
    ) %>%
    select(-ci_z, -ci_denominator, -ci_centre, -ci_half_width)

  overall_edam_group <- edam_group_by_omics %>%
    group_by(operation_group_uri, operation_group_term) %>%
    summarise(annotated_tools = sum(annotated_tools), .groups = "drop") %>%
    arrange(desc(annotated_tools), operation_group_term)
  top_edam_groups <- overall_edam_group %>% slice_head(n = top_n) %>% pull(operation_group_uri)

  edam_operation_group_representation_by_omic <- edam_group_by_omics %>%
    filter(operation_group_uri %in% top_edam_groups) %>%
    mutate(operation_group_term = forcats::fct_reorder(operation_group_term, prevalence, .fun = max))
  save_output(edam_group_by_omics, "edam_operation_group_prevalence_all")
  save_output(edam_operation_group_representation_by_omic,
              "edam_operation_group_representation_by_omic")

  annotated_denominators <- valid_edam_groups %>%
    inner_join(candidate_keys, by = c("biotools_id", "omic_type")) %>%
    distinct(biotools_id, omic_type) %>% count(omic_type, name = "tools_with_valid_edam")
  edam_domain_labels <- denominators %>%
    left_join(annotated_denominators, by = "omic_type") %>%
    mutate(tools_with_valid_edam = replace_na(tools_with_valid_edam, 0L),
           missing_edam = eligible_tools - tools_with_valid_edam,
           label = paste0(omic_type, " (eligible n=", eligible_tools,
                          "; no valid EDAM n=", missing_edam, ")")) %>%
    { setNames(.$label, .$omic_type) }

  p_edam_omics <- ggplot(edam_operation_group_representation_by_omic,
                         aes(x = prevalence, y = operation_group_term, colour = omic_type)) +
    geom_errorbar(aes(xmin = conf_low, xmax = conf_high), orientation = "y", width = 0.16, alpha = 0.65) +
    geom_point(size = 2.7, alpha = 0.9) +
    facet_wrap(~omic_type, ncol = 2, labeller = as_labeller(edam_domain_labels)) +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_colour_manual(values = omic_palette, guide = "none") +
    labs(
      title = "EDAM Operation group representation by omics domain",
      subtitle = "Valid EDAM Operation annotations; points show prevalence and bars show Wilson 95% CIs",
      x = "Eligible tool-domain records annotated to operation group", y = "EDAM Operation group"
    ) +
    theme_minimal(base_size = 11) +
    theme(panel.grid.minor = element_blank(), plot.background = element_rect(fill = "white", colour = NA))
  ggsave(file.path(outdir, paste0("edam_operation_group_representation_by_omic_",
                                  format(Sys.Date(), "%Y%m%d"), ".png")),
         p_edam_omics, width = 11, height = 8, dpi = 300)

  # Curation is evaluated in the full retrieved population. Adoption visibility
  # is based only on age-adjusted citations and is not constructed from curation
  # fields, registry update status or EDAM annotations.
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
  curation_records <- full_population %>%
    left_join(annotation_status_by_tool, by = c("biotools_id", "omic_type")) %>%
    mutate(
      across(c(has_valid, has_obsolete, has_unresolved, has_missing_uri), ~replace_na(.x, FALSE)),
      edam_curation_category = case_when(
        has_valid ~ "Valid EDAM operation annotation",
        has_obsolete ~ "Obsolete EDAM operation annotation",
        has_unresolved ~ "Unresolved EDAM operation annotation",
        has_missing_uri | flag_missing_function_metadata %in% TRUE |
          flag_function_without_operation %in% TRUE ~ "Missing EDAM operation annotation",
        TRUE ~ "Missing EDAM operation annotation"
      ),
      publication_year = suppressWarnings(as.integer(publication_year)),
      total_citations = suppressWarnings(as.numeric(total_citations)),
      years_since_publication = if_else(!is.na(publication_year),
        pmax(1, lubridate::year(as.Date(params$analysis_date)) - publication_year + 1L), NA_real_),
      citations_per_year = if_else(!is.na(total_citations) & !is.na(years_since_publication),
                                   total_citations / years_since_publication, NA_real_),
      citation_visibility = if_else(!is.na(citations_per_year), log1p(citations_per_year), NA_real_)
    ) %>%
    group_by(omic_type) %>%
    mutate(
      visibility_threshold = if_else(any(!is.na(citation_visibility)),
        as.numeric(stats::quantile(citation_visibility, 0.75, na.rm = TRUE)), NA_real_),
      adoption_visibility_group = case_when(
        is.na(citation_visibility) ~ "Citation visibility not observable",
        citation_visibility >= visibility_threshold ~ "Higher age-adjusted citation visibility",
        TRUE ~ "Other observable citation visibility"
      )
    ) %>% ungroup()
  save_output(curation_records, "independent_edam_curation_records")

  curation_summary <- curation_records %>%
    #count(omic_type, adoption_visibility_group, edam_curation_category, name = "n") %>%
    #group_by(omic_type, adoption_visibility_group) %>%
    filter(omic_type %in% c("Genomics", "Transcriptomics", "Proteomics", "Multiomics"))
    mutate(denominator = sum(n), proportion = n / denominator) %>% ungroup()
  save_output(curation_summary, "edam_curation_by_independent_adoption_visibility")
  
  curation_domain_labels <- curation_records %>% group_by(omic_type) %>% summarise(
    eligible = sum(n), missing_visibility = sum(n[adoption_visibility_group == "Citation visibility not observable"]),
    .groups = "drop") %>%
    mutate(label = paste0(omic_type, " (n=", eligible, "; citation missing n=", missing_visibility, ")")) %>%
    { setNames(.$label, .$omic_type) }

  # One prespecified threshold sensitivity analysis: compare the primary upper
  # quartile definition with a within-domain median definition.
  curation_sensitivity <- curation_records %>%
    group_by(omic_type) %>%
    mutate(median_visibility = if_else(any(!is.na(citation_visibility)),
      as.numeric(stats::median(citation_visibility, na.rm = TRUE)), NA_real_)) %>%
    ungroup() %>%
    transmute(
      biotools_id, omic_type, edam_curation_category,
      primary_upper_quartile = adoption_visibility_group,
      sensitivity_median = case_when(
        is.na(citation_visibility) ~ "Citation visibility not observable",
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

  p_curation <- ggplot(
  curation_summary,
  aes(x = adoption_visibility_group, y = proportion, fill = edam_curation_category)
) +
  geom_col(position = "fill") +
  facet_wrap(~omic_type, ncol = 2, labeller = as_labeller(curation_domain_labels)) +
  scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
  scale_fill_manual(values = c(
    "Valid EDAM operation annotation" = "#007C7E",
    "Obsolete EDAM operation annotation" = "#D55E00",
    "Unresolved EDAM operation annotation" = "#8C6A2B",
    "Missing EDAM operation annotation" = "#B8B8B8"
  )) +
  labs(
    title = "EDAM curation completeness by independent citation visibility",
    subtitle = "Full retrieved population; curation fields are excluded from the adoption-visibility definition",
    x = NULL, y = "Share of retrieved tool-domain records", fill = "EDAM curation"
  ) +
  theme_minimal(base_size = 10) +
  theme(axis.text.x = element_text(angle = 20, hjust = 1), panel.grid.minor = element_blank())
  ggsave(file.path(outdir, paste0("edam_curation_by_citation_visibility_",
                                  format(Sys.Date(), "%Y%m%d"), ".png")),
         p_curation, width = 12, height = 8, dpi = 300)

  # Accuracy is reported only after the blinded review is completed. Blank
  # reviewer/consensus fields are never interpreted as incorrect annotations.
  if (file.exists(validation_path)) {
    validation <- readr::read_tsv(validation_path, show_col_types = FALSE, progress = FALSE)
    required_validation <- c("reviewer_1_decision", "reviewer_2_decision", "consensus_decision")
    missing_validation <- setdiff(required_validation, names(validation))
    if (length(missing_validation)) stop("Validation sample lacks required columns: ",
                                         paste(missing_validation, collapse = ", "))
    complete <- validation %>%
      filter(!is.na(reviewer_1_decision), nzchar(reviewer_1_decision),
             !is.na(reviewer_2_decision), nzchar(reviewer_2_decision),
             !is.na(consensus_decision), nzchar(consensus_decision))
    validation_status <- tibble(
      sampled_annotations = nrow(validation), completed_annotations = nrow(complete),
      validation_complete = nrow(validation) > 0L && nrow(complete) == nrow(validation),
      cohen_kappa = cohen_kappa(complete$reviewer_1_decision, complete$reviewer_2_decision)
    )
    save_output(validation_status, "edam_validation_status")
    if (isTRUE(validation_status$validation_complete)) {
      accuracy_summary <- complete %>%
        mutate(strictly_correct = consensus_decision == "Correct",
               acceptable = consensus_decision %in% c("Correct", "Partially correct")) %>%
        group_by(omic_type) %>%
        summarise(n = n(), strictly_correct = sum(strictly_correct), acceptable = sum(acceptable),
                  proportion_strictly_correct = mean(strictly_correct),
                  proportion_acceptable = mean(acceptable), .groups = "drop") %>%
        mutate(
          z = stats::qnorm(0.975),
          strict_denominator = 1 + z^2 / n,
          strict_centre = (proportion_strictly_correct + z^2 / (2 * n)) / strict_denominator,
          strict_half_width = z * sqrt((proportion_strictly_correct * (1 - proportion_strictly_correct) / n) + z^2 / (4 * n^2)) / strict_denominator,
          strict_conf_low = pmax(0, strict_centre - strict_half_width),
          strict_conf_high = pmin(1, strict_centre + strict_half_width)
        ) %>%
        select(-z, -strict_denominator, -strict_centre, -strict_half_width)
      save_output(accuracy_summary, "edam_manual_validation_accuracy")
      save_output(complete %>% count(omic_type, consensus_decision, name = "n"),
                  "edam_manual_validation_consensus_distribution")
    } else {
      message("EDAM validation remains blinded/incomplete (", nrow(complete), "/", nrow(validation),
              "). Accuracy is intentionally not calculated.")
    }
  }

  edam_figure_audit <- bind_rows(
    denominators %>% transmute(
      figure_name = "edam_operation_group_representation_by_omic", population = "Filtered adoption-candidate population",
      omic_type, eligible_tools, plotted_tools = eligible_tools,
      missing_or_unobserved = eligible_tools - map_int(omic_type, function(domain) {
        valid_edam_groups %>%
          filter(omic_type == domain) %>%
          semi_join(candidate_keys %>% filter(omic_type == domain), by = c("biotools_id", "omic_type")) %>%
          summarise(n = n_distinct(biotools_id)) %>% pull(n)
      })
    ),
    curation_records %>% group_by(omic_type) %>% summarise(
      figure_name = "edam_curation_by_citation_visibility", population = "Full retrieved population",
      eligible_tools = n(), plotted_tools = n(),
      missing_or_unobserved = sum(adoption_visibility_group == "Citation visibility not observable"), .groups = "drop"
    )
  )
  save_output(edam_figure_audit, "edam_figure_audit")

  invisible(list(full_population = full_population, candidate_population = candidate_population,
                 edam_group_by_omics = edam_group_by_omics, p_edam_omics = p_edam_omics,
                 curation_summary = curation_summary, p_curation = p_curation,
                 figure_audit = edam_figure_audit))
}

