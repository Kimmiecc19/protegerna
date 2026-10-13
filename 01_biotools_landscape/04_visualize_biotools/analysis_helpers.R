# Shared configuration, publication policy, population loading, publication age
# and statistics. Sourced locally by the filter and both visualisation workflows
# after their packages are loaded.

if (!exists("%||%")) `%||%` <- function(value, fallback) if (is.null(value)) fallback else value

# 1. Configuration --------------------------------------------------------------

# Validate the complete analysis configuration once at startup.
validate_visualize_config <- function(config) {
  scalar_text <- function(value) is.character(value) && length(value) == 1L && !is.na(value) && nzchar(value)
  number <- function(value, minimum = 0, integer = FALSE) {
    is.numeric(value) && length(value) == 1L && is.finite(value) && value >= minimum &&
      (!integer || value == floor(value))
  }
  fail <- function(field) stop("Invalid or missing configuration setting: ", field, call. = FALSE)
  valid_date <- function(value) scalar_text(value) && grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", value) &&
    !is.na(tryCatch(as.Date(value), error = function(error) NA))
  if (!valid_date(config$analysis_date)) fail("analysis_date")
  if (!number(config$random_seed, 0, TRUE)) fail("random_seed")
  for (field in c("filter_results_dir", "mapped_operations", "github_cache")) {
    if (!scalar_text(config$inputs[[field]])) fail(paste0("inputs.", field))
  }
  for (field in c("full_suffix", "candidate_suffix")) {
    if (!scalar_text(config$populations[[field]])) fail(paste0("populations.", field))
  }
  domains <- unlist(config$populations$domains, use.names = TRUE)
  allowed_domains <- c("Genomics", "Transcriptomics", "Proteomics", "Multiomics")
  if (length(domains) != 4L || is.null(names(domains)) || anyDuplicated(names(domains)) ||
      !setequal(unname(domains), allowed_domains)) fail("populations.domains")
  registration_population <- config$populations$registration_population
  if (!scalar_text(registration_population) || !registration_population %in% c("all_records", "with_citations")) {
    fail("populations.registration_population")
  }
  config$candidate_filter <- validate_citation_thresholds(config$candidate_filter)
  if (!number(config$trend$span) || config$trend$span <= 0 || config$trend$span > 1) fail("trend.span")
  if (!number(config$trend$min_loess_n, 2, TRUE)) fail("trend.min_loess_n")
  if (!number(config$trend$tail_quantile) || config$trend$tail_quantile <= 0 ||
      config$trend$tail_quantile > 1) fail("trend.tail_quantile")
  if (!scalar_text(config$citations$source) || !config$citations$source %in% c("Dimensions", "bio.tools")) fail("citations.source")
  if (!number(config$edam$aggregation_depth, 0, TRUE)) fail("edam.aggregation_depth")
  if (!number(config$edam$top_groups, 1, TRUE)) fail("edam.top_groups")
  if (!scalar_text(config$edam$ontology_snapshot)) fail("edam.ontology_snapshot")
  if (!scalar_text(config$edam$valid_status)) fail("edam.valid_status")
  if (!number(config$maintenance$recently_active_months, 0) ||
      !number(config$maintenance$intermediate_activity_months, 0) ||
      config$maintenance$intermediate_activity_months <= config$maintenance$recently_active_months) fail("maintenance activity intervals")
  reference_date <- config$maintenance$reference_date
  if (is.null(reference_date) || identical(reference_date, "")) reference_date <- config$analysis_date
  if (!valid_date(reference_date)) fail("maintenance.reference_date")
  config$maintenance$reference_date <- reference_date
  for (field in c("refresh_by_default", "freeze_cache", "include_open_issues_in_engagement")) {
    value <- config$github[[field]]
    if (!is.logical(value) || length(value) != 1L || is.na(value)) fail(paste0("github.", field))
  }
  if (!scalar_text(config$github$token_environment_variable)) fail("github.token_environment_variable")
  components <- unlist(config$github$engagement_components)
  if (!length(components) || anyDuplicated(components) ||
      any(!components %in% c("stars", "forks", "watchers", "open_issues"))) fail("github.engagement_components")
  config
}

