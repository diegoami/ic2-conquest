"""Decoder of the battle block (block 12 of a save written inside a tactical battle; the same bytes are in the game's memory) - battles plan B2.

Layout (2,105 bytes after the 55-byte trailer; `docs/sav-layout-notes.md` §Block 12; decoded in B2 from the lab series of
`1_rome_270_winter_11.sav`, see `findings/2026-10-04-tactical-battle-sweep.md`; **Wine-only**, tags: [O] observed, [D] derived, [?] unknown):

  header, 9 bytes, `<hhhBh`:
    +0  i16  attacker's strategic army index (Rome's army 0)                     [O] 0 in every battle seen
    +2  i16  defender's strategic army index (Gaul's army 10)                    [O] 10 in every battle seen. This is the "word +2" of the plan: it is
                                                                                  NOT a per-slot word and it is not a unit index (hypothesis rejected for this
                                                                                  battle; whether it is the defender's or "the other army's" index needs a battle
                                                                                  with other army indices)
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
    +14 `state`: 0..4                               [?] not decoded; distribution in the finding
    +16 `ammo`: li 7, ar 25, lc 9, hc 0, hi 0 at the start; falls when the unit shoots (ar -4 per volley)   [D]
    +18 `target`: slot index of the enemy it last attacked, -1 none                                          [D]
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


def from_save(path):
    return block_of_save(Path(path).read_bytes())


def cell(x, y):
    return x * GRID_H + y


def size_class(typ, troops, grid_value):
    return grid_value - 3 * (TYPES.index(typ) if isinstance(typ, str) else typ)


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
