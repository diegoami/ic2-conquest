#!/usr/bin/env python3
"""T0 phase 2: from Carthage's turn (seat 13) in the two-human game: the International relations dialog, war toward Ptolemaic
(is the relation symmetric?), End turn, the next round's autosave names and who moves first.

    python3 runs/experiments/two-humans/t0_phase2.py
"""
import json
import shutil
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import CUR_NATION, G, NATIONS, NATION_LEN, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-two-humans"
res = {"steps": []}


def rel(g, a, b):
    return struct.unpack_from("<h", g.nation_rec(a), 0x26 + 2 * b)[0]


def snap(g, tag):
    me = g.i16(CUR_NATION)
    return {"tag": tag, "cur_nation": me, "calendar": g.calendar(), "title": [w[1] for w in g.find_windows("^Imperial Conquest 2    ")],
            "rel_1_to_3": rel(g, 1, 3), "rel_3_to_1": rel(g, 3, 1), "autosave_log": (G / "AUTOSAVE.LOG").read_text().splitlines()[-4:]}


def step(name, fn):
    t0 = time.time()
    try:
        r = fn()
        res["steps"].append({"step": name, "ok": True, "result": r, "secs": round(time.time() - t0, 1)})
        print("OK  ", name, str(r)[:260], flush=True)
        return r
    except Exception as e:     # noqa: BLE001
        res["steps"].append({"step": name, "ok": False, "error": f"{type(e).__name__}: {e}", "secs": round(time.time() - t0, 1)})
        print("FAIL", name, f"{type(e).__name__}: {e}", flush=True)
    finally:
        (OUT / "t0_phase2.json").write_text(json.dumps(res, indent=1, default=str))


g = Game()
step("load Carthage's turn (T0_AUTO0720.SAV)", lambda: (g.load(OUT / "T0_AUTO0720.SAV", seed=12345), snap(g, "loaded"))[1])
step("relations: war toward Ptolemaic (row 3)", lambda: (g.relation(3, "war"), snap(g, "after war"))[1])
g.shot(OUT / "t0_p2_after_war.png")
step("autosave after war order (save as)", lambda: shutil.copy(g.save_as("T0_P2_WAR.SAV"), OUT / "T0_P2_WAR.SAV").name)
step("Carthage end turn", lambda: g.end_turn(timeout=240))
step("after Carthage's End turn", lambda: snap(g, "after Carthage's End turn"))
g.shot(OUT / "t0_p2_next_round.png")
for f in sorted(G.glob("AUTO07*.SAV")):
    shutil.copy(f, OUT / f"T0_P2_{f.name}")
step("autosave files", lambda: [(f.name, f.stat().st_mtime > 0) for f in sorted(G.glob("AUTO*.SAV"))])
step("who moves now / state", lambda: snap(g, "final"))
