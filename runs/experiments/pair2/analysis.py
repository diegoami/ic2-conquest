#!/usr/bin/env python3
"""Pair 2 analysis from trials.json: attacker wins per cell against the strength formula (`ships x condition / 10`, a factor 1 + U(0, 0.3)
on each side, 400,000 simulated battles per cell) and one-sided binomial tails; plus the per-seed winners that show the draw follows the role.

    python3 runs/experiments/pair2/analysis.py [trials.json]
"""
import json
import random
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
F = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts" / "run-exp-pair2" / "trials.json"
trials = [t for t in json.loads(F.read_text()) if "error" not in t]
rng = random.Random(5)


def p_win(att, dfn, n=400000):
    return sum(att * (1 + rng.uniform(0, .3)) > dfn * (1 + rng.uniform(0, .3)) for _ in range(n)) / n


def tail(n, q, k):
    return sum(comb(n, i) * q ** i * (1 - q) ** (n - i) for i in range(k, n + 1))


exp, wins = {}, {}
for cell in "SP":
    ts = sorted((t for t in trials if t["cell"] == cell), key=lambda t: t["seed"])
    a, d = ts[0]["attacker_before"], ts[0]["defender_before"]
    exp[cell] = p_win(a["ships"] * a["condition"] / 10, d["ships"] * d["condition"] / 10)
    wins[cell] = sum(1 for t in ts if t["attacker_alive"] and not t["defender_alive"])
    print(f"{cell}: {len(ts)} battles, attacker wins {wins[cell]}, expected {exp[cell]:.3f}, P(that many or more) {tail(len(ts), exp[cell], wins[cell]):.3f}")
tot = wins["S"] + wins["P"]
print(f"both cells: attacker wins {tot} of 20, expected {(exp['S'] + exp['P']) * 10:.1f}, P(that many or more at a 0.5 rate) {tail(20, 0.5, tot):.3f}")
by = {c: {t["seed"]: t for t in trials if t["cell"] == c} for c in "SP"}
print("per seed (S winner / P winner):")
for seed in sorted(by["S"]):
    ws = "Seleucid" if by["S"][seed]["attacker_alive"] and not by["S"][seed]["defender_alive"] else "Ptolemaic"
    wp = "Ptolemaic" if by["P"][seed]["attacker_alive"] and not by["P"][seed]["defender_alive"] else "Seleucid"
    print(f"  seed {seed:2d}: {ws:9s} / {wp:9s}  {'attacker won both' if (ws == 'Seleucid' and wp == 'Ptolemaic') else ''}")
