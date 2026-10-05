#!/usr/bin/env python3
"""L1 staging (battles plan §3.3, §2): SYNTHETIC strategic edits of a save, labelled in every report, made BEFORE the attack so that the
battle then starts fresh with placement and initiative the game's own. **Army positions are never edited** (the marker rule is unverified):
adjacency comes from `Game.move`. Every edit writes only its own field; `edit(src, dst)` with no operation is byte-identical.

    ops = [("units", 0, [("hi", 6000, 6)]), ("morale", 0, 65), ("supplies", 0, 500), ("money", 0, 100),
           ("treasury", 6, 900), ("unity", 6, 400), ("relation", 0, 6, 3), ("moves", 0, 8), ("city", 12, {"loyalty": 50})]
    edit("in.sav", "out.sav", ops)

Operations (offsets: docs/sav-layout-notes.md):
  units army [(type, troops, quality[, label[, name]])]   army record slots 0..n-1 written whole (type li|hi|ar|lc|hc, quality 0..9, label 0
                                                          = regular; the name defaults to the slot's existing name when its type is unchanged, else "<ordinal> <kind>  Battalion");
                                                          slots n..19 get troops 0 (their other bytes are left as they are: an empty slot)
  owner army v       army +4 (B16: gives an existing army to another nation; position and map untouched)
  morale army v      army +14        supplies army v   +10        money army v   +12 (the army purse)       moves army v   +6
  treasury n v       nation +0x438 (i32)                          unity n v      nation +0x440
  ncities n v        nation +0x446 (the count word only, B16)
  relation a b v     nation a's +0x26+2b AND nation b's +0x26+2a (the matrix is symmetric)
  city c {field: v}  city record fields: owner, allegiance, loyalty, supplies, fort, pop, max_pop, tribute
Position (x, y) of an army, and the map, are never touched.

L2 (B3): `block_edit(b, ops)` edits the battle block (block 12) of a save written INSIDE a battle (a `BATTLEnn.SAV` of the lab build, or a
File > Save As at a human phase): the attacker's slots follow its army's unit order but the AI (defender) side is RE-SORTED at battle start and the
mapping is not stored (B2), so a slot edit is MIRRORED into the army's unit by default (`consistent=True`: type, troops, quality, label, name)
into the unit found by the slot's OLD (name, type) among that army's units: exactly one match is required, and a slot with no match or with
several (duplicate names) raises ValueError instead of guessing (pass consistent=False to edit the slot only) and the grid cell is kept in step (old cell emptied, new cell = the sprite).
    ("slot", k, {"x": 6, "y": 5, "troops": 3000, "quality": 6, "morale": 70, "type": "hi", "merc": 0, "state": 0, "ammo": 0, "target": -1,
                  "name": "..."}[, consistent])        ("grid", x, y, value) raw grid word      ("header", {"x2": 1, ...})
Not edited by default: positions of strategic armies (never), the half-round counter.
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
ARMY_FIELDS = {"owner": 4, "moves": 6, "supplies": 10, "money": 12, "morale": 14}
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


def _block_off(b):
    t = sav.parse(bytes(b))["tail_off"]
    if b[t + 54] == 0:
        raise ValueError("this save has no battle block (battle flag 0): block edits need a save written inside a battle")
    return t + 55


def sprite_value(side, typ, troops):
    """The grid word of a unit [D, B2]: side*20 + 3*type + size class; class 0 below std/3, 1 below 2*std/3, else 2 (std: STD)."""
    t = typ if isinstance(typ, str) else sav.UNIT_TYPES[typ]
    std = STD[t]
    cls = min(2, troops // (std // 3))          # [R-code] decompiled rule; B2's earlier `3*troops < std` agrees on every troop count seen in the series
    return side * 20 + 3 * sav.UNIT_TYPES.index(t) + cls


def block_edit(b, ops):
    """Apply L2 operations to a bytearray holding a whole save with a battle block; returns b. See the module doc."""
    from state import battle_block as BB
    o = _block_off(b)
    for op in ops:
        k = op[0]
        blk = BB.parse_block(bytes(b[o:o + BB.BLOCK_LEN]))
        if k == "header":
            bad = set(op[1]) - {"attacker_army", "defender_army", "x2", "y1", "half_round"}
            if bad:
                raise ValueError("unknown header field(s) %s" % sorted(bad))
            blk.update({f: v for f, v in op[1].items()})
            b[o:o + BB.BLOCK_LEN] = BB.encode_block(blk)
        elif k == "grid":
            if not (0 <= op[1] < BB.GRID_W and 0 <= op[2] < BB.GRID_H):
                raise ValueError("grid cell (%s,%s) is outside the %d x %d grid" % (op[1], op[2], BB.GRID_W, BB.GRID_H))
            if not -32768 <= op[3] <= 32767:
                raise ValueError("grid word %r does not fit an i16" % (op[3],))
            struct.pack_into("<h", b, o + BB.HEADER_LEN + BB.SLOT_LEN * BB.N_SLOTS + 2 * BB.cell(op[1], op[2]), op[3])
        elif k == "slot":
            n, fields = op[1], dict(op[2])
            consistent = op[3] if len(op) > 3 else True
            if not 0 <= n < BB.N_SLOTS or not set(fields) <= set(BB.SLOT_FIELDS) | {"name"}:
                raise ValueError("bad slot edit %r" % (op,))
            old = blk["slots"][n]
            new = dict(old)
            new.update(fields)
            if new["x"] != old["x"] or new["y"] != old["y"] or new["type"] != old["type"] or new["troops"] != old["troops"]:
                g = blk["grid"]
                if old["alive"] and g[BB.cell(old["x"], old["y"])] == sprite_value(old["side"], old["type"], old["troops"]):
                    g[BB.cell(old["x"], old["y"])] = BB.EMPTY
                if new["troops"] > 0:
                    if not (0 <= new["x"] < BB.GRID_W and 0 <= new["y"] < BB.GRID_H):
                        raise ValueError("cell (%s,%s) is outside the 14 x 12 grid" % (new["x"], new["y"]))
                    g[BB.cell(new["x"], new["y"])] = sprite_value(old["side"], new["type"], new["troops"])
            new["alive"] = new["troops"] > 0
            blk["slots"][n] = new
            b[o:o + BB.BLOCK_LEN] = BB.encode_block(blk)
            if consistent and any(f in fields for f in ("type", "troops", "quality", "merc", "name")):
                army = blk["attacker_army"] if n < 20 else blk["defender_army"]
                u = _army_unit_of_slot(b, army, old)
                set_units_field(b, army, u, {f: new[f] for f in ("type", "troops", "quality", "merc", "name") if f in fields})
        else:
            raise ValueError("unknown block operation %r" % (k,))
    return b


def _army_unit_of_slot(b, army, old_slot):
    """The index of the strategic army's unit that a battle slot belongs to, matched by the slot's (name, type) BEFORE the edit; exactly one match
    or ValueError (the defender's slot order differs from its army's unit order, so an index would be wrong)."""
    base = _army(b, army)
    hits = []
    for k in range(20):
        o = base + 16 + 32 * k
        typ, troops = struct.unpack_from("<2h", b, o + 2)[0], struct.unpack_from("<h", b, o + 4)[0]
        if troops > 0 and sav.cstr(bytes(b[o + 8:o + 32])) == old_slot["name"] and sav.UNIT_TYPES[typ] == old_slot["type"]:
            hits.append(k)
    if len(hits) != 1:
        raise ValueError("slot %d (%r, %s) matches %d units of army %d: cannot mirror the edit; use consistent=False"
                         % (old_slot["slot"], old_slot["name"], old_slot["type"], len(hits), army))
    return hits[0]


def set_units_field(b, army, unit, fields):
    """Edit fields of ONE unit slot of a strategic army (type, troops, quality, merc, name), nothing else."""
    base = _army(b, army) + 16 + 32 * unit
    if "type" in fields:
        typ = fields["type"]
        struct.pack_into("<h", b, base + 2, TYPES[typ] if isinstance(typ, str) else typ)
    if "troops" in fields:
        struct.pack_into("<h", b, base + 4, fields["troops"])
    if "quality" in fields:
        struct.pack_into("<h", b, base + 6, fields["quality"])
    if "merc" in fields:
        struct.pack_into("<h", b, base, fields["merc"])
    if "name" in fields and sav.cstr(bytes(b[base + 8:base + 32])) != fields["name"]:
        b[base + 8:base + 32] = fields["name"].encode("latin1").ljust(24, b"\0")[:24]


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
        elif k == "ncities":              # the nation's city-count word (+0x446, `cities_count`); the city list and the cities' owner fields are not touched (B16)
            set_nation_i16(b, op[1], 0x446, op[2])
        elif k == "relation":
            set_relation(b, op[1], op[2], op[3])
        elif k == "city":
            set_city(b, op[1], op[2])
        else:
            raise ValueError("unknown operation %r (armies' x, y are never edited)" % (k,))
    return b


def edit(src, dst, ops=(), block=()):
    """dst = src with the L1 `ops` and then the L2 battle-block `block` operations applied."""
    b = bytearray(Path(src).read_bytes())
    apply(b, ops)
    if block:
        block_edit(b, block)
    Path(dst).write_bytes(bytes(b))
    return dst


def uniform(typ, n_units=1, size=1.0, q=6):
    """`n_units` units of one type at `size` x the standard battalion, quality q (the sweep's armies; B5)."""
    return [(typ, max(1, min(32767, round(STD[typ] * size))), q) for _ in range(n_units)]
