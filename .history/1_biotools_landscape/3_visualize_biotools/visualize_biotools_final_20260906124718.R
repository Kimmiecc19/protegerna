# ============================================================
# bio.tools Omics Landscape
# ============================================================
# Author: Kimberly Coetzer
# Purpose: Visually investigate the omics tool landscape
# ============================================================

# ============================================================
# Package management: check/install and load required packages
# ============================================================

load_packages <- function(pkgs) {
  to_install <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(to_install)) {
    stop("Missing required R packages: ", paste(to_install, collapse = ", "),
         ". Install them in the project environment before running this analysis.")
  }
  invisible(lapply(pkgs, library, character.only = TRUE))
}

load_packages(c(
  "tidyverse", "conflicted", "httr", "jsonlite", "yaml",
  "glue", "scales", "ggrepel", "patchwork",
  "lubridate", "ggridges", "UpSetR"
))

# Resolve function conflicts

conflicts_prefer(dplyr::filter, .quiet = TRUE)
conflicts_prefer(dplyr::lag, .quiet = TRUE)

# ============================================================
# 2. Output directory setup
# ============================================================

outdir <- paste0("output_visualizations_", format(Sys.Date(), "%Y%m%d"))
if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)

# ============================================================
# Consolidated export helper
# ============================================================

today <- format(Sys.Date(), "%Y%m%d")
outdir <- paste0("output_visualizations_", today)
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
 
save_output <- function(df, name, ext = "csv") {
  path <- file.path(outdir, paste0(name, "_", today, ".", ext))
  
  if (ext == "csv") write_csv(df, path) else saveRDS(df, path)
  
  message(glue("{name}: {nrow(df)} rows → {basename(path)}"))
  invisible(path)
}

save_plot <- function(plot, name, width = 8, height = 6, dpi = 300) {
  path <- file.path(outdir, paste0(name, "_", today, ".png"))
  ggsave(path, plot = plot, width = width, height = height, dpi = dpi)
  message(glue("{name} → {basename(path)}"))
  invisible(path)
}

# ============================================================
# 2. Load configuration (YAML)
# ============================================================

config_candidates <- c(file.path("code", "visualize_config.yaml"), "visualize_config.yaml")
config_file <- config_candidates[file.exists(config_candidates)][1]
if (is.na(config_file)) stop("Configuration file not found. Run from 4_tool_analysis or its code directory.")

params <- yaml::read_yaml(config_file)
analysis_date <- as.Date(params$analysis_date)
if (is.na(analysis_date)) stop("analysis_date in visualize_config.yaml must use YYYY-MM-DD format.")

token_env <- params$github$token_environment_variable %||% "GITHUB_TOKEN"
token <- Sys.getenv(token_env, "")
if (nzchar(token)) {
  Sys.setenv(GITHUB_TOKEN = token)
  message("GitHub token loaded.")
} else {
  message("No GitHub token — using unauthenticated API.")
}

# ============================================================
# RDS file loading helpers
# ============================================================

read_omic_candidates <- function(files) {
  purrr::imap_dfr(files, function(path, omic) {
    if (!file.exists(path)) stop(glue("Candidate population file not found: {path}"))
    rds_path <- sub("\\.tsv$", ".rds", path, ignore.case = TRUE)
    population <- if (file.exists(rds_path)) readRDS(rds_path) else
      readr::read_tsv(path, show_col_types = FALSE, progress = FALSE)
    population %>%
      mutate(omic_type = omic)
  })
}

# Define expected omic RDS files
config_dir <- dirname(normalizePath(config_file, winslash = "/", mustWork = TRUE))
filter_results_dir <- normalizePath(file.path(config_dir, params$inputs$filter_results_dir), winslash = "/", mustWork = TRUE)
domain_map <- unlist(params$populations$domains, use.names = TRUE)
omic_files <- purrr::imap(domain_map, ~file.path(filter_results_dir, paste0(.y, params$populations$candidate_suffix))) %>%
  rlang::set_names(unname(domain_map))

# Load and combine all omics
tools_combined <- read_omic_candidates(omic_files)

# ============================================================
# 4. Data cleaning and metrics
# ============================================================

clean_tools_data <- function(df, current_year = lubridate::year(analysis_date)) {
  
  df %>%
    filter(!is.na(total_citations), !is.na(publication_year)) %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    mutate(
      publication_year = as.integer(publication_year),
      citations_per_year = total_citations / pmax(current_year - publication_year + 1, 1)
    )
}

tools_cleaned <- clean_tools_data(tools_combined)
save_output(tools_cleaned, "tools_cleaned_cache", "rds")

# ============================================================
# GitHub Metadata Integration
# ============================================================

# -----------------------------
# 1. Extract GitHub repo info
# -----------------------------

tools_with_github <- tools_cleaned %>%
    mutate(
        github_url = str_extract(
            paste(homepage, documentation, sep = " "),
            "https?://github\\.com/[^/\\s]+/[^/\\s]+"
        ),
        github_repo = str_remove(github_url, "https?://github\\.com/")
    )

# -----------------------------
# 2. GitHub API query functions
# -----------------------------

get_github_metadata_full <- function(repo, token = NULL) {
    url <- paste0("https://api.github.com/repos/", repo)
    hdr <- httr::add_headers(Accept = "application/vnd.github.v3+json")
    if (!is.null(token) && token != "") {
        hdr <- httr::add_headers(
            Authorization = paste("token", token),
            Accept = "application/vnd.github.v3+json"
        )
    }

    res <- httr::GET(url, hdr)
    sc <- httr::status_code(res)

    if (sc == 200) {
        content <- jsonlite::fromJSON(httr::content(res, as = "text", encoding = "UTF-8"))
        list(
            stars        = content$stargazers_count,
            forks        = content$forks_count,
            watchers     = content$subscribers_count,
            open_issues  = content$open_issues_count,
            last_commit  = content$pushed_at
        )
    } else {
        msg_snip <- substr(tryCatch(httr::content(res, as = "text", encoding = "UTF-8"), error = function(e) "[no body]"), 1, 400)
        message(sprintf("GitHub API error (%s): %s → %s", sc, repo, msg_snip))
        list(stars = NA, forks = NA, watchers = NA, open_issues = NA, last_commit = NA)
    }
}

safe_get_github_metadata_full <- purrr::possibly(function(repo) {
    Sys.sleep(1)
    token <- Sys.getenv("GITHUB_TOKEN", "")
    meta <- get_github_metadata_full(repo, token)
    message(glue("✓ {repo}: {meta$stars} stars, {meta$forks} forks, last commit {meta$last_commit}"))
    meta
}, otherwise = list(stars = NA, forks = NA, watchers = NA, open_issues = NA, last_commit = NA))

# -----------------------------
# 3. GitHub cache handling
# -----------------------------

cache_file <- normalizePath(file.path(config_dir, params$inputs$github_cache), winslash = "/", mustWork = FALSE)
cache_columns <- c("github_repo", "last_commit", "stars", "forks", "watchers", "open_issues")

cache_df <- if (file.exists(cache_file)) {
    raw_cache <- read_csv(cache_file, show_col_types = FALSE)
    missing_cache_columns <- setdiff(cache_columns, names(raw_cache))
    if (length(missing_cache_columns) > 0L) {
        stop("GitHub cache is missing required columns: ", paste(missing_cache_columns, collapse = ", "))
    }
    raw_cache %>%
        transmute(
            github_repo = as.character(github_repo),
            last_commit = as.character(last_commit),
            across(all_of(c("stars", "forks", "watchers", "open_issues")), as.numeric)
        ) %>%
        distinct(github_repo, .keep_all = TRUE)
} else {
    tibble(
        github_repo = character(),
        last_commit = character(),
        stars = numeric(),
        forks = numeric(),
        watchers = numeric(),
        open_issues = numeric()
    )
}

# A row is cached only when at least one GitHub metric was retrieved. Rows from
# earlier failed queries (repository name plus blank values) must be retried.
usable_cached_repos <- cache_df %>%
    filter(if_any(all_of(c("stars", "forks", "watchers", "open_issues")), ~ !is.na(.x))) %>%
    pull(github_repo)

refresh_all_repos <- isTRUE(params$github$refresh_by_default)
repos_to_query <- tools_with_github %>%
    filter(!is.na(github_repo), nzchar(trimws(github_repo))) %>%
    distinct(github_repo) %>%
    filter(refresh_all_repos | !github_repo %in% usable_cached_repos) %>%
    pull(github_repo)

message(glue("GitHub repositories to query: {length(repos_to_query)}"))
if (length(repos_to_query) > 0L && !nzchar(Sys.getenv("GITHUB_TOKEN", ""))) {
    warning(
        "No GITHUB_TOKEN is set. GitHub's unauthenticated API limit may prevent the cache from being completed.",
        call. = FALSE
    )
}

# -----------------------------
# 4. Batch GitHub querying with incremental cache writes
# -----------------------------

batch_size <- 100L
n_batches <- ceiling(length(repos_to_query) / batch_size)

for (i in seq_len(n_batches)) {
    message(glue("Batch {i} / {n_batches}"))
    first_index <- (i - 1L) * batch_size + 1L
    last_index <- min(i * batch_size, length(repos_to_query))
    batch_repos <- repos_to_query[first_index:last_index]
    batch_results <- map(batch_repos, safe_get_github_metadata_full)

    batch_df <- tibble(
        github_repo = batch_repos,
        last_commit = map_chr(batch_results, "last_commit", .default = NA_character_),
        stars       = map_dbl(batch_results, "stars", .default = NA_real_),
        forks       = map_dbl(batch_results, "forks", .default = NA_real_),
        watchers    = map_dbl(batch_results, "watchers", .default = NA_real_),
        open_issues = map_dbl(batch_results, "open_issues", .default = NA_real_)
    )

    # Replace prior failed/stale rows, retain the canonical six-column schema,
    # and write after every batch so interrupted runs can resume.
    cache_df <- cache_df %>%
        filter(!github_repo %in% batch_repos) %>%
        bind_rows(batch_df) %>%
        select(all_of(cache_columns)) %>%
        distinct(github_repo, .keep_all = TRUE)
    write_csv(cache_df, cache_file, na = "")

    if (i %% 5L == 0L && i < n_batches) {
        message("⏸ Pausing briefly to respect GitHub API limits...")
        Sys.sleep(30)
    }
}

# -----------------------------
# 5. Join GitHub metadata back to tools
# Check if all tools are in df, not just those with GitHub?
# -----------------------------

tools_augmented_github <- tools_with_github %>%
    left_join(cache_df, by = "github_repo") %>%
    mutate(
        last_commit = as.Date(last_commit),
        commit_year = year(last_commit),
        across(c(stars, forks, watchers, open_issues), as.numeric)
    )

save_output(tools_augmented_github, "tools_augmented_github_full", "rds")
save_output(tools_augmented_github, "tools_augmented_github_full")

#message(glue("✓ GitHub metadata integrated for {nrow(tools_augmented_github)} tools."))

# ============================================================
# Global defaults and options
# ============================================================

options(
    stringsAsFactors = FALSE,
    readr.show_col_types = FALSE,
    scipen = 999
)

# Seed for reproducibility

set.seed(as.integer(params$random_seed %||% 42L))

# ============================================================
# Unified theme and palette
# ============================================================

