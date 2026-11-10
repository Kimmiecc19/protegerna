# ============================================================
# DREAM-ranked GSEA / pathway interpretation
# Corrected fast version:
#   - DREAM moderated t-statistic is the primary ranking
#   - broad category is run as fast screening only
#   - broad skips pairwise redundancy reduction and clusterProfiler
#   - disease and targeted categories keep fuller interpretation outputs
#   - serial execution to avoid parallel serialize/connection errors
# ============================================================

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(fgsea)
  library(clusterProfiler)
  library(enrichplot)
  library(ggplot2)
  library(stringr)
  library(readr)
  library(org.Hs.eg.db)
  library(AnnotationDbi)
  library(purrr)
  library(BiocParallel)
})

source(file.path("code_ALS_integration", "thesis_palette.R"))

select <- dplyr::select
filter <- dplyr::filter
mutate <- dplyr::mutate
arrange <- dplyr::arrange
summarise <- dplyr::summarise

# ----------------------------
# Settings
# ----------------------------
#project_dir <- "C:/Users/USER-PC/OneDrive/Documents/05_ALS_integration"
#setwd(project_dir)

# Run twice: mode = "rna" (input = 01 output) and mode = "protein" (input = 07 output).
mode <- "protein"            # "rna" or "protein"

if (mode == "rna") {
  # Primary model from 01_rna_dream_answerals.R (AnswerALS release 7 counts).
  dream_results_file <- "results_ALS_integration/results_rna_dream/primary_mixed_seq_batch_random/AALS_primary_mixed_seq_batch_random_dream_results.csv"
  # Sensitivity: "results_ALS_integration/results_rna_dream/sensitivity_fixed_seq_batch/AALS_sensitivity_fixed_seq_batch_dream_results.csv"
  base_out_dir <- "results_ALS_integration/results_fgsea_rna"
} else {
  # Consortium protein matrix, 07_protein_differential_abundance.R (source_mode = "consortium").
  dream_results_file <- "results_ALS_integration/results_protein_da_consortium/AALS_protein_limma_results_for_fgsea.csv"
  base_out_dir <- "results_ALS_integration/results_fgsea_protein"
}
# NOT the old rnasplice-based DREAM_revised_* results (strand-affected; excluded).

validation_root <- file.path(base_out_dir, "gsea_validation")
plot_root <- file.path(base_out_dir, "gsea_plots")
dir.create(validation_root, showWarnings = FALSE, recursive = TRUE)
dir.create(plot_root, showWarnings = FALSE, recursive = TRUE)

min_gs_size <- 15
max_gs_size <- 300
plot_width <- 12
plot_height <- 9
padj_cutoff <- 0.05
redundancy_jaccard_cutoff <- 0.50

# Runtime controls
primary_rank_only <- TRUE
run_clusterprofiler_for_broad <- FALSE
run_redundancy_for_broad <- FALSE
make_running_score_plots_for_broad <- FALSE
make_ridgeplots <- FALSE
run_categories <- c("broad", "disease", "targeted")

# Force serial execution to avoid: Error in serialize(data, node$con)
BPPARAM <- SerialParam()
register(BPPARAM)

safe_filename <- function(x) str_replace_all(x, "[^A-Za-z0-9_]+", "_")

omics_colour <- if (mode == "rna") thesis_primary[["maroon"]] else thesis_primary[["teal"]]
nes_palette <- c("Positive NES" = omics_colour, "Negative NES" = thesis_neutral[["guide"]])
clean_pathway_label <- function(x, width = 48) {
  x <- str_replace(x, "^(REACTOME|HALLMARK|GOCC|GOBP|GOMF|WP|KEGG|HP|PID)_", "\\1: ")
  str_wrap(str_replace_all(x, "_", " "), width = width)
}

make_rank <- function(values, genes) {
  rank_df <- data.frame(
    gene = genes,
    score = as.numeric(values),
    stringsAsFactors = FALSE
  ) %>%
    filter(!is.na(score), !is.na(gene), gene != "") %>%
    group_by(gene) %>%
    slice_max(order_by = abs(score), n = 1, with_ties = FALSE) %>%
    ungroup()
  
  ranks <- rank_df$score
  names(ranks) <- rank_df$gene
  sort(ranks, decreasing = TRUE)
}

