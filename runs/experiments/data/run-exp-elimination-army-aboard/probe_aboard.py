"""Armies aboard a fleet when their nation is eliminated (the player, 2026-10-09). Conquest path FUN_0044C528 with the consistent
pre-state of run-exp-turn-end-army-removal (Rome takes three of Numidia's eight cities in one turn: 8 -> 5 < 6, conquest), plus:
Carthage fleet 0 at (74,71) re-owned to Numidia (marker 333 -> 337), with Celtiberia army 10 re-owned to Numidia and put aboard it
(the edit of runs/experiments/fleet-battles/t3_stage.py: army x,y = fleet tile, moves 0, cell -1, fleet +22 = army index, the army's
old tile (38,64) restored to its covered cell 2). Carthage army 2 at (42,63) is a Numidian army on land, as in the earlier case.
Recorded: the fleet record, the carried army's record, the fleet tile, the land army, compaction (does the fleet's carried-army index
still point at an army of its own after records shift?), news.
python3 probe_aboard.py <out_dir> <case>    cases: sieges | sieges_end_turn | sieges_cover1 (the fleet's covered cell +24 set to 1, rough sea: 0 after = written, 1 = restored)"""
import json, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from harness.driver import G, Game
from state import sav
R = Path("/home/diego/projects/ic2-conquest")
SIEGE = R / "saves/siege-felsina-failed-0721.SAV"
ARMY_COUNT_OFF, ARMY_LEN, FLEET_LEN = 100956, 656, 26
out = Path(sys.argv[1]); case = sys.argv[2]
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]
band = lambda t: 200 if t // 1000 < 25 else 216 if t // 1000 < 50 else 232

def army_at(data, idx):
    return ARMY_COUNT_OFF + 2 + idx * ARMY_LEN

def fleet_at(data, idx):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    return ARMY_COUNT_OFF + 2 + na * ARMY_LEN + 2 + idx * FLEET_LEN

def nation_base(data):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    nf = struct.unpack_from("<h", data, ARMY_COUNT_OFF + 2 + na * ARMY_LEN)[0]
    return ARMY_COUNT_OFF + 2 + na * ARMY_LEN + 2 + nf * FLEET_LEN

def set_relation(data, a, b, rel):
    nb = nation_base(data)
    struct.pack_into("<h", data, nb + a * 1172 + 0x26 + 2 * b, rel)
    struct.pack_into("<h", data, nb + b * 1172 + 0x26 + 2 * a, rel)

def troops_of(data, off):
    return sum(t for t in (struct.unpack_from("<h", data, off + 16 + 32 * k + 4)[0] for k in range(20)) if t > 0)

def place_army(data, idx, owner, x, y, units, moves=8):
    off = army_at(data, idx)
    ox, oy, _ = struct.unpack_from("<3h", data, off)
    struct.pack_into("<h", data, ox * 280 + oy * 2, struct.unpack_from("<h", data, off + 8)[0])
    terrain = struct.unpack_from("<h", data, x * 280 + y * 2)[0]
    assert 2 <= terrain <= 11, (x, y, terrain)
    struct.pack_into("<4h", data, off, x, y, owner, moves)
    struct.pack_into("<h", data, off + 8, terrain)
    for k in range(20):
        data[off + 16 + 32 * k:off + 48 + 32 * k] = bytes(32)
    for k, n in enumerate(units):
        struct.pack_into("<4h", data, off + 16 + 32 * k, 0, 1, n, 7)
    struct.pack_into("<h", data, x * 280 + y * 2, owner + band(sum(units)))

ELIM_SIEGES = [(0, 58), (1, 60), (3, 108)]      # Capsa, Ghadames, Ghirza

