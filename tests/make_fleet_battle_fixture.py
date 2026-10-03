#!/usr/bin/env python3
"""T1 of docs/proposals/fleet-battles-and-storms.md: two hostile fleets one tile apart at sea, from a two-human start.

New Game with Carthage (row 1) and Ptolemaic (row 3) human, seed 12345 (the T0 setup). Carthage sets war toward Ptolemaic on its
first turn (not with --no-war). Each seat's turn: copy the autosave at once (the second human's autosave overwrites the first's: same name), then sail
its fleet along the sea path toward the other fleet (`planner/sea.py`), stopping next to it; End turn. The sailing stops when the
fleets are adjacent at the START of a seat's turn: that save is the fixture.

    python3 -m tests.make_fleet_battle_fixture            # about 20 minutes
    python3 -m tests.make_fleet_battle_fixture --no-war   # the same without Carthage's war order (the nations stay on trade terms):
                                                          # the fixture for the fleet peace prompt; files T1P_*, in run-exp-peace-prompt

Output: artifacts/run-exp-fleet-battles/T1_<turn>_<seat>_<nation>.SAV for every seat's turn start, T1_log.json, and the fixture
(with --no-war: artifacts/run-exp-peace-prompt/T1P_* and T1P_log.json).
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness.driver import G, Game  # noqa: E402
from planner import sea  # noqa: E402
from state import sav  # noqa: E402

NO_WAR = "--no-war" in sys.argv
OUT = ROOT / "artifacts" / ("run-exp-peace-prompt" if NO_WAR else "run-exp-fleet-battles")
PREFIX = "T1P" if NO_WAR else "T1"
OUT.mkdir(parents=True, exist_ok=True)
NAMES = {1: "Carthage", 3: "Ptolemaic"}
log = []


def keep(name):
    """Copy the autosave that was just written for this seat's turn start; returns the loaded state."""
    s = sav.load(str(G / name))
    dst = OUT / f"{PREFIX}_{s['turn']:04d}_s{s['seat_index']:02d}_{NAMES[s['current_nation']]}.SAV"
    shutil.copy(G / name, dst)
    return s, dst


def fleets_of(s):
    return {f["owner"]: f for f in s["fleets"] if f["owner"] in NAMES}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def sail_toward(g, s, me, other):
    """Move my fleet along the cheapest sea path to a tile next to the other fleet, as far as my moves go."""
    f, o = fleets_of(s)[me], fleets_of(s)[other]
    if cheb((f["x"], f["y"]), (o["x"], o["y"])) <= 1:
        return {"already_adjacent": True}
    cost, path = sea.sea_path_adjacent(s, (f["x"], f["y"]), (o["x"], o["y"]))
    if path is None:
        raise RuntimeError("no sea path from my fleet to the other fleet")
    moves = g.fleet_moves(f["id"])
    reach, spent = sea.legs(s, path, moves)
    for t in reach[1:]:
        for attempt in range(3):          # verify every click's effect; retry at most twice
            pos, texts = g.move_fleet(f["id"], *t)
            if tuple(pos) == tuple(t):
                break
        else:
            raise RuntimeError(f"fleet {f['id']} did not reach {t} (at {tuple(pos)}, boxes {texts})")
    return {"from": (f["x"], f["y"]), "to": tuple(g.fleet_pos(f["id"])), "planned": reach[-1], "moves_before": moves,
            "moves_after": g.fleet_moves(f["id"]), "path_cost": cost}


def main(max_rounds=6):
    g = Game()
    path, popups = g.new_game(row=[1, 3], seed=12345)
    s, dst = keep(Path(path).name)
    for rnd in range(max_rounds * 2):
        me = s["current_nation"]
        other = 3 if me == 1 else 1
        f, o = fleets_of(s)[me], fleets_of(s)[other]
        d = cheb((f["x"], f["y"]), (o["x"], o["y"]))
        row = {"save": dst.name, "turn": s["turn"], "seat": s["seat_index"], "nation": NAMES[me], "my_fleet": (f["id"], f["x"], f["y"], f["ships"], f.get("condition"), f["moves"]),
               "other_fleet": (o["id"], o["x"], o["y"], o["ships"], o.get("condition")), "distance": d, "war": s["nations"][me]["relations"][NAMES[other]]}
        print(f"{dst.name}: {NAMES[me]} fleet {row['my_fleet'][1:3]} v {row['other_fleet'][1:3]} distance {d}, war value {row['war']}", flush=True)
        log.append(row)
        if d <= 1:
            shutil.copy(dst, OUT / f"{PREFIX}_FIXTURE_fleets_adjacent.SAV")
            print("FIXTURE:", dst.name, flush=True)
            break
        if me == 1 and not NO_WAR and s["nations"][1]["relations"]["Ptolemaic"] != 3:
            row["war_order"] = g.relation(3, "war")
        row["sail"] = sail_toward(g, s, me, other)
        print("   ", row["sail"], flush=True)
        (OUT / f"{PREFIX}_log.json").write_text(json.dumps(log, indent=1, default=str))
        name, texts = g.end_turn(timeout=300)
        row["end_turn"] = {"autosave": name, "texts": texts}
        s, dst = keep(name)
    (OUT / f"{PREFIX}_log.json").write_text(json.dumps(log, indent=1, default=str))
    g.kill()


if __name__ == "__main__":
    main()
