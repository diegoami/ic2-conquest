#!/usr/bin/env python3
"""Table of the G7 runs (Rome's start at New Game per seed) from the g1_checks-G7_<seed>-*.jsonl logs; the latest complete log of each seed.
Writes g7_summary.md (next free version)."""
import json, sys
from pathlib import Path
D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from versioned import write_new
rows = {}
for p in sorted(D.glob("g1_checks-G7-*.jsonl")):
    for l in p.read_text().splitlines():
        r = json.loads(l)
        if r.get("step") == "rome_start": rows[r["seed"]] = (p.name, r)
out = ["| seed | log | Illyria | Macedonia | Gaul | trade partners | Trade (OCR) | Regular units (OCR / memory) | Army recruit | Expenditure total |", "|---|---|---|---|---|---|---|---|---|---|"]
for s in sorted(rows):
    n, r = rows[s]
    out.append(f"| {s} | {n} | {r['illyria']} | {r['macedonia']} | {r['gaul']} | {', '.join(r['trade_partners']) or '-'} | {r['trade_income_ocr']} | {r['regular_units_ocr']} / {r['regular_units_memory']} | {r['army_recruit_ocr']} | {r['expenditure_total_ocr']} |")
print("\n".join(out)); print(write_new(D / "g7_summary.md", "\n".join(out) + "\n"))
