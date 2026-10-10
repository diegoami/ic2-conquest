"""Shared helpers for the unit-map mouse experiment (questions a-g)."""
import json
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness import driver as d  # noqa: E402
from harness.driver import Game, NATIONS, NATION_LEN, SEL_ARMY, SEL_FLEET, WORK, WINE, sh  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-unitmap-mouse"      # gitignored: saves and screenshots
from harness import environment as _env  # noqa: E402  every game start writes environment-<stamp>.json beside the outputs
_env.folder_sink(OUT, 'unit-map-mouse/common.py')
BASE = WORK / "fixtures" / "BASE.SAV"                    # = saves/run0-start-AUTO0720-seed12345.SAV
SEED = 12345
ROME = 0
OUT.mkdir(parents=True, exist_ok=True)


def fresh():
    g = Game()
    g.load(BASE, seed=SEED)
    return g


def keep(g, name):
    """Save the running game as <name> and copy it into the run's artifacts."""
    p = g.save_as(name)
    shutil.copy(p, OUT / name)
    return OUT / name


def shot(g, name, window="root"):
    g.shot(OUT / name, window=window)
    return name


def nation_i16(g, nation, off):
    return g.i16(NATIONS + nation * NATION_LEN + off)


def sliders(title):
    out = subprocess.run([WINE, str(WORK / "win_slider.exe"), title], capture_output=True, text=True,
                         env=d.ENV).stdout
    rows = []
    for ln in out.splitlines():
        p = ln.split("\t")
        if len(p) == 6:
            rows.append({"class": p[0], "min": int(p[1]), "max": int(p[2]), "pos": int(p[3]),
                         "line": int(p[4]), "page": int(p[5])})
    return rows


def right_click(g, x, y, pause=0.8):
    sh("xdotool", "mousemove", str(x), str(y))
    time.sleep(0.25)
    sh("xdotool", "click", "3")
    time.sleep(pause)


def log(path, obj):
    path = Path(path)
    data = json.loads(path.read_text()) if path.exists() else []
    data.append(obj)
    path.write_text(json.dumps(data, indent=1))