sun_defaults <- function() {
    # ---- Core color palette ----
    core_palette <- c(
        Maroon = "#61223B",
        DarkGreen = "#007C7E",
        Navy = "#1A2F57",
        Copper = "#D55E00",
        Gold = "#8C6A2B"
    )

    # ---- Custom color/fill wrappers ----
    scale_color_sun <- function(..., values = core_palette) {
        # Create a larger palette by interpolating the core palette so plots with
        # many factor levels won't fail due to too few provided colours.
        vals <- unname(values)
        # 5 can be adjusted as needed
        ncols <- max(10, length(vals))
        ggplot2::scale_color_manual(values = grDevices::colorRampPalette(vals)(ncols), ...)
    }
    scale_fill_sun <- function(..., values = core_palette) {
        # Create an interpolated palette with enough colours for many factor levels
        vals <- unname(values)
        ncols <- max(10, length(vals))
        ggplot2::scale_fill_manual(values = grDevices::colorRampPalette(vals)(ncols), ...)
    }

    list(
        palette = core_palette,
        color   = scale_color_sun,
        fill    = scale_fill_sun
    )
}

scales_sun <- sun_defaults()

# Manual palettes for plots

palette <- scales_sun$palette
license_palette <- c(
    Permissive            = palette[["DarkGreen"]] %||% "#007C7E",
    Copyleft              = palette[["Maroon"]] %||% "#61223B",
    `Other specified`     = palette[["Gold"]] %||% "#8C6A2B",
    `Not licensed`        = palette[["Copper"]] %||% "#D55E00",
    `No licence declared` = "#B8B8B8"
)

maintenance_palette <- c(
    Active   = palette[["DarkGreen"]] %||% "#007C7E",
    Stale    = palette[["Gold"]] %||% "#8C6A2B",
    Inactive = palette[["Maroon"]] %||% "#61223B",
    Unknown  = palette[["Navy"]] %||% "#1A2F57"
)

omic_palette <- c(
    Genomics = "#8C6A2B",
    Transcriptomics = "#61223B",
    Proteomics = "#007C7E",
    Multiomics = "#1A2F57"
)

axis_labels <- list(
    publication_year = "Publication year",
    year_added = "Year added to bio.tools",
    age = "Tool-domain record age (years since publication)",
    citations_log = "Citations (log1p)",
    citations_per_year_log = "Citations per year (log1p)",
    tool_count = "Tool-domain record count",
    tool_share = "Tool-domain record share within year",
    composite_score = "Composite score",
    github_engagement_log = "GitHub engagement (log1p)"
)

legend_labels <- list(
    omics = "Omics type",
    maintenance = "Repository commit-recency status",
    license = "Licence class",
    status = "Outlier status",
    publication_decade = "Publication decade",
    language = "Programming language",
    operating_system = "Operating system"
)

# Save palettes for later use in plotting functions

palette_list <- list(omic_type = omic_palette, license = license_palette, maintenance = maintenance_palette, core = palette)
path <- file.path(outdir, "palettes.rds")
saveRDS(palette_list, path)
message(glue("Wrote palettes → {basename(path)}"))

# ============================================================
# Helper functions
# ============================================================

# ---- License classifier ----

classify_license <- function(x) {
    x <- stringr::str_squish(tolower(as.character(x)))
    case_when(
        is.na(x) | x %in% c("", "none", "na", "n/a", "null", "unknown") ~ "No licence declared",
        x == "not licensed" ~ "Not licensed",
        str_detect(x, "mit|bsd|apache|cc0|isc") ~ "Permissive",
        str_detect(x, "gpl|lgpl|agpl") ~ "Copyleft",
        TRUE ~ "Other specified"
    )
}

# ---- Safe numeric conversion ----

to_numeric_safe <- function(x) {
    suppressWarnings(as.numeric(as.character(x)))
}

# ============================================================
# File paths and inputs
# ============================================================

# tools_augmented_github was created above from the current filtered
# adoption-candidate population and the reproducible GitHub cache.

#message(glue("Loaded {nrow(tools_augmented_github)} rows from {input_file}."))

# ============================================================
# Data Processing & Summaries
# ============================================================
# Input: tools_augmented_github
# Output: cleaned tables saved to outdir for downstream plotting
# ============================================================

# -----------------------------
# Minimal column normalization / selection
# -----------------------------

# Start from the loaded dataset and only keep the columns used later
df_for_plots <- tools_augmented_github %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    select(
        -any_of(c("github_repo", "publication_abstract", "publication_title", "homepage", "documentation")),
        everything()
    )
if (!all(c("biotools_id", "omic_type") %in% names(df_for_plots))) {
    stop("Assertion failed: biotools_id and omic_type are required for every visualization.")
}
if (any(is.na(df_for_plots$biotools_id) | !nzchar(trimws(df_for_plots$biotools_id)))) {
    stop("Assertion failed: candidate tool-domain population contains missing biotools_id values.")
}
if (anyDuplicated(df_for_plots[c("biotools_id", "omic_type")])) {
    stop("Assertion failed: duplicate biotools_id + omic_type keys remain after candidate loading.")
}

df_tools_unique <- df_for_plots %>%
    group_by(biotools_id, omic_type) %>%
    # For each tool, summarize the omic types (combine if multiple), and take the max or min of numeric/date fields as appropriate.
    # Handle cases where all values might be NA to avoid returning Inf or -Inf.
    summarise(
        name = dplyr::first(name),
        total_citations = if (all(is.na(total_citations))) NA_real_ else max(as.numeric(total_citations), na.rm = TRUE),
        publication_year = if (all(is.na(publication_year))) NA_integer_ else as.integer(min(publication_year, na.rm = TRUE)),
        stars = if (all(is.na(stars))) NA_real_ else max(as.numeric(stars), na.rm = TRUE),
        forks = if (all(is.na(forks))) NA_real_ else max(as.numeric(forks), na.rm = TRUE),
        watchers = if (all(is.na(watchers))) NA_real_ else max(as.numeric(watchers), na.rm = TRUE),
        open_issues = if (all(is.na(open_issues))) NA_real_ else max(as.numeric(open_issues), na.rm = TRUE),
        commit_year = if (all(is.na(commit_year))) NA_integer_ else as.integer(max(commit_year, na.rm = TRUE)),
        last_commit = if (all(is.na(last_commit))) as.Date(NA) else as.Date(max(last_commit, na.rm = TRUE)),
        .groups = "drop"
    ) %>%
    ungroup()

save_output(df_tools_unique, "df_tools_unique")

# -----------------------------
# Enrich df_for_plots with derived metrics
# -----------------------------

current_year <- lubridate::year(analysis_date)

df_for_plots <- df_for_plots %>%
    mutate(
        # publication_year extraction from either explicit column or publication_date string
        publication_year = coalesce(
            suppressWarnings(as.integer(publication_year)),
            as.integer(str_extract(as.character(publication_date), "\\b(19|20)\\d{2}\\b"))
        ),
        # publication_date = if_else(!is.na(publication_year), as.character(publication_year), as.character(publication_date)),
        current_year = current_year,
        years_since_pub = if_else(!is.na(publication_year), pmax(1, current_year - publication_year + 1L), NA_real_),
        total_citations = to_numeric_safe(total_citations),
        # publication_citations may have weird formatting; attempt to extract first numeric token
        citations_total = coalesce(
            suppressWarnings(as.numeric(readr::parse_number(
                purrr::map_chr(
                    str_split(as.character(publication_citations), ",|;|\\s+"),
                    ~ {
                        toks <- .x[.x != ""]
                        if (length(toks) >= 1) toks[1] else NA_character_
                    }
                )
            ))),
            total_citations
        ),
        citations_per_year = if_else(!is.na(citations_total) & !is.na(years_since_pub), citations_total / years_since_pub, NA_real_),
    )

# write cleaned working table
save_output(df_for_plots, "df_for_plots")


# Enforce consistent omic_type ordering across plots (left-to-right)
desired_omic_levels <- c("Genomics", "Transcriptomics", "Proteomics", "Multiomics")
df_for_plots <- df_for_plots %>%
    mutate(omic_type = factor(omic_type, levels = desired_omic_levels))

# Also set ordering on the per-tool summary table
df_tools_unique <- df_tools_unique %>%
    mutate(omic_type = factor(omic_type, levels = desired_omic_levels))

# -----------------------------
# 5. License classification and palette mapping
# -----------------------------
df_license <- df_for_plots %>%
    mutate(license_class = factor(
        classify_license(license),
        levels = names(license_palette)
    )) %>%
    distinct(biotools_id, omic_type, license_class) %>%
    count(license_class) %>%
    mutate(denominator = nrow(df_for_plots %>% distinct(biotools_id, omic_type)), pct = n / denominator) %>%
    arrange(desc(n))

save_output(df_license, "license_counts")

# -----------------------------
# 7. Precompute language grouping (for later plotting)
# -----------------------------
map_language_group <- function(lang) {
    if (is.na(lang) || trimws(lang) == "") {
        return("Unknown")
    }
    lang_l <- tolower(lang)
    if (str_detect(lang_l, "^r$|\\br\\b")) {
        return("R")
    }
    if (str_detect(lang_l, "python")) {
        return("Python")
    }
    if (str_detect(lang_l, "c\\+\\+|\\bc\\b")) {
        return("C/C++")
    }
    if (str_detect(lang_l, "^java$|\\bjava\\b") && !str_detect(lang_l, "javascript")) {
        return("Java")
    }
    if (str_detect(lang_l, "javascript|node")) {
        return("JavaScript")
    }
    if (str_detect(lang_l, "perl")) {
        return("Perl")
    }
    if (str_detect(lang_l, "ruby")) {
        return("Ruby")
    }
    if (str_detect(lang_l, "matlab|octave")) {
        return("MATLAB")
    }
    if (str_detect(lang_l, "rust|go|golang")) {
        return("Other compiled")
    }
    str_to_title(lang_l)
}

df_lang_prep <- df_for_plots %>%
    separate_rows(language, sep = ",|;|\\\\|\\n") %>%
    mutate(
        language = if_else(is.na(language) | language == "", "Unknown", trimws(language)),
        language_group = map_chr(language, map_language_group)
    ) %>%
    distinct(biotools_id, omic_type, language_group) %>%
    count(language_group, name = "n") %>%
    arrange(desc(n))

save_output(df_lang_prep, "language_groups")

# ============================================================
# Create expanded omics table (one row per tool x omic) now that df_for_plots exists
# ============================================================

df_expanded_omics <- df_for_plots %>%
    select(biotools_id, name, omic_type) %>%
    mutate(omic_type = as.character(omic_type)) %>%
    separate_rows(omic_type, sep = ";\\s*|,\\s*") %>%
    mutate(omic_type = if_else(trimws(omic_type) == "", NA_character_, trimws(omic_type))) %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    filter(!is.na(omic_type))

# Ensure omic_type ordering consistent in expanded omics

df_expanded_omics <- df_expanded_omics %>%
    mutate(omic_type = factor(omic_type, levels = desired_omic_levels))

save_output(df_expanded_omics, "expanded_omics")

# ============================================================
# Visualizations
# ============================================================

# -----------------------------
# Utility functions used by plots
# -----------------------------

safe_rescale <- function(x, to = c(0, 1)) {
    x_num <- suppressWarnings(as.numeric(x))
    if (all(is.na(x_num))) {
        return(rep(NA_real_, length(x_num)))
    }
    vals <- na.omit(x_num)
    if (length(unique(vals)) == 1L) {
        return(rep(mean(to), length(x_num)))
    }
    scales::rescale(x_num, to = to, na.rm = TRUE)
}

