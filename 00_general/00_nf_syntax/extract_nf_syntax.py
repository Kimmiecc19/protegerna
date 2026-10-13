#!/usr/bin/env python3

"""
This script does the following:
1. Fetches the HTML content of multiple Nextflow documentation pages.
2. Parses the HTML to extract sections of text that describe Nextflow syntax elements, including their explanations, constraints, allowed elements, and examples.
3. Classifies the extracted information into categories based on the source documentation page and content patterns.
4. Merges and deduplicates entries that refer to the same syntax element across different documentation pages.
5. Generates a Markdown file that organizes the syntax elements into a visually navigable format, including an index and categorized sections with collapsible details.

The resulting Markdown file serves as an offline reference for Nextflow syntax, allowing users to quickly look up terms and their associated information without needing to navigate through the official documentation. The script is designed to be robust against variations in the documentation structure and to provide a comprehensive mapping of Nextflow syntax elements.

Example usage:
python extract_nf_syntax_full_0704.py
"""

import argparse
import html
import json
import re
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.nextflow.io/docs/stable/reference/syntax.html",
    "https://www.nextflow.io/docs/stable/reference/stdlib-types.html",
    "https://www.nextflow.io/docs/stable/reference/process.html",
    "https://www.nextflow.io/docs/stable/reference/channel.html",
    "https://www.nextflow.io/docs/stable/reference/operator.html",
    "https://www.nextflow.io/docs/stable/reference/cli.html",
    "https://www.nextflow.io/docs/stable/reference/config.html",
    "https://www.nextflow.io/docs/stable/reference/env-vars.html",
    "https://www.nextflow.io/docs/stable/script.html",
    "https://www.nextflow.io/docs/stable/working-with-files.html",
    "https://www.nextflow.io/docs/stable/workflow.html",
    "https://www.nextflow.io/docs/stable/module.html",
]


HEADERS = {
    "User-Agent": "NextflowSyntaxMapper/1.0"
}

# Network settings
NETWORK_TIMEOUT = 30
NETWORK_MAX_RETRIES = 3
NETWORK_RETRY_DELAY = 1

CONSTRAINT_PATTERN = re.compile(
    r"\b(?:should|must|only|cannot|can't|may not|required|not allowed|prohibited)\b",
    re.IGNORECASE,
)

TERM_GROUP_PATTERNS = [
    ("Shebang", re.compile(r"\bshebang\b", re.IGNORECASE)),
    ("Feature flag", re.compile(r"\bfeature\s+flag\b", re.IGNORECASE)),
    ("Include", re.compile(r"\binclude\b", re.IGNORECASE)),
    ("Params", re.compile(r"\bparams?\b|\bparameter\b", re.IGNORECASE)),
    ("Workflow", re.compile(r"\bworkflow\b", re.IGNORECASE)),
    ("Process", re.compile(r"\bprocess\b", re.IGNORECASE)),
    ("Function", re.compile(r"\bfunction\b", re.IGNORECASE)),
    ("Enum", re.compile(r"\benum\b", re.IGNORECASE)),
    ("Output", re.compile(r"\boutput\b", re.IGNORECASE)),
    ("Environment Variables", re.compile(r"\benvironment\s+variables?\b|\benv\s*vars?\b|\benv-vars\b", re.IGNORECASE)),
    ("Variable", re.compile(r"\bvariable\b", re.IGNORECASE)),
    ("Assignment", re.compile(r"\bassign(?:ment)?\b", re.IGNORECASE)),
    ("Type", re.compile(r"\btype\b", re.IGNORECASE)),
    ("Channel", re.compile(r"\bchannel\b", re.IGNORECASE)),
    ("Operator", re.compile(r"\boperator\b", re.IGNORECASE)),
    ("CLI", re.compile(r"\bcli\b|\bcommand\s+line\b", re.IGNORECASE)),
    ("Config", re.compile(r"\bconfig\b|\bconfiguration\b", re.IGNORECASE)),
    ("Modules", re.compile(r"\bmodule\b", re.IGNORECASE)),
    ("Files", re.compile(r"\bfile\b", re.IGNORECASE)),
]

GROUP_DISPLAY_ORDER = [
    "Workflow",
    "Process",
    "Channel",
    "Operator",
    "Function",
    "Enum",
    "Params",
    "Config",
    "CLI",
    "Modules",
    "Files",
    "Environment Variables",
    "Output",
    "Type",
    "Variable",
    "Assignment",
    "Include",
    "Feature flag",
    "Shebang",
]

