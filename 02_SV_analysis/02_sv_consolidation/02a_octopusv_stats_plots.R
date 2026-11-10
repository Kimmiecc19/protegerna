#!/usr/bin/env Rscript
# =============================================================================
# 01_octopusv_stats_plots.R
#
# Objective 2 - Figures summarising the OctopuSV cohort SV callsets
#   * manta.cohort                 (Manta, sample-merged)
#   * tiddit.cohort                (TIDDIT, sample-merged)
#   * manta_tiddit.intersect.cohort (per-sample Manta AND TIDDIT, then cohort-merged)
#   * manta_tiddit.union.cohort     (per-sample Manta OR TIDDIT, then cohort-merged)
#
# Input : the `octopusv stat --report` text files (*.cohort.stats.txt)
#         + the reference FASTA index (.fai) for true chromosome lengths.
# Output: publication figures (PDF + 600 dpi PNG) and tidy CSV tables
#         in <out_dir>/figures and <out_dir>/tables.
#
# Usage (from anywhere):
#   Rscript 02a_octopusv_stats_plots.R [stats_dir] [fai] [out_dir]
# Defaults: stats_dir = 01_results_octopusv/stats, out_dir = 01_results_octopusv/thesis_figures
# (both beside this script); fai = $GRCH38_FAI. The reference index is not in the repository.
#
# NOTE on densities: the "Density: x SVs/Mb" values printed by OctopuSV are
# count / 100 for every contig (e.g. chr1 5742 SVs -> 57.42; a 1-kb decoy with
# 14 SVs -> 14,000,000). They are therefore NOT used. Densities here are
# recomputed from the GRCh38 .fai contig lengths.
# =============================================================================

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(stringr)
  library(purrr)
  library(readr)
  library(scales)
  library(patchwork)
})

# ------------------------------------------------------- thesis style ------
# Colours, theme and save_fig() come from 02_sv_thesis_style.R, which loads the
# dissertation palette (thesis_palette.R, Objective 1). Keep it next to this script.
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
# Defaults follow this repository: 02_SV_analysis/02_sv_consolidation/01_results_octopusv.
base_dir  <- file.path(script_dir, "01_results_octopusv")
args      <- commandArgs(trailingOnly = TRUE)
stats_dir <- if (length(args) >= 1) args[1] else file.path(base_dir, "stats")
# GRCh38_full_analysis_set_plus_decoy_hla.fa.fai is not in the repository: pass it or set GRCH38_FAI.
fai_file  <- if (length(args) >= 2) args[2] else Sys.getenv("GRCH38_FAI",
  unset = "/path/to/reference/GRCh38_full_analysis_set_plus_decoy_hla.fa.fai")
if (!file.exists(fai_file)) stop("Reference index not found: ", fai_file,
  ". Pass it as the second argument or set GRCH38_FAI.", call. = FALSE)
out_dir   <- if (length(args) >= 3) args[3] else file.path(base_dir, "thesis_figures")

fig_dir <- file.path(out_dir, "figures")
tab_dir <- file.path(out_dir, "tables")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)

# ------------------------------------------------------- callset metadata ---
# `pattern` is matched against the file name, so hashed/renamed copies still work.
callsets <- tibble::tribble(
  ~pattern,                    ~callset,
  "manta_tiddit\\.intersect",  "Intersection",
  "manta_tiddit\\.union",      "Union",
  "(^|[-_/])manta\\.cohort",   "Manta",
  "(^|[-_/])tiddit\\.cohort",  "TIDDIT"
)
callset_levels <- c("Manta", "TIDDIT", "Intersection", "Union")

# ================================================================ parsing ====
num <- function(x) as.numeric(str_remove_all(x, "[^0-9.eE+-]"))

# Split a report into named sections (">>>>>>> Type Analysis" -> "Type Analysis")
split_sections <- function(lines) {
  hdr   <- str_detect(lines, "^>>>>>>> ")
  name  <- str_remove(lines[hdr], "^>>>>>>> ")
  idx   <- cumsum(hdr)
  secs  <- split(lines, idx)[-1]              # drop the preamble
  secs  <- map(secs, ~ .x[-1])                # drop the header line itself
  set_names(secs, name)
}

