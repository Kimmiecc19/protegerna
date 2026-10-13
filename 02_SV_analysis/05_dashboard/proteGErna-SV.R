# proteGErna: structural-variant viewer and protegerna resource search

# Locate shared assets when launched with Rscript, source(), or shiny::runApp().
dashboard_source_files <- unlist(lapply(sys.frames(), function(frame) frame$ofile))
dashboard_cli_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
dashboard_candidates <- unique(c(
  dirname(c(dashboard_source_files, dashboard_cli_file)), getwd(),
  file.path(getwd(), "code_dashboard"), file.path(getwd(), "5_dashboard", "code_dashboard")
))
dashboard_code_dir <- dashboard_candidates[file.exists(file.path(dashboard_candidates, "sv_dashboard_helpers.R"))][1]
if (is.na(dashboard_code_dir)) stop("Shared dashboard helpers not found: sv_dashboard_helpers.R")
source(file.path(dashboard_code_dir, "sv_dashboard_helpers.R"), local = TRUE)

required_packages <- c("shiny", "shinydashboard", "DT", "vcfR", "shinyjs", "httr", "jsonlite")
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

# Serve the dashboard logo reliably whether the app is launched from the
# project root or directly from the code directory.
logo_candidates <- c(
  file.path(getwd(), "code", "protegerna_logo.png"),
  file.path(getwd(), "protegerna_logo.png"),
  file.path(getwd(), "code", "www", "protegerna_logo.png"),
  file.path(getwd(), "www", "protegerna_logo.png")
)
logo_path <- logo_candidates[file.exists(logo_candidates)][1]
if (is.na(logo_path)) stop("Dashboard logo not found: protegerna_logo.png")
shiny::addResourcePath(
  "protegerna-assets",
  normalizePath(dirname(logo_path), winslash = "/", mustWork = TRUE)
)

# --- Helpers for constructing resource search URLs ---

# URL rules adapted from the protegerna search/resource functions.
# //REVIEW: should I add any other URLs? -> ClinGen, ACMG, DECIP_HER, DGV, dbVAR?
construct_search_urls <- function(search_type, search_term, gnomad_ensembl_id = NULL) {
  term <- trimws(search_term)
  encoded <- URLencode(term, reserved = TRUE)

  urls <- list(
    PubMed = paste0("https://pubmed.ncbi.nlm.nih.gov/?term=", encoded)
  )

  if (search_type %in% c("Gene", "Disorder", "Phenotype", "OMIM ID")) {
    urls$OMIM <- if (search_type == "OMIM ID" && grepl("^[0-9]+$", term)) {
      paste0("https://www.omim.org/entry/", encoded)
    } else {
      paste0("https://www.omim.org/search?index=entry&start=1&search=", encoded,
             "&sort=score+desc%2C+prefix_sort+desc&limit=10")
    }
  }
  if (search_type == "Gene") {
    urls$ClinVar <- paste0("https://www.ncbi.nlm.nih.gov/clinvar/?term=", encoded, "%5Bgene%5D&redir=gene")
    urls$dbSNP <- paste0("https://www.ncbi.nlm.nih.gov/snp/?term=", encoded)
    urls$GeneReviews <- paste0("https://www.ncbi.nlm.nih.gov/books/NBK1116/?term=", encoded, "%20gene%20review")
    urls$VarSome <- paste0("https://varsome.com/gene/hg38/", encoded)
    urls$LitVar <- paste0("https://www.ncbi.nlm.nih.gov/research/litvar2/docsum?text=", encoded)
    if (!is.null(gnomad_ensembl_id) && nzchar(gnomad_ensembl_id)) {
      urls$gnomAD <- paste0(
        "https://gnomad.broadinstitute.org/gene/",
        URLencode(gnomad_ensembl_id, reserved = TRUE), "?dataset=gnomad_sv_r4"
      )
    }
  } else if (search_type %in% c("Disorder", "Phenotype")) {
    urls$VarSome <- paste0("https://varsome.com/search-results/", encoded)
    urls$LitVar <- paste0("https://www.ncbi.nlm.nih.gov/research/litvar2/docsum?text=", encoded)
  }

  data.frame(Resource = names(urls), URL = unlist(urls, use.names = FALSE), stringsAsFactors = FALSE)
}

# Descriptions restored from 01_protegerna.R. These are used both beside the
# constructed resource links and in the resource guide shown in the dashboard.
resource_descriptions <- data.frame(
  Resource = c(
    "OMIM", "PubMed", "ClinVar", "gnomAD", "GeneReviews", "VarSome", "LitVar", "dbSNP"
  ),
  Description = c(
    "Online Mendelian Inheritance in Man (OMIM) is a comprehensive database of human genes and genetic phenotypes. It catalogues genetic disorders and their associated genes, including clinical descriptions, molecular mechanisms and inheritance patterns.",
    "PubMed is a repository of biomedical literature that supports evidence-based patient care, literature reviews and research into rare diseases.",
    "ClinVar is a public archive of reports and interpretations of the clinical significance of genomic variants, supporting diagnosis, treatment decisions and research.",
    "The Genome Aggregation Database (gnomAD) aggregates sequencing data from diverse populations and provides allele frequencies, functional annotations and population-specific patterns.",
    "GeneReviews provides expert-authored, peer-reviewed summaries of genetic conditions, genes and their associated diseases to inform patient care and research.",
    "VarSome integrates multiple data sources to annotate and interpret genetic variants and assess their potential clinical significance.",
    "LitVar links variants, genes and disorders mentioned in the biomedical literature to relevant publications.",
    "The Single Nucleotide Polymorphism Database (dbSNP) catalogues genetic variation and supports exploration of variants across populations."
  ),
  `Works with` = c(
    "Gene, Disorder, Phenotype or OMIM ID", "Gene, Disorder, Phenotype or OMIM ID",
    "Gene", "Gene", "Gene", "Gene, Disorder or Phenotype",
    "Gene, Disorder or Phenotype", "Gene"
  ),
  check.names = FALSE,
  stringsAsFactors = FALSE
)