def patch(data):
    place_army(data, 0, 0, 84, 89, [30000, 30000])
    place_army(data, 1, 0, 86, 118, [30000, 30000])
    place_army(data, 3, 0, 112, 109, [30000, 30000])
    a2 = army_at(data, 2)                                   # Numidian army on land (control)
    struct.pack_into("<h", data, a2 + 4, 5)
    struct.pack_into("<h", data, 42 * 280 + 63 * 2, 5 + band(troops_of(data, a2)))
    set_relation(data, 0, 5, 3)
    f0 = fleet_at(data, 0)                                  # Numidian fleet with an army aboard
    fx, fy = struct.unpack_from("<2h", data, f0)
    assert struct.unpack_from("<h", data, f0 + 22)[0] == -1 and word(data, fx, fy) == 333
    struct.pack_into("<h", data, f0 + 8, 5)
    struct.pack_into("<h", data, fx * 280 + fy * 2, 337)
    a10 = army_at(data, 10)
    ax, ay, _, _, cell = struct.unpack_from("<5h", data, a10)
    assert troops_of(data, a10) <= struct.unpack_from("<h", data, f0 + 18)[0] * 500
    struct.pack_into("<h", data, ax * 280 + ay * 2, cell)
    struct.pack_into("<3h", data, a10, fx, fy, 5)
    struct.pack_into("<h", data, a10 + 6, 0)
    struct.pack_into("<h", data, a10 + 8, -1)
    struct.pack_into("<h", data, f0 + 22, 10)
    if case == "sieges_cover1":
        struct.pack_into("<h", data, f0 + 24, 1)
    return {"fleet_tile": (fx, fy), "land_army_tile": (42, 63), "old_cargo_tile": (ax, ay)}

def snapshot(path):
    b = path.read_bytes(); s = sav.load(str(path))
    return {"n_armies": len(s["armies"]), "n_fleets": len(s["fleets"]),
            "fleets": [{k: f[k] for k in ("id", "x", "y", "owner", "ships", "army", "cell")} | {"word": word(b, f["x"], f["y"])} for f in s["fleets"]],
            "numidian_or_dead_armies": [{k: a[k] for k in ("id", "x", "y", "owner", "moves", "cell", "troops")} for a in s["armies"]
                                        if a["owner"] in (5, -1) or a["id"] in (2, 10)],
            "numidia": {"cities_count": s["nations"][5]["cities_count"], "owned": sum(1 for c in s["cities"] if c["owner"] == 5)},
            "news_tail": s["news"][-14:]}

data = bytearray(SIEGE.read_bytes())
tiles = patch(data)
pre = out / f"{case}_PRE.SAV"; pre.write_bytes(bytes(data))
g = Game(); g.load(pre, seed=12345)
g.save_as("EA_BEFORE.SAV"); shutil.copy(G / "EA_BEFORE.SAV", out / f"{case}_BEFORE.SAV")
res = {"case": case, "tiles_watched": tiles, "before": snapshot(out / f"{case}_BEFORE.SAV"), "popups": [], "steps": []}
cs = {c["id"]: (c["x"], c["y"]) for c in sav.load(str(pre))["cities"]}
for i, cid in ELIM_SIEGES:
    res["popups"] += g.attack(i, *cs[cid]) + g.dismiss_popups()
    g.save_as("EA_STEP.SAV"); st = sav.load(str(G / "EA_STEP.SAV"))
    res["steps"].append({"army": i, "city": cid, "city_owner": next(c["owner"] for c in st["cities"] if c["id"] == cid),
                         "numidia_count": st["nations"][5]["cities_count"]})
if case == "sieges_end_turn":
    name, texts = g.end_turn()
    res["autosave"] = name; res["popups"] += texts
g.save_as("EA_AFTER.SAV"); shutil.copy(G / "EA_AFTER.SAV", out / f"{case}_AFTER.SAV")
res["after"] = snapshot(out / f"{case}_AFTER.SAV")
res["mem_words"] = {f"{x},{y}": g.cell(x, y) for x, y in tiles.values()}
b1 = (out / f"{case}_AFTER.SAV").read_bytes()
res["save_words"] = {f"{x},{y}": word(b1, x, y) for x, y in tiles.values()}
print(case, json.dumps(res, default=str), flush=True)
(out / f"probe_aboard_{case}.json").write_text(json.dumps(res, indent=1, default=str))
g.kill()
