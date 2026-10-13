# Shared functions. Requires ggplot2 and patchwork; source thesis_palette.R first.
if (!requireNamespace("ggplot2", quietly = TRUE)) {
  stop('Install ggplot2 first: install.packages("ggplot2")')
}
library(ggplot2)
if (!requireNamespace("patchwork", quietly = TRUE)) {
  stop('Install patchwork first: install.packages("patchwork")')
}
set_thesis_geom_defaults()

read_cohort <- function(path) {
  d <- read.csv(path, colClasses = "character", check.names = FALSE,
                na.strings = c("", "NA"), stringsAsFactors = FALSE)
  required <- c("Participant_ID", "HAS_GENOMICS", "HAS_TRANSCRIPTOMICS",
    "HAS_PROTEOMICS", "SEX", "ETHNIC_CATEGORY", "RACE", "SUBJECT_GROUP",
    "SUBJECT_SUBGROUP", "ClinReport_Mutations_Details", "HasVariant",
    "EH_C9orf72", "EH_ATXN2", "C9orf72_repeat_length", "ATXN2_repeat_length",
    "C9orf72_repeat_length_full", "ATXN2_repeat_length_full", "Sporadic_Familial")
  if (!all(required %in% names(d))) stop("Some required columns are missing.")
  if (anyNA(d$Participant_ID) || anyDuplicated(d$Participant_ID)) {
    stop("Participant_ID must be present and unique; resolve duplicates first.")
  }
  d
}

recorded_category <- function(x) {
  x <- trimws(x)
  x[is.na(x) | x == ""] <- "Not recorded"
  x
}

# Stable named colours based on the FULL cohort, shared by both chapters.
# For >8 categories, use one thesis colour: labels identify every category.
category_colours <- function(x) {
  lev <- sort(unique(recorded_category(x)))
  missing <- lev %in% c("Not recorded", "Unknown")
  known <- lev[!missing]
  pal <- if (length(known) <= 8) thesis_categorical(length(known), known) else
    setNames(rep(thesis_secondary[["mint"]], length(known)), known)
  c(pal, setNames(rep(thesis_neutral[["unknown"]], sum(missing)), lev[missing]))
}

save_figure <- function(p, name, out, height = 5, width = 9) {
  ggsave(file.path(out, paste0(name, ".png")), p, width = width, height = height,
         units = "in", dpi = 300, bg = "white")
  ggsave(file.path(out, paste0(name, ".pdf")), p, width = width, height = height,
         units = "in", bg = "white")
}

category_plot <- function(d, reference, variable, title, out, cohort_label) {
  x <- recorded_category(d[[variable]])
  if (variable == "RACE") {
    retained <- c("White", "Black/African American", "Not recorded", "Asian")
    x[!x %in% retained] <- "Other"
  }
  tab <- as.data.frame(table(x), stringsAsFactors = FALSE)
  names(tab) <- c("category", "n")
  tab$percent <- 100 * tab$n / nrow(d)
  tab <- tab[order(tab$n, tab$category), ]
  tab$category <- factor(tab$category, levels = tab$category)
  tab$label <- sprintf("%d (%.1f%%)", tab$n, tab$percent)
  write.csv(tab, file.path(out, paste0(variable, "_counts.csv")), row.names = FALSE)
  if (variable == "RACE") {
    # One panel; mixed-race and all remaining entries are grouped as Other.
    race_panel <- function(z, panel_title) {
      ggplot(z, aes(percent, category, fill = category)) +
        geom_col(width = 0.7) +
        geom_text(aes(label = sprintf("%.2f%% (n = %d)", percent, n)),
                  hjust = -0.08, size = 3.2) +
        scale_fill_manual(values = c(
          White = thesis_primary[["gold"]],
          `Black/African American` = thesis_secondary[["crimson"]],
          `Not recorded` = thesis_neutral[["unknown"]],
          Asian = thesis_secondary[["flame"]],
          Other = thesis_secondary[["mint"]])) +
        scale_x_continuous(labels = function(x) paste0(x, "%"),
          expand = expansion(mult = c(0, 0.4))) +
        scale_y_discrete(drop = TRUE, labels = function(z) vapply(z, function(s)
          paste(strwrap(s, width = 35), collapse = "\n"), character(1))) +
        labs(title = panel_title, x = "Proportion of all participants", y = NULL) +
        theme_thesis(11, legend.position = "none")
    }
    p <- race_panel(tab, "Race proportions") + labs(
      subtitle = paste0(cohort_label, " | N = ", nrow(d)),
      caption = "Percentages use all cohort participants. Other includes remaining and mixed-race categories. Blanks are Not recorded.")
    save_figure(p, variable, out, 5)
    return(invisible(p))
  }
  p <- ggplot(tab, aes(n, category, fill = category)) +
    geom_col(width = 0.7) + geom_text(aes(label = label), hjust = -0.08, size = 3.3) +
    scale_fill_manual(values = category_colours(reference[[variable]])) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.28))) +
    scale_y_discrete(labels = function(z) vapply(z, function(s)
      paste(strwrap(s, width = 38), collapse = "\n"), character(1))) +
    labs(title = title, subtitle = paste0(cohort_label, " | N = ", nrow(d)),
      x = "Participants", y = NULL,
      caption = "Percentages use all participants in this cohort. Missing entries are shown as Not recorded.") +
    theme_thesis(11, legend.position = "none")
  save_figure(p, variable, out, max(4.5, 2 + 0.45 * nrow(tab)))
  invisible(p)
}