choose_loess_span <- function(x, y, folds = 10, span_grid = seq(0.2, 1, by = 0.05)) {
    valid <- is.finite(x) & is.finite(y)
    x <- x[valid]
    y <- y[valid]

    if (length(x) < 10 || length(unique(x)) < 6) {
        return(list(span = 1, method = "lm", mse = NA_real_))
    }

    k_folds <- min(folds, length(x))
    set.seed(1)
    
    fold_id <- sample(rep(seq_len(k_folds), length.out = length(x)))

    cv_mse <- vapply(span_grid, function(span) {
        # partition into folds, fit loess on train, predict on validation, compute MSE
        fold_mse <- numeric(k_folds)
        for (fold in seq_len(k_folds)) {
            train_idx <- fold_id != fold
            test_idx <- fold_id == fold
            fit <- tryCatch(
                stats::loess(
                    y ~ x,
                    data = data.frame(x = x[train_idx], y = y[train_idx]),
                    span = span,
                    degree = 1,
                    control = stats::loess.control(surface = "direct")
                ),
                error = function(e) NULL
            )
            if (is.null(fit) || !any(test_idx)) {
                fold_mse[fold] <- NA_real_
                next
            }
            pred <- tryCatch(
                predict(fit, newdata = data.frame(x = x[test_idx])),
                error = function(e) rep(NA_real_, sum(test_idx))
            )
            fold_mse[fold] <- mean((y[test_idx] - pred)^2, na.rm = TRUE)
        }
        mean(fold_mse, na.rm = TRUE)
    }, numeric(1))

    # handle case where all spans failed (all MSEs are NA)
    if (all(is.na(cv_mse))) {
        warning(
            "choose_loess_span: all candidate spans failed cross-validation after ",
            "removing non-finite x/y values; falling back to linear model with span = 1."
        )
        return(list(
            span   = 1,
            method = "lm",
            mse    = NA_real_
        ))
    }

    # choose best span only among non-NA MSEs
    best_idx <- which.min(cv_mse)
    optimal_span <- span_grid[best_idx]
    optimal_mse  <- cv_mse[best_idx]

    list(
        span   = optimal_span,
        method = "loess",
        mse    = optimal_mse
    )
}

build_trend_df <- function(df, x_col, y_col, group_col = NULL, span = 0.75, n_points = 200) {
    x_sym <- rlang::ensym(x_col)
    y_sym <- rlang::ensym(y_col)

    if (!is.null(group_col)) {
        return(df %>%
            dplyr::group_by(.data[[group_col]]) %>%
            dplyr::group_modify(~ build_trend_df(.x, !!x_sym, !!y_sym, group_col = NULL, span = span, n_points = n_points)) %>%
            dplyr::ungroup())
    }

    data <- df %>%
        dplyr::select(!!x_sym, !!y_sym) %>%
        dplyr::filter(is.finite(.data[[rlang::as_name(x_sym)]]), is.finite(.data[[rlang::as_name(y_sym)]]))

    if (nrow(data) == 0) {
        return(tibble::tibble())
    }

    x <- data[[rlang::as_name(x_sym)]]
    y <- data[[rlang::as_name(y_sym)]]
    grid <- seq(min(x), max(x), length.out = n_points)

    if (length(x) < 10 || length(unique(x)) < 6) {
        fit <- stats::lm(y ~ x)
        pred <- stats::predict(fit, newdata = data.frame(x = grid))
        method <- "lm"
    } else {
        fit <- tryCatch(
            stats::loess(
                y ~ x,
                data = data.frame(x = x, y = y),
                span = span,
                degree = 1,
                control = stats::loess.control(surface = "direct")
            ),
            error = function(e) NULL
        )
        if (is.null(fit)) {
            fit <- stats::lm(y ~ x)
            pred <- stats::predict(fit, newdata = data.frame(x = grid))
            method <- "lm"
        } else {
            pred <- stats::predict(fit, newdata = data.frame(x = grid))
            method <- "loess"
        }
    }

    tibble::tibble(
        !!rlang::as_name(x_sym) := grid,
        trend = as.numeric(pred),
        method = method
    )
}

# ---- Helper: Fit LM with confidence interval ----
fit_lm_band <- function(x, y, grid) {
    fit_model <- stats::lm(y ~ x)
    pred <- stats::predict(fit_model, newdata = data.frame(x = grid), interval = "confidence")
    list(
        fit = as.numeric(pred[, "fit"]),
        lower = as.numeric(pred[, "lwr"]),
        upper = as.numeric(pred[, "upr"]),
        method = "lm"
    )
}

# ---- Helper: Fit LOESS with SE bands ----
fit_loess_band <- function(x, y, grid, span) {
    fit_model <- tryCatch(
        stats::loess(y ~ x, data = data.frame(x = x, y = y), span = span, degree = 1,
                     control = stats::loess.control(surface = "direct")),
        error = function(e) NULL
    )
    
    if (is.null(fit_model)) return(NULL)
    
    pred <- tryCatch(
        stats::predict(fit_model, newdata = data.frame(x = grid), se = TRUE),
        error = function(e) NULL
    )
    
    if (is.null(pred) || is.null(pred$fit) || is.null(pred$se.fit)) return(NULL)
    
    list(
        fit = as.numeric(pred$fit),
        lower = as.numeric(pred$fit - 1.96 * pred$se.fit),
        upper = as.numeric(pred$fit + 1.96 * pred$se.fit),
        method = "loess"
    )
}

build_trend_band_df <- function(df, x_col, y_col, group_col = NULL, span = 0.75, n_points = 200) {
    x_sym <- rlang::ensym(x_col)
    y_sym <- rlang::ensym(y_col)

    # Handle grouped data recursively
    if (!is.null(group_col)) {
        return(df %>%
            dplyr::group_by(.data[[group_col]]) %>%
            dplyr::group_modify(~ build_trend_band_df(.x, !!x_sym, !!y_sym, group_col = NULL, span = span, n_points = n_points)) %>%
            dplyr::ungroup())
    }

    # Extract and validate data
    data <- df %>%
        dplyr::select(!!x_sym, !!y_sym) %>%
        dplyr::filter(is.finite(.data[[rlang::as_name(x_sym)]]), is.finite(.data[[rlang::as_name(y_sym)]]))

    if (nrow(data) == 0) return(tibble::tibble())

    x <- data[[rlang::as_name(x_sym)]]
    y <- data[[rlang::as_name(y_sym)]]
    grid <- seq(min(x), max(x), length.out = n_points)

    # Select and execute appropriate method
    result <- if (length(x) == 1L || length(unique(x)) == 1L) {
        # Constant prediction
        list(fit = rep(as.numeric(y[1]), length(grid)), 
             lower = rep(as.numeric(y[1]), length(grid)),
             upper = rep(as.numeric(y[1]), length(grid)), 
             method = "constant")
    } else if (length(x) < 10 || length(unique(x)) < 6) {
        # Too few points: use LM
        fit_lm_band(x, y, grid)
    } else {
        # Try LOESS first, fall back to LM
        loess_result <- fit_loess_band(x, y, grid, span)
        if (!is.null(loess_result)) loess_result else fit_lm_band(x, y, grid)
    }

    tibble::tibble(
        !!rlang::as_name(x_sym) := grid,
        trend = result$fit,
        ymin = result$lower,
        ymax = result$upper,
        method = result$method
    )
}

# Trend values are predicted by the fitted linear or LOESS model on x_grid.
predict_trend_values <- function(x, y, span = 0.75) {
    valid <- is.finite(x) & is.finite(y)
    x <- x[valid]
    y <- y[valid]

    if (length(x) == 0) {
        return(numeric(0))
    }

    if (length(x) < 10 || length(unique(x)) < 6) {
        fit <- stats::lm(y ~ x)
        return(as.numeric(stats::predict(fit, newdata = data.frame(x = x))))
    }

    fit <- tryCatch(
        stats::loess(
            y ~ x,
            span = span,
            degree = 1,
            control = stats::loess.control(surface = "direct")
        ),
        error = function(e) NULL
    )

    if (is.null(fit)) {
        fit <- stats::lm(y ~ x)
        return(as.numeric(stats::predict(fit, newdata = data.frame(x = x))))
    }

    as.numeric(stats::predict(fit, newdata = data.frame(x = x)))
}

landscape_plot_theme <- function(legend.position = "right", plot_fill = "white", panel_fill = "white") {
    theme_minimal(base_size = 12) +
        theme(
            legend.position = legend.position,
            plot.background = element_rect(fill = plot_fill, color = NA),
            panel.background = element_rect(fill = panel_fill, color = NA),
            panel.grid.major = element_line(color = "grey90", linewidth = 0.35),
            panel.grid.minor = element_blank()
        )
}

# ============================================================
# Tools added per year by omics type
# ============================================================

added_per_year <- df_for_plots %>%
    distinct(biotools_id, omic_type, added, .keep_all = TRUE) %>%
    filter(!is.na(added)) %>%
    count(added = as.integer(added), omic_type) %>%
    arrange(added)

p_added_year <- ggplot(added_per_year, aes(x = added, y = n, fill = omic_type)) +
    geom_col() +
    facet_wrap(~omic_type, scales = "fixed", ncol = 1) +
    labs(
        title = "Number of tool-domain records added to bio.tools per year by omics type",
        x = axis_labels$year_added, y = axis_labels$tool_count,
        fill = legend_labels$omics
    ) +
    scale_y_continuous(breaks = scales::pretty_breaks(8), expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(breaks = scales::pretty_breaks(10)) +
    scale_fill_manual(values = unname(omic_palette), name = legend_labels$omics) +
    theme(plot.background = element_rect(fill = "white"), panel.background = element_rect(fill = "white"))

save_plot(p_added_year, "tools_added_per_year_by_omics", width = 10, height = 8, dpi = 300)

# ============================================================
# Relative share of tool-domain records added per year by omics type
# ============================================================

added_per_year_pct <- added_per_year %>%
    group_by(added) %>%
    mutate(pct_within_year = n / sum(n)) %>%
    ungroup()

p_added_year_pct <- ggplot(added_per_year_pct, aes(x = added, y = pct_within_year, fill = omic_type)) +
    geom_col() +
    facet_wrap(~omic_type, scales = "fixed", ncol = 1) +
    labs(
        title = "Relative share of tool-domain records added per year by omics type",
        x = axis_labels$year_added, y = axis_labels$tool_share,
        fill = legend_labels$omics
    ) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(breaks = scales::pretty_breaks(10)) +
    scale_fill_manual(values = unname(omic_palette), name = legend_labels$omics) +
    theme(plot.background = element_rect(fill = "white"), panel.background = element_rect(fill = "white"))

save_plot(p_added_year_pct, "tools_added_per_year_by_omics_pct", width = 10, height = 8, dpi = 300)

# ============================================================
# Publication year vs. year added to bio.tools
# ============================================================

p_pub_vs_added <- df_for_plots %>%
    mutate(
        publication_year = suppressWarnings(as.integer(publication_year)),
        added = suppressWarnings(as.integer(added))
    ) %>%
    distinct(biotools_id, omic_type, publication_year, added, .keep_all = TRUE) %>%
    filter(!is.na(publication_year), !is.na(added)) %>%
    ggplot(aes(x = publication_year, y = added, color = omic_type)) +
    geom_jitter(alpha = 0.35, width = 0.25, height = 0.25, size = 1.5) +
    geom_smooth(
        aes(group = 1),
        method = "loess",
        se = TRUE,
        color = "white",
        fill = "grey40",
        alpha = 0.5,
        linetype = "dashed",
        linewidth = 0.9,
        formula = y ~ x
    ) +
    facet_wrap(~omic_type, scales = "free") +
    geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "grey20", linewidth = 0.8, alpha = 0.9) +
    labs(
        title = "Publication year vs. year added to bio.tools",
        subtitle = "Dashed line = same-year parity",
        x = "Publication year", y = "Year added"
    ) +
    theme(legend.position = "none", plot.background = element_rect(fill = "grey92"), panel.background = element_rect(fill = "grey92")) +
    scale_y_continuous(breaks = seq(ifelse(exists("current_year"), min(2015, current_year), 2015),
        ifelse(exists("current_year"), current_year, lubridate::year(Sys.Date())),
        by = 1
    )) +
    # scales_sun$color()
    scale_color_manual(values = unname(omic_palette))

