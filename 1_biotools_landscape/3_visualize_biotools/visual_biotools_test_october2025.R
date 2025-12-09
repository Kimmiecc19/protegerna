# ============================================================
# Multi-Omics Tool Landscape
# ============================================================
# Author: Kimberly Coetzer
# Purpose: Visually investigate the omics tool landscape
# token: available on request
# ============================================================

# ========================
# Package management: check/install and load required packages
# ========================
required_packages <- c(
  "tidyverse", "httr", "jsonlite", "lubridate", "readr", "purrr", "ggplot2", "dplyr", "tidyr", "forcats", "ComplexUpset", "glue", "ggraph", "scales", "yaml", "igraph", "lubridate", "ggrepel", "patchwork"
)

# Install any missing packages
for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
}

# -----------------------------
# Load packages
# -----------------------------
suppressPackageStartupMessages({
  library(tidyverse) # ggplot2, dplyr, tidyr, purrr, readr, forcats, etc.
  library(igraph)
  library(ggraph)
  library(yaml)
  library(httr)
  library(jsonlite)
  library(ComplexUpset)
  library(glue)
  library(scales)
  library(ggrepel)
  library(patchwork)
  library(lubridate)
})

# Probably UNNECESSARY?
# Safe 'or' operator (fallback) used in several palette lookups.
`%||%` <- function(a, b) {
  if (is.null(a) || length(a) == 0) return(b)
  if (length(a) == 1 && (is.na(a) || identical(a, "") )) return(b)
  a
}

# -----------------------------
# Output directory setup
# -----------------------------
outdir <- "output_october2025"
if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE)

# -----------------------------
# Load configuration (YAML)
# -----------------------------
config_file <- "visualize_config.yaml"
if (!file.exists(config_file)) {
  stop(glue("Configuration file not found: {config_file}"))
}

params <- yaml::read_yaml(config_file)
if (!is.null(params$token) && params$token != "") {
  Sys.setenv(GITHUB_TOKEN = params$token)
  message("GitHub token loaded from configuration.")
} else {
  message("No GitHub token found — using unauthenticated API calls (rate limit = 60/hr).")
}

# -----------------------------
# RDS file loading helpers
# -----------------------------
read_omic_rds <- function(files) {
  purrr::imap_dfr(files, function(path, omic_type) {
    if (!file.exists(path)) stop(glue("File not found: {path}"))
    df <- readRDS(path)
    df$omic_type <- str_to_title(omic_type)
    df
  })
}

# Define expected omic RDS files
# These files are the outputs from filter_biotools_June2025.R
omic_files <- list(
  proteomics     = "proteomic_annotated_filtered_tools_october2025.rds",
  genomics       = "genomic_annotated_filtered_tools_october2025.rds",
  transcriptomics = "transcriptomic_annotated_filtered_tools_october2025.rds",
  multiomics     = "multiomic_annotated_filtered_tools_october2025.rds"
)

# Load and combine all omics
tools_combined <- read_omic_rds(omic_files)
tools_unique <- tools_combined %>% distinct(name, omic_type, .keep_all = TRUE)

write_csv(tools_unique, file.path(outdir, "tools_unique.csv"))
message(glue("Combined omics dataset: {nrow(tools_unique)} unique entries."))

# -----------------------------
# Data cleaning and metrics
# -----------------------------
clean_tools_data <- function(df, current_year = year(Sys.Date())) {
  df %>%
    filter(!is.na(total_citations), !is.na(publication_year)) %>%
    distinct(name, omic_type, .keep_all = TRUE) %>%
    mutate(
      publication_year   = as.integer(publication_year),
      citations_per_year = total_citations / pmax(current_year - publication_year + 1, 1)
    )
}

tools_cleaned <- clean_tools_data(tools_combined)
saveRDS(tools_cleaned, file = file.path(outdir, "tools_cleaned_cache.rds"))

# ============================================================
# Utility Functions for Plotting and GitHub API
# ============================================================
# -----------------------------
# Multi-format plot saver
# -----------------------------
save_plot_multi <- function(filename, plot, width = 8, height = 6, dpi = 300) {
  tryCatch({
    ggsave(paste0(filename, ".png"), plot, width = width, height = height, dpi = dpi)
    ggsave(paste0(filename, ".svg"), plot, width = width, height = height, dpi = dpi)
  }, error = function(e) {
    message(glue("Plot saving failed for {filename}: {e$message}"))
  })
}

# -----------------------------
# Safe plotting wrapper
# -----------------------------
safe_plot <- function(expr) {
  tryCatch(expr, error = function(e) {
    message("Plotting error: ", e$message)
    NULL
  })
}

# ============================================================
# GitHub Metadata Integration
# ============================================================
# -----------------------------
# Extract GitHub repo info
# -----------------------------
tools_with_github <- tools_cleaned %>%
  mutate(
    github_url  = str_extract(paste(homepage, documentation, sep = " "),
                              "https?://github\\.com/[^/\\s]+/[^/\\s]+"),
    github_repo = str_remove(github_url, "https?://github\\.com/")
  )

