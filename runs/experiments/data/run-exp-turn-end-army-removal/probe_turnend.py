"""Army removals at the turn end / on the AI side, and whether each restores the removed army's tile (research request for
the player, 2026-10-09). The removed army's covered cell (+8) is patched to a value its real terrain is not; after the order
or the end turn the tile word tells: patched value = restored, 0 = cleared, a marker = left on the map.
Every AFTER save is also checked for record compaction (path 4): each live, not-embarked army's tile must hold its marker
(owner + 200 / 216 / 232 by troops div 1000 < 25 / < 50 / more).
python3 probe_turnend.py <out_dir> <case>"""
import json, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
import harness.driver as D
from harness.driver import G, Game
from state import sav
R = Path(__file__).resolve().parents[4]
FLD = R / "artifacts/run-exp-battle-sweep/FLD-RG_0743_rome_army0_at_86_28.SAV"
ARMY_COUNT_OFF, ARMY_LEN = 100956, 656
out = Path(sys.argv[1]); case = sys.argv[2]
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]
marker = lambda a: a["owner"] + (200 if a["troops"] // 1000 < 25 else 216 if a["troops"] // 1000 < 50 else 232)

def army_off(data, x, y, owner):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    return next(ARMY_COUNT_OFF + 2 + i * ARMY_LEN for i in range(na)
                if struct.unpack_from("<3h", data, ARMY_COUNT_OFF + 2 + i * ARMY_LEN) == (x, y, owner))

def compaction_check(path):
    b = path.read_bytes(); s = sav.load(str(path))
    bad = [(a["id"], a["owner"], a["x"], a["y"], a["troops"], word(b, a["x"], a["y"]), marker(a))
           for a in s["armies"] if a["owner"] >= 0 and not a["embarked"] and word(b, a["x"], a["y"]) != marker(a)]
    return {"live_armies": sum(1 for a in s["armies"] if a["owner"] >= 0), "records": len(s["armies"]), "marker_mismatches": bad}

def patch_merc_desertion(data):
    """Rome army 13 at (93,28): every unit a mercenary (label 11, Gallic), purse 0; covered cell 5 (mountains) -> 4."""
    off = army_off(data, 93, 28, 0)
    struct.pack_into("<h", data, off + 8, 4)
    struct.pack_into("<h", data, off + 12, 0)          # money (purse)
    for k in range(20):
        so = off + 16 + 32 * k
        if struct.unpack_from("<h", data, so + 4)[0] > 0:
            struct.pack_into("<h", data, so, 11)
    return [(93, 28)]

def nation_base(data):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    nf = struct.unpack_from("<h", data, ARMY_COUNT_OFF + 2 + na * ARMY_LEN)[0]
    return ARMY_COUNT_OFF + 2 + na * ARMY_LEN + 2 + nf * 26

def set_relation(data, a, b, rel):
    nb = nation_base(data)
    struct.pack_into("<h", data, nb + a * 1172 + 0x26 + 2 * b, rel)
    struct.pack_into("<h", data, nb + b * 1172 + 0x26 + 2 * a, rel)

def patch_merc_desertion_single(data):
    """Rome army 13 at (93,28): ONE mercenary unit (label 11, li, 1,000 men, q7, "D13"), purse 0; covered cell 5 -> 4.
    Rome and Gaul set to trade (1) both ways so Gaul's army 10 does not attack Rome's army 0 in the AI turn (merc_desertion did)."""
    off = army_off(data, 93, 28, 0)
    struct.pack_into("<h", data, off + 8, 4)
    struct.pack_into("<h", data, off + 12, 0)
    for k in range(20):
        so = off + 16 + 32 * k
        data[so:so + 32] = bytes(32)
    struct.pack_into("<4h", data, off + 16, 11, 0, 1000, 7)
    data[off + 24:off + 27] = b"D13"
    set_relation(data, 0, 6, 1)
    return [(93, 28), (86, 28)]

SIEGE = R / "saves/siege-felsina-failed-0721.SAV"

def patch_elimination(data):
    """Conquest path FUN_0044C528: Rome army 0 at (99,32) next to Felsina (98,31, Gaul, at war) gets 2 x 30,000 heavy infantry
    and 8 moves; Gaul's city count (+0x446) is set to 6, so capturing Felsina (-1) leaves 5 < 6 and Gaul is conquered.
    Gaul's only army, 9 at (96,30), covered cell 5 (mountains) -> 4."""
    off = army_off(data, 99, 32, 0)
    struct.pack_into("<h", data, off + 6, 8)
    for k in range(20):
        so = off + 16 + 32 * k
        data[so:so + 32] = bytes(32)
    for k in range(2):
        struct.pack_into("<4h", data, off + 16 + 32 * k, 0, 1, 30000, 7)
    struct.pack_into("<h", data, nation_base(data) + 6 * 1172 + 0x446, 6)
    struct.pack_into("<h", data, army_off(data, 96, 30, 6) + 8, 4)
    return [(96, 30), (99, 32)]

def place_army(data, idx, owner, x, y, units, moves=8):
    """Consistent move of army record idx: old tile <- its covered cell; new covered cell <- the new tile's terrain; marker written."""
    off = ARMY_COUNT_OFF + 2 + idx * ARMY_LEN
    ox, oy, _ = struct.unpack_from("<3h", data, off)
    struct.pack_into("<h", data, ox * 280 + oy * 2, struct.unpack_from("<h", data, off + 8)[0])
    terrain = struct.unpack_from("<h", data, x * 280 + y * 2)[0]
    assert 2 <= terrain <= 11, (x, y, terrain)
    struct.pack_into("<4h", data, off, x, y, owner, moves)
    struct.pack_into("<h", data, off + 8, terrain)
    for k in range(20):
        so = off + 16 + 32 * k
        data[so:so + 32] = bytes(32)
    for k, n in enumerate(units):
        struct.pack_into("<4h", data, off + 16 + 32 * k, 0, 1, n, 7)
    t = sum(units) // 1000
    struct.pack_into("<h", data, x * 280 + y * 2, owner + (200 if t < 25 else 216 if t < 50 else 232))

ELIM_SIEGES = [(0, 58), (1, 60), (3, 108)]      # (Rome army record, Numidian city id): Capsa, Ghadames, Ghirza (not the capital)

def patch_elimination_numidia(data):
    """Conquest path FUN_0044C528 with a consistent pre-state (attempt 1 patched Gaul's city count and broke the city lists).
    Numidia (5) holds 8 cities; three Rome armies besiege three of them in one turn: 8 -> 7 -> 6 -> 5 < 6, conquest.
    Rome army 0 -> (84,89) by Capsa, army 1 -> (86,118) by Ghadames, Carthage army 3 re-owned to Rome -> (112,109) by Ghirza;
    each 2 x 30,000 heavy infantry, 8 moves. Carthage army 2 at (42,63) is re-owned to Numidia (marker 5 + band) and its covered
    cell 2 -> 4. Rome and Numidia at war (3)."""
    place_army(data, 0, 0, 84, 89, [30000, 30000])
    place_army(data, 1, 0, 86, 118, [30000, 30000])
    place_army(data, 3, 0, 112, 109, [30000, 30000])
    off = ARMY_COUNT_OFF + 2 + 2 * ARMY_LEN
    struct.pack_into("<h", data, off + 4, 5)
    troops = sum(struct.unpack_from("<h", data, off + 16 + 32 * k + 4)[0] for k in range(20) if struct.unpack_from("<h", data, off + 16 + 32 * k + 4)[0] > 0)
    struct.pack_into("<h", data, 42 * 280 + 63 * 2, 5 + (200 if troops // 1000 < 25 else 216 if troops // 1000 < 50 else 232))
    struct.pack_into("<h", data, off + 8, 4)
    set_relation(data, 0, 5, 3)
    return [(42, 63), (84, 89), (86, 118), (112, 109)]

def patch_ai_battle(data):
    """AI-vs-AI field battle FUN_0044aee4: Carthage army 2 at (42,63) and Celtiberia army 10 (already at war, rel 3), the latter
    moved next to it at (43,63) (plain). Both covered cells set to 4 (forest; real terrain plain 2). Then Rome ends its turn."""
    off10 = ARMY_COUNT_OFF + 2 + 10 * ARMY_LEN
    units = [struct.unpack_from("<h", data, off10 + 16 + 32 * k + 4)[0] for k in range(20)]
    units = [u for u in units if u > 0]
    place_army(data, 10, 8, 43, 63, units, moves=struct.unpack_from("<h", data, off10 + 6)[0])
    struct.pack_into("<h", data, off10 + 8, 4)
    struct.pack_into("<h", data, ARMY_COUNT_OFF + 2 + 2 * ARMY_LEN + 8, 4)
    return [(42, 63), (43, 63)]

CASES = {"merc_desertion": (FLD, patch_merc_desertion, "end_turn"),
         "ai_battle": (SIEGE, patch_ai_battle, "end_turn"),
         "elimination_end_turn": (SIEGE, patch_elimination_numidia, "sieges+end_turn"),
         "elimination_numidia": (SIEGE, patch_elimination_numidia, "sieges"),
         "elimination": (SIEGE, patch_elimination, "siege"),
         "merc_desertion_single": (FLD, patch_merc_desertion_single, "end_turn")}
src, patch, action = CASES[case]
data = bytearray(src.read_bytes())
tiles = patch(data)
pre = out / f"{case}_PRE.SAV"; pre.write_bytes(bytes(data))
if src == FLD:
    D.VIEW_COLS, D.VIEW_ROWS = 29, 27      # the FLD-RG save opens a 29 x 27-tile unit map
g = Game(); g.load(pre, seed=12345)
g.save_as("TE_BEFORE.SAV"); shutil.copy(G / "TE_BEFORE.SAV", out / f"{case}_BEFORE.SAV")
res = {"case": case, "action": action}
if action == "end_turn":
    name, texts = g.end_turn()
    res["autosave"], res["popups"] = name, texts
elif action.startswith("sieges"):
    cs = {c["id"]: (c["x"], c["y"]) for c in sav.load(str(pre))["cities"]}
    res["popups"] = []
    for i, cid in ELIM_SIEGES:
        res["popups"] += g.attack(i, *cs[cid]) + g.dismiss_popups()
        g.save_as("TE_STEP.SAV"); st = sav.load(str(G / "TE_STEP.SAV"))
        res.setdefault("steps", []).append({"army": i, "city": cid, "city_owner": next(c["owner"] for c in st["cities"] if c["id"] == cid),
                                            "numidia_count": st["nations"][5]["cities_count"], "numidia_owned": sum(1 for c in st["cities"] if c["owner"] == 5)})
    if action.endswith("+end_turn"):
        name, texts = g.end_turn()
        res["autosave"], res["popups"] = name, res["popups"] + texts
elif action == "siege":
    res["popups"] = g.attack(0, 98, 31) + g.dismiss_popups()
g.save_as("TE_AFTER.SAV"); shutil.copy(G / "TE_AFTER.SAV", out / f"{case}_AFTER.SAV")
b0, b1 = (out / f"{case}_BEFORE.SAV").read_bytes(), (out / f"{case}_AFTER.SAV").read_bytes()
s0, s1 = sav.load(str(out / f"{case}_BEFORE.SAV")), sav.load(str(out / f"{case}_AFTER.SAV"))
res["tiles"] = {f"{x},{y}": {"word_before": word(b0, x, y), "word_after": word(b1, x, y), "mem_word": g.cell(x, y),
                             "armies_before": [(a["id"], a["owner"], a["troops"], a["money"], a["cell"]) for a in s0["armies"] if (a["x"], a["y"]) == (x, y)],
                             "armies_after": [(a["id"], a["owner"], a["troops"]) for a in s1["armies"] if (a["x"], a["y"]) == (x, y)]}
                for x, y in tiles}
res["calendar_after"] = s1.get("turn")
res["numidia_after"] = {"cities_count": s1["nations"][5]["cities_count"], "owned": sum(1 for c in s1["cities"] if c["owner"] == 5),
                        "army_rec2": [(a["id"], a["owner"], a["x"], a["y"], a["troops"]) for a in s1["armies"] if a["id"] == 2]}
res["gaul_after"] = {"cities_count": s1["nations"][6]["cities_count"], "unity": s1["nations"][6].get("unity"),
                     "armies": [(a["id"], a["owner"], a["x"], a["y"]) for a in s1["armies"] if a["x"] == 96 and a["y"] == 30]}
res["felsina_after"] = next((c["owner"], c["fort"]) for c in s1["cities"] if c["name"] == "Felsina")
res["news_tail"] = s1["news"][-12:]
res["compaction_after"] = compaction_check(out / f"{case}_AFTER.SAV")
print(case, json.dumps(res, default=str), flush=True)
(out / f"probe_turnend_{case}.json").write_text(json.dumps(res, indent=1, default=str))
g.kill()
