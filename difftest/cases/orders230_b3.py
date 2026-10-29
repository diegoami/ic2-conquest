"""#230 batch 3: fleet orders, mobilization and unit-level orders, each followed by one End turn.

Starts:
- PORT = saves/fleet-port-antium-0734.SAV (Rome, Autumn week 5, 270 BC): army 0 (10,700 troops, 3 moves) at
  (101,45) next to fleet 2 (30 ships, condition 97, 29 moves, empty) at (101,46), beside Antium (102,46); armies
  12 and 13 (0 moves) at (102,45) and (102,44); four queued recruits at Rome (state 24).
- SPLIT = saves/fleet-split-antium-0734.SAV: the same after Split fleet: fleet 2 (20 ships) at (101,46) and
  fleet 5 (10 ships, 0 moves) at (101,47).
- BASE (Rome, 270 BC Spring week 1): army 0 units li 4,800, hi 5,000, hi 5,200, ...; queued recruits at Rome
  (states 9, 13, 17, 17).
"""
from pathlib import Path

from difftest.cases.orders230_b1 import BASE, case

ROOT = Path(__file__).resolve().parents[2]
PORT = str(ROOT / "saves/fleet-port-antium-0734.SAV")
SPLIT = str(ROOT / "saves/fleet-split-antium-0734.SAV")

CASES = [
    case("embark", "army 0 boards fleet 2", {"op": "embark", "army": 0, "fleet": 2}, start=PORT),
    case("embark-sail", "army 0 boards fleet 2, then the fleet sails to (99,47)",
         {"op": "embark", "army": 0, "fleet": 2}, {"op": "move_fleet", "fleet": 2, "x": 99, "y": 47}, start=PORT),
    case("embark-turn-disembark", "army 0 boards fleet 2, End turn, then lands at (102,47)",
         {"op": "embark", "army": 0, "fleet": 2}, {"op": "end_turn"},
         {"op": "disembark", "army": 0, "fleet": 2, "x": 102, "y": 47}, start=PORT),
    case("fleet-sail", "fleet 2 sails to (97,48)", {"op": "move_fleet", "fleet": 2, "x": 97, "y": 48}, start=PORT),
    case("repair-3", "repair fleet 2 by 3 points at Antium", {"op": "repair_fleet", "fleet": 2, "points": 3}, start=PORT),
    case("scuttle", "scuttle fleet 2 next to Antium", {"op": "scuttle_fleet", "fleet": 2}, start=PORT),
    case("split-fleet-10", "split 10 ships off fleet 2", {"op": "split_fleet", "fleet": 2, "ships": 10}, start=PORT),
    case("join-fleets", "join fleets 2 and 5", {"op": "join_fleets", "fleet": 2, "partner": 5}, start=SPLIT),
    case("transfer-ships-5", "move 5 ships from fleet 2 to fleet 5",
         {"op": "transfer_ships", "fleet": 2, "partner": 5, "ships": 5}, start=SPLIT),
    case("mobilize-port-0", "mobilize recruit slot 0 (li 5,500, state 24)", {"op": "mobilize", "slot": 0}, start=PORT),
    case("mobilize-base-3", "mobilize recruit slot 3 (hc 1,000, state 17)", {"op": "mobilize", "slot": 3}),
    case("disband-unit", "disband unit row 0 of army 0", {"op": "disband_unit", "army": 0, "unit": 0}),
    case("join-units-hi", "join unit rows 1 and 2 of army 0 (two hi)", {"op": "join_units", "army": 0, "units": [1, 2]}),
    case("split-transfer-unit", "split row 0 off army 0, then transfer row 0 of army 0 to the new army",
         {"op": "split_army", "army": 0, "units": [0]}, {"op": "transfer_units", "army": 0, "partner": 14, "unit": 0}),
]
