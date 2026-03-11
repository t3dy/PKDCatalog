# PKD Source Database

A research database of primary and secondary sources on Philip K. Dick.

**[Browse the catalog](https://t3dy.github.io/PKDCatalog/)**

## Contents

166 entries across 10 categories:

| Category | Count |
|----------|-------|
| Biographies | 7 |
| Fan Publications | 19 |
| Interviews | 3 |
| Letters | 11 |
| Newspaper & Press | 45 |
| Novels | 4 |
| Other | 11 |
| Primary Sources | 15 |
| Scholarship | 35 |
| Short Stories | 16 |

## Data Pipeline

This catalog was built using a PDF-to-static-site pipeline orchestrated by Claude Code. The process:

### 1. PDF Text Extraction
`extract_texts.py` uses PyMuPDF to extract the first 5 pages (up to 6,000 characters) from each PDF in the collection. Output: `texts.json` with id, filename, page count, extracted text, and duplicate detection.

### 2. Batch Processing
The extracted texts were split into batches of ~17 items (`summary_batch_0.json` through `summary_batch_7.json`). Each batch was processed in the main Claude Code conversation to generate catalog metadata:
- `display_title` — human-readable title
- `author`, `date` — attribution and dating
- `category` — one of 10 taxonomy categories
- `card_summary` — 2-3 sentence summary for the card grid
- `page_summary` — 3-4 paragraph detailed summary for the entry detail page

Results were written to `summary_result_0.json` through `summary_result_7.json` using a checkpoint pattern (each batch saved immediately after generation to prevent data loss).

### 3. New PDF Integration
Additional PDFs were processed by extracting text to `new_texts.json`, generating full catalog entries (both card and page summaries) to `new_entries.json`, then merging into the master catalog.

### 4. Catalog Merge
All summary results were merged into `catalog.json`, the master catalog file containing all 174 entries (166 unique + 8 duplicates).

### 5. Site Generation
`build_simple.py` reads `catalog.json` and generates a static HTML site:
- `docs/index.html` — card grid grouped by category
- `docs/pages/{id}.html` — detail page per entry with full page summary
- Minimal inline CSS, no JavaScript, no external dependencies

## Key Files

| File | Purpose |
|------|---------|
| `extract_texts.py` | Extract text from PDFs using PyMuPDF |
| `build_simple.py` | Generate static HTML site from catalog.json |
| `catalog.json` | Master catalog (174 entries) |
| `texts.json` | Extracted text excerpts |
| `docs/` | Static website (GitHub Pages) |

## About

This database catalogs primary and secondary sources relating to the life and work of Philip K. Dick. Entries include novels, short stories, letters, interviews, scholarly works, biographical writing, newspaper coverage, and fan publications.

Catalog entries and summaries were generated with the assistance of Claude (Anthropic).
