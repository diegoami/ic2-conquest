#!/usr/bin/env python3
"""Offline test (no Wine) for scripts/sav_atlas_coverage.py.

Checks that the shipped field map tiles every record, that a removed row, an
overlapping row and a nation range unlike nation-matrix-v2 are each reported,
and that framing accepts a synthetic minimal SAV (with and without the battle
block) and rejects a truncated one, a trailing byte and a bad news index.

Run: python3 -m tests.test_sav_atlas_coverage   (exit 1 on a failure).
"""
import copy
import importlib.util
import struct
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sav_atlas_coverage.py"


def _module():
    spec = importlib.util.spec_from_file_location("sav_atlas_under_test", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def synthetic(m, armies=1, fleets=1, news_index=0, battle=False):
    b = bytearray(89600 + 11356)
    b += struct.pack("<h", armies) + bytes(656 * armies)
    b += struct.pack("<h", fleets) + bytes(26 * fleets)
    b += bytes(16 * 1172 + 600)
    b += struct.pack("<h", news_index) + bytes(61 * (news_index + 1))
    b += bytes(54) + bytes([1 if battle else 0])
    if battle:
        b += bytes(2105)
    return bytes(b)


def main():
    m = _module()
    fails = []

    def check(cond, what):
        print(("ok   " if cond else "FAIL ") + what)
        if not cond:
            fails.append(what)

    rows = m.load_map()
    check(m.static_check(rows) == [], "shipped field map tiles every record and matches nation-matrix-v2")
    gap = [r for r in rows if r["field_id"] != "FLEET.moves"]
    check(any("fleet: gap" in e for e in m.static_check(gap)), "a removed row is reported as a gap")
    over = copy.deepcopy(rows)
    next(r for r in over if r["field_id"] == "CITY.x")["last"] += 2
    check(any("city: overlap" in e for e in m.static_check(over)), "an overlapping row is reported")
    split = copy.deepcopy(rows)
    next(r for r in split if r["field_id"] == "NATION.unknown27")["last"] -= 1
    next(r for r in split if r["field_id"] == "NATION.hints")["first"] -= 1
    check(any("nation-matrix" in e for e in m.static_check(split)), "a nation range unlike the matrix is reported")

    for kw in ({}, {"battle": True}, {"armies": 0, "fleets": 0, "news_index": -1}):
        f = m.scan(synthetic(m, **kw), rows)
        check(f["physical_coverage"] and f["battle_flag"] == (1 if kw.get("battle") else 0),
              f"synthetic SAV {kw or 'default'} frames to EOF with full coverage")
    unknown = sum(f["bytes_by_semantic"].values()) and f["bytes_by_semantic"]["UNKNOWN"]
    check(unknown == 16 * 31, "UNKNOWN bytes counted as 31 per nation record (496)")
    good = synthetic(m)
    for bad, what in ((good[:-1], "truncated"), (good + b"\0", "trailing byte")):
        try:
            m.frame(bad); check(False, f"{what} file rejected")
        except ValueError:
            check(True, f"{what} file rejected")
    try:
        m.frame(synthetic(m, news_index=40)); check(False, "news index 40 rejected")
    except ValueError:
        check(True, "news index 40 rejected")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
