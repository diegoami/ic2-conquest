#!/usr/bin/env python3
"""T3 analysis from t3_trials.json: win table, the winner's army loss against the winner's ship loss, and the divisor fit
(strength = ships x condition / 10 + siegeStrength / k, random 1 + U(0, 0.3) on each side, defender's cargo counted with the same k).

    python3 runs/experiments/fleet-battles/t3_analysis.py [trials.json]
"""
import collections
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
F = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts" / "run-exp-naval-battle-cargo" / "t3_trials.json"
CARGO50 = {"L5": 83.1, "L10": 167.5, "L15": 250.6, "A5": 250.6, "L25": 418.1}   # siegeStrength/50 of the attacker's cargo (army 7, morale 67)
DEF50 = 81.1                                                                       # Carthage army 2 with 5,000 light infantry (morale 65)
trials = json.loads(F.read_text())
by = collections.defaultdict(list)
for t in trials:
    by[t["cell"]].append(t)
wins = {}
for cell in CARGO50 | {"L15D5": 0}:
    ts = sorted(by[cell], key=lambda t: t["seed"])
    wins[cell] = sum(1 for t in ts if t["attacker_alive"] and not t["defender_alive"])
    print(f"{cell:6s} attacker wins {wins[cell]}/{len(ts)}")

rows = []
for t in trials:
    a0, a1, d0, d1 = t["attacker_before"], t["attacker_after"], t["defender_before"], t["defender_after"]
    if t["attacker_alive"] and not t["defender_alive"]:
        f, army = 1 - a1["ships"] / a0["ships"], ("att_army_before", "att_army_after")
    elif t["defender_alive"] and not t["attacker_alive"] and t["cell"] == "L15D5":
        f, army = 1 - d1["ships"] / d0["ships"], ("def_army_before", "def_army_after")
    else:
        continue
    lost = 1 - t[army[1]]["troops"] / t[army[0]]["troops"]
    rows.append((t["cell"], t["seed"], round(f, 3), round(lost, 3), t[army[1]]["morale"]))
print(len(rows), "won battles with a cargo; army loss against ship loss f:")
for lo, hi in [(0, .13), (.15, .19), (.21, .22), (.229, .23), (.233, .32)]:
    sel = [r for r in rows if lo <= r[2] <= hi]
    print(f"  f {lo}-{hi}: {len(sel)} battles, army lost {sorted(set(r[3] for r in sel))}, multiples {sorted(set(round(r[3] / r[2], 2) for r in sel if r[3] < 1))}")
print("morale after:", sorted(collections.Counter((r[0], r[4]) for r in rows).items()))

random.seed(7)


def p(att, dfn, n=40000):
    return sum(att * (1 + random.uniform(0, .3)) > dfn * (1 + random.uniform(0, .3)) for _ in range(n)) / n


print("divisor k: expected attacker win rates for", list(wins), "and log-likelihood")
for k in (30, 35, 40, 45, 50, 60, 70):
    ll, row = 0, []
    for cell, w in wins.items():
        att = 441 + (CARGO50.get(cell) or CARGO50["L15"]) * 50 / k
        dfn = 666 + (DEF50 * 50 / k if cell == "L15D5" else 0)
        q = min(max(p(att, dfn), 1e-3), 1 - 1e-3)
        row.append(round(q, 2))
        ll += w * math.log(q) + (10 - w) * math.log(1 - q)
    print(f"  k={k}: {row}  logL {ll:.1f}")
