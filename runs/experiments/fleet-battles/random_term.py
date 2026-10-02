#!/usr/bin/env python3
"""What decides a naval battle besides strength? Fit models of the random term to the trials.

Model: the attacker's strength A is multiplied by k * (1 + U(0, wa)) and the defender's D by (1 + U(0, wd)); the attacker wins when its
product is larger. Free parameters: wa, wd (widths of the random terms) and k (an attacker factor). The research formula, read literally,
is wa = wd = 0.3, k = 1 ("plus a random 0-30 %"). For every cell the probability that the attacker wins is computed exactly on a fine
grid and the binomial log-likelihood of the observed wins is summed over cells; models are compared by log-likelihood and AIC.

    python3 runs/experiments/fleet-battles/random_term.py
"""
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
trials = json.loads((ROOT / "artifacts" / "run-exp-naval-battle" / "trials.json").read_text())
cells = defaultdict(lambda: {"n": 0, "w": 0, "ratio": None})
for t in trials:
    if "error" in t:
        continue
    c = cells[t["cell"]]
    c["n"] += 1
    c["w"] += 1 if (t["attacker_alive"] and not t["defender_alive"]) else 0
    a, d = t["strength"]
    c["ratio"] = a / d
N = 240


def p_attacker(ratio, wa, wd, k):
    """P(k * ratio * (1 + ua) > 1 + ud), ua ~ U(0, wa), ud ~ U(0, wd): exact in ud, a midpoint grid in ua (a width of 0 is a point)."""
    uas = [wa * (i + 0.5) / N for i in range(N)] if wa > 0 else [0.0]
    total = 0.0
    for ua in uas:
        a = k * ratio * (1 + ua)
        if wd > 0:
            total += min(1.0, max(0.0, (a - 1) / wd))        # P(1 + ud < a)
        else:
            total += 1.0 if a > 1 else 0.0
    return total / len(uas)


def loglik(wa, wd, k):
    ll = 0.0
    for name, c in cells.items():
        p = min(max(p_attacker(c["ratio"], wa, wd, k), 1e-6), 1 - 1e-6)
        ll += c["w"] * math.log(p) + (c["n"] - c["w"]) * math.log(1 - p)
    return ll


def best(grid_wa, grid_wd, grid_k):
    top = None
    for wa, wd, k in itertools.product(grid_wa, grid_wd, grid_k):
        ll = loglik(wa, wd, k)
        if top is None or ll > top[0]:
            top = (ll, wa, wd, k)
    return top


w_grid = [0.0, 0.02, 0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
k_grid = [0.9, 0.95, 0.98, 1.0, 1.02, 1.05, 1.08, 1.1, 1.15, 1.2]
print("cells (ratio = attacker strength / defender strength):")
for name, c in sorted(cells.items(), key=lambda kv: kv[1]["ratio"]):
    print(f"  {name:4s} ratio {c['ratio']:.3f}  attacker wins {c['w']:2d}/{c['n']:2d} = {c['w'] / c['n']:.2f}   "
          f"literal model (0.3, 0.3, 1.0) predicts {p_attacker(c['ratio'], .3, .3, 1.0):.2f}")
models = [
    ("H1 literal: wa = wd = 0.3, k = 1", [0.3], [0.3], [1.0], 0),
    ("H2 attacker-only term: wa = 0.3, wd = 0, k = 1", [0.3], [0.0], [1.0], 0),
    ("H3 equal free width, k = 1", w_grid, None, [1.0], 1),
    ("H4 free wa and wd, k = 1", w_grid, w_grid, [1.0], 2),
    ("H5 wa = wd = 0.3, free attacker factor k", [0.3], [0.3], k_grid, 1),
    ("H6 all free (wa, wd, k)", w_grid, w_grid, k_grid, 3),
]
print()
print(f"{'model':52s} {'params':>6s} {'logL':>9s} {'AIC':>8s}   best parameters")
for name, ga, gd, gk, npar in models:
    if gd is None:
        top = max(((loglik(w, w, 1.0), w, w, 1.0) for w in ga), key=lambda x: x[0])
    else:
        top = best(ga, gd, gk)
    print(f"{name:52s} {npar:6d} {top[0]:9.2f} {2 * npar - 2 * top[0]:8.2f}   wa={top[1]} wd={top[2]} k={top[3]}")
