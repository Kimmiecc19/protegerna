#!/usr/bin/env Rscript
# =============================================================================
# 02_sv_workflow_figures.R
#
# Objective 2 - chapter figures for the SV detection -> consolidation ->
# annotation -> prioritisation -> audit workflow (ALS cohort, n = 347).
# Companion to 01_octopusv_stats_plots.R.
#
#   Fig 1  Workflow funnel           : records/events retained at each stage
#   Fig 2  SV length spectrum        : log-length distribution per callset & type
#                                      (Alu ~300 bp and L1 ~6 kb peaks as sanity check)
#   Fig 3  Caller concordance        : % of Manta / TIDDIT calls with a matching
#                                      intersection record, by SV type and size
#   Fig 4  Carrier-count spectrum    : singletons -> common SVs per callset
#   Fig 5  Candidate audit           : (a) final audit disposition by original review
#                                      tier, (b) audited case vs control carriers per
#                                      nominated event, coloured by disposition
#   Fig S2 Historical review         : earlier raw-read outcome by tier (appendix)
#
# Inputs (relative to 02_SV_analysis/; paths set below):
#   02_sv_consolidation/01_results_octopusv/merged/*.cohort.vcf     (OctopuSV cohort VCFs)
#   02_sv_consolidation/01_results_octopusv/stats/*.cohort.stats.txt (record totals)
#   04_sv_prioritization/02c_results_prioritise_annotsv_events/
#       {intersection,union_only}_filtered/*_prioritisation_summary.json
#   05_sv_audit/02_results_audited_release/{summary.json,audited_candidates.tsv,
#                                           release_parameters.json}
#
# Any VCF that is missing is skipped (its callset simply drops out of Figs 2-4).
# Parsed VCF summaries are cached in <out_dir>/cache as .rds, so re-runs to
# tweak a figure take seconds; delete the cache folder to force a re-read.
#
# Usage:  Rscript 02b_sv_workflow_figures.R [sv_dir] [out_dir]
#   sv_dir  defaults to the 02_SV_analysis folder that contains this script
#   out_dir defaults to 02_sv_consolidation/02b_sv_workflow_figures
# Packages: ggplot2 dplyr tidyr stringr stringi purrr readr scales patchwork
#           data.table jsonlite
# =============================================================================

suppressPackageStartupMessages({
  library(ggplot2); library(dplyr); library(tidyr); library(stringr)
  library(stringi); library(purrr); library(readr); library(scales)
  library(patchwork); library(data.table); library(jsonlite)
})

# ------------------------------------------------------- thesis style ------
# Colours, theme_sv() and save_fig() come from 02_sv_thesis_style.R, which loads the
# dissertation palette (thesis_palette.R, Objective 1). Keep it next to this script.
callset_levels <- c("Manta", "TIDDIT", "Intersection", "Union")
# Find this script's folder however it is run: Rscript, RStudio "Source",
# source("..."), or Run-all in the editor. Falls back to the working directory.
script_dir <- local({
  a <- commandArgs(FALSE); f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) return(dirname(normalizePath(f)))
  for (fr in rev(sys.frames())) if (!is.null(fr$ofile)) return(dirname(normalizePath(fr$ofile)))
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    p <- tryCatch(rstudioapi::getSourceEditorContext()$path, error = function(e) "")
    if (nzchar(p) && file.exists(file.path(dirname(p), "02_sv_thesis_style.R"))) return(dirname(normalizePath(p)))
  }
  getwd()
})
style_file <- file.path(script_dir, "02_sv_thesis_style.R")
if (!file.exists(style_file)) stop("02_sv_thesis_style.R not found in ", script_dir,
                                   " - keep it in the same folder as this script.", call. = FALSE)
source(style_file)  # also clears stale palette/figure objects from an earlier run
stopifnot("thesis palette did not load" = exists("theme_sv") && exists("thesis_primary"))
# ---------------------------------------------------------------- paths -----
# Defaults follow this repository: the 02_SV_analysis folder above this script.
args    <- commandArgs(trailingOnly = TRUE)
find_sv_dir <- function(start) {
  d <- start
  for (i in 1:3) {
    if (dir.exists(file.path(d, "02_sv_consolidation"))) return(d)
    d <- dirname(d)
  }
  stop("02_SV_analysis folder not found above ", start, "; pass it as the first argument.", call. = FALSE)
}
sv_dir  <- if (length(args) >= 1) args[1] else find_sv_dir(script_dir)
octo_dir <- file.path(sv_dir, "02_sv_consolidation", "01_results_octopusv")
out_dir <- if (length(args) >= 2) args[2] else file.path(sv_dir, "02_sv_consolidation", "02b_sv_workflow_figures")

