#!/usr/bin/env python3
"""L1 staging (battles plan §3.3, §2): SYNTHETIC strategic edits of a save, labelled in every report, made BEFORE the attack so that the
battle then starts fresh with placement and initiative the game's own. **Army positions are never edited** (the marker rule is unverified):
adjacency comes from `Game.move`. Every edit writes only its own field; `edit(src, dst)` with no operation is byte-identical.

    ops = [("units", 0, [("hi", 6000, 6)]), ("morale", 0, 65), ("supplies", 0, 500), ("money", 0, 100),
           ("treasury", 6, 900), ("unity", 6, 400), ("relation", 0, 6, 3), ("moves", 0, 8), ("city", 12, {"loyalty": 50})]
    edit("in.sav", "out.sav", ops)

Operations (offsets: docs/sav-layout-notes.md):
  units army [(type, troops, quality[, label[, name]])]   army record slots 0..n-1 written whole (type li|hi|ar|lc|hc, quality 4..9, label 0
                                                          = regular; the name defaults to the slot's existing name when its type is unchanged, else "<ordinal> <kind>  Battalion");
                                                          slots n..19 get troops 0 (their other bytes are left as they are: an empty slot)
  morale army v      army +14        supplies army v   +10        money army v   +12 (the army purse)       moves army v   +6
  treasury n v       nation +0x438 (i32)                          unity n v      nation +0x440
  relation a b v     nation a's +0x26+2b AND nation b's +0x26+2a (the matrix is symmetric)
  city c {field: v}  city record fields: owner, allegiance, loyalty, supplies, fort, pop, max_pop, tribute
Position (x, y) of an army, and the map, are never touched.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state import sav  # noqa: E402

TYPES = {t: i for i, t in enumerate(sav.UNIT_TYPES)}
KIND = {"li": "Foot", "hi": "Guards", "ar": "Bowmen", "lc": "Lancers", "hc": "Dragoons"}
CITY_FIELDS = {"owner": 18, "allegiance": 20, "loyalty": 22, "supplies": 24, "fort": 26, "pop": 28, "max_pop": 30, "tribute": 32}
ARMY_FIELDS = {"moves": 6, "supplies": 10, "money": 12, "morale": 14}
STD = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}      # one standard battalion (DAT +0x1A; battles.md §4)


def _ordinal(n):
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def _offsets(b):
    na = sav.i16(b, sav.ARMY_OFF)
    off_f = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN
    nf = sav.i16(b, off_f)
    return {"na": na, "army0": sav.ARMY_OFF + 2, "nation0": off_f + 2 + nf * sav.FLEET_LEN}


def _army(b, a):
    o = _offsets(b)
    if not 0 <= a < o["na"]:
        raise ValueError("army %d out of range (%d records)" % (a, o["na"]))
    return o["army0"] + a * sav.ARMY_LEN


def _nation(b, n):
    if not 0 <= n < 16:
        raise ValueError("nation %d" % n)
    return _offsets(b)["nation0"] + n * sav.NATION_LEN


def set_units(b, army, units):
    base = _army(b, army)
    if len(units) > 20:
        raise ValueError("an army has 20 unit slots")
    for k, u in enumerate(units):
        typ, troops, q = u[0], u[1], u[2]
        label = u[3] if len(u) > 3 else 0
        if typ not in TYPES or not 0 < troops <= 32767 or not 0 <= q <= 9:
            raise ValueError("bad unit %r" % (u,))
        o = base + 16 + 32 * k
        old_typ, old_name = struct.unpack_from("<h", b, o + 2)[0], sav.cstr(bytes(b[o + 8:o + 32]))
        name = u[4] if len(u) > 4 else old_name if old_name and old_typ == TYPES[typ] else "%s %s  Battalion" % (_ordinal(k + 1), KIND[typ])
        if len(name.encode("latin1")) > 23:
            raise ValueError("name too long: " + name)
        struct.pack_into("<4h", b, o, label, TYPES[typ], troops, q)
        if name != old_name:       # an unchanged name keeps its bytes (the game leaves residue after the NUL)
            b[o + 8:o + 32] = name.encode("latin1").ljust(24, b"\0")
    for k in range(len(units), 20):
        struct.pack_into("<h", b, base + 16 + 32 * k + 4, 0)


def set_army_field(b, army, field, v):
    struct.pack_into("<h", b, _army(b, army) + ARMY_FIELDS[field], v)


def set_nation_i16(b, n, off, v):
    struct.pack_into("<h", b, _nation(b, n) + off, v)


def set_relation(b, a, c, v):
    set_nation_i16(b, a, 0x26 + 2 * c, v)
    set_nation_i16(b, c, 0x26 + 2 * a, v)


def set_city(b, c, fields):
    if not 0 <= c < sav.CITY_N:
        raise ValueError("city %d" % c)
    for k, v in fields.items():
        struct.pack_into("<h", b, sav.CITY_OFF + c * sav.CITY_LEN + CITY_FIELDS[k], v)


def apply(b, ops):
    for op in ops:
        k = op[0]
        if k == "units":
            set_units(b, op[1], op[2])
        elif k in ARMY_FIELDS:
            set_army_field(b, op[1], k, op[2])
        elif k == "treasury":
            struct.pack_into("<i", b, _nation(b, op[1]) + 0x438, op[2])
        elif k == "unity":
            set_nation_i16(b, op[1], 0x440, op[2])
        elif k == "relation":
            set_relation(b, op[1], op[2], op[3])
        elif k == "city":
            set_city(b, op[1], op[2])
        else:
            raise ValueError("unknown operation %r (armies' x, y are never edited)" % (k,))
    return b


def edit(src, dst, ops=()):
    b = bytearray(Path(src).read_bytes())
    apply(b, ops)
    Path(dst).write_bytes(bytes(b))
    return dst


def uniform(typ, n_units=1, size=1.0, q=6):
    """`n_units` units of one type at `size` x the standard battalion, quality q (the sweep's armies; B5)."""
    return [(typ, max(1, min(32767, round(STD[typ] * size))), q) for _ in range(n_units)]
