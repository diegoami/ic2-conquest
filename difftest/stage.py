"""Staged start saves for limit and refusal cases (#230): a copy of a fixture save with a few fields edited.

Each edit is a tuple; `apply(src, edits, out)` writes the staged copy once (an existing `out` is reused only if it
holds exactly these edits, recorded in `out`.json). Offsets follow state/sav.py:
- ("army_units", army, [(type, troops, quality), ...])  the army's 20 unit slots (unused slots zeroed)
- ("army", army, field, value)    field in x, y, owner, moves, cell, supplies, money, morale (8 words at +0)
- ("treasury", nation, value)     int32 at nation +0x438
- ("mobilization", nation, value) word at nation +0x442
- ("recruit_slots", nation, [(state, type, troops, city), ...])  the 40 slots at nation +0x2E4 (others zeroed)
- ("city_fort", city, word)       the fortification word (a value above 100 encodes an order in progress)
- ("fleet_ships", fleet, ships)   word 9 of the 26-byte fleet record

Only these words change: the staged save is otherwise the fixture, so both games start from identical bytes.
"""
import json
import struct
from pathlib import Path

from state import sav

ARMY_FIELDS = ("x", "y", "owner", "moves", "cell", "supplies", "money", "morale")


def offsets(b):
    na = struct.unpack_from("<h", b, sav.ARMY_OFF)[0]
    a = sav.ARMY_OFF + 2
    f = a + na * sav.ARMY_LEN
    nf = struct.unpack_from("<h", b, f)[0]
    return a, f + 2, f + 2 + nf * sav.FLEET_LEN


def edit(b, e):
    a, f, n = offsets(b)
    kind = e[0]
    if kind == "army_units":
        off = a + e[1] * sav.ARMY_LEN
        b[off + 16:off + sav.ARMY_LEN] = bytes(sav.ARMY_LEN - 16)
        for k, (typ, troops, q) in enumerate(e[2]):
            u = off + 16 + 32 * k
            struct.pack_into("<4h", b, u, 0, sav.UNIT_TYPES.index(typ), troops, q)
            name = f"S{e[1]}U{k}".encode()
            b[u + 8:u + 8 + len(name)] = name
    elif kind == "army":
        struct.pack_into("<h", b, a + e[1] * sav.ARMY_LEN + 2 * ARMY_FIELDS.index(e[2]), e[3])
    elif kind == "treasury":
        struct.pack_into("<i", b, n + e[1] * sav.NATION_LEN + 0x438, e[2])
    elif kind == "mobilization":
        struct.pack_into("<h", b, n + e[1] * sav.NATION_LEN + 0x442, e[2])
    elif kind == "recruit_slots":
        base = n + e[1] * sav.NATION_LEN + 0x2E4
        b[base:base + 320] = bytes(320)
        for k, (st, typ, troops, city) in enumerate(e[2]):
            struct.pack_into("<4h", b, base + 8 * k, st, sav.UNIT_TYPES.index(typ), troops, city)
    elif kind == "city_fort":
        struct.pack_into("<h", b, sav.CITY_OFF + e[1] * sav.CITY_LEN + 14 + 12, e[2])
    elif kind == "fleet_ships":
        struct.pack_into("<h", b, f + e[1] * sav.FLEET_LEN + 18, e[2])
    else:
        raise ValueError(kind)


def apply(src, edits, out):
    out = Path(out)
    rec = {"source": str(src), "edits": [list(map(lambda x: x if not isinstance(x, tuple) else list(x), e)) for e in edits]}
    meta = out.with_suffix(".json")
    if out.exists():
        if json.loads(meta.read_text()) != json.loads(json.dumps(rec)):
            raise SystemExit(f"{out} exists with other edits; refusing to overwrite")
        return out
    b = bytearray(Path(src).read_bytes())
    for e in edits:
        edit(b, e)
    sav.parse(bytes(b))                     # the staged save must still parse
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(b))
    meta.write_text(json.dumps(rec, indent=1))
    return out
