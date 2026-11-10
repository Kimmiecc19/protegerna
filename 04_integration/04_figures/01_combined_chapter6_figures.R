# Combined chapter 6 figure script. Figures 6.1 and 6.3 use base R; the
# additional QC, cross-omics, and pathway figures use ggplot2 and tidyverse.
# Run from the Objective 4 project root after installing the packages below.
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(readr)
  library(stringr)
})
# Paths below are relative to 04_integration/. Find this script's folder however it is run
# (Rscript, RStudio "Source", or source()), then work from 04_integration/.
script_dir <- local({
  f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
  if (length(f)) return(dirname(normalizePath(f[1])))
  for (fr in rev(sys.frames())) if (!is.null(fr$ofile)) return(dirname(normalizePath(fr$ofile)))
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    p <- tryCatch(rstudioapi::getSourceEditorContext()$path, error = function(e) "")
    if (nzchar(p)) return(dirname(normalizePath(p)))
  }
  stop("Cannot locate this script; run it with Rscript or source() it by its path.")
})
project_dir <- normalizePath(file.path(script_dir, ".."))   # 04_integration/
setwd(project_dir)
source(file.path("lib", "thesis_palette.R"))
set_thesis_geom_defaults()
# Result folders of the earlier steps (relative to 04_integration/)
single  <- "01_single_layer"
cross   <- "03_cross_layer"
out_dir <- file.path("04_figures", "01_results_combined_chapter6_figures")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
outline <- thesis_neutral[["outline"]]
ink <- thesis_neutral[["ink"]]
guide <- thesis_neutral[["guide"]]
bg <- "white"

save_figure <- function(path_png, path_pdf, width, height, draw) {
  grDevices::png(path_png, width = width, height = height, units = "in", res = 300,
                 bg = bg, type = if (capabilities("cairo")) "cairo" else getOption("bitmapType"))
  draw()
  grDevices::dev.off()
  grDevices::pdf(path_pdf, width = width, height = height, bg = bg, useDingbats = FALSE)
  draw()
  grDevices::dev.off()
}
# ggplot figures (QC, concordance, pathway plots) are saved with save_png().
save_png <- function(plot, path, width = 10, height = 6) {
  ggsave(path, plot, width = width, height = height, dpi = 300, bg = "white")
}
# Same pathway labels as 01_single_layer/03a_pathway_enrichment.R.
clean_pathway_label <- function(x, width = 48) {
  x <- str_replace(x, "^(REACTOME|HALLMARK|GOCC|GOBP|GOMF|WP|KEGG|HP|PID)_", "\\1: ")
  str_wrap(str_replace_all(x, "_", " "), width = width)
}
sig_stars <- function(p) ifelse(p < .001, "***", ifelse(p < .01, "**", ifelse(p < .05, "*", "")))

# Figure 6.1: expected-direction positive control.
dir_scan <- file.path(single, "01e_results_sv_carrier_expression_scan_unfiltered")
pc <- rbind(
  transform(read.delim(file.path(dir_scan, "intersection_positive_control_by_length.tsv")),
            table_label = "Intersection (both callers)"),
  transform(read.delim(file.path(dir_scan, "union_only_positive_control_by_length.tsv")),
            table_label = "Union-only (exploratory)")
)
len_levels <- c("<1kb", "1-10kb", "10-100kb")
type_levels <- c("DEL", "DUP")
bar_cols <- c(DEL = thesis_secondary[["mint"]], DUP = thesis_secondary[["flame"]])

