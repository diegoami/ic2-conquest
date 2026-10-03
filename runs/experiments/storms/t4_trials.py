#!/usr/bin/env python3
"""T4 trials: one storm per trial. A fleet of Carthage (90 ships) at the two-human start, 0720 (T1_0720_s13_Carthage.SAV), is placed
(sailed) on rough sea, left on calm sea away from any own city, or sailed next to an own city, then End turn: the next autosave
(Ptolemaic's turn start, after the weather tick) is the result. One fresh process per seed (RandSeed is read at program start).

Cells (name: condition, season, place, cargo). NATURAL = nothing edited; SYNTHETIC = a save edit of condition / season / cargo (t4_stage.py):
  R85s   rough sea, condition 85 (as in the save), Spring           natural        (5 seeds)
  K85s   stays on calm sea away from cities, 85, Spring             natural        (5)
  H85s   next to an own city (Akra Leuke), 85, Spring               natural        (5)
  R85w / K85w                the same two in Winter                  season edited  (5 each)
  R45s / K45s / H45s         condition 45, Spring                    condition edited (10 each)
  R45w / K45w                condition 45, Winter                    condition and season edited (10 each)
  R85sA  rough, 85, Spring, the mixed 11,000-man army aboard             cargo edited   (5)
  R45sA  rough, 45, Spring, the mixed 11,000-man army aboard             condition and cargo edited (10)

    python3 runs/experiments/storms/t4_trials.py [cell ...] [--seeds N] [--from K] [--save 3,7]
"""
import json
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from harness.driver import G, Game  # noqa: E402
from planner import sea  # noqa: E402
from state import sav  # noqa: E402
import t4_stage  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-storms"
OUT.mkdir(parents=True, exist_ok=True)
START = ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"
CARGO = (2, [(0, 4000), (1, 3000), (2, 2000), (3, 1000), (4, 1000)])      # the mixed army of T3's M15: 11,000 men, five unit types
# name: (condition, season, place, cargo, default seeds, synthetic?)
CELLS = {"R85s": (None, None, "rough", None, 5), "K85s": (None, None, "stay", None, 5), "H85s": (None, None, "city", None, 5),
         "R45s": (45, None, "rough", None, 10), "K45s": (45, None, "stay", None, 10), "H45s": (45, None, "city", None, 10),
         "R85w": (None, 3, "rough", None, 5), "K85w": (None, 3, "stay", None, 5),
         "R45w": (45, 3, "rough", None, 10), "K45w": (45, 3, "stay", None, 10),
         "R85sA": (None, None, "rough", CARGO, 5), "R45sA": (45, None, "rough", CARGO, 10)}


def fixture(cell):
    cond, season, place, cargo, _ = CELLS[cell]
    p = OUT / f"FIX_T4_{cell}.SAV"
    if cond is not None or season is not None or cargo:
        t4_stage.edit(START, p, condition=cond, season=season, cargo=cargo)
    else:
        shutil.copy(START, p)
    return p


def target(s, place):
    f = [x for x in s["fleets"] if x["owner"] == 1][0]
    start = (f["x"], f["y"])
    if place == "stay":
        return start, []
    own = {(c["x"], c["y"]) for c in s["cities"] if c["owner"] == 1}
    if place == "city":
        goal = lambda x, y: any(max(abs(x - cx), abs(y - cy)) <= 1 for cx, cy in own)      # noqa: E731
    else:
        goal = lambda x, y: sav.cell(s, x, y) == 1                                      # noqa: E731
    cost, path = sea.dijkstra(s, start, goal)
    return start, path


def covered(g, i):
    return struct.unpack_from("<h", g.fleet_rec(i), 24)[0]


