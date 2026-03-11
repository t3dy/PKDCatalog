#!/usr/bin/env python3
"""
build_site.py — PKD Source Catalog
Reads catalog.json and generates a static HTML website.

Output structure:
  catalog/
    index.html              — all entries, card grid
    style.css               — shared stylesheet
    categories/
      {category}.html       — one page per category
    pages/
      {id}.html             — full entry detail page
"""

import json
import re
import html
from pathlib import Path

BASE_DIR = Path(__file__).parent
CATALOG_FILE = BASE_DIR / "catalog.json"
OUT_DIR = BASE_DIR / "catalog"

SITE_TITLE = "PKD Source Database"
SITE_SUBTITLE = "A research database of primary and secondary sources on Philip K. Dick"

CATEGORY_META = {
    "primary":        {"label": "Primary Sources",       "color": "#7b3f00"},
    "novels":         {"label": "Novels",                "color": "#1a3a5c"},
    "short_stories":  {"label": "Short Stories",         "color": "#2d5a1b"},
    "letters":        {"label": "Letters",               "color": "#4a2060"},
    "interviews":     {"label": "Interviews",            "color": "#5a3010"},
    "scholarship":    {"label": "Scholarship",           "color": "#1a4a4a"},
    "biographies":    {"label": "Biographies",           "color": "#3d3d00"},
    "newspaper":      {"label": "Newspaper & Press",     "color": "#3d1010"},
    "fan_publications":{"label": "Fan Publications",     "color": "#1a3a1a"},
    "other":          {"label": "Other",                 "color": "#3d3d3d"},
}


# ── Utilities ──────────────────────────────────────────────────────────────────
def h(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text), quote=True)


def load_catalog() -> list[dict]:
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def entry_slug(entry: dict) -> str:
    return entry["id"]


def pdf_path_relative(entry: dict, depth: int = 1) -> str:
    """Relative path from a page at `depth` levels deep to the PDF file."""
    prefix = "../" * depth
    return f"{prefix}../PKDpdf/{entry['filename']}"


def category_label(cat: str) -> str:
    return CATEGORY_META.get(cat, {}).get("label", cat.replace("_", " ").title())


def category_color(cat: str) -> str:
    return CATEGORY_META.get(cat, {}).get("color", "#555")


def category_page_path(cat: str, from_depth: int = 1) -> str:
    prefix = "../" * from_depth
    return f"{prefix}categories/{cat}.html"


def entry_page_path(entry: dict, from_depth: int = 0) -> str:
    prefix = "../" * from_depth
    return f"{prefix}pages/{entry_slug(entry)}.html"


# ── CSS ─────────────────────────────────────────────────────────────────────────
CSS = """\
/* PKD Source Database — stylesheet */
:root {
  --bg: #f8f6f0;
  --surface: #ffffff;
  --ink: #1a1a1a;
  --ink-light: #555;
  --border: #d8d4c8;
  --accent: #7b3f00;
  --gap: 1.5rem;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--ink);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1rem;
  line-height: 1.65;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Header ── */
.site-header {
  background: var(--ink);
  color: #f8f6f0;
  padding: 2rem var(--gap);
}
.site-header h1 { font-size: 1.8rem; font-weight: normal; letter-spacing: 0.03em; }
.site-header p { margin-top: 0.4rem; color: #bbb; font-size: 0.9rem; font-style: italic; }

/* ── Category nav ── */
.cat-nav {
  background: #2a2a2a;
  padding: 0.5rem var(--gap);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.cat-nav a {
  color: #ccc;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.8rem;
  padding: 0.25rem 0.6rem;
  border-radius: 2px;
  border: 1px solid #555;
  transition: background 0.15s, color 0.15s;
}
.cat-nav a:hover, .cat-nav a.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  text-decoration: none;
}

/* ── Main layout ── */
main { max-width: 1200px; margin: 0 auto; padding: var(--gap); }

.section-heading {
  font-size: 1.3rem;
  font-weight: normal;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.4rem;
  margin: 2rem 0 1rem;
  color: var(--ink);
}
.section-count {
  font-size: 0.85rem;
  color: var(--ink-light);
  margin-left: 0.5rem;
}

/* ── Card grid ── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--gap);
}

/* ── Card ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: box-shadow 0.15s;
}
.card:hover { box-shadow: 0 3px 12px rgba(0,0,0,0.1); }

.card-title {
  font-size: 1rem;
  font-weight: bold;
  line-height: 1.3;
}
.card-title a { color: var(--ink); }
.card-title a:hover { color: var(--accent); text-decoration: none; }

.card-meta {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.8rem;
  color: var(--ink-light);
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 2px;
  font-size: 0.75rem;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #fff;
  text-transform: uppercase;
}
.badge:hover { opacity: 0.85; text-decoration: none; }

.card-summary {
  font-size: 0.88rem;
  color: #333;
  flex: 1;
  margin-top: 0.3rem;
}

.card-footer {
  margin-top: 0.5rem;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.82rem;
}
.card-footer a { color: var(--accent); }

/* ── Entry detail page ── */
.entry-header {
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
.entry-header h1 { font-size: 1.6rem; font-weight: normal; line-height: 1.3; }
.entry-meta {
  margin-top: 0.6rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.85rem;
  color: var(--ink-light);
}
.entry-body {
  max-width: 720px;
  line-height: 1.8;
}
.entry-body p { margin-bottom: 1rem; }

.entry-footer {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.85rem;
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

/* ── Category index page ── */
.page-heading {
  font-size: 1.5rem;
  font-weight: normal;
  margin-bottom: 0.3rem;
}
.page-subheading {
  color: var(--ink-light);
  font-size: 0.9rem;
  font-style: italic;
  margin-bottom: 1.5rem;
}

/* ── Breadcrumb ── */
.breadcrumb {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.82rem;
  color: var(--ink-light);
  margin-bottom: 1.5rem;
}
.breadcrumb a { color: var(--ink-light); }
.breadcrumb a:hover { color: var(--accent); }

/* ── Footer ── */
.site-footer {
  border-top: 1px solid var(--border);
  padding: 1.5rem var(--gap);
  text-align: center;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  font-size: 0.8rem;
  color: var(--ink-light);
  margin-top: 3rem;
}

@media (max-width: 600px) {
  .card-grid { grid-template-columns: 1fr; }
  .cat-nav { gap: 0.3rem; }
}
"""


