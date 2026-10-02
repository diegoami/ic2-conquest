#!/usr/bin/env python3
"""The fleet path planner (planner/sea.py): hand cases on a made-up map, and the real route between Carthage's and Ptolemaic's fleets.

No game: pure logic.   python3 -m tests.test_sea_path
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from planner import sea  # noqa: E402
from state import sav  # noqa: E402
from state.sav import MAP_H, MAP_W  # noqa: E402

BLOCK = 4          # a land code, never sea


def blank():
    return {"map": [BLOCK] * (MAP_W * MAP_H)}


def put(s, x, y, code):
    s["map"][x * MAP_H + y] = code


def test_straight_calm_corridor():
    s = blank()
    for x in range(10, 16):
        put(s, x, 50, sea.CALM)
    cost, path = sea.sea_path(s, (10, 50), (15, 50))
    assert path == [(x, 50) for x in range(10, 16)] and cost == 5, (cost, path)
    return "a calm corridor of 6 tiles costs 5"


def test_rough_costs_three_and_is_avoided_when_a_calm_way_exists():
    s = blank()
    for x in range(10, 14):
        put(s, x, 50, sea.CALM)
    put(s, 12, 50, sea.ROUGH)                       # the direct way crosses a rough tile (cost 3)
    for x in (11, 12, 13):
        put(s, x, 51, sea.CALM)                     # a calm detour of the same length
    cost, path = sea.sea_path(s, (10, 50), (13, 50))
    assert cost == 3 and all(sea.sea_cost(sav.cell(s, *t)) == 1 for t in path[1:]), (cost, path)
    s2 = blank()
    for x in range(10, 14):
        put(s2, x, 50, sea.CALM)
    put(s2, 12, 50, sea.ROUGH)                      # no detour: the rough tile must be crossed
    cost2, path2 = sea.sea_path(s2, (10, 50), (13, 50))
    assert cost2 == 1 + 3 + 1, cost2
    return "rough sea costs 3: avoided when a calm way exists, paid when it does not"


def test_land_cities_and_fleets_block():
    s = blank()
    for x in range(10, 14):
        put(s, x, 50, sea.CALM)
    put(s, 12, 50, 316)                             # a fleet marker blocks the way
    cost, path = sea.sea_path(s, (10, 50), (13, 50))
    assert path is None, path
    return "a fleet marker (and land, and a city marker) blocks a fleet"


def test_adjacent_goal_and_legs():
    s = blank()
    for x in range(10, 40):
        put(s, x, 50, sea.CALM)
    put(s, 39, 50, 316)                             # the target fleet
    cost, path = sea.sea_path_adjacent(s, (10, 50), (39, 50))
    assert path[-1] == (38, 50) and cost == 28, (cost, path[-1])
    reach, spent = sea.legs(s, path, 10)
    assert reach[-1] == (20, 50) and spent == 10, (reach[-1], spent)
    reach2, spent2 = sea.legs(s, path, 100)
    assert reach2 == path and spent2 == 28
    return "adjacent goal at 28; 10 moves reach (20,50); 100 moves reach the end"


def test_fleet_moves_formula():
    assert sea.fleet_moves(90) == 26 and sea.fleet_moves(70) == 28 and sea.fleet_moves(30) == 32, "formula"
    assert sea.fleet_moves(30, troops_aboard=10700) == 32 - (10700 // 100 // 30 + 1)
    assert sea.fleet_moves(90, condition=45) == 26 - ((70 - 45) >> 2)
    return "26 / 28 / 32 moves for 90 / 70 / 30 ships; cargo and condition lower it (the live 30-ship value was 32)"


def test_real_route_between_the_two_fleets():
    s = sav.load(str(ROOT / "saves" / "run0-start-AUTO0720-seed12345.SAV"))
    a = next(f for f in s["fleets"] if f["owner"] == 1)           # Carthage, 90 ships
    b = next(f for f in s["fleets"] if f["owner"] == 3)           # Ptolemaic, 70 ships
    cost, path = sea.sea_path_adjacent(s, (a["x"], a["y"]), (b["x"], b["y"]))
    assert path and max(abs(path[-1][0] - b["x"]), abs(path[-1][1] - b["y"])) == 1, path[-1:]
    assert sea.path_cost(s, path) == cost
    turns = -(-cost // sea.fleet_moves(a["ships"]))
    return (f"Carthage ({a['x']},{a['y']}) -> next to Ptolemaic ({b['x']},{b['y']}): {len(path) - 1} tiles, cost {cost}, "
            f"{turns} turns for one fleet alone (26 moves)")


TESTS = ["straight_calm_corridor", "rough_costs_three_and_is_avoided_when_a_calm_way_exists", "land_cities_and_fleets_block",
         "adjacent_goal_and_legs", "fleet_moves_formula", "real_route_between_the_two_fleets"]

if __name__ == "__main__":
    bad = 0
    for n in sys.argv[1:] or TESTS:
        try:
            print(f"PASS {n}: {globals()['test_' + n]()}")
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"FAIL {n}: {type(e).__name__}: {e}")
    sys.exit(1 if bad else 0)
