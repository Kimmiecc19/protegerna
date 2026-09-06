# SV-RareInsight: structural-variant viewer and RareInsight resource search

required_packages <- c("shiny", "shinydashboard", "DT", "vcfR", "shinyjs")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing_packages)) {
  stop("Install the following packages before running the app: ",
       paste(missing_packages, collapse = ", "))
}

library(shiny)
library(shinydashboard)
library(DT)
library(vcfR)
library(shinyjs)

options(shiny.maxRequestSize = 60 * 1024^2)

 # --- Helper functions for constructing resource search URLs and parsing VCF INFO fields ---

# Helper function to ensure dbSNP rsIDs are prefixed with "rs" for URL construction.
normalise_rs <- function(term) {
  term <- trimws(term)
  if (grepl("^rs", term, ignore.case = TRUE)) term else paste0("rs", term)
}

# URL rules adapted from the RareInsight search/resource functions.
# //REVIEW: should I add any other URLs? -> ClinGen, ACMG, DECIP_HER, DGV, dbVAR?
construct_search_urls <- function(search_type, search_term) {
  term <- trimws(search_term)
  encoded <- URLencode(term, reserved = TRUE)
  rs_term <- URLencode(normalise_rs(term), reserved = TRUE)
  slug <- URLencode(gsub("\\s+", "-", tolower(term)), reserved = TRUE)

  urls <- list(
    PubMed = paste0("https://pubmed.ncbi.nlm.nih.gov/?term=", encoded)
  )

  if (search_type %in% c("Gene", "Disorder", "ClinVar", "dbSNP")) {
    omim_term <- if (search_type == "dbSNP") rs_term else encoded
    urls$OMIM <- paste0(
      "https://www.omim.org/search?index=entry&start=1&search=", omim_term,
      "&sort=score+desc%2C+prefix_sort+desc&limit=10"
    )
  }
  if (search_type == "Gene") {
    urls$ClinVar <- paste0("https://www.ncbi.nlm.nih.gov/clinvar/?term=", encoded, "%5Bgene%5D&redir=gene")
    urls$dbSNP <- paste0("https://www.ncbi.nlm.nih.gov/snp/?term=", encoded)
    urls$GeneReviews <- paste0("https://www.ncbi.nlm.nih.gov/books/NBK1116/?term=", encoded, "%20gene%20review")
    urls$VarSome <- paste0("https://varsome.com/gene/hg38/", encoded)
    urls$LitVar <- paste0("https://www.ncbi.nlm.nih.gov/research/litvar2/docsum?text=", encoded)
    # //REVIEW: specify gnomad-SV? https://gnomad.broadinstitute.org/gene/ENSG00000123500?dataset=gnomad_sv_r4
    urls$gnomAD <- paste0("https://gnomad.broadinstitute.org/gene/", encoded)
  } else if (search_type == "ClinVar") {
    urls$ClinVar <- paste0("https://www.ncbi.nlm.nih.gov/clinvar/?term=", encoded, "&redir=rcv")
  } else if (search_type == "dbSNP") {
    urls$dbSNP <- paste0("https://www.ncbi.nlm.nih.gov/snp/", rs_term)
    urls$VarSome <- paste0("https://varsome.com/variant/hg38/", rs_term)
    urls$LitVar <- paste0("https://www.ncbi.nlm.nih.gov/research/litvar2/docsum?variant=litvar@", rs_term, "%23%23&query=")
  } else if (search_type == "Disorder") {
    urls$NORD <- paste0("https://rarediseases.org/rare-diseases/", slug)
    urls$GARD <- paste0("https://rarediseases.info.nih.gov/diseases?search=", encoded)
    urls$VarSome <- paste0("https://varsome.com/search-results/", encoded)
    urls$LitVar <- paste0("https://www.ncbi.nlm.nih.gov/research/litvar2/docsum?text=", encoded)
  } else if (search_type == "Variant") {
    urls$ClinVar <- paste0("https://www.ncbi.nlm.nih.gov/clinvar/?term=", encoded)
    urls$VarSome <- paste0("https://varsome.com/search-results/", encoded)
    urls$LitVar <- paste0("https://www.ncbi.nlm.nih.gov/research/litvar2/docsum?text=", encoded)
  }

  data.frame(Resource = names(urls), URL = unlist(urls, use.names = FALSE), stringsAsFactors = FALSE)
}

