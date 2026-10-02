#!/usr/bin/env python3
"""T2 probe: the first naval battle. From saves/fleets-adjacent-at-sea-0723.SAV (Ptolemaic's turn, war already, fleets adjacent),
select Ptolemaic's fleet and click Carthage's. Nothing is auto-answered: every box and window is captured as it appears.

    python3 runs/experiments/fleet-battles/probe_attack.py
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import CUR_NATION, G, SEL_FLEET, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-naval-battle"
OUT.mkdir(parents=True, exist_ok=True)
FIX = next(p for p in (ROOT / "saves" / "fleets-adjacent-at-sea-0723.SAV", ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_FIXTURE_fleets_adjacent.SAV") if p.exists())
res = {"windows": []}


def fleets(g):
    s = sav.load(str(g.save_as("PROBE_TMP.SAV")))
    return [(f["id"], f["owner"], f["x"], f["y"], f["ships"], f.get("condition"), f["moves"], f["army"]) for f in s["fleets"] if f["owner"] in (1, 3)]


g = Game()
g.load(FIX, seed=12345)
res["start"] = {"cur_nation": g.i16(CUR_NATION), "calendar": g.calendar(), "fleets": fleets(g)}
print("start", res["start"], flush=True)
mine = next(f for f in res["start"]["fleets"] if f[1] == g.i16(CUR_NATION))
other = next(f for f in res["start"]["fleets"] if f[1] != g.i16(CUR_NATION))
g.select_fleet(mine[0], mine[2], mine[3])
res["selected"] = g.i16(SEL_FLEET)
g.shot(OUT / "probe_1_selected.png")
g.click_tile(other[2], other[3], pause=0.5)
t0 = time.time()
seen = {}
for i in range(40):                      # 20 s of watching
    ws = [(w[1], w[4], w[5]) for w in g.find_windows(".") if w[1] not in ("Imperial Conquest 2", "Area map", "Unit map", "Information")
          and not w[1].startswith("Imperial Conquest 2 ")]
    key = json.dumps(ws)
    if key not in seen:
        seen[key] = round(time.time() - t0, 1)
        res["windows"].append({"t": seen[key], "windows": ws, "texts": [(p[1], g.read_popup(p)) for p in g.popups()], "in_battle_flag": g.in_battle()})
        g.shot(OUT / f"probe_2_t{int(seen[key]):02d}_{len(seen)}.png")
        print(res["windows"][-1], flush=True)
    time.sleep(0.5)
g.shot(OUT / "probe_3_after.png")
sa = sav.load(str(g.save_as("PROBE_AFTER.SAV")))
shutil.copy(G / "PROBE_AFTER.SAV", OUT / "PROBE_AFTER.SAV")
res["after"] = {"cur_nation": g.i16(CUR_NATION), "sel_fleet": g.i16(SEL_FLEET), "fleets": [(f["id"], f["owner"], f["x"], f["y"], f["ships"], f.get("condition"), f["moves"], f["army"], f["supplies"]) for f in sa["fleets"] if f["owner"] in (1, 3)],
                "news_tail": sa["news"][-6:], "treasuries": (sa["nations"][1]["treasury"], sa["nations"][3]["treasury"])}
shutil.copy(FIX, OUT / "PROBE_START.SAV")
(OUT / "probe_attack.json").write_text(json.dumps(res, indent=1, default=str))
print("after", res["after"], flush=True)
