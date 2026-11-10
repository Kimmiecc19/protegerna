# Table and figure builders shared by both visualisation workflows. 
# Sourced locally into each workflow, which also sources thesis_palette.R.

# 1. Shared classification and summary helpers ----------------------------------

classify_license <- function(x) {
  x <- stringr::str_squish(tolower(as.character(x)))
  case_when(
    is.na(x) | x %in% c("", "none", "na", "n/a", "null", "unknown") ~ "No licence declared",
    x == "not licensed" ~ "Not licensed",
    str_detect(x, "mit|bsd|apache|cc0|isc") ~ "Permissive",
    str_detect(x, "gpl|lgpl|agpl") ~ "Copyleft",
    TRUE ~ "Other specified"
  )
}

safe_rescale <- function(x, to = c(0, 1)) {
  x_num <- suppressWarnings(as.numeric(x))
  if (all(is.na(x_num))) return(rep(NA_real_, length(x_num)))
  if (length(unique(na.omit(x_num))) == 1L) return(ifelse(is.na(x_num), NA_real_, mean(to)))
  scales::rescale(x_num, to = to, na.rm = TRUE)
}

map_language_group <- function(lang) {
  if (is.na(lang) || trimws(lang) == "") return("Unknown")
  lang_l <- tolower(lang)
  if (str_detect(lang_l, "^r$|\\br\\b")) return("R")
  if (str_detect(lang_l, "python")) return("Python")
  if (str_detect(lang_l, "c\\+\\+|\\bc\\b")) return("C/C++")
  if (str_detect(lang_l, "^java$|\\bjava\\b") && !str_detect(lang_l, "javascript")) return("Java")
  if (str_detect(lang_l, "javascript|node")) return("JavaScript")
  if (str_detect(lang_l, "perl")) return("Perl")
  if (str_detect(lang_l, "ruby")) return("Ruby")
  if (str_detect(lang_l, "matlab|octave")) return("MATLAB")
  if (str_detect(lang_l, "rust|go|golang")) return("Other compiled")
  str_to_title(lang_l)
}

# Prevalence of a multi-valued field (top_n values, Other, Unknown) per domain.
summarise_multivalue <- function(df, col, top_n, sep = ",\\s*|;", missing_label = "Unknown") {
  denominators <- df %>% distinct(biotools_id, omic_type) %>% count(omic_type, name = "denominator")
  expanded <- df %>%
    separate_rows({{ col }}, sep = sep) %>%
    mutate(value = if_else(is.na({{ col }}) | trimws(as.character({{ col }})) == "",
      missing_label, trimws(as.character({{ col }})))) %>%
    distinct(biotools_id, omic_type, value)
  top_vals <- expanded %>% count(value, sort = TRUE) %>%
    filter(value != missing_label) %>% slice_head(n = top_n) %>% pull(value)
  expanded %>%
    mutate(label = if_else(value %in% c(top_vals, missing_label), value, "Other")) %>%
    distinct(biotools_id, omic_type, label) %>%
    count(omic_type, label, name = "n") %>%
    left_join(denominators, by = "omic_type") %>% mutate(prevalence = n / denominator) %>%
    bind_cols(wilson_ci(.$n, .$denominator))
}

# Facet labels such as "Genomics (n = 1,234; unknown = 56)" from a summary with
# n, denominator and an "Unknown" label.
unknown_facet_labels <- function(summary_df) {
  summary_df %>% group_by(omic_type) %>%
    summarise(eligible = first(denominator), missing = sum(n[label == "Unknown"]), .groups = "drop") %>%
    mutate(label_text = paste0(omic_type, " (n = ", scales::comma(eligible), "; unknown = ", scales::comma(missing), ")")) %>%
    { setNames(.$label_text, .$omic_type) }
}

clean_tool_type <- function(df) {
  df %>%
    tidyr::separate_rows(tool_type, sep = ",|;") %>%
    mutate(tool_type = if_else(is.na(tool_type) | trimws(tool_type) == "", NA_character_, trimws(tool_type)))
}

# 2. Shared layers and theme -----------------------------------------------------

