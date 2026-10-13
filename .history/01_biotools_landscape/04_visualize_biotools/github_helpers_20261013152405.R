# GitHub repository retrieval and incremental snapshot caching.

empty_github_metadata <- list(stars = NA, forks = NA, watchers = NA, open_issues = NA, last_push_at = NA)

get_github_metadata_full <- function(repo, token = NULL) {
  headers <- c(Accept = "application/vnd.github.v3+json")
  if (!is.null(token) && token != "") headers <- c(Authorization = paste("token", token), headers)
  response <- httr::GET(paste0("https://api.github.com/repos/", repo), httr::add_headers(.headers = headers))
  status_code <- httr::status_code(response)
  if (status_code != 200) {
    response_excerpt <- substr(tryCatch(httr::content(response, as = "text", encoding = "UTF-8"), error = function(e) "[no body]"), 1, 400)
    message(sprintf("GitHub API error (%s): %s → %s", status_code, repo, response_excerpt))
    return(empty_github_metadata)
  }
  content <- jsonlite::fromJSON(httr::content(response, as = "text", encoding = "UTF-8"))
  list(stars = content$stargazers_count, forks = content$forks_count, watchers = content$subscribers_count,
    open_issues = content$open_issues_count, last_push_at = content$pushed_at)
}

update_github_cache <- function(tools_with_github, config, cache_file) {
  safe_get_github_metadata_full <- purrr::possibly(function(repo) {
      Sys.sleep(1)
      token <- Sys.getenv(config$github$token_environment_variable, "")
      metadata <- get_github_metadata_full(repo, token)
      message(glue("✓ {repo}: {metadata$stars} stars, {metadata$forks} forks, last push {metadata$last_push_at}"))
      metadata
    }, otherwise = empty_github_metadata)

  dir.create(dirname(cache_file), recursive = TRUE, showWarnings = FALSE)
  required_cache_columns <- c("github_repo", "last_push_at", "stars", "forks", "watchers", "open_issues")
  # retrieved_at records the date each row was fetched from the GitHub API. Older
  # caches without it are still accepted; those rows get NA and are reported in
  # the manifest so the retrieval date range is never silently unknown.
  cache_columns <- c(required_cache_columns, "retrieved_at")

  metric_columns <- c("stars", "forks", "watchers", "open_issues")
  cache_df <- if (file.exists(cache_file)) {
    raw_cache <- read_csv(cache_file, show_col_types = FALSE)
    # Caches written before the column rename store the push date as last_commit.
    if (!"last_push_at" %in% names(raw_cache) && "last_commit" %in% names(raw_cache)) {
      raw_cache <- rename(raw_cache, last_push_at = last_commit)
    }
    missing_cache_columns <- setdiff(required_cache_columns, names(raw_cache))
    if (length(missing_cache_columns) > 0L) {
      stop("GitHub cache is missing required columns: ", paste(missing_cache_columns, collapse = ", "))
    }
    if (!"retrieved_at" %in% names(raw_cache)) raw_cache$retrieved_at <- NA_character_
    raw_cache %>%
      transmute(
      github_repo = as.character(github_repo),
      last_push_at = as.character(last_push_at),
      across(all_of(metric_columns), as.numeric),
      retrieved_at = as.character(retrieved_at)
    ) %>%
      distinct(github_repo, .keep_all = TRUE)
  } else {
    tibble(github_repo = character(), last_push_at = character(), stars = numeric(), forks = numeric(),
      watchers = numeric(), open_issues = numeric(), retrieved_at = character())
  }

  # A row is cached only when at least one GitHub metric was retrieved. Rows from
  # earlier failed queries (repository name plus blank values) must be retried.
  usable_cached_repos <- cache_df %>%
    filter(if_any(all_of(metric_columns), ~ !is.na(.x))) %>%
    pull(github_repo)

  refresh_all_repos <- isTRUE(config$github$refresh_by_default)
  repos_to_query <- tools_with_github %>%
    filter(!is.na(github_repo), nzchar(trimws(github_repo))) %>%
    distinct(github_repo) %>%
    filter(refresh_all_repos | !github_repo %in% usable_cached_repos) %>%
    pull(github_repo)

  # Freeze switch: once the final cache is complete, set github.freeze_cache: true
  # in the config so later runs never re-query (and never change) GitHub data.
  if (isTRUE(config$github$freeze_cache)) {
    message(glue("GitHub cache frozen: skipping {length(repos_to_query)} unretrieved repositories."))
    repos_to_query <- character()
  }

  message(glue("GitHub repositories to query: {length(repos_to_query)}"))
  if (length(repos_to_query) > 0L && !nzchar(Sys.getenv(config$github$token_environment_variable, ""))) {
    warning(
      paste0("No ", config$github$token_environment_variable, " is set. GitHub's unauthenticated API limit may prevent the cache from being completed."),
      call. = FALSE
    )
  }

  # Batch GitHub querying with incremental cache writes -------------------------

  batch_size <- 100L
  batches <- split(repos_to_query, ceiling(seq_along(repos_to_query) / batch_size))
  n_batches <- length(batches)

  for (batch_index in seq_len(n_batches)) {
    message(glue("Batch {batch_index} / {n_batches}"))
    batch_repos <- batches[[batch_index]]
    batch_results <- map(batch_repos, safe_get_github_metadata_full)

    batch_df <- tibble(
      github_repo = batch_repos,
      last_push_at = map_chr(batch_results, "last_push_at", .default = NA_character_),
      stars       = map_dbl(batch_results, "stars", .default = NA_real_),
      forks       = map_dbl(batch_results, "forks", .default = NA_real_),
      watchers    = map_dbl(batch_results, "watchers", .default = NA_real_),
      open_issues = map_dbl(batch_results, "open_issues", .default = NA_real_),
      retrieved_at = as.character(Sys.Date())
    )

    # Replace prior failed/stale rows, retain the canonical cache schema,
    # and write after every batch so interrupted runs can resume.
    cache_df <- cache_df %>%
      filter(!github_repo %in% batch_repos) %>%
      bind_rows(batch_df) %>%
      select(all_of(cache_columns)) %>%
      distinct(github_repo, .keep_all = TRUE)
    write_csv(cache_df, cache_file, na = "")

    if (batch_index %% 5L == 0L && batch_index < n_batches) {
      message("⏸ Pausing briefly to respect GitHub API limits...")
      Sys.sleep(30)
    }
  }
  cache_df
}
