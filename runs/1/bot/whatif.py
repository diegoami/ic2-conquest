"""Run 1 helper: P1 ratio of a Roman army after joins/mobilisations, with morale averaged by troops (L3).

    python3 runs/1/bot/whatif.py <turn> <army> <enemy army> [+army <id>] [+unit type:troops:quality ...]

A mobilised unit enters with morale 59 (rules-digest §4); a joined army brings its own morale.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import sav  # noqa: E402
import strength  # noqa: E402
import turn as T  # noqa: E402


def combine(parts):
    """parts: list of (units, morale). Returns an army dict with the troop-weighted morale."""
    units = [u for us, _ in parts for u in us]
    tr = sum(u["troops"] for u in units) or 1
    mor = sum(sum(u["troops"] for u in us) * m for us, m in parts) // tr
    return {"id": -1, "units": units, "troops": tr, "morale": mor}


def main(argv):
    s = sav.load(T.save_path(int(argv[0])))
    a = s["armies"][int(argv[1])]
    e = s["armies"][int(argv[2])]
    parts = [(a["units"], a["morale"])]
    k = 3
    while k < len(argv):
        if argv[k] == "+army":
            b = s["armies"][int(argv[k + 1])]
            parts.append((b["units"], b["morale"]))
            k += 2
        else:
            t, tr, q = argv[k].lstrip("+").split(":")
            parts.append(([{"type": t, "troops": int(tr), "quality": int(q), "merc": False}], 59))
            k += 1
    c = combine(parts)
    print("combined %d troops, morale %d" % (c["troops"], c["morale"]))
    print(strength.line(c, e))


if __name__ == "__main__":
    main(sys.argv[1:])
