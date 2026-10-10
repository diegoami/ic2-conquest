#!/usr/bin/env python3
"""Pair 2, phase 2: from Seleucid's launch (P2_0732_s02_Ptolemaic.SAV, Ptolemaic's seat) Ptolemaic's fleet (1, 70 ships) sails to Seleucid's new fleet
(2, 60 ships, next to Issus). When adjacent the fleet is next to Seleucid's own city: Ptolemaic tries the attack once (the plan's 2.6:
"You cannot attack a fleet docked at its own city !") and Seleucid then sails out of reach of its city; Ptolemaic follows, ends its turn
adjacent; the autosaves of the next Ptolemaic seat start (Seleucid moved out in its turn, so the fleets are adjacent) and, in the same
turn, of Seleucid's seat start are the two fixtures `FIX_S2_ptolemaic_seat_<turn>.SAV` and `FIX_S2_seleucid_seat_<turn>.SAV`.

    python3 runs/experiments/pair2/phase2.py
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
from harness import environment as _env  # noqa: E402  every game start writes environment-<stamp>.json beside the outputs
_env.folder_sink(OUT, 'pair2/phase2.py')
START = OUT / "P2_0732_s02_Ptolemaic.SAV"
NAMES = {2: "Seleucid", 3: "Ptolemaic"}
log = []


def keep(name):
    s = sav.load(str(G / name))
    dst = OUT / f"P2_{s['turn']:04d}_s{s['seat_index']:02d}_{NAMES.get(s['current_nation'], s['current_nation'])}.SAV"
    shutil.copy(G / name, dst)
    return s, dst


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def fl(s, n):
    return [f for f in s["fleets"] if f["owner"] == n][0]


def near_own_city(s, f, n):
    return any(cheb((f["x"], f["y"]), (c["x"], c["y"])) <= 1 for c in s["cities"] if c["owner"] == n)


def sail(g, s, f, path):
    reach, spent = sea.legs(s, path, g.fleet_moves(f["id"]))
    for t in reach[1:]:
        for _ in range(3):
            pos, texts = g.move_fleet(f["id"], *t)
            if tuple(pos) == tuple(t):
                break
        else:
            raise RuntimeError(f"fleet {f['id']} did not reach {t}")
    return {"to": tuple(g.fleet_pos(f["id"])), "spent": spent}


def sail_toward(g, s, me, other):
    f, o = fl(s, me), fl(s, other)
    cost, path = sea.sea_path_adjacent(s, (f["x"], f["y"]), (o["x"], o["y"]))
    if path is None:
        raise RuntimeError("no sea path")
    return sail(g, s, f, path) | {"path_cost": cost}


def sail_out(g, s, me, min_dist=3):
    """Seleucid's fleet leaves its city's reach: the nearest tile at least `min_dist` from every own city, not adjacent to one."""
    f = fl(s, me)
    own = [(c["x"], c["y"]) for c in s["cities"] if c["owner"] == me]
    goal = lambda x, y: all(cheb((x, y), c) >= min_dist for c in own)       # noqa: E731
    cost, path = sea.dijkstra(s, (f["x"], f["y"]), goal)
    out = sail(g, s, f, path) | {"path_cost": cost}
    if any(cheb(out["to"], c) < min_dist for c in own):
        raise RuntimeError(f"the fleet stopped at {out['to']}, still within {min_dist} tiles of an own city")
    return out


def main(max_turns=14):
    g = Game()
    tested26 = False
    supplied_seleucid = False
    out_done = False
    seats = 0
    try:
        g.load(START, seed=12345)
        s = sav.load(str(START))
        dst = START
        for i in range(max_turns):
            me = s["current_nation"]
            other = 5 - me
            f, o = fl(s, me), fl(s, other)
            d = cheb((f["x"], f["y"]), (o["x"], o["y"]))
            row = {"save": dst.name, "turn": s["turn"], "nation": NAMES[me], "distance": d,
                   "fleets": {NAMES[n]: (fl(s, n)["x"], fl(s, n)["y"], fl(s, n)["ships"], fl(s, n)["condition"], fl(s, n)["supplies"], fl(s, n)["moves"]) for n in NAMES},
                   "seleucid_next_to_city": near_own_city(s, fl(s, 2), 2), "ptolemaic_next_to_city": near_own_city(s, fl(s, 3), 3)}
            log.append(row)
            print(row, flush=True)
            if me == 2 and not supplied_seleucid:
                supplied_seleucid = True
                row["supply"] = g.supply_fleet(f["id"], tons=300)
                row["after_supply"] = g.fleet_state(f["id"])
                print("   supply:", row["after_supply"], flush=True)
            if me == 3 and i == 0:
                row["supply"] = g.supply_fleet(f["id"], tons=400)
                row["after_supply"] = g.fleet_state(f["id"])
            if me == 3 and d > 1:
                row["sail"] = sail_toward(g, s, 3, 2)
            elif me == 3 and d <= 1 and near_own_city(s, fl(s, 2), 2) and not tested26:
                row["attack_next_to_city"] = g.attack_fleet(f["id"], o["id"])
                tested26 = True
                print("   attack next to the enemy's city:", row["attack_next_to_city"], flush=True)
            elif me == 2 and d <= 1 and tested26 and not out_done:
                row["sail_out"] = sail_out(g, s, 2)
                out_done = True
            elif me == 3 and d <= 1 and out_done and not near_own_city(s, fl(s, 2), 2):
                shutil.copy(dst, OUT / f"FIX_S2_ptolemaic_seat_{s['turn']:04d}.SAV")        # Ptolemaic's seat start: Ptolemaic attacks
                print("FIXTURE at Ptolemaic's seat:", dst.name, flush=True)
            elif me == 2 and d <= 1 and out_done and not near_own_city(s, fl(s, 2), 2):
                shutil.copy(dst, OUT / f"FIX_S2_seleucid_seat_{s['turn']:04d}.SAV")         # Seleucid's seat start, same turn: Seleucid attacks
                print("FIXTURE at Seleucid's seat:", dst.name, flush=True)
                seats += 1
            (OUT / "P2_phase2_log.json").write_text(json.dumps(log, indent=1, default=str))
            if seats:
                break
            name, texts = g.end_turn(timeout=300)
            row["end_turn"] = {"autosave": name, "texts": texts}
            s, dst = keep(name)
        else:
            print("no fixture within", max_turns, "turns", flush=True)
    finally:
        (OUT / "P2_phase2_log.json").write_text(json.dumps(log, indent=1, default=str))
        g.kill()


if __name__ == "__main__":
    main()