def trial(cell, seed, fix, save=False):
    cond, season, place, cargo, _ = CELLS[cell]
    s0 = sav.load(str(fix))
    start, path = target(s0, place)
    assert [f["id"] for f in s0["fleets"] if f["owner"] == 1] == [0] and [f["id"] for f in s0["fleets"] if f["owner"] == 3] == [1], "fleet ids: Carthage 0, Ptolemaic 1"
    g = Game()
    try:
        g.load(fix, seed=seed)
        moved = None
        if path:
            moves = g.fleet_moves(0)
            reach, spent = sea.legs(s0, path, moves)
            for t in reach[1:]:
                for _ in range(3):
                    pos, texts = g.move_fleet(0, *t)
                    if tuple(pos) == tuple(t):
                        break
                else:
                    raise RuntimeError(f"did not reach {t}")
            moved = {"to": tuple(g.fleet_pos(0)), "legs_spent": spent, "moves": moves}
        before = g.fleet_state(0) | {"covered": covered(g, 0)}
        if place == "rough" and before["covered"] != 1:
            raise RuntimeError(f"the fleet is not on rough sea (covered {before['covered']}) at {before['x']},{before['y']}")
        if place != "rough" and before["covered"] != 0:
            raise RuntimeError(f"the fleet is not on calm sea (covered {before['covered']}) at {before['x']},{before['y']}")
        near = any(max(abs(before["x"] - c["x"]), abs(before["y"] - c["y"])) <= 1 for c in s0["cities"] if c["owner"] == 1)
        if (place == "city") != near:
            raise RuntimeError(f"the fleet at {before['x']},{before['y']} is {'not ' if place == 'city' else ''}next to an own city: wrong cell")
        b1 = g.fleet_state(1)
        name, texts = g.end_turn(timeout=300)
        s1 = sav.load(str(G / name))
        # a fleet lost at sea leaves the table (the list shrinks): find each fleet by its owner; None = the fleet is gone
        f1 = next((x for x in s1["fleets"] if x["owner"] == 1), None)
        f2 = next((x for x in s1["fleets"] if x["owner"] == 3), None)
        if seed == 1 or save or f1 is None or "45" in cell:      # every low-condition trial is kept: a loss at sea is the point
            shutil.copy(G / name, OUT / f"ST_{cell}_seed{seed}_{name}")
        # an army that dies leaves the table and the last record takes its index: Carthage's armies are listed whole, not by index
        armies = {"carthage_armies_after": [(a["id"], a["troops"], a["cell"], [(u["type"], u["troops"]) for u in a["units"]]) for a in s1["armies"] if a["owner"] == 1]} if cargo else {}
        return {"cell": cell, "seed": seed, "synthetic": bool(cond is not None or season is not None or cargo), "moved": moved, "before": before,
                "after": f1, "ptolemaic_before": b1, "ptolemaic_after": f2, "end_turn_texts": texts, **armies,
                "news": [n for n in s1["news"][-60:] if "fleet" in str(n).lower()], "turn_after": s1["turn"],
                "calendar_after": (s1["season"], s1["week"])}
    finally:
        g.kill()


def main():
    args = sys.argv[1:]
    first = int(args[args.index("--from") + 1]) if "--from" in args else 1
    save_seeds = {int(x) for x in args[args.index("--save") + 1].split(",")} if "--save" in args else set()
    cells = [a for a in args if a in CELLS] or list(CELLS)
    f = OUT / "t4_trials.json"
    res = json.loads(f.read_text()) if f.exists() else []
    for cell in cells:
        n = int(args[args.index("--seeds") + 1]) if "--seeds" in args else CELLS[cell][4]
        fix = fixture(cell)
        for seed in range(first, n + 1):
            try:
                r = trial(cell, seed, fix, save=seed in save_seeds)
            except Exception as e:     # noqa: BLE001 - a failure is a result
                r = {"cell": cell, "seed": seed, "error": f"{type(e).__name__}: {e}"}
            res = [x for x in res if not (x["cell"] == cell and x["seed"] == seed)] + [r]
            f.write_text(json.dumps(res, indent=1, default=str))
            if "error" in r:
                print(cell, seed, "ERROR", r["error"][:150], flush=True)
            else:
                b, a = r["before"], r["after"]
                after = "LOST AT SEA" if a is None else f"{a['ships']} ships, condition {a['condition']}"
                print(f"{cell:6s} seed {seed:2d}: {b['ships']} ships, condition {b['condition']} -> {after}; news {r['news'][-2:]}", flush=True)


if __name__ == "__main__":
    main()
