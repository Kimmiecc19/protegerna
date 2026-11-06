# ============================================================
# 02_sv_thesis_style.R
# Objective 2 (structural variants) figure style, built on the dissertation
# brand palette in thesis_palette.R (Objective 1).
#
#   * Everything here is genomics, so gold is the anchor colour:
#     - facet strips carry the Genomics gold tint (as in Objective 1),
#     - the consensus (intersection) callset is gold and the union a gold tint,
#     - ordered/magnitude scales are gold shade -> gold -> gold tints.
#   * Other categorical variables use the secondary colours
#     (mint, flame, crimson, brown), exactly as thesis_palette.R prescribes.
#   * Filled marks keep the thin dark outline from set_thesis_geom_defaults(),
#     and text on fills uses ink_on() so it is always black or white as needed.
#
# Palettes were checked for colour-vision-deficiency separation; the adjacent
# order within each palette below is part of that check - keep it.
# ============================================================

# Clear anything left over from an earlier run so stale colours/figures can't be reused
suppressWarnings(rm(list = intersect(ls(globalenv()), c("pal_callset", "pal_type", "pal_group",
  "pal_outcome", "pal_disposition", "theme_thesis", "theme_sv", "save_fig", "ink", "ink_muted",
  paste0("fig", 1:5), paste0("p", rep(1:5, each = 3), c("a", "b", "c")))), envir = globalenv()))

# ---- locate and load thesis_palette.R --------------------------------------
local({
  # Folder of this style file, however it is loaded (Rscript, source(), RStudio)
  here <- tryCatch({
    a <- commandArgs(FALSE); f <- sub("^--file=", "", a[grep("^--file=", a)])
    ofile <- NULL
    for (fr in rev(sys.frames())) if (!is.null(fr$ofile)) { ofile <- fr$ofile; break }
    if (!is.null(ofile)) dirname(normalizePath(ofile))
    else if (length(f)) dirname(normalizePath(f)) else getwd()
  }, error = function(e) getwd())
  obj1 <- "C:/Users/USER-PC/OneDrive/Documents/2026 PhD/protegerna/1_omics_tool_landscape/4_tool_analysis"
  candidates <- c(
    Sys.getenv("THESIS_PALETTE", unset = ""),
    file.path(here, "thesis_palette.R"),
    file.path(dirname(here), "thesis_palette.R"),
    file.path(obj1, "code_tool_analysis", "thesis_palette.R"),
    file.path(obj1, "code", "thesis_palette.R")
  )
  hit <- candidates[nzchar(candidates) & file.exists(candidates)][1]
  if (is.na(hit)) stop("thesis_palette.R not found. Set the THESIS_PALETTE environment variable ",
                       "to its path, or copy it next to this script.", call. = FALSE)
  message("Using thesis palette: ", hit)
  source(hit, local = globalenv())
})
set_thesis_geom_defaults()

# ---- gold scale ---------------------------------------------------------------
gold      <- thesis_primary[["gold"]]
gold_tint <- function(strength) unname(thesis_tint(gold, strength))       # lighter
gold_shade <- function(f) {                                                # darker
  m <- round(grDevices::col2rgb(gold) * f)
  grDevices::rgb(m[1], m[2], m[3], maxColorValue = 255)
}
genomics_strip <- grDevices::adjustcolor(gold, alpha.f = 0.35)            # = Objective 1 strip tint

# ---- semantic palettes (named: matched by level, never by position) ----------
# Callsets. Fills (bars) use the secondary tints; lines/points use full strength.
pal_callset <- c(
  Manta        = thesis_secondary[["flame"]],
  TIDDIT       = thesis_secondary[["mint"]],
  Intersection = gold,
  Union        = gold_tint(0.35),
  `Union-only` = gold_tint(0.35)
)
pal_callset_line <- c(
  Manta        = thesis_secondary_full[["flame"]],
  TIDDIT       = thesis_secondary_full[["mint"]],
  Intersection = gold,
  Union        = gold,
  `Union-only` = gold
)
lty_callset   <- c(Manta = "solid", TIDDIT = "solid", Intersection = "solid", Union = "22")
shape_callset <- c(Manta = 21, TIDDIT = 22, Intersection = 24, Union = 23)

# SV types: gold shade -> gold -> tints (read with the outlines and % labels).
pal_type <- c(DEL = gold_shade(0.6), DUP = gold, INS = gold_tint(0.5), INV = gold_tint(0.2))

# Case / control
pal_group <- c(Case = thesis_secondary[["crimson"]], Control = thesis_secondary[["mint"]])

# Technical review outcome (ordered: strongest support -> excluded)
pal_outcome <- c(
  "Technically supported"           = gold_shade(0.6),
  "Supported with caveats"          = gold,
  "Uncertain"                       = thesis_neutral[["unknown"]],
  "Likely artefact / merge error"   = thesis_secondary[["flame"]],
  "Excluded (failed caller filter)" = thesis_secondary[["crimson"]]
)

# Final audit disposition (primary candidates carry the genomics gold)
pal_disposition <- c(
  "Primary candidate"               = gold,
  "Exploratory review only"         = thesis_secondary[["mint"]],
  "Deprioritised (shared/frequent)" = thesis_secondary[["brown"]],
  "Held"                            = thesis_secondary[["flame"]],
  "Excluded (failed caller filter)" = thesis_secondary[["crimson"]]
)

# Sequential (counts): pale gold -> gold shade
seq_gold <- c(low = gold_tint(0.08), high = gold_shade(0.7))

# Text colour for labels drawn on top of a fill, keyed like the fill palette
text_on <- function(pal) stats::setNames(ink_on(pal), names(pal))

ink       <- thesis_neutral[["ink"]]
ink_muted <- thesis_neutral[["guide"]]

# ---- theme -------------------------------------------------------------------
# theme_thesis() from thesis_palette.R, sized for a 180 mm-wide figure, with the
# Genomics gold on every facet strip.
theme_sv <- function(base_size = 9, legend.position = "bottom") {
  theme_thesis(base_size = base_size, legend.position = legend.position) +
    ggplot2::theme(
      strip.background = ggplot2::element_rect(fill = genomics_strip, colour = NA),
      plot.caption     = ggplot2::element_text(hjust = 0, size = base_size * 0.8, colour = "#333333",
                                               margin = ggplot2::margin(t = 6)),
      plot.tag         = ggplot2::element_text(face = "bold", size = base_size * 1.25),
      legend.key.size  = ggplot2::unit(3.5, "mm"),
      panel.spacing.x  = ggplot2::unit(5, "mm"),
      plot.margin      = ggplot2::margin(4, 16, 4, 4)
    )
}
rot_x <- ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 35, hjust = 1))

# ---- saving --------------------------------------------------------------------
save_fig <- function(plot, name, width_mm = 180, height_mm = 120, dir = fig_dir) {
  pdf_dev <- if (capabilities("cairo")) grDevices::cairo_pdf else grDevices::pdf
  ggplot2::ggsave(file.path(dir, paste0(name, ".pdf")), plot, width = width_mm,
                  height = height_mm, units = "mm", device = pdf_dev)
  ggplot2::ggsave(file.path(dir, paste0(name, ".png")), plot, width = width_mm,
                  height = height_mm, units = "mm", dpi = 600, bg = "white")
  message("  wrote ", name)
}