CATEGORY_DISPLAY_ORDER = [
    "Workflow",
    "Process",
    "Channel",
    "Operator",
    "CLI",
    "Config",
    "Types",
    "Script Language",
    "Modules",
    "Files",
    "Other",
]

CATEGORY_STYLE = {
    "Workflow": {"label": "Workflow", "color": "0ea5e9", "marker": "[WF]"},
    "Process": {"label": "Process", "color": "22c55e", "marker": "[PR]"},
    "Channel": {"label": "Channel", "color": "06b6d4", "marker": "[CH]"},
    "Operator": {"label": "Operator", "color": "f59e0b", "marker": "[OP]"},
    "CLI": {"label": "CLI", "color": "6366f1", "marker": "[CLI]"},
    "Config": {"label": "Config", "color": "ef4444", "marker": "[CFG]"},
    "Types": {"label": "Types", "color": "8b5cf6", "marker": "[TY]"},
    "Script Language": {"label": "Script", "color": "14b8a6", "marker": "[SC]"},
    "Modules": {"label": "Modules", "color": "eab308", "marker": "[MD]"},
    "Files": {"label": "Files", "color": "64748b", "marker": "[FL]"},
    "Other": {"label": "Other", "color": "6b7280", "marker": "[OT]"},
}

CATEGORY_SOURCE_PATTERNS = [
    ("Workflow", ("workflow.html",)),
    ("Process", ("reference/process.html", "/process.html")),
    ("Channel", ("reference/channel.html", "/channel.html")),
    ("Operator", ("reference/operator.html",)),
    ("CLI", ("reference/cli.html",)),
    ("Config", ("reference/config.html", "reference/env-vars.html")),
    ("Types", ("reference/stdlib-types.html",)),
    ("Script Language", ("reference/syntax.html", "/script.html")),
    ("Modules", ("module.html",)),
    ("Files", ("working-with-files.html",)),
]

TEXT_ARTIFACT_REPLACEMENTS = {
    "aself-containeda": "self-contained",
    "asquarea": "square",
    "aCartesiana": "Cartesian",
    "atruthya": "truthy",
    "aemptya": "empty",
    "amapsa": "maps",
    "donat": "don't",
    "doesnat": "doesn't",
    "wonat": "won't",
    "itas": "it's",
    "youave": "you've",
    "processas": "process's",
}

# -----------------------------
# Helpers
# -----------------------------

def clean_text(text):
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = " ".join(ascii_text.split())
    for old, new in TEXT_ARTIFACT_REPLACEMENTS.items():
        cleaned = re.sub(rf"\b{re.escape(old)}\b", new, cleaned)
    return cleaned


def markdown_safe_text(text):
    return html.escape(clean_text(text), quote=False)


def strip_type_params(term):
    """Remove type parameters like <E>, <K,V> from term names."""
    return re.sub(r'<[^>]+>', '', term).strip()


def markdown_term_label(term):
    normalized = clean_text(term).replace("`", "").strip()
    # Strip type parameters
    normalized = strip_type_params(normalized)
    if "<" in normalized and ">" in normalized:
        return f"`{normalized}`"
    return markdown_safe_text(normalized)


def truncate_preview(text, max_length, truncate_length):
    """Truncate text for preview display with ellipsis."""
    text = text.strip()
    if len(text) > max_length:
        return text[:truncate_length] + "..."
    return text


def dedupe_preserve_order(items):
    return dedupe_preserve_order_by(items, clean_text)


def dedupe_preserve_order_by(items, normalizer):
    seen = set()
    result = []
    for item in items:
        cleaned = normalizer(item)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def dedupe_exact_preserve_order(items):
    return dedupe_preserve_order_by(items, lambda item: item.strip())


def dedupe_urls_preserve_order(urls):
    return dedupe_preserve_order_by(urls, lambda url: url.strip())


def term_group(term):
    for group_name, pattern in TERM_GROUP_PATTERNS:
        if pattern.search(term):
            return group_name
    return term


def heading_anchor(text):
    lowered = text.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", lowered)
    return re.sub(r"\s+", "-", cleaned)


def entry_anchor(category, term):
    return heading_anchor(f"{category}-{strip_type_params(term)}")


def sort_entries_for_markdown(data):
    order_map = {name: idx for idx, name in enumerate(GROUP_DISPLAY_ORDER)}
    return sorted(
        data,
        key=lambda entry: (order_map.get(entry["group"], 10_000), entry["group"].lower()),
    )