# -----------------------------
# GitHub API query functions
# -----------------------------
get_github_metadata_full <- function(repo, token = NULL) {
  url <- paste0("https://api.github.com/repos/", repo)
  hdr <- add_headers(Accept = "application/vnd.github.v3+json")
  if (!is.null(token) && token != "") {
    hdr <- add_headers(
      Authorization = paste("token", token),
      Accept = "application/vnd.github.v3+json"
    )
  }

  res <- GET(url, hdr)
  sc <- status_code(res)

  if (sc == 200) {
    content <- fromJSON(content(res, as = "text"))
    list(
      stars        = content$stargazers_count,
      forks        = content$forks_count,
      watchers     = content$subscribers_count,
      open_issues  = content$open_issues_count,
      last_commit  = content$pushed_at
    )
  } else {
    msg_snip <- substr(tryCatch(content(res, as = "text"), error = \(e) "[no body]"), 1, 400)
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
# GitHub cache handling
# -----------------------------
cache_file <- "github_commit_cache_october2025.csv"
cache_df <- if (file.exists(cache_file)) {
  read_csv(cache_file, show_col_types = FALSE)
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

# Identify repos not yet cached
repos_to_query <- tools_with_github %>%
  filter(!is.na(github_repo)) %>%
  distinct(github_repo) %>%
  filter(!github_repo %in% cache_df$github_repo) %>%
  pull(github_repo)

message(glue("Total repos to query: {length(repos_to_query)}"))

# -----------------------------
# Batch GitHub querying with rate-limit handling
# -----------------------------
batch_size <- 100
n_batches <- ceiling(length(repos_to_query) / batch_size)

for (i in seq_len(n_batches)) {
  message(glue("Batch {i} / {n_batches}"))
  batch_repos <- repos_to_query[((i - 1) * batch_size + 1):min(i * batch_size, length(repos_to_query))]

  batch_results <- map(batch_repos, safe_get_github_metadata_full)

  batch_df <- tibble(
    github_repo = batch_repos,
    last_commit = map_chr(batch_results, "last_commit", .default = NA_character_),
    stars       = map_dbl(batch_results, "stars", .default = NA_real_),
    forks       = map_dbl(batch_results, "forks", .default = NA_real_),
    watchers    = map_dbl(batch_results, "watchers", .default = NA_real_),
    open_issues = map_dbl(batch_results, "open_issues", .default = NA_real_)
  )

  # Merge and update cache
  cache_df <- bind_rows(cache_df, batch_df) %>%
    distinct(github_repo, .keep_all = TRUE)

  write_csv(cache_df, cache_file)

  # Pause every few batches to avoid API limits
  if (i %% 5 == 0) {
    message("⏸ Pausing briefly to respect GitHub API limits...")
    Sys.sleep(30)
  }
}

# -----------------------------
# Join GitHub metadata back to tools
# -----------------------------
tools_augmented_github <- tools_with_github %>%
  left_join(cache_df, by = "github_repo") %>%
  mutate(
    last_commit = as.Date(last_commit),
    commit_year = year(last_commit),
    across(c(stars, forks, watchers, open_issues), as.numeric)
  )

saveRDS(tools_augmented_github, "tools_augmented_github_full.rds")
write_csv(tools_augmented_github, "tools_augmented_github_full.csv")

message(glue("✓ GitHub metadata integrated for {nrow(tools_augmented_github)} tools."))

# -----------------------------
# Global defaults and options
# -----------------------------
options(
  stringsAsFactors = FALSE,
  readr.show_col_types = FALSE,
  scipen = 999
)

# Seed for reproducibility 
set.seed(42) 

# ================================
# Unified global theme + palette
# ================================

# Omics colours (fixed, non-interpolated) -> based on SU colour palette
omics_colors <- c(
  Genomics       = "#B79962",  # gold
  Transcriptomics = "#61223B", # maroon
  Proteomics     = "#005F61",  # green
  Multiomics     = "#223D71"   # navy
)

# Generic fallback palette for categories NOT = omic_type
# TODO: change to colours other than grey
extra_palette <- c(
  "#888888", "#A0A0A0", "#4A4A4A", "#C0C0C0", "#707070"
)

# ---- Unified colour scales ----
scale_color_omics <- function(...) {
  ggplot2::scale_color_manual(values = omics_colors, ...)
}

scale_fill_omics <- function(...) {
  ggplot2::scale_fill_manual(values = omics_colors, ...)
}

# ---- Generic (non-omics) categorical scales ----
scale_color_extra <- function(n = 10, ...) {
  ggplot2::scale_color_manual(values = rep(extra_palette, length.out = n), ...)
}

scale_fill_extra <- function(n = 10, ...) {
  ggplot2::scale_fill_manual(values = rep(extra_palette, length.out = n), ...)
}

# ---- Global minimal theme ----
theme_set(
  ggplot2::theme_minimal(base_size = 12) +
    ggplot2::theme(
      panel.grid.major = element_line(size = 0.3, colour = "grey85"),
      panel.grid.minor = element_blank(),
      axis.title = element_text(size = 11),
      axis.text = element_text(size = 10),
      plot.title = element_text(size = 14, face = "bold"),
      plot.subtitle = element_text(size = 12),
      legend.position = "right"
    )
)

# -----------------------------
# Helper functions
# -----------------------------

# ---- License classifier ----
classify_license <- function(x) {
  x <- tolower(x)
  case_when(
    is.na(x) | x == "" ~ "Unknown",
    str_detect(x, "mit|bsd|apache|cc0|isc") ~ "Permissive",
    str_detect(x, "gpl|lgpl|agpl") ~ "Restrictive",
    TRUE ~ "Other"
  )
}

# ---- Safe numeric conversion ----
to_numeric_safe <- function(x) {
  suppressWarnings(as.numeric(as.character(x)))
}

# -----------------------------
# File paths and intermediate inputs (optional if available)
# -----------------------------
# Expecting a pre-processed metadata table
input_file <- "tools_augmented_github_full.csv"

if (!file.exists(input_file)) {
  stop(glue("Input file {input_file} not found. Place it in the working directory."))
}

tools_augmented_github <- read_csv(input_file)

message(glue("Loaded {nrow(tools_augmented_github)} rows from {input_file}."))

# ============================================================
# Data Processing & Summaries
# ============================================================

# -----------------------------
# Helper local utilities
# -----------------------------
# coalesce to NA for empty strings
empty_to_na <- function(x) {
  x <- as.character(x)
  x[trimws(x) == ""] <- NA_character_
  x
}

# Extract first non-NA element from a delimited string
first_from_delim <- function(x, sep = ";\\s*|,\\s*") {
  sapply(x, function(s) {
    if (is.na(s)) return(NA_character_)
    toks <- unlist(strsplit(as.character(s), sep))
    toks <- toks[toks != ""]
    if (length(toks) == 0) return(NA_character_) else trimws(toks[1])
  }, USE.NAMES = FALSE)
}

# Safe date parse that returns NA on failure
safe_as_date <- function(x) {
  # Normalize common ISO-like formats before parsing (T/Z timezone markers)
  s <- as.character(x)
  s[is.na(s)] <- NA_character_
  # replace literal 'T' between date and time with space, strip trailing Z
  s_clean <- s %>% stringr::str_replace_all("T", " ") %>% stringr::str_replace_all("Z$", "")

  # Try a few parsers in order: as.Date, ymd_hms, ymd
  out <- suppressWarnings(as.Date(s_clean))
  if (!all(is.na(out))) return(out)

  out2 <- suppressWarnings(lubridate::ymd_hms(s_clean, quiet = TRUE))
  if (!all(is.na(out2))) return(as.Date(out2))

  out3 <- suppressWarnings(lubridate::ymd(s_clean, quiet = TRUE))
  if (!all(is.na(out3))) return(as.Date(out3))

  # final fallback: return NA Date
  as.Date(NA)
}

# -----------------------------
# Minimal column normalization / selection
# -----------------------------
# Start from the loaded dataset and keep the columns used later.
df_for_plots <- tools_augmented_github %>%
  #distinct(name, tool_type, omic_type, topic, Function, .keep_all = TRUE) %>%
  distinct(name, omic_type, .keep_all = TRUE) %>%
  select(-github_repo, -publication_citations,
         -publication_abstract, -publication_date, -publication_title,
         -homepage, -documentation, everything())

df_tools_unique <- df_for_plots %>%
  group_by(name) %>%
  summarise(
    omic_type = paste(sort(unique(na.omit(omic_type))), collapse = "; "),
    total_citations = if (all(is.na(total_citations))) NA_real_ else max(as.numeric(total_citations), na.rm = TRUE),
    publication_year = if (all(is.na(publication_year))) NA_integer_ else as.integer(min(publication_year, na.rm = TRUE)),
    stars = if (all(is.na(stars))) NA_real_ else max(as.numeric(stars), na.rm = TRUE),
    forks = if (all(is.na(forks))) NA_real_ else max(as.numeric(forks), na.rm = TRUE),
    watchers = if (all(is.na(watchers))) NA_real_ else max(as.numeric(watchers), na.rm = TRUE),
    commit_year = if (all(is.na(commit_year))) NA_integer_ else as.integer(max(commit_year, na.rm = TRUE)),
    last_commit = if (all(is.na(last_commit))) as.Date(NA) else as.Date(max(last_commit, na.rm = TRUE)),
    .groups = "drop"
  ) %>%
  ungroup()

write_csv(df_tools_unique, file.path(outdir, "df_tools_unique.csv"))

# -----------------------------
# Enrich df_for_plots with more metrics
# -----------------------------
current_year <- lubridate::year(Sys.Date())

df_for_plots <- df_for_plots %>%
  mutate(
    # publication_year extraction from either explicit column or publication_date string
    publication_year = coalesce(
      suppressWarnings(as.integer(publication_year)),
      as.integer(str_extract(as.character(publication_date), "\\b(19|20)\\d{2}\\b"))
    ),
    #publication_date = if_else(!is.na(publication_year), as.character(publication_year), as.character(publication_date)),
    current_year = current_year,
    years_since_pub = if_else(!is.na(publication_year), pmax(1, current_year - publication_year + 1L), NA_real_),
    total_citations = to_numeric_safe(total_citations),
    # publication_citations may have weird formatting; attempt to extract first numeric token
    citations_total = coalesce(
      suppressWarnings(as.numeric(readr::parse_number(
        purrr::map_chr(str_split(as.character(publication_citations), ",|;|\\s+"),
                       ~{ toks <- .x[.x != ""]; if (length(toks) >= 1) toks[1] else NA_character_ })
      ))),
      total_citations
    ),
    citations_per_year = if_else(!is.na(citations_total) & !is.na(years_since_pub), citations_total / years_since_pub, NA_real_),
  )

# write cleaned working table as intermediate output
write_csv(df_for_plots, file.path(outdir, "df_for_plots_clean.csv"))
message("Wrote df_for_plots_clean.csv with ", nrow(df_for_plots), " rows.")

# -----------------------------
# License classification and palette mapping
# -----------------------------
df_license <- df_for_plots %>%
  mutate(license_class = classify_license(license)) %>%
  distinct(name, license_class) %>%
  count(license_class) %>%
  mutate(pct = n / sum(n)) %>%
  arrange(desc(n))

write_csv(df_license, file.path(outdir, "license_counts.csv"))
message("Wrote license_counts.csv with ", nrow(df_license), " license categories.")

# Map license classes to palette using global palette; provide sensible fallbacks
core_palette <- c(
  DarkGreen = "#005F61",
  Maroon    = "#61223B",
  Gold      = "#B79962",
  Navy      = "#223D71"
)

license_palette <- c(
  Permissive  = core_palette["DarkGreen"] %||% "#005F61",
  Restrictive = core_palette["Maroon"]    %||% "#61223B",
  Other       = core_palette["Gold"]      %||% "#B79962",
  Unknown     = "#CCCCCC"
)

# -----------------------------
# 6. Maintenance palette (explicit)
# -----------------------------
maintenance_palette <- c(
  Active   = core_palette[["DarkGreen"]] %||% "#005F61",
  Inactive = core_palette[["Gold"]]      %||% "#B79962",
  Stale    = core_palette[["Gold"]]      %||% "#B79962",
  Dead     = core_palette[["Maroon"]]    %||% "#61223B",
  Unknown  = core_palette[["Navy"]]      %||% "#223D71"
)

# persist palettes
saveRDS(list(license = license_palette, maintenance = maintenance_palette, core = core_palette),
  file.path(outdir, "palettes.rds"))
message("Saved palettes.rds")

# -----------------------------
# Precompute language grouping (for later)
# -----------------------------
map_language_group <- function(lang) {
  if (is.na(lang) || trimws(lang) == "") return("Unknown")
  lang_l <- tolower(lang)
  if (str_detect(lang_l, "^r$|\\br\\b")) return("R")
  if (str_detect(lang_l, "python")) return("Python")
  if (str_detect(lang_l, "c\\+\\+|\\bc\\b")) return("C/C++")
  if (str_detect(lang_l, "^java$|\\bjava\\b") && !str_detect(lang_l, "javascript")) return("Java")
  if (str_detect(lang_l, "javascript|node")) return("JavaScript")
  if (str_detect(lang_l, "perl")) return("Perl")
  if (str_detect(lang_l, "ruby")) return("Ruby")
  if (str_detect(lang_l, "matlab|octave")) return("MATLAB")
  if (str_detect(lang_l, "rust|go|golang")) return("Other compiled")
  str_to_title(lang_l)
}

df_lang_prep <- df_for_plots %>%
  separate_rows(language, sep = ",|;|\\\\|\\n") %>%
  mutate(language = if_else(is.na(language) | language == "", "Unknown", trimws(language)),
         language_group = map_chr(language, map_language_group)) %>%
  distinct(name, language_group) %>%
  count(language_group, name = "n") %>%
  arrange(desc(n))

write_csv(df_lang_prep, file.path(outdir, "language_groups.csv"))
message("Wrote language_groups.csv")

# -----------------------------
# Topic / Function preprocessing (for network and enrichment)
# -----------------------------
# Normalize and split topics and Function fields for downstream use
df_topic_expanded <- df_for_plots %>%
  filter(!is.na(topic)) %>%
  separate_rows(topic, sep = ",|;") %>%
  mutate(topic = str_squish(topic)) %>%
  distinct(name, topic) 

write_csv(df_topic_expanded, file.path(outdir, "topic_edges.csv"))
message("Wrote topic_edges.csv with ", nrow(df_topic_expanded), " edges.")

df_function_expanded <- df_for_plots %>%
  filter(!is.na(Function)) %>%
  separate_rows(Function, sep = ",|;") %>%
  mutate(Function = str_squish(Function)) %>%
  distinct(name, Function)

write_csv(df_function_expanded, file.path(outdir, "function_edges.csv"))
message("Wrote function_edges.csv with ", nrow(df_function_expanded), " edges.")

# Create expanded omics table (one row per tool x omic) now that df_for_plots exists
df_expanded_omics <- df_for_plots %>%
  select(name, omic_type) %>%
  mutate(omic_type = as.character(omic_type)) %>%
  separate_rows(omic_type, sep = ";\\s*|,\\s*") %>%
  mutate(omic_type = if_else(trimws(omic_type) == "", NA_character_, trimws(omic_type))) %>%
  distinct(name, omic_type) %>%
  filter(!is.na(omic_type))

write_csv(df_expanded_omics, file.path(outdir, "expanded_omics.csv"))
message("Wrote expanded_omics.csv with ", nrow(df_expanded_omics), " rows.")

# ============================================================
# Visualizations
# ============================================================

# -----------------------------
# Utility functions used by plots
# -----------------------------
safe_rescale <- function(x, to = c(0, 1)) {
  x_num <- suppressWarnings(as.numeric(x))
  if (all(is.na(x_num))) return(rep(NA_real_, length(x_num)))
  vals <- na.omit(x_num)
  if (length(unique(vals)) == 1L) return(rep(mean(to), length(x_num)))
  scales::rescale(x_num, to = to, na.rm = TRUE)
}

# -----------------------------
# Tools added per year by omics type
# -----------------------------
added_per_year <- df_for_plots %>%
  distinct(name, omic_type, added) %>%
  filter(!is.na(added)) %>%
  count(added = as.integer(added), omic_type) %>%
  arrange(added)

p_added_year <- ggplot(added_per_year, aes(x = added, y = n, fill = omic_type)) +
  geom_col() +
  facet_wrap(~omic_type, scales = "free_y", ncol = 1) +
  labs(title = "Number of tools added to bio.tools per year by omics type",
       x = "Year added", y = "Tool count") +
  scale_x_continuous(breaks = scales::pretty_breaks(10)) +
  scale_fill_omics()

ggsave(file.path(outdir, "tools_added_per_year_by_omics.png"), p_added_year, width = 10, height = 8, dpi = 300)

# -----------------------------
# Publication year vs added year (scatter)
# -----------------------------
p_pub_vs_added <- df_for_plots %>%
  mutate(publication_year = suppressWarnings(as.integer(publication_year)),
         added = suppressWarnings(as.integer(added))) %>%
  distinct(name, omic_type, publication_year, added) %>%
  filter(!is.na(publication_year), !is.na(added)) %>%
  ggplot(aes(x = publication_year, y = added, color = omic_type)) +
  geom_jitter(alpha = 0.6, width = 0.25, height = 0.25, size = 1.8) +
  facet_wrap(~omic_type, scales = "free") +
  geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "#999999") +
  labs(title = "Publication year vs. year added to bio.tools",
       x = "Publication year", y = "Year added") +
  theme(legend.position = "none") +
  scale_y_continuous(breaks = seq(ifelse(exists("current_year"), min(2015, current_year), 2015),
                                  ifelse(exists("current_year"), current_year, lubridate::year(Sys.Date())), by = 1)) +
  scale_color_omics()

ggsave(file.path(outdir, "publication_vs_year_added_scatter.png"), p_pub_vs_added, width = 10, height = 6, dpi = 300)

# -----------------------------
# Number of tools per omics type (bar)
# -----------------------------
p_count_omics <- df_for_plots %>%
  count(omic_type, name = "n") %>%
  ggplot(aes(x = fct_reorder(omic_type, n, .na_rm = TRUE), y = n, fill = omic_type)) +
  geom_col(show.legend = FALSE) +
  coord_flip() +
  labs(title = "Number of tools per omics type", x = NULL, y = "Tool count") +
  scale_fill_omics()

ggsave(file.path(outdir, "tools_per_omics.png"), p_count_omics, width = 6, height = 4, dpi = 300)

# -----------------------------
# Tool age vs total citations
# -----------------------------
p_age_citations <- df_tools_unique %>%
  filter(!is.na(publication_year), !is.na(total_citations)) %>%
  mutate(age = current_year - publication_year) %>%
  ggplot(aes(x = age, y = total_citations, color = omic_type)) +
  geom_jitter(alpha = 0.6, width = 0.2, size = 1.8) +
  geom_smooth(aes(group = 1), method = "lm", se = TRUE, color = "black", linetype = "dashed") +
  scale_y_continuous(trans = "log1p") +
  labs(title = "Tool age vs. total citations", subtitle = "Scatter plot with log-scaled citations", x = "Age (years since publication)", y = "Total citations (log1p)") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "none") +
  scale_color_omics()

ggsave(file.path(outdir, "age_vs_citations_scatter.png"), p_age_citations, width = 8, height = 6, dpi = 300)

# -----------------------------
# Tool type distribution by omics
# -----------------------------
tools_type <- df_for_plots %>%
  # normalize and deduplicate tool_type values so counts are consistent
  separate_rows(tool_type, sep = ",|;") %>%
  mutate(tool_type = if_else(is.na(tool_type) | trimws(tool_type) == "", NA_character_, trimws(tool_type))) %>%
  distinct(name, omic_type, tool_type) %>%
  filter(!is.na(tool_type)) %>%
  count(omic_type, tool_type) %>%
  group_by(tool_type) %>%
  mutate(total_by_tool = sum(n)) %>%
  ungroup()

p_tool_dist <- ggplot(tools_type, aes(x = fct_reorder(tool_type, total_by_tool), y = n, fill = omic_type)) +
  geom_col(position = position_dodge(width = 0.9)) +
  labs(title = "Tool Type Distribution by Omics Type", x = "Tool Type", y = "Count") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1), strip.text = element_text(size = 10)) +
  scale_fill_omics()

