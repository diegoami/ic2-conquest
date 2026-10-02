#!/usr/bin/env python3
"""Build the fleet fixture: from the run-0 start, build a 30-ship fleet and end turns until it launches.

A fleet takes 24 weeks to build (the countdown falls by 2 a turn, so 12 turns); every fleet order needs a
launched fleet, so this is made once and reused. Output: $IC2_WORK/fixtures/FLEET.SAV (the autosave of the turn
the fleet appeared) and a line with where the fleet is. 30 ships so that Split fleet (20 ships minimum) is possible.

    python3 -m tests.make_fleet_fixture            # FLEET.SAV: the fleet launched (12 turns)
    python3 -m tests.make_fleet_fixture stage      # FLEET2.SAV: from FLEET.SAV, the fleet sails to Antium and army 0
                                                   # marches next to it (Caere fell to Gaul while the fleet was built, so
                                                   # the launch port is no longer Rome's)
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.driver import G, WORK, Game  # noqa: E402
from state import sav  # noqa: E402

BASE = WORK / "fixtures" / "BASE.SAV"
OUT = WORK / "fixtures" / "FLEET.SAV"
OUT2 = WORK / "fixtures" / "FLEET2.SAV"


def rome_fleets(path):
    s = sav.load(str(path))
    return s, [f for f in s["fleets"] if f["owner"] == 0]


def main(ships=30, max_turns=16):
    g = Game()
    g.load(BASE, seed=12345)
    print("build:", g.build_fleet(ships), flush=True)
    for i in range(max_turns):
        name, texts = g.end_turn()
        s, fl = rome_fleets(G / name)
        row = [(f["id"], f["x"], f["y"], f["countdown"], f["ships"], f["building"]) for f in fl]
        print(f"turn {name}: Rome fleets {row}", flush=True)
        launched = [f for f in fl if not f["building"] and (f["x"], f["y"]) != (0, 0)]
        if launched:
            shutil.copy(G / name, OUT)
            print("LAUNCHED:", launched[0], "->", OUT, flush=True)
            break
    else:
        raise SystemExit("no fleet launched within %d turns" % max_turns)
    g.kill()


def stage():
    """FLEET.SAV -> end a turn (a fleet has 0 moves on its launch turn) -> sail to the sea tile next to Antium
    (102,46) -> march army 0 to a land tile next to the fleet -> save FLEET2.SAV."""
    import struct
    from planner.path import path_adjacent, turn_legs
    g = Game()
    g.load(OUT, seed=12345)
    name, _ = g.end_turn()
    print("turn", name, "fleet moves", g.fleet_moves(2), "at", g.fleet_pos(2), flush=True)
    pos, texts = g.move_fleet(2, 101, 46)
    print("fleet ->", pos, texts, flush=True)
    assert tuple(pos) == (101, 46), pos
    for _ in range(4):
        base = sav.load(str(G / name))
        a = g.army_pos(0)
        if max(abs(a[0] - 101), abs(a[1] - 46)) == 1:
            break
        cost, path = path_adjacent(base, tuple(a), (101, 46))
        moves = struct.unpack_from("<h", g.army_rec(0), 6)[0]
        reach, spent = turn_legs(base, path, moves)
        for t in reach[1:]:
            g.move(0, *t)
        print("army 0 ->", g.army_pos(0), "moves left", struct.unpack_from("<h", g.army_rec(0), 6)[0], flush=True)
        if max(abs(g.army_pos(0)[0] - 101), abs(g.army_pos(0)[1] - 46)) == 1:
            break
        name, _ = g.end_turn()
        print("turn", name, flush=True)
    a = g.army_pos(0)
    assert max(abs(a[0] - 101), abs(a[1] - 46)) == 1, ("army not next to the fleet", a)
    p = g.save_as("FLEET2_STAGE.SAV")
    shutil.copy(p, OUT2)
    s2 = sav.load(str(OUT2))
    print("FLEET2:", [(f["id"], f["x"], f["y"], f["ships"], f["moves"]) for f in s2["fleets"] if f["owner"] == 0],
          "army 0", (a[0], a[1], struct.unpack_from("<h", g.army_rec(0), 6)[0]), "->", OUT2, flush=True)
    g.kill()


if __name__ == "__main__":
    stage() if sys.argv[1:] == ["stage"] else main()