# "Key   = value" -> tibble(key, value)
kv <- function(x) {
  x <- x[str_detect(x, "=")]
  tibble(key   = str_trim(str_extract(x, "^[^=]+")),
         value = str_trim(str_remove(x, "^[^=]+=\\s*")))
}

parse_octopusv_stats <- function(file) {
  lines <- readLines(file, warn = FALSE)
  s     <- split_sections(lines)

  # --- SV types -------------------------------------------------------------
  types <- kv(s[["Type Analysis"]]) |>
    filter(str_detect(value, "^\\d+ \\(")) |>
    transmute(type = key, n = num(str_extract(value, "^\\d+")))

  # --- size summary + size bins ----------------------------------------------
  size_kv <- kv(s[["Size Analysis"]])
  size_summary <- size_kv |>
    filter(key %in% c("Total SVs analyzed", "Minimum size", "Maximum size",
                      "Mean size", "Median size", "Standard deviation")) |>
    mutate(value = num(value)) |>
    pivot_wider(names_from = key, values_from = value) |>
    rename(total = `Total SVs analyzed`, min_bp = `Minimum size`,
           max_bp = `Maximum size`, mean_bp = `Mean size`,
           median_bp = `Median size`, sd_bp = `Standard deviation`)
  size_bins <- size_kv |>
    filter(str_detect(key, "bp|kb")) |>
    filter(!str_detect(key, "size|Standard")) |>
    transmute(bin_raw = key, n = num(value))

  # --- chromosomes --------------------------------------------------------------
  chrom <- str_match(s[["Chromosome Analysis"]], "^(\\S+)\\s+=\\s+(\\d+) SVs")
  chrom <- tibble(contig = chrom[, 2], n = as.numeric(chrom[, 3])) |> filter(!is.na(contig))

  # --- QC -------------------------------------------------------------------------
  qc <- kv(s[["Qc Analysis"]]) |>
    filter(value != "") |>
    mutate(value_num = num(str_extract(value, "^[0-9.]+")))

  # --- genotypes (per sample + "Overall") ---------------------------------------
  g  <- s[["Genotype Analysis"]]
  owner <- rep(NA_character_, length(g))
  cur   <- NA_character_
  for (i in seq_along(g)) {
    if (str_detect(g[i], "Genotypes =\\s*$")) cur <- str_trim(str_remove(g[i], "Genotypes =\\s*$"))
    else if (str_detect(g[i], "^Overall\\s+=")) cur <- "Overall"
    owner[i] <- cur
  }
  gm <- str_match(g, "^([0-9.]+[/|][0-9.]+)\\s+=\\s+(\\d+)")
  genotypes <- tibble(sample = owner, gt = gm[, 2], n = as.numeric(gm[, 3])) |>
    filter(!is.na(gt), !is.na(sample))

  list(types = types, size_summary = size_summary, size_bins = size_bins,
       chrom = chrom, qc = qc, genotypes = genotypes)
}

# ============================================================== load data ====
files <- list.files(stats_dir, pattern = "\\.cohort\\.stats\\.txt$", full.names = TRUE)
files <- files[!str_detect(basename(files), "\\.tmp\\.")]
if (length(files) == 0) stop("No *.cohort.stats.txt files found in: ", stats_dir)

label_file <- function(f) {
  hit <- callsets |> filter(str_detect(basename(f), pattern)) |> slice(1)
  if (nrow(hit) == 0) NA_character_ else hit$callset
}
file_map <- tibble(file = files, callset = map_chr(files, label_file)) |>
  filter(!is.na(callset)) |>
  distinct(callset, .keep_all = TRUE)
message("Parsing ", nrow(file_map), " OctopuSV reports:\n  ",
        paste(file_map$callset, basename(file_map$file), sep = " <- ", collapse = "\n  "))