save_plot(p_pub_vs_added, "publication_vs_year_added_scatter", width = 10, height = 6, dpi = 300)

# ============================================================
# Select LOESS span
# ============================================================

# Use a single robust span selection for the citation trend plots below.
loess_choice <- choose_loess_span(
    current_year - df_for_plots$publication_year,
    log1p(as.numeric(df_for_plots$total_citations))
)
optimal_span <- loess_choice$span
message(glue("Chosen trend fit: {loess_choice$method} (span = {round(optimal_span, 3)})"))

# ============================================================
# Tool-domain record age vs. citations with stable trend fits
# ============================================================

df_age_citations_full <- df_for_plots %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    filter(!is.na(publication_year), !is.na(total_citations)) %>%
    mutate(
        age = current_year - publication_year,
        citations_log = log1p(as.numeric(total_citations))
    )
# Residuals are observed log-citations minus model-predicted log-citations.
df_age_citations_full$predicted_log <- predict_trend_values(
    df_age_citations_full$age,
    df_age_citations_full$citations_log,
    span = optimal_span
)
df_age_citations_full$residual <- df_age_citations_full$citations_log - df_age_citations_full$predicted_log

residual_sd <- sd(df_age_citations_full$residual, na.rm = TRUE)
outlier_threshold <- 2.5 * residual_sd

df_outliers <- df_age_citations_full %>%
    mutate(is_outlier = abs(residual) > outlier_threshold) %>%
    filter(is_outlier) %>%
    select(name, omic_type, total_citations, age, citations_log, predicted_log, residual)

label_top_n <- 30
df_outliers_labeled <- df_outliers %>%
    arrange(desc(abs(residual))) %>%
    slice_head(n = min(label_top_n, nrow(df_outliers)))

message(glue("Identified {nrow(df_outliers)} outliers (|residual| > {round(outlier_threshold, 2)})"))
message(glue("Labeling top {nrow(df_outliers_labeled)} outliers by absolute residual in inspection plot."))
print(df_outliers)
 
p_age_citations <- df_age_citations_full %>%
    ggplot(aes(x = age, y = citations_log, color = omic_type)) +
    geom_jitter(alpha = 0.35, width = 0.2, size = 1.5) +
    geom_smooth(
        aes(group = 1),
        method = "loess",
        se = TRUE,
        color = "white",
        fill = "grey40",
        alpha = 0.5,
        linetype = "dashed",
        linewidth = 0.9,
        span = optimal_span,
        formula = y ~ x
    ) +
    labs(
        title = "Tool-domain record age vs. total citations",
        subtitle = glue("Citations transformed with log1p; stable trend fit ({loess_choice$method})"),
        x = axis_labels$age,
        y = axis_labels$citations_log,
        color = legend_labels$omics
    ) +
    scale_color_manual(values = unname(omic_palette), name = legend_labels$omics) +
    landscape_plot_theme(plot_fill = "grey92", panel_fill = "grey92")

save_plot(p_age_citations, "age_vs_citations_scatter", width = 8, height = 6, dpi = 300)

p_age_citations_faceted <- df_age_citations_full %>%
    ggplot(aes(x = age, y = citations_log, color = omic_type)) +
    geom_jitter(alpha = 0.35, width = 0.2, size = 1.5) +
    geom_line(
        data = build_trend_df(df_age_citations_full, age, citations_log, group_col = "omic_type", span = optimal_span),
        aes(x = age, y = trend, group = omic_type),
        inherit.aes = FALSE,
        color = "Black",
        linetype = "dashed",
        linewidth = 0.9
    ) +
    facet_wrap(~omic_type, nrow = 2) +
    labs(
        title = "Tool-domain record age vs. total citations (by omic type)",
        subtitle = glue("Citations transformed with log1p; stable trend fit ({loess_choice$method})"),
        x = axis_labels$age,
        y = axis_labels$citations_log,
        color = legend_labels$omics
    ) +
    scale_color_manual(values = unname(omic_palette), name = legend_labels$omics) +
    landscape_plot_theme(legend.position = "bottom", plot_fill = "grey92", panel_fill = "grey92")

save_plot(p_age_citations_faceted, "age_vs_citations_faceted", width = 12, height = 8, dpi = 300)

p_outlier_inspection <- df_age_citations_full %>%
    mutate(outlier_status = abs(residual) > outlier_threshold) %>%
    ggplot(aes(x = age, y = citations_log, color = outlier_status)) +
    geom_point(size = 2, alpha = 0.35) +
    geom_smooth(
        aes(group = 1),
        method = "loess",
        se = TRUE,
        color = "white",
        fill = "grey40",
        alpha = 0.5,
        linetype = "dashed",
        linewidth = 0.9,
        span = optimal_span,
        formula = y ~ x
    ) +
    geom_label_repel(
        data = df_outliers_labeled,
        aes(x = age, y = citations_log, label = name),
        inherit.aes = FALSE,
        size = 2.5,
        max.overlaps = Inf,
        show.legend = FALSE
    ) +
    scale_color_manual(
    values = c("FALSE" = "#61223B", "TRUE" = "#007C7E"),
    labels = c("FALSE" = "Normal", "TRUE" = "Outlier"),
    name = legend_labels$status
  ) +
    labs(
        title = "Outlier Detection: Stable Trend Residuals",
        subtitle = glue("Threshold: |residual| > {round(outlier_threshold, 2)} (2.5 SD)"),
        x = axis_labels$age,
        y = axis_labels$citations_log
    ) +
    landscape_plot_theme(plot_fill = "grey92", panel_fill = "grey92")
    

save_plot(p_outlier_inspection, "outlier_inspection", width = 10, height = 6, dpi = 300)

df_age_citations_clean <- df_age_citations_full %>%
    mutate(is_outlier = abs(residual) > outlier_threshold)
display_citation_limits <- range(df_age_citations_clean$citations_log[!df_age_citations_clean$is_outlier], na.rm = TRUE)


# Display-only sensitivity plot. These rows remain in every analytical
# population, count, model and principal figure.
p_age_citations_clean <- df_age_citations_clean %>%
    ggplot(aes(x = age, y = citations_log, color = omic_type)) +
    geom_jitter(alpha = 0.35, width = 0.2, size = 1.5) +
    geom_smooth(aes(group = 1), method = "loess", se = TRUE, color = "white", fill = "grey40", alpha = 0.5, linetype = "dashed", linewidth = 0.8, span = optimal_span, formula = y ~ x) +
    labs(
        title = "Display-only age/citation sensitivity view",
        subtitle = glue("{nrow(df_outliers)} visually extreme points hidden here only; candidates and analyses are unchanged"),
        x = "Age (years since publication)",
        y = "Total citations (log1p)"
    ) +
    landscape_plot_theme(plot_fill = "grey92", panel_fill = "grey92") +
    scale_color_manual(values = unname(omic_palette)) +
    coord_cartesian(ylim = display_citation_limits)

save_plot(p_age_citations_clean, "age_vs_citations_clean", width = 8, height = 6, dpi = 300)

p_scatter_vs_clean <- p_age_citations + p_age_citations_clean +
    plot_layout(ncol = 2, widths = c(1, 1)) +
    plot_annotation(
        title = "Display sensitivity of the age/citation relationship",
        subtitle = glue("Left: all tool-domain records; right: {nrow(df_outliers)} visually extreme records hidden only for scale comparison"),
        theme = theme(
            plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
            plot.subtitle = element_text(size = 11, hjust = 0.5),
            legend.position = "right",
            plot.background = element_rect(fill = "white"),
            panel.background = element_rect(fill = "white")
        )
    )

save_plot(p_scatter_vs_clean, "age_vs_citations_scatter_vs_clean", width = 16, height = 6, dpi = 300)

p_age_citations_faceted_clean <- df_age_citations_clean %>%
    ggplot(aes(x = age, y = citations_log, color = omic_type)) +
    geom_jitter(alpha = 0.35, width = 0.2, size = 1.5) +
    geom_ribbon(
        data = build_trend_band_df(df_age_citations_clean, age, citations_log, group_col = "omic_type", span = optimal_span),
        aes(x = age, ymin = ymin, ymax = ymax, group = omic_type),
        inherit.aes = FALSE,
        fill = "grey40",
        alpha = 0.5
    ) +
    geom_line(
        data = build_trend_df(df_age_citations_clean, age, citations_log, group_col = "omic_type", span = optimal_span),
        aes(x = age, y = trend, group = omic_type),
        inherit.aes = FALSE,
        color = "#FFFFFF",
        linetype = "dashed",
        linewidth = 0.9
    ) +
    facet_wrap(~omic_type, nrow = 2) +
    labs(
        title = "Display-only age/citation sensitivity view by omics domain",
        subtitle = glue("{nrow(df_outliers)} visually extreme points hidden here only; analytical populations are unchanged"),
        x = axis_labels$age,
        y = axis_labels$citations_log,
        color = legend_labels$omics
    ) +
    scale_color_manual(values = unname(omic_palette), name = legend_labels$omics) +
    landscape_plot_theme(legend.position = "bottom", plot_fill = "grey92", panel_fill = "grey92") +
    coord_cartesian(ylim = display_citation_limits)

save_plot(p_age_citations_faceted_clean, "age_vs_citations_faceted_clean", width = 12, height = 8, dpi = 300)

# Combined publication-ready figure retains every candidate tool-domain record. LOESS is a
# visual trend smoother only and is never used to determine eligibility.
p_age_citations_combined <- p_age_citations + p_age_citations_faceted +
    plot_layout(ncol = 2, widths = c(1, 1.5)) +
    plot_annotation(
        title = "Tool-domain record age versus citation visibility",
        subtitle = glue("All {nrow(df_age_citations_full)} observable candidate tool-domain records retained; LOESS is descriptive only"),
        theme = theme(
            plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
            plot.subtitle = element_text(size = 11, hjust = 0.5),
            plot.background = element_rect(fill = "grey92", color = NA),
            panel.background = element_rect(fill = "grey92", color = NA)
        )
    )

save_plot(p_age_citations_combined, "age_vs_citations_combined", width = 18, height = 7, dpi = 300)

# ============================================================
# Tool type distribution by omics
# ============================================================

tools_type <- df_for_plots %>%
    # normalize and deduplicate tool_type values so counts are consistent
    separate_rows(tool_type, sep = ",|;") %>%
    mutate(tool_type = if_else(is.na(tool_type) | trimws(tool_type) == "", NA_character_, trimws(tool_type))) %>%
    distinct(biotools_id, omic_type, tool_type, .keep_all = TRUE) %>%
    filter(!is.na(tool_type)) %>%
    count(omic_type, tool_type) %>%
    left_join(df_for_plots %>% distinct(biotools_id, omic_type) %>%
                count(omic_type, name = "denominator"), by = "omic_type") %>%
    mutate(prevalence = n / denominator) %>%
    group_by(tool_type) %>%
    mutate(max_prevalence = max(prevalence)) %>%
    ungroup()
tool_type_labels <- df_for_plots %>% group_by(omic_type) %>% summarise(
    eligible = n_distinct(biotools_id),
    missing = sum(is.na(tool_type) | !nzchar(trimws(as.character(tool_type)))), .groups = "drop") %>%
    mutate(label = paste0(omic_type, " (n=", eligible, "; missing n=", missing, ")")) %>%
    { setNames(.$label, .$omic_type) }

