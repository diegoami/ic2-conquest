#!/usr/bin/env python3
"""T4 staging: SYNTHETIC edits of a save (labelled in every report): a fleet's condition, the season, an army aboard.

The fleet record's condition is at +20 (i16); the season is the tail record's 23rd short (`sav.parse`'s `tail_off` + 44: 0 Spring,
1 Summer, 2 Autumn, 3 Winter). `put_cargo` (t3_stage.py) puts an army aboard as the game's embark does (checked in T3).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "fleet-battles"))
from state import sav  # noqa: E402
from t3_stage import put_cargo  # noqa: E402,F401


def edit(src, dst, fleet=0, condition=None, season=None, supplies=None, cargo=None):
    """Write dst = src with the fleet's condition / supplies, the calendar's season and an army aboard (cargo = (army, units)) changed."""
    b = bytearray(Path(src).read_bytes())
    s = sav.parse(bytes(b))
    na = sav.i16(b, sav.ARMY_OFF)
    f = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN + 2 + fleet * sav.FLEET_LEN
    if condition is not None:
        struct.pack_into("<h", b, f + 20, condition)
    if supplies is not None:
        struct.pack_into("<h", b, f + 14, supplies)
    if season is not None:
        struct.pack_into("<h", b, s["tail_off"] + 44, season)
    Path(dst).write_bytes(bytes(b))
    if cargo:
        put_cargo(dst, dst, cargo[0], fleet, cargo[1])
    return dst


def roundtrip(src):
    """The edit with nothing changed must leave the file identical, and the condition, supplies and season edits change only their own field (checked for fleet 0, the armies, the map and the date; the cargo edit is `put_cargo`, checked in T3 against a natural embark)."""
    tmp = Path(src).with_name("rt.SAV")
    edit(src, tmp)
    assert tmp.read_bytes() == Path(src).read_bytes()
    edit(src, tmp, condition=45, season=3, supplies=7)
    a, b = sav.load(str(src)), sav.load(str(tmp))
    fa, fb = a["fleets"][0], b["fleets"][0]
    assert (fb["condition"], fb["supplies"], b["season"]) == (45, 7, 3)
    assert {k: v for k, v in fa.items() if k not in ("condition", "supplies")} == {k: v for k, v in fb.items() if k not in ("condition", "supplies")}
    assert a["armies"] == b["armies"] and a["map"] == b["map"] and a["week"] == b["week"] and a["year_bc"] == b["year_bc"]
    tmp.unlink()
    return "round-trip ok"


if __name__ == "__main__":
    print(roundtrip(ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"))