parsed <- set_names(map(file_map$file, parse_octopusv_stats), file_map$callset)

bind <- function(el) {
  imap(parsed, ~ mutate(.x[[el]], callset = .y)) |>
    list_rbind() |>
    mutate(callset = factor(callset, levels = callset_levels))
}

types        <- bind("types")
size_summary <- bind("size_summary")
size_bins    <- bind("size_bins")
chrom        <- bind("chrom")
qc           <- bind("qc")
genotypes    <- bind("genotypes")

# Legend labels carrying n and median size
lab_n <- size_summary |>
  mutate(lab = sprintf("%s (n = %s; median %s bp)", callset,
                       comma(total), comma(median_bp, accuracy = 1))) |>
  select(callset, lab) |> tibble::deframe()
lab_n <- lab_n[intersect(callset_levels, names(lab_n))]

# ---------------------------------------------------- reference lengths -----
fai <- read_tsv(fai_file, col_names = c("contig", "length", "offset", "linebases", "linewidth"),
                col_types = "cdddd", progress = FALSE)
primary <- paste0("chr", c(1:22, "X", "Y"))

# ======================================================= Figure 1: types ====
type_levels <- intersect(c("DEL", "DUP", "INS", "INV", "BND", "TRA"), unique(types$type))
types <- types |>
  complete(callset, type = type_levels, fill = list(n = 0)) |>
  mutate(type = factor(type, levels = type_levels)) |>
  group_by(callset) |> mutate(prop = n / sum(n)) |> ungroup()

p1a <- ggplot(types, aes(callset, n, fill = type)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = ifelse(n > 0, comma(n), "0")), vjust = -0.35, size = 2.3, colour = ink) +
  facet_wrap(~ type, nrow = 1) +
  scale_fill_manual(values = pal_type, guide = "none") +
  scale_y_continuous(labels = label_comma(), expand = expansion(mult = c(0, 0.12))) +
  coord_cartesian(clip = "off") +
  labs(x = NULL, y = "SV records in cohort callset") +
  theme_sv() + rot_x

p1b <- ggplot(types, aes(callset, prop, fill = type)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = ifelse(prop >= 0.04, percent(prop, accuracy = 0.1), ""), colour = type),
            position = position_stack(vjust = 0.5), size = 2.3, show.legend = FALSE) +
  scale_fill_manual(values = pal_type, name = "SV type") +
  scale_colour_manual(values = text_on(pal_type), guide = "none") +
  scale_y_continuous(labels = label_percent(), expand = expansion(mult = c(0, 0.02))) +
  labs(x = NULL, y = "Proportion of callset") +
  guides(fill = guide_legend(nrow = 2)) +
  theme_sv() + rot_x

fig1 <- (p1a | p1b) + plot_layout(widths = c(2.2, 1)) + plot_annotation(tag_levels = "a")
save_fig(fig1, "fig_octopusv_1_sv_types", height_mm = 95)

# ======================================================== Figure 2: size ====
bin_label <- function(x) {
  x <- str_squish(x)
  case_when(
    x == "0-50 bp"      ~ "50 bp",          # OctopuSV min size is 50 bp -> bin is exactly 50 bp
    x == "51-100 bp"    ~ "51-100 bp",
    x == "101-500 bp"   ~ "101-500 bp",
    x == "501-1 kb"     ~ "501 bp-1 kb",
    x == "1 kb-10 kb"   ~ "1-10 kb",
    x == ">10 kb"       ~ ">10 kb",
    TRUE ~ x)
}
bin_levels <- c("50 bp", "51-100 bp", "101-500 bp", "501 bp-1 kb", "1-10 kb", ">10 kb")

size_bins <- size_bins |>
  mutate(bin = factor(bin_label(bin_raw), levels = bin_levels)) |>
  group_by(callset) |> mutate(prop = n / sum(n)) |> ungroup()