resource_types <- list(
  OMIM = c("Gene", "Disorder", "Phenotype", "OMIM ID"),
  PubMed = c("Gene", "Disorder", "Phenotype", "OMIM ID"),
  ClinVar = "Gene", gnomAD = "Gene", GeneReviews = "Gene",
  VarSome = c("Gene", "Disorder", "Phenotype"),
  LitVar = c("Gene", "Disorder", "Phenotype"), dbSNP = "Gene"
)

resources_for_type <- function(search_type) {
  names(resource_types)[vapply(resource_types, function(types) search_type %in% types, logical(1))]
}

resolve_ensembl_gene <- function(symbol) {
  response <- httr::GET(
    paste0("https://rest.ensembl.org/lookup/symbol/homo_sapiens/",
           URLencode(trimws(symbol), reserved = TRUE)),
    httr::accept_json(), httr::timeout(10)
  )
  if (httr::http_error(response)) return(NA_character_)
  parsed <- jsonlite::fromJSON(httr::content(response, as = "text", encoding = "UTF-8"))
  if (is.null(parsed$id) || !nzchar(parsed$id)) NA_character_ else parsed$id
}

default_visible_columns <- c(
  "AnnotSV_ID", "SV_chrom", "SV_start", "SV_end", "SV_length", "SV_type", "REF", "ALT",
  "QUAL", "FILTER", "Gene_name", "Gene_count", "Frameshift", "P_gain_phen", "P_gain_hpo",
  "P_loss_phen", "P_loss_hpo", "P_ins_phen", "P_ins_hpo", "po_P_gain_phen", "po_P_gain_hpo",
  "po_P_loss_phen", "po_P_loss_hpo", "P_snvindel_phen", "B_gain_AFmax", "B_loss_AFmax",
  "ACMG", "OMIM_ID", "OMIM_phenotype", "OMIM_inheritance", "OMIM_morbid",
  "OMIM_morbid_candidate", "LOEUF_bin", "GnomAD_pLI", "Exomiser_gene_pheno_score",
  "Human_pheno_evidence", "AnnotSV_ranking_score", "ACMG_class"
)

# Build the same interactive table for both the live dashboard and HTML export.
build_variant_table <- function(data, page_length = 20, sample_group = "none") {
  # CSV and Excel run in the browser. Read the user's requested base filename
  # at click time, remove any extension/unsafe characters, and let DataTables
  # append the correct extension for the selected format.
  browser_export_filename <- JS(
    "function() {",
    "  var field = document.getElementById('export_filename');",
    "  var name = field ? field.value.trim() : '';",
    "  name = name.replace(/\\.(html?|csv|xlsx?)$/i, '');",
    "  name = name.replace(/[<>:\\\\/?*|\"\\x00-\\x1F]/g, '_').replace(/[. ]+$/g, '');",
    "  return name || 'SV_protegerna_export';",
    "}"
  )

  sample_columns <- intersect(attr(data, "sample_names"), names(data))
  selected_sample_columns <- switch(
    sample_group,
    case = sample_columns[grepl("^CASE-", sample_columns, ignore.case = TRUE)],
    control = sample_columns[grepl("^CTRL-", sample_columns, ignore.case = TRUE)],
    both = sample_columns[grepl("^(CASE|CTRL)-", sample_columns, ignore.case = TRUE)],
    character()
  )
  initially_visible <- unique(c(default_visible_columns, selected_sample_columns))
  hidden_columns <- which(!names(data) %in% initially_visible) - 1L
  table <- datatable(
    data,
    filter = "top",
    rownames = FALSE,
    extensions = c("Buttons", "FixedHeader", "FixedColumns"),
    options = list(
      scrollX = TRUE,
      scrollY = "calc(100vh - 300px)",
      scrollCollapse = TRUE,
      pageLength = page_length,
      fixedHeader = TRUE,
      fixedColumns = list(leftColumns = 1),
      columnDefs = if (length(hidden_columns)) list(list(targets = hidden_columns, visible = FALSE)) else list(),
      dom = "Bfrtip",
      buttons = list(
        "copy",
        list(extend = "csv", text = "CSV", filename = browser_export_filename),
        list(extend = "excel", text = "Excel", filename = browser_export_filename),
        list(extend = "colvis", text = "Show/Hide Columns")
      )
    )
  )

  for (column in intersect(c("B_loss_AFmax", "B_gain_AFmax"), names(data))) {
    table <- formatStyle(table, column,
                         backgroundColor = styleInterval(0.05, c("#61223B", "#007C7E")), color = "white")
  }
  if ("ACMG_class" %in% names(data)) {
    table <- formatStyle(table, "ACMG_class",
                         backgroundColor = styleEqual(c("1", "4", "5"),
                                                      c("#007C7E", "#8C6A2B", "#61223B")), color = "white")
  }
  if ("AnnotSV_ranking_score" %in% names(data)) {
    table <- formatStyle(table, "AnnotSV_ranking_score",
                         backgroundColor = styleInterval(0.89, c("#007C7E", "#61223B")), color = "white")
  }
  for (column in intersect(c("OMIM_morbid", "OMIM_morbid_candidate"), names(data))) {
    table <- formatStyle(table, column,
                         backgroundColor = styleEqual(c("no", "yes"), c("#007C7E", "#61223B")), color = "white")
  }
  table
}

