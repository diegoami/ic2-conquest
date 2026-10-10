"""Experiment: can Rome beat Gaul's field army early?

From the run-0 start (`BASE.SAV`, Rome, a fixed seed): join armies 0 and 1,
march the joined army to Gaul's army, attack it and play the battle with
Computer general. Run under several seeds and record both armies' composition
before and after, the winner and the losses.

    python3 runs/experiments/gallic-army.py 12345 999 777

Writes `runs/experiments/gallic-army/results.json` and prints a table. The
turn files and artifacts a real run leaves are the run's, not this probe's.
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from harness.driver import G, WORK, Game          # noqa: E402
from state.battle import by_type                    # noqa: E402
from state.sav import UNIT_TYPES, live_armies, load  # noqa: E402

BASE = WORK / "fixtures" / "BASE.SAV"
OUT = ROOT / "runs" / "experiments" / "gallic-army"
from harness import environment as _env  # noqa: E402  every game start writes environment-<stamp>.json beside the outputs
_env.folder_sink(OUT, 'gallic-army.py')
GAUL = 6


def mem_units(g, i):
    """Army i's troops by type, read from the running game."""
    rec = g.army_rec(i)
    out = {}
    for k in range(20):
        _label, typ, troops, _q = struct.unpack_from("<4h", rec, 16 + 32 * k)
        if troops > 0 and 0 <= typ < 5:
            out[UNIT_TYPES[typ]] = out.get(UNIT_TYPES[typ], 0) + troops
    return out


def army_of(s, nation):
    a = live_armies(s, nation)
    return a[0] if a else None


def run(seed):
    g = Game()
    g.load(BASE, seed=seed)
    r = {"seed": seed}
    # turn 1 (0720): bring army 1 to (113,45)
    g.move(1, 113, 45)
    name, _ = g.end_turn()
    # turn 2 (0721): close in and join into army 0
    g.move(1, 104, 36)
    g.move(0, 103, 36)
    g.join(0)
    r["rome_before"] = mem_units(g, 0)
    r["rome_troops_before"] = sum(r["rome_before"].values())
    r["rome_pos_before"] = g.army_pos(0)
    # march toward Gaul's army, one straight leg per turn, then attack
    for turn in range(8):
        s = load(G / name)
        garmy = army_of(s, GAUL)
        if garmy is None:
            r["result"] = "Gaul has no army"
            return r
        t = (garmy["x"], garmy["y"])
        r["gaul_before"] = {ty: n for ty, n in by_type(garmy).items() if n}      # sum per type (the old comprehension kept only the last unit of each type)
        r["gaul_troops_before"] = garmy["troops"]
        pos = g.army_pos(0)
        r["turns_to_battle"] = turn
        if max(abs(pos[0] - t[0]), abs(pos[1] - t[1])) == 1:
            r["rome_units_before_battle"] = mem_units(g, 0)
            texts = g.attack(0, *t)
            r["attack_texts"] = texts
            r["rome_pos_after"] = g.army_pos(0)
            r["rome_units_after"] = mem_units(g, 0)
            r["rome_troops_after"] = sum(r["rome_units_after"].values())
            # end the turn to write a save with the post-battle records
            name2, _ = g.end_turn()
            s2 = load(G / name2)
            ga2 = army_of(s2, GAUL)
            r["gaul_after"] = {ty: n for ty, n in by_type(ga2).items() if n} if ga2 else {}
            r["gaul_troops_after"] = ga2["troops"] if ga2 else 0
            r["result"] = "battle"
            return r
        # waypoint adjacent to Gaul's army, on the side we approach from
        wx = t[0] + (1 if pos[0] > t[0] else -1 if pos[0] < t[0] else 0)
        wy = t[1] + (1 if pos[1] > t[1] else -1 if pos[1] < t[1] else 0)
        g.move(0, wx, wy)
        name, _ = g.end_turn()
    r["result"] = "no battle in 8 turns"
    return r


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1:]] or [12345]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in seeds:
        r = run(seed)
        rows.append(r)
        print(json.dumps(r, indent=1), flush=True)
    (OUT / "results.json").write_text(json.dumps(rows, indent=1))
    print("wrote", OUT / "results.json")