# AnnotSV fields that are useful for first-pass review. The table derives its
# visibility from the columns that actually exist in the input VCF, so raw
# caller VCFs do not need to manufacture empty annotation columns.
default_visible_columns <- c(
  # Standard VCF / OctopuSV names (raw Manta-TIDDIT union/intersection files)
  "CHROM", "POS", "ID", "SVTYPE", "END", "SVLEN", "SOURCES", "SUPPORT", "SVMETHOD",
  # AnnotSV names (fresh variantconvert VCF files)
  "AnnotSV_ID", "SV_chrom", "SV_start", "SV_end", "SV_length", "SV_type", "REF", "ALT",
  "QUAL", "FILTER", "Gene_name", "Gene_count", "Frameshift", "P_gain_phen", "P_gain_hpo",
  "P_loss_phen", "P_loss_hpo", "P_ins_phen", "P_ins_hpo", "po_P_gain_phen", "po_P_gain_hpo",
  "po_P_loss_phen", "po_P_loss_hpo", "P_snvindel_phen", "B_gain_AFmax", "B_loss_AFmax",
  "ACMG", "OMIM_ID", "OMIM_phenotype", "OMIM_inheritance", "OMIM_morbid",
  "OMIM_morbid_candidate", "LOEUF_bin", "GnomAD_pLI", "Exomiser_gene_pheno_score",
  "Human_pheno_evidence", "AnnotSV_ranking_score", "ACMG_class"
)

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
  result[result == "." | result == ""] <- NA
  attr(result, "sample_names") <- if (is.null(samples)) character() else names(samples)
  result
}

# Column descriptions for the AnnotSV output fields, used in the "Column descriptions" tab.
column_descriptions <- data.frame(
  Column = c(
    "AnnotSV_ID", "SV_chrom", "SV_start", "SV_end", "SV_length", "SV_type", "Samples_ID",
    "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT", "Annotation_mode", "Gene_name",
    "Closest_left", "Closest_right", "Gene_count", "Tx", "Tx_version", "Tx_start", "Tx_end",
    "Overlapped_tx_length", "Overlapped_CDS_length", "Overlapped_CDS_percent", "Frameshift",
    "Exon_count", "Location", "Location2", "Dist_nearest_SS", "Nearest_SS_type", "Intersect_start",
    "Intersect_end", "RE_gene", "ACMG", "HI", "TS", "DDD_HI_percent", "NCBI_gene_ID", "OMIM_ID",
    "OMIM_phenotype", "OMIM_inheritance", "OMIM_morbid", "OMIM_morbid_candidate", "LOEUF_bin",
    "GnomAD_pLI", "AnnotSV_ranking_score", "AnnotSV_ranking_criteria", "ACMG_class"
  ),
  Description = c(
    "Unique identifier for the variant", "Chromosome containing the structural variant",
    "Start position of the variant", "End position of the variant", "Length of the variant",
    "Type of structural variant", "Samples carrying this variant", "VCF variant ID", "Reference allele",
    "Alternate allele", "Variant quality score", "Filter status", "VCF INFO field", "VCF FORMAT field",
    "AnnotSV annotation mode", "Gene affected by the structural variant", "Closest upstream gene",
    "Closest downstream gene", "Number of overlapping genes", "Transcript ID", "Transcript version",
    "Transcript start position", "Transcript end position", "Length of transcript affected",
    "Length of coding sequence affected", "Percentage of coding sequence overlapped",
    "Whether the variant causes a frameshift", "Number of exons affected", "Region type",
    "Detailed location", "Distance to nearest splice site", "Nearest splice-site type",
    "Gene-overlap start coordinate", "Gene-overlap end coordinate", "Regulatory-element gene",
    "ACMG rule code", "Haploinsufficiency score", "Triplosensitivity score",
    "DDD haploinsufficiency percentage", "NCBI Entrez gene ID", "OMIM ID", "OMIM phenotype",
    "OMIM inheritance pattern", "Whether the gene is OMIM morbid", "OMIM morbid-candidate flag",
    "Loss-of-function constraint bin", "gnomAD pLI score", "AnnotSV ranking score",
    "Criteria supporting the AnnotSV ranking", "Final ACMG classification (1-5)"
  ), stringsAsFactors = FALSE
)