safe_export_filename <- function(value, default = "SV_protegerna_export") {
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
      "B_loss_AFmax" = , "B_gain_AFmax" =
        if (!is.na(numeric_value)) if (numeric_value <= 0.05) "#61223B" else "#007C7E",
      "AnnotSV_ranking_score" =
        if (!is.na(numeric_value)) if (numeric_value <= 0.89) "#007C7E" else "#61223B",
      "ACMG_class" = unname(c("1" = "#007C7E", "4" = "#8C6A2B", "5" = "#61223B")[text]),
      "OMIM_morbid" = , "OMIM_morbid_candidate" = unname(c("no" = "#007C7E", "yes" = "#61223B")[tolower(text)]),
      NULL
    )
    if (is.null(colour) || is.na(colour)) "" else paste0(' style="background-color:', colour, ';color:#fff;"')
  }

  connection <- base::file(file, open = "wb")
  on.exit(close(connection), add = TRUE)
  writeLines(c(
    "<!doctype html>",
    '<html lang="en"><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "<title>proteGErna current table view</title>",
    "<style>body{font-family:Arial,sans-serif;margin:20px;color:#1A2F57} .toolbar{position:sticky;top:0;background:#fff;padding:10px 0;z-index:3} input{padding:7px;width:min(420px,70%)} button{padding:7px 12px;margin-left:6px;background:#007C7E;color:#fff;border:0}.table-wrap{overflow:auto;max-height:75vh;border:1px solid #ccc}table{border-collapse:collapse;font-size:12px;width:max-content;min-width:100%}th,td{border:1px solid #ddd;padding:6px;max-width:300px;overflow-wrap:anywhere}th{background:#1A2F57;color:white;position:sticky;top:0;z-index:2}tr:nth-child(even){background:#f7f3f4}@media print{.toolbar{display:none}.table-wrap{max-height:none;overflow:visible}th{position:static}}</style>",
    "</head><body>",
    "<h1>proteGErna current table view</h1>",
    '<div style="padding:12px;background:#fff3cd;border:1px solid #ffeeba"><strong>Educational use only.</strong> This automated annotation does not replace professional clinical interpretation, genetic counselling or medical care.</div>',
    paste0("<p>Exported: ", escape_html(format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
           " &nbsp; Rows: ", nrow(data), "</p>"),
    '<div class="toolbar"><label for="tableSearch">Search this report: </label><input id="tableSearch" type="search" placeholder="Type to filter rows..."><button onclick="window.print()">Print</button></div>',
    '<div class="table-wrap"><table id="variantTable"><thead><tr>',
    paste0("<th>", escape_html(names(data)), "</th>", collapse = ""),
    "</tr></thead><tbody>"
  ), connection, useBytes = TRUE)

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

  writeLines(c(
    "</tbody></table></div>",
    "<script>document.getElementById('tableSearch').addEventListener('input',function(){var q=this.value.toLowerCase();document.querySelectorAll('#variantTable tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().includes(q)?'':'none';});});</script>",
    "</body></html>"
  ), connection, useBytes = TRUE)
}

