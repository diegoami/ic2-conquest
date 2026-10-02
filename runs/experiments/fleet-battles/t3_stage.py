#!/usr/bin/env python3
"""T3 staging: put an army of chosen size and composition aboard a fleet in a SAVE FILE (a synthetic edit, labelled as such).

An army can only embark from a land tile next to the fleet, so a natural fixture would need one sailing per cargo (about 20 minutes
each, and the armies of this start are 18,600-56,400 men, not the 5,000-15,000 the plan wants). The edit writes what the game
itself writes when an army boards (verified by `check`, which applies the edit to the save the natural embark started from and
compares the bytes with the natural save `T3_NATURAL_EMBARK.SAV`): the army's x, y = the fleet's tile, cell -1, moves 0; the
fleet's carried-army field = the army's index (and moves 0, which the edit leaves alone for a fleet that must attack this turn);
the map cell the army left is restored to the terrain it covered. Units are rewritten from `units` [(type, troops), ...] (None leaves them): types
0 light infantry, 1 heavy infantry, 2 archers, 3 light cavalry, 4 heavy cavalry; the rest of the 20 slots are emptied (troops 0).

    python3 runs/experiments/fleet-battles/t3_stage.py check      # the edit against the natural embark (needs the game run once:
                                                                  # t3_natural_embark.py)
    python3 runs/experiments/fleet-battles/t3_stage.py build      # the cargo fixtures of t3_trials.py
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state import sav  # noqa: E402

ART = ROOT / "artifacts"
ARMY0 = sav.ARMY_OFF + 2


def put_cargo(src, dst, army, fleet, units, morale=None, keep_moves=True):
    """Write `dst` = `src` with army `army` aboard fleet `fleet` and its units replaced by `units`. Returns a dict of what changed."""
    b = bytearray(Path(src).read_bytes())
    na = sav.i16(b, sav.ARMY_OFF)
    fl0 = ARMY0 + na * sav.ARMY_LEN + 2
    a = ARMY0 + army * sav.ARMY_LEN
    f = fl0 + fleet * sav.FLEET_LEN
    ax, ay, owner, _moves, cell = struct.unpack_from("<5h", b, a)
    fx, fy, fowner = struct.unpack_from("<3h", b, f)[0], struct.unpack_from("<3h", b, f)[1], struct.unpack_from("<h", b, f + 8)[0]
    assert owner == fowner, f"army {army} belongs to {owner}, fleet {fleet} to {fowner}"
    assert sav.i16(b, f + 22) == -1, "the fleet already carries an army"
    assert cell >= 0, "the army is already aboard"
    ship_cap = sav.i16(b, f + 18) * 500
    troops = sum(t for _, t in units) if units is not None else sav.parse(bytes(b))["armies"][army]["troops"]
    assert troops <= ship_cap, f"{troops} troops exceed the {ship_cap} the fleet carries"
    struct.pack_into("<h", b, (ax * sav.MAP_H + ay) * 2, cell)          # the map cell shows the terrain again (the edit trusts `cell`)
    struct.pack_into("<2h", b, a, fx, fy)
    struct.pack_into("<h", b, a + 6, 0)
    struct.pack_into("<h", b, a + 8, -1)
    struct.pack_into("<h", b, f + 22, army)
    if not keep_moves:
        struct.pack_into("<h", b, f + 12, 0)
    if morale is not None:
        struct.pack_into("<h", b, a + 14, morale)
    for k in range(20 if units is not None else 0):
        o = a + 16 + 32 * k
        if k < len(units):
            typ, tr = units[k]
            struct.pack_into("<3h", b, o, 0, typ, tr)
            struct.pack_into("<h", b, o + 6, 6)             # average quality
            b[o + 8:o + 32] = (b"Cargo" + bytes(24))[:24]
        else:
            struct.pack_into("<h", b, o + 4, 0)
    Path(dst).write_bytes(bytes(b))
    return {"army": army, "fleet": fleet, "from": [ax, ay], "to": [fx, fy], "troops": troops}


def check():
    """Apply the edit with the natural embark's parameters (army 2 keeps its units: the same 33,900) and compare."""
    start = ART / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"
    nat = (ART / "run-exp-naval-battle-cargo" / "T3_NATURAL_EMBARK.SAV").read_bytes()
    out = ART / "run-exp-naval-battle-cargo" / "T3_EDIT_CHECK.SAV"
    put_cargo(start, out, 2, 0, None, keep_moves=False)     # units None: the army's own units stay
    ed = out.read_bytes()
    diff = [i for i in range(len(nat)) if nat[i] != ed[i]]
    n, e = sav.load(str(ART / "run-exp-naval-battle-cargo" / "T3_NATURAL_EMBARK.SAV")), sav.load(str(out))
    same = {k: n[k] == e[k] for k in ("map", "fleets", "cities", "nations")}
    same["armies"] = [(a["x"], a["y"], a["owner"], a["moves"], a["cell"], a["troops"]) for a in n["armies"]] == \
                     [(a["x"], a["y"], a["owner"], a["moves"], a["cell"], a["troops"]) for a in e["armies"]]
    print("parsed states equal:", same)
    print("raw differing bytes:", len(diff), diff, [(nat[i], ed[i]) for i in diff])


def build():
    sys.path.insert(0, str(Path(__file__).parent))
    import t3_trials
    t3_trials.build(list(t3_trials.CELLS))


if __name__ == "__main__":
    {"check": check, "build": build}[sys.argv[1]]()
