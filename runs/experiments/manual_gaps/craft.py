#!/usr/bin/env python3
"""Save edits for run-exp-manual-gaps (SYNTHETIC: every crafted save is labelled as such in the README and the csv).

Offsets: state/sav.py (from docs/sav-layout-notes.md and run-exp-sav-atlas107/field-map-v12.csv). Map cell (x, y) is the i16 at
(x*140 + y)*2; an army marker is owner + (troops<25000 ? 200 : troops<50000 ? 216 : 232), a fleet marker owner + (ships<25 ? 300 :
ships<50 ? 316 : 332); the terrain under a marker is the record's covered-cell field (army +8, fleet +24).
Outputs are created exclusively (never overwritten, rule 6).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state import sav  # noqa: E402

ART = Path("/home/user/ic2-conquest/artifacts/run-exp-manual-gaps")
SAVES = ART / "saves"


class Sav:
    def __init__(self, src):
        self.src = Path(src)
        self.b = bytearray(self.src.read_bytes())
        self.edits = []
        self._frame()

    def _frame(self):
        s = sav.parse(bytes(self.b))
        self.s = s
        self.na = sav.i16(self.b, sav.ARMY_OFF)
        self.a0 = sav.ARMY_OFF + 2
        self.nf = sav.i16(self.b, self.a0 + self.na * sav.ARMY_LEN)
        self.f0 = self.a0 + self.na * sav.ARMY_LEN + 2
        self.n0 = self.f0 + self.nf * sav.FLEET_LEN
        self.tail = s["tail_off"]

    # ---- raw ----
    def get(self, off, fmt="<h"):
        return struct.unpack_from(fmt, self.b, off)[0]

    def put(self, off, value, fmt="<h", what=""):
        old = self.get(off, fmt)
        struct.pack_into(fmt, self.b, off, value)
        self.edits.append({"what": what, "offset": off, "old": old, "new": value})

    # ---- records ----
    def army(self, i):
        return self.a0 + i * sav.ARMY_LEN

    def fleet(self, i):
        return self.f0 + i * sav.FLEET_LEN

    def nation(self, n):
        return self.n0 + n * sav.NATION_LEN

    def city(self, c):
        return sav.CITY_OFF + c * sav.CITY_LEN

    def cell_off(self, x, y):
        return (x * 140 + y) * 2

    def cell(self, x, y):
        return self.get(self.cell_off(x, y))

    # ---- edits ----
    def move_army(self, i, x, y):
        o = self.army(i)
        ox, oy, owner = self.get(o), self.get(o + 2), self.get(o + 4)
        covered = self.get(o + 8)
        marker = self.cell(ox, oy)
        assert 200 <= marker < 248, (ox, oy, marker)
        new_under = self.cell(x, y)
        assert 2 <= new_under <= 11, f"target {x},{y} is not free land: {new_under}"
        self.put(self.cell_off(ox, oy), covered, what=f"map({ox},{oy}) <- covered terrain of army {i}")
        self.put(self.cell_off(x, y), marker, what=f"map({x},{y}) <- army {i} marker")
        self.put(o, x, what=f"army {i} x")
        self.put(o + 2, y, what=f"army {i} y")
        self.put(o + 8, new_under, what=f"army {i} covered cell")

    def move_fleet(self, i, x, y):
        o = self.fleet(i)
        ox, oy = self.get(o), self.get(o + 2)
        covered = self.get(o + 24)
        marker = self.cell(ox, oy)
        assert 300 <= marker < 348, (ox, oy, marker)
        new_under = self.cell(x, y)
        assert new_under in (0, 1), f"target {x},{y} is not free sea: {new_under}"
        self.put(self.cell_off(ox, oy), covered, what=f"map({ox},{oy}) <- covered sea of fleet {i}")
        self.put(self.cell_off(x, y), marker, what=f"map({x},{y}) <- fleet {i} marker")
        self.put(o, x, what=f"fleet {i} x")
        self.put(o + 2, y, what=f"fleet {i} y")
        self.put(o + 24, new_under, what=f"fleet {i} covered cell")

    def relation(self, a, b, value):
        self.put(self.nation(a) + 0x26 + 2 * b, value, what=f"relation {sav.NATIONS[a]}->{sav.NATIONS[b]}")
        self.put(self.nation(b) + 0x26 + 2 * a, value, what=f"relation {sav.NATIONS[b]}->{sav.NATIONS[a]}")

    def nation_field(self, n, off, value, fmt="<h", name=""):
        self.put(self.nation(n) + off, value, fmt, what=f"{sav.NATIONS[n]} {name or hex(off)}")

    def treasury(self, n, v):
        self.nation_field(n, 0x438, v, "<i", "treasury")

    def wealth(self, n, v):
        self.nation_field(n, 0x430, v, "<i", "wealth")

    def unity(self, n, v):
        self.nation_field(n, 0x440, v, "<h", "unity")

    def mobilization(self, n, v):
        self.nation_field(n, 0x442, v, "<h", "mobilization")

    def army_field(self, i, off, v, name):
        self.put(self.army(i) + off, v, what=f"army {i} {name}")

    def fleet_field(self, i, off, v, name):
        self.put(self.fleet(i) + off, v, what=f"fleet {i} {name}")

    def calendar(self, year_bc=None, season=None, week=None):
        if week is not None:
            self.put(self.tail + 40, week, what="calendar week")
        if year_bc is not None:
            self.put(self.tail + 42, year_bc, what="calendar year BC")
        if season is not None:
            self.put(self.tail + 44, season, what="calendar season")

    def write(self, name):
        SAVES.mkdir(parents=True, exist_ok=True)
        out = SAVES / name
        sav.parse(bytes(self.b))         # still parses
        with open(out, "xb") as fh:
            fh.write(bytes(self.b))
        return out


def free_neighbours(s, x, y, land=True):
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                c = s.cell(x + dx, y + dy)
                if (2 <= c <= 11) if land else c in (0, 1):
                    out.append((x + dx, y + dy, c))
    return out