ggsave(file.path(outdir, "tool_type_distribution.png"), p_tool_dist, width = 8, height = 6, dpi = 300)

# ================================
# Technical elements
# ================================
# -----------------------------
# License distribution (pie)
# -----------------------------
if (exists("df_license")) {
  p_license <- ggplot(df_license, aes(x = "", y = pct, fill = license_class)) +
    geom_col(width = 1, color = "white") +
    coord_polar(theta = "y") +
    geom_text(aes(label = paste0(license_class, " (", scales::percent(pct), ")")),
              position = position_stack(vjust = 0.5), size = 3) +
    labs(title = "License Distribution") +
    theme_void() +
    theme(plot.title = element_text(hjust = 0.5)) +
    # use unnamed palette values so scale works even if factor levels don't perfectly match names
    scale_fill_manual(values = unname(license_palette))
  ggsave(file.path(outdir, "license_distribution.png"), p_license, width = 6, height = 6, dpi = 300)
}

# -----------------------------
# Combined Language + OS pie chart
# -----------------------------
lang_df_pie <- df_for_plots %>%
  separate_rows(language, sep = ",\\s*|;") %>%
  mutate(language = if_else(is.na(language) | language == "", "Other", language)) %>%
  count(language, sort = TRUE) %>%
  slice_max(order_by = n, n = 8) %>%
  mutate(category = "Language", label = language) %>%
  select(label, n, category)

