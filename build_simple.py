#!/usr/bin/env python3
"""
build_simple.py — Generate the simplest possible HTML catalog site.
Reads catalog.json, writes docs/index.html + docs/pages/{id}.html.
"""

import json
import html
import re
from pathlib import Path

BASE = Path(__file__).parent
CATALOG = BASE / "catalog.json"
OUT = BASE / "docs"

CATEGORIES = {
    "primary":         "Primary Sources",
    "novels":          "Novels",
    "short_stories":   "Short Stories",
    "letters":         "Letters",
    "interviews":      "Interviews",
    "scholarship":     "Scholarship",
    "biographies":     "Biographies",
    "newspaper":       "Newspaper & Press",
    "fan_publications": "Fan Publications",
    "other":           "Other",
}

STYLE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, serif; background: #f8f6f0; color: #1a1a1a; }
.layout { display: flex; min-height: 100vh; }
.sidebar { width: 220px; background: #1a1a1a; color: #ccc; padding: 1.5rem 1rem; position: sticky; top: 0; height: 100vh; overflow-y: auto; flex-shrink: 0; }
.sidebar h2 { color: #f8f6f0; font-size: 1rem; margin-bottom: 1rem; border-bottom: 1px solid #444; padding-bottom: .5rem; }
.sidebar a { display: block; color: #bbb; text-decoration: none; padding: .35rem .5rem; font-size: .85rem; border-radius: 3px; }
.sidebar a:hover, .sidebar a.active { background: #7b3f00; color: #fff; }
.sidebar .count { color: #777; font-size: .75rem; }
.main { flex: 1; padding: 2rem; max-width: 1100px; }
h1 { border-bottom: 2px solid #7b3f00; padding-bottom: .5rem; margin-bottom: .5rem; }
h1 + p { margin-bottom: 1.5rem; }
h2 { margin-top: 2rem; color: #7b3f00; scroll-margin-top: 1rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; margin-top: .75rem; }
a.card { display: block; background: #fff; border: 1px solid #d8d4c8; padding: 1rem; border-radius: 4px; text-decoration: none; color: inherit; transition: box-shadow .15s, border-color .15s; }
a.card:hover { box-shadow: 0 3px 12px rgba(0,0,0,.12); border-color: #7b3f00; }
.card h3 { margin: 0 0 .3rem; font-size: 1rem; color: #1a1a1a; }
a.card:hover h3 { color: #7b3f00; }
.card .meta { font-size: .8rem; color: #666; margin-bottom: .4rem; }
.card .summary { font-size: .85rem; color: #333; }
.back { display: inline-block; margin-bottom: 1rem; color: #7b3f00; text-decoration: none; }
.back:hover { text-decoration: underline; }
.badge { display: inline-block; background: #7b3f00; color: #fff; font-size: .7rem; padding: .1rem .4rem; border-radius: 2px; text-transform: uppercase; }
.entry-body { max-width: 700px; line-height: 1.8; }
.entry-body p { margin-bottom: 1rem; }
.footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #d8d4c8; font-size: .8rem; color: #666; }
@media (max-width: 768px) {
  .layout { flex-direction: column; }
  .sidebar { width: 100%; height: auto; position: static; display: flex; flex-wrap: wrap; gap: .25rem; padding: .75rem; }
  .sidebar h2 { width: 100%; margin-bottom: .5rem; }
  .sidebar a { display: inline-block; font-size: .75rem; padding: .25rem .5rem; }
  .main { padding: 1rem; }
  .cards { grid-template-columns: 1fr; }
}
"""

def h(text):
    return html.escape(str(text or ""), quote=True)

def summary_to_paragraphs(text):
    if not text:
        return ""
    parts = [p.strip() for p in re.split(r"\n{2,}", text.strip()) if p.strip()]
    return "\n".join(f"<p>{h(p)}</p>" for p in parts)

def build_card(entry):
    title = h(entry.get("display_title", entry["filename"]))
    author = entry.get("author", "")
    date = entry.get("date", "")
    summary = h(entry.get("card_summary", ""))
    link = f"pages/{entry['id']}.html"
    meta_parts = []
    if author and author != "Unknown":
        meta_parts.append(h(author))
    if date and date != "Unknown":
        meta_parts.append(h(date))
    meta = " &#183; ".join(meta_parts)
    return f"""<a class="card" href="{link}">
<h3>{title}</h3>
<div class="meta">{meta}</div>
<div class="summary">{summary}</div>
</a>"""

def build_sidebar(by_cat):
    links = []
    for cat_key, label in CATEGORIES.items():
        items = by_cat.get(cat_key, [])
        if not items:
            continue
        links.append(f'<a href="#{cat_key}">{h(label)} <span class="count">({len(items)})</span></a>')
    return f'<nav class="sidebar"><h2>Categories</h2>\n' + "\n".join(links) + '\n</nav>'

def build_index(entries, by_cat):
    total = len(entries)
    sections = []
    for cat_key, label in CATEGORIES.items():
        items = by_cat.get(cat_key, [])
        if not items:
            continue
        cards = "\n".join(build_card(e) for e in items)
        sections.append(f'<h2 id="{cat_key}">{h(label)} ({len(items)})</h2>\n<div class="cards">\n{cards}\n</div>')
    body = "\n".join(sections)
    sidebar = build_sidebar(by_cat)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PKD Source Database</title>
<style>{STYLE}</style></head>
<body>
<div class="layout">
{sidebar}
<div class="main">
<h1>PKD Source Database</h1>
<p><em>A research database of {total} primary and secondary sources on Philip K. Dick</em></p>
{body}
<div class="footer">PKD Source Database</div>
</div>
</div>
</body></html>"""

def build_page(entry):
    title = h(entry.get("display_title", entry["filename"]))
    author = entry.get("author", "")
    date = entry.get("date", "")
    cat = CATEGORIES.get(entry.get("category", "other"), "Other")
    body = summary_to_paragraphs(entry.get("page_summary", ""))
    meta_parts = []
    if author and author != "Unknown":
        meta_parts.append(h(author))
    if date and date != "Unknown":
        meta_parts.append(h(date))
    meta_parts.append(f'<span class="badge">{h(cat)}</span>')
    if entry.get("is_pkd_authored"):
        meta_parts.append('<strong style="color:#7b3f00">PKD-authored</strong>')
    meta = " &#183; ".join(meta_parts)
    pdf_link = ""
    if entry.get("filename"):
        pdf_link = f'<p><a href="../../PKDpdf/{h(entry["filename"])}" target="_blank">Source PDF ↗</a></p>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{STYLE}</style></head>
<body>
<a class="back" href="../index.html">← All Entries</a>
<h1>{title}</h1>
<p class="meta">{meta}</p>
<div class="entry-body">{body}</div>
{pdf_link}
<div class="footer"><a href="../index.html">← Back to catalog</a></div>
</body></html>"""

def main():
    with open(CATALOG, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    entries = [e for e in catalog if e.get("processed") and not e.get("is_duplicate") and not e.get("error")]
    entries.sort(key=lambda e: e.get("display_title", "").lower())
    print(f"{len(entries)} entries")

    by_cat = {}
    for e in entries:
        by_cat.setdefault(e.get("category", "other"), []).append(e)

    (OUT / "pages").mkdir(parents=True, exist_ok=True)

    index = build_index(entries, by_cat)
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print(f"Wrote docs/index.html")

    for e in entries:
        page = build_page(e)
        (OUT / "pages" / f"{e['id']}.html").write_text(page, encoding="utf-8")

    print(f"Wrote {len(entries)} pages in docs/pages/")
    print("Done.")

if __name__ == "__main__":
    main()
