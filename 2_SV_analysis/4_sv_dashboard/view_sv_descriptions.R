#Check if packages are downloaded
if (!require("shiny"))
  install.packages("shiny")
if (!require("vcfR"))
  install.packages("vcfR")
if (!require("DT"))
  install.packages("DT")
if (!require("shinyjs"))
  install.packages("shinyjs")
if (!require("shinythemes"))
  install.packages("shinythemes")
if (!require("progress"))
  install.packages("progress")

# Load packages
library(shiny)
library(vcfR)
library(DT)
library(shinythemes)
library(shinyjs)
library(progress)

ui <- fluidPage(
  theme = shinytheme("flatly"),
  useShinyjs(),
  
  titlePanel("Structural Variant Dashboard"),
  
  # --- Floating Top-Right Filter Panel ---
  tags$div(
    id = "filterPanel",
    class = "floating-filter",
    wellPanel(
      style = "padding: 10px; margin-bottom: 0;",
      actionButton("toggle_filter", "Hide Filters", class = "btn btn-info btn-xs", style = "width:100%; margin-bottom:5px;"),
      selectizeInput(
        "gene_filter",
        "Gene(s):",
        choices = NULL,
        multiple = TRUE,
        options = list(placeholder = 'Type or select genes...')
      ),
      actionButton("clear_filter", "Clear", class = "btn btn-warning btn-xs", style = "width:100%; margin-top:5px;")
    )
  ),
  
  # --- Main Panel ---
  fluidRow(
    column(
      width = 12,
      id = "main_panel",
      tabsetPanel(
        tabPanel("Variants", DTOutput("variant_table")),
        
        # --- New Column Description Tab ---
        tabPanel("Column Description",
                 tags$div(style = "padding:20px;",
                          h4("AnnotSV Column Descriptions"),
                          DT::dataTableOutput("column_description_table")
                 )
        )
      )
    )
  ),
  
  # --- Filter Panel collapse styling ---
  tags$style(HTML("
    .floating-filter {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 220px;
      z-index: 1001;
      background: #f7f7f7;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      transition: top 0.4s, opacity 0.4s;
      opacity: 1;
    }
    .floating-filter.collapsed {
      top: -180px;
      opacity: 0.1;
      pointer-events: none;
    }
    #toggle_tab {
      position: fixed;
      top: 20px;
      right: 20px;
      background: #5bc0de;
      color: white;
      padding: 5px 12px;
      border-radius: 0 5px 5px 0;
      font-weight: bold;
      cursor: pointer;
      z-index: 1002;
      display: none;
    }
    .floating-filter.collapsed + #toggle_tab {
      display: block !important;
    }
    table.dataTable td {
      white-space: normal !important;
      word-wrap: break-word;
      max-width: 300px;
    }
    table.dataTable th {
      white-space: nowrap;
    }
  "))
)


