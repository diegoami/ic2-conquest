"""Decoder of the battle block (block 12 of a save written inside a tactical battle; the same bytes are in the game's memory) - battles plan B2.

Layout (2,105 bytes after the 55-byte trailer; `docs/sav-layout-notes.md` §Block 12; decoded in B2 from the lab series of
`1_rome_270_winter_11.sav`, see `findings/2026-10-04-tactical-battle-sweep.md`; **Wine-only**, tags: [O] observed, [D] derived, [?] unknown):

  header, 9 bytes, `<hhhBh`:
    +0  i16  attacker's strategic army index (Rome's army 0)                     [O] 0 in every battle seen
    +2  i16  defender's strategic army index (Gaul's army 10)                    [O] 10 in every battle seen. A header field, NOT a per-slot word and not a
                                                                                  unit index. (The research request's "word +2" is the SLOT word index 2 =
                                                                                  slot byte +4, the origin label below: it is that field the plan's hypothesis
                                                                                  about a link to the army's unit index was tested on, and rejected.)
    +4  i16  unknown (`x2`): 1, 0, 0, 1, 0, 1, 0, 1 ... from the 4th half-round on 1 at even half-rounds   [?]
    +6  u8   unknown (`y1`): 0 for the first two saves, then 1                                              [?]
    +7  i16  half-round counter = the BATTLEnn number of the lab build (1, 2, 3 ...)                        [O]
  40 slots of 44 bytes (slots 0-19 the attacker's army, 20-39 the defender's), each `<10h` + a 24-byte name:
    +0  x (0..13)           +2  y (0..11)           [O] grid index = x*12 + y
    +4  merc label (0 regular, 11 Gallic ...)       [O] the strategic unit's label
    +6  type 0 li 1 hi 2 ar 3 lc 4 hc               [O]
    +8  troops (<= 0 empty / dead)                  [O] equals the strategic unit's troops at the start
    +10 quality                                     [O]
    +12 battle-local morale (60..99 seen)           [O] initial = clamp(Random(q*4) + army morale, 60, 90) (+3 for the computer side) [R]
    +14 `state` = slot word 7, moves left this half-round [R-code]: 0..6 seen (LC 6, HC 5)   [D] the type's allowance (HI 2, LI/Ar 4, HC 5, LC 6) refilled when the side starts a half-round; exact
                                                    semantics [?] (Gaul's LI read 1 at the second file)
    +16 `ammo` = slot word 8, SHOTS LEFT FOR THE BATTLE [R-code]: li 7, ar 25, lc 9, hc 0, hi 0 at the start; falls when the unit shoots (ar -4 per volley)   [D]
    +18 `target` = slot word 9, the MELEE TARGET slot [R-code] (a BATTLEnn snapshot is taken before the side's melee, so it holds the targets of the melee that follows; -1 none)                                          [D]
    +20 name (NUL padded, 24 bytes)
  grid: 14 x 12 int16 (336 bytes), index x*12 + y: 50 = empty, else side*20 + 3*type + size class (0..2) = the SPRITE of the unit. It carries
        no terrain in any battle seen and is [D] derived from the slots (checked on every save of the series).
"""
import struct
from pathlib import Path

from . import sav

HEADER_LEN, SLOT_LEN, N_SLOTS, GRID_W, GRID_H = 9, 44, 40, 14, 12
BLOCK_LEN = HEADER_LEN + SLOT_LEN * N_SLOTS + GRID_W * GRID_H * 2          # 2105
EMPTY = 50
TYPES = sav.UNIT_TYPES
SLOT_FIELDS = ("x", "y", "merc", "type", "troops", "quality", "morale", "state", "ammo", "target")
UNKNOWN_FIELDS = ("header.x2", "header.y1", "slot.state")           # named but not understood (every other field is decoded)
CHEB = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def parse_slot(r, k):
    v = struct.unpack_from("<10h", r, 0)
    s = dict(zip(SLOT_FIELDS, v))
    s["slot"] = k
    s["side"] = 0 if k < 20 else 1
    s["type"] = TYPES[v[3]] if 0 <= v[3] < 5 else v[3]
    s["name"] = sav.cstr(r[20:44])
    s["alive"] = v[4] > 0
    return s