# Additional pathogenic, benign and partial-overlap fields from the complete
# AnnotSV catalogue in view_sv_descriptions.R.
column_descriptions <- rbind(
  column_descriptions,
  data.frame(
    Column = c("AnnotSV_ID", "SV_chrom", "SV_start", "SV_end", "SV_length", "SV_type",
                 "Samples_ID", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT",
                 "Annotation_mode", "Gene_name", "Closest_left", "Closest_right", "Gene_count",
                 "Tx", "Tx_version", "Tx_start", "Tx_end", "Overlapped_tx_length", "Overlapped_CDS_length",
                 "Overlapped_CDS_percent", "Frameshift", "Exon_count", "Location", "Location2",
                 "Dist_nearest_SS", "Nearest_SS_type", "Intersect_start", "Intersect_end", "RE_gene",
                 "P_gain_phen", "P_gain_hpo", "P_gain_source", "P_gain_coord",
                 "P_loss_phen", "P_loss_hpo", "P_loss_source", "P_loss_coord",
                 "P_ins_phen", "P_ins_hpo", "P_ins_source", "P_ins_coord",
                 "po_P_gain_phen", "po_P_gain_hpo", "po_P_gain_source", "po_P_gain_coord", "po_P_gain_percent",
                 "po_P_loss_phen", "po_P_loss_hpo", "po_P_loss_source", "po_P_loss_coord", "po_P_loss_percent",
                 "P_snvindel_nb", "P_snvindel_phen",
                 "B_gain_source", "B_gain_coord", "B_gain_AFmax",
                 "B_loss_source", "B_loss_coord", "B_loss_AFmax",
                 "po_B_gain_allG_source", "po_B_gain_allG_coord",
                 "po_B_gain_someG_source", "po_B_gain_someG_coord",
                 "po_B_loss_allG_coord", "po_B_loss_someG_source", "po_B_loss_someG_coord",
                 "ACMG", "HI", "TS", "DDD_HI_percent", "NCBI_gene_ID",
                 "OMIM_ID", "OMIM_phenotype", "OMIM_inheritance", "OMIM_morbid", "OMIM_morbid_candidate",
                 "LOEUF_bin", "GnomAD_pLI", "AnnotSV_ranking_score", "AnnotSV_ranking_criteria", "ACMG_class"),
                 Description = c(
                  "Unique identifier for the variant",
                  "Chromosome containing the structural variant",
                  "Start position of the variant",
                  "End position of the variant",
                  "Length of the variant",
                  "Type of SV (DEL, DUP, INS, INV)",
                  "Sample(s) carrying this variant",
        "VCF variant ID",
        "Reference allele",
        "Alternate allele",
        "Variant quality score",
        "Filter status (e.g., PASS)",
        "VCF INFO field content",
        "VCF FORMAT field content",
        "Annotation mode used (full, split, gene)",
        "Gene affected by the SV",
        "Closest gene upstream",
        "Closest gene downstream",
        "Number of overlapping genes",
        "Transcript ID",
        "Transcript version",
        "Transcript start position",
        "Transcript end position",
        "Length of transcript affected",
        "Length of CDS affected",
        "Percent of CDS overlapped",
        "Whether the variant causes a frameshift",
        "Number of exons affected",
        "Region type (intronic, exonic, etc.)",
        "Detailed location info",
        "Distance to nearest splice site",
        "Type of nearest splice site",
        "Overlap start coordinate with gene",
        "Overlap end coordinate with gene",
        "Regulatory element gene",
        "Phenotypes associated with predicted gain",
        "HPO terms for gain",
        "Source of gain prediction",
        "Coordinates of predicted gain",
        "Phenotypes associated with predicted loss",
        "HPO terms for loss",
        "Source of loss prediction",
        "Coordinates of predicted loss",
        "Phenotypes associated with predicted insertion",
        "HPO terms for insertion",
        "Source of insertion prediction",
        "Coordinates of predicted insertion",
        "Phenotypes for partial gain overlap",
        "HPO terms for partial gain",
        "Source for partial gain",
        "Coordinates for partial gain",
        "Percent region affected by partial gain",
        "Phenotypes for partial loss",
        "HPO terms for partial loss",
        "Source for partial loss",
        "Coordinates for partial loss",
        "Percent region affected by partial loss",
        "Number of pathogenic SNVs/indels nearby",
        "Phenotypes linked to SNVs/indels",
        "Source for known pathogenic gains",
        "Coordinates for known gains",
        "Max allele frequency for gains",
        "Source for known losses",
        "Coordinates for known losses",
        "Max allele frequency for losses",
        "Partial overlap gain (all genes) source",
        "Partial overlap gain (all genes) coord",
        "Partial overlap gain (some genes) source",
        "Partial overlap gain (some genes) coord",
        "Partial overlap loss (all genes) coord",
        "Partial overlap loss (some genes) source",
        "Partial overlap loss (some genes) coord",
        "ACMG rule code",
        "Haploinsufficiency score",
        "Triplosensitivity score",
        "Deciphering Developmental Disorders (DDD) dataset haploinsufficiency %",
        "NCBI Entrez gene ID",
        "OMIM ID",
        "OMIM phenotype",
        "OMIM inheritance pattern",
        "Gene is OMIM morbid",
        "OMIM morbid candidate flag",
        "Loss-of-function constraint bin",
        "gnomAD pLI score",
        "AnnotSV ranking score",
        "Criteria supporting the ranking - based on ACMG and ClinGen criteria (Riggs et al., 2020)",
        "Final ACMG classification (1–5)"
      ),
      stringsAsFactors = FALSE
    )
  )  
        