p2a <- ggplot(size_bins, aes(bin, prop, fill = callset)) +
  geom_col(position = position_dodge(width = 0.82), width = 0.78) +
  scale_fill_manual(values = pal_callset, labels = lab_n, name = NULL) +
  scale_y_continuous(labels = label_percent(), expand = expansion(mult = c(0, 0.05))) +
  labs(x = "SV length", y = "Proportion of callset") +
  guides(fill = guide_legend(nrow = 2)) +
  theme_sv()

p2b <- ggplot(size_bins, aes(bin, n, fill = callset)) +
  geom_col(position = position_dodge(width = 0.82), width = 0.78) +
  scale_fill_manual(values = pal_callset, guide = "none") +
  scale_y_continuous(labels = label_comma(), expand = expansion(mult = c(0, 0.05))) +
  labs(x = "SV length", y = "SV records") +
  theme_sv()

fig2 <- (p2a / p2b) + plot_layout(guides = "collect") +
  plot_annotation(tag_levels = "a") & theme(legend.position = "bottom")
save_fig(fig2, "fig_octopusv_2_sv_sizes", height_mm = 140)

# ============================================== Figure 3: genomic distribution
chrom <- chrom |>
  left_join(select(fai, contig, length), by = "contig") |>
  mutate(is_primary = contig %in% primary)

# share of calls on non-primary contigs (decoys, unplaced, random, alt, HLA, EBV, chrM)
nonprim <- chrom |>
  group_by(callset) |>
  summarise(total = sum(n), off_primary = sum(n[!is_primary]), .groups = "drop") |>
  mutate(prop = off_primary / total)

p3b <- ggplot(nonprim, aes(callset, prop, fill = callset)) +
  geom_col(width = 0.65) +
  geom_text(aes(label = sprintf("%s\n(%s)", percent(prop, accuracy = 0.1), comma(off_primary))),
            vjust = -0.25, size = 2.3, colour = ink, lineheight = 0.9) +
  scale_fill_manual(values = pal_callset, guide = "none") +
  scale_y_continuous(labels = label_percent(), expand = expansion(mult = c(0, 0.3))) +
  coord_cartesian(clip = "off") +
  labs(x = NULL, y = "SVs on non-primary contigs") +
  theme_sv() + rot_x

top_contigs <- chrom |>
  filter(!is_primary) |>
  group_by(contig) |> summarise(max_n = max(n), .groups = "drop") |>
  slice_max(max_n, n = 10, with_ties = FALSE) |> pull(contig)

heat <- chrom |>
  filter(contig %in% top_contigs) |>
  select(callset, contig, n) |>
  complete(callset, contig = top_contigs, fill = list(n = 0)) |>
  mutate(contig = factor(contig, levels = rev(top_contigs)))

p3c <- ggplot(heat, aes(callset, contig, fill = n)) +
  geom_tile(colour = "white", linewidth = 0.6) +
  geom_text(aes(label = comma(n), colour = n > max(n) * 0.2), size = 2.2, show.legend = FALSE) +
  scale_colour_manual(values = c(`TRUE` = "white", `FALSE` = ink)) +
  scale_fill_gradient(low = seq_gold[["low"]], high = seq_gold[["high"]], trans = "log1p",
                      breaks = c(0, 10, 100, 1000, 10000), labels = label_comma(),
                      name = "SV records") +
  labs(x = NULL, y = NULL) +
  theme_sv() + rot_x +
  theme(panel.grid = element_blank(), axis.line.x = element_blank(),
        legend.position = "right", legend.key.height = unit(8, "mm"))

# Appendix figure: non-primary contig burden (per-contig densities are in the
# octopusv_contig_counts_density.csv table).
fig3 <- (p3b | p3c) + plot_layout(widths = c(1, 1.8)) +
  plot_annotation(tag_levels = "a")
save_fig(fig3, "fig_octopusv_3_nonprimary_contigs", height_mm = 95)

