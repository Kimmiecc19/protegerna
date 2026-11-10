# ============================================================
# 01_rna_dream_answerals.R
# Objective 4 - transcriptomics evidence
#
# DREAM differential expression, ALS vs healthy control, using the
# AnswerALS consortium raw gene-count matrix (NOT the rnasplice/Salmon
# counts, which were quantified with the wrong library strandedness).
#
# Inputs
#   counts_file   AnswerALS raw-count matrix (CSV; first column = gene ID,
#                 header row = sample IDs such as CASE-NEUAG241NUD-6681-T)
#   coldata_file  your 336-sample metadata (286 ALS + 50 HC, BDC only;
#                 rownames like CASE_NEUAG241NUD_6681_T; columns condition,
#                 seq_batch, sex, diagnosis)
#   Both are read from 04_integration/data/ (controlled access; not committed).
# Outputs (out_dir)
#   QC/                          sample matching, design tables, library sizes,
#                                PCA, p-value histograms, low-depth flags
#   <model>/AALS_<model>_dream_results.csv   all genes; columns gene_id,
#                                ensembl_clean, gene_name, logFC, AveExpr, t,
#                                P.Value, adj.P.Val, ... (the format the
#                                existing dream_fgsea_*.R scripts read)
#   AALS_dream_voom_objects.rds  voom object + metadata for the permutation
#                                check (03b_pathway_label_permutation.R)
#
#Installed with bioconductor: edger, variancepartition, annotationdbi, org.Hs.eg.db
#
# Edit the "Settings" block, then run with Rscript or in RStudio.


# ============================================================

