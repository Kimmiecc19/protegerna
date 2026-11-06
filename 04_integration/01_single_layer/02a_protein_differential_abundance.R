# ============================================================
# 07_protein_differential_abundance.R
# Objective 4 - conventional proteomic layer: ALS vs healthy controls
#
# Two input sources (choose with source_mode):
#
#   "consortium" (PRIMARY)  Answer ALS consortium protein matrix
#       AnswerALS-447-P_proteomics-protein-matrix_prebatchcorrected.txt
#       Same SWATH raw files as our searches, quantified by the consortium against UniProt
#       (OpenSWATH + mProphet 1% FDR, MS2TIC-normalised, MapDIA roll-up; NOT imputed).
#       Covers all 336 RNA participants (286 ALS, 50 HC). Zero = not quantified -> NA.
#       Batch covariate = sample preparation (digestion) batch from cohort_samples.tsv.
#       The 436 "correctedImputed" matrix is NOT used (random-forest imputation);
#       the 664 Exploris matrix shares no participants with the RNA cohort.
#
#   "v5" (SENSITIVITY)  our quantms-diann v5 searches, consolidated by 05_consolidate_cohort.py
#       (log2 PG.MaxLFQ, all six batches; failed runs excluded upstream). Batch covariate = MS search batch.
#
# Model: limma ~ condition + sex + batch, trend + robust eBayes, no imputation,
#        protein kept if quantified in >= 70% of ALS and of HC participants.
#
# Outputs (out_dir)
#   QC/  design tables, missingness, run medians, PCA + variance explained, p-value histogram
#   AALS_protein_limma_results.csv            gene_id, gene_name, logFC, AveExpr, t, P.Value, adj.P.Val, ...
#   AALS_protein_limma_results_for_fgsea.csv  one row per gene (for 02_08_dream_fgsea.R)
#   protein_objects.rds                       for 03_09_pathway_label_permutation.R (mode = "protein")
#   protein_by_participant_gene.log2.tsv      gene x participant matrix (median-centred log2) for
#                                             14_cross_omics_agreement.py and 16_integration_evaluation_table.py
#                                             (--protein-gene-matrix)
# ============================================================

suppressPackageStartupMessages({
  library(limma)
  library(dplyr)
  library(tibble)
  library(ggplot2)
})

source(file.path("code_ALS_integration", "thesis_palette.R"))
set_thesis_geom_defaults()

# ----------------------------
# Settings
# ----------------------------
#project_dir <- "C:/Users/USER-PC/OneDrive/Documents/05_ALS_integration"
#setwd(project_dir)

source_mode   <- "V5"     # "consortium" (primary) or "v5" (sensitivity)
clinical_file <- "data_ALS_integration/answerals_cohort_coldata.csv"
min_valid_fraction_per_group <- 0.70
control_line  <- "CTRL-NEUEU392AE8"
run_dream_sensitivity <- FALSE

# consortium input
consortium_file <- "data_ALS_integration/4_matrix_proteomics_answerals/AnswerALS-447-P_proteomics-protein-matrix_prebatchcorrected.txt"
prep_batch_file <- "data_ALS_integration/data_consolidate_quantms/cohort_samples.tsv"   # sample_preparation_batch per participant

# v5 input (05_consolidate_cohort.py output)
protein_file   <- "results_ALS_integration/results_05_cohort_v5_b1to6/protein_by_run.log2.tsv"
samples_file   <- "results_ALS_integration/results_05_cohort_v5_b1to6/sample_metadata.tsv"
pgdb_meta_file <- "proteogenomic_db_compare_v5_v7/results_pgdb_publication_rerun_v5/proteogenomic_metadata.tsv"
batches_to_use <- paste0("batch", 1:6)

out_dir <- if (source_mode == "consortium") "results_ALS_integration/results_07_protein_da_consortium" else
  "results_ALS_integration/results_07_protein_da_v5_b1to6"
if (dir.exists(out_dir)) stop("Output folder exists: ", out_dir, " (rename or delete it first)")
dir.create(file.path(out_dir, "QC"), recursive = TRUE)

part_id <- function(x) {
  m <- regmatches(x, regexpr("(CASE|CTRL)[-_]NEU[A-Z0-9]+", x))
  out <- rep(NA_character_, length(x)); out[regexpr("(CASE|CTRL)[-_]NEU[A-Z0-9]+", x) > 0] <- gsub("_", "-", m); out
}

