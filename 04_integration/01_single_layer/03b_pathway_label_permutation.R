# ============================================================
# 03_pathway_label_permutation.R
# Sample-label permutation check for the top fgsea pathways.
#
# Why: preranked fgsea permutes GENES, which ignores gene-gene correlation
# and inflates significance for co-regulated sets (ribosome, spliceosome,
# translation...). Permuting the ALS/HC labels WITHIN batch, refitting the
# model and recomputing NES gives an empirical p-value that respects that
# correlation. Report a pathway as robust only if it passes both.
#
# Works for RNA (output of 01_*.R) or protein (output of 02_*.R).
#
# Inputs
#   mode           "rna" or "protein"
#   rna_rds        AALS_dream_voom_objects.rds from 01_rna_dream_answerals.R
#   protein_rds    protein_objects.rds from 02_protein_differential_abundance.R
#   fgsea_results  one or more fgsea result CSVs from dream_fgsea_*.R
#                  (columns pathway, NES, padj)
#   gmt_files      the GMT files used for those results
#
# Output
#   permutation_<mode>.csv : pathway, NES_observed (fast fixed-effect model),
#     NES from original fgsea, empirical_p, n_perm, robust flag
#
# NB: remember to select the correct mode!
# ============================================================

suppressPackageStartupMessages({ library(limma); library(fgsea); library(dplyr) })

# ----------------------------
# Settings
# ----------------------------
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
mode          <- "rna"         # "rna" or "protein"
min_gs_size   <- 15; max_gs_size <- 300   # match the 03a run whose fgsea results are retested (300 or 500)
rna_rds       <- "01_single_layer/01a_results_rna_differential_expression/AALS_dream_voom_objects.rds"
protein_rds   <- "01_single_layer/02a_results_protein_da_consortium/protein_objects.rds"
fgsea_dir     <- file.path("01_single_layer", paste0("03a_results_pathway_enrichment_", mode))
if (max_gs_size != 300) fgsea_dir <- file.path(fgsea_dir, paste0("results_fgsea_", mode, "_", max_gs_size))
fgsea_results <- file.path(fgsea_dir, "gsea_validation", "fgsea_ALL_categories_DREAM_t_nonredundant_combined.csv")
gmt_files     <- list.files(file.path("data", "gene_sets"), pattern = "\\.gmt$", recursive = TRUE, full.names = TRUE)
top_n         <- 15        # pathways to test: top N by padj from the fgsea results
n_perm        <- 1000 # also tested on 200
seed          <- 20261014
out_file      <- file.path("01_single_layer", "03b_results_pathway_label_permutation_rna_protein",
  paste0("results_pathway_permutation_", n_perm, if (max_gs_size != 300) paste0("_maxsize", max_gs_size), "_", mode, ".csv"))
dir.create(dirname(out_file), recursive = TRUE, showWarnings = FALSE)

set.seed(seed)

# ----------------------------
# Data and fast model
# ----------------------------
if (mode == "rna") {
  obj <- readRDS(rna_rds)
  v <- obj$voom; meta <- obj$meta; gm <- obj$gene_map
  y <- v$E; w <- v$weights
  symbols <- gm$gene_name[match(rownames(y), gm$gene_id)]
  strata <- meta$seq_batch
  make_design <- function(cond) model.matrix(~ cond + meta$sex + meta$seq_batch)
  fit_t <- function(cond) { f <- eBayes(lmFit(y, make_design(cond), weights = w)); f$t[, 2] }
  cond0 <- meta$condition
} else {
  obj <- readRDS(protein_rds)        # written by 02_protein_differential_abundance.R
  y <- obj$mat; meta <- obj$s; symbols <- obj$gene
  strata <- meta$ms_batch; cond0 <- meta$condition
  fit_t <- function(cond) eBayes(lmFit(y, model.matrix(~ cond + meta$sex + meta$ms_batch)),
                                 trend = TRUE, robust = TRUE)$t[, 2]
}

rank_from_t <- function(tt) {
  ok <- !is.na(symbols) & symbols != "" & !is.na(tt)
  d <- data.frame(g = symbols[ok], t = tt[ok]) %>% group_by(g) %>%
    slice_max(abs(t), n = 1, with_ties = FALSE) %>% ungroup()
  r <- setNames(d$t, d$g); sort(r, decreasing = TRUE)
}

# ----------------------------
# Pathways to test
# ----------------------------
fr <- bind_rows(lapply(fgsea_results, read.csv))
sel <- fr %>% arrange(padj) %>% distinct(pathway, .keep_all = TRUE) %>% head(top_n)
all_pw <- unlist(lapply(gmt_files, gmtPathways), recursive = FALSE)
pw <- all_pw[intersect(sel$pathway, names(all_pw))]
if (length(pw) < nrow(sel)) warning("Pathways not found in GMT files: ", paste(setdiff(sel$pathway, names(pw)), collapse = ", "))

nes_for <- function(r) {
  x <- suppressWarnings(fgsea(pw, r, minSize = min_gs_size, maxSize = max_gs_size, nPermSimple = 1000))
  setNames(x$NES, x$pathway)[names(pw)]
}

# ----------------------------
# Observed and permuted
# Takes very long
# ----------------------------
obs <- nes_for(rank_from_t(fit_t(cond0)))
perm_within <- function(cond, strata) {
  out <- cond
  for (b in unique(strata)) { i <- which(strata == b); if (length(i) > 1) out[i] <- cond[i][sample.int(length(i))] }
  out
}
null <- matrix(NA_real_, n_perm, length(pw), dimnames = list(NULL, names(pw)))
for (k in seq_len(n_perm)) {
  null[k, ] <- nes_for(rank_from_t(fit_t(perm_within(cond0, strata))))
  if (k %% 20 == 0) message("permutation ", k, "/", n_perm)
}

emp <- sapply(names(pw), function(p) {
  o <- obs[p]; z <- null[, p]; z <- z[!is.na(z)]
  if (is.na(o) || !length(z)) return(NA_real_)
  (sum(if (o > 0) z >= o else z <= o) + 1) / (length(z) + 1)   # one-sided in the observed direction
})

res <- data.frame(pathway = names(pw), NES_observed_fast_model = obs[names(pw)],
                  NES_original = sel$NES[match(names(pw), sel$pathway)],
                  padj_original = sel$padj[match(names(pw), sel$pathway)],
                  empirical_p = emp, n_perm = n_perm) %>%
  mutate(empirical_padj = p.adjust(empirical_p, "BH"),
         robust = padj_original < 0.05 & empirical_padj < 0.05 & sign(NES_observed_fast_model) == sign(NES_original)) %>%
  arrange(empirical_p)
dir.create(dirname(out_file), showWarnings = FALSE, recursive = TRUE)
write.csv(res, out_file, row.names = FALSE)
print(res)

