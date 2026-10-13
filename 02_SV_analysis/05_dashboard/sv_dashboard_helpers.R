# Parse the INFO field of a VCF entry into a named list.
parse_info_field <- function(info) {
  if (is.na(info) || !nzchar(info)) return(list())
  entries <- strsplit(info, ";", fixed = TRUE)[[1]]
  result <- list()
  for (entry in entries) {
    parts <- strsplit(entry, "=", fixed = TRUE)[[1]]
    key <- parts[[1]]
    result[[key]] <- if (length(parts) > 1) paste(parts[-1], collapse = "=") else TRUE
  }
  result
}

# Count a known alternate allele, including partial alternate GTs such as ./1.
is_carrier <- function(format, sample_values) {
  if (is.na(format) || is.na(sample_values)) return(FALSE)
  gt_index <- match("GT", strsplit(format, ":", fixed = TRUE)[[1]])
  values <- strsplit(sample_values, ":", fixed = TRUE)[[1]]
  if (is.na(gt_index) || gt_index > length(values)) return(FALSE)
  genotype <- values[[gt_index]]
  if (!grepl("^(\\.[/|]|[0-9]+[/|])*([0-9]+|\\.)$", genotype)) return(FALSE)
  alleles <- strsplit(genotype, "[/|]")[[1]]
  any(alleles != "." & suppressWarnings(as.numeric(alleles)) > 0, na.rm = TRUE)
}

# Convert a vcfR object to a data frame, expanding INFO fields into separate columns.
vcf_to_data_frame <- function(vcf) {
  fixed <- as.data.frame(vcf@fix, stringsAsFactors = FALSE, check.names = FALSE)
  parsed <- lapply(fixed$INFO, parse_info_field)
  keys <- unique(unlist(lapply(parsed, names), use.names = FALSE))
  info <- if (length(keys)) {
    as.data.frame(do.call(rbind, lapply(parsed, function(row) {
      setNames(vapply(keys, function(key) {
        value <- row[[key]]
        if (is.null(value)) NA_character_ else as.character(value)
      }, character(1)), keys)
    })), stringsAsFactors = FALSE, check.names = FALSE)
  } else data.frame(row.names = seq_len(nrow(fixed)))

  gt <- vcf@gt
  samples <- if (ncol(gt) > 1) as.data.frame(gt[, -1, drop = FALSE], stringsAsFactors = FALSE) else NULL
  # cbind.data.frame() already controls check.names internally. Passing
  # check.names here is forwarded to data.frame() twice and causes
  # "formal argument 'check.names' matched by multiple actual arguments".
  result <- cbind(fixed, info, samples)
  result$FORMAT <- if (ncol(gt)) gt[, "FORMAT"] else rep(NA_character_, nrow(fixed))
  result[result == "." | result == ""] <- NA
  attr(result, "sample_names") <- if (is.null(samples)) character() else names(samples)
  result
}

# Column descriptions shown in the dashboard.
column_descriptions <- read.delim(
  file.path(dashboard_code_dir, "annotsv_column_descriptions.tsv"),
  stringsAsFactors = FALSE, check.names = FALSE, encoding = "UTF-8",
  quote = "", comment.char = ""
)
stopifnot(!anyDuplicated(column_descriptions$Column))