jaccard <- function(a, b) {
  a <- unique(a[a != ""])
  b <- unique(b[b != ""])
  denom <- length(union(a, b))
  if (denom == 0) return(0)
  length(intersect(a, b)) / denom
}

# Greedy redundancy reduction: keep strongest pathway, remove overlapping pathways
# with similar leading-edge genes. This is intentionally NOT run for broad sets.
reduce_redundant_pathways <- function(df, gene_col = "leadingEdge", cutoff = 0.50) {
  if (is.null(df) || nrow(df) == 0) return(df)
  
  df <- df %>% arrange(padj, desc(abs(NES)))
  keep <- rep(TRUE, nrow(df))
  representative <- rep(NA_character_, nrow(df))
  
  for (i in seq_len(nrow(df))) {
    if (!keep[i]) next
    representative[i] <- df$pathway[i]
    genes_i <- strsplit(as.character(df[[gene_col]][i]), ";|/")[[1]]
    
    for (j in seq_len(nrow(df))) {
      if (j <= i || !keep[j]) next
      genes_j <- strsplit(as.character(df[[gene_col]][j]), ";|/")[[1]]
      if (jaccard(genes_i, genes_j) >= cutoff) {
        keep[j] <- FALSE
        representative[j] <- df$pathway[i]
      }
    }
  }
  
  df$redundancy_representative <- representative
  df$kept_after_redundancy_reduction <- keep
  df
}

classify_als_relevance <- function(pathway) {
  p <- toupper(as.character(pathway))
  case_when(
    str_detect(p, "ALS|AMYOTROPHIC") ~ "Direct ALS gene set",
    str_detect(p, "NEURO|AXON|SYNAP|ROBO|TRANSMISSION|GUIDANCE") ~ "Neuronal/axon/synaptic biology",
    str_detect(p, "RNA|SPLIC|MRNA|NMD|RIBONUCLEO|TRANSLATION|RIBOSOME") ~ "RNA processing / translation",
    str_detect(p, "PROTEASOME|AUTOPHAGY|UNFOLDED|UPR|PROTEIN|UBIQUITIN") ~ "Proteostasis / protein quality control",
    str_detect(p, "TNF|NFK|INFLAM|IMMUNE|CYTOKINE") ~ "Inflammation / immune signalling",
    str_detect(p, "MITOCHON|OXIDATIVE|RESPIRATORY|METABOL") ~ "Mitochondrial/metabolic stress",
    TRUE ~ "Other pathway; inspect leading-edge genes"
  )
}

interpret_direction <- function(NES) {
  ifelse(
    NES > 0,
    "Positive NES: genes in this pathway are enriched toward genes up-ranked in ALS/CASE relative to CTRL.",
    "Negative NES: genes in this pathway are enriched toward genes down-ranked in ALS/CASE relative to CTRL."
  )
}

# ============================================================
# Prepare DREAM ranked lists
# ============================================================
res <- read.csv(dream_results_file, check.names = FALSE)

required_cols <- c("gene_id", "logFC", "P.Value", "t")
missing_cols <- setdiff(required_cols, colnames(res))
if (length(missing_cols) > 0) {
  stop("DREAM results file is missing required columns: ", paste(missing_cols, collapse = ", "))
}

if (!"gene_name" %in% colnames(res) || all(is.na(res$gene_name))) {
  res$ensembl_clean <- sub("\\..*$", "", res$gene_id)
  res$gene_name <- mapIds(
    org.Hs.eg.db,
    keys = res$ensembl_clean,
    keytype = "ENSEMBL",
    column = "SYMBOL",
    multiVals = "first"
  )
}

if (!"ensembl_clean" %in% colnames(res)) {
  res$ensembl_clean <- sub("\\..*$", "", res$gene_id)
}