banded_trend_layers <- function(trend_df, x = "age", boundary) {
  list(
    geom_ribbon(data = trend_df,
      aes(x = .data[[x]], ymin = ymin, ymax = ymax, group = trend_group),
      inherit.aes = FALSE, fill = "grey55", alpha = 0.35),
    geom_line(data = trend_df,
      aes(x = .data[[x]], y = trend, group = trend_group),
      inherit.aes = FALSE, colour = thesis_neutral[["ink"]], linewidth = 0.9),
    geom_vline(xintercept = boundary, linetype = "dotted", colour = thesis_neutral[["guide"]], linewidth = 0.5)
  )
}

# Wraps the dissertation-wide theme so every figure shares fonts, grid and background.
landscape_plot_theme <- function(legend.position = "right") {
  theme_thesis(base_size = 12, legend.position = legend.position) +
    theme(plot.background = element_rect(fill = "white", color = NA),
      panel.background = element_rect(fill = "white", color = NA))
}

jittered_points <- function(fill_var = "omic_type") {
  geom_jitter(aes(fill = .data[[fill_var]]), shape = 21, colour = point_outline, stroke = point_stroke,
    alpha = point_alpha, width = 0.2, size = point_size)
}

annotation_theme <- function(...) {
  theme(plot.title = element_text(size = 14, face = "bold", hjust = 0),
    plot.subtitle = element_text(size = 11, hjust = 0),
    plot.caption = element_text(hjust = 0, size = 9), ...)
}

# 3. Registration figures (candidate and full-population workflows) -------------
# This section builds and saves the registration figures from registration_analysis().

build_added_year_plot <- function(added_per_year, axis_labels, n_records, records_label, title_suffix = "") {
  ggplot(added_per_year, aes(x = added, y = n, fill = omic_type)) +
    geom_col() +
    facet_wrap(~omic_type, scales = "fixed", ncol = 1) +
    labs(
      title = paste0("Tool-domain records added to bio.tools per year", title_suffix),
      subtitle = glue("{scales::comma(n_records)} {records_label}; year = registration, not publication"),
      x = axis_labels$year_added, y = axis_labels$tool_count
    ) +
    scale_y_continuous(breaks = scales::pretty_breaks(6), expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(breaks = scales::pretty_breaks(10)) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    theme_thesis()
}

build_added_year_pct_plot <- function(added_per_year_pct, axis_labels, title_suffix = "") {
  ggplot(added_per_year_pct, aes(x = added, y = pct_within_year, fill = omic_type)) +
    geom_col() +
    facet_wrap(~omic_type, scales = "fixed", ncol = 1) +
    labs(title = paste0("Share of each year's added records by omics domain", title_suffix),
      x = axis_labels$year_added, y = axis_labels$tool_share) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(breaks = scales::pretty_breaks(10)) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    theme_thesis()
}

# One record per tool-domain-year pair with both years known.
publication_vs_added_records <- function(records) {
  records %>%
    mutate(publication_year = suppressWarnings(as.integer(publication_year)),
      added = suppressWarnings(as.integer(added))) %>%
    distinct(biotools_id, omic_type, publication_year, added, .keep_all = TRUE) %>%
    filter(!is.na(publication_year), !is.na(added))
}

build_pub_vs_added_plot <- function(df_pub_added, current_year, title_suffix = "") {
  ggplot(df_pub_added, aes(x = publication_year, y = added, color = omic_type)) +
    geom_jitter(aes(fill = omic_type), shape = 21, colour = point_outline, stroke = point_stroke,
      alpha = point_alpha, width = 0.25, height = 0.25, size = point_size) +
    geom_smooth(
      # Trend restricted to publication years with enough records; before
      # 2000 the fit rests on a handful of points.
      data = function(d) dplyr::filter(d, publication_year >= 2000),
      aes(group = 1), method = "loess", se = TRUE, color = "grey10", fill = "grey60",
      alpha = 0.5, linetype = "solid", linewidth = 0.9, formula = y ~ x
    ) +
    facet_wrap(~omic_type, scales = "free") +
    geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "grey20", linewidth = 0.8, alpha = 0.9) +
    labs(
      title = paste0("Publication year vs year added to bio.tools", title_suffix),
      subtitle = "Dashed line: added in the publication year; solid line: LOESS with 95% CI (publication year >= 2000)",
      x = "Publication year", y = "Year added"
    ) +
    landscape_plot_theme(legend.position = "none") +
    scale_y_continuous(breaks = seq(min(2015, current_year), current_year, by = 1)) +
    scale_fill_manual(values = omic_palette)
}