def parse_block(raw):
    """Parse the 2,105 bytes of block 12 (a `bytes`/`bytearray`)."""
    if len(raw) != BLOCK_LEN:
        raise ValueError("battle block is %d bytes, not %d" % (len(raw), BLOCK_LEN))
    a, d, x2, y1, rnd = struct.unpack_from("<hhhBh", raw, 0)
    slots = [parse_slot(raw[HEADER_LEN + SLOT_LEN * k:HEADER_LEN + SLOT_LEN * (k + 1)], k) for k in range(N_SLOTS)]
    g0 = HEADER_LEN + SLOT_LEN * N_SLOTS
    grid = list(struct.unpack_from("<%dh" % (GRID_W * GRID_H), raw, g0))
    return {"attacker_army": a, "defender_army": d, "x2": x2, "y1": y1, "half_round": rnd, "slots": slots, "grid": grid}


def block_of_save(raw):
    """The block of a whole save (bytes), or None when the battle flag is 0 (no block 12)."""
    t = sav.parse(raw)["tail_off"]
    if raw[t + 54] == 0:
        return None
    return parse_block(raw[t + 55:])


def encode_block(b):
    """The inverse of `parse_block`: 2,105 bytes from a parsed block (the slots' `name` is kept as given, NUL padded)."""
    out = bytearray(struct.pack("<hhhBh", b["attacker_army"], b["defender_army"], b["x2"], b["y1"], b["half_round"]))
    for s in b["slots"]:
        typ = TYPES.index(s["type"]) if isinstance(s["type"], str) else s["type"]
        out += struct.pack("<10h", s["x"], s["y"], s["merc"], typ, s["troops"], s["quality"], s["morale"], s["state"], s["ammo"], s["target"])
        out += s["name"].encode("latin1").ljust(24, b"\0")[:24]
    out += struct.pack("<%dh" % (GRID_W * GRID_H), *b["grid"])
    return bytes(out)


def synthetic_block(attacker_units, defender_units, attacker_army=0, defender_army=10, half_round=1):
    """A block built from scratch (tests, crafted saves): each side's units are (type, troops, quality, merc, name); attackers stand in row y=0 from
    x=0, defenders in row y=9 from x=1 (the placement seen in B2), full morale 70, ammo li 7 / ar 25 / lc 9 / else 0, no targets; the grid is
    derived with the sprite rule (side*20 + 3*type + size class)."""
    for side, units in (("attacker", attacker_units), ("defender", defender_units)):
        if len(units) > 13:       # attacker unit j stands at x=j (0..13), defender j at x=j+1: more than 13 / 12 would leave the 14-wide grid
            raise ValueError("synthetic_block: %s has %d units; at most 13 (attacker) / 12 (defender) fit the 14 x 12 grid" % (side, len(units)))
    if len(defender_units) > 12:
        raise ValueError("synthetic_block: defender has %d units; at most 12 fit the 14 x 12 grid (x = j + 1)" % len(defender_units))
    std = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}
    ammo = {"li": 7, "ar": 25, "lc": 9, "hi": 0, "hc": 0}
    slots = []
    for side, units in ((0, attacker_units), (1, defender_units)):
        for j in range(20):
            if j < len(units):
                typ, troops, q, merc, name = units[j]
                x, y = (j, 0) if side == 0 else (j + 1, 9)
                slots.append({"slot": 20 * side + j, "side": side, "x": x, "y": y, "merc": merc, "type": typ, "troops": troops, "quality": q,
                              "morale": 70, "state": 0, "ammo": ammo[typ], "target": -1, "name": name, "alive": troops > 0})
            else:
                slots.append({"slot": 20 * side + j, "side": side, "x": 0, "y": 0, "merc": 0, "type": 0, "troops": 0, "quality": 0, "morale": 0,
                              "state": 0, "ammo": 0, "target": -1 if side else 0, "name": "", "alive": False})
    grid = [EMPTY] * (GRID_W * GRID_H)
    for s in slots:
        if s["alive"]:
            t = s["type"]
            cls = 0 if s["troops"] * 3 < std[t] else 1 if s["troops"] * 3 < 2 * std[t] else 2
            grid[cell(s["x"], s["y"])] = 20 * s["side"] + 3 * TYPES.index(t) + cls
    return {"attacker_army": attacker_army, "defender_army": defender_army, "x2": 0, "y1": 0, "half_round": half_round, "slots": slots, "grid": grid}