def entry_category(entry):
    source_text = " ".join(entry.get("sources", []))

    for category, patterns in CATEGORY_SOURCE_PATTERNS:
        if any(pattern in source_text for pattern in patterns):
            return category

    return "Other"


def group_entries_by_category(sorted_data):
    grouped = {category: [] for category in CATEGORY_DISPLAY_ORDER}
    for entry in sorted_data:
        grouped.setdefault(entry_category(entry), []).append(entry)
    return [(category, grouped[category]) for category in CATEGORY_DISPLAY_ORDER if grouped.get(category)]


def build_synopsis(entry):
    explanation = entry.get("explanation", [])
    if explanation:
        first = strip_type_params(clean_text(explanation[0]))
        if first and not first.endswith(":"):
            return first
    related_terms = dedupe_preserve_order(entry.get("terms", [entry["term"]]))
    if related_terms:
        return f"Reference for {strip_type_params(related_terms[0])}."
    return ""


def category_marker(category):
    return CATEGORY_STYLE.get(category, {}).get("marker", "[SEC]")


def category_badge_markdown(category, count):
    style = CATEGORY_STYLE.get(category, {})
    label = style.get("label", category)
    color = style.get("color", "6b7280")
    value = f"{count}%20terms"
    return (
        f"![{label}](https://img.shields.io/badge/{label}-{value}-{color}?style=flat-square)"
    )


def category_block_markdown(category, entries):
    style = CATEGORY_STYLE.get(category, {})
    label = style.get("label", category)
    marker = category_marker(category)
    anchor = heading_anchor(category)
    preview_terms = ", ".join(markdown_term_label(entry["group"]) for entry in entries[:4])
    if len(entries) > 4:
        preview_terms += ", ..."

    return (
        f"<table>\n"
        f"  <tr><td>\n"
        f"<strong>{marker} {label}</strong><br/>\n"
        f"<a href=\"#{anchor}\">Jump to section</a><br/>\n"
        f"<em>Terms:</em> {len(entries)}<br/>\n"
        f"<em>Preview:</em> {html.escape(preview_terms or 'None')}\n"
        f"  </td></tr>\n"
        f"</table>\n"
    )


def write_visual_header(fh, sorted_data):
    fh.write("# Nextflow Syntax (Mapped, Combined Sources)\n\n")
    fh.write(
        "![Nextflow Syntax Reference Banner](https://dummyimage.com/1400x220/0b3d91/ffffff&text=Nextflow+Syntax+Reference)\n\n"
    )
    fh.write(
        "A grouped reference of Nextflow terms extracted from multiple docs pages, rendered with quick-glance visual navigation.\n\n"
    )

    counts = {category: 0 for category in CATEGORY_DISPLAY_ORDER}
    for entry in sorted_data:
        category = entry_category(entry)
        counts[category] = counts.get(category, 0) + 1

    fh.write("## Snapshot\n\n")
    fh.write(
        f"![Total Terms](https://img.shields.io/badge/Total%20Grouped%20Terms-{len(sorted_data)}-111827?style=for-the-badge) "
        "![Mode](https://img.shields.io/badge/Mode-full-334155?style=for-the-badge)\n\n"
    )

    badge_lines = []
    current_line = []
    for category in CATEGORY_DISPLAY_ORDER:
        count = counts.get(category, 0)
        if count <= 0:
            continue
        current_line.append(category_badge_markdown(category, count))
        if len(current_line) == 3:
            badge_lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        badge_lines.append(" ".join(current_line))

    for line in badge_lines:
        fh.write(line + "\n\n")


def write_html_block_quote(fh, title, body_lines):
    fh.write(f"> **{title}**\n")
    for line in body_lines:
        fh.write(f"> {line}\n")
    fh.write("\n")


def write_collapsible_section(fh, heading, body_writer, summary="Show details"):
    fh.write(f"## {heading}\n\n")
    fh.write("<details>\n")
    fh.write(f"<summary>{summary}</summary>\n\n")
    body_writer()
    fh.write("</details>\n\n")


def write_callouts(fh):
    fh.write(
        "> [!TIP]\n"
        "> Start with the term index table for fast lookup, then expand details only when needed.\n\n"
    )
    fh.write(
        "> [!IMPORTANT]\n"
        "> Constraints are extracted from multiple documentation pages and may vary by Nextflow version.\n\n"
    )