merged_dir <- file.path(octo_dir, "merged")
stats_dir  <- file.path(octo_dir, "stats")
# Downstream results: prioritisation (step 04) and the audited release (step 05)
rank_dir   <- file.path(sv_dir, "04_sv_prioritization", "02c_results_prioritise_annotsv_events")
audit_dir  <- file.path(sv_dir, "05_sv_audit", "02_results_audited_release")

vcf_files <- c(
  Manta        = file.path(merged_dir, "manta.cohort.vcf"),
  TIDDIT       = file.path(merged_dir, "tiddit.cohort.vcf"),
  Intersection = file.path(merged_dir, "manta_tiddit.intersect.cohort.vcf"),
  Union        = file.path(merged_dir, "manta_tiddit.union.cohort.vcf")
)

fig_dir   <- file.path(out_dir, "figures")
tab_dir   <- file.path(out_dir, "tables")
cache_dir <- file.path(out_dir, "cache")
walk(c(fig_dir, tab_dir, cache_dir), dir.create, recursive = TRUE, showWarnings = FALSE)

# Matching rule used for caller concordance (Fig 3)
MIN_RECIP_OVERLAP <- 0.5     # DEL / DUP / INV: >= 50% reciprocal overlap, same type
INS_MAX_DIST      <- 500     # INS: breakpoints within 500 bp, same type
SIZE_BREAKS       <- c(50, 100, 200, 500, 1e3, 2e3, 5e3, 1e4, 2e4, 5e4, 1e5 + 1)

wrap_cap <- function(x, width = 130) paste(strwrap(unlist(strsplit(x, "\n")), width), collapse = "\n")
size_lab <- function(x) ifelse(x >= 1e3, paste0(x / 1e3, " kb"), paste0(x, " bp"))

# ============================================================ VCF parsing ====
# One streaming pass per VCF: site fields + per-record genotype tallies.
# NOTE: in OctopuSV cohort VCFs a sample with no call is written as 0/0, so
# "carriers" (0/1 or 1/1) are meaningful but 0/0 is NOT confirmed reference.
read_vcf_sites <- function(path, chunk = 20000L) {
  con <- file(path, open = "r"); on.exit(close(con))
  repeat {
    h <- readLines(con, n = 1L)
    if (!length(h)) stop("No #CHROM header in ", path)
    if (startsWith(h, "#CHROM")) break
  }
  samples <- strsplit(h, "\t", fixed = TRUE)[[1]][-(1:9)]
  is_case <- startsWith(samples, "CASE"); is_ctrl <- startsWith(samples, "CTRL")
  ns <- length(samples)
  out <- list(); k <- 0L
  repeat {
    x <- readLines(con, n = chunk)
    if (!length(x)) break
    f  <- stri_split_fixed(x, "\t", simplify = TRUE)
    gt <- matrix(stri_extract_first_regex(f[, 10:(9 + ns), drop = FALSE], "^[^:]*"),
                 nrow = nrow(f))
    het <- gt == "0/1" | gt == "1/0" | gt == "0|1" | gt == "1|0"
    hom <- gt == "1/1" | gt == "1|1"
    nonref <- het | hom
    info   <- f[, 8]
    getk   <- function(key) stri_match_first_regex(info, paste0("(?:^|;)", key, "=([^;]+)"))[, 2]
    pos    <- as.numeric(f[, 2])
    end    <- suppressWarnings(as.numeric(getk("END")))
    svlen  <- suppressWarnings(abs(as.numeric(getk("SVLEN"))))
    svlen  <- ifelse(is.na(svlen), end - pos, svlen)
    k <- k + 1L
    out[[k]] <- data.table(
      chrom = f[, 1], pos = pos, end = ifelse(is.na(end), pos, end), id = f[, 3],
      svtype = getk("SVTYPE"), svlen = svlen, filter = f[, 7],
      n_het = rowSums(het), n_hom = rowSums(hom),
      n_missing = rowSums(matrix(stri_startswith_fixed(gt, "."), nrow = nrow(gt))),
      carriers_case = rowSums(nonref[, is_case, drop = FALSE]),
      carriers_ctrl = rowSums(nonref[, is_ctrl, drop = FALSE]))
    message("    ", format(sum(map_int(out, nrow)), big.mark = ","), " records")
  }
  res <- rbindlist(out)
  setattr(res, "n_case", sum(is_case)); setattr(res, "n_ctrl", sum(is_ctrl))
  res
}

