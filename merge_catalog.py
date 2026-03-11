#!/usr/bin/env python3
"""Merge batch_result_*.json files into catalog.json"""
import json
import glob
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUT_FILE = BASE_DIR / "catalog.json"

entries = []
for f in sorted(glob.glob(str(BASE_DIR / "batch_result_*.json"))):
    with open(f, encoding="utf-8") as fh:
        data = json.load(fh)
    entries.extend(data)
    print(f"  Loaded {len(data)} entries from {f}")

entries.sort(key=lambda e: e.get("display_title", "").lower())

with open(OUT_FILE, "w", encoding="utf-8") as fh:
    json.dump(entries, fh, indent=2, ensure_ascii=False)

cats = {}
for e in entries:
    c = e.get("category", "other")
    cats[c] = cats.get(c, 0) + 1

print(f"\nTotal: {len(entries)} entries")
for c, n in sorted(cats.items()):
    print(f"  {c}: {n}")
print(f"Written to {OUT_FILE}")