# Resolve a configured path: absolute paths are kept, relative paths are read
# relative to the directory containing the YAML file.
resolve_config_path <- function(path, config_file, must_work = FALSE) {
  if (is.null(path) || !nzchar(path)) stop("A required path is missing from visualize_config.yaml.")
  if (!grepl("^(?:[A-Za-z]:[/\\\\]|/)", path)) {
    path <- file.path(dirname(normalizePath(config_file, winslash = "/", mustWork = TRUE)), path)
  }
  normalizePath(path, winslash = "/", mustWork = must_work)
}

# 2. Publication policy ---------------------------------------------------------
# Raw totals are retained; incomplete totals are never substituted with zero.

coverage_statuses <- c("complete", "partial", "unavailable", "no_publications")

validate_publication_schema <- function(records, expected_source = "Dimensions") {
  required <- c("citation_coverage", "citation_source", "publication_conflict_groups",
    "distinct_publication_count", "publication_count", "total_citations")
  missing_columns <- setdiff(required, names(records))
  if (length(missing_columns)) stop("Regenerate outputs with the updated fetch/filter scripts; missing columns: ",
    paste(missing_columns, collapse = ", "))
  if (any(is.na(records$citation_source) | records$citation_source != expected_source))
    stop("Citation source must consistently be ", expected_source,
      "; do not mix retrieval snapshots/providers.")
  if (any(is.na(records$citation_coverage) | !records$citation_coverage %in% coverage_statuses)) stop("Invalid citation coverage.")
  invisible(records)
}

default_citation_thresholds <- function() {
  list(no_threshold_from_year = 2020, middle_from_year = 2015,
    older_from_year = 2010, middle_min_citations = 30,
    older_min_citations = 50, earliest_min_citations = 70)
}

validate_citation_thresholds <- function(thresholds) {
  for (field in names(default_citation_thresholds())) {
    value <- thresholds[[field]]
    if (!is.numeric(value) || length(value) != 1L || !is.finite(value) ||
        value < 0 || value != floor(value)) stop("Invalid citation threshold: ", field)
  }
  if (thresholds$older_from_year >= thresholds$middle_from_year ||
      thresholds$middle_from_year >= thresholds$no_threshold_from_year) {
    stop("Citation threshold year boundaries must increase.")
  }
  if (thresholds$middle_min_citations > thresholds$older_min_citations ||
      thresholds$older_min_citations > thresholds$earliest_min_citations) {
    stop("Citation minima must not decrease for older publications.")
  }
  thresholds
}

# Publication-year citation thresholds. Partial totals can establish a pass;
# only complete totals establish a fail.
citation_decision <- function(year, citations, coverage, conflicts,
    thresholds = default_citation_thresholds()) {
  threshold <- ifelse(year >= thresholds$no_threshold_from_year, 0,
    ifelse(year >= thresholds$middle_from_year, thresholds$middle_min_citations,
      ifelse(year >= thresholds$older_from_year, thresholds$older_min_citations,
        thresholds$earliest_min_citations)))
  result <- rep("Review", length(year))
  safe <- !is.na(year) & !is.na(conflicts) & conflicts == 0
  # Recent records have no citation threshold: missing counts do not exclude them.
  result[safe & !is.na(threshold) & threshold == 0] <- "Pass"
  observed <- safe & !is.na(citations) & coverage %in% c("complete", "partial")
  result[observed & !is.na(threshold) & citations >= threshold] <- "Pass"
  result[observed & coverage == "complete" & !is.na(threshold) & citations < threshold] <- "Fail"
  result
}

# Preserve reported totals; only complete, conflict-free totals enter analyses.
prepare_publication_analysis <- function(records, expected_source = "Dimensions") {
  validate_publication_schema(records, expected_source)
  if (!"total_citations_reported" %in% names(records)) records$total_citations_reported <- records$total_citations
  citation_counts <- suppressWarnings(as.numeric(as.character(records$total_citations_reported)))
  conflicts <- suppressWarnings(as.numeric(as.character(records$publication_conflict_groups)))
  records$citation_analysis_eligible <- records$citation_coverage == "complete" & !is.na(conflicts) & conflicts == 0 & !is.na(citation_counts)
  records$total_citations <- ifelse(records$citation_analysis_eligible, citation_counts, NA_real_)
  records
}