load_vcf <- function(callset, path) {
  if (!file.exists(path)) { message("  [skip] ", callset, ": not found (", path, ")"); return(NULL) }
  fi  <- file.info(path)
  key <- file.path(cache_dir, sprintf("%s_%s_%s.rds", callset, fi$size, as.integer(fi$mtime)))
  if (file.exists(key)) { message("  [cache] ", callset); return(readRDS(key)) }
  message("  [read] ", callset, " <- ", basename(path))
  d <- read_vcf_sites(path); d[, callset := callset]
  saveRDS(d, key); d
}

message("Reading cohort VCFs")
sites_list <- imap(vcf_files, ~ load_vcf(.y, .x)) |> compact()
if (!length(sites_list)) stop("No VCFs found under ", merged_dir)
n_case <- attr(sites_list[[1]], "n_case"); n_ctrl <- attr(sites_list[[1]], "n_ctrl")
n_all  <- n_case + n_ctrl
sites  <- rbindlist(sites_list, fill = TRUE)
sites[, callset := factor(callset, levels = callset_levels)]
avail  <- levels(droplevels(sites$callset))
primary_contigs <- paste0("chr", c(1:22, "X", "Y"))

# ====================================================== Fig 1: funnel =======
read_total <- function(pattern) {
  f <- list.files(stats_dir, pattern = pattern, full.names = TRUE)
  f <- f[!str_detect(basename(f), "\\.tmp\\.")]
  if (!length(f)) return(NA_real_)
  l <- grep("^Total SVs analyzed", readLines(f[1], warn = FALSE), value = TRUE)
  as.numeric(str_extract(l, "\\d+$"))
}
safe_json <- function(p) if (file.exists(p)) fromJSON(p) else list()
j_int   <- safe_json(file.path(rank_dir, "intersection_filtered", "intersection_prioritisation_summary.json"))
j_union <- safe_json(file.path(rank_dir, "union_only_filtered", "union_only_prioritisation_summary.json"))
j_audit <- safe_json(file.path(audit_dir, "summary.json"))
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) NA_real_ else a

stage_levels <- c(
  "1. Per-caller cohort callset\n(OctopuSV sample merge)",
  "2. Caller consolidation\n(per-sample intersection / union)",
  "3. Overlaps ALS candidate gene\n(AnnotSV candidate-gene filter)",
  "4. Prioritised for review\n(ALSoD evidence or AnnotSV score >= 0.9)",
  "5. Audited primary candidates")

funnel <- tribble(
  ~stage, ~lane, ~n,
  stage_levels[1], "Manta",        read_total("^manta\\.cohort\\.stats\\.txt$"),
  stage_levels[1], "TIDDIT",       read_total("^tiddit\\.cohort\\.stats\\.txt$"),
  stage_levels[2], "Intersection", read_total("intersect\\.cohort\\.stats\\.txt$"),
  stage_levels[2], "Union",        read_total("union\\.cohort\\.stats\\.txt$"),
  stage_levels[3], "Intersection", j_int$intersection_events %||% NA,
  stage_levels[3], "Union-only",   j_union$union_only_events %||% NA,
  stage_levels[4], "Intersection", j_int$intersection_priority_events %||% NA,
  stage_levels[4], "Union-only",   j_union$union_only_priority_events %||% NA,
  stage_levels[5], "Intersection", j_audit$primary_by_provenance$intersection %||% NA,
  stage_levels[5], "Union-only",   j_audit$primary_by_provenance$union_only %||% NA
) |>
  mutate(stage = factor(stage, levels = rev(stage_levels)),
         lane  = factor(lane, levels = c("Manta", "TIDDIT", "Intersection", "Union", "Union-only")))
# Lanes absent from a stage (e.g. union-only events not taken into the audit) are dropped
funnel <- filter(funnel, !is.na(n))
union_audited <- !is.null(j_audit$primary_by_provenance$union_only)
write_csv(funnel, file.path(tab_dir, "workflow_funnel_counts.csv"))