# --- Shiny UI and server logic ---
ui <- dashboardPage(
  dashboardHeader(
    title = tags$div(
      class = "dashboard-brand-logo",
      tags$img(src = "protegerna-assets/protegerna_logo.png", alt = "proteGErna-SV")
    )
  ),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Overview", tabName = "overview", icon = icon("chart-bar")),
      menuItem("Structural Variants", tabName = "variants", icon = icon("table")),
      menuItem("Column Descriptions", tabName = "descriptions", icon = icon("book")),
      menuItem("Resource Search", tabName = "search", icon = icon("search"))
    )
  ),
  dashboardBody(
    useShinyjs(),
    tags$head(
      tags$style(HTML("
        :root { --maroon:#61223B; --dark-green:#007C7E; --navy:#1A2F57;
          --copper:#B84F00; --gold:#8C6A2B; }
        .skin-blue .main-header .logo { background-color:#DCEAF5; color:var(--navy); }
        .skin-blue .main-header .logo:hover { background-color:#C9DFEF; }
        .dashboard-brand-logo { position:relative; width:100%; height:50px; overflow:hidden; }
        .dashboard-brand-logo img { position:absolute; width:230px; height:230px;
          max-width:none; left:-20px; top:-78px; }
        .skin-blue .main-header .navbar { background-color:var(--navy); }
        .skin-blue .main-sidebar, .skin-blue .wrapper { background-color:var(--navy); }
        .skin-blue .sidebar-menu > li > a { color:#fff; }
        .skin-blue .sidebar-menu > li.active > a,
        .skin-blue .sidebar-menu > li:hover > a { background-color:var(--maroon); border-left-color:var(--gold); }
        .main-header { position:fixed; top:0; width:100%; z-index:1100; }
        .main-sidebar { position:fixed; padding-top:50px; }
        .content-wrapper { background:#f7f3f4; padding-top:50px; }
        .box.box-primary { border-top-color:var(--maroon); }
        .box.box-info { border-top-color:var(--dark-green); }
        .box.box-warning { border-top-color:var(--gold); }
        .box.box-solid.box-primary > .box-header { background:var(--maroon); }
        .box.box-solid.box-info > .box-header { background:var(--dark-green); }
        .box.box-solid.box-warning > .box-header { background:var(--gold); color:#fff; }
        .btn-primary { background-color:var(--dark-green); border-color:#006668; }
        .btn-primary:hover, .btn-primary:focus { background-color:#006668; border-color:#005557; }
        .btn-info { background-color:var(--navy); border-color:#132441; }
        .btn-warning { background-color:var(--copper); border-color:#963F00; color:#fff; }
        .bg-aqua { background-color:var(--maroon) !important; }
        .bg-green { background-color:var(--dark-green) !important; }
        .bg-yellow { background-color:var(--gold) !important; color:#fff !important; }
        .bg-purple { background-color:var(--navy) !important; }
        .pagination > .active > a, .pagination > .active > span {
          background-color:var(--dark-green); border-color:var(--dark-green); }
        /* FixedColumns supplies its own white header background. Keep the
           heading readable on the pinned column as well as ordinary columns. */
        table.dataTable thead th {
          background-color:var(--navy) !important;
          color:#fff !important;
        }
        .dt-button { background:var(--dark-green) !important; color:#fff !important;
          border-color:#006668 !important; }
        .dataTables_wrapper { overflow-x: auto; }
        .dataTables_scrollHead { position:sticky; top:50px; z-index:20; background:#fff; }
        .dataTables_scrollBody { border-bottom:1px solid #ddd; }
        .floating-filter {
          position: fixed;
          top: 60px;
          right: 20px;
          width: 280px;
          max-height: calc(100vh - 80px);
          overflow-y: auto;
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
          background: var(--dark-green);
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
        .resource-card { border:1px solid #d9e2e8; border-left:4px solid var(--copper);
          border-radius:5px; padding:12px; margin:10px 0; background:#fff; }
        .resource-card-header { display:flex; align-items:center; justify-content:space-between; gap:12px; }
        .resource-card-header h4 { margin:0 0 8px 0; }
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
        selectizeInput("sv_type_filter", "SV Type(s):", choices = NULL, multiple = TRUE),
        selectizeInput("chrom_filter", "Chromosome(s):", choices = NULL, multiple = TRUE),
        selectizeInput("acmg_filter", "ACMG Class(es):", choices = NULL, multiple = TRUE),
        selectizeInput("sample_filter", "Sample(s):", choices = NULL, multiple = TRUE),
        numericInput("start_position", "Minimum Start Coordinate:", value = NA, min = 0),
        numericInput("end_position", "Maximum End Coordinate:", value = NA, min = 0),
        numericInput("min_length", "Minimum SV Length:", value = NA, min = 0),
        numericInput("max_length", "Maximum SV Length:", value = NA, min = 0),
        numericInput("max_af", "Maximum Benign AF:", value = NA, min = 0, max = 1, step = 0.001),
        numericInput("min_ranking", "Minimum AnnotSV Ranking Score:", value = NA, step = 0.01),
        selectInput("omim_filter", "OMIM Morbidity:",
                    choices = c("All" = "all", "Morbid" = "yes", "Not Morbid" = "no")),
        selectInput("pass_filter", "Filter Status:",
                    choices = c("All" = "all", "PASS Only" = "pass", "Non-PASS Only" = "nonpass")),
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
        tabName = "overview",
        fluidRow(
          box(width = 12, title = "Load An SV VCF", status = "primary", solidHeader = TRUE,
              radioButtons("input_method", "VCF Source",
                           choices = c("Upload File" = "upload", "Local File Path" = "local"),
                           selected = "upload", inline = TRUE),
              conditionalPanel(
                condition = "input.input_method == 'upload'",
                fileInput("input_file", "Choose A VCF File", accept = c(".vcf", ".vcf.gz"))
              ),
              conditionalPanel(
                condition = "input.input_method == 'local'",
                textInput("local_vcf_path", "Local VCF Path",
                          placeholder = "C:/data/sample.annotated.vcf.gz"),
                actionButton("load_local_vcf", "Load Local VCF", class = "btn-primary"),
                helpText("The path must be accessible from the computer running this Shiny app.")
              ),
              helpText("Uncompressed .vcf and compressed .vcf.gz files are supported. VCF INFO annotations, including AnnotSV fields, are expanded into table columns."))
        ),
        fluidRow(
          valueBoxOutput("summary_variants", width = 3),
          valueBoxOutput("summary_samples", width = 3),
          valueBoxOutput("summary_types", width = 3),
          valueBoxOutput("summary_annotations", width = 3)
        ),
        fluidRow(
          box(width = 12, title = "Upload Summary", collapsible = TRUE,
              DTOutput("upload_summary"))
        ),
        fluidRow(
          valueBoxOutput("overview_variants", width = 3),
          valueBoxOutput("overview_genes", width = 3),
          valueBoxOutput("overview_samples", width = 3),
          valueBoxOutput("overview_pass", width = 3)
        ),
        fluidRow(
          box(width = 6, title = "Structural Variant Types", plotOutput("sv_type_plot", height = 300)),
          box(width = 6, title = "ACMG Classifications", plotOutput("acmg_plot", height = 300)),
          box(width = 6, title = "SV Length Distribution", plotOutput("length_plot", height = 300)),
          box(width = 6, title = "Variants By Chromosome", plotOutput("chromosome_plot", height = 300))
        ),
        box(width = 12, status = "warning",
            p(strong("Educational use only."),
              "Charts summarize automated annotations and do not constitute clinical interpretation."))
      ),
      tabItem(
        tabName = "variants",
        fluidRow(
          box(
            width = 12,
            title = "Variants",
            textInput(
              "export_filename",
              "Export Filename",
              value = paste0("SV_protegerna_", Sys.Date()),
              placeholder = "Enter a filename without an extension"
            ),
            downloadButton("download_variant_html", "Download Current View (HTML)"),
            tags$span(style = "margin-left:8px; color:#666;",
                      "The same filename is used by the CSV and Excel buttons below."),
            tags$div(class = "alert alert-warning", style = "margin-top:12px;",
                     tags$strong("Educational use only. "),
                     "Automated annotations do not replace clinical interpretation or genetic consultation. Please use with caution."),
            radioButtons(
              "sample_column_group", "Sample Columns",
              choices = c("Hide Sample Columns" = "none", "CASE" = "case",
                          "CTRL" = "control", "CASE And CTRL" = "both"),
              selected = "none", inline = TRUE
            ),
            tags$hr(),
            DTOutput("variant_table")
          )
        )
      ),
      tabItem(tabName = "descriptions",
              box(width = 12, title = "AnnotSV Column Descriptions",
                  checkboxInput("descriptions_present_only", "Show Only Fields Present In The Uploaded VCF", TRUE),
                  selectInput("description_category", "Category", choices = "All"),
                  DTOutput("column_description_table"))),
      tabItem(
        tabName = "search",
        fluidRow(
          box(width = 12, title = "Search Genetic Resources", status = "primary", solidHeader = TRUE,
              selectInput("search_type", "Search Type",
                          choices = c("Gene", "Disorder", "Phenotype", "OMIM ID")),
              textInput("search_input", "Search Term"),
              checkboxGroupInput("selected_resources", "Resources", choices = character()),
              actionButton("search_button", "Construct Resource Links", class = "btn-primary"),
              tags$hr(), uiOutput("search_results")),
          box(width = 12, status = "warning",
              p("Educational use only. Results do not replace clinical or genetic consultation."))
        )
      )
    )
  )
)

server <- function(input, output, session) {
  find_column <- function(data, candidates) {
    hit <- names(data)[tolower(names(data)) %in% tolower(candidates)]
    if (length(hit)) hit[[1]] else NA_character_
  }

  split_values <- function(values) {
    values <- unlist(strsplit(as.character(values), "[,;]"))
    sort(unique(trimws(values[!is.na(values) & nzchar(trimws(values))])))
  }

  sv_lengths <- function(data) {
    columns <- names(data)[tolower(names(data)) %in% c("sv_length", "svlen")]
    if (!length(columns)) return(rep(NA_real_, nrow(data)))
    result <- rep(NA_real_, nrow(data))
    for (column in columns) {
      values <- sub(",.*$", "", as.character(data[[column]]))
      parsed <- abs(suppressWarnings(as.numeric(values)))
      result[is.na(result)] <- parsed[is.na(result)]
    }
    result
  }

  observeEvent(input$toggle_filter, {
    shinyjs::addClass(id = "filterPanel", class = "collapsed")
    shinyjs::show(id = "toggle_tab")
  })

  observeEvent(input$show_filter, {
    shinyjs::removeClass(id = "filterPanel", class = "collapsed")
    shinyjs::hide(id = "toggle_tab")
  })

  selected_vcf_path <- reactive({
    if (identical(input$input_method, "local")) {
      req(input$load_local_vcf)
      requested_path <- trimws(isolate(input$local_vcf_path))
      validate(need(nzchar(requested_path), "Enter a local VCF path."))
      validate(need(grepl("\\.vcf(\\.gz)?$", requested_path, ignore.case = TRUE),
                    "The local file must end in .vcf or .vcf.gz."))
      validate(need(file.exists(requested_path), "The local VCF path does not exist or is not accessible."))
      normalizePath(requested_path, winslash = "/", mustWork = TRUE)
    } else {
      req(input$input_file)
      validate(need(grepl("\\.vcf(\\.gz)?$", input$input_file$name, ignore.case = TRUE),
                    "Upload a .vcf or .vcf.gz file."))
      input$input_file$datapath
    }
  })

  data_source_ready <- reactive({
    path <- selected_vcf_path()
    is.character(path) && length(path) == 1L && file.exists(path)
  })

  variants <- reactive({
    req(data_source_ready())
    vcf_path <- selected_vcf_path()
    validate(need(file.exists(vcf_path), "The selected VCF is unavailable."))
    withProgress(message = "Reading and parsing VCF", value = 0.2, {
      vcf <- tryCatch(
        withCallingHandlers(
          vcfR::read.vcfR(vcf_path, verbose = FALSE),
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
        error = function(error_condition) NULL
      )
      validate(need(!is.null(vcf), "The selected file could not be parsed as a VCF."))
      incProgress(0.5)
      vcf_to_data_frame(vcf)
    })
  })

  gene_column <- reactive({
    req(data_source_ready())
    find_column(variants(), c("Gene_name", "GeneSymbol", "SYMBOL"))
  })

  ## --- Populate filter dropdowns from the loaded VCF ---
  observeEvent(variants(), {
    data <- variants()
    column_choices <- function(column) if (!is.na(column)) split_values(data[[column]]) else character()
    choices <- list(
      gene_filter = column_choices(gene_column()),
      sv_type_filter = column_choices(find_column(data, c("SV_type", "SVTYPE"))),
      chrom_filter = column_choices(find_column(data, c("SV_chrom", "CHROM"))),
      acmg_filter = column_choices(find_column(data, "ACMG_class")),
      sample_filter = attr(data, "sample_names")
    )
    for (id in names(choices)) {
      updateSelectizeInput(session, id, choices = choices[[id]], selected = character(), server = TRUE)
    }
    updateSelectInput(session, "description_category",
                      choices = c("All", sort(unique(column_descriptions$Category))), selected = "All")
  })

  ## --- Filtered Data ---
  filtered_variants <- reactive({
    req(data_source_ready())
    data <- variants()
    match_any <- function(values, selected) {
      if (!length(selected)) return(rep(TRUE, length(values)))
      pattern <- paste(vapply(selected, function(x) gsub("([][{}()+*^$|\\\\?.])", "\\\\\\1", x), character(1)), collapse = "|")
      !is.na(values) & grepl(pattern, values, ignore.case = TRUE)
    }
    gene <- gene_column()
    if (!is.na(gene)) data <- data[match_any(data[[gene]], input$gene_filter), , drop = FALSE]
    type_column <- find_column(data, c("SV_type", "SVTYPE"))
    if (!is.na(type_column) && length(input$sv_type_filter))
      data <- data[data[[type_column]] %in% input$sv_type_filter, , drop = FALSE]
    chrom_column <- find_column(data, c("SV_chrom", "CHROM"))
    if (!is.na(chrom_column) && length(input$chrom_filter))
      data <- data[data[[chrom_column]] %in% input$chrom_filter, , drop = FALSE]
    acmg_column <- find_column(data, "ACMG_class")
    if (!is.na(acmg_column) && length(input$acmg_filter))
      data <- data[data[[acmg_column]] %in% input$acmg_filter, , drop = FALSE]
    start_column <- find_column(data, c("SV_start", "POS"))
    end_column <- find_column(data, c("SV_end", "END"))
    if (!is.na(start_column) && !is.na(input$start_position)) {
      coordinates <- suppressWarnings(as.numeric(data[[start_column]]))
      data <- data[!is.na(coordinates) & coordinates >= input$start_position, , drop = FALSE]
    }
    if (!is.na(end_column) && !is.na(input$end_position)) {
      coordinates <- suppressWarnings(as.numeric(data[[end_column]]))
      data <- data[!is.na(coordinates) & coordinates <= input$end_position, , drop = FALSE]
    }
    has_length <- any(tolower(names(data)) %in% c("sv_length", "svlen"))
    if (has_length && (!is.na(input$min_length) || !is.na(input$max_length))) {
      lengths <- sv_lengths(data)
      data <- data[!is.na(lengths) & (is.na(input$min_length) | lengths >= input$min_length) &
                     (is.na(input$max_length) | lengths <= input$max_length), , drop = FALSE]
    }
    if (!is.na(input$max_af)) {
      af_columns <- intersect(c("B_gain_AFmax", "B_loss_AFmax"), names(data))
      if (length(af_columns)) {
        af <- do.call(pmax, c(lapply(data[af_columns], function(x) suppressWarnings(as.numeric(x))), list(na.rm = TRUE)))
        af[!is.finite(af)] <- NA_real_
        data <- data[is.na(af) | af <= input$max_af, , drop = FALSE]
      }
    }
    ranking_column <- find_column(data, "AnnotSV_ranking_score")
    if (!is.na(ranking_column) && !is.na(input$min_ranking)) {
      ranking <- suppressWarnings(as.numeric(data[[ranking_column]]))
      data <- data[!is.na(ranking) & ranking >= input$min_ranking, , drop = FALSE]
    }
    omim_column <- find_column(data, "OMIM_morbid")
    if (!is.na(omim_column) && input$omim_filter != "all")
      data <- data[tolower(as.character(data[[omim_column]])) == input$omim_filter, , drop = FALSE]
    filter_column <- find_column(data, "FILTER")
    if (!is.na(filter_column) && input$pass_filter != "all") {
      is_pass <- is.na(data[[filter_column]]) | data[[filter_column]] %in% c("PASS", ".")
      data <- data[if (input$pass_filter == "pass") is_pass else !is_pass, , drop = FALSE]
    }
    if (length(input$sample_filter)) {
      available <- intersect(input$sample_filter, names(data))
      if (length(available)) {
        carried <- Reduce(`|`, lapply(data[available], function(sample_values) {
          mapply(is_carrier, data$FORMAT, sample_values, USE.NAMES = FALSE)
        }))
        data <- data[carried, , drop = FALSE]
      }
    }
    attr(data, "sample_names") <- attr(variants(), "sample_names")
    data
  })

  ## --- Clear Filter Button ---
  observeEvent(input$clear_filter, {
    for (id in c("gene_filter", "sv_type_filter", "chrom_filter", "acmg_filter", "sample_filter"))
      updateSelectizeInput(session, id, selected = character())
    for (id in c("start_position", "end_position", "min_length", "max_length", "max_af", "min_ranking"))
      updateNumericInput(session, id, value = NA)
    for (id in c("omim_filter", "pass_filter"))
      updateSelectInput(session, id, selected = "all")
  })

  ## --- Render Variant Table ---
  output$variant_table <- renderDT({
    build_variant_table(filtered_variants(), sample_group = input$sample_column_group)
  }, server = TRUE)

  sample_count <- reactive({
    req(data_source_ready())
    length(attr(variants(), "sample_names"))
  })
  unique_gene_count <- reactive({
    column <- gene_column()
    if (is.na(column)) 0L else length(split_values(filtered_variants()[[column]]))
  })
  pass_count <- reactive({
    data <- filtered_variants()
    column <- find_column(data, "FILTER")
    if (is.na(column)) NA_integer_ else sum(is.na(data[[column]]) | data[[column]] %in% c("PASS", "."))
  })

  output$summary_variants <- renderValueBox({
    req(data_source_ready())
    valueBox(nrow(variants()), "Uploaded Variants", icon = icon("dna"), color = "aqua")
  })
  output$summary_samples <- renderValueBox({
    req(data_source_ready())
    valueBox(sample_count(), "Samples", icon = icon("users"), color = "green")
  })
  output$summary_types <- renderValueBox({
    req(data_source_ready())
    column <- find_column(variants(), c("SV_type", "SVTYPE"))
    valueBox(if (is.na(column)) 0 else length(unique(na.omit(variants()[[column]]))), "SV Types", icon = icon("shapes"), color = "yellow")
  })
  output$summary_annotations <- renderValueBox({
    req(data_source_ready())
    valueBox(sum(names(variants()) %in% column_descriptions$Column), "Recognised Annotations", icon = icon("tags"), color = "purple")
  })
  output$overview_variants <- renderValueBox({
    req(data_source_ready())
    valueBox(nrow(filtered_variants()), "Filtered Variants", icon = icon("filter"), color = "aqua")
  })
  output$overview_genes <- renderValueBox({
    req(data_source_ready())
    valueBox(unique_gene_count(), "Genes", icon = icon("dna"), color = "green")
  })
  output$overview_samples <- renderValueBox({
    req(data_source_ready())
    valueBox(sample_count(), "Samples", icon = icon("users"), color = "yellow")
  })
  output$overview_pass <- renderValueBox({
    req(data_source_ready())
    valueBox(ifelse(is.na(pass_count()), "N/A", pass_count()), "PASS Variants", icon = icon("check"), color = "purple")
  })

  output$upload_summary <- renderDT({
    req(data_source_ready())
    data <- variants()
    recognised <- intersect(names(data), column_descriptions$Column)
    unrecognised <- setdiff(names(data), c(column_descriptions$Column, attr(data, "sample_names")))
    chromosome_column <- find_column(data, c("SV_chrom", "CHROM"))
    type_column <- find_column(data, c("SV_type", "SVTYPE"))
    upload_filter_column <- find_column(data, "FILTER")
    upload_pass <- if (is.na(upload_filter_column)) "N/A" else
      sum(is.na(data[[upload_filter_column]]) | data[[upload_filter_column]] %in% c("PASS", "."))
    detected_sources <- c(
      if (any(grepl("^OMIM", names(data)))) "OMIM",
      if (any(grepl("^(P_|B_|po_P_|po_B_)", names(data)))) "AnnotSV evidence",
      if (any(grepl("^Exomiser", names(data)))) "Exomiser",
      if (any(grepl("^(GnomAD|gnomAD)", names(data)))) "gnomAD",
      if ("ACMG_class" %in% names(data)) "ACMG classification"
    )
    source_path <- selected_vcf_path()
    source_label <- if (identical(input$input_method, "local")) source_path else input$input_file$name
    source_size_mb <- round(file.info(source_path)$size / 1024^2, 2)
    summary <- data.frame(
      Metric = c("Source", "Compressed Input", "File Size (MB)", "Rows", "Columns", "Samples", "PASS Variants", "Chromosomes", "SV Types",
                 "Detected Annotation Sources", "Recognised AnnotSV Fields", "Other Fields",
                 "Missing Default Display Fields"),
      Value = c(source_label, grepl("\\.vcf\\.gz$", source_label, ignore.case = TRUE), source_size_mb,
                nrow(data), ncol(data), sample_count(), upload_pass,
                if (is.na(chromosome_column)) "N/A" else length(unique(na.omit(data[[chromosome_column]]))),
                if (is.na(type_column)) "N/A" else paste(sort(unique(na.omit(data[[type_column]]))), collapse = ", "),
                if (length(detected_sources)) paste(detected_sources, collapse = ", ") else "None recognised",
                length(recognised), length(unrecognised),
                paste(setdiff(default_visible_columns, names(data)), collapse = ", ")),
      stringsAsFactors = FALSE
    )
    datatable(summary, rownames = FALSE, options = list(dom = "t", ordering = FALSE))
  })

  draw_count_plot <- function(data, column, title = NULL) {
    if (is.na(column) || !nrow(data)) return(plot.new())
    counts <- sort(table(data[[column]], useNA = "no"), decreasing = TRUE)
    if (!length(counts)) return(plot.new())
    par(mar = c(7, 4, 2, 1))
    barplot(counts, las = 2, col = "#007C7E", border = NA, ylab = "Variants", main = title)
  }
  output$sv_type_plot <- renderPlot({
    data <- filtered_variants(); draw_count_plot(data, find_column(data, c("SV_type", "SVTYPE")))
  })
  output$acmg_plot <- renderPlot({
    data <- filtered_variants(); draw_count_plot(data, find_column(data, "ACMG_class"))
  })
  output$chromosome_plot <- renderPlot({
    data <- filtered_variants(); draw_count_plot(data, find_column(data, c("SV_chrom", "CHROM")))
  })
  output$length_plot <- renderPlot({
    data <- filtered_variants()
    if (!nrow(data)) return(plot.new())
    values <- sv_lengths(data); values <- values[is.finite(values) & values > 0]
    if (!length(values)) return(plot.new())
    hist(log10(values), breaks = "FD", col = "#61223B", border = "white",
         xlab = "log10 SV Length (bp)", main = "")
  })

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

  filtered_descriptions <- reactive({
    descriptions <- column_descriptions
    if (isTRUE(input$descriptions_present_only)) {
      req(data_source_ready())
      descriptions <- descriptions[descriptions$Column %in% names(variants()), , drop = FALSE]
    }
    if (!is.null(input$description_category) && input$description_category != "All")
      descriptions <- descriptions[descriptions$Category == input$description_category, , drop = FALSE]
    descriptions
  })
  output$column_description_table <- renderDT({
    datatable(filtered_descriptions(), filter = "top", rownames = FALSE,
              options = list(pageLength = 30, scrollX = TRUE))
  })

  observeEvent(input$search_type, {
    available <- resources_for_type(input$search_type)
    updateCheckboxGroupInput(session, "selected_resources", choices = available, selected = available)
  }, ignoreInit = FALSE)

  resource_card <- function(resource, url) {
    row <- resource_descriptions[resource_descriptions$Resource == resource, , drop = FALSE]
    action <- tags$a(class = "btn btn-primary", href = url, target = "_blank", rel = "noopener noreferrer",
                     icon("up-right-from-square"), paste("Open", resource))
    tags$div(
      class = "resource-card ",
      tags$div(class = "resource-card-header", tags$h4(resource), action),
      tags$p(row$Description), tags$small(tags$strong("Works With: "), row[["Works with"]])
    )
  }

  search_links <- eventReactive(input$search_button, {
    validate(need(nzchar(trimws(input$search_input)), "Enter a search term first."))
    selected <- intersect(input$selected_resources, resources_for_type(input$search_type))
    validate(need(length(selected), "Select at least one available resource."))
    ensembl_id <- NULL
    if (input$search_type == "Gene" && "gnomAD" %in% selected) {
      ensembl_id <- tryCatch(resolve_ensembl_gene(input$search_input), error = function(error_condition) NA_character_)
      if (is.na(ensembl_id)) {
        showNotification("gnomAD was omitted because the gene could not be resolved to an Ensembl ID.", type = "warning")
      }
    }
    links <- construct_search_urls(input$search_type, input$search_input, ensembl_id)
    links <- links[links$Resource %in% selected, , drop = FALSE]
    validate(need(nrow(links), "No links could be constructed for the selected resources."))
    links$Description <- resource_descriptions$Description[match(links$Resource, resource_descriptions$Resource)]
    links
  }, ignoreInit = TRUE)

  output$search_results <- renderUI({
    links <- search_links()
    tagList(lapply(seq_len(nrow(links)), function(index) {
      resource_card(links$Resource[[index]], links$URL[[index]])
    }))
  })
}

shinyApp(ui, server)
