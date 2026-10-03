#!/usr/bin/env python3
"""T4 analysis from t4_trials.json: the observed storm outcome of each cell against the research formula
(docs/rules-digest.md §8, supply-driven-morale-and-fleet-attrition.md), simulated exactly:

    dmg = max(1, Random(100 - condition) // 10)
    Winter: dmg = min(5, 2 dmg);  rough sea: dmg = min(8, 3 dmg)          (both apply, winter first: seen in R85w)
    away from own cities: dmg = 2 dmg + 1 (Winter: a 1-in-20 spike to 30);  next to one: dmg = dmg / 2
    dmg < 6: condition -= dmg;  dmg >= 6: ships and condition lose d/300 of themselves, d = (10000/(dmg+100))^2/100 (integer steps)
    condition < 40 after the storm damage: the fleet is lost at sea (with any army aboard)
    out of supplies: condition -= Random(2)   (applied after the loss test)

    python3 runs/experiments/storms/t4_analysis.py [t4_trials.json]

The table simulates Carthage's fleet (supplies at zero at the tick). The Ptolemaic expectations quoted in the finding (calm sea away from cities,
70 ships, condition 75, supplies 80 so no out-of-supply term; Spring 0.8/0.2, Winter 0.76/0.19/0.05) are `storm(rng, 70, 75, winter, False, False,
supplies0=False)` of this file, run by hand.
"""
import collections
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
F = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts" / "run-exp-storms" / "t4_trials.json"
PLACE = {"R": "rough", "K": "stay", "H": "city"}


def storm(rng, ships, cond, winter, rough, near_city, supplies0=True):
    dmg = max(1, rng.randrange(100 - cond) // 10) if cond < 100 else 1
    if winter:
        dmg = min(5, dmg * 2)
    if rough:
        dmg = min(8, dmg * 3)
    if near_city:
        dmg //= 2
    else:
        dmg = 2 * dmg + 1
        if winter and rng.randrange(20) == 0:
            dmg = 30
    new_ships, new_cond = ships, cond
    if dmg < 6:
        new_cond = cond - dmg
    else:
        d = (10000 // (dmg + 100)) ** 2 // 100
        new_ships, new_cond = ships - ships * d // 300, cond - cond * d // 300
    lost = new_cond < 40            # tested before the out-of-supply decrement: a fleet can end at 39 (seen in K45s, K45w)
    if supplies0:
        new_cond -= rng.randrange(2)
    return new_ships, new_cond, lost, dmg


def cell_flags(cell):
    return PLACE[cell[0]] == "rough", PLACE[cell[0]] == "city", cell.endswith("w")


if __name__ == "__main__":
    allt = json.loads(F.read_text())
    trials = [t for t in allt if "error" not in t]
    if len(trials) != len(allt):
        print(f"WARNING: {len(allt) - len(trials)} failed trials dropped:", sorted((t["cell"], t["seed"]) for t in allt if "error" in t))
    by = collections.defaultdict(list)
    for t in trials:
        by[t["cell"]].append(t)
    rng = random.Random(1)
    for cell in sorted(by):
        rough, city, winter = cell_flags(cell)
        ts = sorted(by[cell], key=lambda t: t["seed"])
        obs = collections.Counter()
        for t in ts:
            a, b = t["after"], t["before"]
            obs["lost" if a is None else (b["ships"] - a["ships"], b["condition"] - a["condition"])] += 1
        b = ts[0]["before"]
        sim = collections.Counter()
        n = 20000
        for _ in range(n):
            ns, nc, lost, _d = storm(rng, b["ships"], b["condition"], winter, rough, city)
            sim["lost" if lost else (b["ships"] - ns, b["condition"] - nc)] += 1
        print(f"{cell}: {len(ts)} trials (seeds {ts[0]['seed']}-{ts[-1]['seed']}{'' if not set(range(1, ts[-1]['seed'] + 1)) - {t['seed'] for t in ts} else ', SOME MISSING'}), condition {b['condition']}")
        print("  observed (ships lost, condition lost):", dict(sorted(obs.items(), key=lambda kv: -kv[1])))
        print("  formula  :", {k: round(v / n, 3) for k, v in sorted(sim.items(), key=lambda kv: -kv[1])[:8]})