def from_save(path):
    return block_of_save(Path(path).read_bytes())


def cell(x, y):
    return x * GRID_H + y


def expected_grid(b):
    """The grid implied by the slots (alive slots only): side*20 + sprite. The sprite's size class is not derivable from troops without the
    thresholds (found in B2: see the finding), so this returns {cell: (side, type)} and `check_grid` compares side and type."""
    out = {}
    for s in b["slots"]:
        if s["alive"]:
            out[cell(s["x"], s["y"])] = (s["side"], TYPES.index(s["type"]) if isinstance(s["type"], str) else s["type"])
    return out


def check_grid(b):
    """Does the grid match the slots? Returns a list of problems (empty = consistent): a non-empty grid cell must hold side*20 + 3*type + (0..2) of
    the slot standing there, and nothing else may be non-empty."""
    exp, bad = expected_grid(b), []
    for i, v in enumerate(b["grid"]):
        if v == EMPTY:
            if i in exp:
                bad.append(("slot at empty cell", i))
            continue
        if i not in exp:
            bad.append(("grid cell without a slot", i, v))
            continue
        side, typ = exp[i]
        sc = v - 20 * side - 3 * typ
        if not 0 <= sc <= 2:
            bad.append(("sprite mismatch", i, v, side, typ))
    return bad


def sprite(b, s):
    """The sprite value of an alive slot, read from the grid (side*20 + 3*type + size class)."""
    return b["grid"][cell(s["x"], s["y"])]


def side_slots(b, side, alive=True):
    return [s for s in b["slots"] if s["side"] == side and (s["alive"] or not alive)]


def diff(a, b):
    """Half-round diff between two parsed blocks (a before, b after): per slot the change of position, troops, morale, state, ammo, target, and
    inferred actions. **Every action is [D]** (one half-round can hold several exchanges; the block does not say who hit whom):
      move: the position changed (exact as a fact; calling it a move is [D]);
      loss: troops fell; `shooters`: units of the OTHER side whose ammo fell (they shot, [D]); `adjacent`: units of the other side within 1
            cell (Chebyshev) of the victim at the start or the end of the half-round (melee candidates, [D]);
      kind: "melee" when no unit of the other side lost ammo and at least one is adjacent; "shooting" when at least one shooter and none
            adjacent; "unknown" otherwise (both, or neither, or several candidates: the diff does not fix it);
      actor: the single candidate when there is exactly one (shooter or adjacent), else "unknown".
    Returns {"slots": {k: {...}}, "ambiguous": n, "unambiguous": m, "losses": n_slots_with_loss}."""
    out, n_amb, n_ok, n_loss = {}, 0, 0, 0
    shooters = {s: [x["slot"] for x in b["slots"] if x["side"] == s and x["alive"] or x["side"] == s and a["slots"][x["slot"]]["alive"]
                    if b["slots"][x["slot"]]["ammo"] < a["slots"][x["slot"]]["ammo"]] for s in (0, 1)}
    for k in range(N_SLOTS):
        sa, sb = a["slots"][k], b["slots"][k]
        if not (sa["alive"] or sb["alive"]):
            continue
        row = {"slot": k, "side": sa["side"]}
        if (sa["x"], sa["y"]) != (sb["x"], sb["y"]):
            row["move"] = {"from": (sa["x"], sa["y"]), "to": (sb["x"], sb["y"]), "label": "[D]"}
        for f in ("troops", "morale", "state", "ammo", "target", "quality"):
            if sa[f] != sb[f]:
                row["d_" + f] = (sa[f], sb[f])
        if sb["troops"] < sa["troops"]:
            n_loss += 1
            enemy = 1 - sa["side"]
            adj = [e["slot"] for e in b["slots"] if e["side"] == enemy and (e["alive"] or a["slots"][e["slot"]]["alive"])
                   and (CHEB((sa["x"], sa["y"]), (a["slots"][e["slot"]]["x"], a["slots"][e["slot"]]["y"])) <= 1
                        or CHEB((sb["x"], sb["y"]), (e["x"], e["y"])) <= 1)]
            sh = shooters[enemy]
            kind = "melee" if adj and not sh else "shooting" if sh and not adj else "unknown"
            cands = adj if kind == "melee" else sh if kind == "shooting" else sorted(set(adj) | set(sh))
            row["loss"] = {"amount": sa["troops"] - sb["troops"], "kind": kind, "adjacent": adj, "shooters": sh,
                           "actor": cands[0] if len(cands) == 1 else "unknown", "label": "[D]"}
            if len(cands) == 1 and kind != "unknown":
                n_ok += 1
            else:
                n_amb += 1
        if len(row) > 2:
            out[k] = row
    return {"slots": out, "ambiguous": n_amb, "unambiguous": n_ok, "losses": n_loss}


