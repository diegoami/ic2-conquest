#!/usr/bin/env python3
"""T0 of docs/proposals/fleet-battles-and-storms.md: what does the original do with two human seats?

New Game with Carthage (row 1) and Ptolemaic (row 3) human, seed 12345. Phase 1 (this file) records the form, the title bar and CUR_NATION,
the autosaves, the turn order, ONE order for the first seat (Ptolemaic's tax) and its End turn, which hands control to the second human
seat (Carthage). The second seat's order and End turn, and the International relations war order, are phase 2 (t0_phase2.py). Every step is
wrapped: a failure is a result.

    python3 runs/experiments/two-humans/t0.py
"""
import json
import shutil
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import CUR_NATION, G, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-two-humans"
OUT.mkdir(parents=True, exist_ok=True)
res = {"steps": []}


def log_file():
    f = G / "AUTOSAVE.LOG"
    return f.read_text().splitlines() if f.exists() else []


def snap(g, tag):
    """What the game says about the seat now."""
    me = g.i16(CUR_NATION)
    tax = struct.unpack_from("<h", g.nation_rec(me), 0x44A)[0]
    return {"tag": tag, "cur_nation": me, "calendar": g.calendar(), "title": [w[1] for w in g.find_windows("^Imperial Conquest 2    ")],
            "tax_of_cur_nation": tax, "autosave_log": log_file()[-4:], "popups": [(p[1], g.read_popup(p)) for p in g.popups()]}


def step(name, fn):
    t0 = time.time()
    try:
        r = fn()
        res["steps"].append({"step": name, "ok": True, "result": r, "secs": round(time.time() - t0, 1)})
        print("OK  ", name, str(r)[:200], flush=True)
        return r
    except Exception as e:     # noqa: BLE001
        res["steps"].append({"step": name, "ok": False, "error": f"{type(e).__name__}: {e}", "secs": round(time.time() - t0, 1)})
        print("FAIL", name, f"{type(e).__name__}: {e}", flush=True)
        return None
    finally:
        (OUT / "t0.json").write_text(json.dumps(res, indent=1, default=str))


g = Game()
r = step("new_game rows [1, 3] (Carthage + Ptolemaic)", lambda: [str(x) for x in g.new_game(rows=[1, 3], seed=12345)])
if r:
    start = Path(r[0])
    shutil.copy(start, OUT / "T0_NEWGAME_AUTO0720.SAV")
    s = sav.load(str(start))
    step("start save", lambda: {"human_flags": [i for i, n in enumerate(s["nations"]) if n["human"]], "seat_index": s["seat_index"],
                               "current_nation": s["current_nation"], "turn_order": s["turn_order"], "turn": s["turn"]})
    step("seat A state", lambda: snap(g, "seat A at the start"))
    g.shot(OUT / "t0_seatA.png")
    step("seat A taxation 15", lambda: [g.taxation(15), snap(g, "after taxation")][1])
    def relations_dialog():
        g.tool("relations", pause=2.0)
        g.wait(lambda: g.find_windows("^International Relations$"), 10, "International Relations")
        for _ in range(8):          # the controls are not always enumerable the instant the window appears
            try:
                cs = g.controls("International Relations")
                break
            except Exception:     # noqa: BLE001
                time.sleep(1)
        w = g.find_windows("^International Relations$")[0]
        g.shot(OUT / "t0_relations_dialog_ptolemaic.png", window=str(w[0]))
        n = sum(1 for c in cs if c["cls"] == "TRadioButton")
        for _ in range(3):          # Cancel until the window is gone (a click into an inactive window may only activate it)
            g.click_control(g.control(cs, text="Cancel"), pause=1.5)
            if not g.find_windows("^International Relations$"):
                break
        return {"radio_buttons": n, "window": w[2:], "closed": not g.find_windows("^International Relations$")}


    step("seat A international relations dialog (screenshot, radio count)", relations_dialog)
    a1 = step("seat A end turn", lambda: g.end_turn(timeout=180))
    step("after seat A end turn", lambda: snap(g, "after seat A's End turn"))
    g.shot(OUT / "t0_after_A_end.png")
    for f in sorted(G.glob("AUTO07*.SAV")):
        shutil.copy(f, OUT / f"T0_{f.name}")
    step("autosaves", lambda: sorted(f.name for f in G.glob("AUTO*.SAV")))
g.shot(OUT / "t0_final.png")
print(json.dumps(res["steps"][-1], default=str)[:300])