draw_61 <- function() {
  old <- par(no.readonly = TRUE); on.exit(par(old))
  par(mfrow = c(1, 2), mar = c(5.1, 4.2, 3.7, 1.2), oma = c(0.5, 0, 2.3, 0),
      col = ink, fg = outline, bg = bg, cex = 0.95)
  for (tbl in c("Intersection (both callers)", "Union-only (exploratory)")) {
    d <- pc[pc$table_label == tbl, ]
    by_type <- lapply(type_levels, function(tp) d[d$sv_type == tp, ])
    vals <- t(sapply(by_type, function(z) z$frac_in_expected_direction[match(len_levels, z$len_bin)])) * 100
    ns <- t(sapply(by_type, function(z) z$pairs[match(len_levels, z$len_bin)]))
    ps <- t(sapply(by_type, function(z) z$sign_test_p[match(len_levels, z$len_bin)]))
    # Start every column at the displayed 35% axis. A 42% result therefore
    # rises to 42%, below the 50% reference line but above the x-axis.
    heights <- vals - 35
    centers <- barplot(heights, beside = TRUE, names.arg = rep("", length(len_levels)),
                       col = bar_cols[type_levels], border = outline, lwd = 0.7,
                       ylim = c(0, 31), axes = FALSE, xlab = "",
                       ylab = "Pairs changing in expected direction (%)",
                       main = tbl, cex.main = 1.0, cex.names = 0.85)
    abline(h = seq(0, 30, 5), col = thesis_neutral[["grid"]], lwd = 0.7)
    abline(h = 15, col = guide, lty = 2, lwd = 1.1)
    axis(2, at = seq(0, 30, 5), labels = seq(35, 65, 5), las = 1,
         col.axis = ink, cex.axis = 0.8)
    axis(1, at = colMeans(centers), labels = len_levels, tick = FALSE, line = 0.7, cex.axis = 0.8)
    mtext("SV length", side = 1, line = 3.2, cex = 0.9, col = ink)
    box(col = outline)
    for (j in seq_along(type_levels)) for (i in seq_along(len_levels)) {
      text(centers[j, i], 2.5, labels = paste0("n=", format(ns[j, i], big.mark = ",")),
           srt = 90, adj = c(0, 0.5), cex = 0.62, col = ink, xpd = NA)
      text(centers[j, i], heights[j, i] + 1.1,
           labels = sig_stars(ps[j, i]),
           cex = 0.85, col = ink, xpd = NA)
    }
    legend("topright", legend = c("Deletions (expected decrease)", "Duplications (expected increase)"),
           fill = bar_cols[type_levels], border = outline, bty = "n", cex = 0.69)
  }
  mtext("SV expression scan positive control", outer = TRUE, side = 3,
        line = 0.6, font = 2, cex = 1.12, col = ink)
}
save_figure(file.path(out_dir, "Figure_6.1_SV_expression_scan_positive_control.png"),
            file.path(out_dir, "Figure_6.1_SV_expression_scan_positive_control.pdf"),
            11, 6.4, draw_61)

# Figure 6.3: status changes after cross-layer evaluation.
ev <- read.delim(file.path(cross, "02_results_evaluation_table", "evaluation_summary.tsv"),
                 check.names = FALSE)
category_order <- c("recurrent_fusion", "novel_peptide", "isoform_peptide", "ALS_gene_SV", "primary_SV")
category_labels <- c("Recurrent fusions", "Novel peptides", "Isoform peptides",
                     "SVs in ALS genes", "Primary SV candidates")
status_order <- c("confirmed", "rejected", "reclassified", "unchanged")
status_labels <- c("Confirmed", "Rejected", "Reclassified", "Unchanged")
status_cols <- c(Confirmed = thesis_secondary[["mint"]],
                 Rejected = thesis_secondary[["flame"]],
                 Reclassified = thesis_secondary[["crimson"]],
                 Unchanged = thesis_secondary[["brown"]])
ev <- ev[match(category_order, ev$category), ]
status_counts <- as.matrix(ev[, status_order])
rownames(status_counts) <- category_labels
colnames(status_counts) <- status_labels
totals <- ev$total
shares <- status_counts / totals

draw_63 <- function() {
  old <- par(no.readonly = TRUE); on.exit(par(old))
  par(mar = c(4.4, 11.8, 3.2, 5.4), col = ink, fg = outline, bg = bg, cex = 0.9)
  centers <- barplot(t(shares * 100), horiz = TRUE, beside = FALSE,
                     names.arg = category_labels, las = 1, xlim = c(0, 118),
                     col = status_cols, border = outline, lwd = 0.6,
                     axes = FALSE, xlab = "Candidates (%)", cex.names = 0.84)
  abline(v = seq(0, 100, 25), col = thesis_neutral[["grid"]], lwd = 0.75)
  axis(1, at = seq(0, 100, 25), labels = seq(0, 100, 25), col.axis = ink, cex.axis = 0.8)
  box(col = outline)
  for (i in seq_along(category_labels)) {
    cumulative <- 0
    for (j in seq_along(status_order)) {
      n <- status_counts[i, j]
      if (n > 0) {
        mid <- cumulative + 50 * shares[i, j]
        text(mid, centers[i], labels = n,
             col = ink_on(status_cols[j]), cex = 0.82, font = 1)
      }
      cumulative <- cumulative + 100 * shares[i, j]
    }
    text(102.2, centers[i], labels = paste0("n = ", format(totals[i], big.mark = ",")),
         adj = 0, cex = 0.78, col = guide, xpd = NA)
  }
  legend("top", inset = c(0, -0.14), xpd = NA, horiz = TRUE,
         legend = status_labels, fill = status_cols, border = outline,
         bty = "n", cex = 0.79)
  title(main = "Integration changes the interpretation of candidate evidence",
        line = 1, cex.main = 1.05, col.main = ink)
}
save_figure(file.path(out_dir, "Figure_6.3_change_in_conclusion.png"),
            file.path(out_dir, "Figure_6.3_change_in_conclusion.pdf"),
            10.5, 5.4, draw_63)

