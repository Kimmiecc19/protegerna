# thesis_palette.R ------------------------------------------------------------
# University brand colours for every figure in the dissertation.
# https://files.su.ac.za/public/doctoral-office/documents/2025-09/output-su-style-guide.pdf
# Source this file at the top of any plotting script:
#     source("thesis_palette.R")
#
# Rules
#   * Omics domains ALWAYS use the four primary colours, always matched by
#     name (never by position), so a domain keeps its colour in every figure:
#       Genomics = gold, Transcriptomics = maroon,
#       Proteomics = teal, Multiomics = blue
#   * Other categorical variables use the secondary colours, and draw on the
#     primaries only when more than four colours are needed.
#   * Gold (#CAA258) and mint (#82CCAE) are light: on white they fall below
#     the 3:1 contrast recommended for graphics (WCAG 1.4.11). Every filled
#     mark therefore gets a thin dark outline, and text drawn on a coloured
#     fill uses ink_on() to pick black or white automatically.

if (!exists("%||%")) `%||%` <- function(a, b) if (is.null(a)) b else a

# Brand colours ---------------------------------------------------------------
thesis_primary <- c(
  maroon = "#61223B",
  gold   = "#CAA258",
  teal   = "#005F61",
  blue   = "#223D71"
)

# Full-strength secondary colours (kept for reference, text or thin lines).
thesis_secondary_full <- c(
  mint    = "#82CCAE",
  flame   = "#DC4405",
  crimson = "#A60A3D",
  brown   = "#643335"
)

# Large fills use 80% colour mixed with 20% white (strength = 0.8).
# Small points use full-strength colours. Filled marks retain a dark outline.
thesis_tint <- function(hex, strength = 0.6) {
  rgb <- grDevices::col2rgb(hex)
  mixed <- round(rgb * strength + 255 * (1 - strength))
  stats::setNames(grDevices::rgb(mixed[1, ], mixed[2, ], mixed[3, ], maxColorValue = 255), names(hex))
}
thesis_secondary <- thesis_tint(thesis_secondary_full, 0.8)
# The tints are calculated from the declared strength; no hand-coded hex copies.

thesis_neutral <- c(
  ink     = "#1A1A1A",  # text, trend lines
  outline = "#3A3A3A",  # outlines on filled marks
  guide   = "#6E6E6E",  # reference / median lines
  grid    = "#E0D6D6",
  unknown = "#E0D6D6",  # Unknown / missing / not observed
  muted   = "#F4EDE0"   # de-emphasised marks (e.g. non-outlier points)
)

# Fixed semantic palettes (named: matched by level, never by order) -----------
omic_palette <- c(
  Genomics        = thesis_primary[["gold"]],
  Transcriptomics = thesis_primary[["maroon"]],
  Proteomics      = thesis_primary[["teal"]],
  Multiomics      = thesis_primary[["blue"]]
)

# Repository commit-recency status: ordered from recent to inactive.
maintenance_palette <- c(
  Active   = thesis_secondary[["mint"]],
  Stale    = thesis_secondary[["flame"]],
  Inactive = thesis_secondary[["crimson"]],
  Unknown  = thesis_neutral[["unknown"]]
)

license_palette <- c(
  Permissive            = thesis_secondary[["mint"]],
  Copyleft              = thesis_secondary[["crimson"]],
  `Other specified`     = thesis_secondary[["brown"]],
  `Not licensed`        = thesis_secondary[["flame"]],
  `No licence declared` = thesis_neutral[["unknown"]]
)

# Full-strength versions for SMALL marks (points). Large fills (bars, ridges,
# violins) use the 80% colour tints above; small points need full strength to stay
# visible and distinguishable (including for colour-blind readers).
maintenance_palette_points <- c(
  Active   = thesis_secondary_full[["mint"]],
  Stale    = thesis_secondary_full[["flame"]],
  Inactive = thesis_secondary_full[["crimson"]],
  Unknown  = thesis_neutral[["unknown"]]
)

# Two-level highlight (e.g. outlier vs normal)
highlight_palette <- c(
  Normal  = thesis_neutral[["muted"]],
  Outlier = thesis_secondary_full[["flame"]]   # a point: full strength
)

