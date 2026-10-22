"""Run 1 helper: path cost (planner/path.py) for an army to reach a tile adjacent to (x, y): can that enemy army attack there?

    python3 runs/1/bot/dist.py <turn> <army> <x> <y> [<x> <y> ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from planner import path as P  # noqa: E402
from state import sav  # noqa: E402
import turn as T  # noqa: E402

s = sav.load(T.save_path(int(sys.argv[1])))
a = s["armies"][int(sys.argv[2])]
xs = [int(v) for v in sys.argv[3:]]
for x, y in zip(xs[::2], xs[1::2]):
    cost, pth = P.path_adjacent(s, (a["x"], a["y"]), (x, y))
    print("army %d (%d,%d) moves %d -> adjacent to (%d,%d): cost %s, stand %s" % (
        a["id"], a["x"], a["y"], a["moves"], x, y, cost, pth[-1] if pth else None))