suppressPackageStartupMessages({
  library(edgeR)
  library(limma)
  library(variancePartition)
  library(BiocParallel)
  library(dplyr)
  library(tibble)
  library(ggplot2)
  library(AnnotationDbi)
  library(org.Hs.eg.db)
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

# ----------------------------
# Settings
# ----------------------------
counts_file  <- "data/AnswerALS-1276-T-v1-release7_raw-counts.csv"   # release 7: all 336 samples match exactly
coldata_file <- "data/answerals_cohort_coldata.csv"
out_dir      <- "01_single_layer/01a_results_rna_differential_expression"
min_count    <- 10      # same filtering rule as the earlier analysis
min_samples  <- 20
allow_participant_fallback <- TRUE   # match on participant ID if the exact sample ID is absent
n_workers    <- 1                    # >1 uses SnowParam; keep 1 on Windows if errors occur

dir.create(file.path(out_dir, "QC"), recursive = TRUE, showWarnings = FALSE)
BPPARAM <- if (n_workers > 1) SnowParam(n_workers) else SerialParam()

# ----------------------------
# Read inputs
# ----------------------------
raw <- read.csv(counts_file, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
# gene-ID column = first column whose values look like Ensembl IDs (release 6 has an extra row-number column)
gene_col <- names(raw)[which(vapply(raw, function(x) is.character(x) && mean(grepl("^ENSG", head(x, 100))) > 0.9, logical(1)))[1]]
if (is.na(gene_col)) stop("Could not find an Ensembl gene-ID column")
genes <- raw[[gene_col]]
sample_cols <- grep("^(CASE|CTRL)-", names(raw), value = TRUE)
counts <- as.matrix(raw[, sample_cols, drop = FALSE])
storage.mode(counts) <- "numeric"
rownames(counts) <- genes
if (anyDuplicated(rownames(counts))) stop("Duplicate gene IDs in counts file")
if (any(counts < 0, na.rm = TRUE) || anyNA(counts)) stop("Negative or missing counts found")
message("Count matrix: ", nrow(counts), " genes x ", ncol(counts), " samples")

meta <- read.csv(coldata_file, check.names = FALSE, stringsAsFactors = FALSE, row.names = 1)
meta$sample_rnasplice <- rownames(meta)
meta$sample <- gsub("_", "-", meta$sample_rnasplice)                 # CASE_NEU..._T -> CASE-NEU...-T
meta$participant <- sub("^((CASE|CTRL)-NEU[A-Z0-9]+)-.*$", "\\1", meta$sample)

meta <- meta %>%
  filter(diagnosis %in% c("ALS", "Healthy Control")) %>%
  filter(!source %in% c("BDC_CTRL", "BTC", "BTC2"))

# ----------------------------
# Match samples (exact sample ID first; optional participant fallback)
# ----------------------------
count_participant <- sub("^((CASE|CTRL)-NEU[A-Z0-9]+)-.*$", "\\1", colnames(counts))
meta$matrix_column <- NA_character_
meta$match_type <- "unmatched"
exact <- meta$sample %in% colnames(counts)
meta$matrix_column[exact] <- meta$sample[exact]
meta$match_type[exact] <- "exact_sample_id"
if (allow_participant_fallback) {
  for (i in which(!exact)) {
    hits <- colnames(counts)[count_participant == meta$participant[i]]
    if (length(hits) == 1) {
      meta$matrix_column[i] <- hits
      meta$match_type[i] <- "participant_id_only"
    } else if (length(hits) > 1) {
      meta$match_type[i] <- "ambiguous_participant_multiple_columns"
    }
  }
}
write.csv(meta[, c("sample", "participant", "diagnosis", "matrix_column", "match_type")],
          file.path(out_dir, "QC", "sample_matching.csv"), row.names = FALSE)
print(table(meta$match_type, meta$diagnosis))
meta <- meta[!is.na(meta$matrix_column), ]
if (anyDuplicated(meta$matrix_column)) stop("Two metadata rows map to the same matrix column")

counts <- counts[, meta$matrix_column, drop = FALSE]
colnames(counts) <- meta$sample
rownames(meta) <- meta$sample

meta <- meta %>%
  mutate(
    condition = factor(ifelse(diagnosis == "ALS", "CASE", "CTRL"), levels = c("CTRL", "CASE")),
    sex       = factor(sex),
    seq_batch = factor(seq_batch)
  )
meta <- droplevels(meta)
stopifnot(identical(colnames(counts), rownames(meta)))

sink(file.path(out_dir, "QC", "design_tables.txt"))
cat("Samples analysed:", ncol(counts), "\n\n"); print(table(meta$condition))
cat("\nSex x condition\n"); print(table(meta$sex, meta$condition))
cat("\nseq_batch x condition\n"); print(table(meta$seq_batch, meta$condition))
sink()

# ----------------------------
# Filtering, TMM, QC
# ----------------------------
dge <- DGEList(counts)
keep <- rowSums(dge$counts >= min_count) >= min_samples
dge <- dge[keep, , keep.lib.sizes = FALSE]
dge <- calcNormFactors(dge, method = "TMM")
message("Genes retained after filtering: ", nrow(dge))

lib <- data.frame(sample = colnames(dge), lib_size = dge$samples$lib.size,
                  norm_factor = dge$samples$norm.factors,
                  condition = meta$condition, seq_batch = meta$seq_batch)
loglib <- log10(lib$lib_size)
lib$low_depth_flag <- loglib < median(loglib) - 3 * mad(loglib)
write.csv(lib, file.path(out_dir, "QC", "library_sizes_and_flags.csv"), row.names = FALSE)
if (any(lib$low_depth_flag)) {
  warning("Low-depth samples flagged (not removed): ",
          paste(lib$sample[lib$low_depth_flag], collapse = ", "),
          ". Inspect QC/library_sizes_and_flags.csv and the PCA before deciding.")
}

logcpm <- cpm(dge, log = TRUE, prior.count = 1)
pca <- prcomp(t(logcpm[order(apply(logcpm, 1, var), decreasing = TRUE)[1:2000], ]), scale. = TRUE)
ve <- round(100 * pca$sdev^2 / sum(pca$sdev^2), 1)
pdat <- data.frame(pca$x[, 1:2], meta)
ggsave(file.path(out_dir, "QC", "PCA_condition.png"),
       ggplot(pdat, aes(PC1, PC2, fill = condition, shape = sex)) +
         geom_point(size = 2.2, colour = thesis_neutral[["outline"]], stroke = 0.25) +
         scale_shape_manual(values = setNames(c(21, 24)[seq_along(levels(pdat$sex))], levels(pdat$sex))) +
         scale_fill_manual(values = c(CTRL = thesis_secondary[["mint"]], CASE = thesis_secondary[["flame"]]),
                           name = "Diagnosis") + theme_thesis() +
         labs(x = paste0("PC1 (", ve[1], "%)"), y = paste0("PC2 (", ve[2], "%)"), fill = "Diagnosis"),
       width = 7, height = 5, dpi = 300)
ggsave(file.path(out_dir, "QC", "PCA_seq_batch.png"),
       ggplot(pdat, aes(PC1, PC2, colour = as.numeric(as.character(seq_batch)))) +
         geom_point(size = 2, alpha = 0.85) +
         scale_colour_gradientn(colours = unname(thesis_primary[c("blue", "teal", "gold", "maroon")]),
                                name = "Sequencing\nbatch") + theme_thesis() +
         labs(title = "RNA sample PCA by sequencing batch",
              x = paste0("PC1 (", ve[1], "%)"), y = paste0("PC2 (", ve[2], "%)")),
       width = 7, height = 5, dpi = 300)

# Variance explained by covariates on the top PCs (batch-effect check)
r2 <- sapply(c("condition", "sex", "seq_batch"), function(v)
  sapply(1:5, function(k) summary(lm(pca$x[, k] ~ meta[[v]]))$r.squared))
rownames(r2) <- paste0("PC", 1:5)
write.csv(round(r2, 3), file.path(out_dir, "QC", "PC_variance_explained_by_covariates.csv"))

# Gene symbols
ens <- sub("\\..*$", "", rownames(dge))
sym <- mapIds(org.Hs.eg.db, keys = ens, keytype = "ENSEMBL", column = "SYMBOL", multiVals = "first")
gene_map <- data.frame(gene_id = rownames(dge), ensembl_clean = ens,
                       gene_name = ifelse(is.na(sym) | sym == "", ens, unname(sym)))

# ----------------------------
# Models
# primary:     mixed model, seq_batch random intercept
# sensitivity: seq_batch as fixed effect
# This step takes long to run
# ----------------------------
models <- list(
  primary_mixed_seq_batch_random = ~ condition + sex + (1 | seq_batch),
  sensitivity_fixed_seq_batch     = ~ condition + sex + seq_batch
)

run_model <- function(name, form) {
  mdir <- file.path(out_dir, name); dir.create(mdir, showWarnings = FALSE)
  v <- voomWithDreamWeights(dge, form, meta, BPPARAM = BPPARAM)
  fit <- eBayes(dream(v, form, meta, BPPARAM = BPPARAM))
  res <- topTable(fit, coef = "conditionCASE", number = Inf, sort.by = "P") %>%
    rownames_to_column("gene_id") %>% left_join(gene_map, by = "gene_id") %>%
    relocate(gene_id, ensembl_clean, gene_name)
  write.csv(res, file.path(mdir, paste0("AALS_", name, "_dream_results.csv")), row.names = FALSE)
  p_hist <- ggplot(res, aes(x = P.Value)) +
    geom_histogram(bins = 50, fill = thesis_secondary[["mint"]],
                   colour = thesis_neutral[["outline"]], linewidth = 0.2) +
    theme_thesis() + labs(title = paste(name, "p-value distribution"), x = "P-value", y = "Number of genes")
  ggsave(file.path(mdir, "pvalue_histogram.png"), p_hist, width = 7, height = 5, dpi = 300)
  sink(file.path(mdir, "summary.txt"))
  cat("Formula: "); print(form)
  cat("Genes tested:", nrow(res), "\nFDR<0.05:", sum(res$adj.P.Val < 0.05), "\nFDR<0.10:", sum(res$adj.P.Val < 0.10),
      "\nSD of t (expect ~1 under null):", round(sd(res$t), 3), "\n")
  sink()
  invisible(list(voom = v, res = res))
}

out <- lapply(names(models), function(n) run_model(n, models[[n]]))
names(out) <- names(models)
saveRDS(list(voom = out$primary_mixed_seq_batch_random$voom, meta = meta, gene_map = gene_map),
        file.path(out_dir, "AALS_dream_voom_objects.rds"))

cmp <- inner_join(out[[1]]$res[, c("gene_id", "t")], out[[2]]$res[, c("gene_id", "t")], by = "gene_id")
message("Correlation of t between primary and sensitivity models: ", round(cor(cmp$t.x, cmp$t.y), 3))
writeLines(capture.output(sessionInfo()), file.path(out_dir, "sessionInfo.txt"))
message("Done. Feed ", file.path(out_dir, names(models)[1]), "/AALS_..._dream_results.csv to the fgsea script.")