# General categorical palette -------------------------------------------------
# For variables that are not omics domains: secondary colours first, then the
# primaries once more than four colours are needed. Stops if more than eight
# are requested, because interpolated colours would leave the brand palette.
thesis_categorical <- function(n, levels = NULL) {
  pal <- unname(c(thesis_secondary, thesis_primary))
  if (n > length(pal)) {
    stop("thesis_categorical(): ", n, " colours requested but the brand palette has ",
      length(pal), ". Group rare categories into 'Other' first.", call. = FALSE)
  }
  out <- pal[seq_len(n)]
  if (!is.null(levels)) names(out) <- levels
  out
}

# Contrast helpers ------------------------------------------------------------
relative_luminance <- function(hex) {
  rgb <- grDevices::col2rgb(hex) / 255
  rgb <- ifelse(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055)^2.4)
  as.numeric(0.2126 * rgb[1, ] + 0.7152 * rgb[2, ] + 0.0722 * rgb[3, ])
}

contrast_ratio <- function(a, b) {
  la <- relative_luminance(a);
  lb <- relative_luminance(b)
  (pmax(la, lb) + 0.05) / (pmin(la, lb) + 0.05)
}

# Black or white text, whichever contrasts more with the fill behind it.
ink_on <- function(fill_hex, dark = thesis_neutral[["ink"]], light = "#FFFFFF") {
  fill_hex <- unname(fill_hex)
  out <- ifelse(contrast_ratio(fill_hex, dark) >= contrast_ratio(fill_hex, light), dark, light)
  out[is.na(fill_hex)] <- dark
  out
}

# Contrast of every brand colour against white, for the Methods / appendix.
thesis_contrast_table <- function() {
  all_cols <- c(thesis_primary, thesis_secondary)
  data.frame(
    colour = names(all_cols),
    hex = unname(all_cols),
    contrast_vs_white = round(contrast_ratio(all_cols, "#FFFFFF"), 2),
    text_colour_on_fill = ink_on(all_cols),
    row.names = NULL
  )
}

# Scales ----------------------------------------------------------------------
scale_fill_omics <- function(..., name = "Omics type") {
  ggplot2::scale_fill_manual(values = omic_palette, name = name, ...)
}
scale_colour_omics <- function(..., name = "Omics type") {
  ggplot2::scale_colour_manual(values = omic_palette, name = name, ...)
}

# Theme and geometry defaults -------------------------------------------------
theme_thesis <- function(base_size = 11, legend.position = "right") {
  ggplot2::theme_minimal(base_size = base_size) +
    ggplot2::theme(
      plot.background  = ggplot2::element_rect(fill = "white", colour = NA),
      panel.background = ggplot2::element_rect(fill = "white", colour = NA),
      panel.grid.major = ggplot2::element_line(colour = thesis_neutral[["grid"]], linewidth = 0.35),
      panel.grid.minor = ggplot2::element_blank(),
      text             = ggplot2::element_text(colour = thesis_neutral[["ink"]]),
      axis.text        = ggplot2::element_text(colour = "#333333"),
      strip.text       = ggplot2::element_text(colour = thesis_neutral[["ink"]], face = "bold"),
      # A real (white) strip rectangle is needed so colour_omic_strips() can tint it.
      strip.background = ggplot2::element_rect(fill = "white", colour = NA),
      plot.caption     = ggplot2::element_text(hjust = 0, size = 9, colour = "#333333"),
      plot.title.position = "plot",
      plot.caption.position = "plot",
      legend.position  = legend.position
    )
}

# Thin dark outlines on bars/columns so light brand colours (gold, mint) keep
# a visible edge against white. Call once after loading ggplot2.
set_thesis_geom_defaults <- function() {
  ggplot2::update_geom_defaults("col", list(colour = thesis_neutral[["outline"]], linewidth = 0.2))
  ggplot2::update_geom_defaults("bar", list(colour = thesis_neutral[["outline"]], linewidth = 0.2))
  invisible(TRUE)
}