# 4. Age-citation figures (candidate and full-population workflows) -------------
# Builds and saves the seven age-citation figures from age_citation_analysis().
# Files are named <figure><name_suffix>; titles take title_suffix.

save_age_citation_figures <- function(ac, save_plot, axis_labels, legend_labels, trend_caption,
    boundary, boundary_label, records_label, title_suffix = "", name_suffix = "") {
  n_outliers <- nrow(ac$outliers)
  age_axes <- labs(x = axis_labels$age, y = axis_labels$citations_log)
  base_plot <- function(data, trend) {
    ggplot(data, aes(x = age, y = citations_log, color = omic_type)) +
      jittered_points() +
      banded_trend_layers(trend, boundary = boundary)
  }
  save <- function(plot, name, width, height) save_plot(plot, paste0(name, name_suffix), width = width, height = height, dpi = 300)

  p_scatter <- base_plot(ac$data, ac$trend_all) +
    annotate("text", x = boundary, y = Inf, label = boundary_label,
      hjust = -0.05, vjust = 1.4, size = 3, colour = thesis_neutral[["guide"]]) +
    labs(title = "Years since publication vs total citations", subtitle = "All omics domains",
      fill = legend_labels$omics) + age_axes +
    guides(fill = guide_legend(override.aes = list(alpha = 1, size = 3))) +
    scale_fill_manual(values = omic_palette, name = legend_labels$omics) +
    landscape_plot_theme()
  save(p_scatter, "age_vs_citations_scatter", 8, 6)

  p_faceted <- base_plot(ac$data, ac$trend_by_omic) +
    facet_wrap(~omic_type, nrow = 2) +
    labs(title = "Years since publication vs total citations by omics domain") + age_axes +
    scale_fill_manual(values = omic_palette, guide = "none") +
    landscape_plot_theme(legend.position = "none")
  save(p_faceted, "age_vs_citations_faceted", 12, 8)

  p_outliers <- ggplot(ac$data, aes(x = age, y = citations_log, color = is_outlier)) +
    geom_point(aes(fill = is_outlier), shape = 21, colour = tint_point_outline, stroke = point_stroke,
      size = point_size, alpha = tint_point_alpha) +
    banded_trend_layers(ac$trend_all, boundary = boundary) +
    geom_label_repel(data = ac$labelled, aes(x = age, y = citations_log, label = name),
      inherit.aes = FALSE, size = 2.5, max.overlaps = Inf, show.legend = FALSE) +
    scale_fill_manual(values = c("FALSE" = highlight_palette[["Normal"]], "TRUE" = highlight_palette[["Outlier"]]),
      labels = c("FALSE" = "Normal", "TRUE" = "Outlier"), name = legend_labels$status) +
    labs(title = paste0("Outliers from the age-citation trend", title_suffix),
      subtitle = glue("|residual| > 2.5 SD ({round(ac$threshold, 2)} log1p units); flagged for display only")) +
    age_axes + landscape_plot_theme()
  save(p_outliers, "outlier_inspection", 10, 6)

  # Display-only sensitivity plots: hidden rows remain in every analytical
  # population, count, model and principal figure.
  hidden_subtitle <- glue("{n_outliers} extreme records hidden for display; analyses unchanged")
  p_clean <- base_plot(ac$data, ac$trend_all) +
    labs(title = "Age-citation trend with extreme points hidden", subtitle = hidden_subtitle) + age_axes +
    landscape_plot_theme() +
    scale_fill_manual(values = omic_palette, guide = "none") +
    coord_cartesian(ylim = ac$display_limits)
  save(p_clean, "age_vs_citations_clean", 8, 6)

  p_scatter_vs_clean <- p_scatter + p_clean +
    plot_layout(ncol = 2, widths = c(1, 1)) +
    plot_annotation(
      title = paste0("Age-citation trend with and without extreme points", title_suffix),
      subtitle = glue("Left: all records; right: {n_outliers} extreme records hidden for display only"),
      caption = trend_caption,
      theme = annotation_theme(legend.position = "right",
        plot.background = element_rect(fill = "white"), panel.background = element_rect(fill = "white")))
  save(p_scatter_vs_clean, "age_vs_citations_scatter_vs_clean", 16, 6)

  p_faceted_clean <- base_plot(ac$data, ac$trend_by_omic) +
    facet_wrap(~omic_type, nrow = 2) +
    labs(title = "Age-citation trend by omics domain, extreme points hidden",
      subtitle = hidden_subtitle, caption = trend_caption) + age_axes +
    scale_fill_manual(values = omic_palette, guide = "none") +
    landscape_plot_theme(legend.position = "none") +
    coord_cartesian(ylim = ac$display_limits)
  save(p_faceted_clean, "age_vs_citations_faceted_clean", 12, 8)

  # Combined figure retains every record. LOESS is a visual trend smoother only
  # and is never used to determine eligibility.
  p_combined <- p_scatter + p_faceted +
    plot_layout(ncol = 2, widths = c(1, 1.5)) +
    plot_annotation(
      title = paste0("Citation visibility by years since publication", title_suffix),
      subtitle = glue("All {scales::comma(nrow(ac$data))} {records_label}; trend lines are descriptive"),
      caption = trend_caption,
      theme = annotation_theme(plot.background = element_rect(fill = "white", color = NA),
        panel.background = element_rect(fill = "white", color = NA)))
  save(p_combined, "age_vs_citations_combined", 18, 7)
  invisible(NULL)
}

