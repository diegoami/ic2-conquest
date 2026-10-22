"""Can a siege remove the attacking army, and what does that write to its tile (2026-10-09)? Siege FUN_0044b27c (:49786-49838)
removes nothing itself: the attacker loses pct = clamp(defence*6/attack, 1, 15) through FUN_0044ae20 (not extracted), and a
capture (FUN_0044bb18) only changes owners. So an army can vanish only if attrition empties it.
Fixture saves/siege-felsina-failed-0721.SAV: Rome army 0 at (99,32), next to Felsina (98,31, Gaul, at war), real covered cell 4
(forest). Patch: army 0 moves 8, covered cell 5 (mountains: neither its real 4 nor 0), units replaced (regular heavy infantry, q7).
python3 probe_siege.py <out_dir> [case ...]"""
import json, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from harness.driver import G, Game
from state import sav
FIX = (Path(__file__).resolve().parents[4] / "saves/siege-felsina-failed-0721.SAV")
CASES = {"one_man": [1], "spread": [1, 6, 7, 13, 100, 1000], "u99": [99], "u100": [100], "u150": [150],
         "u79": [79], "u80": [80], "ar26": [(26, 2)], "ar27": [(27, 2)]}   # 2026-10-09: atk = sum(troops, archers x3) div 80 x morale (research): 0 below 80
TYPE_HI = 1
COVER = 5
ARMY_COUNT_OFF, ARMY_LEN = 100956, 656
out = Path(sys.argv[1])
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]

def army_off(data, x, y, owner):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    return next(ARMY_COUNT_OFF + 2 + i * ARMY_LEN for i in range(na)
                if struct.unpack_from("<3h", data, ARMY_COUNT_OFF + 2 + i * ARMY_LEN) == (x, y, owner))

res = {}
for case in (sys.argv[2:] or CASES):
    data = bytearray(FIX.read_bytes())
    off = army_off(data, 99, 32, 0)
    struct.pack_into("<h", data, off + 6, 8)          # moves
    struct.pack_into("<h", data, off + 8, COVER)      # covered cell
    for k in range(20):
        so = off + 16 + 32 * k
        data[so:so + 32] = bytes(32)
        if k < len(CASES[case]):
            n, t = CASES[case][k] if isinstance(CASES[case][k], tuple) else (CASES[case][k], TYPE_HI)
            struct.pack_into("<4h", data, so, 0, t, n, 7)
            data[so + 8:so + 8 + len(f"U{k}")] = f"U{k}".encode()
    pre = out / f"{case}_PRE.SAV"; pre.write_bytes(bytes(data))
    g = Game(); g.load(pre, seed=12345)
    g.save_as("SG_BEFORE.SAV"); shutil.copy(G / "SG_BEFORE.SAV", out / f"{case}_BEFORE.SAV")
    texts = g.attack(0, 98, 31)
    texts += g.dismiss_popups()
    g.save_as("SG_AFTER.SAV"); shutil.copy(G / "SG_AFTER.SAV", out / f"{case}_AFTER.SAV")
    b0, b1 = (out / f"{case}_BEFORE.SAV").read_bytes(), (out / f"{case}_AFTER.SAV").read_bytes()
    s0, s1 = sav.load(str(out / f"{case}_BEFORE.SAV")), sav.load(str(out / f"{case}_AFTER.SAV"))
    a_before = next(a for a in s0["armies"] if a["id"] == 0)
    a_after = [a for a in s1["armies"] if a["id"] == 0]
    fel = lambda s: next((c["owner"], c["fort"], c["loyalty"]) for c in s["cities"] if c["name"] == "Felsina")
    r = {"units_before": [(u["slot"], u["type"], u["troops"]) for u in a_before["units"]], "moves_before": a_before["moves"], "morale": a_before["morale"],
         "army0_after": [(a["owner"], a["x"], a["y"], a["moves"], [(u["slot"], u["troops"]) for u in a["units"]]) for a in a_after],
         "word_99_32": [word(b0, 99, 32), word(b1, 99, 32)], "mem_word": g.cell(99, 32),
         "felsina": [fel(s0), fel(s1)], "news_tail": s1["news"][-2:], "popups": texts}
    res[case] = r; print(case, json.dumps(r, default=str), flush=True)
    g.kill()
(out / ("probe_siege_" + "_".join(res) + ".json")).write_text(json.dumps(res, indent=1, default=str))
