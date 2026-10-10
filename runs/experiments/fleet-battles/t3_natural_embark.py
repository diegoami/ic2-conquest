#!/usr/bin/env python3
"""T3 step 1: embark Carthage's army 2 (33,900 troops) on its 90-ship fleet 0 by clicks at the two-human start (Carthage's seat,
0720), and keep the save: the natural record that the synthetic edit of t3_stage.py must reproduce.

    python3 runs/experiments/fleet-battles/t3_natural_embark.py
"""
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import Game  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-naval-battle-cargo"
from harness import environment as _env  # noqa: E402  every game start writes environment-<stamp>.json beside the outputs
_env.folder_sink(OUT, 'fleet-battles/t3_natural_embark.py')
OUT.mkdir(parents=True, exist_ok=True)
START = ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"

g = Game()
try:
    g.load(START, seed=12345)
    print("army 2 at", g.army_pos(2), "fleet 0 at", g.fleet_pos(0))
    ax0, ay0 = g.army_pos(2)
    fx0, fy0 = g.fleet_pos(0)
    land = ((ax0 + fx0) // 2, (ay0 + fy0) // 2)         # the tile between the army and the fleet (here (48,62): the fleet is 2 tiles away)
    print("move:", g.move(2, *land))
    ax, ay = g.army_pos(2)
    fx, fy = g.fleet_pos(0)
    assert (ax, ay) == land and max(abs(ax - fx), abs(ay - fy)) == 1, f"army 2 at {ax},{ay} is not next to fleet 0 at {fx},{fy}"
    print("embark:", g.embark(2, 0))
    print("fleet:", g.fleet_state(0))
    assert g.fleet_state(0)["army"] == 2 and struct.unpack_from("<h", g.army_rec(2), 8)[0] == -1, "the embark did not happen"
    shutil.copy(g.save_as("T3_NATURAL_EMBARK.SAV"), OUT / "T3_NATURAL_EMBARK.SAV")
finally:
    g.kill()