def write_entry_card_summary(fh, entry, category):
    synopsis = build_synopsis(entry) or "Reference term."
    term_display = markdown_term_label(entry["group"])

    fh.write(
        "<table>\n"
        "  <tr><td>\n"
        f"<strong>{category_marker(category)} {term_display}</strong><br/>\n"
        f"{html.escape(synopsis)}<br/>\n"
    )
    fh.write("  </td></tr>\n</table>\n\n")


def write_term_index_html_table(fh, sorted_data):
    """Write term index as HTML table for proper rendering in all outputs."""
    fh.write("Use this table for quick lookup.\n\n")
    fh.write("<table>\n")
    fh.write("  <thead>\n")
    fh.write("    <tr><th>Term</th><th>Category</th><th>Synopsis</th><th>Related Terms</th></tr>\n")
    fh.write("  </thead>\n")
    fh.write("  <tbody>\n")

    for entry in sorted_data:
        category = entry_category(entry)
        related_terms = dedupe_preserve_order(entry.get("terms", [entry["term"]]))
        synopsis = build_synopsis(entry) or "Reference term."
        term_display = markdown_term_label(entry["group"])
        anchor = entry_anchor(category, entry["group"])
        related_preview = ", ".join(markdown_term_label(term) for term in related_terms[:4])
        if len(related_terms) > 4:
            related_preview += ", ..."

        term_link = f'<a href="#{anchor}">{term_display}</a>'
        syn_display = html.escape(truncate_preview(synopsis, 100, 97))
        rel_display = html.escape(related_preview or '-')
        cat_display = f"{category_marker(category)} {html.escape(category)}"

        fh.write(f"    <tr><td>{term_link}</td><td>{cat_display}</td><td>{syn_display}</td><td>{rel_display}</td></tr>\n")

    fh.write("  </tbody>\n")
    fh.write("</table>\n\n")


def write_sources_html_table(fh, sources):
    """Write sources as HTML table for proper rendering in all outputs."""
    fh.write("<table>\n")
    fh.write("  <thead>\n")
    fh.write("    <tr><th>Source URL</th></tr>\n")
    fh.write("  </thead>\n")
    fh.write("  <tbody>\n")

    for source in sources:
        source_display = html.escape(source)
        fh.write(f"    <tr><td><a href=\"{html.escape(source)}\" target=\"_blank\">{source_display}</a></td></tr>\n")

    fh.write("  </tbody>\n")
    fh.write("</table>\n\n")


def write_html_list_section(fh, title, items):
    if not items:
        return
    fh.write(f"<h4>{title}</h4>\n")
    fh.write("<ul>\n")
    for item in items:
        fh.write(f"  <li>{html.escape(item)}</li>\n")
    fh.write("</ul>\n\n")


def write_html_code_block(fh, code, language="nextflow"):
    fh.write(f"<pre><code class=\"language-{language}\">")
    fh.write(html.escape(code))
    fh.write("</code></pre>\n\n")


def write_entry_details(fh, entry):
    fh.write("<details>\n")
    fh.write("<summary>Show full details</summary>\n\n")

    if entry["syntax"]:
        fh.write("<h4>Syntax</h4>\n")
        write_html_code_block(fh, entry["syntax"])

    write_html_list_section(fh, "Explanation", entry["explanation"])
    write_html_list_section(fh, "Constraints", entry["constraints"])
    write_html_list_section(fh, "Allowed Elements", entry["allowed_elements"])

    if entry["examples"]:
        fh.write("<h4>Examples</h4>\n")
        for ex in entry["examples"]:
            write_html_code_block(fh, ex)

    fh.write("</details>\n\n")


def get_section_term(section):
    for heading_tag in ("h3", "h2", "h4"):
        heading = section.find(heading_tag, recursive=False)
        if heading:
            term = clean_text(heading.get_text(" ", strip=True))
            # Remove common trailing heading markers that may appear in docs rendering.
            term = re.sub(r"[#:>\-\s]+$", "", term)
            # Nextflow docs headings include a permalink icon that can collapse to trailing 'i'.
            term = re.sub(r"\s+[iI]$", "", term)
            return term
    return ""


