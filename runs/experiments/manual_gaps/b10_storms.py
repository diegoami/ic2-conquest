#!/usr/bin/env python3
"""B10: winter storms on six Rome fleets (50 ships, condition 100, supplies 400) on calm open sea far from any city (staged).
Each End turn the six fleet records are read from memory; b10-storms.jsonl holds every turn.

Expected from the code (docs/rules-digest.md §8), condition 100, calm sea, away from own cities, Winter:
dmg = max(1, Random(0)/10) = 1; Winter min(5, 2) = 2; away 2*2+1 = 5 -> condition -5, no ship loss.
The 1-in-20 Winter spike sets dmg = 30: d = (10000/130)^2/100 = 57 (integer steps: 76*76/100) -> ships and condition lose d/300
of themselves: 50 ships -> -9, condition 100 -> -19. Rough sea (weather) instead: min(8, 3*2) = 6, away 13 -> d = 78 -> ships -13.

    python3 runs/experiments/manual_gaps/b10_storms.py SEED [TURNS]
"""
import sys

from mg import SAVES, DATA, start
from turns import end_turns

SAVE = SAVES / "MG_B10_staged_6_rome_fleets_at_sea_winter_270.SAV"


def measure(g):
    out = []
    for i in range(6):
        f = g.fleet_state(i)
        out.append({k: f[k] for k in ("id", "x", "y", "owner", "ships", "condition", "supplies", "moves")}
                   | {"cell": g.cell(f["x"], f["y"])})
    return out


if __name__ == "__main__":
    seed = int(sys.argv[1])
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    g, texts = start(SAVE, seed=seed)
    g.dismiss_popups()
    end_turns(g, "B10", seed, n, measure, jsonl=DATA / "b10-storms.jsonl")