p_tool_dist <- ggplot(tools_type, aes(x = fct_reorder(tool_type, max_prevalence), y = prevalence, colour = omic_type)) +
    geom_point(size = 2.5) +
    facet_wrap(~omic_type, labeller = as_labeller(tool_type_labels)) +
    coord_flip() +
    labs(title = "Tool type prevalence by omics domain",
         subtitle = "Multi-valued metadata; percentages may sum to more than 100% within a domain",
         x = "Tool type", y = "Share of eligible tool-domain records", colour = legend_labels$omics) +
    theme_minimal(base_size = 11) +
    theme(
        axis.text.y = element_text(size = 8),
        strip.text = element_text(size = 10),
        plot.background = element_rect(fill = "white", color = NA),
        panel.background = element_rect(fill = "white", color = NA),
        panel.grid.minor = element_blank(),
        plot.margin = margin(t = 8, r = 8, b = 8, l = 40)
    ) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_colour_manual(values = unname(omic_palette), guide = "none")

save_plot(p_tool_dist, "tool_type_distribution_by_omics", width = 12, height = 8, dpi = 300)

# ============================================================
# Technical stack overview
# ============================================================

# ============================================================
# License distribution
# ============================================================
if (exists("df_license")) {
    license_total <- unique(df_license$denominator)
    licence_not_declared <- sum(df_license$n[df_license$license_class == "No licence declared"])
    p_license <- ggplot(df_license, aes(x = fct_reorder(license_class, pct), y = pct, fill = license_class)) +
        geom_col(show.legend = FALSE) +
        geom_text(aes(label = glue("{scales::percent(pct, accuracy = 0.1)} ({n}/{denominator})")),
                  hjust = -0.05, size = 3.2) +
        coord_flip() +
        labs(title = "Licence metadata distribution",
             subtitle = glue("Eligible n={license_total}; no licence declared n={licence_not_declared}\nOther specified = uncommon named licences"),
             x = NULL, y = "Share of eligible tool-domain records") +
        scale_y_continuous(labels = scales::percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.18))) +
        theme_minimal(base_size = 11) +
        scale_fill_manual(values = license_palette)
    save_plot(p_license, "license_distribution", width = 7.5, height = 6, dpi = 300)
}

# ============================================================
# Programming languages and operating systems
# ============================================================
# Create grouped top-N pies separately for language and operating system
# then arrange them side-by-side and save as one combined image

# Number to keep in top
top_n_lang <- 5
top_n_os <- 3

summarise_multivalue <- function(df, col, top_n, sep = ",\\s*|;", missing_label = "Unknown") {
    denominators <- df %>% distinct(biotools_id, omic_type) %>% count(omic_type, name = "denominator")
    expanded <- df %>%
        separate_rows({{ col }}, sep = sep) %>%
        mutate(value = if_else(is.na({{ col }}) | trimws(as.character({{ col }})) == "",
                               missing_label, trimws(as.character({{ col }})))) %>%
        distinct(biotools_id, omic_type, value)
    top_vals <- expanded %>% count(value, sort = TRUE) %>%
        filter(value != missing_label) %>% slice_head(n = top_n) %>% pull(value)
    expanded %>%
        mutate(label = if_else(value %in% c(top_vals, missing_label), value, "Other")) %>%
        distinct(biotools_id, omic_type, label) %>%
        count(omic_type, label, name = "n") %>%
        left_join(denominators, by = "omic_type") %>% mutate(prevalence = n / denominator)
}

lang_df_pie <- summarise_multivalue(df_for_plots, language, top_n_lang)
os_df_pie <- summarise_multivalue(df_for_plots, operating_system, top_n_os)
save_output(lang_df_pie, "language_multivalue_prevalence")
save_output(os_df_pie, "operating_system_multivalue_prevalence")
language_labels <- lang_df_pie %>% group_by(omic_type) %>% summarise(
    eligible = first(denominator), missing = sum(n[label == "Unknown"]), .groups = "drop") %>%
    mutate(label_text = paste0(omic_type, " (n=", eligible, "; missing n=", missing, ")")) %>%
    { setNames(.$label_text, .$omic_type) }
os_labels <- os_df_pie %>% group_by(omic_type) %>% summarise(
    eligible = first(denominator), missing = sum(n[label == "Unknown"]), .groups = "drop") %>%
    mutate(label_text = paste0(omic_type, " (n=", eligible, "; missing n=", missing, ")")) %>%
    { setNames(.$label_text, .$omic_type) }

# Build ggplots for each pie
p_lang <- ggplot(lang_df_pie, aes(x = prevalence, y = fct_reorder(label, prevalence), colour = omic_type)) +
    geom_point(size = 2.3) + facet_wrap(~omic_type, labeller = as_labeller(language_labels)) +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_colour_manual(values = omic_palette, guide = "none") +
    labs(title = "Programming-language prevalence", subtitle = "Multi-valued; percentages may sum to more than 100%",
         x = "Share of eligible tool-domain records", y = NULL) + theme_minimal(base_size = 10)

p_os <- ggplot(os_df_pie, aes(x = prevalence, y = fct_reorder(label, prevalence), colour = omic_type)) +
    geom_point(size = 2.3) + facet_wrap(~omic_type, labeller = as_labeller(os_labels)) +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_colour_manual(values = omic_palette, guide = "none") +
    labs(title = "Operating-system prevalence", subtitle = "Multi-valued; percentages may sum to more than 100%",
         x = "Share of eligible tool-domain records", y = NULL) + theme_minimal(base_size = 10)

# Combine side-by-side using patchwork and save
combined_pies <- p_lang + p_os + patchwork::plot_layout(ncol = 2)
save_plot(combined_pies, "language_os_pies", width = 12, height = 6, dpi = 300)

# ============================================================
# Combined technical stack overview
# ============================================================

p_tech_stack_combined <- p_license + p_lang + p_os + plot_spacer() +
    plot_layout(ncol = 2, nrow = 2) +
    plot_annotation(
        title = "Technical Stack Overview",
        subtitle = "Licence distribution, programming languages, and operating systems for candidate tool-domain records",
        theme = theme(
            plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
            plot.subtitle = element_text(size = 11, hjust = 0.5)
        )
    )

save_plot(p_tech_stack_combined, "technical_stack_combined", width = 14, height = 12, dpi = 300)

# ============================================================
# Composite scoring of tools and top 10 per omic type -GitHub tools only
# ============================================================
# Restricted to tools with observable GitHub repository metrics.

scored_tools_git <- tools_augmented_github %>%
    mutate(
      publication_year = suppressWarnings(as.integer(publication_year)),
      years_since_pub = if_else(!is.na(publication_year), pmax(1L, current_year - publication_year + 1L), NA_real_)
    ) %>%
    filter(!is.na(github_repo), if_any(c(stars, forks, watchers), ~ !is.na(.x))) %>%
    # Exploratory score. Registry curation/update fields are deliberately
    # excluded so this score remains independent of curation outcomes.
    mutate(
        citations_per_year = total_citations / pmax(years_since_pub, 1),
        age_adjusted_citation_score = safe_rescale(log1p(citations_per_year)),
        commit_recency_score = safe_rescale(commit_year),
        # GitHub engagement excludes open issues.
        github_engagement_score = safe_rescale(replace_na(stars, 0) + replace_na(forks, 0) + replace_na(watchers, 0)),
        composite_score = rowMeans(cbind(age_adjusted_citation_score, commit_recency_score, github_engagement_score), na.rm = FALSE)
    )

# Top 10 tools by composite score overall or by omic_type
top_by_score_git <- scored_tools_git %>%
    group_by(omic_type) %>% # optional: remove if I want top 10 overall
    slice_max(order_by = composite_score, n = 10, with_ties = FALSE) %>%
    ungroup() %>%
    mutate(name = as.character(name))

save_output(top_by_score_git, "top_by_score_git")

# Plot using omic_type when the cache contains usable GitHub metadata.
if (nrow(top_by_score_git) > 0L) {
    p_tool_comp_git <- ggplot(top_by_score_git, aes(
        x = fct_reorder(name, composite_score, .na_rm = TRUE),
        y = composite_score, fill = omic_type
    )) +
        geom_col(show.legend = FALSE) +
        coord_flip() +
        facet_wrap(~omic_type, scales = "free") +
        labs(
            title = "Top 10 tool-domain records by exploratory composite score (GitHub-observable subset)",
            subtitle = "Equal-weight descriptive index; not a validated ranking of tool quality or adoption",
            x = "Tool name", y = "Exploratory composite score"
        ) +
        scale_fill_manual(values = unname(omic_palette)) +
        theme(plot.background = element_rect(fill = "white"), panel.background = element_rect(fill = "white"))

    save_plot(p_tool_comp_git, "top_10_git_tools_composite", width = 10, height = 8, dpi = 300)
} else {
    p_tool_comp_git <- NULL
    warning(
        "Skipping top_10_git_tools_composite: the configured GitHub cache contains no usable stars, forks, or watchers metadata.",
        call. = FALSE
    )
}

# ============================================================
# EDAM Operation coverage and independent curation analysis
# ============================================================

edam_module <- file.path(dirname(normalizePath(config_file, winslash = "/", mustWork = TRUE)),
                         "edam_curation_analysis.R")
if (!file.exists(edam_module)) stop("EDAM analysis module not found: ", edam_module)
source(edam_module, local = TRUE)
edam_results <- run_edam_curation_analysis(params, config_file, outdir, omic_palette)
edam_group_by_omics <- edam_results$edam_group_by_omics
p_edam_omics <- edam_results$p_edam_omics

# ============================================================
# UpSet plot for omic overlap analysis (https://upset.app/advanced/)
# ============================================================

# Build boolean matrix (one row per tool, columns = omic sets)
tool_omic_matrix <- df_expanded_omics %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    mutate(value = 1) %>%
    pivot_wider(names_from = omic_type, values_from = value, values_fill = list(value = 0))

# Define sets to include in UpSet plot
required_sets <- c("Genomics", "Transcriptomics", "Proteomics", "Multiomics")

# Keep only name + required_sets (in canonical order)
tool_omic_matrix <- tool_omic_matrix %>%
    mutate(across(all_of(required_sets), as.logical)) %>%
    mutate(across(all_of(required_sets), as.numeric)) %>%
    select(name, all_of(required_sets))

# Draw UpSet plot using UpSetR with custom colors
png(file.path(outdir, paste0("upset_tools_per_omic_", format(Sys.Date(), "%Y%m%d"), ".png")),
    width = 8, height = 6, units = "in", res = 300
)

UpSetR::upset(
    as.data.frame(tool_omic_matrix),
    sets = required_sets,
    sets.bar.color = omic_palette[required_sets],
    order.by = "freq",
    mainbar.y.label = "Unique bio.tools records in overlap",
    sets.x.label = "Unique bio.tools records per omics domain",
    # main.bar.color = omic_palette[required_sets][1]
)

dev.off()

# Build a named list of sets from the boolean/0-1 matrix (assumes 'name' column)
list_of_sets <- lapply(required_sets, function(col) {
    tool_omic_matrix$name[as.logical(tool_omic_matrix[[col]])]
})
names(list_of_sets) <- required_sets

# Write counts per set for debugging and remove empty sets
set_counts <- vapply(list_of_sets, length, integer(1))
write.csv(tibble::enframe(set_counts, name = "set", value = "size"), file = file.path(outdir, paste0("upset_omics_counts_", format(Sys.Date(), "%Y%m%d"), ".csv")), row.names = FALSE)

# ============================================================
# Maintenance and activity analysis
# Calculate repository commit-recency status from the last commit date/year,
# with fallbacks for missing or inconsistent data.
# active = last commit within 18 months or commit year within last 2 years
# stale = last commit 18-36 months ago
# inactive = last commit >36 months ago or commit year >2 years ago