# 5. Candidate-only figures -------------------------------------------------------
# This section builds and saves the candidate-only figures from candidate_analysis().

make_stack_faceted_bars <- function(summary_df, panel_title, domain_sizes) {
  # Missingness is shown in headings, not as a declared feature. Keep all
  # records in the denominator so incomplete metadata remains visible.
  facet_labels <- summary_df %>% group_by(omic_type) %>%
    summarise(eligible = first(denominator), missing = sum(n[label == "Unknown"]), .groups = "drop") %>%
    mutate(label_text = paste0(omic_type, " (n = ", scales::comma(eligible), ")",
      "\nNot reported: ", scales::comma(missing), " (",
      scales::percent(missing / eligible, accuracy = 0.1), ")")) %>%
    { setNames(.$label_text, .$omic_type) }
  category_order <- summary_df %>%
    filter(label != "Unknown") %>% group_by(label) %>%
    summarise(total = sum(n), .groups = "drop") %>%
    arrange(desc(total), label) %>% pull(label)
  category_positions <- setNames(rev(seq_along(category_order)), category_order)
  plot_data <- tidyr::expand_grid(omic_type = as.character(domain_sizes$omic_type), label = category_order) %>%
    left_join(summary_df %>% select(omic_type, label, n), by = c("omic_type", "label")) %>%
    left_join(domain_sizes %>% mutate(omic_type = as.character(omic_type)), by = "omic_type") %>%
    mutate(n = replace_na(n, 0L), prevalence = n / denominator,
      y_position = unname(category_positions[label]),
      omic_type = factor(omic_type, levels = names(omic_palette)))
  ggplot(plot_data, aes(x = prevalence, y = y_position, fill = omic_type)) +
    geom_col(orientation = "y", width = 0.65, colour = thesis_neutral[["outline"]], linewidth = 0.25) +
    geom_text(aes(label = scales::percent(prevalence, accuracy = 0.1)),
      hjust = -0.15, size = 3, colour = thesis_neutral[["ink"]]) +
    facet_wrap(~omic_type, ncol = 2, labeller = as_labeller(facet_labels)) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1),
      limits = c(0, NA), expand = expansion(mult = c(0, 0.23))) +
    scale_y_continuous(breaks = unname(category_positions), labels = category_order,
      limits = c(0.5, max(category_positions) + 0.5)) +
    labs(title = panel_title, x = "Records declaring this feature (%)", y = NULL) +
    theme_thesis(base_size = 10, legend.position = "none") +
    theme(panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
      panel.spacing.x = grid::unit(1.4, "lines"))
}

make_top_tool_status <- function(status_df, totals_df, top_n = 5L) {
  ordered_levels <- totals_df %>% arrange(desc(total_by_tool)) %>% slice_head(n = top_n) %>% pull(tool_type)
  status_df %>%
    filter(tool_type %in% ordered_levels) %>%
    mutate(tool_type = factor(tool_type, levels = ordered_levels))
}