idx_missing_symbol <- is.na(res$gene_name) | res$gene_name == ""
res$gene_name[idx_missing_symbol] <- res$ensembl_clean[idx_missing_symbol]

# Main ranking: DREAM moderated t-statistic across all tested genes.
ranks_t <- make_rank(res$t, res$gene_name)

# Sensitivity rankings, used only if primary_rank_only <- FALSE for non-broad categories.
ranks_signed_p <- make_rank(
  sign(res$logFC) * -log10(pmax(res$P.Value, .Machine$double.xmin)),
  res$gene_name
)
ranks_lfc <- make_rank(res$logFC, res$gene_name)

rank_list <- list(
  DREAM_t = ranks_t,
  Signed_log10P = ranks_signed_p,
  LogFC = ranks_lfc
)

# clusterProfiler uses DREAM_t only.
ranks <- ranks_t

write.csv(
  data.frame(gene = names(ranks), DREAM_t = as.numeric(ranks)),
  file.path(validation_root, "DREAM_t_ranked_all_genes_used_for_GSEA.csv"),
  row.names = FALSE
)

# ============================================================
# GMT files by category
# ============================================================
# Broad is deliberately restricted. Full GO/HPO broad GMTs are very large and
# should be run separately if needed.
gmt_broad <- c(
  "gene_sets/broad_sets/c2.cp.reactome.v2026.1.Hs.symbols.gmt",
  "gene_sets/broad_sets/c2.cp.wikipathways.v2026.1.Hs.symbols.gmt",
  "gene_sets/broad_sets/c5.go.v2026.1.Hs.symbols.gmt",
  "gene_sets/broad_sets/c5.hpo.v2026.1.Hs.symbols.gmt",
  "gene_sets/broad_sets/h.all.v2026.1.Hs.symbols.gmt"
)

# Optional broad GMTs that are intentionally excluded for speed:
# "gene_sets/broad_sets/c2.cp.biocarta.v2025.1.Hs.symbols.gmt"
# "gene_sets/broad_sets/c2.cp.v2025.1.Hs.symbols.gmt"
# "gene_sets/broad_sets/c5.go.mf.v2026.1.Hs.symbols.gmt"
# "gene_sets/broad_sets/c5.go.v2026.1.Hs.symbols.gmt"
# "gene_sets/broad_sets/c5.hpo.v2026.1.Hs.symbols.gmt"

gmt_disease <- c(
  "gene_sets/disease_sets/GOCC_NUCLEOCYTOPLASMIC_TRANSPORT_COMPLEX.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/HP_AMYOTROPHIC_LATERAL_SCLEROSIS.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/HP_NEURODEGENERATION.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/KEGG_ALZHEIMERS_DISEASE.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/KEGG_AMYOTROPHIC_LATERAL_SCLEROSIS_ALS.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/KEGG_HUNTINGTONS_DISEASE.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/REACTOME_AXON_GUIDANCE.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/REACTOME_NEURONAL_SYSTEM.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/REACTOME_SIGNALING_BY_ROBO_RECEPTORS.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/REACTOME_TRANSMISSION_ACROSS_CHEMICAL_SYNAPSES.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/WP_ALZHEIMERS_DISEASE.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/WP_AMYOTROPHIC_LATERAL_SCLEROSIS_ALS.v2026.1.Hs.gmt",
  "gene_sets/disease_sets/WP_PARKINSONS_DISEASE_PATHWAY.v2026.1.Hs.gmt"
)

