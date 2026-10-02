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
cells = defaultdict(lambda: {"n": 0, "w": 0, "ratio": None, "att": None, "dfn": None})
for t in trials:
    if "error" in t:
        continue
    c = cells[t["cell"]]
    c["n"] += 1
    c["w"] += 1 if (t["attacker_alive"] and not t["defender_alive"]) else 0
    a, d = t["strength"]
    c["ratio"] = a / d
    c["att"], c["dfn"] = (t["attacker_before"]["ships"], t["attacker_before"]["condition"]), (t["defender_before"]["ships"], t["defender_before"]["condition"])
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


def loglik_gamma(gamma, wa=0.3, wd=0.3, k=1.0):
    """The literal random term, but strength = ships * condition ** gamma (gamma = 1 is the research formula)."""
    ll = 0.0
    for c in cells.values():
        ratio = (c["att"][0] * c["att"][1] ** gamma) / (c["dfn"][0] * c["dfn"][1] ** gamma)
        p = min(max(p_attacker(ratio, wa, wd, k), 1e-6), 1 - 1e-6)
        ll += c["w"] * math.log(p) + (c["n"] - c["w"]) * math.log(1 - p)
    return ll


print()
print("H7: strength = ships * condition^gamma (literal random term wa = wd = 0.3, k = 1); gamma = 1 is the research formula")
prof = [(g / 10, loglik_gamma(g / 10)) for g in range(0, 41)]
top = max(prof, key=lambda x: x[1])
print(f"  best gamma {top[0]:.1f}: logL {top[1]:.2f} (gamma = 1: logL {loglik_gamma(1.0):.2f}; AIC {2 - 2 * top[1]:.2f} against {-2 * loglik_gamma(1.0):.2f} for gamma = 1)")
print("  gamma values within 1.92 log-likelihood units of the best (an approximate 95 % interval):",
      [g for g, l in prof if top[1] - l <= 1.92])
print()
print("profile for the equal random width w (k = 1) and for the attacker factor k (w = 0.3); values within 1.92 of the best:")
pw = [(w, loglik(w, w, 1.0)) for w in [i / 100 for i in range(5, 61, 1)]]
tw = max(pw, key=lambda x: x[1]); print(f"  w: best {tw[0]:.2f} (logL {tw[1]:.2f}); interval {min(w for w, l in pw if tw[1] - l <= 1.92):.2f} to {max(w for w, l in pw if tw[1] - l <= 1.92):.2f}")
pk = [(k, loglik(0.3, 0.3, k)) for k in [0.9 + i / 200 for i in range(0, 41)]]
tk = max(pk, key=lambda x: x[1]); print(f"  k: best {tk[0]:.3f} (logL {tk[1]:.2f}); interval {min(k for k, l in pk if tk[1] - l <= 1.92):.3f} to {max(k for k, l in pk if tk[1] - l <= 1.92):.3f}")
print()
print("goodness of fit of the literal model (Pearson chi-square over the cells):")
chi = 0.0
for name, c in sorted(cells.items(), key=lambda kv: kv[1]["ratio"]):
    p = p_attacker(c["ratio"], .3, .3, 1.0); e = c["n"] * p; var = c["n"] * p * (1 - p)
    z = (c["w"] - e) / math.sqrt(var) if var > 1e-9 else 0.0
    chi += z * z if var > 1e-9 else 0
    print(f"  {name:4s} observed {c['w']:2d}  expected {e:5.1f}  z {z:+.2f}")
print(f"  chi-square {chi:.2f} on about {len(cells)} cells")
