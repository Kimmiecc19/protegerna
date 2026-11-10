# Recreate Objective 4 thesis-palette plots from saved analysis outputs.
# Run from the Objective 4 project root after installing ggplot2/dplyr/readr.
# Figures 6.1 and 6.3 use the saved TSVs directly; this script does not rerun models.

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(readr)
  library(stringr)
})
source(file.path("code_ALS_integration", "thesis_palette.R"))
set_thesis_geom_defaults()

results <- "results_ALS_integration"
fig_dir <- file.path(results, "results_interpretation")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
theme_set(theme_thesis(base_size = 11))

save_png <- function(plot, path, width = 10, height = 6) {
  ggsave(path, plot, width = width, height = height, dpi = 300, bg = "white")
}
clean_pathway_label <- function(x, width = 48) {
  x <- str_replace(x, "^(REACTOME|HALLMARK|GOCC|GOBP|GOMF|WP|KEGG|HP|PID)_", "\\1: ")
  str_wrap(str_replace_all(x, "_", " "), width = width)
}
stars <- function(p) case_when(p < 0.001 ~ "***", p < 0.01 ~ "**", p < 0.05 ~ "*", TRUE ~ "")

# -----------------------------------------------------------------------------
# Figure 6.1: positive control for the SV expression scan
# Uses the unfiltered scan tables shown in the Objective 4 chapter.
# -----------------------------------------------------------------------------
pc_files <- c(
  intersection = file.path(results, "results_sv_carrier_expression_scan_unfiltered",
                            "intersection_positive_control_by_length.tsv"),
  `union-only` = file.path(results, "results_sv_carrier_expression_scan_unfiltered",
                           "union_only_positive_control_by_length.tsv")
)
pc <- bind_rows(lapply(names(pc_files), function(nm) {
  x <- read_tsv(pc_files[[nm]], show_col_types = FALSE)
  x$table <- nm
  x
})) %>%
  mutate(table = factor(table, levels = c("intersection", "union-only"),
                        labels = c("Intersection (both callers)", "Union-only (exploratory)")),
         sv_type = factor(sv_type, levels = c("DEL", "DUP"),
                          labels = c("Deletions (expected ↓)", "Duplications (expected ↑)")),
         len_bin = factor(len_bin, levels = c("<1kb", "1-10kb", "10-100kb")),
         expected_pct = 100 * frac_in_expected_direction,
         bar_height = expected_pct - 35,
         star = stars(sign_test_p),
         n_label = paste0("n=", format(pairs, big.mark = ",")))

p61 <- ggplot(pc, aes(len_bin, bar_height, fill = sv_type)) +
  geom_hline(yintercept = 15, colour = thesis_neutral[["guide"]],
             linetype = "dashed", linewidth = 0.45) +
  geom_col(position = position_dodge(width = 0.82), width = 0.76,
           colour = thesis_neutral[["outline"]], linewidth = 0.2) +
  geom_text(aes(y = 2.5, label = n_label), position = position_dodge(width = 0.82),
            angle = 90, hjust = 1.05, vjust = 0.5, size = 2.6, colour = thesis_neutral[["ink"]]) +
  geom_text(aes(y = bar_height + 1.1, label = star),
            position = position_dodge(width = 0.82), size = 3.7, colour = thesis_neutral[["ink"]]) +
  facet_wrap(~table, nrow = 1) +
  scale_fill_manual(values = c("Deletions (expected ↓)" = thesis_secondary[["mint"]],
                               "Duplications (expected ↑)" = thesis_secondary[["flame"]])) +
  scale_y_continuous(limits = c(0, 31), breaks = seq(0, 30, 5),
                     labels = seq(35, 65, 5), expand = expansion(mult = c(0, 0))) +
  labs(title = "SV-associated expression effects follow the expected direction",
       subtitle = "Fraction of SV–gene pairs in the expected direction; dashed line = 50%",
       x = "SV length", y = "Pairs changing in expected direction (%)", fill = NULL,
       caption = NULL) +
  theme_thesis(base_size = 10) +
  theme(legend.position = "top", strip.text = element_text(face = "bold"),
        plot.title = element_text(face = "bold"), plot.margin = margin(10, 12, 10, 10))
save_png(p61, file.path(fig_dir, "Figure_6.1_SV_expression_scan_positive_control.png"), 11, 6.2)
ggsave(file.path(fig_dir, "Figure_6.1_SV_expression_scan_positive_control.pdf"),
       p61, width = 11, height = 6.2, bg = "white")

# -----------------------------------------------------------------------------
# Figure 6.3: changes in evidence classification after integration
# -----------------------------------------------------------------------------
ev <- read_tsv(file.path(results, "results_evaluation_table_final", "evaluation_summary.tsv"),
               show_col_types = FALSE)