# ============================================================

# Classify maintenance based on last commit date string and/or commit year.
# Active   = last commit within 18 months or commit year within last 2 years
# Stale    = last commit 18–36 months ago
# Inactive = last commit >36 months ago, or commit year >2 years ago when only
#            a year is available
# Unknown  = insufficient information
classify_maintenance <- function(last_commit_char,
                                 commit_year = NA_integer_,
                                 ref_date = analysis_date) {
    # Coerce inputs to scalar safe values
    lc <- if (length(last_commit_char) == 0) NA_character_ else as.character(last_commit_char[1])
    cy <- if (length(commit_year) == 0) NA_integer_ else suppressWarnings(as.integer(commit_year[1]))

    # Normalize empty strings to NA
    if (!is.na(lc) && !nzchar(lc)) lc <- NA_character_

    classify_from_year <- function(year_val, ref_date) {
        if (is.na(year_val) || year_val <= 0L) return(NA_character_)
        recent_cutoff <- lubridate::year(ref_date) - 2L
        if (year_val >= recent_cutoff) "Active" else "Inactive"
    }

    # If last-commit string is missing, fall back to commit_year
    if (is.na(lc)) {
        from_year <- classify_from_year(cy, ref_date)
        return(ifelse(is.na(from_year), "Unknown", from_year))
    }

    # Try multiple parsers in order of specificity
    parsed <- suppressWarnings(lubridate::ymd_hms(lc))
    if (is.na(parsed)) parsed <- suppressWarnings(lubridate::ymd(lc))
    if (is.na(parsed)) parsed <- suppressWarnings(
        lubridate::parse_date_time(
            lc,
            orders = c("ymd", "Y-m-d", "Y/m/d", "Y")
        )
    )

    if (!is.na(parsed)) {
        days_since <- as.numeric(difftime(ref_date, parsed, units = "days"))

        if (!is.na(days_since)) {
            if (days_since <= 540) {        # 18 months
                return("Active")
            } else if (days_since <= 1095) { # 3 years
                return("Stale")
            } else {
                return("Inactive")
            }
        }
    }

    # Fallback to commit_year if parsing failed
    from_year <- classify_from_year(cy, ref_date)
    if (!is.na(from_year)) return(from_year)

    "Unknown"
}

df_for_maint_github <- tools_with_github %>%
    left_join(cache_df, by = "github_repo") %>%
    distinct(biotools_id, omic_type, .keep_all = TRUE) %>%
    # select(-github_repo, -publication_citations, -publication_abstract, -publication_date, publication_title, -homepage, -documentation, everything()) %>%
    mutate(
        last_commit = as.Date(last_commit),
        commit_year = year(last_commit),
        across(c(stars, forks, watchers, open_issues), as.numeric),
        publication_year = suppressWarnings(as.integer(publication_year)),
        years_since_pub = if_else(!is.na(publication_year), pmax(1L, current_year - publication_year + 1L), NA_real_)
    )

# Normalize omic_type ordering for maintenance/analysis tables
df_for_maint_github <- df_for_maint_github %>%
    mutate(omic_type = factor(omic_type, levels = desired_omic_levels))

save_output(df_for_maint_github, "df_for_maint_github_full", "rds")
save_output(df_for_maint_github, "df_for_maint_github_full")

df_for_maint_github <- df_for_maint_github %>%
    mutate(maintenance = purrr::pmap_chr(list(last_commit, commit_year), classify_maintenance)) %>%
    mutate(maintenance = if_else(is.na(maintenance) | trimws(as.character(maintenance)) == "", "Unknown", as.character(maintenance)))

allowed_statuses <- names(maintenance_palette)

normalize_maintenance <- function(x, allowed = allowed_statuses) {
    x_chr <- stringr::str_trim(as.character(x))
    x_lower <- tolower(x_chr)

    canonical <- dplyr::case_when(
        x_lower %in% "active"   ~ "Active",
        x_lower %in% "inactive" ~ "Inactive",
        x_lower %in% "stale"    ~ "Stale",
        x_lower %in% "dead"     ~ "Inactive", # normalize legacy output
        x_lower %in% c("unknown", "") ~ "Unknown",
        TRUE ~ "Unknown" # anything unexpected is mapped to Unknown
    )

    factor(canonical, levels = allowed)
}

df_for_maint <- df_for_maint_github %>%
    mutate(
        maintenance = normalize_maintenance(maintenance)
    )

status_counts <- df_for_maint %>%
    count(maintenance) %>%
    tidyr::complete(maintenance = factor(allowed_statuses, levels = allowed_statuses), fill = list(n = 0))
message("Repository commit-recency status counts (df_for_maint):")
print(status_counts)
message("Repository commit-recency palette values:")
print(maintenance_palette)

# Maintenance distribution uses the full candidate population. Tools without
# an identifiable/observable GitHub repository remain explicitly Unknown.
maintenance_distribution <- df_for_maint %>%
    distinct(biotools_id, omic_type, maintenance) %>%
    count(omic_type, maintenance, name = "n") %>%
    group_by(omic_type) %>%
    mutate(denominator = sum(n), proportion = n / denominator) %>% ungroup()
save_output(maintenance_distribution, "maintenance_distribution_all_candidates")
p_maintenance_distribution <- ggplot(maintenance_distribution,
                                      aes(x = omic_type, y = proportion, fill = maintenance)) +
    geom_col() +
    geom_text(aes(label = if_else(proportion >= 0.05,
                                  glue("{scales::percent(proportion, accuracy = 1)}\n({n}/{denominator})"), "")),
              position = position_stack(vjust = 0.5), size = 2.7, colour = "white") +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
    scale_fill_manual(values = maintenance_palette, drop = FALSE) +
    labs(title = "Repository commit-recency status across candidate tool-domain records",
         subtitle = "Commit-recency classification; absent or unusable GitHub metadata is retained as Unknown",
         x = NULL, y = "Share of candidate tool-domain records", fill = legend_labels$maintenance) +
    theme_minimal(base_size = 11)
save_plot(p_maintenance_distribution, "maintenance_distribution_all_candidates", width = 10, height = 6, dpi = 300)

# Citation visibility by repository commit-recency status.
maintenance_order <- c("Active", "Stale", "Inactive")

df_maint_citations <- df_for_maint %>%
    distinct(biotools_id, omic_type, maintenance, total_citations, .keep_all = TRUE) %>%
    mutate(
        total_citations = as.numeric(total_citations),
        citations_log = log1p(total_citations),
        maintenance = as.character(maintenance)
    ) %>%
    filter(
        maintenance %in% maintenance_order,
        is.finite(citations_log)
    ) %>%
    mutate(maintenance = factor(maintenance, levels = maintenance_order))

if (nrow(df_maint_citations) > 0) {
    df_age_maint <- df_for_maint %>%
        distinct(biotools_id, omic_type, maintenance, publication_year, total_citations, .keep_all = TRUE) %>%
        mutate(
            publication_year = suppressWarnings(as.integer(publication_year)),
            age = current_year - publication_year,
            citations_log = log1p(as.numeric(total_citations)),
            maintenance = factor(maintenance, levels = maintenance_order)
        ) %>%
        filter(!is.na(age), is.finite(citations_log), maintenance %in% maintenance_order)

    if (nrow(df_age_maint) > 0) {
        df_age_maint_trend <- build_trend_band_df(
            df_age_maint,
            age,
            citations_log,
            group_col = "maintenance",
            span = optimal_span
        )

        p_age_by_maintenance <- ggplot(df_age_maint, aes(x = age, y = citations_log, color = maintenance)) +
            geom_jitter(alpha = 0.35, width = 0.2, size = 1.5) +
            facet_wrap(~maintenance, ncol = 4) +
            geom_ribbon(
                data = df_age_maint_trend,
                aes(x = age, ymin = ymin, ymax = ymax, group = maintenance),
                inherit.aes = FALSE,
                fill = "grey40",
                alpha = 0.5
            ) +
            geom_line(
                data = df_age_maint_trend,
                aes(x = age, y = trend, group = maintenance),
                inherit.aes = FALSE,
                color = "white",
                linetype = "dashed",
                linewidth = 0.9
            ) +
            labs(
                title = "Tool-domain record age vs citations by repository commit-recency status",
                subtitle = "Shows whether inactive/stale records are older and have had more time to accumulate citations",
                x = axis_labels$age,
                y = axis_labels$citations_log,
                color = legend_labels$maintenance
            ) +
            scale_color_manual(values = maintenance_palette, name = legend_labels$maintenance) +
            landscape_plot_theme(legend.position = "none", plot_fill = "grey92", panel_fill = "grey92") +
            theme(strip.text = element_text(face = "bold", size = 11))

        save_plot(p_age_by_maintenance, "maintenance_age_vs_citations_faceted", width = 14, height = 5, dpi = 300)

        # Create a companion faceted plot with maintenance-specific outliers removed.
        df_age_maint_outlier <- df_age_maint %>%
            group_by(maintenance) %>%
            group_modify(~ {
                .x <- .x %>% filter(is.finite(age), is.finite(citations_log))
                if (nrow(.x) == 0) return(.x)

                .x$predicted_log <- predict_trend_values(.x$age, .x$citations_log, span = optimal_span)
                .x$residual <- .x$citations_log - .x$predicted_log

                resid_sd <- sd(.x$residual, na.rm = TRUE)
                if (!is.finite(resid_sd) || resid_sd <= 0) {
                    .x$is_outlier <- FALSE
                } else {
                    .x$is_outlier <- abs(.x$residual) > (2.5 * resid_sd)
                }
                .x
            }) %>%
            ungroup()

        n_maint_outliers <- sum(df_age_maint_outlier$is_outlier, na.rm = TRUE)

        df_age_maint_clean <- df_age_maint_outlier
        maint_display_limits <- range(df_age_maint_clean$citations_log[!df_age_maint_clean$is_outlier], na.rm = TRUE)

        df_age_maint_clean_trend <- build_trend_band_df(
            df_age_maint_clean,
            age,
            citations_log,
            group_col = "maintenance",
            span = optimal_span
        )

        p_age_by_maintenance_clean <- ggplot(df_age_maint_clean, aes(x = age, y = citations_log, color = maintenance)) +
            geom_jitter(alpha = 0.35, width = 0.2, size = 1.5) +
            facet_wrap(~maintenance, ncol = 4) +
            geom_ribbon(
                data = df_age_maint_clean_trend,
                aes(x = age, ymin = ymin, ymax = ymax, group = maintenance),
                inherit.aes = FALSE,
                fill = "grey40",
                alpha = 0.5
            ) +
            geom_line(
                data = df_age_maint_clean_trend,
                aes(x = age, y = trend, group = maintenance),
                inherit.aes = FALSE,
                color = "white",
                linetype = "dashed",
                linewidth = 0.9
            ) +
            labs(
                title = "Tool-domain record age vs citations by repository commit-recency status (outliers removed)",
                subtitle = glue("Status-specific residual filter applied; {n_maint_outliers} outliers removed"),
                x = axis_labels$age,
                y = axis_labels$citations_log,
                color = legend_labels$maintenance
            ) +
            scale_color_manual(values = maintenance_palette, name = legend_labels$maintenance) +
            landscape_plot_theme(legend.position = "none", plot_fill = "grey92", panel_fill = "grey92") +
            theme(strip.text = element_text(face = "bold", size = 11)) +
            coord_cartesian(ylim = maint_display_limits)

        save_plot(p_age_by_maintenance_clean, "maintenance_age_vs_citations_faceted_clean", width = 14, height = 5, dpi = 300)
    }

    # Ridge plot: citation distribution by repository commit-recency status.
    p_ridge_maintenance <- ggplot(df_maint_citations, aes(x = citations_log, y = maintenance, fill = maintenance)) +
        ggridges::geom_density_ridges(
            alpha = 0.65,
            scale = 1.5,
            rel_min_height = 0.01,
            color = NA
        ) +
        labs(
            title = "Citation distribution by repository commit-recency status",
            subtitle = "Ridge curves show distribution shape; higher curves = wider spread of citations",
            x = axis_labels$citations_log,
            y = legend_labels$maintenance,
            fill = legend_labels$maintenance
        ) +
        scale_fill_manual(values = maintenance_palette, name = legend_labels$maintenance) +
        landscape_plot_theme(legend.position = "none", plot_fill = "white", panel_fill = "white")

    save_plot(p_ridge_maintenance, "maintenance_citations_ridge", width = 10, height = 6, dpi = 300)

    # Ridge plot: tool-domain record age by repository commit-recency status.
    df_age_maint_ridge <- df_for_maint %>%
        distinct(biotools_id, omic_type, publication_year, maintenance) %>%
        mutate(
            publication_year = suppressWarnings(as.integer(publication_year)),
            age = current_year - publication_year,
            maintenance = factor(maintenance, levels = maintenance_order)
        ) %>%
        filter(!is.na(age), age > 0, maintenance %in% maintenance_order)

    if (nrow(df_age_maint_ridge) > 0) {
        p_ridge_age <- ggplot(df_age_maint_ridge, aes(x = age, y = maintenance, fill = maintenance)) +
            ggridges::geom_density_ridges(
                alpha = 0.65,
                scale = 1.5,
                rel_min_height = 0.01,
                color = NA
            ) +
            labs(
                title = "Tool-domain record age distribution by repository commit-recency status",
                subtitle = "Older inactive records may explain higher accumulated citations through survivor bias",
                x = axis_labels$age,
                y = legend_labels$maintenance,
                fill = legend_labels$maintenance
            ) +
            scale_fill_manual(values = maintenance_palette, name = legend_labels$maintenance) +
            landscape_plot_theme(legend.position = "none", plot_fill = "white", panel_fill = "white")

        save_plot(p_ridge_age, "maintenance_age_ridge", width = 10, height = 6, dpi = 300)

        df_maint_age_adjusted <- df_for_maint %>%
            distinct(biotools_id, omic_type, maintenance, publication_year, total_citations) %>%
            mutate(
                publication_year = suppressWarnings(as.integer(publication_year)),
                years_since_pub = if_else(!is.na(publication_year), pmax(1, current_year - publication_year + 1L), NA_real_),
                citations_per_year = if_else(!is.na(total_citations) & !is.na(years_since_pub), as.numeric(total_citations) / years_since_pub, NA_real_),
                cpy_log = log1p(citations_per_year),
                maintenance = factor(maintenance, levels = maintenance_order)
            ) %>%
            filter(is.finite(cpy_log), maintenance %in% maintenance_order)

        p_cpy_by_maintenance <- patchwork::plot_spacer()
        if (nrow(df_maint_age_adjusted) > 0) {
            p_cpy_by_maintenance <- ggplot(df_maint_age_adjusted, aes(x = maintenance, y = cpy_log, fill = maintenance)) +
                geom_violin(alpha = 0.6, trim = FALSE, color = NA) +
                geom_jitter(width = 0.12, alpha = 0.35, size = 1.4, color = "grey20") +
                labs(
                    title = "Age-adjusted citation visibility by repository commit-recency status",
                    subtitle = "Metric = citations per year (log1p), reducing bias from record age",
                    x = legend_labels$maintenance,
                    y = axis_labels$citations_per_year_log,
                    fill = legend_labels$maintenance
                ) +
                scale_fill_manual(values = maintenance_palette, name = legend_labels$maintenance) +
                landscape_plot_theme(legend.position = "none", plot_fill = "white", panel_fill = "white")

            save_plot(p_cpy_by_maintenance, "maintenance_citations_per_year", width = 10, height = 6, dpi = 300)
        }

        p_maintenance_combined <- patchwork::wrap_plots(
            p_age_by_maintenance,
            p_ridge_maintenance,
            p_ridge_age,
            p_cpy_by_maintenance,
            ncol = 1
        ) +
            patchwork::plot_annotation(
                title = "Repository Commit-Recency Analysis",
                subtitle = "Citation and age distributions describe the GitHub-observable subset; Unknown records are excluded",
                theme = theme(
                    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
                    plot.subtitle = element_text(hjust = 0.5, size = 11)
                )
            )

        save_plot(p_maintenance_combined, "maintenance_impact_combined", width = 14, height = 18, dpi = 300)
    }
}

