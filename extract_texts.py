#!/usr/bin/env python3
"""
extract_texts.py — PKD Source Catalog
Extracts first PAGES_TO_READ pages of text from every PDF in PKDpdf/
and saves results to texts.json for LLM-based cataloging.

Usage: python extract_texts.py
"""

import json
import re
import datetime
from pathlib import Path

import fitz  # PyMuPDF

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "PKDpdf"
OUT_FILE = BASE_DIR / "texts.json"

PAGES_TO_READ = 5
MAX_CHARS = 6_000   # Per document

DUPLICATE_RE = re.compile(r"^(.+?)\s+\(\d+\)(\.pdf)$", re.IGNORECASE)


def make_slug(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")[:80]


def is_duplicate(filename: str):
    m = DUPLICATE_RE.match(filename)
    if m:
        return True, m.group(1) + m.group(2)
    return False, None


def extract(pdf_path: Path):
    try:
        doc = fitz.open(str(pdf_path))
        total = len(doc)
        pages = min(total, PAGES_TO_READ)
        text = "\n".join(doc[i].get_text() for i in range(pages)).strip()
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
        return text, total
    except Exception as e:
        return f"[Extract error: {e}]", 0


def main():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs")

    results = []
    for pdf_path in pdfs:
        fn = pdf_path.name
        slug = make_slug(fn)
        size_mb = round(pdf_path.stat().st_size / 1_048_576, 2)
        dup, base = is_duplicate(fn)

        if dup:
            results.append({
                "id": slug, "filename": fn, "size_mb": size_mb,
                "is_duplicate": True, "duplicate_of": make_slug(base),
                "total_pages": 0, "text": None
            })
            print(f"  DUP  {fn}")
            continue

        text, total = extract(pdf_path)
        has_text = bool(text and not text.startswith("["))
        results.append({
            "id": slug, "filename": fn, "size_mb": size_mb,
            "is_duplicate": False, "duplicate_of": None,
            "total_pages": total,
            "text": text if has_text else None,
            "scanned": not has_text,
        })
        print(f"  {'TEXT' if has_text else 'SCAN'} {fn} ({total}pp, {size_mb}MB)")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    text_count = sum(1 for r in results if r.get("text"))
    dup_count = sum(1 for r in results if r.get("is_duplicate"))
    scan_count = sum(1 for r in results if r.get("scanned"))
    print(f"\nDone: {text_count} with text, {scan_count} scanned/image, {dup_count} duplicates")
    print(f"Saved to {OUT_FILE}")


if __name__ == "__main__":
    main()
