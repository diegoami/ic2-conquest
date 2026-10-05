"""Shared pieces of the B7/B12 runs (battles plan B7 and B12, docs/tasks/battles-b7-b12.md): the data folder, the game class and the battle opener.

Everything is isolated like the B11 runs (`b11_common.py`): `IC2_WORK` (a private copy of the prefix) and `DISPLAY_IC2` (a private X display) are REQUIRED in the
environment, only this run's pids are killed. Text outputs go to the TRACKED folder runs/experiments/data/run-exp-battle-orders/ (CLAUDE.md rule 6: written with
`common.write_new` or append-only, never overwritten); saves, screenshots and raw hook buffers go to artifacts/run-exp-battle-orders/ (git-ignored), their
SHA-256 in SAVES.sha256 and in the release archives' manifests.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402  (exits when IC2_WORK / DISPLAY_IC2 are not set)
import common as C  # noqa: E402
import harness.driver as D  # noqa: E402
from harness.battle_orders import BattleGame  # noqa: E402

NAME = "run-exp-battle-orders"
C.NAME = NAME
C.ART = C.ROOT / "artifacts" / NAME
C.DATA = C.ROOT / "runs" / "experiments" / "data" / NAME
B.NAME, B.ART, B.DATA = NAME, C.ART, C.DATA
ART, DATA = C.ART, C.DATA
HOOK_EXE = B.HOOK_EXE


class OGame(BattleGame, B.HookGame):
    """The B11 game (pid by display, hook buffer reader) with the six battle orders."""


def new_game(seed):
    g = OGame(exe=HOOK_EXE % seed)
    B.kill_mine(g)
    return g


def open_battle(g, log, cell="mix-rg", seed=1, tag="probe"):
    """A fresh process on the hooked exe of `seed`, the cell's start save loaded (the same FLD-RG staging as the B5/B11 runs), the attack clicked, the battle
    window open at its placement phase (half-round counter 2: Gaul has placed, Rome to place). Returns the start save Path."""
    import b11_run as R
    start, _ = R.stage_start(cell)
    for f in D.G.glob("BATTLE*.SAV"):
        C.keep(f, "stray_%s_%s" % (tag, f.name))
        f.unlink()
    g.exe = HOOK_EXE % seed
    g.start()
    log("process_started", tag=tag, exe=g.exe, pid=g.pid)
    g.open(start)
    g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
    g.click_tile(*C.GAUL_TILE, pause=0.0)
    import trials as T
    T.wait_battle(g, log)
    time.sleep(2.5)
    return start