# -----------------------------------------------------------------------------
# Rebuild DREAM and protein consortium QC plots from saved model outputs.
# -----------------------------------------------------------------------------
rna_qc_dir <- file.path(single, "01a_results_rna_differential_expression", "QC")
rna_obj_path <- file.path(single, "01a_results_rna_differential_expression", "AALS_dream_voom_objects.rds")
if (file.exists(rna_obj_path)) {
  obj <- readRDS(rna_obj_path)
  expr <- obj$voom$E
  meta <- obj$meta
  top <- order(apply(expr, 1, var, na.rm = TRUE), decreasing = TRUE)[seq_len(min(2000, nrow(expr)))]
  pca <- prcomp(t(expr[top, , drop = FALSE]), scale. = TRUE)
  pct <- round(100 * pca$sdev^2 / sum(pca$sdev^2), 1)
  pd <- data.frame(pca$x[, 1:2], meta)
  p <- ggplot(pd, aes(PC1, PC2, fill = condition, shape = sex)) +
    geom_point(size = 2.2, colour = thesis_neutral[["outline"]], stroke = 0.25) +
    scale_shape_manual(values = setNames(c(21, 24)[seq_along(levels(factor(pd$sex)))],
                                         levels(factor(pd$sex)))) +
    scale_fill_manual(values = c(CTRL = thesis_secondary[["mint"]], CASE = thesis_secondary[["flame"]])) +
    labs(x = paste0("PC1 (", pct[1], "%)"), y = paste0("PC2 (", pct[2], "%)"),
         fill = "Diagnosis", title = "RNA sample PCA by diagnosis") + theme_thesis()
  save_png(p, file.path(rna_qc_dir, "PCA_condition.png"), 7, 5)
  pd$seq_batch_num <- as.numeric(as.character(pd$seq_batch))
  p <- ggplot(pd, aes(PC1, PC2, colour = seq_batch_num)) + geom_point(size = 2, alpha = 0.85) +
    scale_colour_gradientn(colours = unname(thesis_primary[c("blue", "teal", "gold", "maroon")]),
                           name = "Sequencing\nbatch") +
    labs(x = paste0("PC1 (", pct[1], "%)"), y = paste0("PC2 (", pct[2], "%)"),
         title = "RNA sample PCA by sequencing batch") + theme_thesis()
  save_png(p, file.path(rna_qc_dir, "PCA_seq_batch.png"), 7, 5)
  for (model in c("primary_mixed_seq_batch_random", "sensitivity_fixed_seq_batch")) {
    csv <- file.path(single, "01a_results_rna_differential_expression", model,
                     paste0("AALS_", model, "_dream_results.csv"))
    if (file.exists(csv)) {
      d <- read_csv(csv, show_col_types = FALSE)
      p <- ggplot(d, aes(P.Value)) +
        geom_histogram(bins = 50, fill = thesis_secondary[["mint"]],
                       colour = thesis_neutral[["outline"]], linewidth = 0.2) +
        labs(title = paste(model, "p-value distribution"), x = "P-value", y = "Number of genes") + theme_thesis()
      save_png(p, file.path(single, "01a_results_rna_differential_expression", model, "pvalue_histogram.png"), 7, 5)
    }
  }
}