plot_citation_engagement <- function(omics_filter, df, axis_limits, axis_labels, legend_labels, top_n_labels = 12) {
  sub <- df %>% filter(omic_type == omics_filter)
  if (nrow(sub) == 0) return(NULL)
  sub_fin <- sub %>% filter(is.finite(citation_visibility_log) & is.finite(github_engagement_log))
  if (nrow(sub_fin) < 3) {
    message(glue("Skipping citation-engagement plot for {omics_filter}: insufficient numeric metrics (n = {nrow(sub_fin)})."))
    return(NULL)
  }
  x_med <- median(sub_fin$citation_visibility_log, na.rm = TRUE)
  y_med <- median(sub_fin$github_engagement_log, na.rm = TRUE)
  if (is.na(x_med) || is.na(y_med)) {
    message(glue("Skipping citation-engagement plot for {omics_filter}: median(s) are NA."))
    return(NULL)
  }
  # Top-right quadrant labels
  top_tools <- sub_fin %>%
    filter(citation_visibility_log > x_med, github_engagement_log > y_med) %>%
    slice_max(order_by = (citation_visibility_log + github_engagement_log), n = top_n_labels)
  # log1p guide lines for easier interpretation of multiplicative differences
  x_guides <- log1p(c(1, 10, 100))
  y_guides <- log1p(c(10, 100, 1000))
  sub_fin <- sub_fin %>%
    mutate(strip_label = glue("{omics_filter} (n = {scales::comma(nrow(sub_fin))} of {scales::comma(nrow(sub))} with GitHub data)"))
  ggplot(sub_fin, aes(x = citation_visibility_log, y = github_engagement_log)) +
    geom_point(aes(fill = maintenance), shape = 21, colour = point_outline, stroke = point_stroke,
      alpha = point_alpha, size = point_size + 0.1) +
    geom_vline(xintercept = x_med, linetype = "dashed", color = thesis_neutral[["guide"]]) +
    geom_hline(yintercept = y_med, linetype = "dashed", color = thesis_neutral[["guide"]]) +
    geom_vline(xintercept = x_guides, linetype = "dotted", color = "gray65", linewidth = 0.4) +
    geom_hline(yintercept = y_guides, linetype = "dotted", color = "gray65", linewidth = 0.4) +
    ggrepel::geom_text_repel(
      data = top_tools, aes(label = name),
      size = 3, max.overlaps = Inf, box.padding = 0.4,
      point.padding = 0.2, segment.color = thesis_neutral[["guide"]], seed = 42,
      colour = thesis_neutral[["ink"]], show.legend = FALSE
    ) +
    scale_fill_manual(values = maintenance_palette_points, na.value = maintenance_palette_points[["Unknown"]]) +  # points: full strength
    guides(fill = guide_legend(override.aes = list(alpha = 1, size = 3))) +
    scale_x_continuous(expand = expansion(mult = c(0.03, 0.05))) +
    scale_y_continuous(expand = expansion(mult = c(0.03, 0.05))) +
    coord_cartesian(xlim = c(axis_limits$x_min, axis_limits$x_max), ylim = c(axis_limits$y_min, axis_limits$y_max)) +
    # One-panel facet gives each domain a tinted strip that also carries n.
    facet_wrap(~strip_label) +
    labs(x = axis_labels$citations_per_year_log, y = axis_labels$github_engagement_log,
      fill = legend_labels$maintenance) +
    theme_thesis(base_size = 11, legend.position = "bottom") +
    theme(panel.border = element_rect(fill = NA, colour = thesis_neutral[["grid"]]))
}

build_tool_dist_plot <- function(axis_labels, tool_type_labels, tools_type) {
  ggplot(tools_type, aes(x = fct_reorder(tool_type, max_prevalence), y = prevalence, colour = omic_type)) +
    geom_errorbar(aes(ymin = conf_low, ymax = conf_high), width = 0.3, colour = thesis_neutral[["guide"]], linewidth = 0.4) +
    geom_point(aes(fill = omic_type), shape = 21, colour = thesis_neutral[["outline"]], stroke = 0.25, size = dot_size) +
    facet_wrap(~omic_type, labeller = as_labeller(tool_type_labels)) +
    coord_flip() +
    labs(title = "Tool types by omics domain",
      subtitle = "Share of records declaring each type, with Wilson 95% CIs; a record can have several types",
      x = NULL, y = axis_labels$share) +
    theme_thesis(base_size = 11, legend.position = "none") +
    theme(axis.text.y = element_text(size = 9)) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_fill_manual(values = omic_palette, guide = "none")
}