os_df_pie <- df_for_plots %>%
  count(operating_system, sort = TRUE) %>%
  slice_max(order_by = n, n = 4) %>%
  mutate(category = "Operating System", label = operating_system) %>%
  select(label, n, category)

# TODO: Fix
combined_pie_df <- bind_rows(lang_df_pie, os_df_pie)
if (nrow(combined_pie_df) > 0) {
  p_combined_pie <- combined_pie_df %>%
    group_by(category) %>%
    mutate(pct = n / sum(n)) %>%
    ungroup() %>%
    ggplot(aes(x = "", y = n, fill = label)) +
    geom_col(width = 1, color = "white") +
    coord_polar(theta = "y") +
    facet_wrap(~category, ncol = 2) +
    geom_text(aes(label = scales::percent(pct)), position = position_stack(vjust = 0.5), size = 3) +
    labs(title = "Top Programming Languages and Operating Systems", fill = "Category") +
    theme_void() +
    theme(plot.title = element_text(hjust = 0.5)) +
    scale_fill_extra()
  ggsave(file.path(outdir, "combined_language_os_pie.png"), p_combined_pie, width = 12, height = 6, dpi = 300)
}

# -----------------------------
# Composite scoring of tools & Top 10 per omic
# -----------------------------
scored_tools <- df_for_plots %>%
  mutate(
    citation_score = safe_rescale(total_citations),
    publication_year_score = safe_rescale(publication_year),
    commit_score = safe_rescale(commit_year),
    stars_score = safe_rescale(stars),
    # Add a small maintenance proxy (sum of stars/forks/watchers scaled) to reduce bias
    maintenance_proxy = safe_rescale(replace_na(stars, 0) + replace_na(forks, 0) + replace_na(watchers, 0)),
    composite_score = rowMeans(cbind(citation_score, publication_year_score, commit_score, stars_score, maintenance_proxy), na.rm = TRUE)
  )

