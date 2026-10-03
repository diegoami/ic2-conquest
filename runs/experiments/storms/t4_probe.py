#!/usr/bin/env python3
"""T4 probe: Carthage's fleet sails onto a rough-sea tile (code 1) at the two-human start, 0720, and ends the turn; the next autosave
(Ptolemaic's turn start, after the weather tick and the AI seats) shows what the storm did. NATURAL state (no save edit): the
rough tiles are read from the save's map (spring 0720: 112 code-1 tiles, nearest 12 tiles from the fleet).

    python3 runs/experiments/storms/t4_probe.py SEED [SEED ...]
"""
import json
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import G, Game  # noqa: E402
from planner import sea  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-storms"
OUT.mkdir(parents=True, exist_ok=True)
START = ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"


def covered(g, i):
    """The terrain code under fleet i (record offset 24: 0 calm, 1 rough)."""
    return struct.unpack_from("<h", g.fleet_rec(i), 24)[0]


def trial(seed):
    s0 = sav.load(str(START))
    f = [x for x in s0["fleets"] if x["owner"] == 1][0]
    cost, path = sea.dijkstra(s0, (f["x"], f["y"]), lambda x, y: sav.cell(s0, x, y) == 1)
    g = Game()
    try:
        g.load(START, seed=seed)
        moves = g.fleet_moves(f["id"])
        reach, spent = sea.legs(s0, path, moves)
        for t in reach[1:]:
            for _ in range(3):
                pos, texts = g.move_fleet(f["id"], *t)
                if tuple(pos) == tuple(t):
                    break
            else:
                raise RuntimeError(f"did not reach {t}")
        before = g.fleet_state(f["id"]) | {"covered": covered(g, f["id"])}
        name, texts = g.end_turn(timeout=300)
        s1 = sav.load(str(G / name))
        f1 = [x for x in s1["fleets"] if x["owner"] == 1][0]
        shutil.copy(G / name, OUT / f"PROBE_seed{seed}_{name}")
        return {"seed": seed, "before": before, "after": f1, "path_cost": cost, "moves": moves, "legs_spent": spent, "end_turn_texts": texts,
                "news": [n for n in s1["news"] if "fleet" in str(n).lower()][-5:], "turn_after": s1["turn"]}
    finally:
        g.kill()


if __name__ == "__main__":
    res = []
    for seed in map(int, sys.argv[1:]):
        r = trial(seed)
        res.append(r)
        print(json.dumps(r, default=str), flush=True)
    (OUT / "probe.json").write_text(json.dumps(res, indent=1, default=str))
