#!/usr/bin/env python3
"""
generate_summaries.py — Generates page summaries for catalog entries.
Reads summary_batch_*.json, writes summary_result_*.json.
Run one batch at a time: python generate_summaries.py 0
"""
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

def write_result(batch_num: int, summaries: list[dict]):
    out = BASE_DIR / f"summary_result_{batch_num}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(summaries)} summaries to {out}")

if __name__ == "__main__":
    batch_num = int(sys.argv[1])
    # Read from stdin as JSON
    summaries = json.load(sys.stdin)
    write_result(batch_num, summaries)