# Helper
clean_tool_type <- function(df, col = "tool_type") {
    col <- rlang::ensym(col)
    df %>%
        tidyr::separate_rows(!!col, sep = ",|;") %>%
        mutate(
            !!col := dplyr::if_else(
                is.na(!!col) | trimws(!!col) == "",
                NA_character_,
                trimws(!!col)
            )
        )
}

tool_type_totals <- df_for_maint_github %>%
    clean_tool_type("tool_type") %>%
    # normalize and trim tool_type; treat empty strings as NA
    distinct(biotools_id, omic_type, tool_type, .keep_all = TRUE) %>%
    filter(!is.na(tool_type)) %>%
    # Count tool-domain records per tool type; result has `total_by_tool`.
    count(tool_type, name = "total_by_tool") %>%
    arrange(desc(total_by_tool))

# Tool-domain record counts by omic type, tool type, and commit-recency status.
make_top_tool_status <- function(status_df, totals_df, top_n = 5L) {
    top_tool_types <- totals_df %>%
        arrange(desc(total_by_tool)) %>%
        slice_head(n = top_n) %>%
        pull(tool_type)

    ordered_levels <- totals_df %>%
        filter(tool_type %in% top_tool_types) %>%
        arrange(desc(total_by_tool)) %>%
        pull(tool_type)

    status_df %>%
        filter(tool_type %in% top_tool_types) %>%
        mutate(tool_type = factor(tool_type, levels = ordered_levels))
}

tool_status_count <- df_for_maint_github %>%
    clean_tool_type("tool_type") %>%
    distinct(biotools_id, omic_type, tool_type, maintenance, .keep_all = TRUE) %>%
    mutate(tool_type = coalesce(tool_type, "Unknown")) %>%
    count(omic_type, tool_type, maintenance, name = "n") %>%
    left_join(tool_type_totals, by = "tool_type") %>%
    mutate(total_by_tool = tidyr::replace_na(total_by_tool, 0)) %>%
    make_top_tool_status(tool_type_totals, top_n = 5L)

# Calculate overall count per tool_type (across all omics) for top-of-bar labels
tool_status_totals_overall <- tool_status_count %>%
    group_by(tool_type) %>%
    summarise(total_overall = sum(n), .groups = "drop")

tool_status_labels <- tool_status_count %>%
    group_by(omic_type, tool_type) %>%
    summarise(total_in_panel = sum(n), .groups = "drop") %>%
    left_join(tool_status_totals_overall, by = "tool_type")

p_tool_status_count <- ggplot(
    tool_status_count,
    aes(x = tool_type, y = n, fill = maintenance)
) +
    geom_col(position = "stack") +
    facet_wrap(~omic_type) +
    coord_flip() +
    geom_text(
        data = tool_status_labels, aes(x = tool_type, y = total_in_panel * 1.02, label = paste0("Total: ", total_overall)),
        inherit.aes = FALSE, hjust = -0.05, size = 3, fontface = "bold"
    ) +
    labs(
        title = "Repository commit-recency counts by tool type and omics domain",
        subtitle = "Bar-end labels show tool-domain record counts summed across omics domains",
        x = "Tool type", y = axis_labels$tool_count, fill = legend_labels$maintenance
    ) +
    theme(
        axis.text.y = element_text(size = 8),
        strip.text = element_text(size = 10), plot.background = element_rect(fill = "white"), panel.background = element_rect(fill = "white")
    ) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
    scale_fill_manual(values = maintenance_palette, na.value = maintenance_palette[["Unknown"]], name = legend_labels$maintenance)

save_plot(p_tool_status_count, "tool_type_status", width = 10, height = 8, dpi = 300)

# ============================================================
# Citation visibility versus GitHub engagement
# ============================================================
engagement_df <- df_for_maint_github %>%
  # Quadrants use the complete maintenance dataset
  select(-any_of(c(
    "is_outlier", "outlier_status", "residual",
    "predicted_log", "citations_log"
  ))) %>%
  
  distinct(
    biotools_id, omic_type, name, maintenance, github_repo,
    publication_year, total_citations, stars, forks, watchers
  ) %>%
  
  # Canonical per-tool metrics used as fallbacks
  left_join(
    df_tools_unique %>%
      select(
        biotools_id,
        omic_type,
        publication_year_tool = publication_year,
        total_citations_tool = total_citations,
        stars_tool = stars,
        forks_tool = forks,
        watchers_tool = watchers
      ),
    by = c("biotools_id", "omic_type")
  ) %>%
  
  mutate(
    publication_year = coalesce(
      suppressWarnings(as.integer(publication_year)),
      suppressWarnings(as.integer(publication_year_tool))
    ),
    total_citations = coalesce(
      as.numeric(total_citations),
      as.numeric(total_citations_tool)
    ),
    stars = coalesce(
      as.numeric(stars),
      as.numeric(stars_tool)
    ),
    forks = coalesce(
      as.numeric(forks),
      as.numeric(forks_tool)
    ),
    watchers = coalesce(
      as.numeric(watchers),
      as.numeric(watchers_tool)
    )
  ) %>%
  
  mutate(
    years_since_pub = if_else(
      !is.na(publication_year),
      pmax(1L, current_year - publication_year + 1L),
      NA_real_
    ),
    
    citations_per_year = if_else(
      !is.na(total_citations) & !is.na(years_since_pub),
      total_citations / years_since_pub,
      NA_real_
    ),
    
    citation_visibility_log = if_else(
      !is.na(citations_per_year),
      log1p(citations_per_year),
      NA_real_
    ),
    
    github_metrics_observed =
      !is.na(github_repo) &
      if_any(c(stars, forks, watchers), ~ !is.na(.x)),
    
    github_engagement_total = if_else(
      github_metrics_observed,
      replace_na(stars, 0) +
        replace_na(forks, 0) +
        replace_na(watchers, 0),
      NA_real_
    ),
    
    github_engagement_log = if_else(
      github_metrics_observed,
      log1p(github_engagement_total),
      NA_real_
    )
  )

engagement_axis_limits <- engagement_df %>%
  filter(
    is.finite(citation_visibility_log),
    is.finite(github_engagement_log)
  ) %>%
  summarise(
    x_min = min(citation_visibility_log, na.rm = TRUE),
    x_max = max(citation_visibility_log, na.rm = TRUE),
    y_min = min(github_engagement_log, na.rm = TRUE),
    y_max = max(github_engagement_log, na.rm = TRUE)
  )

engagement_axis_limits
# Citation visibility versus GitHub engagement plot