# Top 10 tools by composite score overall or by omic_type
top_by_score <- scored_tools %>%
  group_by(omic_type) %>%       # optional: remove if you want top 10 overall
  slice_max(order_by = composite_score, n = 10, with_ties = FALSE) %>%
  ungroup() %>%
  mutate(name = as.character(name))

# Plot using omic_type 
p_tool_comp <- ggplot(top_by_score, aes(x = fct_reorder(name, composite_score, .na_rm = TRUE),
                                        y = composite_score, fill = omic_type)) +
  geom_col(show.legend = FALSE) +
  coord_flip() +
  facet_wrap(~omic_type, scales = "free") +
  labs(title = "Top 10 Tools by Composite Score per Omics Type",
       x = "Tool Name", y = "Composite Score") +
    scale_fill_omics()

ggsave(file.path(outdir, "top_10_tools_composite.png"), p_tool_comp, width = 10, height = 8, dpi = 300)

# ================================
# Commit Year & Citations Plots
# ================================
# ----------------------------------------
# Last Commit Date vs Total Citations
# ----------------------------------------
if ("last_commit" %in% names(df_for_plots) && any(!is.na(df_for_plots$last_commit))) {
  df_commit_plot <- df_for_plots %>%
    mutate(last_commit_date = lubridate::as_date(last_commit)) %>%
    filter(!is.na(last_commit_date) & !is.na(total_citations))
  
  if (nrow(df_commit_plot) > 0) {
    p_commit_vs_cite <- ggplot(df_commit_plot, aes(x = last_commit_date, y = total_citations, color = omic_type)) +
      geom_point(alpha = 0.7) +
      scale_y_log10() +
      labs(
        title = "Last Commit Date vs Total Citations",
        x = "Last Commit Date", y = "Total Citations (log scale)"
      ) +
      # Use the named omics palette
      scale_color_omics() +
      theme_minimal()
    ggsave(file.path(outdir, "commit_vs_citations.png"), p_commit_vs_cite, width = 9, height = 6, dpi = 300)
  }
}