# participant-level diagnosis and sex from the RNA metadata
clin <- read.csv(clinical_file, row.names = 1, stringsAsFactors = FALSE, check.names = FALSE)
clin$participant_id <- part_id(rownames(clin))
clin <- clin %>% filter(!is.na(participant_id)) %>% distinct(participant_id, .keep_all = TRUE) %>%
  dplyr::select(participant_id, diagnosis, sex)

# ----------------------------
# Read inputs -> mat (protein x sample), s (sample metadata), gene (per row)
# ----------------------------
if (source_mode == "consortium") {
  raw <- read.delim(consortium_file, check.names = FALSE, stringsAsFactors = FALSE)
  prot <- raw$Protein
  sample_cols <- grep("(CASE|CTRL)[-_]NEU[A-Z0-9]+", colnames(raw), value = TRUE)
  mat <- as.matrix(raw[, sample_cols]); storage.mode(mat) <- "numeric"
  mat[!is.finite(mat) | mat <= 0] <- NA
  mat <- log2(mat)
  rownames(mat) <- prot
  # keep UniProt entries only (drops iRT and other non-protein rows)
  is_uniprot <- grepl("\\|", prot)
  mat <- mat[is_uniprot, , drop = FALSE]
  # one column per participant (average repeated samples; drop the technical control line)
  pid <- part_id(colnames(mat))
  keep_cols <- !is.na(pid) & pid != control_line
  mat <- mat[, keep_cols, drop = FALSE]; pid <- pid[keep_cols]
  if (any(duplicated(pid))) {
    mat <- sapply(split(seq_along(pid), pid), function(i) rowMeans(mat[, i, drop = FALSE], na.rm = TRUE))
    mat[is.nan(mat)] <- NA
  } else colnames(mat) <- pid
  # gene symbols: UniProt accession -> SYMBOL (org.Hs.eg.db), fallback = entry-name prefix
  acc <- sub("^[0-9]+/(sp|tr)\\|([^|]+)\\|.*$", "\\2", rownames(mat))
  entry <- sub("^.*\\|([^|_]+)_HUMAN.*$", "\\1", rownames(mat))
  sym <- tryCatch({
    # namespace only: library(org.Hs.eg.db) attaches AnnotationDbi, whose select() masks dplyr::select()
    if (!requireNamespace("org.Hs.eg.db", quietly = TRUE)) stop("org.Hs.eg.db is not installed")
    AnnotationDbi::mapIds(org.Hs.eg.db::org.Hs.eg.db, keys = acc, keytype = "UNIPROT", column = "SYMBOL", multiVals = "first")
  }, error = function(e) { warning("org.Hs.eg.db mapping failed; using UniProt entry names"); rep(NA, length(acc)) })
  gene <- ifelse(is.na(sym), entry, sym)
  gene_map_type <- ifelse(is.na(sym), "entry_name", "uniprot_to_symbol")
  # sample metadata
  pb <- read.delim(prep_batch_file, stringsAsFactors = FALSE, check.names = FALSE) %>%
    filter(sample_type == "participant") %>% distinct(participant_id, .keep_all = TRUE) %>%
    dplyr::select(participant_id, prep_batch = sample_preparation_batch)
  s <- data.frame(sample = colnames(mat), participant_id = colnames(mat), stringsAsFactors = FALSE) %>%
    left_join(clin, by = "participant_id") %>% left_join(pb, by = "participant_id")
  s$batch <- s$prep_batch
} else {
  mat <- read.delim(protein_file, check.names = FALSE, stringsAsFactors = FALSE, na.strings = c("NA", ""))
  rownames(mat) <- mat$Protein.Group
  mat <- as.matrix(mat[, setdiff(colnames(mat), "Protein.Group")]); storage.mode(mat) <- "numeric"
  mat[is.infinite(mat)] <- NA
  s <- read.delim(samples_file, stringsAsFactors = FALSE, check.names = FALSE) %>%
    filter(sample_type == "participant", batch %in% batches_to_use, participant_id != control_line) %>%
    left_join(clin, by = "participant_id") %>% mutate(sample = cohort_run)
  mat <- mat[, s$sample, drop = FALSE]
  pg_meta <- read.delim(pgdb_meta_file, stringsAsFactors = FALSE, check.names = FALSE)
  id2gene <- setNames(pg_meta$gene, pg_meta$sequence_id)
  pg_ids <- function(pg) unique(unlist(regmatches(pg, gregexpr("PGDB_U[0-9]+", pg))))
  gi <- t(vapply(rownames(mat), function(pg) {
    g <- unique(na.omit(unlist(strsplit(id2gene[pg_ids(pg)], "[;,]")))); g <- g[g != "" & g != "NA"]
    if (length(g) == 1) c(g, "unique_gene") else if (length(g) == 0) c(NA, "no_gene") else c(paste(g, collapse = ";"), "multiple_genes")
  }, character(2)))
  gene <- gi[, 1]; gene_map_type <- gi[, 2]
}
names(gene) <- rownames(mat); names(gene_map_type) <- rownames(mat)