build_tool_dist_bars_plot <- function(axis_labels, tool_type_labels, tools_type_bars) {
  ggplot(tools_type_bars, aes(x = prevalence, y = tool_type, fill = omic_type)) +
    geom_col(orientation = "y", width = 0.7, colour = thesis_neutral[["outline"]], linewidth = 0.25) +
    geom_text(aes(label = scales::percent(prevalence, accuracy = 0.1)),
      hjust = -0.15, size = 3, colour = thesis_neutral[["ink"]]) +
    facet_wrap(~omic_type, ncol = 2, labeller = as_labeller(tool_type_labels)) +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1),
      limits = c(0, NA), expand = expansion(mult = c(0, 0.18))) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    labs(title = "Tool types by omics domain",
      subtitle = "Share of records declaring each type; a record can have several types",
      caption = "Denominators include records with no declared type; percentages can add up to more than 100%.",
      x = axis_labels$share, y = NULL) +
    theme_thesis(base_size = 11, legend.position = "none") +
    theme(axis.text.y = element_text(size = 9),
      panel.grid.major.y = element_blank(), panel.grid.minor = element_blank(),
      plot.caption = element_text(hjust = 0, size = 9))
}

build_feature_prevalence_plot <- function(axis_labels, data, facet_labels, title) {
  ggplot(data, aes(x = prevalence, y = fct_reorder(label, prevalence), colour = omic_type)) +
    geom_errorbar(aes(xmin = conf_low, xmax = conf_high), orientation = "y", width = 0.3,
      colour = thesis_neutral[["guide"]], linewidth = 0.4) +
    geom_point(aes(fill = omic_type), shape = 21, colour = thesis_neutral[["outline"]], stroke = 0.25, size = dot_size) +
    facet_wrap(~omic_type, labeller = as_labeller(facet_labels)) +
    scale_x_continuous(labels = scales::percent_format(accuracy = 1), limits = c(0, NA)) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    labs(title = title, subtitle = "Share of records with Wilson 95% CIs; a record can declare several",
      x = axis_labels$share, y = NULL) + theme_thesis(base_size = 10)
}

build_language_os_faceted_bars_plot <- function(p_lang_faceted_bars, p_os_faceted_bars) {
  p_lang_faceted_bars + p_os_faceted_bars +
    patchwork::plot_layout(ncol = 2) +
    patchwork::plot_annotation(
      subtitle = "A record can declare multiple features; percentages do not sum to 100%.",
      caption = paste0(
        "Denominator: all records in each domain, including those with missing metadata. Not reported = missing metadata for the panel's feature.",
        "\nOther = any language outside the top five (each record counted once within Other)."),
      theme = theme(plot.caption = element_text(hjust = 0, size = 9))
    )
}

build_tech_stack_faceted_plot <- function(p_lang_faceted_bars, p_license_faceted_bars, p_os_faceted_bars) {
  p_license_faceted_bars / (p_lang_faceted_bars | p_os_faceted_bars) +
    plot_layout(heights = c(0.8, 1)) +
    plot_annotation(
      title = "Technical metadata of candidate tools by omics domain",
      subtitle = "Licence, programming language and operating system as declared in bio.tools; a record can declare several languages or systems",
      caption = paste0("Denominator: all records in each domain, including those with missing metadata. Not reported = missing metadata for that panel. ",
        "Other = any language outside the top five, or any system outside the top three."),
      theme = annotation_theme()
    )
}

build_tech_heat_plot <- function(domain_col_labels, tech_heat_df) {
  ggplot(tech_heat_df, aes(x = omic_type, y = row_id)) +
    geom_tile(aes(fill = cell_fill), colour = "white", linewidth = 0.8) +
    geom_text(aes(label = scales::percent(prevalence, accuracy = 1), colour = text_col), size = 3.3) +
    facet_grid(feature ~ ., scales = "free_y", space = "free_y", switch = "y") +
    scale_fill_identity() +
    scale_colour_identity() +
    scale_x_discrete(position = "top", labels = domain_col_labels) +
    scale_y_discrete(labels = function(x) sub("^.*___", "", x)) +
    labs(title = "Technical metadata of candidate tools by omics domain",
      subtitle = "Share of records in each domain declaring each value; darker = more common (shading scaled to the largest share)",
      caption = paste0("Denominator: all records in each domain. Records can declare several languages or operating systems, so columns need not sum to 100%.\n",
        "Not reported = value missing in bio.tools. Other = any language outside the top five or system outside the top three.\n",
        "Licence: permissive = MIT, BSD, Apache, CC0, ISC; copyleft = GPL family."),
      x = NULL, y = NULL) +
    theme_thesis(base_size = 11) +
    theme(panel.grid = element_blank(),
      strip.placement = "outside",
      strip.text.y.left = element_text(angle = 0, hjust = 1, face = "bold"),
      axis.text.x.top = element_text(face = "bold", colour = thesis_neutral[["ink"]]),
      axis.ticks = element_blank(),
      plot.caption = element_text(hjust = 0, size = 8.5))
}