# Preserve the order used by the original catalogue rather than placing the
# restored fields after ACMG/OMIM fields.
annot_sv_column_order <- c(
  "AnnotSV_ID", "SV_chrom", "SV_start", "SV_end", "SV_length", "SV_type", "Samples_ID",
  "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT", "Annotation_mode", "Gene_name",
  "Closest_left", "Closest_right", "Gene_count", "Tx", "Tx_version", "Tx_start", "Tx_end",
  "Overlapped_tx_length", "Overlapped_CDS_length", "Overlapped_CDS_percent", "Frameshift",
  "Exon_count", "Location", "Location2", "Dist_nearest_SS", "Nearest_SS_type", "Intersect_start",
  "Intersect_end", "RE_gene", "P_gain_phen", "P_gain_hpo", "P_gain_source", "P_gain_coord",
  "P_loss_phen", "P_loss_hpo", "P_loss_source", "P_loss_coord", "P_ins_phen", "P_ins_hpo",
  "P_ins_source", "P_ins_coord", "po_P_gain_phen", "po_P_gain_hpo", "po_P_gain_source",
  "po_P_gain_coord", "po_P_gain_percent", "po_P_loss_phen", "po_P_loss_hpo", "po_P_loss_source",
  "po_P_loss_coord", "po_P_loss_percent", "P_snvindel_nb", "P_snvindel_phen", "B_gain_source",
  "B_gain_coord", "B_gain_AFmax", "B_loss_source", "B_loss_coord", "B_loss_AFmax",
  "po_B_gain_allG_source", "po_B_gain_allG_coord", "po_B_gain_someG_source", "po_B_gain_someG_coord",
  "po_B_loss_allG_coord", "po_B_loss_someG_source", "po_B_loss_someG_coord", "ACMG", "HI", "TS",
  "DDD_HI_percent", "NCBI_gene_ID", "OMIM_ID", "OMIM_phenotype", "OMIM_inheritance", "OMIM_morbid",
  "OMIM_morbid_candidate", "LOEUF_bin", "GnomAD_pLI", "AnnotSV_ranking_score",
  "AnnotSV_ranking_criteria", "ACMG_class"
)
column_descriptions <- column_descriptions[match(annot_sv_column_order, column_descriptions$Column), , drop = FALSE]