# ----------------------------
# ALS vs HC samples only
# ----------------------------
if (any(is.na(s$diagnosis)))
  write.csv(s[is.na(s$diagnosis), ], file.path(out_dir, "QC", "samples_without_RNA_metadata.csv"), row.names = FALSE)
s <- s %>% filter(diagnosis %in% c("ALS", "Healthy Control"))
if (any(is.na(s$batch))) stop("Missing batch for: ", paste(head(s$sample[is.na(s$batch)]), collapse = ", "))
s <- s %>% mutate(condition = factor(ifelse(diagnosis == "ALS", "CASE", "CTRL"), levels = c("CTRL", "CASE")),
                  sex = factor(sex), ms_batch = factor(batch))
mat <- mat[, s$sample, drop = FALSE]
mat <- sweep(mat, 2, apply(mat, 2, median, na.rm = TRUE))      # per-sample median centring
s <- droplevels(s); rownames(s) <- s$sample
stopifnot(identical(colnames(mat), rownames(s)))

sink(file.path(out_dir, "QC", "design_tables.txt"))
cat("Source:", source_mode, "\nSamples:", ncol(mat), "\n"); print(table(s$condition))
cat("\nbatch x condition\n"); print(table(s$ms_batch, s$condition))
cat("\nsex x condition\n"); print(table(s$sex, s$condition))
sink()

# ----------------------------
# Missing-value filter (no imputation)
# ----------------------------
n_case <- rowSums(!is.na(mat[, s$condition == "CASE", drop = FALSE]))
n_ctrl <- rowSums(!is.na(mat[, s$condition == "CTRL", drop = FALSE]))
keep <- n_case >= ceiling(min_valid_fraction_per_group * sum(s$condition == "CASE")) &
        n_ctrl >= ceiling(min_valid_fraction_per_group * sum(s$condition == "CTRL"))
write.csv(data.frame(source = source_mode, proteins_total = nrow(mat), proteins_kept = sum(keep),
                     min_valid_fraction_per_group = min_valid_fraction_per_group),
          file.path(out_dir, "QC", "missingness_filter.csv"), row.names = FALSE)

