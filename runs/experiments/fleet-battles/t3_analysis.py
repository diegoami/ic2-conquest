#!/usr/bin/env python3
"""T3 analysis from t3_trials.json: win table, the winner's army loss against the winner's ship loss, and the divisor fit
(strength = ships x condition / 10 + siegeStrength / k, random 1 + U(0, 0.3) on each side, defender's cargo counted with the same k).

    python3 runs/experiments/fleet-battles/t3_analysis.py [trials.json]
"""
import collections
import functools
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
F = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts" / "run-exp-naval-battle-cargo" / "t3_trials.json"
sys.path.insert(0, str(ROOT))
from state import sav  # noqa: E402

ART = ROOT / "artifacts" / "run-exp-naval-battle-cargo"
BASE_ATT, BASE_DEF = 441.0, 666.0      # 70 ships x 63 and 90 x 74, / 10 (the fixture's fleets: cell P of trials.py)


def cargo50(cell, army):
    """siegeStrength/50 of an army as written into the cell's fixture."""
    return sav.siege_strength(sav.load(str(ART / f"FIX_T3_{cell}.SAV"))["armies"][army]) / 50


CARGO50 = {c: cargo50(c, 7) for c in ("L5", "L10", "L15", "A5", "L25", "H15", "M15")}     # Ptolemaic army 7, morale 67
DEF50 = cargo50("L15D5", 2)                                                                 # Carthage army 2 with 5,000 light infantry (morale 65)
trials = [t for t in json.loads(F.read_text()) if "error" not in t]      # failed trials carry only an error
by = collections.defaultdict(list)
for t in trials:
    by[t["cell"]].append(t)
wins = {}
FIT = ["L5", "L10", "L15", "A5", "L25", "L15D5"]       # the six cells of the first batch; H15 and M15 repeat L15's strength and its draws
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
    if t["cell"] == "M15":      # a mixed army loses unit by unit: listed apart below
        continue
    lost = 1 - t[army[1]]["troops"] / t[army[0]]["troops"]
    rows.append((t["cell"], t["seed"], round(f, 3), round(lost, 3), t[army[1]]["morale"]))
print(len(rows), "won battles with a cargo; army loss against ship loss f:")
for lo, hi in [(0, .13), (.15, .19), (.21, .22), (.229, .23), (.233, .32)]:
    sel = [r for r in rows if lo <= r[2] <= hi]
    print(f"  f {lo}-{hi}: {len(sel)} battles, army lost {sorted(set(r[3] for r in sel))}, multiples {sorted(set(round(r[3] / r[2], 2) for r in sel if r[3] < 1))}")
print("M15 (mixed army) won battles: ship loss f and troops left of 11,000:",
      [(round(1 - t["attacker_after"]["ships"] / t["attacker_before"]["ships"], 3), t["att_army_after"]["troops"])
       for t in sorted(by["M15"], key=lambda t: t["seed"]) if t["attacker_alive"] and not t["defender_alive"]])
same = {c: [(t["seed"], t["attacker_alive"], t["attacker_after"]["ships"], t["attacker_after"]["condition"]) for t in sorted(by[c], key=lambda t: t["seed"])] for c in ("L15", "A5", "H15", "M15")}
print("L15, A5, H15, M15 identical in winner and in the winner's ships and condition for every seed:", all(v == same["L15"] for v in same.values()))
print("morale after:", sorted(collections.Counter((r[0], r[4]) for r in rows).items()))

random.seed(7)


@functools.lru_cache(maxsize=None)
def p(att, dfn, n=200000):          # cached: cells of equal strength share one value
    return sum(att * (1 + random.uniform(0, .3)) > dfn * (1 + random.uniform(0, .3)) for _ in range(n)) / n


print("divisor k: expected attacker win rates for", FIT, "and log-likelihood")
for k in (30, 35, 40, 45, 50, 60, 70):
    ll, row = 0, []
    for cell in FIT:
        w = wins[cell]
        att = round(BASE_ATT + (CARGO50.get(cell) or CARGO50["L15"]) * 50 / k, 6)
        dfn = round(BASE_DEF + (DEF50 * 50 / k if cell == "L15D5" else 0), 6)
        q = min(max(p(att, dfn), 1e-3), 1 - 1e-3)
        row.append(round(q, 2))
        n = len(by[cell])
        ll += w * math.log(q) + (n - w) * math.log(1 - q)
    print(f"  k={k}: {row}  logL {ll:.1f}")