# -----------------------------
# Top functions by omics (top 10)
# -----------------------------
top_funcs_per_omics <- df_for_plots %>%
  filter(!is.na(Function)) %>%
  separate_rows(Function, sep = ",|;") %>%
  mutate(Function = str_squish(Function)) %>%
  distinct(name, omic_type, Function) %>%
  count(omic_type, Function, name = "n") %>%
  group_by(omic_type) %>%
  slice_max(n, n = 10) %>%
  ungroup() %>%
  group_by(omic_type) %>%
  mutate(Function = fct_reorder(Function, n)) %>%
  ungroup()

p_funcs_omics <- ggplot(top_funcs_per_omics, aes(x = Function, y = n, fill = omic_type)) +
  geom_col(show.legend = FALSE) +
  facet_wrap(~omic_type, scales = "free_y") +
  coord_flip() +
  labs(title = "Top functions by omics type (top 5 each)", x = NULL, y = "Count of tools") +
  scale_fill_omics()

ggsave(file.path(outdir, "functions_by_omics.png"), p_funcs_omics, width = 12, height = 8, dpi = 300)

# -----------------------------
# Functional coverage
# -----------------------------
func_by_omics <- df_for_plots %>%
  separate_rows(Function, sep = ",|;") %>%
  filter(!is.na(Function)) %>%
  mutate(Function = str_squish(Function)) %>%
  distinct(name, omic_type, Function) %>%
  count(omic_type, Function, name = "n") %>%
  group_by(omic_type) %>%
  mutate(frac = n / sum(n)) %>%
  ungroup()

overall_func <- df_for_plots %>%
  separate_rows(Function, sep = ",|;") %>%
  filter(!is.na(Function)) %>%
  mutate(Function = str_squish(Function)) %>%
  distinct(name, Function) %>%
  count(Function, name = "n") %>%
  mutate(overall_frac = n / sum(n)) %>%
  select(Function, overall_frac)

func_representation <- func_by_omics %>%
  left_join(overall_func, by = "Function") %>%
  mutate(enrichment = log2(frac / overall_frac),
         enrichment = replace_na(enrichment, 0),
         enrichment = ifelse(is.infinite(enrichment), 0, enrichment))

top_funcs <- overall_func %>% slice_max(order_by = overall_frac, n = 10) %>% pull(Function)

# Saturation of functional categories and topics (which over/under-represented)
func_by_omics <- df_function_expanded %>%
  # join to expanded omics: this can intentionally be many-to-many (functions x omics per tool)
  # explicitly declare the relationship to avoid unexpected join warnings in newer dplyr
  left_join(df_expanded_omics, by = "name", relationship = "many-to-many") %>%
  filter(!is.na(Function)) %>%
  distinct(name, omic_type, Function) %>%
  count(omic_type, Function) %>%
  group_by(omic_type) %>%
  mutate(frac = n / sum(n)) %>%
  ungroup()

overall_func <- df_function_expanded %>%
  filter(!is.na(Function)) %>%
  distinct(name, Function) %>%
  count(Function) %>%
  mutate(overall_frac = n / sum(n)) %>%
  select(Function, overall_frac)

func_representation <- func_by_omics %>%
  left_join(overall_func, by = "Function") %>%
  mutate(enrichment = frac / overall_frac) %>%
  arrange(desc(enrichment))

# Plot of functional categories across omics (similar to 2.2 but global)
# TODO: Fix 
func_counts_global <- df_function_expanded %>%
  filter(!is.na(Function)) %>%
  count(Function, sort = TRUE)
p_func_global <- func_counts_global %>%
  top_n(30, n) %>%
  ggplot(aes(x = fct_reorder(Function, n), y = n, fill = Function)) +
  geom_col(show.legend = FALSE) +
  coord_flip() +
  labs(title = "Top functional categories across all omics", x = "", y = "Count") +
  theme_minimal() +
  scale_fill_extra()
ggsave(glue("{outdir}/top_functions_global.png"), p_func_global, width = 8, height = 10, dpi = 300)

# ----------------------------
# Multi-functional & Multi-omic Tools
# ----------------------------
# TODO: add upset plot again