# Build the same interactive table for both the live dashboard and HTML export.
build_variant_table <- function(data, page_length = 20) {
  # CSV and Excel run in the browser. Read the user's requested base filename
  # at click time, remove any extension/unsafe characters, and let DataTables
  # append the correct extension for the selected format.
  browser_export_filename <- JS(
    "function() {",
    "  var field = document.getElementById('export_filename');",
    "  var name = field ? field.value.trim() : '';",
    "  name = name.replace(/\\.(html?|csv|xlsx?)$/i, '');",
    "  name = name.replace(/[<>:\\\\/?*|\"\\x00-\\x1F]/g, '_').replace(/[. ]+$/g, '');",
    "  return name || 'SV_RareInsight_export';",
    "}"
  )

  # DataTables targets are calculated only from the schema in this upload.
  # This is important for unannotated Manta/TIDDIT VCFs, where most AnnotSV
  # fields are absent and must not be passed to formatStyle/columnDefs.
  sample_columns <- intersect(attr(data, "sample_names"), names(data))
  initially_visible <- unique(c(default_visible_columns, sample_columns))
  hidden_columns <- which(!names(data) %in% initially_visible) - 1L

  table <- datatable(
    data,
    filter = "top",
    rownames = FALSE,
    extensions = c("Buttons", "FixedHeader", "FixedColumns"),
    options = list(
      scrollX = TRUE,
      pageLength = page_length,
      fixedHeader = TRUE,
      fixedColumns = list(leftColumns = 1),
      columnDefs = if (length(hidden_columns)) {
        list(list(targets = hidden_columns, visible = FALSE))
      } else list(),
      dom = "Bfrtip",
      buttons = list(
        "copy",
        list(extend = "csv", text = "CSV", filename = browser_export_filename),
        list(extend = "excel", text = "Excel", filename = browser_export_filename),
        list(extend = "colvis", text = "Show/Hide Columns")
      )
    )
  )

  if ("B_loss_AFmax" %in% names(data)) {
    table <- formatStyle(table, "B_loss_AFmax",
                         backgroundColor = styleInterval(0.05, c("#FB7575", "#6FF97C")))
  }
  if ("B_gain_AFmax" %in% names(data)) {
    table <- formatStyle(table, "B_gain_AFmax",
                         backgroundColor = styleInterval(0.05, c("#FB7575", "#6FF97C")))
  }
  if ("ACMG_class" %in% names(data)) {
    table <- formatStyle(table, "ACMG_class",
                         backgroundColor = styleEqual(c("1", "4", "5"),
                                                      c("#6FF97C", "#FCCF8C", "#FB7575")))
  }
  if ("AnnotSV_ranking_score" %in% names(data)) {
    table <- formatStyle(table, "AnnotSV_ranking_score",
                         backgroundColor = styleInterval(0.89, c("#6FF97C", "#FB7575")))
  }
  if ("OMIM_morbid" %in% names(data)) {
    table <- formatStyle(table, "OMIM_morbid",
                         backgroundColor = styleEqual(c("no", "yes"), c("#6FF97C", "#FB7575")))
  }
  if ("OMIM_morbid_candidate" %in% names(data)) {
    table <- formatStyle(table, "OMIM_morbid_candidate",
                         backgroundColor = styleEqual(c("no", "yes"), c("#6FF97C", "#FB7575")))
  }
  table
}

safe_export_filename <- function(value, default = "SV_RareInsight_export") {
  value <- trimws(if (is.null(value) || is.na(value)) "" else as.character(value)[1])
  value <- sub("\\.(html?|csv|xlsx?)$", "", value, ignore.case = TRUE)
  value <- gsub('[<>:"/\\\\|?*[:cntrl:]]', "_", value)
  value <- sub("[. ]+$", "", value)
  if (!nzchar(value)) default else value
}