# One row per coverage status, including missing-data groups.
publication_coverage_summary <- function(records) {
  data.frame(citation_coverage = coverage_statuses,
    n_records = vapply(coverage_statuses,
      function(status) sum(records$citation_coverage == status, na.rm = TRUE),
      integer(1)))
}

# 3. Population loading ---------------------------------------------------------

# Prefer the lossless RDS snapshot when it is at least as new as the TSV.
prefer_rds_population <- function(paths) {
  rds_paths <- sub("\\.tsv$", ".rds", paths, ignore.case = TRUE)
  use_rds <- file.exists(rds_paths) & file.info(rds_paths)$mtime >= file.info(paths)$mtime
  ifelse(use_rds %in% TRUE, rds_paths, paths)
}

# `files` is named by omics domain; the name becomes omic_type.
read_omic_tables <- function(files, required_columns = "biotools_id") {
  populations <- lapply(names(files), function(domain) {
    path <- files[[domain]]
    if (!file.exists(path)) stop("Population input not found: ", path)
    selected_path <- prefer_rds_population(path)
    population <- if (grepl("\\.rds$", selected_path, ignore.case = TRUE)) readRDS(selected_path) else
      readr::read_tsv(selected_path, show_col_types = FALSE, progress = FALSE)
    missing_columns <- setdiff(required_columns, names(population))
    if (length(missing_columns)) stop("Population input lacks columns: ", paste(missing_columns, collapse = ", "))
    population$omic_type <- rep(domain, nrow(population))
    population
  })
  dplyr::bind_rows(populations)
}

# Population files named <stem><suffix>, keyed by the configured domain map.
population_files <- function(filter_results_dir, domains, suffix) {
  stats::setNames(file.path(filter_results_dir, paste0(names(domains), suffix)), unname(domains))
}

read_population_files <- function(filter_results_dir, domains, suffix, population_name) {
  files <- population_files(filter_results_dir, domains, suffix)
  population <- read_omic_tables(files, c("biotools_id", "canonical_record_id", "publication_year"))
  population$population <- population_name
  population |>
    dplyr::filter(!is.na(biotools_id), nzchar(trimws(biotools_id))) |>
    dplyr::distinct(biotools_id, omic_type, .keep_all = TRUE)
}

# 4. Publication age and citation rate ------------------------------------------

# Inclusive publication age (years since earliest linked publication, minimum 1).
derive_publication_metrics <- function(records, analysis_date, domain_levels = NULL) {
  publication_year <- if ("publication_year" %in% names(records))
    suppressWarnings(as.integer(as.character(records$publication_year))) else rep(NA_integer_, nrow(records))
  if ("publication_date" %in% names(records)) {
    dates <- as.character(records$publication_date)
    matches <- regexpr("\\b(?:19|20)[0-9]{2}\\b", dates, perl = TRUE)
    fallback_year <- rep(NA_integer_, length(dates))
    found <- !is.na(matches) & matches > 0
    fallback_year[found] <- as.integer(substr(dates[found], matches[found], matches[found] + 3L))
    publication_year[is.na(publication_year)] <- fallback_year[is.na(publication_year)]
  }
  current_year <- as.integer(format(as.Date(analysis_date), "%Y"))
  citations <- suppressWarnings(as.numeric(as.character(records$total_citations)))
  records$publication_year <- publication_year
  records$current_year <- rep(current_year, nrow(records))
  records$years_since_pub <- ifelse(is.na(publication_year), NA_real_, pmax(1, current_year - publication_year + 1L))
  records$total_citations <- citations
  records$citations_total <- citations
  records$citations_per_year <- citations / records$years_since_pub
  if (!is.null(domain_levels)) records$omic_type <- factor(records$omic_type, levels = domain_levels)
  records
}

# 5. Trend models and statistical intervals ---------------------------------------

fit_lm_band <- function(x, y, grid) {
  pred <- stats::predict(stats::lm(y ~ x), newdata = data.frame(x = grid), interval = "confidence")
  list(fit = as.numeric(pred[, "fit"]), lower = as.numeric(pred[, "lwr"]),
    upper = as.numeric(pred[, "upr"]), method = "lm")
}