# ============================================
# Maintenance and Activity
# ============================================
classify_maintenance <- function(last_commit_char, commit_year = NA_integer_, ref_date = Sys.Date()) {
  # Coerce inputs to scalar safe values
  lc <- if (length(last_commit_char) == 0) NA_character_ else as.character(last_commit_char)[1]
  cy <- if (length(commit_year) == 0) NA_integer_ else suppressWarnings(as.integer(commit_year[1]))
  
  # Normalize empty strings to NA
  if (!is.na(lc) && nzchar(lc) == FALSE) lc <- NA_character_
  
  # If we don't have a last-commit string, try to classify from commit_year
  if (is.na(lc)) {
    if (!is.na(cy) && cy > 0) {
      if (cy >= (lubridate::year(ref_date) - 2)) return("Active")
      return("Inactive")
    }
    return("Unknown")
  }
  
  parsed <- NA
  parsed <- suppressWarnings(lubridate::ymd_hms(lc))
  if (is.na(parsed)) parsed <- suppressWarnings(lubridate::ymd(lc))
  if (is.na(parsed)) parsed <- suppressWarnings(lubridate::parse_date_time(lc, orders = c("ymd", "Y-m-d", "Y/m/d", "Y")))
  
  if (!is.na(parsed)) {
    days_since <- as.numeric(difftime(ref_date, parsed, units = "days"))
    if (!is.na(days_since)) {
      if (days_since <= 540) return("Active")
      if (days_since <= 1095) return("Stale")
      return("Dead")
    }
  }
  
  # Fallback to commit_year if parsing failed
  if (!is.na(cy) && cy > 0) {
    if (cy >= (lubridate::year(ref_date) - 2)) return("Active")
    return("Inactive")
  }
  
  return("Unknown")
}

df_for_maint <- df_for_plots %>%
  mutate(maintenance = purrr::pmap_chr(list(last_commit, commit_year), classify_maintenance)) %>%
  mutate(maintenance = if_else(is.na(maintenance) | trimws(as.character(maintenance)) == "", "Unknown", as.character(maintenance)))

allowed_statuses <- names(maintenance_palette)
normalize_maintenance <- function(x) {
  x <- as.character(x)
  x <- stringr::str_trim(x)
  x_lower <- tolower(x)
  dplyr::case_when(
    x_lower %in% c("active", "a", "recent", "maintained") ~ "Active",
    x_lower %in% c("inactive", "archived", "unmaintained", "archived/inactive") ~ "Inactive",
    x_lower %in% c("stale", "outdated") ~ "Stale",
    x_lower %in% c("dead", "abandoned") ~ "Dead",
    x_lower %in% c("unknown", "na", "n/a", "") ~ "Unknown",
    TRUE ~ x
  )
}

df_for_maint <- df_for_maint %>%
  mutate(maintenance = normalize_maintenance(maintenance),
         maintenance = ifelse(maintenance %in% allowed_statuses, maintenance, "Unknown"),
         maintenance = factor(maintenance, levels = allowed_statuses))

status_counts <- df_for_maint %>% count(maintenance) %>%
  tidyr::complete(maintenance = factor(allowed_statuses, levels = allowed_statuses), fill = list(n = 0))
message("Maintenance status counts (df_for_maint):")
print(status_counts)
message("Maintenance palette values:")
print(maintenance_palette)

# Aggregate counts per tool_type x maintenance (across omic types), then compute prop
maintenance_summary <- df_for_maint %>%
  separate_rows(tool_type, sep = ",|;") %>%
  distinct(name, tool_type, maintenance) %>%
  mutate(tool_type = coalesce(tool_type, "Unknown")) %>%
  count(tool_type, maintenance, name = "n") %>%
  group_by(tool_type) %>%
  mutate(prop = n / sum(n)) %>%
  ungroup()

## Compute maintenance status using last_commit from the GitHub-augmented table
tool_type_totals <- df_for_maint %>%
  separate_rows(tool_type, sep = ",|;") %>%
  distinct(name, tool_type) %>%
  filter(!is.na(tool_type) & trimws(tool_type) != "") %>%
  count(tool_type, name = "total_by_tool")

# Raw count bar plot (dodge) — compute counts per (omic_type, tool_type, maintenance) and plot
tool_status_count <- df_for_maint %>%
  separate_rows(tool_type, sep = ",|;") %>%
  distinct(name, omic_type, tool_type, maintenance) %>%
  mutate(tool_type = coalesce(tool_type, "Unknown")) %>%
  count(omic_type, tool_type, maintenance, name = "n") %>%
  left_join(tool_type_totals, by = "tool_type") %>%
  mutate(total_by_tool = replace_na(total_by_tool, 0)) %>%
  {
    df <- .
    # determine top 5 tool types by total_by_tool
    top_tool_types <- tool_type_totals %>% arrange(desc(total_by_tool)) %>% slice_head(n = 5) %>% pull(tool_type)
    # keep only the top 10 for plotting
    df2 <- df %>% filter(tool_type %in% top_tool_types)
    # order factor levels by descending total_by_tool so the largest appears first
    ordered_levels <- tool_type_totals %>% filter(tool_type %in% top_tool_types) %>% arrange(desc(total_by_tool)) %>% pull(tool_type)
    df2 %>% mutate(tool_type = factor(tool_type, levels = ordered_levels))
  }

p_tool_status_count <- ggplot(tool_status_count,
          aes(x = tool_type, y = n, fill = maintenance)) +
  geom_col() +
  facet_wrap(~omic_type, scales = "free_y") +
  coord_flip() +
  # place counts centered inside each stacked segment
  geom_text(aes(label = n), position = position_stack(vjust = 0.5), size = 3, color = "white") +
  labs(title = "Tool Counts by Status and Tool Type (per Omic Type)",
       x = "Tool Type", y = "Count", fill = "Status") +
  theme(axis.text.y = element_text(size = 8),
        strip.text = element_text(size = 10)) +
  scale_fill_manual(values = maintenance_palette, na.value = maintenance_palette[["Unknown"]])