plot_citation_engagement <- function(
    omics_filter,
    df = engagement_df,
    axis_limits = engagement_axis_limits,
    top_n_labels = 12)
  {

    # Normalize maintenance for plotting (independent of upstream factor)
    sub <- df %>%
      filter(omic_type == omics_filter)
    
    if (nrow(sub) == 0) {
      return(NULL)
    }
    
    sub <- sub %>%
      mutate(
        maintenance_plot = normalize_maintenance(maintenance)
      )

    # Print maintenance composition for debugging (use maintenance_plot)
    maint_counts <- sub %>%
        count(maintenance_plot) %>%
        arrange(desc(n))
    message(glue("{omics_filter}: repository commit-recency levels (total {nrow(sub)}): ", paste0(as.character(maint_counts$maintenance_plot), "=", maint_counts$n, collapse = ", ")))

    # Keep only rows with finite numeric metrics for plotting
    sub_fin <- sub %>% filter(is.finite(citation_visibility_log) & is.finite(github_engagement_log))
    # Use maintenance_plot for counts among finite rows
    maint_counts_fin <- sub_fin %>%
        count(maintenance_plot) %>%
        arrange(desc(n))
    message(glue("{omics_filter}: repository commit-recency levels among finite rows (total {nrow(sub_fin)}): ", paste0(as.character(maint_counts_fin$maintenance_plot), "=", maint_counts_fin$n, collapse = ", ")))
    if (nrow(sub_fin) < 3) {
        message(glue("Skipping citation-engagement plot for {omics_filter}: insufficient numeric metrics (n = {nrow(sub_fin)})."))
        return(NULL)
    }

    x_med <- median(sub_fin$citation_visibility_log, na.rm = TRUE)
    y_med <- median(sub_fin$github_engagement_log, na.rm = TRUE)
    if (is.na(x_med) || is.na(y_med)) {
        message(glue("Skipping citation-engagement plot for {omics_filter}: median(s) are NA."))
        return(NULL)
    }

    # Top-right quadrant labels
    top_tools <- sub_fin %>%
        filter(citation_visibility_log > x_med, github_engagement_log > y_med) %>%
        slice_max(order_by = (citation_visibility_log + github_engagement_log), n = top_n_labels)

    # log1p guide lines for easier interpretation of multiplicative differences
    x_guides <- log1p(c(1, 10, 100))
    y_guides <- log1p(c(10, 100, 1000))

    plotted_n <- nrow(sub_fin)
    eligible_n <- nrow(sub)
    unknown_n <- eligible_n - plotted_n
    ggplot(sub_fin, aes(x = citation_visibility_log, y = github_engagement_log, color = maintenance_plot)) +
        geom_point(alpha = 0.35, size = 1.5) +
        geom_vline(xintercept = x_med, linetype = "dashed", color = "gray40") +
        geom_hline(yintercept = y_med, linetype = "dashed", color = "gray40") +
        geom_vline(xintercept = x_guides, linetype = "dotted", color = "gray65", linewidth = 0.4) +
        geom_hline(yintercept = y_guides, linetype = "dotted", color = "gray65", linewidth = 0.4) +
        annotate("text", x = Inf, y = Inf, label = "higher citations, higher engagement",
                 hjust = 1.03, vjust = 1.4, size = 3, colour = "grey25") +
        annotate("text", x = -Inf, y = Inf, label = "lower citations, higher engagement",
                 hjust = -0.03, vjust = 1.4, size = 3, colour = "grey25") +
        annotate("text", x = Inf, y = -Inf, label = "higher citations, lower engagement",
                 hjust = 1.03, vjust = -0.6, size = 3, colour = "grey25") +
        annotate("text", x = -Inf, y = -Inf, label = "lower citations, lower engagement",
                 hjust = -0.03, vjust = -0.6, size = 3, colour = "grey25") +
        ggrepel::geom_text_repel(
            data = top_tools, aes(label = name),
            size = 3, max.overlaps = Inf, box.padding = 0.4,
            point.padding = 0.2, segment.color = "grey60", seed = 42
        ) +
        scale_color_manual(values = maintenance_palette, na.value = maintenance_palette[["Unknown"]]) +
        #scale_x_continuous(limits = c(engagement_axis_limits$x_min, engagement_axis_limits$x_max), expand = expansion(mult = c(0.03, 0.05))) +
        #scale_y_continuous(limits = c(engagement_axis_limits$y_min, engagement_axis_limits$y_max), expand = expansion(mult = c(0.03, 0.05))) +
      scale_x_continuous(
        expand = expansion(mult = c(0.03, 0.05))
      ) +
      scale_y_continuous(
        expand = expansion(mult = c(0.03, 0.05))
      ) +
      coord_cartesian(
        xlim = c(
          axis_limits$x_min,
          axis_limits$x_max
        ),
        ylim = c(
          axis_limits$y_min,
          axis_limits$y_max
        )
      ) +
        labs(
            title = glue("{omics_filter}: Age-adjusted citation visibility versus GitHub engagement"),
            subtitle = glue("Plotted {plotted_n}/{eligible_n} tool-domain records; missing citation or GitHub metrics: {unknown_n}. Dashed lines: within-domain medians"),
            x = "Citations per year (log1p)", y = axis_labels$github_engagement_log,
            color = legend_labels$maintenance
        ) +
        theme_bw() +
        theme(
            plot.title = element_text(hjust = 0.5, face = "bold"),
            legend.position = "bottom",
            plot.background = element_rect(fill = "white"),
            panel.background = element_rect(fill = "white")
        )
}

# Ensure citation-engagement plots follow the canonical omic ordering
# Use `desired_omic_levels` and keep only those present in the data, preserving order
#omics_list_plot <- desired_omic_levels[desired_omic_levels %in% unique(na.omit(as.character(engagement_df$omic_type)))]
#engagement_plots <- map(omics_list_plot, plot_citation_engagement) %>% compact()
omics_list_plot <- desired_omic_levels[
  desired_omic_levels %in%
    unique(na.omit(as.character(engagement_df$omic_type)))
]

engagement_plots <- map(
  omics_list_plot,
  ~plot_citation_engagement(
    omics_filter = .x,
    df = engagement_df,
    axis_limits = engagement_axis_limits
  )
) %>%
  purrr::discard(is.null)

p_engagement_combined <- patchwork::wrap_plots(engagement_plots, ncol = 2)
save_plot(p_engagement_combined, "citation_visibility_vs_github_engagement", width = 14, height = 10, dpi = 300)

# ============================================================
# Figure-level audit and reproducibility manifest
# ============================================================

candidate_denominators <- df_for_plots %>% distinct(biotools_id, omic_type) %>%
    count(omic_type, name = "eligible_tools")

figure_audit <- bind_rows(
    edam_results$figure_audit,
    candidate_denominators %>% transmute(
      figure_name = "citation_visibility_vs_github_engagement",
      population = "Filtered adoption-candidate population", omic_type,
      eligible_tools,
      plotted_tools = map_int(omic_type, ~sum(engagement_df$omic_type == .x &
                                               is.finite(engagement_df$citation_visibility_log) &
                                               is.finite(engagement_df$github_engagement_log), na.rm = TRUE)),
      missing_or_unobserved = eligible_tools - plotted_tools
    ),
    maintenance_distribution %>% group_by(omic_type) %>% summarise(
      figure_name = "maintenance_distribution_all_candidates",
      population = "Filtered adoption-candidate population",
      eligible_tools = unique(denominator), plotted_tools = unique(denominator),
      missing_or_unobserved = sum(n[as.character(maintenance) == "Unknown"]), .groups = "drop"
    ),
    candidate_denominators %>% transmute(
      figure_name = "tool_type_distribution_by_omics",
      population = "Filtered adoption-candidate population", omic_type,
      eligible_tools, plotted_tools = eligible_tools,
      missing_or_unobserved = map_int(omic_type, function(domain) {
        df_for_plots %>% filter(omic_type == domain) %>%
          summarise(n = sum(is.na(tool_type) | !nzchar(trimws(as.character(tool_type))))) %>% pull(n)
      })
    ),
    candidate_denominators %>% transmute(
      figure_name = "technical_stack_combined",
      population = "Filtered adoption-candidate population", omic_type,
      eligible_tools, plotted_tools = eligible_tools,
      missing_or_unobserved = map_int(omic_type, function(domain) {
        df_for_plots %>% filter(omic_type == domain) %>%
          summarise(n = sum((is.na(language) | !nzchar(trimws(as.character(language)))) |
                            (is.na(operating_system) | !nzchar(trimws(as.character(operating_system)))) |
                            (is.na(license) | !nzchar(trimws(as.character(license)))))) %>% pull(n)
      })
    ),
    candidate_denominators %>% transmute(
      figure_name = "age_vs_citations_combined",
      population = "Filtered adoption-candidate population", omic_type,
      eligible_tools,
      plotted_tools = map_int(omic_type, ~sum(df_age_citations_full$omic_type == .x, na.rm = TRUE)),
      missing_or_unobserved = eligible_tools - plotted_tools
    )
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

prefer_rds_population <- function(paths) {
  rds_paths <- sub("\\.tsv$", ".rds", paths, ignore.case = TRUE)
  ifelse(file.exists(rds_paths), rds_paths, paths)
}
candidate_population_inputs <- prefer_rds_population(unlist(omic_files, use.names = FALSE))
full_population_inputs <- prefer_rds_population(
  file.path(filter_results_dir, paste0(names(domain_map), params$populations$full_suffix))
)

manifest_inputs <- unique(c(
  normalizePath(config_file, winslash = "/", mustWork = TRUE),
  normalizePath(edam_module, winslash = "/", mustWork = TRUE),
  normalizePath(candidate_population_inputs, winslash = "/", mustWork = TRUE),
  normalizePath(full_population_inputs, winslash = "/", mustWork = TRUE),
  normalizePath(file.path(config_dir, params$inputs$mapped_operations), winslash = "/", mustWork = TRUE),
  normalizePath(file.path(config_dir, params$edam$ontology_snapshot), winslash = "/", mustWork = TRUE),
  normalizePath(file.path(config_dir, params$inputs$validation_sample), winslash = "/", mustWork = FALSE),
  normalizePath(cache_file, winslash = "/", mustWork = FALSE)
))
manifest_inputs <- manifest_inputs[file.exists(manifest_inputs)]
reproducibility_manifest <- list(
  pipeline = "bio.tools landscape visualization with EDAM Operation analysis",
  analysis_date = as.character(analysis_date),
  run_date = as.character(Sys.Date()),
  population_unit = "biotools_id + omic_type tool-domain record",
  population_source_format = "RDS preferred; sanitized TSV fallback",
  populations = list(
    full_retrieved = nrow(edam_results$full_population),
    filtered_adoption_candidate = nrow(edam_results$candidate_population)
  ),
  edam = list(valid_status = params$edam$valid_status, aggregation_depth = params$edam$aggregation_depth),
  github = list(
    engagement_components = unname(params$github$engagement_components),
    open_issues_included = isTRUE(params$github$include_open_issues_in_engagement),
    missing_treatment = params$github$missing_github_treatment,
    status_measure = "Repository commit-recency status"
  ),
  composite_score = list(
    role = "exploratory supplementary ranking only",
    validated_measure_of_quality_or_adoption = FALSE
  ),
  loess = list(role = "descriptive visualization only", candidate_exclusion = FALSE),
  inputs = lapply(manifest_inputs, function(path) list(
    path = path, md5 = unname(tools::md5sum(path)), bytes = unname(file.info(path)$size)
  )),
  software = list(
    R = R.version.string,
    platform = R.version$platform,
    packages = as.list(vapply(c("dplyr", "readr", "ggplot2", "tidyr", "purrr", "yaml", "lubridate"),
                              function(pkg) as.character(utils::packageVersion(pkg)), character(1)))
  ),
  outputs = list(directory = normalizePath(outdir, winslash = "/", mustWork = TRUE),
                 figure_audit_rows = nrow(figure_audit))
)
jsonlite::write_json(reproducibility_manifest,
                     file.path(outdir, paste0("reproducibility_manifest_", today, ".json")),
                     pretty = TRUE, auto_unbox = TRUE, na = "null")