fit_loess_band <- function(x, y, grid, span) {
  pred <- tryCatch({
    fit_model <- stats::loess(y ~ x, data = data.frame(x = x, y = y), span = span, degree = 1,
      control = stats::loess.control(surface = "direct"))
    stats::predict(fit_model, newdata = data.frame(x = grid), se = TRUE)
  }, error = function(e) NULL)
  if (is.null(pred$fit) || is.null(pred$se.fit)) return(NULL)
  list(fit = as.numeric(pred$fit), lower = as.numeric(pred$fit - 1.96 * pred$se.fit),
    upper = as.numeric(pred$fit + 1.96 * pred$se.fit), method = "loess")
}

predict_trend_values <- function(x, y, span = 0.75) {
  valid <- is.finite(x) & is.finite(y)
  x <- x[valid]
  y <- y[valid]
  if (!length(x)) return(numeric(0))
  fit <- if (length(x) < 10 || length(unique(x)) < 6) NULL else tryCatch(
    stats::loess(y ~ x, span = span, degree = 1, control = stats::loess.control(surface = "direct")),
    error = function(e) NULL)
  if (is.null(fit)) fit <- stats::lm(y ~ x)
  as.numeric(stats::predict(fit, newdata = data.frame(x = x)))
}

# Fits one trend per group and per side of the filter boundary.
# * Fewer than `min_loess_n` records on a side -> straight line (lm) instead
#   of LOESS, so a handful of points cannot bend the curve.
# * The line stops at the `tail_quantile` of x on the thresholded side, so it is
#   not extrapolated through the last few very old tools.
build_banded_trend <- function(df, x, y, group_col = NULL, boundary,
  span = 0.75, n_points = 100, min_loess_n = 50L, tail_quantile = 0.97) {
  df <- df %>% filter(is.finite(.data[[x]]), is.finite(.data[[y]]))
  df$.side <- if_else(df[[x]] <= boundary, "No citation threshold", "Citation threshold applied")
  df$.grp <- if (is.null(group_col)) "all" else as.character(df[[group_col]])
  pieces <- split(df, list(df$.grp, df$.side), drop = TRUE)
  purrr::map_dfr(pieces, function(d) {
    xs <- d[[x]]; ys <- d[[y]]
    upper <- if (d$.side[1] == "Citation threshold applied") stats::quantile(xs, tail_quantile, names = FALSE) else max(xs)
    grid <- seq(min(xs), upper, length.out = n_points)
    use_lm <- nrow(d) < min_loess_n || length(unique(xs)) < 6
    fit <- if (use_lm) fit_lm_band(xs, ys, grid) else (fit_loess_band(xs, ys, grid, span) %||% fit_lm_band(xs, ys, grid))
    out <- tibble::tibble(!!x := grid, trend = fit$fit, ymin = fit$lower, ymax = fit$upper,
      method = fit$method, trend_segment = d$.side[1], n = nrow(d))
    if (!is.null(group_col)) {
      out[[group_col]] <- if (is.factor(df[[group_col]])) factor(d$.grp[1], levels = levels(df[[group_col]])) else d$.grp[1]
    }
    out
  }) %>%
    mutate(trend_group = paste(if (is.null(group_col)) "all" else .data[[group_col]], trend_segment))
}

predict_banded <- function(x, y, boundary, span = 0.75) {
  out <- rep(NA_real_, length(x))
  for (side in list(which(x <= boundary), which(x > boundary))) {
    keep <- side[is.finite(x[side]) & is.finite(y[side])]
    if (length(keep)) out[keep] <- predict_trend_values(x[keep], y[keep], span = span)
  }
  out
}

spearman_row <- function(x, y) {
  ok <- is.finite(x) & is.finite(y)
  ct <- suppressWarnings(cor.test(x[ok], y[ok], method = "spearman", exact = FALSE))
  tibble(rho = unname(ct$estimate), p = ct$p.value, n = sum(ok))
}