# Same ggplot2 + patchwork layout as Objective 1: intersection bars,
# domain-coloured matrix dots and set-size bars on the left.
omics_upset <- function(d, flags, out, cohort_label) {
  sets <- names(flags)
  membership <- sapply(unname(flags), function(v)
    !is.na(d[[v]]) & tolower(trimws(d[[v]])) == "yes")
  colnames(membership) <- sets
  combination <- apply(membership, 1, function(r)
    if (any(r)) paste(sets[r], collapse = " & ") else "None recorded")
  intersections <- as.data.frame(table(combination), stringsAsFactors = FALSE)
  names(intersections) <- c("combination", "n")
  intersections <- intersections[order(-intersections$n, intersections$combination), ]
  intersections$combination <- factor(intersections$combination,
    levels = intersections$combination)
  write.csv(intersections, file.path(out, "omics_combination_counts.csv"), row.names = FALSE)
  matrix_data <- expand.grid(combination = levels(intersections$combination),
    set = sets, stringsAsFactors = FALSE)
  matrix_data$member <- mapply(function(comb, domain)
    domain %in% strsplit(comb, " & ", fixed = TRUE)[[1]],
    matrix_data$combination, matrix_data$set)
  matrix_data$combination <- factor(matrix_data$combination,
    levels = levels(intersections$combination))
  matrix_data$set <- factor(matrix_data$set, levels = rev(sets))
  sizes <- data.frame(set = factor(sets, levels = rev(sets)), n = colSums(membership))
  write.csv(sizes, file.path(out, "upset_set_sizes.csv"), row.names = FALSE)
  bars <- ggplot(intersections, aes(combination, n)) +
    geom_col(fill = thesis_neutral[["ink"]], width = 0.7) +
    geom_text(aes(label = n), vjust = -0.4, size = 3.5) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
    scale_x_discrete(drop = FALSE) +
    labs(x = NULL, y = "Participants in exact intersection") + theme_thesis() +
    theme(axis.text.x = element_blank(), panel.grid.major.x = element_blank())
  active <- matrix_data[matrix_data$member, ]
  # Lines only for intersections with at least two active domains.
  line_data <- active[as.character(active$combination) %in%
    names(which(table(active$combination) >= 2)), ]
  dots <- ggplot(matrix_data, aes(combination, set)) +
    geom_point(data = matrix_data[!matrix_data$member, ],
      colour = thesis_neutral[["grid"]], size = 3.2) +
    geom_line(data = line_data, aes(group = combination),
      colour = thesis_neutral[["outline"]], linewidth = 0.6) +
    geom_point(data = active, aes(fill = as.character(set)), shape = 21,
      colour = thesis_neutral[["outline"]], stroke = 0.3, size = 3.6) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    scale_x_discrete(drop = FALSE, labels = function(x)
      ifelse(x == "None recorded", "None\nrecorded", "")) +
    scale_y_discrete(drop = FALSE) + labs(x = NULL, y = NULL) + theme_thesis() +
    theme(panel.grid.major.x = element_blank())
  set_bars <- ggplot(sizes, aes(n, set, fill = as.character(set))) +
    geom_col(width = 0.6) +
    scale_x_reverse(expand = expansion(mult = c(0.15, 0))) +
    scale_y_discrete(drop = FALSE) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    labs(x = "Participants per domain", y = NULL) + theme_thesis() +
    theme(axis.text.y = element_blank(), panel.grid.major.y = element_blank())
  p <- patchwork::wrap_plots(patchwork::plot_spacer(), bars, set_bars, dots,
    ncol = 2, widths = c(1, 3), heights = c(2, 1)) +
    patchwork::plot_annotation(title = "Participant overlap between omics domains",
      subtitle = paste0(cohort_label, " | N = ", nrow(d)),
      caption = paste("Each column is an exact combination of recorded Yes flags; coloured dots indicate membership.",
        "Grey dots mean no recorded Yes (including blanks). None recorded means no domain marked Yes.", sep = "\n"))
  stopifnot(sum(intersections$n) == nrow(d))
  save_figure(p, "omics_combination", out, 6)
  invisible(p)
}

