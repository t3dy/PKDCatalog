#!/usr/bin/env python3
"""
process_pdfs.py — PKD Source Catalog
Processes PDFs using Claude Haiku (Anthropic API) to generate index card summaries.
Extracts first 5 pages of text per PDF; saves to catalog.json.
Page summaries are left null for a future deeper-read pass.

Usage:
  python process_pdfs.py              # process all unprocessed PDFs
  python process_pdfs.py --reprocess FILENAME
  python process_pdfs.py --limit N    # process only N files (for testing)
"""

import os
import sys
import json
import time
import re
import argparse
import datetime
from pathlib import Path

from dotenv import load_dotenv
import fitz  # PyMuPDF

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "PKDpdf"
CATALOG_FILE = BASE_DIR / "catalog.json"
LOG_FILE = BASE_DIR / "run.log"

PAGES_TO_READ = 5        # First N pages for quick summary
MAX_CHARS = 8_000        # ~2,000 tokens — plenty for a card summary
RATE_LIMIT_SLEEP = 2     # Seconds between API calls

MODEL = "claude-haiku-4-5-20251001"

VALID_CATEGORIES = {
    "primary", "novels", "short_stories", "letters",
    "interviews", "scholarship", "biographies",
    "newspaper", "fan_publications", "other"
}

PROMPT = """\
You are cataloging documents for a Philip K. Dick research archive. \
Analyze the text below (first few pages of the document) and return ONLY valid JSON — \
no markdown, no code fences, no explanation.

Required JSON fields:
{
  "display_title": "Clean human-readable title (not the filename)",
  "author": "Author name(s). Use 'Philip K. Dick' if PKD-authored.",
  "date": "Year or date range (e.g. '1974' or 'early 1970s'). Use 'Unknown' if unclear.",
  "category": "Exactly one of: primary|novels|short_stories|letters|interviews|scholarship|biographies|newspaper|fan_publications|other",
  "card_summary": "~100 words. Factual, archival tone. Start with the single most important fact about this document.",
  "is_pkd_authored": true or false
}

Category guide:
- primary: PKD's own non-fiction essays, speeches, Exegesis entries, philosophical writings
- novels: Full PKD novel texts
- short_stories: Short story collections or individual stories by PKD
- letters: Correspondence by or to PKD (collections or individual letters)
- interviews: Interview transcripts or recorded conversations with PKD
- scholarship: Academic papers, theses, literary criticism, analytical essays about PKD
- biographies: Book-length biographical works about PKD's life
- newspaper: Newspaper clippings, press articles, magazine articles about PKD
- fan_publications: Fanzines, fan magazines, convention program books
- other: Anything not fitting the above

Document text follows:
---
"""


# ── Logging ────────────────────────────────────────────────────────────────────
def log(event: dict):
    entry = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), **event}
    line = json.dumps(entry)
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── Catalog I/O ────────────────────────────────────────────────────────────────
def load_catalog() -> dict:
    if CATALOG_FILE.exists():
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)
        return {e["id"]: e for e in entries}
    return {}


def save_catalog(catalog: dict):
    entries = sorted(catalog.values(), key=lambda e: e.get("display_title", "").lower())
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# ── Filename utilities ──────────────────────────────────────────────────────────
def make_slug(filename: str) -> str:
    stem = Path(filename).stem
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug[:80]


def is_duplicate_filename(filename: str):
    """Detect 'foo (1).pdf' → returns (True, 'foo.pdf')."""
    match = re.match(r"^(.+?)\s+\(\d+\)(\.pdf)$", filename, re.IGNORECASE)
    if match:
        return True, match.group(1) + match.group(2)
    return False, None


# ── PDF text extraction ─────────────────────────────────────────────────────────
def extract_text(pdf_path: Path) -> tuple[str, int]:
    """Returns (text, total_page_count). Text is from first PAGES_TO_READ pages."""
    try:
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        pages = min(total_pages, PAGES_TO_READ)
        parts = []
        for i in range(pages):
            parts.append(doc[i].get_text())
        text = "\n".join(parts).strip()
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
        return text, total_pages
    except Exception as e:
        return f"[Could not extract text: {e}]", 0