server <- function(input, output, session) {
  
  ## --- Add a floating toggle tab ---
  observe({
    runjs("
      if (!document.getElementById('toggle_tab')) {
        var toggle = document.createElement('div');
        toggle.id = 'toggle_tab';
        toggle.innerText = 'Show Filters';
        document.body.appendChild(toggle);
        toggle.style.display = 'none';
        toggle.addEventListener('click', function(){
          Shiny.setInputValue('toggle_filter', Math.random());
        });
      }
    ")
  })
  
  ## ---- Filter Panel Toggle ----
  filterPanel_state <- reactiveVal("open")
  
  observeEvent(input$toggle_filter, {
    if (filterPanel_state() == "open") {
      shinyjs::addClass(id = "filterPanel", class = "collapsed")
      runjs("document.getElementById('toggle_tab').style.display = 'block';")
      filterPanel_state("closed")
    } else {
      shinyjs::removeClass(id = "filterPanel", class = "collapsed")
      runjs("document.getElementById('toggle_tab').style.display = 'none';")
      filterPanel_state("open")
    }
  })
  
  #TODO: Trim columns first then be able to add back in 
  ## --- Read SV VCF File (From AnnotSV)---
  vcf_data <- reactive({
    # Show progress while loading VCF and processing data
    vcf <- NULL
    shiny::withProgress(
      message = 'Loading variants...',
      detail = 'This may take a while...',
      value = 0,
      {
        vcf <- read.vcfR("~/2026 PhD/protegerna/2_SV_analysis/sv_dashboard/octopusv_manta_tiddit_30062026/merged/manta_tiddit.intersect.vcf", verbose = TRUE)
        # Artificial delay to simulate processing (remove or adjust as needed)
        Sys.sleep(1) # Still not staying until loading complete. Remove completely? Or increase sys.sleep
      }
    )
    vcf
  })
  
  ## --- Process SV Data ---
  processed_data <- reactive({
    vcf <- vcf_data()
    fix_df <- as.data.frame(vcf@fix, stringsAsFactors = FALSE)
    
    parse_info_field <- function(info) {
      kvs <- unlist(strsplit(info, ";"))
      out <- list()
      for (kv in kvs) {
        parts <- strsplit(kv, "=")[[1]]
        if (length(parts) == 2) {
          out[[parts[1]]] <- parts[2]
        } else {
          out[[parts[1]]] <- NA
        }
      }
      return(out)
    }
    
    info_list <- lapply(fix_df$INFO, parse_info_field)
    all_info_keys <- unique(unlist(lapply(info_list, names)))
    
    info_df <- as.data.frame(do.call(rbind, lapply(info_list, function(row) {
      sapply(all_info_keys, function(k) ifelse(!is.null(row[[k]]), row[[k]], NA))
    })), stringsAsFactors = FALSE)
    
    gt <- vcf@gt
    # Keep FORMAT/sample columns as-is (do not split by ":")
    sample_df <- if (ncol(gt) > 1) as.data.frame(gt[, -1, drop = FALSE], stringsAsFactors = FALSE) else NULL
    colnames(sample_df) <- if (!is.null(sample_df)) colnames(gt)[-1] else character(0)
    
    
    combined_df <- cbind(
      fix_df[, c("CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER")],
      info_df,
      if (!is.null(sample_df)) sample_df else NULL
    )
    
    combined_df[combined_df == "." | combined_df == ""] <- NA
    combined_df
  })
  
  ## --- Populate dropdown dynamically with gene names ---
  observe({
    df <- processed_data()
    if ("Gene_name" %in% colnames(df)) {
      updateSelectizeInput(session, "gene_filter",
                           choices = sort(unique(df$Gene_name)),
                           server = TRUE)
    }
  })
  
  ## --- Filtered Data ---
  filtered_data <- reactive({
    df <- processed_data()
    if (!is.null(input$gene_filter) && length(input$gene_filter) > 0) {
      if ("Gene_name" %in% colnames(df)) {
        df <- df[df$Gene_name %in% input$gene_filter, ]
      }
    }
    df
  })
  
  ## --- Clear Filter Button ---
  observeEvent(input$clear_filter, {
    updateSelectizeInput(session, "gene_filter", selected = character(0))
  })
  
  ## --- Render Variant Table ---
  output$variant_table <- DT::renderDataTable({
    df <- filtered_data()
    dt <- datatable(
      df,
      escape = FALSE,
      options = list(
        scrollX = TRUE,
        scrollY = "600px",
        paging = TRUE,
        pageLength = 20, # Adjust as needed or add an option to select 
        fixedHeader = TRUE,
        searchHighlight = TRUE, # Highlights matching search term in table
        autoWidth = TRUE,
        dom = 'Bfrtip',
        buttons = list(
          'copy', 'csv', 'excel', # Export table in two formats (current view)
          list(extend = "colvis", text = "Show/Hide Columns") # Select columns to hide or show in table
        )
      ),
      filter = "top",
      rownames = FALSE,
      extensions = c("Buttons", "FixedHeader", "FixedColumns")
    )
    dt <- DT::formatStyle(
      dt,
      "B_loss_AFmax",
      backgroundColor = DT::styleInterval(
        0.05, c("#FB7575", "#6FF97C")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "B_gain_AFmax",
      backgroundColor = DT::styleInterval(
        0.05, c("#FB7575", "#6FF97C")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "ACMG_class",
      backgroundColor = DT::styleEqual(
        c("1", "4", "5"), c("#6FF97C", "#FCCF8C", "#FB7575")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "AnnotSV_ranking_score",
      backgroundColor = DT::styleInterval(
        0.89, c("#6FF97C", "#FB7575")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "OMIM_morbid",
      backgroundColor = DT::styleEqual(
        c("no", "yes"), c("#6FF97C", "#FB7575")
      )
    )
    dt <- DT::formatStyle(
      dt,
      "OMIM_morbid_candidate",
      backgroundColor = DT::styleEqual(
        c("no", "yes"), c("#6FF97C", "#FB7575")
      )
    )
    dt
  })

  # Table of column descriptions
  output$column_description_table <- DT::renderDataTable({
    desc <- data.frame(
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
      )
    )
    DT::datatable(desc, options = list(pageLength = 30), rownames = FALSE)
  })
}

shinyApp(ui, server)