# Write a portable HTML report without Pandoc or external JavaScript/CSS files.
write_variant_html <- function(data, file) {
  escape_html <- function(value) {
    value <- ifelse(is.na(value), "", as.character(value))
    value <- gsub("&", "&amp;", value, fixed = TRUE)
    value <- gsub("<", "&lt;", value, fixed = TRUE)
    value <- gsub(">", "&gt;", value, fixed = TRUE)
    value <- gsub('"', "&quot;", value, fixed = TRUE)
    value
  }

  cell_colour <- function(column, value) {
    if (is.na(value) || !nzchar(as.character(value))) return("")
    text <- as.character(value)
    numeric_value <- suppressWarnings(as.numeric(text))
    colour <- switch(
      column,
      "B_loss_AFmax" = if (!is.na(numeric_value)) if (numeric_value <= 0.05) "#FB7575" else "#6FF97C" else NULL,
      "B_gain_AFmax" = if (!is.na(numeric_value)) if (numeric_value <= 0.05) "#FB7575" else "#6FF97C" else NULL,
      "AnnotSV_ranking_score" = if (!is.na(numeric_value)) if (numeric_value <= 0.89) "#6FF97C" else "#FB7575" else NULL,
      "ACMG_class" = unname(c("1" = "#6FF97C", "4" = "#FCCF8C", "5" = "#FB7575")[text]),
      "OMIM_morbid" = unname(c("no" = "#6FF97C", "yes" = "#FB7575")[tolower(text)]),
      "OMIM_morbid_candidate" = unname(c("no" = "#6FF97C", "yes" = "#FB7575")[tolower(text)]),
      NULL
    )
    if (is.null(colour) || is.na(colour)) "" else paste0(' style="background-color:', colour, ';"')
  }

  connection <- base::file(file, open = "wb")
  on.exit(close(connection), add = TRUE)
  writeLines(c(
    "<!doctype html>",
    '<html lang="en"><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "<title>SV-RareInsight current table view</title>",
    "<style>body{font-family:Arial,sans-serif;margin:20px;color:#222} .toolbar{position:sticky;top:0;background:#fff;padding:10px 0;z-index:3} input{padding:7px;width:min(420px,70%)} button{padding:7px 12px;margin-left:6px}.table-wrap{overflow:auto;max-height:75vh;border:1px solid #ccc}table{border-collapse:collapse;font-size:12px;width:max-content;min-width:100%}th,td{border:1px solid #ddd;padding:6px;max-width:300px;overflow-wrap:anywhere}th{background:#3c8dbc;color:white;position:sticky;top:0;z-index:2}tr:nth-child(even){background:#f7f7f7}@media print{.toolbar{display:none}.table-wrap{max-height:none;overflow:visible}th{position:static}}</style>",
    "</head><body>",
    "<h1>SV-RareInsight current table view</h1>",
    paste0("<p>Exported: ", escape_html(format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
           " &nbsp; Rows: ", nrow(data), "</p>"),
    '<div class="toolbar"><label for="tableSearch">Search this report: </label><input id="tableSearch" type="search" placeholder="Type to filter rows..."><button onclick="window.print()">Print</button></div>',
    '<div class="table-wrap"><table id="variantTable"><thead><tr>',
    paste0("<th>", escape_html(names(data)), "</th>", collapse = ""),
    "</tr></thead><tbody>"
  ), connection, useBytes = TRUE)

  if (nrow(data)) {
    for (row_number in seq_len(nrow(data))) {
      values <- data[row_number, , drop = TRUE]
      cells <- vapply(seq_along(values), function(column_number) {
        value <- values[[column_number]]
        paste0("<td", cell_colour(names(data)[column_number], value), ">",
               escape_html(value), "</td>")
      }, character(1))
      writeLines(paste0("<tr>", paste0(cells, collapse = ""), "</tr>"),
                 connection, useBytes = TRUE)
    }
  }

  writeLines(c(
    "</tbody></table></div>",
    "<script>document.getElementById('tableSearch').addEventListener('input',function(){var q=this.value.toLowerCase();document.querySelectorAll('#variantTable tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().includes(q)?'':'none';});});</script>",
    "</body></html>"
  ), connection, useBytes = TRUE)
}

# --- Shiny UI and server logic ---
ui <- dashboardPage(
  dashboardHeader(title = tagList(tags$img(src = "SV.png", height = 40), " SV-RareInsight")),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Structural variants", tabName = "variants", icon = icon("table")),
      menuItem("Column descriptions", tabName = "descriptions", icon = icon("book")),
      menuItem("Resource search", tabName = "search", icon = icon("search"))
    )
  ),
  dashboardBody(
    useShinyjs(),
    tags$head(
      tags$style(HTML("
        .content-wrapper { background: #fff; }
        .dataTables_wrapper { overflow-x: auto; }
        .floating-filter {
          position: fixed;
          top: 60px;
          right: 20px;
          width: 220px;
          z-index: 1050;
          background: #f7f7f7;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
          transition: top 0.4s, opacity 0.4s;
          opacity: 1;
        }
        .floating-filter.collapsed {
          top: -190px;
          opacity: 0.1;
          pointer-events: none;
        }
        #toggle_tab {
          position: fixed;
          top: 60px;
          right: 20px;
          z-index: 1051;
          display: none;
          background: #5bc0de;
          color: white;
          padding: 6px 12px;
          border-radius: 4px;
          font-weight: bold;
          cursor: pointer;
        }
        table.dataTable td {
          white-space: normal !important;
          word-wrap: break-word;
          max-width: 300px;
        }
        table.dataTable th { white-space: nowrap; }
      "))
    ),
    tags$div(
      id = "filterPanel",
      class = "floating-filter",
      wellPanel(
        style = "padding:10px; margin-bottom:0;",
        actionButton("toggle_filter", "Hide Filters", class = "btn btn-info btn-xs",
                     style = "width:100%; margin-bottom:5px;"),
        selectizeInput(
          "gene_filter", "Gene(s):", choices = NULL, multiple = TRUE,
          options = list(placeholder = "Type or select genes...")
        ),
        actionButton("clear_filter", "Clear", class = "btn btn-warning btn-xs",
                     style = "width:100%; margin-top:5px;")
      )
    ),
    tags$div(
      id = "toggle_tab",
      onclick = "Shiny.setInputValue('show_filter', Math.random(), {priority: 'event'});",
      "Show Filters"
    ),
    tabItems(
      tabItem(
        tabName = "variants",
        fluidRow(
          box(width = 12, title = "Load an SV VCF", status = "primary", solidHeader = TRUE,
              fileInput("input_file", "Choose a VCF file", accept = c(".vcf", ".vcf.gz")),
              helpText("VCF INFO annotations, including AnnotSV fields, are expanded into table columns.")),
          box(
            width = 12,
            title = "Variants",
            textInput(
              "export_filename",
              "Export filename",
              value = paste0("SV_RareInsight_", Sys.Date()),
              placeholder = "Enter a filename without an extension"
            ),
            downloadButton("download_variant_html", "Download current view (HTML)"),
            tags$span(style = "margin-left:8px; color:#666;",
                      "The same filename is used by the CSV and Excel buttons below."),
            tags$hr(),
            DTOutput("variant_table")
          )
        )
      ),
      tabItem(tabName = "descriptions",
              box(width = 12, title = "AnnotSV column descriptions", DTOutput("column_description_table"))),
      # //REVIEW: add back in descriptions of the buttons? A separate button for each resource?
      tabItem(
        tabName = "search",
        fluidRow(
          box(width = 12, title = "Search genetic resources", status = "primary", solidHeader = TRUE,
              selectInput("search_type", "Search type",
                          choices = c("Gene", "Variant", "Disorder", "dbSNP", "ClinVar")),
              textInput("search_input", "Search term"),
              actionButton("search_button", "Construct resource links", class = "btn-primary"),
              tags$hr(), DTOutput("search_results")),
          box(width = 12, status = "warning",
              p("Educational use only. Results do not replace clinical or genetic consultation."))
        )
      )
    )
  )
)

server <- function(input, output, session) {
  filter_panel_state <- reactiveVal("open")

  observeEvent(input$toggle_filter, {
    shinyjs::addClass(id = "filterPanel", class = "collapsed")
    shinyjs::show(id = "toggle_tab")
    filter_panel_state("closed")
  })

  observeEvent(input$show_filter, {
    shinyjs::removeClass(id = "filterPanel", class = "collapsed")
    shinyjs::hide(id = "toggle_tab")
    filter_panel_state("open")
  })

  variants <- reactive({
    req(input$input_file)
    validate(need(grepl("\\.vcf(\\.gz)?$", input$input_file$name, ignore.case = TRUE),
                  "Upload a .vcf or .vcf.gz file."))
    validate(need(file.exists(input$input_file$datapath), "The uploaded file is unavailable."))
    withProgress(message = "Reading and parsing VCF", value = 0.2, {
      vcf <- tryCatch(
        withCallingHandlers(
          vcfR::read.vcfR(input$input_file$datapath, verbose = FALSE),
          warning = function(warning_condition) {
            # Some callers repeat SOURCE_IDS/SOURCES declarations in the VCF
            # header. vcfR can still parse these files, so silence only this
            # known duplicate-key warning and preserve every other warning.
            if (grepl("INFO key occurred more than once",
                      conditionMessage(warning_condition), fixed = TRUE)) {
              invokeRestart("muffleWarning")
            }
          }
        ),
        error = function(e) NULL
      )
      validate(need(!is.null(vcf), "The selected file could not be parsed as a VCF."))
      incProgress(0.5)
      vcf_to_data_frame(vcf)
    })
  })

  gene_column <- reactive({
    names(variants())[tolower(names(variants())) %in% c("gene_name", "genesymbol", "symbol")][1]
  })

  ## --- Populate dropdown dynamically with gene names ---
  observeEvent(variants(), {
    column <- gene_column()
    choices <- if (!is.na(column) && length(column)) {
      genes <- unlist(strsplit(as.character(variants()[[column]]), "[,;]"))
      sort(unique(trimws(genes[nzchar(trimws(genes)) & !is.na(genes)])))
    } else character()
    updateSelectizeInput(session, "gene_filter", choices = choices, selected = character(), server = TRUE)
  })

  ## --- Filtered Data ---
  filtered_variants <- reactive({
    data <- variants()
    selected <- input$gene_filter
    column <- gene_column()
    if (length(selected) && !is.na(column) && length(column)) {
      pattern <- paste(vapply(selected, function(x) gsub("([][{}()+*^$|\\\\?.])", "\\\\\\1", x), character(1)), collapse = "|")
      data <- data[grepl(pattern, data[[column]], ignore.case = TRUE), , drop = FALSE]
    }
    data
  })

  ## --- Clear Filter Button ---
  observeEvent(input$clear_filter, {
    updateSelectizeInput(session, "gene_filter", selected = character())
  })

  ## --- Render Variant Table ---
  output$variant_table <- renderDT({
    build_variant_table(filtered_variants())
  }, server = TRUE)

  output$download_variant_html <- downloadHandler(
    filename = function() {
      paste0(safe_export_filename(input$export_filename), ".html")
    },
    content = function(file) {
      data <- filtered_variants()

      # DT reports these indices after its search boxes and sorting have been
      # applied. If the browser has not reported them yet, export all rows from
      # the current gene-filtered reactive data set.
      displayed_rows <- input$variant_table_rows_all
      if (!is.null(displayed_rows)) {
        displayed_rows <- displayed_rows[
          !is.na(displayed_rows) & displayed_rows >= 1L & displayed_rows <= nrow(data)
        ]
        data <- data[displayed_rows, , drop = FALSE]
      }

      write_variant_html(data, file)
    },
    contentType = "text/html"
  )

  output$column_description_table <- renderDT({
    datatable(column_descriptions, filter = "top", rownames = FALSE,
              options = list(pageLength = 30, scrollX = TRUE))
  })

  search_links <- eventReactive(input$search_button, {
    validate(need(nzchar(trimws(input$search_input)), "Enter a search term first."))
    links <- construct_search_urls(input$search_type, input$search_input)
    links$Resource <- sprintf('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>',
                              links$URL, links$Resource)
    links
  }, ignoreInit = TRUE)

  output$search_results <- renderDT({
    datatable(search_links(), escape = FALSE, rownames = FALSE,
              colnames = c("Resource", "Constructed URL"),
              options = list(dom = "t", scrollX = TRUE))
  })
}

shinyApp(ui, server)