gmt_targeted <- c(
  "gene_sets/targeted_sets/GOBP_ALTERNATIVE_MRNA_SPLICING_VIA_SPLICEOSOME.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOBP_REGULATION_OF_RNA_SPLICING.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOBP_RNA_SPLICING.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOBP_STRESS_GRANULE_ASSEMBLY.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOBP_TRANSLATIONAL_ELONGATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOBP_TRANSLATIONAL_INITIATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOBP_TRANSLATIONAL_TERMINATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/GOMF_RNA_BINDING.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/HALLMARK_UNFOLDED_PROTEIN_RESPONSE.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/HP_ABNORMAL_METABOLISM.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/KEGG_PROTEASOME.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/KEGG_RNA_DEGRADATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/KEGG_SPLICEOSOME.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/NFKAPPAB65_01.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/PID_NFKAPPAB_ATYPICAL_PATHWAY.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/PID_NFKAPPAB_CANONICAL_PATHWAY.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/PID_TNF_PATHWAY.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_AUTOPHAGY.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_DISEASES_OF_METABOLISM.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_EUKARYOTIC_TRANSLATION_ELONGATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_EUKARYOTIC_TRANSLATION_INITIATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_METABOLISM_OF_RNA.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_MRNA_SPLICING.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_NONSENSE_MEDIATED_DECAY_NMD.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_PROCESSING_OF_CAPPED_INTRON_CONTAINING_PRE_MRNA.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_TNF_SIGNALING.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_TRANSLATION.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/REACTOME_UNFOLDED_PROTEIN_RESPONSE_UPR.v2026.1.Hs.gmt",
  "gene_sets/targeted_sets/WP_UNFOLDED_PROTEIN_RESPONSE.v2026.1.Hs.gmt"
)

# gene-set files live in data_ALS_integration/gene_sets
gmt_broad    <- file.path("data_ALS_integration", gmt_broad)
gmt_disease  <- file.path("data_ALS_integration", gmt_disease)
gmt_targeted <- file.path("data_ALS_integration", gmt_targeted)

gmt_categories <- list(
  broad = gmt_broad,
  disease = gmt_disease,
  targeted = gmt_targeted
)