# =================================== Figure 4: per-sample genotype burden ====
per_sample <- genotypes |>
  filter(sample != "Overall") |>
  mutate(gt = str_replace(gt, "\\|", "/"),
         class = case_when(gt %in% c("0/1", "1/0") ~ "het",
                           gt == "1/1" ~ "hom_alt",
                           gt == "0/0" ~ "hom_ref",
                           TRUE ~ "other")) |>
  group_by(callset, sample, class) |> summarise(n = sum(n), .groups = "drop") |>
  pivot_wider(names_from = class, values_from = n, values_fill = 0) |>
  mutate(non_ref   = het + hom_alt,
         het_hom   = het / pmax(hom_alt, 1),
         group     = case_when(str_starts(sample, "CASE") ~ "Case",
                               str_starts(sample, "CTRL") ~ "Control",
                               TRUE ~ "Other"),
         group     = factor(group, levels = c("Case", "Control")))

group_n <- per_sample |> distinct(sample, group) |> count(group)
group_lab <- setNames(sprintf("%s (n = %d)", group_n$group, group_n$n), group_n$group)

wilcox_tab <- per_sample |>
  group_by(callset) |>
  summarise(
    median_case    = median(non_ref[group == "Case"]),
    median_control = median(non_ref[group == "Control"]),
    p_non_ref      = tryCatch(wilcox.test(non_ref ~ group)$p.value, error = function(e) NA_real_),
    p_het_hom      = tryCatch(wilcox.test(het_hom ~ group)$p.value, error = function(e) NA_real_),
    .groups = "drop") |>
  mutate(q_non_ref = p.adjust(p_non_ref, "BH"),
         q_het_hom = p.adjust(p_het_hom, "BH"))

p_lab <- function(q) ifelse(is.na(q), "", ifelse(q < 0.001, "q < 0.001", sprintf("q = %.3f", q)))

burden_plot <- function(yvar, ylab, qcol) {
  ann <- per_sample |> group_by(callset) |>
    summarise(y = max(.data[[yvar]]) * 1.06, .groups = "drop") |>
    left_join(select(wilcox_tab, callset, q = all_of(qcol)), by = "callset")
  ggplot(per_sample, aes(group, .data[[yvar]], fill = group)) +
    geom_boxplot(width = 0.55, outlier.shape = NA, colour = thesis_neutral[["outline"]], linewidth = 0.3) +
    geom_point(aes(fill = group), shape = 21, colour = point_outline, stroke = point_stroke,
               position = position_jitter(width = 0.15, height = 0, seed = 1),
               size = point_size * 0.7, alpha = point_alpha + 0.2) +
    geom_text(data = ann, aes(x = 1.5, y = y, label = p_lab(q)), inherit.aes = FALSE,
              size = 2.3, colour = ink) +
    facet_wrap(~ callset, nrow = 1, scales = "free_y") +
    scale_fill_manual(values = pal_group, labels = group_lab, name = NULL) +
    scale_y_continuous(labels = label_comma(), expand = expansion(mult = c(0.03, 0.1))) +
    labs(x = NULL, y = ylab) +
    theme_sv() +
    theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
}

p4a <- burden_plot("non_ref", "Non-ref SVs per genome", "q_non_ref")
p4b <- burden_plot("het_hom", "Het : hom-alt ratio", "q_het_hom")
fig4 <- (p4a / p4b) + plot_layout(guides = "collect") +
  plot_annotation(tag_levels = "a",
                  caption = "Two-sided Wilcoxon rank-sum test, cases vs controls; BH-adjusted across callsets.",
                  theme = theme_sv()) &
  theme(legend.position = "bottom")
save_fig(fig4, "fig_octopusv_4_per_sample_burden", height_mm = 130)

# ========================================= Figure 5 (supplementary): QC =====
qc_get <- function(prefix) {
  qc |>
    filter(str_detect(key, paste0("^(Average|Median|Min|Max|Q1|Q3) ", prefix, "$"))) |>
    mutate(stat = word(key, 1)) |>
    select(callset, stat, value_num) |>
    pivot_wider(names_from = stat, values_from = value_num)
}
qual    <- qc_get("QUAL")
support <- qc_get("Read Support")
support_cov <- qc |>
  filter(key == "Number of variants with support info") |>
  select(callset, with_support = value_num) |>
  left_join(select(size_summary, callset, total), by = "callset") |>
  mutate(prop = with_support / total)
