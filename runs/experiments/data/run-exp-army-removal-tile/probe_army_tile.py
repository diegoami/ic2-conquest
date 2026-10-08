"""What does an army's removal write to its tile (2026-10-08)? The covered-cell field (+8) of the army (or armies) that may be
removed is set to 4 (forest; the real terrain is plain, 2), so the tile word afterwards tells: 4 = covered cell restored,
0 = cleared, 2 = something re-read the real terrain. Code: FUN_0044ab90 writes the covered cell back (:49386-49389); it is the
removal in TBattleOver_OK (:57627), FUN_0044aee4 (:49679), Join armies (:46996) and Disband army.
  disband: saves/run0-start-AUTO0720-seed12345.SAV, Rome army 0 at (100,37) next to Arretium -> disband_army(0)
  join:    saves/fleet-port-antium-0734.SAV, army 0 (101,45) joins; partner = army 13 at (102,44) (last adjacent) -> join(0)
  battle:  artifacts/run-exp-battle-sweep/FLD-RG_0743_rome_army0_at_86_28.SAV, Rome army 0 (86,28) attacks Gaul army 10 (85,28),
           both patched; tactical battle played with Computer general (play_battle)
python3 probe_army_tile.py <out_dir> [case ...]"""
import json, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from harness.driver import G, Game
from state import sav
R = Path("/home/diego/projects/ic2-conquest")
CASES = {
    "disband": (R / "saves/run0-start-AUTO0720-seed12345.SAV", [(100, 37, 0)]),
    "join": (R / "saves/fleet-port-antium-0734.SAV", [(102, 44, 0)]),
    "battle": (R / "artifacts/run-exp-battle-sweep/FLD-RG_0743_rome_army0_at_86_28.SAV", [(86, 28, 0), (85, 28, 6)]),
}
PATCH = 4
ARMY_COUNT_OFF, ARMY_LEN = 100956, 656
out = Path(sys.argv[1])
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]

def army_off(data, x, y, owner):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    return next(ARMY_COUNT_OFF + 2 + i * ARMY_LEN for i in range(na)
                if struct.unpack_from("<3h", data, ARMY_COUNT_OFF + 2 + i * ARMY_LEN) == (x, y, owner))

res = {}
for case in (sys.argv[2:] or CASES):
    src, targets = CASES[case]
    data = bytearray(src.read_bytes())
    for x, y, o in targets:
        struct.pack_into("<h", data, army_off(data, x, y, o) + 8, PATCH)
    pre = out / f"{case}_PRE.SAV"; pre.write_bytes(bytes(data))
    g = Game(); g.load(pre, seed=12345)
    g.save_as("AT_BEFORE.SAV"); shutil.copy(G / "AT_BEFORE.SAV", out / f"{case}_BEFORE.SAV")
    extra = {}
    if case == "disband":
        extra["popups"] = g.disband_army(0)
    elif case == "join":
        extra["popups"] = g.join(0)
    else:
        import harness.driver as D
        D.VIEW_COLS, D.VIEW_ROWS = 29, 27      # this save opens the unit map 1143 x 903 (runs/experiments/battles/common.py); attempt 1 failed in show()
        extra["popups"] = g.attack(0, 85, 28)
        if g.in_battle():
            extra["battle"] = g.play_battle()
        extra["popups_after"] = g.dismiss_popups()
    g.save_as("AT_AFTER.SAV"); shutil.copy(G / "AT_AFTER.SAV", out / f"{case}_AFTER.SAV")
    b0, b1 = (out / f"{case}_BEFORE.SAV").read_bytes(), (out / f"{case}_AFTER.SAV").read_bytes()
    s1 = sav.load(str(out / f"{case}_AFTER.SAV"))
    r = {"targets": targets, "cover_before": [struct.unpack_from("<h", b0, army_off(b0, x, y, o) + 8)[0] for x, y, o in targets],
         "word_before": [word(b0, x, y) for x, y, o in targets], "word_after": [word(b1, x, y) for x, y, o in targets],
         "mem_word": [g.cell(x, y) for x, y, o in targets],
         "armies_on_tiles_after": [[(a["id"], a["owner"], a["troops"]) for a in s1["armies"] if (a["x"], a["y"]) == (x, y) and a["owner"] >= 0] for x, y, o in targets],
         "news_tail": s1["news"][-2:], **extra}
    res[case] = r; print(case, json.dumps(r, default=str), flush=True)
    g.kill()
(out / ("probe_army_tile_" + "_".join(res) + ".json")).write_text(json.dumps(res, indent=1, default=str))