# ── Claude API ─────────────────────────────────────────────────────────────────
def call_claude(client, text: str, filename: str) -> str:
    import anthropic
    message = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"{PROMPT}\nFilename hint: {filename}\n\n{text if text.strip() else '[Document appears to be a scanned image with no extractable text.]'}"
        }]
    )
    return message.content[0].text


def parse_response(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def validate_entry(data: dict) -> dict:
    required = ["display_title", "author", "date", "category",
                "card_summary", "is_pkd_authored"]
    for field in required:
        if field not in data:
            data[field] = "Unknown" if field != "is_pkd_authored" else False
    if data["category"] not in VALID_CATEGORIES:
        data["category"] = "other"
    return data


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reprocess", help="Re-process a specific filename")
    parser.add_argument("--limit", type=int, help="Process only N files (testing)")
    args = parser.parse_args()

    load_dotenv(BASE_DIR / ".env")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    log({"event": "start", "total_files": len(pdf_files), "model": MODEL})

    catalog = load_catalog()
    processed = 0
    skipped = 0
    errors = 0
    count = 0

    for pdf_path in pdf_files:
        if args.limit and count >= args.limit:
            break

        filename = pdf_path.name
        file_id = make_slug(filename)

        # Skip if already done
        if file_id in catalog and catalog[file_id].get("processed") and not args.reprocess:
            log({"event": "skip_done", "file": filename})
            skipped += 1
            continue

        if args.reprocess and args.reprocess != filename:
            skipped += 1
            continue

        # Detect duplicates
        is_dup, base_name = is_duplicate_filename(filename)
        if is_dup:
            base_id = make_slug(base_name)
            log({"event": "skip_duplicate", "file": filename, "original": base_name})
            catalog[file_id] = {
                "id": file_id, "filename": filename,
                "display_title": f"[Duplicate] {Path(filename).stem}",
                "author": "", "date": "", "category": "other",
                "card_summary": f"Duplicate of {base_name}",
                "page_summary": None,
                "is_pkd_authored": False,
                "is_duplicate": True, "duplicate_of": base_id,
                "total_pages": 0, "processed": True, "error": None,
            }
            save_catalog(catalog)
            skipped += 1
            count += 1
            continue

        # Extract text
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        t0 = time.time()
        log({"event": "process_start", "file": filename, "size_mb": round(size_mb, 2)})

        text, total_pages = extract_text(pdf_path)

        try:
            raw = call_claude(client, text, filename)
            data = parse_response(raw)
            data = validate_entry(data)

            entry = {
                "id": file_id, "filename": filename,
                **data,
                "page_summary": None,   # To be filled in a future deep-read pass
                "is_duplicate": False, "duplicate_of": None,
                "total_pages": total_pages,
                "processed": True, "error": None,
            }
            elapsed = round(time.time() - t0, 1)
            log({"event": "done", "file": filename,
                 "category": entry["category"], "elapsed_s": elapsed})
            processed += 1

        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            log({"event": "error", "file": filename, "error": str(e), "elapsed_s": elapsed})
            entry = {
                "id": file_id, "filename": filename,
                "display_title": Path(filename).stem,
                "author": "Unknown", "date": "Unknown", "category": "other",
                "card_summary": "", "page_summary": None,
                "is_pkd_authored": False,
                "is_duplicate": False, "duplicate_of": None,
                "total_pages": total_pages,
                "processed": False, "error": str(e),
            }
            errors += 1

        catalog[file_id] = entry
        save_catalog(catalog)
        count += 1
        time.sleep(RATE_LIMIT_SLEEP)

    log({"event": "complete", "processed": processed, "skipped": skipped, "errors": errors})
    print(f"\nDone. {processed} processed, {skipped} skipped, {errors} errors.")
    print(f"Results in {CATALOG_FILE}")


if __name__ == "__main__":
    main()
