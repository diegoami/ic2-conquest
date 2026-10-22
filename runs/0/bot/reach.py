"""Run 0 helper: path costs from an army to the tiles next to listed cities (planner/path.py, DAT terrain costs).

    python3 runs/0/bot/reach.py <save> <army> [nation ids of target cities, default 6]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from planner import path as P  # noqa: E402
from state import sav  # noqa: E402


def main(save, army, nations=(6,)):
    s = sav.load(save)
    a = s["armies"][army]
    atk = sum(u["troops"] * (3 if u["type"] == "ar" else 1) for u in a["units"]) // 80 * a["morale"]
    print("army %d at (%d,%d) troops %d moves %d siege strength %d" % (army, a["x"], a["y"], a["troops"], a["moves"], atk))
    rows = []
    for c in s["cities"]:
        if c["owner"] in nations:
            cost, path = P.path_adjacent(s, (a["x"], a["y"]), (c["x"], c["y"]))
            if cost is None:
                continue
            d = sav.siege_defence(s, c)
            rows.append((cost, c["name"], c["x"], c["y"], c["loyalty"], d, round(atk / d, 2), path[-1], P.turns_needed(s, path, 9)))
    for r in sorted(rows)[:25]:
        print("cost %3d  %-12s (%3d,%3d) loy %3d def %6d atk/def %.2f  stand %s  turns %s" % r)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), tuple(int(x) for x in sys.argv[3:]) or (6,))
