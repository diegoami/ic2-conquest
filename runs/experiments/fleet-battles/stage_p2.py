#!/usr/bin/env python3
"""Staging for the swapped-role cells: at Carthage's seat (FIX_C, turn 0723) Carthage splits 30 ships off its fleet (it keeps 60) and
ends its turn; the autosave of Ptolemaic's NEXT turn start (0724, seat 2) is kept as FIX_P2. There Ptolemaic's fleet can attack
Carthage's 60-ship fleet: the attacker role swapped, strengths near parity (the conditions fall a few points at the tick).

    python3 runs/experiments/fleet-battles/stage_p2.py
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
g = Game()
g.load(OUT / "FIX_C_0723_carthage_seat.SAV", seed=12345)
texts_split = g.split_fleet(0, 30)
name, texts = g.end_turn(timeout=300)
s = sav.load(str(G / name))
shutil.copy(G / name, OUT / "FIX_P2_0724_ptolemaic_seat_c60.SAV")
fl = [(f["id"], f["owner"], f["x"], f["y"], f["ships"], f.get("condition"), f["moves"], f["supplies"]) for f in s["fleets"] if f["owner"] in (1, 3)]
print(name, "turn", s["turn"], "seat", s["seat_index"], "current", s["current_nation"], "relation", s["nations"][1]["relations"]["Ptolemaic"])
for f in fl:
    print("fleet", f, "strength", f[4] * f[5] / 10)
(OUT / "stage_p2.json").write_text(json.dumps({"autosave": name, "turn": s["turn"], "seat": s["seat_index"], "fleets": fl, "split_texts": texts_split, "end_turn_texts": texts}, indent=1, default=str))
g.kill()