category_labels <- c(
  primary_SV = "Primary SV candidates",
  ALS_gene_SV = "SVs in ALS genes",
  isoform_peptide = "Isoform peptides",
  novel_peptide = "Novel peptides",
  recurrent_fusion = "Recurrent fusions"
)
status_cols <- c("confirmed", "rejected", "reclassified", "unchanged")
status_labels <- c(confirmed = "Confirmed", rejected = "Rejected",
                   reclassified = "Reclassified", unchanged = "Unchanged")
ev_long <- ev %>%
  select(category, all_of(status_cols), total) %>%
  tidyr::pivot_longer(all_of(status_cols), names_to = "status", values_to = "n") %>%
  mutate(category = factor(category, levels = names(category_labels), labels = unname(category_labels)),
         status = factor(status, levels = status_cols, labels = unname(status_labels[status_cols])),
         count_label = if_else(n > 0, as.character(n), ""))
status_palette <- c(
  Confirmed = thesis_secondary[["mint"]],
  Rejected = thesis_secondary[["flame"]],
  Reclassified = thesis_secondary[["crimson"]],
  Unchanged = thesis_secondary[["brown"]]
)
p63 <- ggplot(ev_long, aes(y = category, x = n, fill = status)) +
  geom_col(position = "fill", colour = thesis_neutral[["outline"]], linewidth = 0.2) +
  geom_text(aes(label = count_label, colour = status), position = position_fill(vjust = 0.5),
            size = 3.2) +
  geom_text(data = distinct(ev_long, category, total),
            aes(y = category, x = 1.02, label = paste0("n = ", format(total, big.mark = ","))),
            inherit.aes = FALSE, hjust = 0, size = 3.1, colour = thesis_neutral[["guide"]]) +
  scale_fill_manual(values = status_palette, drop = FALSE) +
  scale_colour_manual(values = setNames(ink_on(status_palette), names(status_palette)), guide = "none") +
  scale_x_continuous(labels = scales::label_percent(), breaks = seq(0, 1, 0.25),
                     limits = c(0, 1.15), expand = expansion(mult = c(0, 0))) +
  labs(title = "Integration changes the interpretation of candidate evidence",
       x = "Candidates (%)", y = NULL, fill = NULL,
       caption = "Numbers within bars are candidate counts; totals are shown at right.") +
  coord_cartesian(xlim = c(0, 1.15), clip = "off") +
  theme_thesis(base_size = 10) +
  theme(legend.position = "top", plot.title = element_text(face = "bold"),
        plot.margin = margin(10, 50, 10, 10), panel.grid.major.y = element_blank())
save_png(p63, file.path(fig_dir, "Figure_6.3_change_in_conclusion.png"), 10.5, 5.2)
ggsave(file.path(fig_dir, "Figure_6.3_change_in_conclusion.pdf"),
       p63, width = 10.5, height = 5.2, bg = "white")

# -----------------------------------------------------------------------------
# Rebuild DREAM and protein consortium QC plots from saved model outputs.
# -----------------------------------------------------------------------------
rna_qc_dir <- file.path(results, "results_rna_dream", "QC")
rna_obj_path <- file.path(results, "results_rna_dream", "AALS_dream_voom_objects.rds")
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
    csv <- file.path(results, "results_rna_dream", model,
                     paste0("AALS_", model, "_dream_results.csv"))
    if (file.exists(csv)) {
      d <- read_csv(csv, show_col_types = FALSE)
      p <- ggplot(d, aes(P.Value)) +
        geom_histogram(bins = 50, fill = thesis_secondary[["mint"]],
                       colour = thesis_neutral[["outline"]], linewidth = 0.2) +
        labs(title = paste(model, "p-value distribution"), x = "P-value", y = "Number of genes") + theme_thesis()
      save_png(p, file.path(results, "results_rna_dream", model, "pvalue_histogram.png"), 7, 5)
    }
  }
}

prot_dir <- file.path(results, "results_protein_da_consortium")
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
cross_dir <- file.path(results, "results_cross_omics")
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
for (mode in c("rna", "protein")) {
  base <- file.path(results, paste0("results_fgsea_", mode))
  omics_colour <- if (mode == "rna") thesis_primary[["maroon"]] else thesis_primary[["teal"]]
  direction_colours <- c("Positive NES" = omics_colour, "Negative NES" = thesis_neutral[["guide"]])
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
      if (nrow(d)) {
        d <- d %>% mutate(label = clean_pathway_label(Description),
                          label = factor(label, levels = rev(unique(label))),
                          direction = if_else(NES >= 0, "Positive NES", "Negative NES"))
        dot <- ggplot(d, aes(label, Count, size = Count, colour = -log10(p.adjust))) +
          geom_point(alpha = 0.9) + coord_flip(clip = "off") +
          scale_colour_gradient(low = thesis_neutral[["muted"]], high = omics_colour,
                                name = "−log10(adj. p)") +
          labs(title = paste("DREAM-t ranked GSEA:", category), x = NULL, y = "Gene count", size = "Count") +
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