# Arguments for outlined points: use as
#   geom_point(aes(fill = group), shape = 21, colour = point_outline, stroke = point_stroke, ...)
# Points: low fill opacity and a semi-transparent outline, so dense clusters
# show density instead of merging into a solid dark block.
point_outline <- grDevices::adjustcolor(thesis_neutral[["outline"]], alpha.f = 0.4)
point_stroke  <- 0.15
point_alpha   <- 0.4
point_size    <- 1.3   # scatter / jitter points
dot_size      <- 1.5     # single summary points (prevalence dot plots)
# Very pale point fills (e.g. the "Normal" cream in the outlier plot) keep a
# near-opaque fill and a stronger outline so they do not vanish on white.
tint_point_alpha   <- 0.9
tint_point_outline <- grDevices::adjustcolor(thesis_neutral[["outline"]], alpha.f = 0.65)



# Omics-coloured facet strips -------------------------------------------------
# Tints the background of every facet strip whose label starts with an omics
# domain name ("Genomics", "Genomics (n = 2,222)", ...) with that domain's
# primary colour at `alpha` opacity. Strips for any other variable are left
# untouched. Works on single ggplots and patchwork layouts and needs no extra
# packages: it edits the rendered grob, matching strips by their label text,
# so panel order can never put a colour on the wrong domain.
colour_omic_strips <- function(plot, alpha = 0.35, palette = omic_palette) {
  g <- if (inherits(plot, "patchwork")) {
    patchwork::patchworkGrob(plot)
  } else if (inherits(plot, "ggplot")) {
    ggplot2::ggplotGrob(plot)
  } else {
    plot
  }
  tinted <- 0L
  tints <- grDevices::adjustcolor(palette, alpha.f = alpha)
  names(tints) <- names(palette)

  first_label <- function(x) {
    if (!is.null(x$label) && is.character(x$label) && length(x$label)) return(x$label[1])
    kids <- if (inherits(x, "gtable")) x$grobs else x$children
    for (k in kids) {
      lab <- first_label(k)
      if (!is.null(lab)) return(lab)
    }
    NULL
  }
  tint_for <- function(label) {
    if (is.null(label)) return(NULL)
    hit <- names(tints)[startsWith(trimws(label), names(tints))]
    if (length(hit)) tints[[hit[1]]] else NULL
  }
  # A strip is any gTree with a "strip.background..." rectangle among its
  # children; its label is read from the same gTree. Handles strips that
  # patchwork merges into one gtable per row.
  walk <- function(x) {
    if (inherits(x, "gtable")) {
      for (i in seq_along(x$grobs)) x$grobs[[i]] <- walk(x$grobs[[i]])
    } else if (inherits(x, "gTree") && length(x$children)) {
      kid_names <- vapply(x$children, function(k) k$name %||% "", character(1))
      bg <- which(grepl("^strip\\.background", kid_names) &
        vapply(x$children, inherits, logical(1), what = "rect"))
      if (length(bg)) {
        fill <- tint_for(first_label(x))
        if (!is.null(fill)) {
          for (b in bg) x$children[[b]]$gp$fill <- fill
          tinted <<- tinted + 1L
        }
      } else {
        for (i in seq_along(x$children)) x$children[[i]] <- walk(x$children[[i]])
      }
    }
    x
  }
  out <- walk(g)
  attr(out, "omic_strips_tinted") <- tinted
  out
}

# Save any ggplot / patchwork as PNG with omics strip tints applied.
save_thesis_plot <- function(plot, path, width = 8, height = 6, dpi = 300, strip_alpha = 0.35) {
  g <- colour_omic_strips(plot, alpha = strip_alpha)
  n_tinted <- attr(g, "omic_strips_tinted") %||% 0L
  if (n_tinted > 0L) message(basename(path), ": tinted ", n_tinted, " omics facet strip(s)")
  grDevices::png(path, width = width, height = height, units = "in", res = dpi,
    type = if (isTRUE(capabilities("cairo"))) "cairo" else getOption("bitmapType"))
  on.exit(grDevices::dev.off(), add = TRUE)
  grid::grid.newpage()
  grid::grid.draw(g)
  invisible(path)
}