support <- support |>
  left_join(select(support_cov, callset, with_support), by = "callset") |>
  filter(with_support > 0)                      # TIDDIT reports no read-support field

five_num_box <- function(d, ylab) {
  ggplot(d, aes(callset, fill = callset)) +
    geom_boxplot(aes(ymin = Min, lower = Q1, middle = Median, upper = Q3, ymax = Max),
                 stat = "identity", width = 0.55, colour = thesis_neutral[["outline"]], linewidth = 0.3) +
    geom_point(aes(y = Average), shape = 23, size = 1.8, fill = "white", colour = ink) +
    scale_fill_manual(values = pal_callset, guide = "none") +
    scale_y_continuous(labels = label_comma()) +
    labs(x = NULL, y = ylab) +
    theme_sv() + rot_x
}

p5a <- five_num_box(qual, "QUAL (caller-specific scale)")
p5b <- five_num_box(support, "Supporting reads per SV")
p5c <- ggplot(support_cov, aes(callset, prop, fill = callset)) +
  geom_col(width = 0.6) +
  geom_text(aes(label = percent(prop, accuracy = 0.1)), vjust = -0.3, size = 2.3, colour = ink) +
  scale_fill_manual(values = pal_callset, guide = "none") +
  scale_y_continuous(labels = label_percent(), limits = c(0, 1.08), expand = expansion(mult = c(0, 0))) +
  labs(x = NULL, y = "SVs with read-support field") +
  theme_sv() + rot_x

fig5 <- (p5a | p5b | p5c) + plot_layout(widths = c(1.3, 1, 1)) +
  plot_annotation(tag_levels = "a",
                  caption = paste("Boxes drawn from OctopuSV five-number summaries (min, Q1, median, Q3, max); diamond = mean.",
                                  "QUAL is not comparable between callers (TIDDIT 0-80; Manta capped at 999).",
                                  "TIDDIT records carry no read-support field.", sep = "\n"),
                  theme = theme_sv())
save_fig(fig5, "fig_octopusv_S1_qc", height_mm = 85)

# =================================================================== tables ==
summary_tab <- size_summary |>
  left_join(types |> select(callset, type, n) |> pivot_wider(names_from = type, values_from = n),
            by = "callset") |>
  left_join(select(nonprim, callset, off_primary, prop_off_primary = prop), by = "callset") |>
  left_join(select(qual, callset, median_qual = Median), by = "callset") |>
  left_join(select(support_cov, callset, prop_with_support = prop), by = "callset") |>
  left_join(per_sample |> group_by(callset) |>
              summarise(n_samples = n(), median_non_ref_per_sample = median(non_ref),
                        .groups = "drop"), by = "callset") |>
  arrange(callset)

write_csv(summary_tab,   file.path(tab_dir, "octopusv_callset_summary.csv"))
write_csv(types,         file.path(tab_dir, "octopusv_sv_types.csv"))
write_csv(size_bins,     file.path(tab_dir, "octopusv_size_bins.csv"))
write_csv(chrom |> mutate(per_mb = n / (length / 1e6)), file.path(tab_dir, "octopusv_contig_counts_density.csv"))
write_csv(per_sample,    file.path(tab_dir, "octopusv_per_sample_genotypes.csv"))
write_csv(wilcox_tab,    file.path(tab_dir, "octopusv_case_control_tests.csv"))

# Sanity checks (printed, not fatal)
chk <- per_sample |> mutate(tot = het + hom_alt + hom_ref) |>
  distinct(callset, tot) |> left_join(select(size_summary, callset, total), by = "callset")
if (any(chk$tot != chk$total)) {
  message("NOTE: per-sample genotype totals differ from callset size for some samples ",
          "(e.g. missing './.' genotypes not reported by OctopuSV).")
}

message("\nDone. Figures -> ", fig_dir, "\n      Tables  -> ", tab_dir)
print(summary_tab, width = Inf)