def merge_entries(existing, incoming):
    if not existing.get("syntax") and incoming.get("syntax"):
        existing["syntax"] = incoming["syntax"]

    merge_rules = [
        ("examples", dedupe_exact_preserve_order),
        ("explanation", dedupe_preserve_order),
        ("constraints", dedupe_preserve_order),
        ("allowed_elements", dedupe_preserve_order),
        ("sources", dedupe_urls_preserve_order),
        ("terms", dedupe_preserve_order),
        ("ids", dedupe_exact_preserve_order),
    ]
    for key, deduper in merge_rules:
        existing[key] = deduper(existing.get(key, []) + incoming.get(key, []))

    return existing


def split_sentences(text):
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]


def extract_paragraphs(section):
    return [
        clean_text(p.get_text(" ", strip=True))
        for p in section.find_all("p", recursive=False)
        if p.get_text(strip=True)
    ]


def extract_code_blocks(section):
    return [
        pre.get_text("\n", strip=True)
        for pre in section.find_all("pre", recursive=False)
        if pre.get_text(strip=True)
    ]


def extract_lists(section):
    items = []
    for ul in section.find_all("ul", recursive=False):
        for li in ul.find_all("li", recursive=False):
            txt = clean_text(li.get_text(" ", strip=True))
            if txt:
                items.append(txt)
    return dedupe_preserve_order(items)


# -----------------------------
# Semantic mapping logic
# -----------------------------

def classify_sentences(paragraphs):
    explanation = []
    constraints = []

    for para in paragraphs:
        sentences = split_sentences(para)

        for s in sentences:
            if CONSTRAINT_PATTERN.search(s):
                constraints.append(s)
            else:
                explanation.append(s)

    return dedupe_preserve_order(explanation), dedupe_preserve_order(constraints)


def extract_syntax_example_mapping(section):
    code_blocks = extract_code_blocks(section)
    if not code_blocks:
        return None, []
    return code_blocks[0], code_blocks[1:]


# -----------------------------
# Main extraction
# -----------------------------

def extract_mappings(soup, source_url):
    results_by_term = {}

    for section in soup.find_all("section"):
        sec_id = section.get("id")
        if not sec_id:
            continue

        term = get_section_term(section)
        if not term:
            continue

        paragraphs = extract_paragraphs(section)
        lists = extract_lists(section)

        explanation, constraints = classify_sentences(paragraphs)
        syntax, examples = extract_syntax_example_mapping(section)

        entry = {
            "term": term,
            "group": term_group(term),
            "id": sec_id,
            "ids": [sec_id],
            "terms": [term],
            "syntax": syntax,
            "examples": dedupe_exact_preserve_order(examples),
            "explanation": explanation,
            "constraints": constraints,
            "allowed_elements": lists,
            "source": source_url,
            "sources": [source_url],
        }

        if term in results_by_term:
            results_by_term[term] = merge_entries(results_by_term[term], entry)
        else:
            results_by_term[term] = entry

    return list(results_by_term.values())


def merge_all_mappings(all_entries):
    merged_by_term = {}
    for entry in all_entries:
        group = entry["group"]
        if group in merged_by_term:
            merged_by_term[group] = merge_entries(merged_by_term[group], entry)
        else:
            merged_by_term[group] = entry
    return list(merged_by_term.values())


def markdown_to_html(markdown_text, title="Nextflow Syntax Mapped", full_document=True):
    try:
        import markdown as markdown_lib

        body = markdown_lib.markdown(
            markdown_text,
            extensions=["extra", "tables", "fenced_code", "sane_lists"],
            output_format="html5",
        )
    except Exception:
        body = "<pre>" + html.escape(markdown_text) + "</pre>"

    if not full_document:
        return body

    return f"""<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{html.escape(title)}</title>
    <style>
        :root {{
            color-scheme: light;
            --bg: #f8fafc;
            --panel: #ffffff;
            --text: #0f172a;
            --muted: #475569;
            --border: #dbe4ee;
            --accent: #0ea5e9;
        }}
        body {{
            margin: 0;
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(180deg, #eef6ff 0%, var(--bg) 180px);
            color: var(--text);
        }}
        .wrap {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px 16px 48px;
        }}
        .content {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
        }}
        .content img {{ max-width: 100%; height: auto; }}
        .content pre {{ overflow: auto; padding: 16px; background: #0f172a; color: #e2e8f0; border-radius: 12px; }}
        .content code {{ background: #e2e8f0; padding: 0.15rem 0.35rem; border-radius: 6px; }}
        .content pre code {{ background: transparent; padding: 0; }}
        .content table {{ border-collapse: collapse; width: 100%; }}
        .content th, .content td {{ border: 1px solid var(--border); padding: 8px 10px; vertical-align: top; }}
        .content table {{ margin: 1rem 0 1.5rem; background: #ffffff; }}
        .content thead th {{ background: #eff6ff; }}
        .content a {{ color: var(--accent); }}
        .content h2 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 2rem; }}
        .content h3 {{ margin-top: 1.4rem; }}
        .content blockquote {{ border-left: 4px solid var(--accent); margin: 1rem 0; padding: 0.5rem 1rem; background: #f8fbff; color: #334155; }}
        .content details {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; margin: 1rem 0; }}
        .content summary {{ cursor: pointer; font-weight: 600; color: #0f172a; }}
    </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"content\">
            {body}
        </div>
    </div>
</body>
</html>"""