make_plots <- function(d, reference, out, cohort_label) {
  if (!nrow(d)) stop("The selected cohort is empty.")
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  write.csv(data.frame(Participant_ID = d$Participant_ID),
            file.path(out, "participant_ids.csv"), row.names = FALSE)
  titles <- c(SEX = "Sex", ETHNIC_CATEGORY = "Ethnicity", RACE = "Race",
    SUBJECT_GROUP = "Subject group", SUBJECT_SUBGROUP = "Recorded subject subgroup",
    Sporadic_Familial = "Recorded sporadic / familial classification",
    ClinReport_Mutations_Details = "Recorded clinical mutation details",
    HasVariant = "Recorded variant labels",
    EH_C9orf72 = "EH_C9orf72: recorded flag", EH_ATXN2 = "EH_ATXN2: recorded flag")
  category_figures <- setNames(vector("list", length(titles)), names(titles))
  for (v in names(titles)) {
    category_figures[[v]] <- category_plot(d, reference, v, titles[[v]], out, cohort_label)
  }

  # Counts are overlapping: one participant can have all three omics.
  flags <- c(Genomics = "HAS_GENOMICS", Transcriptomics = "HAS_TRANSCRIPTOMICS",
             Proteomics = "HAS_PROTEOMICS")
  om <- do.call(rbind, lapply(names(flags), function(domain) {
    x <- tolower(recorded_category(d[[flags[[domain]]]]))
    data.frame(domain = domain, n = sum(x == "yes"))
  }))
  om$percent <- 100 * om$n / nrow(d)
  write.csv(om, file.path(out, "omics_availability_counts.csv"), row.names = FALSE)
  om$domain <- factor(om$domain, levels = names(flags))
  p <- ggplot(om, aes(domain, n, fill = domain)) + geom_col(width = 0.65) +
    geom_text(aes(label = n), vjust = -0.4, size = 4) + scale_fill_omics() +
    scale_y_continuous(expand = expansion(mult = c(0, 0.18))) +
    labs(title = "Omics availability", subtitle = paste0(cohort_label, " | N = ", nrow(d)),
      x = NULL, y = "Participants with omics data", caption = "Counts include Yes entries only. Each participant can appear in more than one domain.") +
    theme_thesis(11, legend.position = "none")
  save_figure(p, "omics_availability", out)

  upset_figure <- omics_upset(d, flags, out, cohort_label)

  # Stack panels in the requested order. Wrap the UpSet grob to retain its
  # internal layout and title when it is nested in the combined figure.
  upset_no_caption <- upset_figure + patchwork::plot_annotation(caption = NULL)
  combined <- patchwork::wrap_plots(
    patchwork::wrap_elements(full = patchwork::patchworkGrob(upset_no_caption)),
    category_figures[["SUBJECT_GROUP"]] + labs(caption = NULL),
    category_figures[["SEX"]] + labs(caption = NULL),
    category_figures[["RACE"]] + labs(caption = NULL),
    ncol = 1, heights = c(1.5, 1, 0.8, 1))
  save_figure(combined, "combined_cohort_overview", out, height = 18, width = 10)

  # Numeric summaries only. Keep allele pairs and censored strings in audit tables.
  for (v in c("C9orf72_repeat_length", "ATXN2_repeat_length",
              "C9orf72_repeat_length_full", "ATXN2_repeat_length_full")) {
    raw <- recorded_category(d[[v]])
    numeric_entry <- grepl("^[0-9]+([.][0-9]+)?$", raw)
    audit <- data.frame(Participant_ID = d$Participant_ID, recorded_value = raw,
      parsing_status = ifelse(raw == "Not recorded", "Not recorded",
        ifelse(numeric_entry, "Single numeric value", "Non-numeric / allele-pair value")))
    write.csv(audit, file.path(out, paste0(v, "_audit.csv")), row.names = FALSE)
    if (!any(numeric_entry)) next
    vals <- as.numeric(raw[numeric_entry])
    p <- ggplot(data.frame(repeats = vals), aes(repeats)) +
      geom_histogram(bins = 30, fill = thesis_secondary[["mint"]],
        colour = thesis_neutral[["outline"]], linewidth = 0.2) +
      labs(title = gsub("_", " ", v), subtitle = paste0(cohort_label,
        " | numeric records = ", length(vals), " / ", nrow(d)),
        x = "Recorded repeat length", y = "Participants",
        caption = "Only single numeric entries shown. See audit CSV for missing, allele-pair and other values. No clinical thresholds applied.") +
      theme_thesis()
    save_figure(p, v, out)
  }
  writeLines(c(paste("Cohort:", cohort_label), paste("Participants:", nrow(d)),
    "One row per unique Participant_ID.", "Categories retain source labels; blanks are Not recorded.",
    "Race: White, Black/African American, Asian and Not recorded retained; remaining and mixed-race categories grouped as Other.",
    "EH flags are plotted as recorded; their clinical meaning is not inferred.",
    "Full repeat-length fields containing allele pairs are retained in audit CSVs.",
    "Subgroup and familial plots use the entire selected cohort denominator."),
    file.path(out, "figure_notes.txt"))
  message("Saved figures and tables in: ", normalizePath(out))
}
