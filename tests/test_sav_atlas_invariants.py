#!/usr/bin/env python3
"""Offline test (no saves) for scripts/sav_atlas_invariants.py.

Builds a synthetic SAV (as tests.test_sav_atlas_coverage does): one army of Rome on a correct marker, a
city list in name order and a matching count; then breaks the marker, the order, the count, the fort encoding
and the army cell, and checks that each break is reported.

Run: python3 -m tests.test_sav_atlas_invariants   (exit 1 on a failure).
"""
import importlib.util
import struct
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def build(marker=200, names=(b"Alba", b"Roma"), count=2, fort=50, army_cell=3):
    b = bytearray(89600 + 11356)
    for i, nm in enumerate(names):                      # cities 0, 1 owned by Rome (owner 0), at (10+i, 5)
        o = 89600 + 34 * i
        b[o:o + len(nm)] = nm
        struct.pack_into("<hhh", b, o + 14, 10 + i, 5, 0)
        struct.pack_into("<h", b, o + 0x1A, fort)
        struct.pack_into("<h", b, 2 * ((10 + i) * 140 + 5), 20)
    for i in range(2, 334):                             # the other cities: owner 1, own tile, marker 21
        o = 89600 + 34 * i
        struct.pack_into("<hhh", b, o + 14, 0, i - 2, 1)
        struct.pack_into("<h", b, 2 * (0 * 140 + i - 2), 21)
    struct.pack_into("<h", b, 2 * (50 * 140 + 50), marker)
    army = bytearray(656)
    struct.pack_into("<hhhhh", army, 0, 50, 50, 0, 0, army_cell)
    struct.pack_into("<hhhh", army, 16, 0, 1, 1000, 5)
    b += struct.pack("<h", 1) + army + struct.pack("<h", 0)
    nations = bytearray(16 * 1172)
    for n in range(16):
        struct.pack_into("<h", nations, 1172 * n + 0x48, -1)
        struct.pack_into("<h", nations, 1172 * n + 0x444, -1)
    struct.pack_into("<hhh", nations, 0x48, 0, 1, -1)
    struct.pack_into("<hh", nations, 0x444, 0, count)
    struct.pack_into("<hh", nations, 1172 + 0x444, 2, 332)  # nation 1: capital city 2, 332 cities
    for e in range(332):
        struct.pack_into("<h", nations, 1172 + 0x48 + 2 * e, 2 + e)
    struct.pack_into("<h", nations, 1172 + 0x48 + 2 * 332, -1)
    b += nations + bytes(600) + struct.pack("<h", -1) + bytes(55)
    return bytes(b)


def main():
    spec = importlib.util.spec_from_file_location("inv_under_test", SCRIPTS / "sav_atlas_invariants.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    bad = lambda b, k: len(m.check(b)[k][1])
    good = build()
    cases = [("good save: army marker holds", bad(good, "army_marker") == 0),
             ("good save: city count holds", bad(good, "city_count") == 0),
             ("good save: every list in name order", m.check(good)["city_list_sorted"][1] == []),
             ("good save: fort and army cell hold", bad(good, "fort_encoding") == 0 and bad(good, "army_cell_terrain_or_city") == 0),
             ("pending fort 372 (3 + 72) holds", bad(build(fort=372), "fort_encoding") == 0),
             ("fort 9950 (99 + 50) is reported", bad(build(fort=9950), "fort_encoding") == 2),
             ("negative fort is reported", bad(build(fort=-5), "fort_encoding") == 2),
             ("an army cell of 40 off any city is reported", bad(build(army_cell=40), "army_cell_terrain_or_city") == 1),
             ("wrong marker owner is reported", bad(build(marker=201), "army_marker") == 1),
             ("names out of order are reported", 0 in m.check(build(names=(b"Roma", b"Alba")))["city_list_sorted"][1]),
             ("a wrong count is reported", bad(build(count=3), "city_count") == 1)]
    fails = 0
    for name, ok in cases:
        print(("ok   " if ok else "FAIL ") + name)
        fails += not ok
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