def attribute(a, b):
    """Attribution of the loss rows between two consecutive snapshots using the slot words the decompiled battle module explains [R-code: research repo
    `docs/reports/2026-10-04-decompiled-tactical-battle-rules.md`]: word 9 (`target`) is the melee target slot (-1 none) and word 8 (`ammo`) the shots left for the
    battle. A lab BATTLEnn snapshot is the state after a side's moves and BEFORE its melee [R-code], so in the diff a -> b the units of `a` with a live enemy target
    melee that target (the melee is the first event of the diff), and every drop of an enemy unit's `ammo` between a and b is a shot fired in the moves that
    finished at b. Per loss row of unit v:
      melee      v is the target of, or targets, a live enemy in `a` and no enemy unit's ammo fell: `pair` = the single (attacker, target) link when there is exactly one
                 link involving v (`fixed` True), else the several links (merged exchanges, `fixed` False);
      shooting   no melee link and enemy ammo fell: `actors` = the shooters; `fixed` True only when exactly one shooter and v is the only unit of its side that
                 lost troops in the diff (otherwise the SHOOTER is known from word 8 but WHICH of the losing units it hit is not: the word of a shot's target is not stored);
      mixed      both a melee link and a shooter: `fixed` False (the diff merges them);
      unknown    none of them.
    Returns {"rows": {slot: {...}}, "losses": n, "fixed": n_fixed, "by_kind": {...}}. Every entry is [D] (derived from the words, not a logged exchange)."""
    rows, by_kind, fixed = {}, {"melee": 0, "shooting": 0, "mixed": 0, "unknown": 0}, 0
    sl = lambda blk, k: blk["slots"][k]
    links = [(u["slot"], u["target"]) for u in a["slots"] if u["alive"] and u["target"] >= 0 and u["target"] < N_SLOTS
             and a["slots"][u["target"]]["alive"] and a["slots"][u["target"]]["side"] != u["side"]]
    shot = {s["slot"] for s in a["slots"] if s["alive"] and sl(b, s["slot"])["ammo"] < s["ammo"]}
    losers = [s["slot"] for s in a["slots"] if sl(b, s["slot"])["troops"] < s["troops"] and s["alive"]]
    for v in losers:
        side = sl(a, v)["side"]
        mine = []
        for u, t in links:                       # a mutual pair (u targets t and t targets u) is ONE exchange
            if v in (u, t) and (t, u) not in mine and (u, t) not in mine:
                mine.append((u, t))
        shooters = sorted(s for s in shot if sl(a, s)["side"] != side)
        row = {"slot": v, "amount": sl(a, v)["troops"] - sl(b, v)["troops"]}
        if mine and not shooters:
            row.update(kind="melee", links=mine, fixed=len(mine) == 1)
        elif shooters and not mine:
            same_side_losers = [x for x in losers if sl(a, x)["side"] == side]
            row.update(kind="shooting", actors=shooters, fixed=len(shooters) == 1 and same_side_losers == [v])
        elif shooters and mine:
            row.update(kind="mixed", links=mine, actors=shooters, fixed=False)
        else:
            row.update(kind="unknown", fixed=False)
        by_kind[row["kind"]] += 1
        fixed += row["fixed"]
        rows[v] = row
    return {"rows": rows, "losses": len(losers), "fixed": fixed, "by_kind": by_kind}