# gene x participant matrix for the Python integration scripts (all quantified proteins, unique genes)
gm <- mat[gene_map_type[rownames(mat)] != "no_gene" & !grepl(";", gene[rownames(mat)]), , drop = FALSE]
pmat <- rowsum(ifelse(is.na(gm), 0, gm), gene[rownames(gm)]) / pmax(rowsum(1 * !is.na(gm), gene[rownames(gm)]), 1)
pmat[rowsum(1 * !is.na(gm), gene[rownames(gm)]) == 0] <- NA
colnames(pmat) <- s$participant_id
write.table(data.frame(gene = rownames(pmat), pmat, check.names = FALSE),
            file.path(out_dir, "protein_by_participant_gene.log2.tsv"), sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")

mat <- mat[keep, , drop = FALSE]; n_case <- n_case[keep]; n_ctrl <- n_ctrl[keep]
message("Proteins tested: ", nrow(mat))

qc_long <- data.frame(sample = rep(colnames(mat), each = nrow(mat)),
                      intensity = as.vector(mat),
                      prep_batch = rep(suppressWarnings(as.numeric(gsub("[^0-9.]", "", as.character(s$ms_batch)))), each = nrow(mat)))
p_medians <- ggplot(qc_long, aes(x = sample, y = intensity, fill = prep_batch)) +
  geom_boxplot(outlier.shape = NA, linewidth = 0.15) +
  scale_fill_gradientn(colours = unname(thesis_primary[c("blue", "teal", "gold", "maroon")]),
                       name = "Preparation\nbatch") +
  theme_thesis(base_size = 10) +
  theme(axis.text.x = element_blank(), axis.ticks.x = element_blank(),
        plot.margin = margin(8, 10, 8, 8)) +
  labs(title = paste0("Protein intensity distributions by sample (", source_mode, ")"),
       x = "Participants", y = "Median-centred log2 protein intensity")
ggsave(file.path(out_dir, "QC", "sample_medians_by_batch.png"), p_medians,
       width = 12, height = 6, dpi = 300)
cc <- mat[rowMeans(is.na(mat)) <= 0.10, , drop = FALSE]          # PCA only: proteins <= 10% missing,
cc <- t(apply(cc, 1, function(x) { x[is.na(x)] <- mean(x, na.rm = TRUE); x }))   # row-mean filled for PCA only
if (nrow(cc) > 50) {
  pca <- prcomp(t(cc), scale. = TRUE); ve <- round(100 * pca$sdev^2 / sum(pca$sdev^2), 1)
  pd <- data.frame(pca$x[, 1:2], s)
  ggsave(file.path(out_dir, "QC", "PCA.png"),
         ggplot(pd, aes(PC1, PC2, fill = condition)) +
           geom_point(shape = 21, size = 2.2, colour = thesis_neutral[["outline"]], stroke = 0.25) +
           scale_fill_manual(values = c(CTRL = thesis_secondary[["mint"]], CASE = thesis_secondary[["flame"]]),
                             name = "Diagnosis") + theme_thesis() +
           labs(x = paste0("PC1 (", ve[1], "%)"), y = paste0("PC2 (", ve[2], "%)")),
         width = 7, height = 5, dpi = 300)
  r2 <- sapply(c("condition", "sex", "ms_batch"), function(v)
    sapply(1:5, function(k) summary(lm(pca$x[, k] ~ s[[v]]))$r.squared))
  rownames(r2) <- paste0("PC", 1:5)
  write.csv(round(r2, 3), file.path(out_dir, "QC", "PC_variance_explained_by_covariates.csv"))
}

# ----------------------------
# limma: ~ condition + sex + batch
# ----------------------------
design <- model.matrix(~ condition + sex + ms_batch, data = s)
fit <- eBayes(lmFit(mat, design), trend = TRUE, robust = TRUE)
res <- topTable(fit, coef = "conditionCASE", number = Inf, sort.by = "none") %>%
  rownames_to_column("gene_id") %>%
  mutate(gene_name = gene[gene_id], gene_mapping = gene_map_type[gene_id],
         n_valid_CASE = n_case[gene_id], n_valid_CTRL = n_ctrl[gene_id]) %>%
  relocate(gene_id, gene_name) %>% arrange(P.Value)
write.csv(res, file.path(out_dir, "AALS_protein_limma_results.csv"), row.names = FALSE)

fg <- res %>% filter(!is.na(gene_name), gene_mapping != "no_gene", !grepl(";", gene_name)) %>%
  group_by(gene_name) %>% slice_max(abs(t), n = 1, with_ties = FALSE) %>% ungroup() %>% arrange(P.Value)
write.csv(fg, file.path(out_dir, "AALS_protein_limma_results_for_fgsea.csv"), row.names = FALSE)

saveRDS(list(mat = mat, s = s,
             gene = ifelse(gene_map_type[rownames(mat)] == "no_gene" | grepl(";", gene[rownames(mat)]), NA, gene[rownames(mat)])),
        file.path(out_dir, "protein_objects.rds"))

p_hist <- ggplot(res, aes(x = P.Value)) +
  geom_histogram(bins = 50, fill = thesis_secondary[["mint"]],
                 colour = thesis_neutral[["outline"]], linewidth = 0.2) +
  theme_thesis() + labs(title = "Protein ALS versus control p-value distribution",
                         x = "P-value", y = "Number of proteins")
ggsave(file.path(out_dir, "QC", "pvalue_histogram.png"), p_hist, width = 7, height = 5, dpi = 300)
sink(file.path(out_dir, "summary.txt"))
cat("Source:", source_mode, "\nModel: ~ condition + sex + batch (limma, trend+robust eBayes)\n")
cat("Samples:", ncol(mat), "(", sum(s$condition == "CASE"), "ALS,", sum(s$condition == "CTRL"), "HC )\n")
cat("Proteins tested:", nrow(res), "\nFDR<0.05:", sum(res$adj.P.Val < 0.05), "\nFDR<0.10:", sum(res$adj.P.Val < 0.10),
    "\nGenes for fgsea:", nrow(fg), "\n")
print(table(res$gene_mapping))
sink()

if (run_dream_sensitivity) {
  suppressPackageStartupMessages(library(variancePartition))
  fit_d <- eBayes(dream(mat, ~ condition + sex + (1 | ms_batch), s))
  res_d <- topTable(fit_d, coef = "conditionCASE", number = Inf, sort.by = "none")
  write.csv(rownames_to_column(res_d, "gene_id"), file.path(out_dir, "AALS_protein_dream_random_batch_sensitivity.csv"), row.names = FALSE)
}
writeLines(capture.output(sessionInfo()), file.path(out_dir, "sessionInfo.txt"))