build_tech_stack_combined_plot <- function(p_lang, p_license, p_os) {
  p_license / (p_lang | p_os) +
    plot_layout(heights = c(0.8, 1)) +
    plot_annotation(
      title = "Technical metadata of candidate tools",
      subtitle = "Licence, programming language and operating system as declared in bio.tools",
      theme = annotation_theme()
    )
}

build_upset_bars_plot <- function(upset_intersections) {
  ggplot(upset_intersections, aes(x = combination, y = n)) +
    geom_col(fill = thesis_neutral[["ink"]], width = 0.7) +
    geom_text(aes(label = scales::comma(n)), vjust = -0.4, size = 3, colour = thesis_neutral[["ink"]]) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.12)), labels = scales::comma) +
    labs(x = NULL, y = "Unique bio.tools records\nin intersection") +
    theme_thesis(base_size = 11) +
    theme(axis.text.x = element_blank(), panel.grid.major.x = element_blank())
}

build_upset_matrix_plot <- function(upset_matrix) {
  ggplot(upset_matrix, aes(x = combination, y = set)) +
    geom_point(data = function(d) dplyr::filter(d, !member), colour = thesis_neutral[["grid"]], size = 3.2) +
    geom_line(data = function(d) dplyr::filter(d, member), aes(group = combination),
      colour = thesis_neutral[["outline"]], linewidth = 0.6) +
    geom_point(data = function(d) dplyr::filter(d, member), aes(fill = as.character(set)),
      shape = 21, colour = thesis_neutral[["outline"]], stroke = 0.3, size = 3.6) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    labs(x = NULL, y = NULL) +
    theme_thesis(base_size = 11) +
    theme(axis.text.x = element_blank(), panel.grid.major.x = element_blank())
}

build_upset_sets_plot <- function(upset_set_sizes) {
  ggplot(upset_set_sizes, aes(x = n, y = set, fill = as.character(set))) +
    geom_col(width = 0.6) +
    scale_x_reverse(labels = scales::comma, expand = expansion(mult = c(0.15, 0))) +
    scale_fill_manual(values = omic_palette, guide = "none") +
    labs(x = "Records per domain", y = NULL) +
    theme_thesis(base_size = 11) +
    theme(axis.text.y = element_blank(), panel.grid.major.y = element_blank())
}

build_maintenance_distribution_plot <- function(axis_labels, legend_labels, maintenance_distribution, maintenance_ref_date) {
  ggplot(maintenance_distribution, aes(x = omic_type, y = proportion, fill = maintenance)) +
    geom_col() +
    geom_text(aes(label = if_else(proportion >= 0.05,
        glue("{scales::percent(proportion, accuracy = 1)}\n({n}/{denominator})"), ""),
      colour = ink_on(maintenance_palette[as.character(maintenance)]),
      group = maintenance),  # keep labels stacked in the same order as the bars
      position = position_stack(vjust = 0.5), size = 2.7) +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1)) +
    scale_fill_manual(values = maintenance_palette, drop = TRUE) +
    scale_colour_identity() +  # label colour = black or white, chosen per fill by ink_on()
    labs(title = "Repository commit-recency status by omics domain",
      subtitle = glue("All candidate records; Unknown = no usable GitHub repository or push date (reference date {maintenance_ref_date})"),
      x = NULL, y = axis_labels$share, fill = legend_labels$maintenance) +
    theme_thesis(base_size = 11)
}