# ============================================================
# Main analysis function per GMT category
# ============================================================
run_gsea_category <- function(category_name, gmt_files) {
  message("Running GSEA category: ", category_name)
  
  category_validation_dir <- file.path(validation_root, category_name)
  category_plot_dir <- file.path(plot_root, category_name)
  dir.create(category_validation_dir, showWarnings = FALSE, recursive = TRUE)
  dir.create(category_plot_dir, showWarnings = FALSE, recursive = TRUE)
  
  existing_gmt <- gmt_files[file.exists(gmt_files)]
  missing_gmt <- setdiff(gmt_files, existing_gmt)
  writeLines(missing_gmt, file.path(category_validation_dir, paste0("missing_GMT_files_", category_name, ".txt")))
  
  if (length(existing_gmt) == 0) {
    warning("No GMT files found for category: ", category_name)
    return(NULL)
  }
  
  message("  GMT files found: ", length(existing_gmt))
  all_pathways <- unlist(lapply(existing_gmt, fgsea::gmtPathways), recursive = FALSE)
  message("  Pathways loaded before size filtering: ", length(all_pathways))
  
  # Pre-filter pathways before fgsea to avoid processing very small/large sets.
  all_pathways <- all_pathways[vapply(all_pathways, function(x) {
    n <- length(intersect(x, names(ranks)))
    n >= min_gs_size && n <= max_gs_size
  }, logical(1))]
  
  message("  Pathways retained after size/rank overlap filtering: ", length(all_pathways))
  
  if (length(all_pathways) == 0) {
    warning("No pathways retained after filtering for category: ", category_name)
    return(NULL)
  }
  
  run_fgsea_validation <- function(rank_vector, rank_name) {
    message("  Running fgsea with ranking: ", rank_name)
    
    fg <- fgsea(
      pathways = all_pathways,
      stats = rank_vector,
      minSize = min_gs_size,
      maxSize = max_gs_size,
      BPPARAM = SerialParam()
    ) %>%
      arrange(padj, desc(abs(NES))) %>%
      mutate(
        gmt_category = category_name,
        ranking_method = rank_name,
        leadingEdge = vapply(leadingEdge, paste, collapse = ";", FUN.VALUE = character(1)),
        als_relevance_class = classify_als_relevance(pathway),
        direction_interpretation = interpret_direction(NES)
      )
    
    write.csv(
      fg,
      file.path(category_validation_dir, paste0("fgsea_", category_name, "_", rank_name, "_results.csv")),
      row.names = FALSE
    )
    
    fg
  }
  
  # Broad always uses DREAM_t only. Disease/targeted can use all rankings if primary_rank_only is FALSE.
  if (primary_rank_only || category_name == "broad") {
    fgsea_all <- run_fgsea_validation(rank_list[["DREAM_t"]], "DREAM_t")
  } else {
    fgsea_all <- bind_rows(
      lapply(names(rank_list), function(nm) run_fgsea_validation(rank_list[[nm]], nm))
    )
  }
  
  write.csv(
    fgsea_all,
    file.path(category_validation_dir, paste0("fgsea_", category_name, "_all_ranking_methods_combined.csv")),
    row.names = FALSE
  )
  
  fgsea_main <- fgsea_all %>% filter(ranking_method == "DREAM_t")
  
  # Critical speed fix: do not run pairwise redundancy reduction on broad pathways.
  if (category_name == "broad" && !run_redundancy_for_broad) {
    message("  Skipping redundancy reduction for broad category because it is too large.")
    fgsea_main_reduced <- fgsea_main %>%
      arrange(padj, desc(abs(NES))) %>%
      mutate(
        redundancy_representative = pathway,
        kept_after_redundancy_reduction = TRUE
      )
  } else {
    message("  Running redundancy reduction for category: ", category_name)
    fgsea_main_reduced <- reduce_redundant_pathways(
      fgsea_main,
      cutoff = redundancy_jaccard_cutoff
    )
  }
  
  write.csv(
    fgsea_main_reduced,
    file.path(category_validation_dir, paste0("fgsea_", category_name, "_DREAM_t_redundancy_annotated.csv")),
    row.names = FALSE
  )
  
  write.csv(
    filter(fgsea_main_reduced, kept_after_redundancy_reduction),
    file.path(category_validation_dir, paste0("fgsea_", category_name, "_DREAM_t_nonredundant_pathways.csv")),
    row.names = FALSE
  )
  
  validation_summary <- fgsea_all %>%
    filter(padj < padj_cutoff) %>%
    group_by(pathway) %>%
    summarise(
      gmt_category = category_name,
      n_methods_significant = n_distinct(ranking_method),
      methods = paste(sort(unique(ranking_method)), collapse = ";"),
      best_padj = min(padj, na.rm = TRUE),
      mean_NES = mean(NES, na.rm = TRUE),
      NES_direction_consistent = length(unique(sign(NES))) == 1,
      als_relevance_class = classify_als_relevance(pathway[1]),
      .groups = "drop"
    ) %>%
    arrange(desc(n_methods_significant), best_padj)
  
  write.csv(
    validation_summary,
    file.path(category_validation_dir, paste0("fgsea_", category_name, "_validation_summary_recurring_pathways.csv")),
    row.names = FALSE
  )
  
  top20_fgsea <- fgsea_main_reduced %>%
    filter(kept_after_redundancy_reduction) %>%
    arrange(padj, desc(abs(NES))) %>%
    slice_head(n = 20) %>%
    mutate(
      NES_direction = ifelse(NES >= 0, "Positive NES", "Negative NES"),
      pathway_label = clean_pathway_label(pathway),
      pathway_label = factor(pathway_label, levels = rev(pathway_label))
    )
  
  write.csv(
    top20_fgsea,
    file.path(category_validation_dir, paste0("fgsea_", category_name, "_top20_DREAM_t_pathways.csv")),
    row.names = FALSE
  )
  
  if (nrow(top20_fgsea) > 0) {
    p_top20 <- ggplot(top20_fgsea, aes(x = pathway_label, y = -log10(padj), fill = NES_direction)) +
      geom_col(width = 0.75, colour = thesis_neutral[["outline"]], linewidth = 0.2) +
      coord_flip(clip = "off") +
      scale_fill_manual(values = nes_palette, drop = FALSE) +
      theme_thesis(base_size = 11) +
      theme(plot.margin = margin(10, 24, 10, 10), axis.text.y = element_text(size = 8.5)) +
      labs(
        title = paste0("Top DREAM-t fgsea pathways: ", category_name),
        subtitle = "Ranking uses all genes ranked by DREAM moderated t-statistic.",
        x = NULL,
        y = "-log10(adjusted p-value)",
        fill = "NES direction"
      )
    
    ggsave(
      file.path(category_plot_dir, paste0("fgsea_", category_name, "_top20_DREAM_t.png")),
      p_top20,
      width = plot_width,
      height = plot_height,
      dpi = 300
    )
    
    ggsave(
      file.path(category_plot_dir, paste0("fgsea_", category_name, "_top20_DREAM_t.pdf")),
      p_top20,
      width = plot_width,
      height = plot_height
    )
  }
  
  # ALS-specific interpretation table from fgsea, available for all categories including broad.
  fgsea_als_interpretation_table <- fgsea_main_reduced %>%
    filter(padj < padj_cutoff, kept_after_redundancy_reduction) %>%
    arrange(padj, desc(abs(NES))) %>%
    transmute(
      gmt_category,
      pathway_id = pathway,
      pathway_description = pathway,
      NES,
      pvalue = pval,
      p_adjust = padj,
      ALS_relevance_class = als_relevance_class,
      enrichment_direction = ifelse(NES > 0, "Up-ranked in ALS/CASE", "Down-ranked in ALS/CASE"),
      interpretation = paste0(als_relevance_class, ". ", direction_interpretation),
      leading_edge_genes = leadingEdge,
      source = "fgsea_DREAM_t"
    )
  
  write.csv(
    fgsea_als_interpretation_table,
    file.path(category_validation_dir, paste0("fgsea_", category_name, "_ALS_specific_interpretation_table.csv")),
    row.names = FALSE
  )
  
  # Broad stops here by design.
  if (category_name == "broad" && !run_clusterprofiler_for_broad) {
    message("  Skipping clusterProfiler, ridgeplots, and running-score plots for broad category to reduce runtime.")
    return(list(
      fgsea = fgsea_all,
      fgsea_main_reduced = fgsea_main_reduced,
      fgsea_summary = validation_summary,
      cp = data.frame(),
      leading_edge_table = data.frame(),
      leading_edge_frequency = data.frame(),
      als_interpretation_table = fgsea_als_interpretation_table
    ))
  }
  
  # ============================================================
  # clusterProfiler GSEA using DREAM_t only for disease/targeted
  # ============================================================
  message("  Running clusterProfiler::GSEA for category: ", category_name)
  
  gmt_df <- bind_rows(lapply(existing_gmt, clusterProfiler::read.gmt))
  
  cp_gsea <- GSEA(
    geneList = ranks,
    TERM2GENE = gmt_df,
    minGSSize = min_gs_size,
    maxGSSize = max_gs_size,
    pvalueCutoff = 1,
    pAdjustMethod = "BH",
    seed = TRUE,
    verbose = FALSE
  )
  
  cp_df <- as.data.frame(cp_gsea) %>%
    mutate(
      gmt_category = category_name,
      als_relevance_class = classify_als_relevance(ID),
      direction_interpretation = interpret_direction(NES)
    )
  
  write.csv(
    cp_df,
    file.path(category_validation_dir, paste0("clusterProfiler_GSEA_", category_name, "_DREAM_t_results.csv")),
    row.names = FALSE
  )
  
  if (nrow(cp_df) > 0) {
    p_dot <- dotplot(cp_gsea, showCategory = 20) +
      ggtitle(paste0("DREAM-t ranked GSEA: ", category_name)) +
      scale_colour_gradient(low = thesis_neutral[["muted"]], high = omics_colour) +
      theme_thesis(base_size = 11) +
      theme(plot.margin = margin(10, 22, 10, 10), axis.text.y = element_text(size = 8.5))
    
    ggsave(
      file.path(category_plot_dir, paste0("clusterProfiler_", category_name, "_dotplot_top20.png")),
      p_dot,
      width = plot_width,
      height = plot_height,
      dpi = 300
    )
    
    if (make_ridgeplots) {
      p_ridge <- ridgeplot(cp_gsea, showCategory = 20) +
        ggtitle(paste0("DREAM-t ranked GSEA distribution: ", category_name)) +
        theme_thesis(base_size = 11) +
        theme(plot.margin = margin(10, 22, 10, 10), axis.text.y = element_text(size = 8.5))
      
      ggsave(
        file.path(category_plot_dir, paste0("clusterProfiler_", category_name, "_ridgeplot_top20.png")),
        p_ridge,
        width = plot_width,
        height = plot_height,
        dpi = 300
      )
    }
    
    top_nes <- cp_df %>%
      arrange(p.adjust) %>%
      slice_head(n = 20) %>%
      mutate(
        pathway_label = clean_pathway_label(Description),
        pathway_label = factor(pathway_label, levels = rev(pathway_label)),
        direction = ifelse(NES > 0, "Positive NES", "Negative NES")
      )
    
    p_nes <- ggplot(top_nes, aes(x = pathway_label, y = NES, fill = direction)) +
      geom_col(show.legend = FALSE, colour = thesis_neutral[["outline"]], linewidth = 0.2) +
      coord_flip(clip = "off") +
      scale_fill_manual(values = c("Positive NES" = omics_colour,
                                   "Negative NES" = thesis_neutral[["guide"]])) +
      theme_thesis(base_size = 11) +
      theme(plot.margin = margin(10, 24, 10, 10), axis.text.y = element_text(size = 8.5)) +
      labs(
        title = paste0("Top DREAM-t GSEA pathways: ", category_name),
        x = NULL,
        y = "Normalized enrichment score"
      )
    
    ggsave(
      file.path(category_plot_dir, paste0("clusterProfiler_", category_name, "_top20_NES_barplot.png")),
      p_nes,
      width = plot_width,
      height = plot_height,
      dpi = 300
    )
    
    selected_pathways <- validation_summary %>%
      arrange(desc(n_methods_significant), best_padj) %>%
      slice_head(n = 8) %>%
      pull(pathway)
    
    selected_pathways <- selected_pathways[selected_pathways %in% cp_gsea@result$ID]
    
    if (length(selected_pathways) > 0) {
      for (pathway_id in selected_pathways) {
        pathway_title <- cp_gsea@result$Description[match(pathway_id, cp_gsea@result$ID)]
        # Keep enrichplot's standard running-score palette and theme. The thesis
        # palette is applied to the top-20 summary plots above, not this diagnostic.
        p <- gseaplot2(cp_gsea, geneSetID = pathway_id, title = pathway_title,
                       pvalue_table = TRUE)
        safe_name <- substr(safe_filename(pathway_id), 1, 80)
        
        png_file <- file.path(
          category_plot_dir,
          paste0("GSEA_", category_name, "_running_score_", safe_name, ".png")
        )
        
        pdf_file <- file.path(
          category_plot_dir,
          paste0("GSEA_", category_name, "_running_score_", safe_name, ".pdf")
        )
        
        ggsave(png_file, p, width = 9, height = 6, dpi = 300)
        
        tryCatch(
          ggsave(pdf_file, p, width = 9, height = 6),
          error = function(e) {
            warning("Could not save PDF for ", pathway_id, ": ", conditionMessage(e))
          }
        )
      }
    }
  }
  
  # Leading-edge and ALS interpretation tables from clusterProfiler.
  leading_edge_table <- cp_df %>%
    dplyr::filter(!is.na(core_enrichment), core_enrichment != "") %>%
    dplyr::select(
      gmt_category,
      ID,
      Description,
      NES,
      p.adjust,
      als_relevance_class,
      direction_interpretation,
      core_enrichment
    ) %>%
    dplyr::mutate(gene = strsplit(core_enrichment, "/")) %>%
    tidyr::unnest(gene)
  
  leading_edge_frequency <- leading_edge_table %>%
    count(gene, sort = TRUE, name = "n_pathways") %>%
    dplyr::left_join(
      res %>% dplyr::select(gene_name, gene_id, logFC, t, P.Value, adj.P.Val),
      by = c("gene" = "gene_name")
    ) %>%
    mutate(gmt_category = category_name) %>%
    arrange(desc(n_pathways), P.Value)
  
  cp_als_interpretation_table <- cp_df %>%
    filter(p.adjust < padj_cutoff) %>%
    arrange(p.adjust, desc(abs(NES))) %>%
    transmute(
      gmt_category,
      pathway_id = ID,
      pathway_description = Description,
      NES,
      pvalue,
      p_adjust = p.adjust,
      ALS_relevance_class = als_relevance_class,
      enrichment_direction = ifelse(NES > 0, "Up-ranked in ALS/CASE", "Down-ranked in ALS/CASE"),
      interpretation = paste0(als_relevance_class, ". ", direction_interpretation),
      leading_edge_genes = core_enrichment,
      source = "clusterProfiler_DREAM_t"
    )
  
  als_interpretation_table <- bind_rows(
    fgsea_als_interpretation_table,
    cp_als_interpretation_table
  )
  
  write.csv(
    leading_edge_table,
    file.path(category_validation_dir, paste0("GSEA_", category_name, "_leading_edge_gene_by_pathway.csv")),
    row.names = FALSE
  )
  
  write.csv(
    leading_edge_frequency,
    file.path(category_validation_dir, paste0("GSEA_", category_name, "_leading_edge_gene_frequency.csv")),
    row.names = FALSE
  )
  
  write.csv(
    als_interpretation_table,
    file.path(category_validation_dir, paste0("GSEA_", category_name, "_ALS_specific_interpretation_table.csv")),
    row.names = FALSE
  )
  
  list(
    fgsea = fgsea_all,
    fgsea_main_reduced = fgsea_main_reduced,
    fgsea_summary = validation_summary,
    cp = cp_df,
    leading_edge_table = leading_edge_table,
    leading_edge_frequency = leading_edge_frequency,
    als_interpretation_table = als_interpretation_table
  )
}