prot_dir <- file.path(single, "02a_results_protein_da_consortium")
prot_qc_dir <- file.path(prot_dir, "QC")
prot_obj_path <- file.path(prot_dir, "protein_objects.rds")
if (file.exists(prot_obj_path)) {
  obj <- readRDS(prot_obj_path)
  mat <- obj$mat
  s <- obj$s
  qc_long <- data.frame(sample = rep(colnames(mat), each = nrow(mat)),
                        intensity = as.vector(mat),
                        prep_batch = as.numeric(as.character(s$ms_batch)))
  p <- ggplot(qc_long, aes(sample, intensity, fill = prep_batch)) +
    geom_boxplot(outlier.shape = NA, linewidth = 0.15) +
    scale_fill_gradientn(colours = unname(thesis_primary[c("blue", "teal", "gold", "maroon")]),
                         name = "Preparation\nbatch") +
    labs(title = "Protein intensity distributions by sample (consortium)",
         x = "Participants", y = "Median-centred log2 protein intensity") +
    theme_thesis(base_size = 9) + theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
  save_png(p, file.path(prot_qc_dir, "sample_medians_by_batch.png"), 12, 6)
  cc <- mat[rowMeans(is.na(mat)) <= 0.10, , drop = FALSE]
  cc <- t(apply(cc, 1, function(x) { x[is.na(x)] <- mean(x, na.rm = TRUE); x }))
  if (nrow(cc) > 50) {
    pca <- prcomp(t(cc), scale. = TRUE)
    pct <- round(100 * pca$sdev^2 / sum(pca$sdev^2), 1)
    pd <- data.frame(pca$x[, 1:2], s)
    p <- ggplot(pd, aes(PC1, PC2, fill = condition)) +
      geom_point(shape = 21, size = 2.2, colour = thesis_neutral[["outline"]], stroke = 0.25) +
      scale_fill_manual(values = c(CTRL = thesis_secondary[["mint"]], CASE = thesis_secondary[["flame"]])) +
      labs(x = paste0("PC1 (", pct[1], "%)"), y = paste0("PC2 (", pct[2], "%)"), fill = "Diagnosis") + theme_thesis()
    save_png(p, file.path(prot_qc_dir, "PCA.png"), 7, 5)
  }
  prot_csv <- file.path(prot_dir, "AALS_protein_limma_results.csv")
  d <- read_csv(prot_csv, show_col_types = FALSE)
  p <- ggplot(d, aes(P.Value)) +
    geom_histogram(bins = 50, fill = thesis_secondary[["mint"]],
                   colour = thesis_neutral[["outline"]], linewidth = 0.2) +
    labs(title = "Protein ALS versus control p-value distribution",
         x = "P-value", y = "Number of proteins") + theme_thesis()
  save_png(p, file.path(prot_qc_dir, "pvalue_histogram.png"), 7, 5)
}

# Rebuild the existing RNA–protein concordance scatter from its saved table.
cross_dir <- file.path(cross, "01_results_cross_omics_agreement")
cross_file <- file.path(cross_dir, "rna_protein_concordance.tsv")
cross_summary <- file.path(cross_dir, "rna_protein_concordance_summary.json")
if (file.exists(cross_file) && file.exists(cross_summary)) {
  d <- read_tsv(cross_file, show_col_types = FALSE)
  summ <- jsonlite::fromJSON(cross_summary)
  sig <- d %>% filter(rna_P.Value < 0.01, prot_P.Value < 0.01)
  p <- ggplot(d, aes(rna_logFC, prot_logFC)) +
    geom_hline(yintercept = 0, colour = thesis_neutral[["guide"]], linewidth = 0.35) +
    geom_vline(xintercept = 0, colour = thesis_neutral[["guide"]], linewidth = 0.35) +
    geom_point(colour = thesis_primary[["blue"]], alpha = 0.38, size = 1.2) +
    geom_point(data = sig, colour = thesis_secondary_full[["flame"]],
               alpha = 0.9, size = 1.7) +
    labs(title = paste0("RNA–protein effect concordance: Spearman ρ = ",
                        sprintf("%.2f", summ$spearman_rho_logFC)),
         subtitle = paste0("n = ", format(summ$genes_in_both, big.mark = ","),
                           " genes; highlighted: nominal p < 0.01 in both layers"),
         x = "RNA log2 fold change (ALS vs control)",
         y = "Protein log2 fold change (ALS vs control)") +
    theme_thesis() + theme(plot.title = element_text(face = "bold"))
  save_png(p, file.path(cross_dir, "rna_protein_concordance.png"), 7, 6)
}

