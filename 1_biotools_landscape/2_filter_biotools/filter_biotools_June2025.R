filter_biotools <- function(
    input_file, 
    keep_file, 
    filter_file, 
    function_file,
    filter_summary_tool, 
    output_file,
    output_file_rds 
) {
  
  # ================================================
  #  Load Libraries
  # ================================================
  library(dplyr)
  library(httr)
  library(stringr)
  library(tidyr)
  library(curl)
  library(future)
  library(future.apply)
  library(janitor)
  library(magrittr)
  
  # ================================================
  #  Define Metadata and Input Files
  # ================================================
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  script_name <- "filter_proteomic_tools.R"
  
  tools_df <- read.csv(input_file, sep = "\t", header = TRUE, stringsAsFactors = FALSE)
  file1 <- readLines(keep_file)
  file2 <- readLines(filter_file)
  function_df <- read.csv(function_file, header = TRUE, stringsAsFactors = FALSE)
  
  # ================================================
  #  Clean Column Names
  # ================================================
  clean_names_custom <- function(df, case = "snake") {
    janitor::clean_names(df, case = case)
  }
  tools_df <- clean_names_custom(tools_df)
  
  # ================================================
  #  Compile Regex Patterns
  # ================================================
  keep_pattern <- paste0("\\b(", paste(file1, collapse = "|"), ")\\b")
  filter_pattern <- paste0("\\b(", paste(file2, collapse = "|"), ")\\b")
  
  # ================================================
  #  Initialize Log
  # ================================================
  filter_summary <- data.frame(
    Step = c(paste0("Filtering summary created on ", timestamp),
             paste0("Script: ", script_name),
             paste0("Input file: ", input_file)),
    tools_remaining = c(NA, NA, NA),
    stringsAsFactors = FALSE
  )
  
  filter_summary <- rbind(filter_summary, data.frame(
    Step = "Initial load",
    tools_remaining = nrow(tools_df)
  ))
  
  log_step <- function(step, df) {
    filter_summary <<- rbind(filter_summary, data.frame(
      Step = step,
      tools_remaining = nrow(df)
    ))
  }
  
  # ================================================
  #  Filtering Steps
  # ================================================
  tools_filtered <- tools_df %>%
    distinct(name, publication_doi, .keep_all = TRUE)
  log_step("Remove duplicate tools", tools_filtered)
  
  tools_filtered <- tools_filtered %>%
    filter(grepl(keep_pattern, topic, ignore.case = TRUE) |
             (!grepl(keep_pattern, topic, ignore.case = TRUE) & !grepl(filter_pattern, topic, ignore.case = TRUE))) %>%
    distinct()
  log_step("Remove unrelated keywords", tools_filtered)
  
  tools_filtered <- tools_filtered %>%
    filter(!grepl("web application|desktop application", tool_type, ignore.case = TRUE))
  log_step("Removed web/desktop apps", tools_filtered)
  
  tools_filtered %<>% filter(!is.na(publication_doi) & publication_doi != "")
  log_step("Remove tools with no DOI", tools_filtered)
  
  # ================================================
  #  Publication Year & Citations
  # ================================================
  tools_filtered <- tools_filtered %>%
    mutate(
      publication_year = str_extract_all(publication_date, "\\d{4}") %>%
        lapply(function(x) {
          years <- as.numeric(x)
          if (length(years) == 0 || all(is.na(years))) return(NA_real_)
          return(min(years, na.rm = TRUE))
        }) %>%
        unlist(),
      
      citation_total = str_extract_all(publication_citations, "\\d+") %>%
        lapply(function(x) {
          nums <- as.numeric(x)
          if (length(nums) == 0 || all(is.na(nums))) return(NA_real_)
          return(sum(nums, na.rm = TRUE))
        }) %>%
        unlist()
    )
  
  # Safe filtering function
  passes_filter <- function(year, citations) {
    if (is.na(year) || is.na(citations)) return(FALSE)
    
    year >= 2020 ||
      (year >= 2015 && year < 2020 && citations >= 30) ||
      (year >= 2010 && year < 2015 && citations >= 50) ||
      (year < 2010 && citations >= 70)
  }
  
  # Apply filtering
  tools_filtered <- tools_filtered %>%
    filter(mapply(passes_filter, publication_year, citation_total))
  
  log_step("Filtered by Publication Year and Citations", tools_filtered)
  
  tools_filtered$publication_year <- sapply(tools_filtered$publication_year, function(x) paste(x, collapse = ","))
  
  # ================================================
  #  URL Validation
  # ================================================
  plan(multisession, workers = 8)
  
  url_exists <- function(url) {
    if (is.na(url) || url == "") return(FALSE)
    tryCatch({
      resp <- httr::HEAD(url, timeout(5))
      return(httr::status_code(resp) < 400)
    }, error = function(e) {
      return(FALSE)
    })
  }
  
  check_urls_parallel <- function(homepage, documentation) {
    results <- mapply(function(h, d) {
      homepage_ok <- url_exists(h)
      documentation_ok <- url_exists(d)
      return(homepage_ok || documentation_ok)
    }, homepage, documentation, SIMPLIFY = TRUE)
    return(results)
  }
  
  tools_filtered$URL_OK <- check_urls_parallel(tools_filtered$homepage, tools_filtered$documentation)
  tools_filtered <- tools_filtered %>% filter(URL_OK)
  log_step("Filtered by URL accessibility", tools_filtered)
  
  # ================================================
  #  Functional Annotation
  # ================================================
    function_df$Keyword <- tolower(function_df$Keyword)
  function_keywords <- split(function_df$Keyword, function_df$Category)
  
  assign_function <- function(text, keyword_map) {
    tags <- c()
    text <- tolower(text)
    for (category in names(keyword_map)) {
      for (kw in keyword_map[[category]]) {
        if (grepl(kw, text, fixed = TRUE)) {
          tags <- c(tags, category)
          break
        }
      }
    }
    if (length(tags) == 0) return("Unclassified")
    return(paste(unique(tags), collapse = "; "))
  }
  
  tools_filtered$Function <- sapply(
    paste(tools_filtered$topic, tools_filtered$description, sep = " "),
    assign_function,
    keyword_map = function_keywords
  )
  log_step("Assigned function tags", tools_filtered)
  
  # ================================================
  #  Save Outputs
  # ================================================
  write.csv(
    filter_summary,
    filter_summary_tool,
    row.names = FALSE
  )
  
  write.table(
    tools_filtered,
    output_file,
    sep = "\t", row.names = FALSE, quote = FALSE
  )
  
  saveRDS(tools_filtered, output_file_rds)
}