# ============================================================
# Run categories and write combined summaries
# ============================================================
# For fastest troubleshooting, run only broad first:
# run_categories <- c("broad")

all_category_results <- list()
for (category_name in run_categories) {
  all_category_results[[category_name]] <- run_gsea_category(
    category_name,
    gmt_categories[[category_name]]
  )
}

fgsea_combined <- bind_rows(lapply(all_category_results, function(x) if (is.null(x)) NULL else x$fgsea))
fgsea_nonredundant_combined <- bind_rows(lapply(all_category_results, function(x) {
  if (is.null(x) || is.null(x$fgsea_main_reduced) || nrow(x$fgsea_main_reduced) == 0) return(NULL)
  filter(x$fgsea_main_reduced, kept_after_redundancy_reduction)
}))
cp_combined <- bind_rows(lapply(all_category_results, function(x) if (is.null(x)) NULL else x$cp))
als_combined <- bind_rows(lapply(all_category_results, function(x) if (is.null(x)) NULL else x$als_interpretation_table))
leading_edge_frequency_combined <- bind_rows(lapply(all_category_results, function(x) if (is.null(x)) NULL else x$leading_edge_frequency))

write.csv(fgsea_combined, file.path(validation_root, "fgsea_ALL_categories_all_ranking_methods_combined.csv"), row.names = FALSE)
write.csv(fgsea_nonredundant_combined, file.path(validation_root, "fgsea_ALL_categories_DREAM_t_nonredundant_combined.csv"), row.names = FALSE)
write.csv(cp_combined, file.path(validation_root, "clusterProfiler_GSEA_ALL_categories_DREAM_t_results.csv"), row.names = FALSE)
write.csv(als_combined, file.path(validation_root, "GSEA_ALL_categories_ALS_specific_interpretation_table.csv"), row.names = FALSE)
write.csv(leading_edge_frequency_combined, file.path(validation_root, "GSEA_ALL_categories_leading_edge_gene_frequency.csv"), row.names = FALSE)

message("Done. GSEA outputs written to: ", base_out_dir)

