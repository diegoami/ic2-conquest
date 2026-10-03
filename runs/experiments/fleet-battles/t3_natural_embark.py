#!/usr/bin/env python3
"""T3 step 1: embark Carthage's army 2 (33,900 troops) on its 90-ship fleet 0 by clicks at the two-human start (Carthage's seat,
0720), and keep the save: the natural record that the synthetic edit of t3_stage.py must reproduce.

    python3 runs/experiments/fleet-battles/t3_natural_embark.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import Game  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-naval-battle-cargo"
OUT.mkdir(parents=True, exist_ok=True)
START = ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"

g = Game()
try:
    g.load(START, seed=12345)
    print("army 2 at", g.army_pos(2), "fleet 0 at", g.fleet_pos(0))
    print("move:", g.move(2, 48, 62))
    ax, ay = g.army_pos(2)
    fx, fy = g.fleet_pos(0)
    assert (ax, ay) == (48, 62) and max(abs(ax - fx), abs(ay - fy)) == 1, f"army 2 at {ax},{ay} is not next to fleet 0 at {fx},{fy}"
    print("embark:", g.embark(2, 0))
    print("fleet:", g.fleet_state(0))
    shutil.copy(g.save_as("T3_NATURAL_EMBARK.SAV"), OUT / "T3_NATURAL_EMBARK.SAV")
finally:
    g.kill()