safe_plot(save_plot_multi(glue("{outdir}/tool_type_status"),
          p_tool_status_count, width = 10, height = 8, dpi = 300))

# -----------------------------
# Adoption Quadrants
# -----------------------------
adoption_df <- df_for_maint %>%
  distinct(name, omic_type, maintenance, total_citations, stars, forks, watchers) %>%
  # join canonical per-tool numeric metrics as fallback
  left_join(df_tools_unique %>% select(name, total_citations_tool = total_citations, stars_tool = stars, forks_tool = forks, watchers_tool = watchers), by = "name") %>%
  mutate(
    total_citations = coalesce(as.numeric(total_citations), as.numeric(total_citations_tool)),
    stars = coalesce(as.numeric(stars), as.numeric(stars_tool)),
    forks = coalesce(as.numeric(forks), as.numeric(forks_tool)),
    watchers = coalesce(as.numeric(watchers), as.numeric(watchers_tool))
  ) %>%
  mutate(
    citations_log = if_else(is.na(total_citations), NA_real_, log1p(total_citations)),
    stars_log = if_else(is.na(stars), NA_real_, log1p(stars)),
    forks_log = if_else(is.na(forks), NA_real_, log1p(forks)),
    watchers_log = if_else(is.na(watchers), NA_real_, log1p(watchers)),
    # Use the average (mean) of stars/forks/watchers logs as a maintenance metric.
    # Treat missing numeric indicators as zero so absence of one metric doesn't drop the row.
    maintenance_metric = rowMeans(cbind(replace_na(stars_log, 0), replace_na(forks_log, 0), replace_na(watchers_log, 0)), na.rm = TRUE)
  )
adoption_df$maintenance_metric[is.infinite(adoption_df$maintenance_metric)] <- NA_real_

# Plot adoption quadrants
plot_adoption_quadrant <- function(omics_filter, df = adoption_df, top_n_labels = 12) {
  sub <- df %>% filter(omic_type == omics_filter)
  if(nrow(sub) == 0) return(NULL)

  # Normalize maintenance factor and drop Unknown category for plotting if requested
  # Create a dedicated plotting column for maintenance to avoid mutating original data
  sub <- sub %>% mutate(maintenance_plot = as.character(maintenance))
  # Replace NA or empty strings with 'Unknown' and map unexpected values to 'Unknown'
  sub$maintenance_plot[is.na(sub$maintenance_plot) | trimws(sub$maintenance_plot) == ""] <- "Unknown"
  sub$maintenance_plot[!sub$maintenance_plot %in% names(maintenance_palette)] <- "Unknown"

  sub$maintenance_plot <- factor(sub$maintenance_plot, levels = names(maintenance_palette))

  # Print maintenance composition for debugging (use maintenance_plot)
  maint_counts <- sub %>% count(maintenance_plot) %>% arrange(desc(n))
  message(glue("{omics_filter}: maintenance levels (total {nrow(sub)}): ", paste0(as.character(maint_counts$maintenance_plot), "=", maint_counts$n, collapse=", ")))

  # Keep only rows with finite numeric metrics for plotting
  sub_fin <- sub %>% filter(is.finite(citations_log) & is.finite(maintenance_metric))
  # Use maintenance_plot for counts among finite rows
  maint_counts_fin <- sub_fin %>% count(maintenance_plot) %>% arrange(desc(n))
  message(glue("{omics_filter}: maintenance levels among finite rows (total {nrow(sub_fin)}): ", paste0(as.character(maint_counts_fin$maintenance_plot), "=", maint_counts_fin$n, collapse=", ")))
  if (nrow(sub_fin) < 3) {
    message(glue("Skipping adoption quadrant for {omics_filter}: insufficient numeric metrics (n = {nrow(sub_fin)})."))
    return(NULL)
  }

  x_med <- median(sub_fin$citations_log, na.rm = TRUE)
  y_med <- median(sub_fin$maintenance_metric, na.rm = TRUE)
  if (is.na(x_med) || is.na(y_med)) {
    message(glue("Skipping adoption quadrant for {omics_filter}: median(s) are NA."))
    return(NULL)
  }

  # Top-right quadrant labels
  top_tools <- sub_fin %>%
    filter(citations_log > x_med, maintenance_metric > y_med) %>%
    slice_max(order_by = (citations_log + maintenance_metric), n = top_n_labels)

  ggplot(sub_fin, aes(x = citations_log, y = maintenance_metric, color = maintenance_plot)) +
    geom_point(alpha = 0.7, size = 2) +
    geom_vline(xintercept = x_med, linetype = "dashed", color = "gray40") +
    geom_hline(yintercept = y_med, linetype = "dashed", color = "gray40") +
  ggrepel::geom_text_repel(data = top_tools, aes(label = name),
               size = 3, max.overlaps = Inf, box.padding = 0.4,
               point.padding = 0.2, segment.color = "grey60", seed = 42) +
  scale_color_manual(values = maintenance_palette, na.value = maintenance_palette[["Unknown"]]) +
    labs(title = glue("{omics_filter}: Adoption Quadrant (Citations vs Maintenance Activity)"),
         x = "Citations (log1p)", y = "Maintenance metric (log1p of stars/forks)",
         color = "Maintenance") +
    theme_bw() +
    theme(plot.title = element_text(hjust = 0.5, face = "bold"),
          legend.position = "bottom")
}

omics_list_plot <- unique(na.omit(adoption_df$omic_type))
adoption_plots <- map(omics_list_plot, plot_adoption_quadrant) %>% compact()

p_adoption_combined <- patchwork::wrap_plots(adoption_plots, ncol = 2)
ggsave(glue("{outdir}/adoption_quadrants_all_omics.png"), p_adoption_combined, width = 14, height = 10, dpi = 300)

