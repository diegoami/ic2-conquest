"""Naval battle loser on rough sea (2026-10-08): is the loser's tile word cleared to 0, or restored from the fleet record's
covered-cell field (+24)? Fixture saves/fleets-adjacent-at-sea-0723.SAV (Ptolemaic's turn, war with Carthage): Ptolemaic fleet 1
(70 ships) at (111,73) attacks Carthage fleet 0 (90 ships) at (110,73), as in run-exp-naval-battle PROBE (seed 12345: Ptolemaic lost).
Case cover1: both fleets' covered-cell field set to 1 (rough sea); control cover0: unpatched (0, sea).
python3 probe_rough.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from harness.driver import G, SEL_FLEET, Game
from state import sav
FIX = Path("/home/diego/projects/ic2-conquest/saves/fleets-adjacent-at-sea-0723.SAV")
FLEETS = {(110, 73): 1, (111, 73): 3}          # tile: owner
EXTRA = [(111, 74)]                              # the move target, word read too
CASES = {"cover0": None, "cover1": 1, "move_cover1": 1}   # move_cover1: no battle, fleet 1 sails one tile to (111,74), empty sea
out = Path(sys.argv[1])
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]

def fleet_off(data, x, y, owner):
    for off in range(0, len(data) - 26):
        f = struct.unpack_from("<13h", data, off)
        if f[0] == x and f[1] == y and f[4] == owner:
            return off
    raise RuntimeError((x, y, owner))

res = {}
for case in (sys.argv[2:] or CASES):
    data = bytearray(FIX.read_bytes())
    if CASES[case] is not None:
        for (x, y), o in FLEETS.items():
            struct.pack_into("<h", data, fleet_off(data, x, y, o) + 24, CASES[case])
    pre = out / f"{case}_PRE.SAV"; pre.write_bytes(bytes(data))
    g = Game(); g.load(pre, seed=12345)
    s0 = sav.load(str(g.save_as("RS_BEFORE.SAV"))); shutil.copy(G / "RS_BEFORE.SAV", out / f"{case}_BEFORE.SAV")
    if case.startswith("move"):
        g.move_fleet(1, 111, 74)                 # control: the fleet leaves its tile; is the covered cell (1) put back?
    else:
        g.select_fleet(1, 111, 73)
        g.click_tile(110, 73, pause=0.5)
    for _ in range(40):                      # the battle resolves at once (run-exp-naval-battle); watch up to 20 s
        if g.popups(): break
        time.sleep(0.5)
    texts = g.dismiss_popups()
    g.save_as("RS_AFTER.SAV"); shutil.copy(G / "RS_AFTER.SAV", out / f"{case}_AFTER.SAV")
    b = (out / f"{case}_AFTER.SAV").read_bytes(); s = sav.load(str(out / f"{case}_AFTER.SAV"))
    r = {"popups": texts, "selected": g.i16(SEL_FLEET),
         "fleets_after": [(f["id"], f["owner"], f["x"], f["y"], f["ships"]) for f in s["fleets"] if f["id"] in (0, 1)],
         "cover_after": {f"{x},{y}": struct.unpack_from("<h", b, fleet_off(b, x, y, o) + 24)[0] if any(ff["owner"] == o and (ff["x"], ff["y"]) == (x, y) for ff in s["fleets"]) else None
                         for (x, y), o in FLEETS.items()},
         "word_after": {f"{x},{y}": word(b, x, y) for (x, y) in list(FLEETS) + EXTRA}, "mem_word": {f"{x},{y}": g.cell(x, y) for (x, y) in FLEETS},
         "word_before": {f"{x},{y}": word((out / f"{case}_BEFORE.SAV").read_bytes(), x, y) for (x, y) in FLEETS},
         "news_tail": s["news"][-2:]}
    res[case] = r; print(case, json.dumps(r, default=str), flush=True)
    g.kill()
(out / ("probe_rough_" + "_".join(res) + ".json")).write_text(json.dumps(res, indent=1, default=str))
