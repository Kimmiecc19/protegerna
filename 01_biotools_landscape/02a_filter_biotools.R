# bio.tools curation audit and candidate-set construction
# Rscript 02a_filter_biotools.R [--omic=proteomics] [--analysis-date=YYYY-MM-DD]
#                                      [--check-urls] [--url-timeout=5] [--url-retries=1]
#                                      [--url-workers=20]
#                                      [--install-packages] [--config=03_helpers/visualize_config.yaml]
#                                      [--input-tag=YYYYMMDD] [--citation-source=Dimensions]
# Input tag defaults to today's date; explicitly name the completed fetch tag, e.g.
# Rscript 02a_filter_biotools.R --omic=all --analysis-date=2026-09-30 --input-tag=sept2026 --check-urls
# The shared publication policy and configuration checks live in
# 03_helpers/analysis_helpers.R
# Settings are in 03_helpers/visualize_config.yaml.
# Inputs: results/01ab_results_fetch_biotools/results_fetch_biotools_final/ and data/02a_data_filter_biotools/.
# Outputs: inputs.filter_results_dir in the config (results/02a_results_filter_biotools/).
# NOTE: scope_reason = positive omics evidence was spelled incorrectly in the results as "posiative". This was corrected in the scripts but not in the result files.

main <- function() {

  # 1. Packages and command-line options ----------------------------------------
  # The script requires the following packages; if any are missing, rerun with --install-packages to install them.

  pkgs <- c("dplyr", "curl", "jsonlite", "purrr", "readr", "stringr", "tidyr", "janitor", "yaml")
  args <- commandArgs(trailingOnly = TRUE)
  missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing) && "--install-packages" %in% args) {
    install.packages(missing, repos = "https://cloud.r-project.org")
    missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  }
  if (length(missing)) stop("Missing required R packages: ", paste(missing, collapse = ", "),
    ". Rerun once with --install-packages.")
  suppressPackageStartupMessages(invisible(lapply(pkgs, library, character.only = TRUE)))
  options(stringsAsFactors = FALSE, timeout = 120)

  arg <- function(x, default) {
    hit <- grep(paste0("^", x, "="), args, value = TRUE)
    if (length(hit)) sub(paste0("^", x, "="), "", hit[1]) else default
  }

  # 2. Resolve project paths and analysis settings ------------------------------
  # The script path is used to locate the project root and the shared analysis_helpers.R script.

  file_arg <- grep("^--file=", commandArgs(), value = TRUE)
  if (!length(file_arg)) stop("Run with Rscript: Rscript 02a_filter_biotools.R [options]")
  script_path <- normalizePath(sub("^--file=", "", file_arg[1]), mustWork = TRUE)
  filter_dir <- dirname(script_path)
  analysis_helper_path <- file.path(filter_dir, "03_helpers", "analysis_helpers.R")
  source(analysis_helper_path, local = TRUE)
  config_file <- normalizePath(arg("--config", file.path(dirname(analysis_helper_path), "visualize_config.yaml")), mustWork = TRUE)
  config <- validate_visualize_config(yaml::read_yaml(config_file))
  input_tag <- arg("--input-tag", format(Sys.Date(), "%Y%m%d"))
  citation_source_expected <- arg("--citation-source", config$citations$source)
  selected_omic <- tolower(arg("--omic", "all"))
  analysis_date <- as.Date(arg("--analysis-date", config$analysis_date))
  check_urls <- "--check-urls" %in% args && !"--skip-url-check" %in% args
  url_timeout_seconds <- suppressWarnings(as.numeric(arg("--url-timeout", "5")))
  url_retries <- suppressWarnings(as.integer(arg("--url-retries", "1")))
  # Number of URLs checked at the same time (at most 4 per host).
  url_workers <- suppressWarnings(as.integer(arg("--url-workers", "20")))
  if (is.na(url_timeout_seconds) || url_timeout_seconds <= 0) stop("--url-timeout must be a positive number")
  if (is.na(url_retries) || url_retries < 1L) stop("--url-retries must be a positive integer")
  if (is.na(url_workers) || url_workers < 1L) stop("--url-workers must be a positive integer")
  if (!check_urls) message("Live URL audit disabled (default). Use --check-urls for the separate network-dependent audit.")

  # 3. Configure domain inputs and output paths ---------------------------------
  # The fetch results are in results/01ab_results_fetch_biotools/results_fetch_biotools_final; the filter results are
  # written to inputs.filter_results_dir (results/02a_results_filter_biotools).

  fetch_dir <- file.path(filter_dir, "results", "01ab_results_fetch_biotools", "results_fetch_biotools_final")
  filter_data_dir <- file.path(filter_dir, "data", "02a_data_filter_biotools")
  output_dir <- resolve_config_path(config$inputs$filter_results_dir, config_file)
  exclusion_file <- file.path(filter_data_dir, "general_exclusion_terms_2026.txt")
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  domain_config <- tibble::tribble(
    ~omic,              ~keep,                              ~stem,
    "genomics",         "genomic_keep_topics.txt",          "genomic",
    "transcriptomics",  "transcriptomics_keep_topics.txt",  "transcriptomic",
    "proteomics",       "proteomic_keep_topics.txt",        "proteomic",
    "multiomics",       "multiomics_keep_topics.txt",       "multiomic"
  ) |>
    mutate(input = file.path(fetch_dir, paste0(omic, "_fetch_biotools_", input_tag, ".tsv")),
      function_input = paste0(input, ".functions.tsv"),
      keep = file.path(filter_data_dir, keep))
  if (selected_omic != "all") {
    if (!selected_omic %in% domain_config$omic) stop("Invalid --omic value")
    domain_config <- filter(domain_config, omic == selected_omic)
  }

  # 4. Text, identifier, and table-export helpers -------------------------------
  # The functions below are used to read and process the fetch results, function annotations, and publication metadata.

  read_terms <- function(path) {
    x <- trimws(readLines(path, warn = FALSE, encoding = "UTF-8"))
    x[nzchar(x) & !startsWith(x, "#")]
  }
  # Whole-word, literal (\Q...\E) match of any listed terms.
  escape_regex <- function(x) paste0("\\Q", gsub("\\E", "\\E\\\\E\\Q", x, fixed = TRUE), "\\E")
  term_regex <- function(x) if (length(x)) paste0("(?<![[:alnum:]_])(?:", paste(escape_regex(x), collapse = "|"),
    ")(?![[:alnum:]_])") else "(?!)"
  has_term <- function(x, pattern) str_detect(x, regex(pattern, ignore_case = TRUE))
  earliest_year <- function(x) map_dbl(str_extract_all(coalesce(as.character(x), ""), "\\b(?:19|20)\\d{2}\\b"), ~ {
    y <- suppressWarnings(as.numeric(.x))
    if (!length(y) || all(is.na(y))) NA_real_ else min(y, na.rm = TRUE)
  })
  is_missing_text <- function(x) {
    x <- str_to_lower(str_trim(as.character(x)))
    is.na(x) | !nzchar(x) | x %in% c("none", "null", "na", "n/a")
  }
  is_blank <- function(x) is.na(x) | !nzchar(str_trim(x))
  add_missing <- function(x, cols, value = NA_character_) {
    for (nm in setdiff(cols, names(x))) x[[nm]] <- value
    x
  }
  # Fetch tables written with Title Case headers ("EDAM Operation URIs") become
  # *_ur_is after janitor::clean_names(); restore the *_uris spelling.
  normalize_uri_column_names <- function(x) {
    for (old in grep("_ur_is$", names(x), value = TRUE)) {
      new <- sub("_ur_is$", "_uris", old)
      if (new %in% names(x)) {
        x[[new]] <- coalesce(as.character(x[[new]]), as.character(x[[old]]))
        x[[old]] <- NULL
      } else names(x)[names(x) == old] <- new
    }
    x
  }
  read_fetch_table <- function(path) {
    read_tsv(path, show_col_types = FALSE, progress = FALSE) |> clean_names() |> normalize_uri_column_names()
  }
  safe_md5 <- function(path) if (file.exists(path)) unname(tools::md5sum(path)) else NA_character_
  # TSV exports flatten control whitespace; RDS retains the original text.
  write_safe_tsv <- function(x, path) {
    x |> mutate(across(where(is.character), ~ str_squish(str_replace_all(.x, "[\\t\\r\\n]+", " ")))) |> write_tsv(path, na = "")
  }
  extract_urls <- function(x) unique(str_remove(str_trim(str_extract_all(coalesce(as.character(x), ""), "https?://[^,;[:space:]]+")[[1]]),
    "[),.;]+$"))

  # 5. URL availability audit -----------------------------------------------------
  # The URL audit is performed on the homepage and documentation URLs of each tool, to check whether they are accessible. 
  # The audit uses concurrent HTTP requests with a timeout and retries, and caches results to avoid redundant checks.
  # The audit is network-bound, so it is run (1) only on citation-eligible
  # records, i.e. after every metadata gate, 
  # (2) concurrently with curl, and 
  # (3) with a results cache on disk, so an interrupted run resumes where
  # it stopped and a rerun on the same analysis date does not
  # re-query URLs that were already checked.

  url_cache_file <- file.path(output_dir, paste0("url_audit_cache_", format(analysis_date, "%Y%m%d"), ".csv"))
  url_cache_cols <- c("url", "accessible", "status_code", "final_url", "method", "failure_reason", "checked_at_utc")
  url_audit_cache <- if (file.exists(url_cache_file)) {
    read_csv(url_cache_file,
      col_types = cols(accessible = col_logical(), status_code = col_integer(), .default = col_character()),
      progress = FALSE) |> distinct(url, .keep_all = TRUE)
  } else tibble(url = character(), accessible = logical(), status_code = integer(), final_url = character(),
    method = character(), failure_reason = character(), checked_at_utc = character())
  if (nrow(url_audit_cache)) message("URL cache: ", nrow(url_audit_cache), " URLs already checked (",
    basename(url_cache_file), ")")

  # One concurrent pass over `urls` with a single method. Returns one row per URL.
  url_pass <- function(urls, method) {
    out <- vector("list", length(urls))
    names(out) <- urls
    # Newer curl versions pass a condition object (e.g. curl_error_couldnt_resolve_host)
    # to the fail callback rather than a string; always store plain text.
    as_reason <- function(msg) if (inherits(msg, "condition")) conditionMessage(msg) else paste(as.character(msg), collapse = " ")
    failed_row <- function(uu, msg) tibble(url = uu, accessible = FALSE, status_code = NA_integer_,
      final_url = NA_character_, method = method, failure_reason = as_reason(msg))
    pool <- curl::new_pool(total_con = url_workers, host_con = 4L)
    add_request <- function(uu) {
      h <- curl::new_handle(followlocation = TRUE, timeout = url_timeout_seconds,
        connecttimeout = url_timeout_seconds, useragent = "bio.tools-curation-audit/1.0")
      if (method == "HEAD") curl::handle_setopt(h, nobody = TRUE) else curl::handle_setopt(h, range = "0-2047")
      curl::curl_fetch_multi(uu, handle = h, pool = pool,
        done = function(r) {
          code <- as.integer(r$status_code)
          out[[uu]] <<- tibble(url = uu, accessible = code >= 200L & code < 400L, status_code = code,
            final_url = as.character(r$url), method = method,
            failure_reason = if (code < 400L) "accessible" else paste0("HTTP ", code))
        },
        fail = function(msg) out[[uu]] <<- failed_row(uu, msg))
    }
    # A malformed URL can fail when the request is created; record it and move on.
    for (u in urls) tryCatch(add_request(u), error = function(e) out[[u]] <<- failed_row(u, e))
    curl::multi_run(pool = pool)
    # Any URL that never reported back is recorded as a failure, not silently dropped.
    for (u in urls[vapply(out, is.null, logical(1))]) out[[u]] <- failed_row(u, "no response from curl")
    bind_rows(out)
  }

  # Check every URL not already in the cache: HEAD first, then GET (first 2 kB)
  # for URLs whose HEAD failed (some servers reject HEAD), with retries for the
  # remainder. Results are appended to the cache file after every batch.
  audit_urls <- function(urls, label, batch_size = 200L) {
    todo <- setdiff(unique(urls[!is.na(urls) & nzchar(urls)]), url_audit_cache$url)
    message(label, ": ", length(unique(urls)), " distinct URLs; ", length(todo), " to check (",
      url_workers, " concurrent, timeout ", url_timeout_seconds, "s)")
    started <- Sys.time()
    batches <- split(todo, ceiling(seq_along(todo) / batch_size))
    for (b in seq_along(batches)) {
      res <- url_pass(batches[[b]], "HEAD")
      for (attempt in seq_len(url_retries)) {
        failed <- res$url[!res$accessible]
        if (!length(failed)) break
        if (attempt > 1L) Sys.sleep(min(2^(attempt - 2), 4))
        retry <- url_pass(failed, "GET")
        res <- bind_rows(filter(res, !url %in% retry$url), retry)
      }
      res <- mutate(res, checked_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE))
      url_audit_cache <<- bind_rows(url_audit_cache, res) |> distinct(url, .keep_all = TRUE)
      write_csv(url_audit_cache[url_cache_cols], url_cache_file, na = "")
      message(sprintf("[%s] URL batch %d/%d done; %d/%d URLs; elapsed %.1f min", label, b, length(batches),
        min(b * batch_size, length(todo)), length(todo),
        as.numeric(difftime(Sys.time(), started, units = "mins"))))
    }
    invisible(url_audit_cache)
  }

  # Summarise the cached results for one homepage/documentation pair.
  audit_fields <- function(homepage, documentation) {
    hu <- extract_urls(homepage)
    du <- extract_urls(documentation)
    h <- filter(url_audit_cache, url %in% hu)
    d <- filter(url_audit_cache, url %in% du)
    hok <- nrow(h) > 0 && any(h$accessible)
    dok <- nrow(d) > 0 && any(d$accessible)
    status <- function(x, present) if (!present) "missing" else
      paste0(x$url, " [", coalesce(as.character(x$status_code), x$failure_reason), "]", collapse = "; ")
    tibble(homepage_accessible = hok, documentation_accessible = dok, any_url_accessible = hok | dok,
      homepage_status = status(h, length(hu) > 0), documentation_status = status(d, length(du) > 0),
      url_failure_reason = if (hok | dok) NA_character_ else
        paste(unique(na.omit(filter(url_audit_cache, url %in% c(hu, du))$failure_reason)), collapse = "; "))
  }

  # 6. Audit and filter one omics population ------------------------------------
  # The audit_publications() function checks the publication metadata for each tool, 
  # ensuring that the citation counts and publication identifiers are consistent with the fetched data. 
  # It reads the fetch table, validates the schema, and extracts relevant information from the publication metadata JSON. 
  # The function also checks for missing DOIs and other identifiers, and compares reported citation totals with audited totals to ensure consistency.

  audit_publications <- function(input) {
    tools_raw <- read_fetch_table(input) |>
      add_missing(c("biotools_id", "retrieval_query", "retrieval_timestamp_utc")) |>
      add_missing(c("function_count", "function_metadata_status", "edam_operation_terms", "edam_operation_uris",
        "function_metadata_json"), NA)
    validate_publication_schema(tools_raw, citation_source_expected)
    if (!"publication_metadata_json" %in% names(tools_raw)) stop("Publication Metadata JSON is required for the registry/enrichment audit.")
    # Read original registry evidence separately from externally enriched fields.
    evidence <- map_dfr(tools_raw$publication_metadata_json, function(text) {
      pubs <- jsonlite::fromJSON(text, simplifyVector = FALSE)
      # Validate fetch aggregation without repairing or re-deduplicating it here.
      if (length(pubs) && any(!vapply(pubs, function(publication) all(c("citation_total_contribution", "publication_group") %in% names(publication)), logical(1))))
        stop("Publication audit lacks duplicate/contribution fields; rerun the updated fetcher.")
      contributions <- unlist(lapply(pubs, function(publication) publication$citation_total_contribution))
      groups <- unique(unlist(lapply(pubs, function(publication) publication$publication_group)))
      any_id <- function(key, original = FALSE) any(vapply(pubs, function(publication) {
        value <- (if (original) publication$registry_publication else publication)[[key]]
        !is.null(value) && length(value) == 1L && !is_missing_text(value)
      }, logical(1)))
      registry_dates <- vapply(pubs, function(publication) {
        registry_metadata <- publication$registry_publication$metadata
        paste(unlist(registry_metadata$date %||% registry_metadata$publicationYear), collapse = "; ")
      }, character(1))
      tibble(audited_citation_total = if (length(contributions)) sum(contributions) else NA_real_,
        audited_publication_entries = length(pubs), audited_publication_groups = length(groups),
        publication_traceable_id = any_id("doi") | any_id("pmid") | any_id("pmcid"),
        enriched_has_doi = any_id("doi"), registry_has_doi = any_id("doi", TRUE),
        registry_publication_traceable = any_id("doi", TRUE) | any_id("pmid", TRUE) | any_id("pmcid", TRUE),
        registry_publication_year = earliest_year(paste(registry_dates, collapse = "; ")))
    })
    tools_raw <- bind_cols(tools_raw, evidence)
    reported <- suppressWarnings(as.numeric(tools_raw$total_citations))
    equal_total <- (is.na(reported) & is.na(tools_raw$audited_citation_total)) |
      (!is.na(reported) & !is.na(tools_raw$audited_citation_total) & reported == tools_raw$audited_citation_total)
    if (any(!equal_total) || any(tools_raw$publication_count != tools_raw$audited_publication_entries) ||
      any(tools_raw$distinct_publication_count != tools_raw$audited_publication_groups))
      stop("Fetch totals or publication counts disagree with the publication audit; inspect the source output.")
    tools_raw
  }

  load_function_annotations <- function(function_input) {
    function_records <- read_fetch_table(function_input) |>
      add_missing(c("biotools_id", "operation_term", "operation_uri", "input_data_terms", "input_data_uris",
        "input_format_terms", "input_format_uris", "output_data_terms", "output_data_uris",
        "output_format_terms", "output_format_uris"))
    # Function annotations provide scope evidence; they do not define new categories.
    function_scope <- function_records |>
      mutate(across(c(operation_term, input_data_terms, input_format_terms, output_data_terms, output_format_terms), ~ coalesce(as.character(.x), "")),
        function_scope_row = str_c(operation_term, input_data_terms, input_format_terms, output_data_terms,
          output_format_terms, sep = "; ")) |>
      summarise(function_scope_text = str_squish(paste(function_scope_row, collapse = "; ")), .by = biotools_id)
    list(records = function_records, scope = function_scope)
  }

  # Derive scope classification and accessibility flags for each tool, based on the function annotations, omics layer evidence, and exclusion terms.
  # The function returns a data frame with the original tool records and additional columns for scope classification, reason, and various accessibility flags.

  derive_scope_access_flags <- function(tools_raw, function_scope, omic, keep_re, exclude_re) {
    tools_raw |> left_join(function_scope, by = "biotools_id") |> mutate(
      function_scope_text = coalesce(function_scope_text, ""),
      source_row = row_number(),
      omic_type = str_to_title(omic),
      canonical_record_id = case_when(
        !is_blank(biotools_id) ~ paste0("biotools:", str_to_lower(str_trim(biotools_id))),
        !is_blank(name) & !is_blank(publication_doi) ~ paste0("name_doi:", str_to_lower(str_squish(name)), "|", str_to_lower(str_squish(publication_doi))),
        TRUE ~ paste0("unresolved:", omic, ":", source_row)),
      publication_year = earliest_year(publication_date),
      total_citations = suppressWarnings(as.numeric(total_citations)),
      flag_missing_doi = !enriched_has_doi,
      flag_missing_publication_identifier = !publication_traceable_id,
      flag_registry_missing_doi = !registry_has_doi,
      flag_registry_missing_publication_year = is.na(registry_publication_year),
      flag_partial_citations = citation_coverage == "partial",
      flag_publication_conflict = is.na(publication_conflict_groups) | publication_conflict_groups > 0,
      flag_missing_publication_year = is.na(publication_year),
      flag_missing_citations = is.na(total_citations),
      flag_missing_homepage = is_missing_text(homepage),
      flag_missing_documentation = is_missing_text(documentation),
      flag_missing_license = is_missing_text(license),
      flag_missing_accessibility = is_missing_text(accessibility),
      flag_missing_operating_system = is_missing_text(operating_system),
      flag_missing_language = is_missing_text(language),
      flag_missing_updated = is_missing_text(updated),
      flag_missing_function_metadata = is.na(function_count) | function_count == 0 | is.na(function_metadata_status) | function_metadata_status == "Function metadata missing",
      flag_function_without_operation = !flag_missing_function_metadata & is_blank(edam_operation_uris),
      scope_search_text = str_c(coalesce(topic, ""), coalesce(name, ""), coalesce(description, ""), function_scope_text, sep = "; "),
      scope_evidence_topic = has_term(coalesce(topic, ""), keep_re),
      scope_evidence_name_description = has_term(str_c(coalesce(name, ""), coalesce(description, ""), sep = "; "), keep_re),
      scope_evidence_function = has_term(function_scope_text, keep_re),
      scope_layer_genomics = has_term(scope_search_text, "genomics|genome sequencing|variant calling|epigenomics"),
      scope_layer_transcriptomics = has_term(scope_search_text, "transcriptomics|rna-seq|rna sequencing|gene expression profiling"),
      scope_layer_proteomics = has_term(scope_search_text, "proteomics|mass spectrometry|protein identification"),
      scope_layer_metabolomics = has_term(scope_search_text, "metabolomics|metabolic profiling|lipidomics"),
      scope_omics_layer_count = as.integer(scope_layer_genomics + scope_layer_transcriptomics +
        scope_layer_proteomics + scope_layer_metabolomics),
      scope_evidence_multilayer = omic == "multiomics" & scope_omics_layer_count >= 2L,
      scope_evidence_exclusion = has_term(str_c(coalesce(topic, ""), coalesce(name, ""), coalesce(description, ""), sep = "; "), exclude_re),
      scope_positive_evidence_count = as.integer(scope_evidence_topic + scope_evidence_name_description +
        scope_evidence_function + scope_evidence_multilayer),
      scope_positive_sources = str_remove(str_c(if_else(scope_evidence_topic, "topic; ", ""),
        if_else(scope_evidence_name_description, "name/description; ", ""),
        if_else(scope_evidence_function, "function metadata; ", ""),
        if_else(scope_evidence_multilayer, "at least two omics layers; ", "")), "; $"),
      # Positive evidence takes precedence over exclusion terms.
      scope_classification = case_when(
        scope_positive_evidence_count > 0L ~ "Include",
        scope_evidence_exclusion ~ "Out of scope",
        TRUE ~ "Review"
      ),
      scope_reason = case_when(
        scope_positive_evidence_count > 0L ~ str_c("Positive omics evidence: ", scope_positive_sources),
        scope_evidence_exclusion ~ "Exclusion evidence with no positive omics evidence",
        TRUE ~ "No decisive positive or exclusion evidence"
      ),
      flag_scope_review = scope_classification == "Review",
      flag_scope_out_of_scope = scope_classification == "Out of scope",
      flag_topic_exclusion = flag_scope_out_of_scope,
      # Web/desktop-only records: every declared tool type is a web or desktop application.
      flag_web_or_desktop = map_lgl(tool_type, function(x) {
        if (is_blank(x)) return(FALSE)
        types <- str_to_lower(str_trim(str_split(x, "[,;]")[[1]]))
        types <- types[nzchar(types)]
        length(types) > 0L && all(types %in% c("web application", "desktop application"))
      }),
      flag_proprietary = has_term(coalesce(license, ""), "proprietary|commercial"),
      flag_restricted_access = has_term(coalesce(accessibility, ""), "restricted|registration required|commercial"),
      flag_open_access = has_term(str_trim(coalesce(accessibility, "")), "^open access"),
      access_license_status = case_when(
        flag_restricted_access | flag_proprietary ~ "Recorded restriction or proprietary licence",
        flag_open_access & !flag_missing_license ~ "Recorded open access and non-proprietary licence",
        TRUE ~ "No restriction recorded; access/licence evidence incomplete"
      ),
      access_license_eligible = !flag_restricted_access & !flag_proprietary,
      citation_filter_decision = citation_decision(publication_year, total_citations, citation_coverage, publication_conflict_groups, config$candidate_filter),
      flag_citation_review = citation_filter_decision == "Review",
      passes_citation_filter = citation_filter_decision == "Pass"
    ) |> mutate(duplicate_group_size = n(), flag_duplicate_record = row_number() > 1L, .by = canonical_record_id) |>
      # Passes every metadata gate; only these records reach the (slow, network-bound) URL audit.
      mutate(url_check_eligible = !flag_duplicate_record & scope_classification == "Include" & access_license_eligible &
        !flag_web_or_desktop & !flag_missing_publication_identifier & passes_citation_filter)
  }

  audit_population_urls <- function(tools_audited, omic) {
    not_checked <- function(x, reason) mutate(x, homepage_accessible = NA, documentation_accessible = NA,
      any_url_accessible = NA, homepage_status = reason, documentation_status = reason, url_failure_reason = NA_character_)
    url_pairs <- tools_audited |> filter(url_check_eligible) |> distinct(homepage, documentation)
    url_keys <- if (!check_urls || !nrow(url_pairs)) not_checked(url_pairs, "not checked") else {
      audit_urls(unlist(map2(url_pairs$homepage, url_pairs$documentation, ~ c(extract_urls(.x), extract_urls(.y)))), omic)
      mutate(url_pairs, audit = map2(homepage, documentation, audit_fields)) |> unnest(audit)
    }
    current_year <- as.integer(format(analysis_date, "%Y"))
    bind_rows(
      tools_audited |> filter(url_check_eligible) |> left_join(url_keys, by = c("homepage", "documentation")),
      tools_audited |> filter(!url_check_eligible) |> not_checked("not checked (failed an earlier gate)")
    ) |> arrange(source_row) |> mutate(
      flag_url_unresolved = if (!check_urls) NA else if_else(url_check_eligible, !any_url_accessible, NA),
      registry_update_year = suppressWarnings(as.integer(updated)),
      years_since_registry_update = if_else(!is.na(registry_update_year), pmax(0, current_year - registry_update_year), NA_real_),
      registry_update_age_group = factor(case_when(is.na(years_since_registry_update) ~ "Update year missing",
        years_since_registry_update <= 1 ~ "0-1 years",
        years_since_registry_update <= 3 ~ "2-3 years", years_since_registry_update <= 5 ~ "4-5 years", TRUE ~ ">5 years"),
        levels = c("0-1 years", "2-3 years", "4-5 years", ">5 years", "Update year missing")),
      # Shares of present metadata fields; publication evidence differs between scores.
      enriched_metadata_completeness_score = rowMeans(cbind(!flag_missing_doi, !flag_missing_publication_year,
        !flag_missing_homepage, !flag_missing_documentation, !flag_missing_license, !flag_missing_accessibility,
        !flag_missing_operating_system, !flag_missing_language, !flag_missing_updated,
        !flag_missing_function_metadata, !flag_function_without_operation)),
      metadata_completeness_score = rowMeans(cbind(!flag_registry_missing_doi, !flag_registry_missing_publication_year,
        !flag_missing_homepage, !flag_missing_documentation, !flag_missing_license, !flag_missing_accessibility,
        !flag_missing_operating_system, !flag_missing_language, !flag_missing_updated,
        !flag_missing_function_metadata, !flag_function_without_operation)))
  }

  # Sequential eligibility gates where each population is a subset of the previous one.
  select_candidate_populations <- function(tools_audited) {
    p <- list(unique_records = filter(tools_audited, !flag_duplicate_record))
    p$scope_included <- filter(p$unique_records, scope_classification == "Include")
    p$scope_review <- filter(p$unique_records, scope_classification == "Review")
    p$scope_out <- filter(p$unique_records, scope_classification == "Out of scope")
    p$access_eligible <- filter(p$scope_included, access_license_eligible)
    p$programmatic_scope <- filter(p$access_eligible, !flag_web_or_desktop)
    p$publication_traceable <- filter(p$programmatic_scope, !flag_missing_publication_identifier)
    p$citation_eligible <- filter(p$publication_traceable, passes_citation_filter)
    p$tools_candidates <- filter(p$citation_eligible, if (!check_urls) TRUE else any_url_accessible)
    p
  }

  annotate_function_records <- function(function_records, tools_audited, tools_candidates, omic) {
    audited <- function_records |> mutate(
      omic_type = str_to_title(omic),
      flag_missing_operation_uri = is_blank(operation_uri),
      flag_invalid_operation_uri = !flag_missing_operation_uri & !str_detect(operation_uri, "^https?://edamontology\\.org/operation_[0-9]+$"),
      flag_missing_input_data = is_blank(input_data_uris),
      flag_missing_input_format = is_blank(input_format_uris),
      flag_missing_output_data = is_blank(output_data_uris),
      flag_missing_output_format = is_blank(output_format_uris)) |>
      left_join(distinct(tools_audited, biotools_id, canonical_record_id, flag_duplicate_record, scope_classification,
        scope_reason, flag_scope_review, flag_scope_out_of_scope, flag_topic_exclusion), by = "biotools_id")
    candidate_ids <- tools_candidates |> filter(!is.na(biotools_id)) |> distinct(biotools_id) |> pull()
    list(audited = audited, candidate = filter(audited, biotools_id %in% candidate_ids))
  }

  export_omic_outputs <- function(tools_audited, p, function_annotations, omic, stem, input, function_input, keep) {
    output_path_for <- function(suffix) file.path(output_dir, paste0(stem, suffix))
    # Table, TSV suffix and optional lossless RDS copy. The legacy
    # *_annotated_filtered_tools_jan2026 files repeat the candidate table.
    tables <- list(
      list(tools_audited, "_all_records_quality_flags", TRUE),
      list(p$tools_candidates, "_candidate_tools", TRUE),
      list(p$scope_included, "_scope_included", FALSE),
      list(p$scope_review, "_scope_review", FALSE),
      list(p$scope_out, "_scope_out_of_scope", FALSE),
      list(p$tools_candidates, "_annotated_filtered_tools_jan2026", TRUE),
      list(function_annotations$audited, "_all_function_operations", TRUE),
      list(function_annotations$candidate, "_candidate_function_operations", TRUE)
    )
    outputs <- character()
    for (table in tables) {
      tsv <- output_path_for(paste0(table[[2]], ".tsv"))
      write_safe_tsv(table[[1]], tsv)
      outputs <- c(outputs, tsv)
      if (table[[3]]) {
        rds <- output_path_for(paste0(table[[2]], ".rds"))
        saveRDS(table[[1]], rds)
        outputs <- c(outputs, rds)
      }
    }
    write_output <- function(x, suffix) {
      path <- output_path_for(suffix)
      write_safe_tsv(x, path)
      outputs <<- c(outputs, path)
    }

    # 6.1 Citation coverage and independent quality summaries -------------------
    # The citation coverage summary reports the number of tools with traceable publications, the number of tools with missing DOIs, and the number of tools that require manual review due to conflicting or incomplete citation data. The independent quality statistics report the number and proportion of tools with missing function metadata, missing operation URIs, and other quality flags.

    write_output(filter(p$publication_traceable, citation_filter_decision == "Review"), "_citation_review.tsv")
    write_output(publication_coverage_summary(p$unique_records), "_citation_coverage.tsv")
    write_output(summarise(tools_audited,
      n_tools = n(),
      n_function_metadata_missing = sum(flag_missing_function_metadata, na.rm = TRUE),
      proportion_function_metadata_missing = mean(flag_missing_function_metadata, na.rm = TRUE),
      n_function_present_operation_missing = sum(flag_function_without_operation, na.rm = TRUE),
      proportion_function_present_operation_missing = mean(flag_function_without_operation, na.rm = TRUE)),
      "_function_annotation_quality.tsv")
    flags <- names(tools_audited)[startsWith(names(tools_audited), "flag_")]
    write_output(map_dfr(flags, function(flag) {
      flagged <- tools_audited[[flag]] %in% TRUE
      tibble(metric = flag, n_flagged = sum(flagged), proportion_flagged = mean(flagged), denominator = nrow(tools_audited))
    }), "_independent_quality_statistics.tsv")
    write_output(summarise(tools_audited,
      n = n(),
      mean_metadata_completeness = mean(metadata_completeness_score, na.rm = TRUE),
      median_metadata_completeness = median(metadata_completeness_score, na.rm = TRUE),
      n_url_checked = sum(!is.na(any_url_accessible)),
      proportion_url_accessible_among_checked = if (!check_urls) NA_real_ else mean(any_url_accessible, na.rm = TRUE),
      .by = registry_update_age_group), "_registry_age_completeness.tsv")

    # 6.2 Model registry update age and metadata completeness ---------------------
    # The linear regression model predicts the metadata completeness score based on the number of years since the last registry update. The model is only fitted if there are at least 10 records and at least 2 distinct values for years since the last registry update. The model summary includes coefficients, standard errors, t-statistics, p-values, number of observations, and R-squared value.
    # NOTE: Metadata completeness is currently not reported in dissertation results and were just included as an additional quality metric for the audit. The model is not used to filter candidates.

    model_data <- filter(tools_audited, !is.na(years_since_registry_update), !is.na(metadata_completeness_score))
    models <- tibble()
    if (nrow(model_data) >= 10 && n_distinct(model_data$years_since_registry_update) >= 2) {
      fit <- lm(metadata_completeness_score ~ years_since_registry_update, data = model_data)
      fit_summary <- summary(fit)
      coefficient_table <- as.data.frame(fit_summary$coefficients)
      models <- tibble(model = "metadata_completeness ~ years_since_registry_update",
        term = rownames(coefficient_table), estimate = coefficient_table[, 1], std_error = coefficient_table[, 2],
        statistic = coefficient_table[, 3], p_value = coefficient_table[, 4], n = nobs(fit), r_squared = fit_summary$r.squared)
    }
    write_output(models, "_registry_age_completeness_model.tsv")

    # 6.3 Filter counts and the reproducibility manifest -------------------------
    # The manifest is a JSON file that records the inputs, outputs, and parameters of the analysis for reproducibility.
    
    counts <- c(initial_load = nrow(tools_audited),
      unique_records = nrow(p$unique_records),
      scope_included = nrow(p$scope_included),
      scope_review = nrow(p$scope_review),
      scope_out_of_scope = nrow(p$scope_out),
      access_and_license_eligible = nrow(p$access_eligible),
      programmatic_scope = nrow(p$programmatic_scope),
      publication_traceable = nrow(p$publication_traceable),
      citation_eligible = nrow(p$citation_eligible),
      final_candidate = nrow(p$tools_candidates))
    summary_path <- file.path(output_dir, paste0(omic, "_filter_summary.tsv"))
    write_safe_tsv(tibble(step = names(counts), tools_remaining = as.integer(counts)), summary_path)
    outputs <- c(outputs, summary_path)

    file_record <- function(x) list(path = normalizePath(x, winslash = "/", mustWork = FALSE), md5 = safe_md5(x))
    manifest <- list(
      pipeline = "bio.tools curation audit and candidate selection",
      run_timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      publication_policy = list(source = citation_source_expected, input_tag = input_tag,
        traceability = "DOI or PMID or PMCID", publication_year = "Earliest available linked publication year",
        thresholds = "Recent records pass without citation counts; older partial totals above threshold pass, below threshold require review; conflicts require review",
        registry_completeness = "Original bio.tools publication evidence; enriched completeness reported separately"),
      analysis_date = as.character(analysis_date),
      omic = omic,
      script = list(path = script_path, md5 = safe_md5(script_path)),
      inputs = lapply(c(records = input, function_records = function_input, keep_terms = keep,
        exclusion_terms = exclusion_file, analysis_helpers = analysis_helper_path, configuration = config_file), file_record),
      thresholds = c(config$candidate_filter, list(
        url_timeout_seconds = if (check_urls) url_timeout_seconds else NA, url_retries = if (check_urls) url_retries else NA)),
      scope_model = list(classes = c("Include", "Review", "Out of scope"),
        positive_sources = c("bio.tools topic", "name and description", "bio.tools function operation/input/output metadata", "at least two distinct omics layers for multiomics"),
        rule = "Positive omics evidence -> Include; otherwise exclusion evidence -> Out of scope; otherwise Review",
        exclusion_never_overrides_positive_evidence = TRUE, review_records_excluded_from_candidate_set = TRUE),
      url_audit_performed = check_urls,
      url_audit = list(scope = "citation-eligible records only (after all metadata gates)",
        workers = url_workers,
        cache = file_record(url_cache_file),
        checked_at_utc_range = if (nrow(url_audit_cache)) range(url_audit_cache$checked_at_utc) else NA),
      record_counts = as.list(counts),
      function_classification = "bio.tools function.operation EDAM URIs; no investigator-defined keyword categories",
      outputs = setNames(lapply(outputs, file_record), basename(outputs)),
      software = list(R = R.version.string, platform = R.version$platform,
        packages = as.list(vapply(pkgs, function(x) as.character(packageVersion(x)), character(1)))))
    write_json(manifest, output_path_for("_reproducibility_manifest.json"), pretty = TRUE, auto_unbox = TRUE, na = "null")
    message(omic, ": ", nrow(tools_audited), " audited; ", nrow(p$tools_candidates), " candidates")
  }

  # 7. Process one omics dataset ---------------------------------------------------
  # The `pwalk()` call below iterates over the rows of `domain_config`, passing each row's values to this function.

  process_omic <- function(omic, keep, stem, input, function_input) {
    message("Processing ", omic)
    required <- c(input, function_input, keep, exclusion_file)
    if (any(!file.exists(required))) stop("Missing: ", paste(required[!file.exists(required)], collapse = ", "))
    keep_re <- term_regex(read_terms(keep))
    exclude_re <- term_regex(read_terms(exclusion_file))
    tools_raw <- audit_publications(input)
    function_annotations <- load_function_annotations(function_input)
    tools_audited <- derive_scope_access_flags(tools_raw, function_annotations$scope, omic, keep_re, exclude_re) |>
      audit_population_urls(omic)
    populations <- select_candidate_populations(tools_audited)
    function_annotations <- annotate_function_records(function_annotations$records, tools_audited,
      populations$tools_candidates, omic)
    export_omic_outputs(tools_audited, populations, function_annotations, omic, stem, input, function_input, keep)
  }
  # 8. Main entry point -------------------------------------------------------------
  
  pwalk(domain_config, process_omic)
  message("Completed ", nrow(domain_config), " omics dataset(s).")
}

main()
