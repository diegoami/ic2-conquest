"""#230 batch 6: limits and refusals, on staged copies of fixtures (difftest/stage.py). Written 2026-10-30 before
running. Each case sits just inside or just outside a documented limit; the expected original behaviour is the
refusal catalogue `findings/2026-10-05-refusal-texts-and-conditions.md` (R-numbers) unless noted.

PORT = saves/fleet-port-antium-0734.SAV: Rome's army 0 (101,45, 3 moves) next to Rome's armies 12 (102,45) and 13
(102,44). The original's Join picks "the last own army one tile away" (R02), i.e. army 13, so the remake's
partner is 13 too. SPLIT = saves/fleet-split-antium-0734.SAV (fleets 2 and 5 side by side). BASE = Rome 270 BC.
"""
from pathlib import Path

from difftest.cases.orders230_b1 import BASE, case

ROOT = Path(__file__).resolve().parents[2]
PORT = str(ROOT / "saves/fleet-port-antium-0734.SAV")
SPLIT = str(ROOT / "saves/fleet-split-antium-0734.SAV")


def units(n, typ="li", troops=1000, q=6):
    return [(typ, troops, q)] * n


def staged(id, note, start, stage, *actions):
    c = case(id, note, *actions, start=start)
    c["stage"] = stage
    return c


JOIN = {"op": "join_armies", "army": 0, "partner": 13}
ROME_SLOTS = [(9, "li", 3000, 85)]

CASES = [
    staged("join-20-ok", "join 12 + 8 units: exactly 20 (accepted)", PORT,
           [("army_units", 0, units(12)), ("army_units", 13, units(8))], JOIN),
    staged("join-21-refused", "join 12 + 9 units: 21 (R03 refusal)", PORT,
           [("army_units", 0, units(12)), ("army_units", 13, units(9))], JOIN),
    staged("join-100k-exact", "join to exactly 100,000 troops (accepted)", PORT,
           [("army_units", 0, units(10, "hi", 6000, 7)), ("army_units", 13, units(6, "hi", 6000, 7) + [("li", 4000, 6)])], JOIN),
    staged("join-100k-over", "join to 102,000 troops (R04 refusal)", PORT,
           [("army_units", 0, units(10, "hi", 6000, 7)), ("army_units", 13, units(7, "hi", 6000, 7))], JOIN),
    staged("split-one-unit", "split an army of 1 unit (R01 refusal)", PORT,
           [("army_units", 0, units(1, "li", 4000))], {"op": "split_army", "army": 0, "units": [0]}),
    staged("transfer-into-20", "transfer a unit into an army of 20 units (R28 refusal)", PORT,
           [("army_units", 0, units(3)), ("army_units", 13, units(20))],
           {"op": "transfer_units", "army": 0, "partner": 13, "unit": 0}),
    staged("recruit-slot-40", "recruit with 39 slots queued: the 40th (accepted)", BASE,
           [("recruit_slots", 0, ROME_SLOTS * 39)], {"op": "recruit", "city": 85, "type": "li", "troops": 3000}),
    staged("recruit-slot-41", "recruit with 40 slots queued (R46 refusal)", BASE,
           [("recruit_slots", 0, ROME_SLOTS * 40)], {"op": "recruit", "city": 85, "type": "li", "troops": 3000}),
    staged("recruit-mob-100", "recruit at mobilisation 100 (R47 refusal)", BASE,
           [("mobilization", 0, 100)], {"op": "recruit", "city": 85, "type": "hi", "troops": 1200}),
    staged("recruit-no-money", "recruit 1,200 HI (120 talents) with 50 in the treasury (no catalogued refusal)", BASE,
           [("treasury", 0, 50)], {"op": "recruit", "city": 85, "type": "hi", "troops": 1200}),
    staged("fortify-full", "fortify Rome at 100 (R23 refusal)", BASE,
           [("city_fort", 85, 100)], {"op": "fortify", "city": 85, "points": 1}),
    staged("fortify-in-progress", "fortify Rome with an order in progress, word 578 (R24 refusal)", BASE,
           [("city_fort", 85, 578)], {"op": "fortify", "city": 85, "points": 1}),
    staged("join-fleets-101", "join fleets of 60 + 41 ships (R15 refusal)", SPLIT,
           [("fleet_ships", 2, 60), ("fleet_ships", 5, 41)], {"op": "join_fleets", "fleet": 2, "partner": 5}),
    staged("join-fleets-100", "join fleets of 60 + 40 ships (accepted)", SPLIT,
           [("fleet_ships", 2, 60), ("fleet_ships", 5, 40)], {"op": "join_fleets", "fleet": 2, "partner": 5}),
    staged("split-fleet-19", "split a fleet of 19 ships (R17 refusal)", PORT,
           [("fleet_ships", 2, 19)], {"op": "split_fleet", "fleet": 2, "ships": 5}),
    staged("merc-20-units", "hire a mercenary into an army of 20 units (R08 refusal)", BASE,
           [("army_units", 1, units(20))], {"op": "hire_mercenary", "army": 1, "pool": 25}),
    staged("merc-low-supplies", "hire a mercenary with 10 tons for 22,000 troops (R11 refusal)", BASE,
           [("army", 1, "supplies", 10)], {"op": "hire_mercenary", "army": 1, "pool": 25}),
]
