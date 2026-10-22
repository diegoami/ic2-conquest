#!/usr/bin/env python3
"""Craft the SYNTHETIC start saves of run-exp-manual-gaps (one per item that needs one). Each edit is logged to
runs/experiments/data/run-exp-manual-gaps/staged-edits.jsonl and the save's SHA-256 to SAVES.sha256.

    python3 runs/experiments/manual_gaps/stage.py ITEM [ITEM ...]     # items: a1 a2 a5 a6 b9 b10 b11
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from craft import Sav, ROOT  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-manual-gaps"
RUN0 = ROOT / "saves/run0-start-AUTO0720-seed12345.SAV"
M133 = Path("/home/user/ic2-conquest/artifacts/run-exp-manual133/saves")


def done(s, name, why):
    out = s.write(name)
    h = hashlib.sha256(out.read_bytes()).hexdigest()
    with (DATA / "SAVES.sha256").open("a") as f:
        f.write(f"{h}  {name}\n")
    with (DATA / "staged-edits.jsonl").open("a") as f:
        f.write(json.dumps({"save": name, "base": s.src.name, "why": why, "sha256": h, "edits": s.edits}) + "\n")
    print(name, h[:12], len(s.edits), "edits")


def a1():
    s = Sav(RUN0)
    s.move_army(3, 101, 37)          # Carthage's army 3 (peace with Rome) next to Rome's army 0 at (100,37)
    done(s, "MG_A1_staged_carthage_army3_at_101_37.SAV", "A1: an army of a nation at peace next to Rome's army 0")


def a2():
    s = Sav(ROOT / "saves/fleets-adjacent-at-sea-0723.SAV")
    s.relation(1, 3, 0)              # Carthage (fleet 0) and Ptolemaic (fleet 1, the current seat) at peace, adjacent at sea
    done(s, "MG_A2_staged_ptolemaic_carthage_peace_0723.SAV", "A2: Ptolemaic's fleet 1 next to Carthage's fleet 0, relation set to peace")


def set_units(s, i, units):
    """units: [(type, troops, quality)] into slots 0.., the rest emptied; the map marker follows the new total."""
    o = s.army(i)
    for k in range(20):
        u = o + 16 + 32 * k
        if k < len(units):
            t, n, q = units[k]
            s.put(u + 2, t, what=f"army {i} slot {k} type")
            s.put(u + 4, n, what=f"army {i} slot {k} troops")
            s.put(u + 6, q, what=f"army {i} slot {k} quality")
        elif s.get(u + 4) != 0:
            s.put(u + 4, 0, what=f"army {i} slot {k} troops")
    total = sum(n for _, n, _ in units)
    owner = s.get(o + 4)
    marker = owner + (200 if total < 25000 else 216 if total < 50000 else 232)
    x, y = s.get(o), s.get(o + 2)
    if s.cell(x, y) != marker:
        s.put(s.cell_off(x, y), marker, what=f"map({x},{y}) army {i} marker for {total} troops")


def scale_units(s, i, factor):
    o = s.army(i)
    units = []
    for k in range(20):
        u = o + 16 + 32 * k
        n = s.get(u + 4)
        if n > 0:
            units.append((s.get(u + 2), int(n * factor), s.get(u + 6)))
    set_units(s, i, units)


def a5():
    s = Sav(M133 / "M133_session1_AUTO0722.SAV")
    set_units(s, 0, [(0, 3000, 6)])          # Rome's army 0: one light-infantry battalion of 3,000 (it should lose)
    scale_units(s, 9, 1 / 3)                 # Gaul's army 9 cut to a third (~14,900) so that armies(Gaul) < armies(Rome)
    done(s, "MG_A5_staged_rome0_3000li_gaul9_third_0722.SAV",
         "A5: D-LOSS set-up of findings/2026-10-05-battle-peace-offer.md on the M133 game: Rome's army 0 weak, Gaul's army 9 cut to a third")


def a6():
    s = Sav(RUN0)
    s.calendar(year_bc=251, season=3, week=11)
    done(s, "MG_A6a_staged_251bc_winter_w11.SAV", "A6a: 250 BC end")
    s = Sav(RUN0)
    s.treasury(0, -30000)
    done(s, "MG_A6b_staged_rome_treasury_-30000.SAV", "A6b: deposition for debt")
    s = Sav(RUN0)
    s.nation_field(0, 0x446, 334, "<h", "cities count")
    done(s, "MG_A6c_staged_rome_cities_count_334.SAV", "A6c: victory (Rome's city-count word 334, as EOG_victory_b1 of the end-of-game finding)")


def b9():
    s = Sav(RUN0)
    s.move_army(1, 107, 67)          # Rome's army 1 next to Agrigentum (Carthage, peace), no own city within one tile
    done(s, "MG_B9_staged_rome_army1_at_107_67_agrigentum.SAV", "B9: Rome's army 1 next to a foreign city at peace (Agrigentum, Carthage)")


STORM_TILES = [(80, 44), (80, 48), (80, 52), (83, 42), (83, 46), (84, 44)]   # calm sea, every neighbour sea, nearest city 6-9 tiles


def b10():
    s = Sav(ROOT / "saves/fleet-split-antium-0734.SAV")
    for i, (x, y) in enumerate(STORM_TILES):
        o = s.fleet(i)
        if s.get(o + 10) >= 0:           # under construction at (0,0): no marker on the map yet; launch it at the tile
            assert s.cell(x, y) == 0
            s.put(o, x, what=f"fleet {i} x")
            s.put(o + 2, y, what=f"fleet {i} y")
            s.put(o + 10, -1, what=f"fleet {i} countdown (launched)")
            s.put(o + 24, 0, what=f"fleet {i} covered cell")
        else:
            s.move_fleet(i, x, y)
        s.fleet_field(i, 8, 0, "owner (Rome)")
        s.fleet_field(i, 18, 50, "ships")
        s.fleet_field(i, 20, 100, "condition")
        s.fleet_field(i, 14, 400, "supplies")
        s.fleet_field(i, 16, 0, "money")
        s.fleet_field(i, 22, -1, "army aboard")
        s.fleet_field(i, 4, -1, "route x")
        s.put(s.cell_off(x, y), 332, what=f"map({x},{y}) <- Rome fleet marker (50 ships: 0 + 332)")
    s.calendar(season=3, week=1)     # Winter week 1, 270 BC
    done(s, "MG_B10_staged_6_rome_fleets_at_sea_winter_270.SAV",
         "B10: six Rome fleets of 50 ships, condition 100, supplies 400, on calm open sea >2 tiles from any city, Winter week 1")


def b11():
    s = Sav(RUN0)
    s.relation(1, 8, -18)            # Carthage's only war (Celtiberia) ended, with the -18 cooldown so Celtiberia is no war target
    done(s, "MG_B11_staged_carthage_celtiberia_-18.SAV",
         "B11: Carthage at war with nobody; its other neighbours are excluded (Numidia ally, Ptolemaic -10, Celtiberia -18): Rome is its only possible target")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        globals()[a]()
