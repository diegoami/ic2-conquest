#!/usr/bin/env python3
"""Pair 2 (Seleucid + Ptolemaic, both human, seed 12345), phase 1: Seleucid orders a 60-ship fleet at the port the game picks (Issus,
the first Build fleet by a nation that is not Rome in a two-human game) while Ptolemaic's fleet is docked, repaired and supplied at
Alexandria; both only end turns until Seleucid's fleet is launched (12 turns). Every seat's autosave is copied at once (the second
human's overwrites the first's).

    python3 runs/experiments/pair2/phase1.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import G, Game  # noqa: E402
from planner import sea  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-pair2"
OUT.mkdir(parents=True, exist_ok=True)
NAMES = {2: "Seleucid", 3: "Ptolemaic"}
SHIPS = 60
log = []


def keep(name):
    s = sav.load(str(G / name))
    dst = OUT / f"P2_{s['turn']:04d}_s{s['seat_index']:02d}_{NAMES.get(s['current_nation'], s['current_nation'])}.SAV"
    shutil.copy(G / name, dst)
    return s, dst


def my_fleets(s, n):
    return [f for f in s["fleets"] if f["owner"] == n]


def dock_ptolemaic(g, s):
    f = my_fleets(s, 3)[0]
    own = {(c["x"], c["y"]) for c in s["cities"] if c["owner"] == 3}
    goal = lambda x, y: any(max(abs(x - cx), abs(y - cy)) <= 1 for cx, cy in own)      # noqa: E731
    cost, path = sea.dijkstra(s, (f["x"], f["y"]), goal)
    reach, spent = sea.legs(s, path, g.fleet_moves(f["id"]))
    for t in reach[1:]:
        for _ in range(3):
            pos, texts = g.move_fleet(f["id"], *t)
            if tuple(pos) == tuple(t):
                break
        else:
            raise RuntimeError(f"did not reach {t}")
    out = {"path_cost": cost, "docked_at": tuple(g.fleet_pos(f["id"])), "before": g.fleet_state(f["id"])}
    out["repair"] = g.repair_fleet(f["id"], 100 - f["condition"])
    out["supply"] = g.supply_fleet(f["id"], tons=400)
    out["after"] = g.fleet_state(f["id"])
    return out


def main(max_turns=40):
    g = Game()
    path, popups = g.new_game(row=[2, 3], seed=12345)
    s, dst = keep(Path(path).name)
    done_seleucid = done_ptolemaic = False
    try:
        for i in range(max_turns):
            me = s["current_nation"]
            row = {"save": dst.name, "turn": s["turn"], "seat": s["seat_index"], "nation": NAMES[me],
                   "fleets": [(f["id"], f["owner"], f["x"], f["y"], f.get("ships"), f.get("condition"), f.get("supplies"), f.get("moves"), f.get("countdown"), f["building"]) for f in s["fleets"] if f["owner"] in NAMES],
                   "treasury": {NAMES[n]: s["nations"][n]["treasury"] for n in NAMES}}
            log.append(row)
            print(row, flush=True)
            if me == 3 and not done_ptolemaic:
                row["dock"] = dock_ptolemaic(g, s)
                print("   ", row["dock"], flush=True)
                done_ptolemaic = True
            if me == 2 and not done_seleucid:
                row["build"] = g.build_fleet(SHIPS)
                print("   build:", row["build"], flush=True)
                done_seleucid = True
            launched = [f for f in my_fleets(s, 2) if not f["building"]]
            (OUT / "P2_phase1_log.json").write_text(json.dumps(log, indent=1, default=str))
            if launched:
                print("LAUNCHED:", launched, flush=True)
                break
            name, texts = g.end_turn(timeout=300)
            s, dst = keep(name)
            row["end_turn"] = {"autosave": name, "texts": texts}
    finally:
        (OUT / "P2_phase1_log.json").write_text(json.dumps(log, indent=1, default=str))
        g.kill()


if __name__ == "__main__":
    main()