# ── HTML fragments ──────────────────────────────────────────────────────────────
def page_head(title: str, depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{h(title)} — {h(SITE_TITLE)}</title>
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>"""


def site_header(depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""
<header class="site-header">
  <h1><a href="{prefix}index.html" style="color:inherit;text-decoration:none">{h(SITE_TITLE)}</a></h1>
  <p>{h(SITE_SUBTITLE)}</p>
</header>"""


def cat_nav(active_cat: str = "", depth: int = 0) -> str:
    links = [f'<a href="{"../" * depth}index.html"{"class=\"active\"" if active_cat == "__all__" else ""}>All</a>']
    for cat, meta in CATEGORY_META.items():
        active = ' class="active"' if cat == active_cat else ""
        links.append(
            f'<a href="{"../" * depth}categories/{cat}.html"{active}>{h(meta["label"])}</a>'
        )
    return '<nav class="cat-nav">' + "\n".join(links) + "</nav>"


def badge_html(cat: str, depth: int = 0) -> str:
    label = category_label(cat)
    color = category_color(cat)
    link = category_page_path(cat, from_depth=depth)
    return (f'<a class="badge" href="{link}" '
            f'style="background:{color}" title="Browse {label}">{h(label)}</a>')


def render_card(entry: dict, depth: int = 0) -> str:
    title = h(entry.get("display_title", entry["filename"]))
    author = h(entry.get("author", ""))
    date = h(entry.get("date", ""))
    cat = entry.get("category", "other")
    summary = h(entry.get("card_summary", ""))
    page_link = entry_page_path(entry, from_depth=depth)

    meta_parts = []
    if author:
        meta_parts.append(f'<span>{author}</span>')
    if date and date != "Unknown":
        meta_parts.append(f'<span>{date}</span>')
    meta_parts.append(badge_html(cat, depth=depth))

    return f"""
<article class="card">
  <div class="card-title"><a href="{page_link}">{title}</a></div>
  <div class="card-meta">{"".join(meta_parts)}</div>
  <div class="card-summary">{summary}</div>
  <div class="card-footer"><a href="{page_link}">View Entry →</a></div>
</article>"""


def site_footer() -> str:
    return """
<footer class="site-footer">
  PKD Source Database — research archive
</footer>
</body>
</html>"""


# ── Page generators ─────────────────────────────────────────────────────────────
def build_index(entries: list[dict], by_category: dict):
    lines = [page_head(SITE_TITLE, depth=0), site_header(depth=0), cat_nav("__all__", depth=0), "<main>"]

    total = len([e for e in entries if not e.get("is_duplicate") and e.get("processed")])
    lines.append(f'<p style="color:#666;font-family:sans-serif;font-size:.85rem;margin-bottom:1rem">'
                 f'{total} entries across {len(by_category)} categories</p>')

    for cat, cat_entries in sorted(by_category.items(), key=lambda x: category_label(x[0])):
        meta = CATEGORY_META.get(cat, {})
        label = meta.get("label", cat)
        color = category_color(cat)
        count = len(cat_entries)
        cat_link = f"categories/{cat}.html"
        lines.append(
            f'<h2 class="section-heading" id="{cat}">'
            f'<a href="{cat_link}" style="color:inherit">{h(label)}</a>'
            f'<span class="section-count">({count})</span>'
            f'</h2>'
        )
        lines.append('<div class="card-grid">')
        for entry in cat_entries:
            lines.append(render_card(entry, depth=0))
        lines.append("</div>")

    lines.append("</main>")
    lines.append(site_footer())
    return "\n".join(lines)


def build_category_page(cat: str, cat_entries: list[dict]) -> str:
    label = category_label(cat)
    lines = [
        page_head(label, depth=1),
        site_header(depth=1),
        cat_nav(cat, depth=1),
        "<main>",
        f'<p class="breadcrumb"><a href="../index.html">All Entries</a> › {h(label)}</p>',
        f'<h1 class="page-heading">{h(label)}</h1>',
        f'<p class="page-subheading">{len(cat_entries)} entries</p>',
        '<div class="card-grid">',
    ]
    for entry in cat_entries:
        lines.append(render_card(entry, depth=1))
    lines.append("</div>")
    lines.append("</main>")
    lines.append(site_footer())
    return "\n".join(lines)


def build_entry_page(entry: dict) -> str:
    title = entry.get("display_title", entry["filename"])
    author = entry.get("author", "")
    date = entry.get("date", "")
    cat = entry.get("category", "other")
    page_summary = entry.get("page_summary") or ""
    filename = entry.get("filename", "")

    # Format page summary into paragraphs
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", page_summary.strip()) if p.strip()]
    if not paragraphs and page_summary:
        paragraphs = [page_summary]
    body_html = "\n".join(f"<p>{h(p)}</p>" for p in paragraphs)

    meta_parts = []
    if author:
        meta_parts.append(f'<span>{h(author)}</span>')
    if date and date != "Unknown":
        meta_parts.append(f'<span>{h(date)}</span>')
    meta_parts.append(badge_html(cat, depth=1))
    if entry.get("is_pkd_authored"):
        meta_parts.append('<span style="color:#7b3f00;font-weight:bold">PKD-authored</span>')

    lines = [
        page_head(title, depth=1),
        site_header(depth=1),
        cat_nav(cat, depth=1),
        "<main>",
        f'<p class="breadcrumb"><a href="../index.html">All Entries</a> › '
        f'<a href="../categories/{cat}.html">{h(category_label(cat))}</a> › {h(title)}</p>',
        '<div class="entry-header">',
        f'<h1>{h(title)}</h1>',
        f'<div class="entry-meta">{"".join(meta_parts)}</div>',
        "</div>",
        f'<div class="entry-body">{body_html}</div>',
        '<div class="entry-footer">',
        f'<a href="../index.html">← All Entries</a>',
        f'<a href="../categories/{cat}.html">More {h(category_label(cat))}</a>',
    ]

    if filename:
        lines.append(f'<a href="../../PKDpdf/{h(filename)}" target="_blank">Source Document ↗</a>')

    lines.append("</div>")
    lines.append("</main>")
    lines.append(site_footer())
    return "\n".join(lines)


def build_readme(total: int, by_category: dict) -> str:
    cat_lines = "\n".join(
        f"- **{category_label(c)}**: {len(entries)} entries"
        for c, entries in sorted(by_category.items(), key=lambda x: category_label(x[0]))
    )
    return f"""# PKD Source Database

{SITE_SUBTITLE}.

## Contents

{total} entries across {len(by_category)} categories:

{cat_lines}

## About

This database catalogs primary and secondary sources relating to the life and work of Philip K. Dick. Entries include novels, short stories, letters, interviews, scholarly works, biographical writing, newspaper coverage, and fan publications.

Summaries were generated with the assistance of Google Gemini AI.
"""


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"Reading {CATALOG_FILE}...")
    all_entries = load_catalog()

    # Filter: only successfully processed, non-duplicate entries for main display
    entries = [
        e for e in all_entries
        if e.get("processed") and not e.get("is_duplicate") and not e.get("error")
    ]

    print(f"  {len(entries)} valid entries ({len(all_entries)} total in catalog)")

    # Group by category
    by_category: dict[str, list] = {}
    for entry in sorted(entries, key=lambda e: e.get("display_title", "").lower()):
        cat = entry.get("category", "other")
        by_category.setdefault(cat, []).append(entry)

    # Create output directories
    (OUT_DIR / "pages").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "categories").mkdir(parents=True, exist_ok=True)

    # Write CSS
    css_path = OUT_DIR / "style.css"
    css_path.write_text(CSS, encoding="utf-8")
    print(f"  Wrote {css_path}")

    # Write index
    index_html = build_index(entries, by_category)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"  Wrote {OUT_DIR / 'index.html'}")

    # Write category pages
    for cat, cat_entries in by_category.items():
        cat_html = build_category_page(cat, cat_entries)
        cat_file = OUT_DIR / "categories" / f"{cat}.html"
        cat_file.write_text(cat_html, encoding="utf-8")
        print(f"  Wrote {cat_file} ({len(cat_entries)} entries)")

    # Write entry pages
    written = 0
    for entry in entries:
        entry_html = build_entry_page(entry)
        entry_file = OUT_DIR / "pages" / f"{entry_slug(entry)}.html"
        entry_file.write_text(entry_html, encoding="utf-8")
        written += 1

    print(f"  Wrote {written} entry pages in {OUT_DIR / 'pages'}")

    # Write README
    readme = build_readme(len(entries), by_category)
    (BASE_DIR / "README.md").write_text(readme, encoding="utf-8")
    print(f"  Wrote README.md")

    print(f"\nDone. Open {OUT_DIR / 'index.html'} in a browser to preview.")


if __name__ == "__main__":
    main()