# Status labels with the number of records in each group, e.g. "Active (n = 609)".
status_n_labels <- function(df) {
  counts <- df %>% count(maintenance) %>% mutate(maintenance = as.character(maintenance))
  setNames(paste0(counts$maintenance, " (n = ", scales::comma(counts$n), ")"), counts$maintenance)
}

build_status_ridge_plot <- function(df, x, title, subtitle, x_label, legend_labels) {
  ggplot(df, aes(x = .data[[x]], y = maintenance, fill = maintenance)) +
    ggridges::geom_density_ridges(alpha = 0.85, scale = 1.5, rel_min_height = 0.01,
      color = thesis_neutral[["outline"]], linewidth = 0.3) +
    labs(title = title, subtitle = subtitle, x = x_label,
      y = legend_labels$maintenance, fill = legend_labels$maintenance) +
    scale_fill_manual(values = maintenance_palette, name = legend_labels$maintenance) +
    scale_y_discrete(labels = status_n_labels(df)) +
    landscape_plot_theme(legend.position = "none")
}

build_tool_status_count_plot <- function(axis_labels, legend_labels, tool_status_count, tool_status_labels) {
  ggplot(tool_status_count, aes(x = tool_type, y = n, fill = maintenance)) +
    geom_col(position = "stack") +
    facet_wrap(~omic_type) +
    coord_flip(clip = "off") +
    geom_text(data = tool_status_labels, aes(x = tool_type, y = total_in_panel, label = scales::comma(total_in_panel)),
      inherit.aes = FALSE, hjust = -0.15, size = 3, colour = thesis_neutral[["ink"]]) +
    labs(title = "Commit-recency status by tool type (counts)",
      subtitle = "Five most common tool types; labels give records per bar",
      x = NULL, y = axis_labels$tool_count, fill = legend_labels$maintenance) +
    theme_thesis(base_size = 11, legend.position = "bottom") +
    scale_y_continuous(expand = expansion(mult = c(0, 0.22))) +
    scale_fill_manual(values = maintenance_palette, na.value = maintenance_palette[["Unknown"]], name = legend_labels$maintenance)
}

build_tool_status_pct_plot <- function(axis_labels, legend_labels, tool_status_pct, tool_status_pct_labels) {
  ggplot(tool_status_pct, aes(x = tool_type, y = share, fill = maintenance)) +
    geom_col(position = position_stack(reverse = TRUE)) +
    geom_text(aes(label = if_else(share >= 0.08, scales::percent(share, accuracy = 1), ""),
        colour = ink_on(maintenance_palette[as.character(maintenance)]), group = maintenance),
      position = position_stack(vjust = 0.5, reverse = TRUE), size = 2.6) +
    geom_text(data = tool_status_pct_labels, aes(x = tool_type, y = 1.02, label = paste0("n = ", scales::comma(bar_n))),
      inherit.aes = FALSE, hjust = 0, size = 2.8, colour = thesis_neutral[["ink"]]) +
    facet_wrap(~omic_type) +
    coord_flip(clip = "off") +
    scale_y_continuous(labels = scales::percent_format(accuracy = 1), breaks = seq(0, 1, 0.25),
      expand = expansion(mult = c(0, 0.18))) +
    scale_fill_manual(values = maintenance_palette, name = legend_labels$maintenance, drop = TRUE) +
    scale_colour_identity() +
    labs(title = "Commit-recency status by tool type (share)",
      subtitle = "Five most common tool types; each bar sums to 100%",
      x = NULL, y = axis_labels$share) +
    theme_thesis(base_size = 11, legend.position = "bottom")
}

build_engagement_combined_plot <- function(engagement_plots) {
  patchwork::wrap_plots(engagement_plots, ncol = 2) +
    patchwork::plot_layout(guides = "collect") +
    patchwork::plot_annotation(
      title = "Citations per year vs GitHub engagement",
      subtitle = "GitHub-observable candidate records, coloured by commit-recency status",
      caption = paste(
        "Dashed lines: within-domain medians; records above both (upper right) have higher citation visibility and higher engagement than the domain median.",
        "\nDotted lines: 1, 10 and 100 citations per year; 10, 100 and 1,000 stars + forks + watchers. Labels: highest-ranked upper-right records."
      ),
      theme = theme(plot.title = element_text(face = "bold", size = 14),
        plot.caption = element_text(hjust = 0, size = 9))
    ) &
    theme(legend.position = "bottom")
}