# Spearman correlation of age and total citations: pooled, by domain and by
# citation-filter band (`filter_band` column).
age_citation_spearman <- function(stats_base) {
  bind_rows(
    stats_base %>% summarise(spearman_row(years_since_pub, total_citations)) %>% mutate(group = "All domains"),
    stats_base %>% group_by(group = as.character(omic_type)) %>%
      summarise(spearman_row(years_since_pub, total_citations), .groups = "drop"),
    stats_base %>% filter(!is.na(filter_band)) %>% group_by(group = as.character(filter_band)) %>%
      summarise(spearman_row(years_since_pub, total_citations), .groups = "drop")
  ) %>% select(group, rho, p, n)
}

wilson_ci <- function(x, n, conf_level = 0.95) {
  z <- stats::qnorm(1 - (1 - conf_level) / 2)
  p <- ifelse(n > 0, x / n, NA_real_)
  denom <- 1 + z^2 / n
  centre <- (p + z^2 / (2 * n)) / denom
  half <- z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2)) / denom
  data.frame(conf_low = pmax(0, centre - half), conf_high = pmin(1, centre + half))
}

# 6. Age-citation analysis shared by the candidate and full-population runs ------

# Banded trends, residuals and display-only outliers (|residual| > 2.5 SD).
age_citation_analysis <- function(records, current_year, boundary, trend_config, label_top_n = 30) {
  data <- records %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    filter(!is.na(publication_year), !is.na(total_citations)) %>%
    mutate(age = current_year - publication_year, citations_log = log1p(as.numeric(total_citations)))
  trend <- function(group_col = NULL) build_banded_trend(data, "age", "citations_log", group_col = group_col,
    boundary = boundary, span = trend_config$span,
    min_loess_n = trend_config$min_loess_n, tail_quantile = trend_config$tail_quantile)
  # Residuals are observed log-citations minus model-predicted log-citations.
  data$predicted_log <- predict_banded(data$age, data$citations_log, boundary = boundary, span = trend_config$span)
  trend_all <- trend()
  trend_by_omic <- trend("omic_type")
  data$residual <- data$citations_log - data$predicted_log
  threshold <- 2.5 * sd(data$residual, na.rm = TRUE)
  data$is_outlier <- abs(data$residual) > threshold
  outliers <- data %>%
    filter(is_outlier) %>%
    select(name, omic_type, total_citations, age, citations_log, predicted_log, residual)
  # A tool assigned to several omics domains appears once per domain (same age and
  # citations, so the points overlap). Label each tool once, at its record with the
  # largest absolute residual; all records stay plotted and in the outlier table.
  labelled <- outliers %>%
    arrange(desc(abs(residual))) %>%
    distinct(name, .keep_all = TRUE) %>%
    slice_head(n = label_top_n)
  list(data = data, trend_all = trend_all, trend_by_omic = trend_by_omic,
    outliers = outliers, labelled = labelled, threshold = threshold,
    display_limits = range(data$citations_log[!data$is_outlier], na.rm = TRUE))
}

# 7. Table and figure exports ----------------------------------------------------
# Each workflow supplies its output names and plot saver. The callback records
# files for the candidate workflow's manifest; the full population workflow
# uses the default no-op callback.
make_analysis_exporters <- function(output_dir, run_tag, plot_saver,
    record_output = function(path) invisible(path), companion_tables = character()) {
  output_path <- function(name, ext) file.path(output_dir, paste0(name, "_", run_tag, ".", ext))
  save_output <- function(df, name, ext = "csv") {
    path <- output_path(name, ext)
    if (ext == "csv") readr::write_csv(df, path) else saveRDS(df, path)
    record_output(path)
    if (ext == "csv" && name %in% companion_tables) {
      companion_path <- sub("[.]csv$", ".tsv", path)
      readr::write_tsv(df, companion_path)
      record_output(companion_path)
    }
    message(glue::glue("{name}: {nrow(df)} rows → {basename(path)}"))
    invisible(path)
  }
  save_plot <- function(plot, name, width = 8, height = 6, dpi = 300) {
    path <- output_path(name, "png")
    plot_saver(plot, path, width = width, height = height, dpi = dpi)
    record_output(path)
    message(glue::glue("{name} → {basename(path)}"))
    invisible(path)
  }
  list(save_output = save_output, save_plot = save_plot)
}