# -----------------------------------------------------------------------------
# Recreate fgsea and clusterProfiler summary plots from saved result tables.
# Running-score plots retain enrichplot's original style; they are not recoloured here.
# -----------------------------------------------------------------------------
fgsea_dirs <- c(
  rna = file.path("03a_results_pathway_enrichment_rna", "results_fgsea_rna_500"),
  protein = file.path("03a_results_pathway_enrichment_protein", "results_fgsea_protein_500")
)
for (mode in names(fgsea_dirs)) {
  base <- file.path(single, fgsea_dirs[[mode]])
  omics_colour <- if (mode == "rna") thesis_primary[["maroon"]] else thesis_primary[["teal"]]
  negative_nes_colour <- if (mode == "protein") "#7FAFB0" else "#B0909D"
  direction_colours <- c("Positive NES" = omics_colour, "Negative NES" = negative_nes_colour)
  for (category in c("broad", "disease", "targeted")) {
    val_dir <- file.path(base, "gsea_validation", category)
    plot_dir <- file.path(base, "gsea_plots", category)
    dir.create(plot_dir, recursive = TRUE, showWarnings = FALSE)
    top_file <- file.path(val_dir, paste0("fgsea_", category, "_top20_DREAM_t_pathways.csv"))
    if (file.exists(top_file)) {
      d <- read_csv(top_file, show_col_types = FALSE) %>%
        mutate(label = clean_pathway_label(pathway),
               label = factor(label, levels = rev(label)),
               NES_direction = if_else(NES >= 0, "Positive NES", "Negative NES"))
      p <- ggplot(d, aes(label, -log10(padj), fill = NES_direction)) +
        geom_col(width = 0.75, colour = thesis_neutral[["outline"]], linewidth = 0.2) +
        coord_flip(clip = "off") + scale_fill_manual(values = direction_colours) +
        labs(title = paste("Top DREAM-t fgsea pathways:", category),
             subtitle = "Ranking uses all genes ranked by DREAM moderated t-statistic.",
             x = NULL, y = "−log10(adjusted p-value)", fill = "NES direction") +
        theme_thesis(base_size = 10) + theme(axis.text.y = element_text(size = 8.5),
                                               plot.margin = margin(10, 24, 10, 10))
      save_png(p, file.path(plot_dir, paste0("fgsea_", category, "_top20_DREAM_t.png")), 12, 9)
    }
    cp_file <- file.path(val_dir, paste0("clusterProfiler_GSEA_", category, "_DREAM_t_results.csv"))
    if (file.exists(cp_file)) {
      d <- read_csv(cp_file, show_col_types = FALSE) %>%
        filter(!is.na(p.adjust), !is.na(Description)) %>% arrange(p.adjust) %>% slice_head(n = 20)
      # clusterProfiler GSEA tables store the gene-set size in setSize (not Count).
      if (!"setSize" %in% names(d) && "Count" %in% names(d)) {
        d <- d %>% mutate(setSize = Count)
      }
      if (!"setSize" %in% names(d)) {
        stop("Missing both setSize and Count in ", cp_file, call. = FALSE)
      }
      if (nrow(d)) {
        d <- d %>% mutate(label = clean_pathway_label(Description),
                          label = factor(label, levels = rev(unique(label))),
                          direction = if_else(NES >= 0, "Positive NES", "Negative NES"))
        dot <- ggplot(d, aes(label, setSize, size = setSize, colour = -log10(p.adjust))) +
          geom_point(alpha = 0.9) + coord_flip(clip = "off") +
          scale_colour_gradient(low = thesis_neutral[["muted"]], high = omics_colour,
                                name = "−log10(adj. p)") +
          labs(title = paste("DREAM-t ranked GSEA:", category), x = NULL, y = "Gene count", size = "Gene set size") +
          theme_thesis(base_size = 10) + theme(axis.text.y = element_text(size = 8.5),
                                                plot.margin = margin(10, 24, 10, 10))
        save_png(dot, file.path(plot_dir, paste0("clusterProfiler_", category, "_dotplot_top20.png")), 12, 9)
        d$direction <- factor(d$direction, levels = c("Negative NES", "Positive NES"))
        nes <- ggplot(d, aes(label, NES, fill = direction)) +
          geom_col(colour = thesis_neutral[["outline"]], linewidth = 0.2) +
          coord_flip(clip = "off") + scale_fill_manual(values = direction_colours) +
          labs(title = paste("Top DREAM-t GSEA pathways:", category), x = NULL,
               y = "Normalized enrichment score") +
          theme_thesis(base_size = 10) + theme(legend.position = "none", axis.text.y = element_text(size = 8.5),
                                                plot.margin = margin(10, 24, 10, 10))
        save_png(nes, file.path(plot_dir, paste0("clusterProfiler_", category, "_top20_NES_barplot.png")), 12, 9)
      }
    }
  }
}

message("Objective 4 palette plots refreshed. Figure 6.1 and 6.3 were built from the saved TSV summaries.")