fig1 <- ggplot(funnel, aes(n, stage, fill = lane)) +
  geom_col(position = position_dodge2(width = 0.8, preserve = "single", reverse = TRUE),
           width = 0.75) +
  geom_text(aes(label = paste0(lane, "  ", comma(n))),
            position = position_dodge2(width = 0.8, preserve = "single", reverse = TRUE),
            hjust = -0.08, size = 2.4, colour = ink) +
  scale_x_log10(labels = label_comma(), breaks = 10^(0:6),
                expand = expansion(mult = c(0, 0.35))) +
  scale_fill_manual(values = pal_callset, guide = "none") +
  labs(x = "SV records (stages 1-2) or events (stages 3-5), log scale", y = NULL,
       caption = wrap_cap(paste0(
         "Stage 3: of ", comma((j_union$union_only_events %||% NA) +
                                 (j_union$union_events_excluded_as_intersection %||% NA)),
         " candidate-gene union events, ", j_union$union_events_excluded_as_intersection %||% NA,
         " matched an intersection event (shared source VCF ID or identical chrom/start/end/SVTYPE) ",
         "and were removed; the rest are union-only.\n",
         "Stage 5: ", j_audit$original_nominations %||% NA,
         " nominations re-audited against raw per-sample calls (see Fig 5)",
         if (union_audited) "." else paste0("; the ", j_union$union_only_priority_events %||% NA,
                                            " union-only priority events were not taken into the audit.")))) +
  theme_sv() +
  theme(panel.grid.major.y = element_blank(),
        axis.text.y = element_text(colour = ink, hjust = 0, lineheight = 0.95))
save_fig(fig1, "fig_sv_1_workflow_funnel", height_mm = 105)

# ================================================ Fig 2: length spectrum ====
type_levels <- intersect(c("DEL", "DUP", "INS", "INV"), unique(sites$svtype))
len_breaks  <- seq(log10(50), 5, by = 0.05)
spec <- sites[svtype %in% type_levels & svlen >= 50 & svlen <= 1e5 & chrom %in% primary_contigs,
              .(bin = cut(log10(svlen), len_breaks, include.lowest = TRUE, labels = FALSE)),
              by = .(callset, svtype)]
spec <- spec[, .N, by = .(callset, svtype, bin)][
  , prop := N / sum(N), by = .(callset, svtype)][
  , mid := 10^(len_breaks[bin] + 0.025)]
spec_n <- sites[svtype %in% type_levels & chrom %in% primary_contigs, .N, by = .(callset, svtype)]
spec[, svtype := factor(svtype, levels = type_levels)]
spec_n[, svtype := factor(svtype, levels = type_levels)]

te <- tibble(x = c(300, 6000), lab = c("Alu ~300 bp", "L1 ~6 kb"))
fig2 <- ggplot(spec, aes(mid, prop, colour = callset, linetype = callset)) +
  geom_vline(data = te, aes(xintercept = x), linetype = "22", colour = ink_muted, linewidth = 0.3) +
  geom_text(data = te, aes(x = x, y = Inf, label = lab), inherit.aes = FALSE,
            vjust = 1.3, hjust = -0.05, size = 2.2, colour = ink_muted) +
  geom_line(linewidth = 0.7) +
  facet_wrap(~ svtype, ncol = 2, scales = "free_y") +
  scale_x_log10(breaks = c(100, 300, 1e3, 3e3, 1e4, 3e4, 1e5), labels = size_lab) +
  scale_y_continuous(labels = label_percent(accuracy = 1), expand = expansion(mult = c(0, 0.12))) +
  scale_colour_manual(values = pal_callset_line[avail], name = NULL) +
  scale_linetype_manual(values = lty_callset[avail], name = NULL) +
  guides(colour = guide_legend(override.aes = list(linewidth = 1))) +
  labs(x = "SV length (log scale)", y = "Share of callset's SVs of this type (per 0.05 log10 bin)",
       caption = wrap_cap("Primary chromosomes only; 50 bp-100 kb. Lines are within-callset, within-type proportions so shapes are comparable across callsets of different size.")) +
  theme_sv()
save_fig(fig2, "fig_sv_2_length_spectrum", height_mm = 115)
write_csv(as_tibble(spec), file.path(tab_dir, "length_spectrum.csv"))

# ============================================ Fig 3: caller concordance ======
match_to_ref <- function(q, ref) {
  q <- copy(q)[, qid := .I]
  hits <- integer()
  sv_iv <- c("DEL", "DUP", "INV")
  qa <- q[svtype %in% sv_iv, .(qid, chrom, svtype, start = pos, end = pmax(end, pos + 1))]
  ra <- ref[svtype %in% sv_iv, .(chrom, svtype, start = pos, end = pmax(end, pos + 1))]
  if (nrow(qa) && nrow(ra)) {
    setkey(ra, chrom, svtype, start, end)
    ov <- foverlaps(qa, ra, by.x = c("chrom", "svtype", "start", "end"), nomatch = NULL)
    ov[, olap := pmin(end, i.end) - pmax(start, i.start)]
    ov[, ro := olap / pmax(end - start, i.end - i.start)]
    hits <- c(hits, unique(ov[ro >= MIN_RECIP_OVERLAP, qid]))
  }
  qi <- q[svtype == "INS", .(qid, chrom, svtype, start = pos - INS_MAX_DIST, end = pos + INS_MAX_DIST)]
  ri <- ref[svtype == "INS", .(chrom, svtype, start = pos, end = pos)]
  if (nrow(qi) && nrow(ri)) {
    setkey(ri, chrom, svtype, start, end)
    hits <- c(hits, unique(foverlaps(qi, ri, nomatch = NULL)$qid))
  }
  q[, matched := qid %in% hits][]
}

