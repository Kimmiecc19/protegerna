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
#project_dir   <- "C:/Users/USER-PC/OneDrive/Documents/2026 PhD/protegerna/05_ALS_integration"
#setwd(project_dir)
mode          <- "rna"         # "rna" or "protein"
rna_rds       <- "results_ALS_integration/results_01_rna_dream/AALS_dream_voom_objects.rds"
protein_rds   <- "results_ALS_integration/results_07_protein_da_consortium/protein_objects.rds"
fgsea_results <- if (mode == "rna") "results_ALS_integration/results_02_fgsea_rna/gsea_validation/fgsea_ALL_categories_DREAM_t_nonredundant_combined.csv" else
                 "results_ALS_integration/results_08_fgsea_protein/gsea_validation/fgsea_ALL_categories_DREAM_t_nonredundant_combined.csv"
gmt_files     <- list.files("data_ALS_integration/gene_sets", pattern = "\\.gmt$", recursive = TRUE, full.names = TRUE)
top_n         <- 15        # pathways to test: top N by padj from the fgsea results
n_perm        <- 5000 # also tested on 200
min_gs_size   <- 15; max_gs_size <- 300
seed          <- 20261014
out_file      <- paste0("results_ALS_integration/results_pathway_permutation_5000_", mode, ".csv")

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

