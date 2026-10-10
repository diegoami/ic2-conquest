#!/usr/bin/env python3
"""T2 staging: the Carthage-seat fixture. From saves/fleets-adjacent-at-sea-0723.SAV (Ptolemaic's turn, seat 2), Ptolemaic ends its
turn without acting; the autosave of Carthage's turn start (seat 13, same turn 0723) is kept as FIX_C. The fleets stay adjacent
if nothing moved them (checked).

    python3 runs/experiments/fleet-battles/stage_cells.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import G, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-naval-battle"
from harness import environment as _env  # noqa: E402  every game start writes environment-<stamp>.json beside the outputs
_env.folder_sink(OUT, 'fleet-battles/stage_cells.py')
OUT.mkdir(parents=True, exist_ok=True)
FIX = next(p for p in (ROOT / "saves" / "fleets-adjacent-at-sea-0723.SAV", ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_FIXTURE_fleets_adjacent.SAV") if p.exists())
g = Game()
g.load(FIX, seed=12345)
shutil.copy(FIX, OUT / "FIX_P_0723_ptolemaic_seat.SAV")
name, texts = g.end_turn(timeout=300)
s = sav.load(str(G / name))
shutil.copy(G / name, OUT / "FIX_C_0723_carthage_seat.SAV")
fl = [(f["id"], f["owner"], f["x"], f["y"], f["ships"], f.get("condition"), f["moves"], f["supplies"]) for f in s["fleets"] if f["owner"] in (1, 3)]
print(name, "turn", s["turn"], "seat", s["seat_index"], "current", s["current_nation"], "relation", s["nations"][1]["relations"]["Ptolemaic"])
print("fleets:", fl)
print("texts:", texts)
(OUT / "stage_cells.json").write_text(json.dumps({"autosave": name, "turn": s["turn"], "seat": s["seat_index"], "fleets": fl, "end_turn_texts": texts}, indent=1, default=str))
g.kill()