conc <- NULL
if ("Intersection" %in% avail) {
  ref <- sites[callset == "Intersection"]
  conc <- rbindlist(lapply(intersect(c("Manta", "TIDDIT"), avail), function(cs) {
    m <- match_to_ref(sites[callset == cs & svtype %in% type_levels], ref)
    m[, size_bin := cut(svlen, SIZE_BREAKS, right = FALSE)]
    m[!is.na(size_bin), .(n = .N, matched = sum(matched)), by = .(callset, svtype, size_bin)]
  }))
}
if (!is.null(conc) && nrow(conc)) {
  bin_lo <- head(SIZE_BREAKS, -1); bin_hi <- tail(SIZE_BREAKS, -1)
  conc[, i := as.integer(size_bin)][, mid := sqrt(bin_lo[i] * pmin(bin_hi[i], 1e5))][
    , pct := matched / n][, svtype := factor(svtype, levels = type_levels)]
  conc_tot <- conc[, .(n = sum(n), matched = sum(matched)), by = .(callset, svtype)][
    , lab := sprintf("%s: %s of %s (%s)", callset, comma(matched), comma(n),
                     percent(matched / n, accuracy = 0.1))]
  write_csv(as_tibble(conc), file.path(tab_dir, "caller_concordance_by_size.csv"))

  conc_types <- conc[, .(any = sum(matched) > 0), by = svtype][any == TRUE, svtype]
  cp <- conc[svtype %in% conc_types]
  lab_df <- conc_tot[svtype %in% conc_types][
    , .(label = paste(lab, collapse = "\n")), by = svtype]

  fig3 <- ggplot(cp, aes(mid, pct, colour = callset)) +
    geom_line(linewidth = 0.7) +
    geom_point(aes(size = n, fill = callset, shape = callset), colour = tint_point_outline, stroke = 0.3) +
    geom_text(data = lab_df, aes(x = 55, y = 1.02, label = label), inherit.aes = FALSE,
              hjust = 0, vjust = 1, size = 2.2, colour = ink, lineheight = 0.95) +
    facet_wrap(~ svtype, nrow = 1) +
    scale_x_log10(breaks = c(100, 300, 1e3, 3e3, 1e4, 3e4, 1e5), labels = size_lab) +
    scale_y_continuous(labels = label_percent(), limits = c(0, 1.02)) +
    scale_colour_manual(values = pal_callset_line, name = NULL) +
    scale_fill_manual(values = pal_callset, name = NULL) +
    scale_shape_manual(values = shape_callset, name = NULL) +
    scale_size_area(max_size = 3.2, labels = label_comma(), name = "Calls in size bin") +
    labs(x = "SV length (log scale)", y = "Calls with a matching intersection record",
         caption = wrap_cap(sprintf(paste0(
           "Match = same type and >= %d%% reciprocal overlap with an intersection record (positional; ",
           "intersection records carry Manta coordinates, so TIDDIT concordance is conservative).\n",
           "INS (Manta only) and INV (TIDDIT only) cannot be concordant by construction and are not shown."),
           round(MIN_RECIP_OVERLAP * 100)))) +
    theme_sv()
  save_fig(fig3, "fig_sv_3_caller_concordance", height_mm = 95)
}

# ============================================ Fig 4: carrier spectrum =======
carrier_bins <- function(k, n) {
  pct5 <- ceiling(0.05 * n); pct50 <- ceiling(0.5 * n)
  cut(k, c(-Inf, 0, 1, 2, 5, pct5 - 1, pct50 - 1, Inf),
      labels = c("0 (no GT call)", "1 (singleton)", "2", "3-5",
                 sprintf("6-%d (<5%%)", pct5 - 1), sprintf("%d-%d (5-50%%)", pct5, pct50 - 1),
                 sprintf(">=%d (>=50%%)", pct50)))
}
cs <- sites[chrom %in% primary_contigs][, carriers := n_het + n_hom][
  , bin := carrier_bins(carriers, n_all)][, .N, by = .(callset, bin)][
  , prop := N / sum(N), by = callset]
write_csv(as_tibble(cs), file.path(tab_dir, "carrier_count_spectrum.csv"))