def save_markdown_html(markdown_path, html_path=None):
    markdown_path = Path(markdown_path)
    if html_path is None:
        html_path = markdown_path.with_suffix(".html")
    html_doc = markdown_to_html(markdown_path.read_text(encoding="utf-8"), title="Nextflow Syntax Mapped")
    Path(html_path).write_text(html_doc, encoding="utf-8")


def build_summary_markdown(data):
    sorted_data = sort_entries_for_markdown(data)
    categorized_data = group_entries_by_category(sorted_data)
    counts = {category: len(entries) for category, entries in categorized_data}

    lines = []
    lines.append("# Nextflow Syntax Summary")
    lines.append("")
    lines.append("A concise, category-first overview of grouped terms with short synopses and quick lookup links.")
    lines.append("")
    lines.append(
        f"![Total Terms](https://img.shields.io/badge/Total%20Terms-{len(sorted_data)}-0f172a?style=for-the-badge) "
        f"![Categories](https://img.shields.io/badge/Categories-{len(categorized_data)}-0ea5e9?style=for-the-badge)"
    )
    lines.append("")

    lines.append("## <a id=\"summary-category-snapshot\"></a>Category Snapshot")
    lines.append("")
    lines.append("| Category | Count | Top Terms |")
    lines.append("|---|---|---|")
    for category, entries in categorized_data:
        preview_terms = ", ".join(markdown_term_label(entry["group"]) for entry in entries[:3])
        if len(entries) > 3:
            preview_terms += ", ..."
        lines.append(
            f"| [{category}](#{heading_anchor(category)}) | {counts.get(category, 0)} | {preview_terms or '-'} |"
        )
    lines.append("")

    lines.append("## <a id=\"summary-category-index\"></a>Category Index")
    lines.append("")
    for category, entries in categorized_data:
        lines.append(category_block_markdown(category, entries).rstrip())
        lines.append("")

    for category, entries in categorized_data:
        lines.append(f"## <a id=\"summary-{heading_anchor(category)}\"></a>{category}")
        lines.append("")
        lines.append("| Term | Synopsis |")
        lines.append("|---|---|")
        for entry in entries:
            synopsis = build_synopsis(entry) or "Reference term."
            term_display = markdown_term_label(entry["group"])
            synopsis_display = markdown_safe_text(synopsis)
            lines.append(f"| {term_display} | {synopsis_display} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# -----------------------------
# Output formatting
# -----------------------------

def save_json(data):
    with open("nextflow_syntax_mapped.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_markdown(data, card_layout=True):
    sorted_data = sort_entries_for_markdown(data)
    categorized_data = group_entries_by_category(sorted_data)

    with open("nextflow_syntax_mapped.md", "w", encoding="utf-8") as f:
        write_visual_header(f, sorted_data)
        write_callouts(f)

        all_sources = dedupe_urls_preserve_order(
            [source for entry in sorted_data for source in entry.get("sources", [entry.get("source", "")]) if source]
        )

        write_html_block_quote(
            f,
            "Category Index",
            ["Each category is grouped into its own block below.", "Use the jump links to move directly to a section."],
        )

        def write_category_index_body():
            for category, entries in categorized_data:
                f.write(category_block_markdown(category, entries) + "\n")

        write_collapsible_section(
            f,
            "Category Index",
            write_category_index_body,
        )

        alpha_entries = sorted(sorted_data, key=lambda entry: entry["group"].lower())
        write_collapsible_section(
            f,
            "Term Index",
            lambda: write_term_index_html_table(f, alpha_entries),
        )

        if all_sources:
            write_collapsible_section(
                f,
                "Sources",
                lambda: write_sources_html_table(f, all_sources),
            )

        for category, entries in categorized_data:
            f.write(f"## {category_marker(category)} {category}\n\n")

            for entry in entries:
                term_display = markdown_term_label(entry["group"])
                f.write(f"### <a id=\"{entry_anchor(category, entry['group'])}\"></a>{category_marker(category)} {term_display}\n\n")

                if card_layout:
                    write_entry_card_summary(f, entry, category)

                synopsis = build_synopsis(entry)
                if synopsis:
                    f.write(f"**At a glance:** {synopsis}\n\n")

                related_terms = dedupe_preserve_order(entry.get("terms", [entry["term"]]))
                if related_terms:
                    f.write("#### Related Terms\n")
                    for term in related_terms:
                        term_safe = markdown_term_label(term)
                        f.write(f"- {term_safe}\n")
                    f.write("\n")

                write_entry_details(f, entry)
                f.write("[Back to top](#nextflow-syntax-mapped-combined-sources)\n\n")
                f.write("---\n\n")


def save_summary_markdown(data):
    with open("nextflow_syntax_summary.md", "w", encoding="utf-8") as f:
        f.write(build_summary_markdown(data))


def save_summary_html(data):
    summary_markdown = build_summary_markdown(data)
    body_html = markdown_to_html(summary_markdown, title="Nextflow Syntax Summary", full_document=False)

    sidebar_links = [
        ("Summary", "#top"),
        ("Category Snapshot", "#summary-category-snapshot"),
        ("Category Index", "#summary-category-index"),
    ]
    for category in CATEGORY_DISPLAY_ORDER:
        sidebar_links.append((category, f"#summary-{heading_anchor(category)}"))

    nav_items = "\n".join(
        f'<a href="{html.escape(href)}">{html.escape(label)}</a>' for label, href in sidebar_links
    )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Nextflow Syntax Summary</title>
    <style>
        :root {{
            color-scheme: light;
            --bg: #f8fafc;
            --panel: #ffffff;
            --text: #0f172a;
            --muted: #475569;
            --border: #dbe4ee;
            --accent: #0ea5e9;
            --accent-soft: #e0f2fe;
        }}
        body {{
            margin: 0;
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(180deg, #eef6ff 0%, var(--bg) 220px);
            color: var(--text);
        }}
        .layout {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px 16px 40px;
            display: grid;
            grid-template-columns: 280px minmax(0, 1fr);
            gap: 20px;
        }}
        .sidebar {{
            position: sticky;
            top: 16px;
            align-self: start;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
        }}
        .sidebar h1 {{
            font-size: 1.25rem;
            margin: 0 0 6px;
        }}
        .sidebar p {{
            margin: 0 0 14px;
            color: var(--muted);
            line-height: 1.5;
        }}
        .searchbox {{
            width: 100%;
            box-sizing: border-box;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #fff;
            font: inherit;
            color: var(--text);
            margin-bottom: 14px;
        }}
        .nav {{ display: grid; gap: 6px; margin-bottom: 16px; }}
        .nav a {{
            display: block;
            text-decoration: none;
            color: var(--text);
            padding: 8px 10px;
            border-radius: 10px;
            border: 1px solid transparent;
        }}
        .nav a:hover {{
            background: var(--accent-soft);
            border-color: #bae6fd;
        }}
        .sidebar .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .sidebar .pill {{
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            border-radius: 999px;
            background: #eff6ff;
            color: #075985;
            font-size: 0.86rem;
        }}
        .content {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.04);
        }}
        .content img {{ max-width: 100%; height: auto; }}
        .content pre {{ overflow: auto; padding: 16px; background: #0f172a; color: #e2e8f0; border-radius: 12px; }}
        .content code {{ background: #e2e8f0; padding: 0.15rem 0.35rem; border-radius: 6px; }}
        .content pre code {{ background: transparent; padding: 0; }}
        .content table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 1.5rem; background: #ffffff; }}
        .content th, .content td {{ border: 1px solid var(--border); padding: 8px 10px; vertical-align: top; }}
        .content thead th {{ background: #eff6ff; }}
        .content a {{ color: var(--accent); }}
        .content h2 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 2rem; }}
        .content h3 {{ margin-top: 1.4rem; }}
        .content blockquote {{ border-left: 4px solid var(--accent); margin: 1rem 0; padding: 0.5rem 1rem; background: #f8fbff; color: #334155; }}
        .content details {{ background: #f8fafc; border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; margin: 1rem 0; }}
        .content summary {{ cursor: pointer; font-weight: 600; color: #0f172a; }}
        .content mark {{ background: #fde68a; color: #111827; padding: 0 2px; border-radius: 3px; }}
        .content .hidden-by-search {{ display: none !important; }}
        @media (max-width: 980px) {{
            .layout {{ grid-template-columns: 1fr; }}
            .sidebar {{ position: static; }}
        }}
    </style>
</head>
<body>
    <div class="layout" id="top">
        <aside class="sidebar">
            <h1>Syntax Summary</h1>
            <p>Category-first report with live search and quick jumps to each section.</p>
            <input id="summary-search" class="searchbox" type="search" placeholder="Search terms, synopses..." aria-label="Search summary">
            <div class="nav">{nav_items}</div>
            <div class="meta">
                <span class="pill">Markdown + HTML</span>
                <span class="pill">Live filter</span>
                <span class="pill">Sticky nav</span>
            </div>
        </aside>
        <main class="content" id="summary-content">
            {body_html}
        </main>
    </div>
    <script>
        const searchInput = document.getElementById('summary-search');
        const content = document.getElementById('summary-content');

        function normalize(text) {{
            return (text || '').toLowerCase();
        }}

        function applySearch() {{
            const query = normalize(searchInput.value).trim();
            const rows = content.querySelectorAll('table tr');
            const items = content.querySelectorAll('li');

            rows.forEach((row) => {{
                if (row.querySelector('th')) {{
                    row.classList.remove('hidden-by-search');
                    return;
                }}
                const match = !query || normalize(row.textContent).includes(query);
                row.classList.toggle('hidden-by-search', !match);
            }});

            items.forEach((item) => {{
                const match = !query || normalize(item.textContent).includes(query);
                item.classList.toggle('hidden-by-search', !match);
            }});
        }}

        searchInput.addEventListener('input', applySearch);
    </script>
</body>
</html>
"""

    Path("nextflow_syntax_summary.html").write_text(html_doc, encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and combine Nextflow reference terms into JSON and Markdown."
    )
    parser.add_argument(
        "--no-card-layout",
        action="store_true",
        help="Disable HTML summary cards in markdown output.",
    )
    return parser.parse_args()


def fetch_url_with_retry(url, max_retries=NETWORK_MAX_RETRIES, timeout=NETWORK_TIMEOUT):
    """Fetch URL with automatic retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                print(f"[ERROR] Failed to fetch {url} after {max_retries} attempts: {e}")
                raise
            print(f"[WARN] Attempt {attempt}/{max_retries} failed for {url}, retrying in {NETWORK_RETRY_DELAY}s...")
            time.sleep(NETWORK_RETRY_DELAY)


# -----------------------------
# Run
# -----------------------------

def main():
    args = parse_args()

    urls = dedupe_urls_preserve_order(URLS)
    all_mappings = []
    failed_urls = []

    for url in urls:
        try:
            print(f"[INFO] Fetching page: {url}")
            response = fetch_url_with_retry(url)
            soup = BeautifulSoup(response.text, "lxml")

            print(f"[INFO] Extracting mappings from: {url}")
            page_mappings = extract_mappings(soup, source_url=url)
            print(f"[INFO] Extracted {len(page_mappings)} entries from source")
            all_mappings.extend(page_mappings)
        except Exception as e:
            print(f"[ERROR] Failed to process {url}: {e}")
            failed_urls.append(url)
            continue

    mappings = merge_all_mappings(all_mappings)
    print(f"[INFO] Combined into {len(mappings)} grouped terms")

    save_json(mappings)
    save_markdown(mappings, card_layout=not args.no_card_layout)
    save_markdown_html("nextflow_syntax_mapped.md", "nextflow_syntax_mapped.html")
    save_summary_markdown(mappings)
    save_summary_html(mappings)

    print("[DONE] Outputs:")
    outputs = [
        "nextflow_syntax_mapped.json",
        "nextflow_syntax_mapped.md",
        "nextflow_syntax_mapped.html",
        "nextflow_syntax_summary.md",
        "nextflow_syntax_summary.html",
    ]
    for output in outputs:
        print(f" - {output}")
    
    if failed_urls:
        print(f"\n[WARNING] {len(failed_urls)} URL(s) failed to process:")
        for url in failed_urls:
            print(f"  - {url}")


if __name__ == "__main__":
    main()
    