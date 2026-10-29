"""#233 pre-registration (written 2026-10-28, before any trial ran).

Each scenario is played once per seed in each game from the same start save. Metrics are computed from the start
and final saves only. Test: two-sided permutation test on the difference of means per metric, Holm-corrected over
all metrics of all scenarios, ALPHA = 0.05 (difftest/stats.py). Sample sizes are fixed here; a scenario that needs
more seeds gets a NEW scenario id with its own pre-registration, never a quiet extension.

- naval30: fixture `saves/fleets-adjacent-at-sea-0723.SAV` (Carthage and Ptolemaic human, at war). Ptolemaic
  fleet 1 (70 ships, condition 63) attacks the adjacent Carthaginian fleet 0 (90 ships, condition 74). Instant in
  both games. Seeds 1-30.
- storm30: fixture `saves/fleet-port-antium-0734.SAV` (Rome, Autumn week 5, 270 BC). Rome's fleet 2 (30 ships,
  condition 97, empty) sails from Antium (101,46) to calm open sea (97,48), then End turn. Seeds 1-30.
- siege10: army 0 next to Felsina (Gaul, at war) besieges it. Start fixture `siege-felsina-start.SAV`, built once
  in the original (BASE.SAV, seed 12345: army 0 to (99,34), End turn, then to Felsina's neighbourhood) and kept
  with the run. The siege may be deterministic; 10 seeds check that. Seeds 1-10.

ADDED 2026-10-29, after storm30 ran (its storm damage could not be compared: Carthage's fleet hunted and sank
Rome's fleet in 30 of 30 original trials and never moved in the remake; `findings/2026-10-29-ai-fleet-hunt-absent-
in-remake233.md`). Pre-registered before running:
- storm30b: storm30 from a staged copy of the fixture with Rome-Carthage set to peace (0) both ways, so no
  nation at war with Rome has a fleet within reach; the staged save is written once by stage_storm_peace() and
  kept with the run. Same order, metrics and seeds 1-30.

ADDED 2026-10-30, before running (after the #232 AI-free game showed 520 rough-sea cells painted in the remake and none in
the original over one week, a single draw):
- weather30: BASE.SAV (Rome, 270 BC Spring week 1), one End turn; metrics: the number of rough-sea cells (map code 1)
  after it, and whether any is painted. Seeds 1-30. The original's rule (research feature inventory E07): 20 fixed sea
  regions rolled each tick, spring 1/15 (radius 4) before week 6.
"""
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
ALPHA = 0.05
SIEGE_START = str(ROOT / "artifacts/run-exp-diff084-stats/fixtures/siege-felsina-start.SAV")


def naval(before, after):
    # Fleets are matched by owner (one fleet each): a sunk fleet's record is dropped by the remake's export
    # and kept with owner -1 by the original, so record indexes are not stable across the battle.
    by_owner = lambda s, n: next((f for f in s["fleets"] if f["owner"] == n and f["ships"] > 0), None)
    a0, d0 = by_owner(before, 3), by_owner(before, 1)
    a1, d1 = by_owner(after, 3), by_owner(after, 1)
    alive = lambda f: int(f is not None)
    return {"attacker_survives": alive(a1), "defender_survives": alive(d1),
            "attacker_ships_lost": a0["ships"] - (a1["ships"] if alive(a1) else 0),
            "defender_ships_lost": d0["ships"] - (d1["ships"] if alive(d1) else 0),
            "attacker_condition": a1.get("condition") if alive(a1) else None,
            "defender_condition": d1.get("condition") if alive(d1) else None}


def storm(before, after):
    f0, f1 = before["fleets"][2], after["fleets"][2]
    alive = int(f1["owner"] == 0 and f1["ships"] > 0)
    return {"fleet_survives": alive, "ships_lost": f0["ships"] - (f1["ships"] if alive else 0),
            "condition_lost": (f0["condition"] - f1["condition"]) if alive else None,
            "at_target": int(alive and (f1["x"], f1["y"]) == (97, 48))}


def weather(before, after):
    cells = sum(1 for v in after["map"] if v == 1)
    return {"rough_cells": cells, "any_rough": int(cells > 0)}


def siege(before, after):
    a0, a1 = before["armies"][0], after["armies"][0]
    c0, c1 = before["cities"][79], after["cities"][79]
    return {"captured": int(c1["owner"] == 0), "army_troops_lost": a0["troops"] - a1["troops"],
            "loyalty_change": c1["loyalty"] - c0["loyalty"], "fort_change": c1["fort"] - c0["fort"],
            "pop_change": c1["pop"] - c0["pop"]}


STORM_PEACE = str(ROOT / "artifacts/run-exp-diff084-stats/fixtures/fleet-port-antium-peace-carthage.SAV")


def stage_storm_peace():
    """Write STORM_PEACE once: the storm fixture with nations 0 and 1 at relation 0 both ways (state/sav.py layout:
    relations are 16 words at +0x26 of each 1,172-byte nation record)."""
    import sys
    sys.path.insert(0, str(ROOT))
    from difftest.tactical import _offsets
    out = Path(STORM_PEACE)
    if out.exists():
        return out
    b = bytearray((ROOT / "saves/fleet-port-antium-0734.SAV").read_bytes())
    _, _, n = _offsets(b)
    for me, them in ((0, 1), (1, 0)):
        struct.pack_into("<h", b, n + me * 1172 + 0x26 + 2 * them, 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(b))
    return out


SCENARIOS = [
    {"id": "naval30", "start": str(ROOT / "saves/fleets-adjacent-at-sea-0723.SAV"),
     "actions": [{"op": "attack_fleet", "fleet": 1, "target": 0}], "metrics": naval, "seeds": list(range(1, 31))},
    {"id": "storm30", "start": str(ROOT / "saves/fleet-port-antium-0734.SAV"),
     "actions": [{"op": "move_fleet", "fleet": 2, "x": 97, "y": 48}, {"op": "end_turn"}], "metrics": storm,
     "seeds": list(range(1, 31))},
    {"id": "siege10", "start": SIEGE_START,
     "actions": [{"op": "besiege", "army": 0, "city": 79}], "metrics": siege, "seeds": list(range(1, 11))},
    {"id": "weather30", "start": str(Path.home() / "ic2-work/fixtures/BASE.SAV"), "actions": [{"op": "end_turn"}],
     "metrics": weather, "seeds": list(range(1, 31))},
    {"id": "storm30b", "start": STORM_PEACE,
     "actions": [{"op": "move_fleet", "fleet": 2, "x": 97, "y": 48}, {"op": "end_turn"}], "metrics": storm,
     "seeds": list(range(1, 31))},
]