fig4 <- ggplot(cs, aes(bin, prop, fill = callset)) +
  geom_col(position = position_dodge(width = 0.84), width = 0.8) +
  scale_fill_manual(values = pal_callset[avail], name = NULL) +
  scale_y_continuous(labels = label_percent(), expand = expansion(mult = c(0, 0.05))) +
  labs(x = sprintf("Carriers per SV (0/1 or 1/1) among %d genomes", n_all),
       y = "Share of callset",
       caption = wrap_cap(paste("Primary chromosomes only. OctopuSV writes 0/0 for samples without a call,",
                       "so carrier counts are lower bounds and 0/0 is not confirmed reference."))) +
  theme_sv() + rot_x
save_fig(fig4, "fig_sv_4_carrier_spectrum", height_mm = 90)

# ============================================ Fig 5: candidate audit =========
# Built only from the final audited release (audited_candidates.tsv), so every
# count, panel and caption number follows the data. Re-running after a new
# audit release updates the figure without editing this block.
aud_file <- file.path(audit_dir, "audited_candidates.tsv")
if (!file.exists(aud_file)) {
  message("  [skip] Fig 5: ", aud_file, " not found")
} else {
  rel_par <- safe_json(file.path(audit_dir, "release_parameters.json"))
  n_case_rel <- rel_par$case_n    %||% n_case
  n_ctrl_rel <- rel_par$control_n %||% n_ctrl
  ctrl_thr   <- rel_par$control_count_review_threshold %||% 3

  disp_map <- c(primary_candidate                = "Primary candidate",
                exploratory_review_only          = "Exploratory review only",
                deprioritised_shared_or_frequent = "Deprioritised (shared/frequent)")
  reason_map <- c(matching_sensitive_tier_or_support = "tier/support changes with matching policy",
                  event_support_rule_not_met         = "event support rule not met",
                  low_mapping_quality                = "low mapping quality")

  aud <- read_tsv(aud_file, show_col_types = FALSE, guess_max = 1e4,
                  col_types = cols(.default = col_character())) |>
    mutate(across(c(tier, audited_tier, audited_case_carriers, audited_control_carriers),
                  as.integer),
           provenance = recode(shortlist, intersection = "Intersection", union_only = "Union-only"),
           provenance = factor(provenance, levels = c("Intersection", "Union-only")),
           outcome = recode(old_outcome,
                            technically_supported = "Technically supported",
                            supported_with_caveats = "Supported with caveats",
                            uncertain = "Uncertain",
                            likely_artefact_or_merge_error = "Likely artefact / merge error",
                            excluded_failed_caller_filter = "Excluded (failed caller filter)"),
           outcome = factor(outcome, levels = names(pal_outcome)),
           disposition = case_when(
             disposition %in% names(disp_map) ~ unname(disp_map[disposition]),
             str_starts(disposition, "held")     ~ "Held",
             str_starts(disposition, "excluded") ~ "Excluded (failed caller filter)",
             TRUE ~ disposition),
           disposition = factor(disposition, levels = names(pal_disposition)),
           hold_reasons = replace_na(hold_reasons, ""))
  if (anyNA(aud$disposition)) stop("Fig 5: unrecognised disposition value(s) in ", aud_file, call. = FALSE)

  n_nom    <- nrow(aud)
  multi_pr <- n_distinct(aud$provenance) > 1
  disp_present <- levels(droplevels(aud$disposition))
  pal_disp_use <- pal_disposition[disp_present]

  tier_lab <- function(t) sprintf("Tier %s", t)

  # --- (a) disposition by original review tier ------------------------------
  a_dat <- count(aud, provenance, tier, disposition) |>
    mutate(tier_f = factor(tier_lab(tier), levels = tier_lab(sort(unique(aud$tier)))))
  a_tot <- aud |>
    group_by(provenance, tier) |>
    summarise(n = n(), moved = sum(audited_tier != tier, na.rm = TRUE),
              moved_to = paste(sort(unique(audited_tier[audited_tier != tier])), collapse = "/"),
              .groups = "drop") |>
    mutate(tier_f = factor(tier_lab(tier), levels = levels(a_dat$tier_f)),
           lab = ifelse(moved > 0,
                        sprintf("n = %d\n%d re-tiered\nto Tier %s", n, moved, moved_to),
                        sprintf("n = %d", n)))

  p5_a <- ggplot(a_dat, aes(tier_f, n, fill = disposition)) +
    geom_col(width = 0.68, position = position_stack(reverse = TRUE)) +
    geom_text(aes(label = ifelse(n >= 2, n, ""), colour = disposition),
              position = position_stack(vjust = 0.5, reverse = TRUE),
              size = 2.4, fontface = "bold", show.legend = FALSE) +
    geom_text(data = a_tot, aes(tier_f, n, label = lab), inherit.aes = FALSE,
              vjust = -0.25, size = 2.1, colour = ink, lineheight = 0.9) +
    scale_colour_manual(values = text_on(pal_disp_use), guide = "none") +
    scale_fill_manual(values = pal_disp_use, name = "Audit disposition") +
    scale_y_continuous(expand = expansion(mult = c(0, 0.28))) +
    labs(x = "Original review tier", y = "Nominated events") +
    theme_sv() +
    theme(panel.grid.major.x = element_blank())
  if (multi_pr) p5_a <- p5_a + facet_wrap(~ provenance)

  # --- (b) audited carriers: cases vs controls --------------------------------
  # log10(k + 1) axes so 0 carriers is shown; coincident events are pooled into one
  # point sized by count (labelled when >= 3), with a small horizontal offset between dispositions.
  tr <- function(k) log10(k + 1)
  brk <- c(0, 1, 2, 5, 10, 20, 50, 100, 300)
  offs <- c("Primary candidate" = -0.045, "Exploratory review only" = 0.045)
  b_dat <- aud |>
    count(provenance, disposition, audited_case_carriers, audited_control_carriers, name = "n") |>
    mutate(x = tr(audited_case_carriers) +
             coalesce(unname(offs[as.character(disposition)]), 0),
           y = tr(audited_control_carriers))

  p5_b <- ggplot(b_dat, aes(x, y)) +
    annotate("rect", xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = 0.07,
             fill = gold_tint(0.12), colour = NA) +
    annotate("text", x = tr(max(brk)), y = 0.085, label = "case-only",
             hjust = 1, vjust = 0, size = 2.1, colour = ink_muted, fontface = "italic") +
    geom_hline(yintercept = tr(ctrl_thr) - 0.5 * (tr(ctrl_thr) - tr(ctrl_thr - 1)),
               linetype = "22", colour = ink_muted, linewidth = 0.3) +
    annotate("text", x = tr(0), y = tr(ctrl_thr) - 0.5 * (tr(ctrl_thr) - tr(ctrl_thr - 1)),
             label = sprintf("%d or more control carriers", ctrl_thr),
             hjust = 0, vjust = -0.4, size = 2.1, colour = ink_muted) +
    geom_point(aes(size = n, fill = disposition), shape = 21,
               colour = tint_point_outline, stroke = 0.35, alpha = 0.95) +
    geom_text(aes(label = ifelse(n >= 3, n, "")), size = 2, colour = ink, fontface = "bold") +
    scale_fill_manual(values = pal_disp_use, guide = "none") +
    scale_size_area(max_size = 6, breaks = c(1, 5, 15), name = "Events") +
    scale_x_continuous(breaks = tr(brk), labels = brk,
                       limits = tr(c(0, max(300, max(aud$audited_case_carriers)))),
                       expand = expansion(mult = 0.04)) +
    scale_y_continuous(breaks = tr(brk[brk <= n_ctrl_rel]), labels = brk[brk <= n_ctrl_rel],
                       limits = tr(c(0, n_ctrl_rel)), expand = expansion(mult = 0.05)) +
    labs(x = sprintf("Audited case carriers (of %d)", n_case_rel),
         y = sprintf("Audited control carriers (of %d)", n_ctrl_rel)) +
    theme_sv() +
    theme(panel.grid.minor = element_blank())
  if (multi_pr) p5_b <- p5_b + facet_wrap(~ provenance)

  # --- caption from the data ------------------------------------------------
  dn <- table(aud$disposition)  # includes zero counts for every disposition level
  n_primary <- dn[["Primary candidate"]]
  disp_counts <- sprintf("%d primary candidates, %d exploratory review only, %d deprioritised as shared or frequent.",
                         n_primary, dn[["Exploratory review only"]], dn[["Deprioritised (shared/frequent)"]])
  reason_txt <- function(d) {
    r <- aud |> filter(disposition == d, hold_reasons != "") |>
      separate_rows(hold_reasons, sep = ";") |> count(hold_reasons, sort = TRUE)
    if (!nrow(r)) return("")
    paste0(" (", paste(sprintf("%s, n = %d",
                               coalesce(unname(reason_map[r$hold_reasons]), r$hold_reasons), r$n),
                       collapse = "; "), ")")
  }
  prov_txt <- if (multi_pr) {
    paste(sprintf("%s n = %d", names(table(droplevels(aud$provenance))),
                  table(droplevels(aud$provenance))), collapse = ", ")
  } else sprintf("all from the %s shortlist", tolower(as.character(aud$provenance[1])))
  n_stable_prim <- sum(aud$disposition == "Primary candidate" &
                         aud$decision_stable_across_all_matching_policies == "True")
  cap_intro <- sprintf("%d nominated events (%s) re-audited against raw per-sample Manta/TIDDIT calls; ", n_nom, prov_txt)
  cap_tiers <- "Tier 1: case-only, stronger ALSoD evidence; 2: case-only, AnnotSV/ALSoD priority; 3: seen in controls; 4: frequency or genotype QC flag"
  cap_union <- if (!"Union-only" %in% aud$provenance && !is.na(j_union$union_only_priority_events %||% NA))
    sprintf(" The %d union-only priority events (Fig 1, stage 4) were not part of this audit.",
            as.integer(j_union$union_only_priority_events)) else ""

  cap5 <- paste0(
    cap_intro, disp_counts, "\n",
    "(a) Bars: final disposition within each original review tier; labels above bars give events whose tier changed on raw-call recount. ",
    cap_tiers, ".\n",
    "(b) Each point is one or more events with the same audited carrier counts (axes log10(k + 1)); 0/0 genotypes are unknown, not confirmed reference. ",
    sprintf("Primary candidates (%d of %d stable across all matching policies) are audited Tier 1-2 and case-only; ",
            n_stable_prim, n_primary),
    "exploratory events are case-only but carry a flag", reason_txt("Exploratory review only"), "; an event can carry both.",
    cap_union)

  fig5 <- (p5_a + p5_b) +
    plot_layout(widths = c(1, 1.25), guides = "collect") +
    plot_annotation(tag_levels = "a", caption = wrap_cap(cap5, 120),
                    theme = theme_sv()) &
    theme(legend.position = "bottom", legend.box = "vertical", legend.box.just = "left")
  save_fig(fig5, "fig_sv_5_audit_disposition", height_mm = 125)

  # Single-panel version: panel (a) only, untagged, with its own caption
  cap5a <- paste0(
    cap_intro, disp_counts, " ",
    "Bars show the final disposition within each original review tier; labels above bars give the tier size and any events whose tier changed on raw-call recount.\n",
    cap_tiers, ". ",
    sprintf("Primary candidates (%d of %d stable across all matching policies) are audited Tier 1-2 and case-only.",
            n_stable_prim, n_primary),
    cap_union)
  fig5a <- p5_a +
    guides(fill = guide_legend(ncol = 1)) +
    labs(caption = wrap_cap(cap5a, 105)) +
    theme(legend.position = "right", plot.caption.position = "plot")
  save_fig(fig5a, "fig_sv_5a_audit_disposition_by_tier", width_mm = 150, height_mm = 105)

  # Appendix: earlier (superseded) raw-call review outcome, by tier
  p_s2 <- aud |> count(provenance, tier, outcome) |>
    mutate(tier_f = tier_lab(tier)) |>
    ggplot(aes(tier_f, n, fill = outcome)) +
    geom_col(width = 0.68, position = position_stack(reverse = TRUE)) +
    geom_text(aes(label = ifelse(n >= 2, n, ""), colour = outcome),
              position = position_stack(vjust = 0.5, reverse = TRUE),
              size = 2.3, show.legend = FALSE) +
    scale_colour_manual(values = text_on(pal_outcome), guide = "none") +
    scale_fill_manual(values = pal_outcome[levels(droplevels(aud$outcome))],
                      name = "Technical evidence\n(earlier raw-read review)") +
    scale_y_continuous(expand = expansion(mult = c(0, 0.04))) +
    labs(x = "Original review tier", y = "Nominated events",
         caption = wrap_cap(paste(
           "Outcomes from the earlier raw-read review, superseded by the final audit (Fig 5) and",
           "shown for traceability only. Tiers order manual review and are not clinical classifications."))) +
    guides(fill = guide_legend(ncol = 1)) +
    theme_sv() + theme(legend.position = "right", panel.grid.major.x = element_blank())
  if (multi_pr) p_s2 <- p_s2 + facet_wrap(~ provenance)
  save_fig(p_s2, "fig_sv_S2_historical_review", height_mm = 85)

  write_csv(count(aud, provenance, tier, audited_tier, outcome, disposition),
            file.path(tab_dir, "review_audit_counts.csv"))
  write_csv(select(b_dat, -x, -y), file.path(tab_dir, "audit_carrier_counts.csv"))
}

message("\nDone. Figures -> ", fig_dir)

