#!/usr/bin/env python3
"""Check 7 (review fix R1/R2): the army-damage rule of FUN_0044b4f8 -> FUN_0044ae20 -> FUN_0044ac3c as a model, enumerated exactly (no sampling), for the
army of FIX_T4_R85sA.SAV (units li 4000, hi 3000, ar 2000, lc 1000, hc 1000 in slots 0-4, label 0) at d = 86 (the storm of cell R85sA). Lines cited are
those of the pinned all_app_functions.txt, see code_extract_g2.txt.

Model (every step names its lines):
 1. FUN_0044ae20 49584-49591: each of 20 slots: troops -= (troops / (rand(15) + 105)) * d   (integer division, rand(15) = 0..14 uniform)
 2. FUN_0044ae20 49592-49603: slots 19 down to 0: a unit with 0 < troops < limit/10 (label 0) is removed (FUN_0044ac3c: the last occupied slot is copied over it)
 3. FUN_0044b4f8 49865-49877 (d > 70): n = FUN_0044a66c (last occupied slot + 1); n*d/250 + 1 times: remove slot rand(FUN_0044a66c) (recomputed each time)
Not modelled: the game's own random number generator (a uniform draw stands in), the army-gone handling of FUN_0044ab90, the units' labels (all 0).
Writes c7_storm_model.txt beside this script (next free version, rule 6)."""
import sys, itertools
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from versioned import write_new

D = 86
LIM = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}   # size limits read from game memory at 0x478fca (finding C5c)
UNITS = (("li", 4000), ("hi", 3000), ("ar", 2000), ("lc", 1000), ("hc", 1000))


def span(sl):
    idx = [i for i, s in enumerate(sl) if s[1] > 0]
    return (idx[-1] + 1) if idx else 0


def remove(sl, i):
    n = span(sl)
    if n == 0:
        return sl
    sl = list(sl); sl[i] = sl[n - 1]
    if n - 1 != i: sl[n - 1] = (sl[n - 1][0], 0)
    else: sl[i] = (sl[i][0], 0)
    return tuple(sl)


@lru_cache(maxsize=None)
def removals(sl, k):
    """distribution {final unit tuple: probability} after k random removals"""
    if k == 0:
        return {tuple(s for s in sl if s[1] > 0): Fraction(1)}
    n = span(sl)
    if n == 0:
        return {(): Fraction(1)}
    out = {}
    for i in range(n):
        for key, p in removals(remove(sl, i), k - 1).items():
            out[key] = out.get(key, 0) + p / n
    return out


def after_step2(rolls):
    sl = tuple((t, tr - (tr // (r + 105)) * D) for (t, tr), r in zip(UNITS, rolls))
    for i in range(19, -1, -1):
        if i < len(sl) and 0 < sl[i][1] < LIM[sl[i][0]] // 10:
            sl = remove(sl, i)
    return sl


dist = {}; step2 = {}
for rolls in itertools.product(range(15), repeat=len(UNITS)):
    sl = after_step2(rolls)
    step2[sl] = step2.get(sl, 0) + 1
total = 15 ** len(UNITS)
for sl, c in step2.items():
    n = span(sl); k = n * D // 250 + 1 if n and D > 70 else 0
    for key, p in removals(sl, k).items():
        dist[key] = dist.get(key, 0) + Fraction(c, total) * p
kinds = {}
for key, p in dist.items():
    name = "+".join(t for t, _ in key) or "gone"
    kinds[name] = kinds.get(name, 0) + p
lines = [f"d = {D}; army of FIX_T4_R85sA.SAV; exact enumeration of {total} roll combinations",
         "units surviving step 2 (before the random removals), by roll combination count: %d distinct states" % len(step2)]
lines.append("always removed in step 2 (below limit/10 at every roll): " + ", ".join(
    t for i, (t, tr) in enumerate(UNITS)
    if all(tr - (tr // (r + 105)) * D < LIM[t] // 10 for r in range(15))))
lines.append("never removed in step 2: " + ", ".join(
    t for i, (t, tr) in enumerate(UNITS)
    if all(tr - (tr // (r + 105)) * D >= LIM[t] // 10 for r in range(15))))
lines.append("probability of the final army by unit type kept:")
for name, p in sorted(kinds.items(), key=lambda kv: -kv[1]):
    lines.append(f"  {name:8s} {float(p):.4f}  ({p})")
lines.append("final single-unit troops range by type: " + str({
    name: (min(s[0][1] for s in dist if len(s) == 1 and s[0][0] == name), max(s[0][1] for s in dist if len(s) == 1 and s[0][0] == name))
    for name in {s[0][0] for s in dist if len(s) == 1}}))
print("\n".join(lines))
print(write_new(Path(__file__).resolve().parent / "c7_storm_model.txt", "\n".join(lines) + "\n"))
