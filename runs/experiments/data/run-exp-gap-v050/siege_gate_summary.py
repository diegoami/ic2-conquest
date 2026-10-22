"""Summarise siege_gate_s<seed>.jsonl (siege_probe): per seed, the AI army / at-war city pairs (army-turns, End turns 11-80), how many
are legal, and how many pass the remake's gate (ratio >= the nation's RequiredAttackRatioPermille) with the real fortification and with the
fortification frozen at turn 10; the required ratios seen; the ratio quartiles; and how many legal pairs reach 909 permille, the
strength/defence ratio at which the original's cityScore (strength x 110 / cityDefense, distance added back) reaches 100 (an analogy:
the two engines' strength and defence formulas are not compared here). Writes siege_gate_summary.json (versioned). python3 siege_gate_summary.py"""
import json, statistics
from collections import Counter
from pathlib import Path
D = Path(__file__).resolve().parent
out = {}
for p in sorted(D.glob("siege_gate_s*.jsonl")):
    R = [json.loads(l) for l in p.read_text().splitlines()]
    L = [r for r in R if r["legal"]]
    q = lambda xs: [round(x) for x in statistics.quantiles(xs, n=4)] if len(xs) >= 4 else xs
    out[p.stem.replace("siege_gate_", "")] = {
        "pairs": len(R), "legal": len(L), "pass_real": sum(r["pass_real"] for r in L), "pass_frozen": sum(r["pass_frozen"] for r in L),
        "fort_rose_since_t10": sum(r["fort"] % 100 > r["fort_t10"] % 100 for r in L),
        "required_seen": dict(Counter(r["required"] for r in L)), "ratio_real_quartiles": q([r["ratio_real"] for r in L]),
        "ratio_frozen_quartiles": q([r["ratio_frozen"] for r in L]), "ratio_max": max((r["ratio_real"] for r in L), default=None),
        "legal_ge_909_real": sum(r["ratio_real"] >= 909 for r in L)}
p = D / "siege_gate_summary.json"; k = 1
while p.exists(): k += 1; p = D / f"siege_gate_summary.v{k}.json"
p.write_text(json.dumps(out, indent=1)); print(p.name)
for k, v in out.items(): print(k, v)
