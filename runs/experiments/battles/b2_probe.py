#!/usr/bin/env python3
"""B2 live checks (battles plan §4 B2) of the battle-block decoder `state/battle_block.py` and of `Game.battle_state()` (game memory):

    python3 runs/experiments/battles/b2_probe.py

On the lab seed-1 exe, from the NATURAL FLD-RG (Rome's army 0, nine units, against Gaul's army 10, five units), attack and, at the placement
phase and after two End turn clicks with Computer general OFF (as B0's Save As probe: Rome idle, the AI plays):
  1. `Game.battle_state()` (memory) against File > Save As's block 12 of the same moment: every field of the 2,105 bytes (the header fields
     read from their own addresses) must be equal;
  2. the grid <-> screen mapping: a screenshot of the battle window, every one of the 14 x 12 cells classified occupied/empty by its corner
     pixel (the map starts at window y 28, tiles are 32 px) against the block's occupied cells;
  3. the slots' merc label ("word +2" of the research request, byte +4 of a slot) against the strategic unit labels, and the slot order
     against the strategic army's unit order (names).
Nothing is clicked except the attack, End turn (each proven by the half-round counter / title moving on) and File > Save As.
Output: tracked `b2-verify-<stamp>.json` + log; saves and screenshots in artifacts/run-exp-battle-sweep/.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import trials as T  # noqa: E402
from harness.driver import DriverError, Game  # noqa: E402
from state import battle, battle_block as BB, sav  # noqa: E402


def load_rgb(p):
    raw = subprocess.run(["convert", str(p), "-depth", "8", "rgb:-"], capture_output=True).stdout
    w, h = map(int, subprocess.run(["identify", "-format", "%w %h", str(p)], capture_output=True, text=True).stdout.split())
    return w, h, raw


def screen_check(png, block, y0=28, tile=32):
    """Classify every cell of the 14 x 12 grid by the colour of a pixel 4 px inside its top-left corner: the empty ground is pure green
    (0,255,0), an occupied cell is anything else. Returns (agreeing cells, total, mismatches)."""
    w, h, raw = load_rgb(png)
    occ = {(s["x"], s["y"]) for s in block["slots"] if s["alive"]}
    bad = []
    for y in range(BB.GRID_H):
        for x in range(BB.GRID_W):
            px = tuple(raw[((y0 + y * tile + 4) * w + x * tile + 4) * 3:((y0 + y * tile + 4) * w + x * tile + 4) * 3 + 3])
            if (px != (0, 255, 0)) != ((x, y) in occ):
                bad.append({"cell": (x, y), "pixel": px, "occupied": (x, y) in occ})
    return BB.GRID_W * BB.GRID_H - len(bad), BB.GRID_W * BB.GRID_H, bad


def end_turn(g, wid, log):
    """One End turn click with proof it advanced the battle. After a File > Save As the battle window is inactive and the first click may only
    activate it: the window is raised and focused first; if there is still no sign of progress within 8 s (proof the click did nothing) ONE
    more click is made, never a third."""
    for attempt in (1, 2):
        C.D.sh("xdotool", "windowraise", str(wid), check=False)
        C.D.sh("xdotool", "windowfocus", str(wid), check=False)
        time.sleep(0.3)
        try:
            g.end_turn_proven(lambda: g.click(C.D.BATTLE_TOOLS["end_turn"], C.BATTLE_Y, pause=1.0))
            log("end_turn_proven", attempt=attempt)
            return
        except DriverError as e:
            log("end_turn_no_sign", attempt=attempt, error=str(e))
            if attempt == 2:
                raise


def saved_block(path):
    raw = Path(path).read_bytes()
    t = sav.parse(raw)["tail_off"]
    return raw[t + 55:]


def main():
    log = C.Log("b2-verify")
    g = Game(exe=C.LAB_EXE % 1)
    out = {"phases": []}
    try:
        start = C.ART / C.FLD_RG_NAME
        for f in C.D.G.glob("BATTLE*.SAV"):       # strays of an earlier process are kept, not lost
            C.keep(f, f"stray_b2_{f.name}")
            f.unlink()
        g.start()
        g.open(start)
        a0, a10 = g.army_state(C.ROME_ARMY), g.army_state(C.GAUL_ARMY)
        g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
        g.click_tile(*C.GAUL_TILE, pause=0.0)
        T.wait_battle(g, log)
        time.sleep(2)
        win = g.find_windows(" v ")[0]
        for phase in ("placement", "after_end_turn_1", "after_end_turn_2"):
            if phase != "placement":
                end_turn(g, win[0], log)
                time.sleep(2)
            png = C.ART / f"b2_{phase}_window.png"
            g.shot(png, window=str(win[0]))
            st = g.battle_state()
            sv = C.keep(g.save_as(f"B2_{phase}.SAV"))
            sb = saved_block(sv)
            mem_bytes = BB.encode_block(st)
            diff = [i for i in range(len(sb)) if mem_bytes[i] != sb[i]]
            ok_cells, total, bad = screen_check(png, st)
            rec = {"phase": phase, "save": sv.name, "screenshot": png.name, "memory_equals_save_block": not diff, "differing_byte_offsets": diff,
                   "half_round": st["half_round"], "x2": st["x2"], "y1": st["y1"], "attacker_army": st["attacker_army"],
                   "defender_army": st["defender_army"], "title": [w[1] for w in g.find_windows(" v ")],
                   "grid_check_problems": BB.check_grid(st), "screen_cells_agreeing": ok_cells, "screen_cells_total": total,
                   "screen_mismatches": bad, "occupied": [(s["slot"], s["side"], s["type"], s["x"], s["y"]) for s in st["slots"] if s["alive"]]}
            out["phases"].append(rec)
            log("phase", **{k: v for k, v in rec.items() if k != "occupied"})
        # slots v the strategic armies (before the battle)
        slots = st["slots"]
        key = lambda u: (u["name"], u["type"], u["merc"], u["quality"])
        for side, army in ((0, a0), (1, a10)):
            units = army["units"]
            sl = [s for s in slots if s["side"] == side and (s["name"], s["type"]) in {(u["name"], u["type"]) for u in units}]
            out[f"side{side}"] = {"strategic_order": [(u["name"], u["type"], u["merc"]) for u in units],
                                  "slot_order": [(s["name"], s["type"], s["merc"]) for s in slots if s["side"] == side and s["name"]],
                                  "same_order": [(u["name"], u["type"]) for u in units] == [(s["name"], s["type"]) for s in slots if s["side"] == side and s["name"]],
                                  "same_set": sorted(map(key, units)) == sorted((s["name"], s["type"], s["merc"], s["quality"]) for s in slots if s["side"] == side and s["name"])}
        out["merc_label_equals_strategic_label_for_every_unit"] = all(
            {u["name"]: u["merc"] for u in a0["units"] + a10["units"]}.get(s["name"]) == s["merc"] for s in slots if s["name"])
        g.click(C.D.BATTLE_TOOLS["computer"], C.BATTLE_Y, pause=1.5)       # let the battle end; it is not needed any more
        out["status"] = "ok"
    except Exception as e:      # noqa: BLE001
        out["status"] = "error: %s: %s" % (type(e).__name__, e)
        log("error", error=out["status"])
    finally:
        C.kill_stale(g)
    p = C.DATA / f"b2-verify-{C.STAMP}.json"
    p.write_text(json.dumps(out, indent=1, default=str))
    print(p)


if __name__ == "__main__":
    main()
