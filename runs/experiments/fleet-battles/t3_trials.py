#!/usr/bin/env python3
"""T3 trials: naval battles with an army aboard (SYNTHETIC cargo: written into the fixture by t3_stage.py, verified against a natural
embark). Same fixture and fleets as cell P of trials.py (Ptolemaic 70 ships x 63 attacks Carthage 90 x 74, strength 441 v 666,
no cargo: 0 of 10 won), so each cell differs from P only by the army aboard. Ptolemaic's cargo is army 7 (morale 67), Carthage's
army 2 (morale 65); a unit is (type, troops), 0 light infantry, 2 archers.

  L5    attacker carries 5,000 light infantry        (siegeStrength/50 = 83.1)
  L10   10,000 light infantry                         (167.5)
  L15   15,000 light infantry                         (250.6)
  A5    5,000 archers (x3 weight: the same strength as L15, a third of the men)
  L25   25,000 light infantry                         (418.1)
  L15D5 attacker L15, defender carries 5,000 light infantry (does the defender's cargo count?)
  H15   15,000 heavy infantry (the siege formula weights only archers: the same strength as L15)
  M15   a mixed army of five unit types, 11,000 men, siege-weighted 15,000 (4,000 light infantry, 3,000 heavy infantry, 2,000 archers x3,
        1,000 light and 1,000 heavy cavalry): the same strength as L15

    python3 runs/experiments/fleet-battles/t3_stage.py build ; python3 runs/experiments/fleet-battles/t3_trials.py [cell ...] [--seeds N] [--from K] [--save 8,10]
(seed 1 of each cell is always saved; --save adds seeds, to keep a win and a loss per cell)
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import Game  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-naval-battle-cargo"
SRC = ROOT / "artifacts" / "run-exp-naval-battle" / "FIX_P_0723_ptolemaic_seat.SAV"
ATT_ARMY, DEF_ARMY, ATT, DEF = 7, 2, 1, 0
CELLS = {"L5": ([(0, 5000)], None), "L10": ([(0, 10000)], None), "L15": ([(0, 15000)], None), "A5": ([(2, 5000)], None),
         "L25": ([(0, 25000)], None), "L15D5": ([(0, 15000)], [(0, 5000)]),
         "H15": ([(1, 15000)], None), "M15": ([(0, 4000), (1, 3000), (2, 2000), (3, 1000), (4, 1000)], None)}
OUT.mkdir(parents=True, exist_ok=True)


def fixture(cell):
    return OUT / f"FIX_T3_{cell}.SAV"


def build(cells):
    sys.path.insert(0, str(Path(__file__).parent))
    from t3_stage import put_cargo
    for cell in cells:
        att, dfn = CELLS[cell]
        fx = fixture(cell)
        tmp = OUT / "tmp.SAV"
        print(cell, put_cargo(SRC, tmp, ATT_ARMY, ATT, att))
        if dfn:
            print(cell, put_cargo(tmp, fx, DEF_ARMY, DEF, dfn))
        else:
            shutil.copy(tmp, fx)
        tmp.unlink()


def army_state(g, i):
    rec = g.army_rec(i)
    import struct
    x, y, owner, moves, cell, sup, money, morale = struct.unpack_from("<8h", rec, 0)
    troops = sum(max(0, struct.unpack_from("<h", rec, 16 + 32 * k + 4)[0]) for k in range(20))
    return {"id": i, "x": x, "y": y, "owner": owner, "moves": moves, "cell": cell, "supplies": sup, "morale": morale, "troops": troops}


def trial(cell, seed, save=False):
    g = Game()
    try:
        g.load(fixture(cell), seed=seed)
        a0, d0 = g.fleet_state(ATT), g.fleet_state(DEF)
        ar0, dr0 = army_state(g, ATT_ARMY), army_state(g, DEF_ARMY)
        texts = g.attack_fleet(ATT, DEF)
        time.sleep(1.0)
        a1, d1 = g.fleet_state(ATT), g.fleet_state(DEF)
        ar1, dr1 = army_state(g, ATT_ARMY), army_state(g, DEF_ARMY)
        if seed == 1 or save:
            shutil.copy(g.save_as(f"NBC_{cell}_seed{seed}.SAV"), OUT / f"NBC_{cell}_seed{seed}.SAV")
        return {"cell": cell, "seed": seed, "attacker_before": a0, "defender_before": d0, "attacker_after": a1, "defender_after": d1,
                "att_army_before": ar0, "att_army_after": ar1, "def_army_before": dr0, "def_army_after": dr1, "boxes": texts,
                "attacker_alive": a1["owner"] != -1 and a1["ships"] > 0, "defender_alive": d1["owner"] != -1 and d1["ships"] > 0}
    finally:
        g.kill()


def main():
    args = sys.argv[1:]
    n = int(args[args.index("--seeds") + 1]) if "--seeds" in args else 10
    first = int(args[args.index("--from") + 1]) if "--from" in args else 1
    save_seeds = {int(x) for x in args[args.index("--save") + 1].split(",")} if "--save" in args else set()   # seeds whose battle is also saved
    cells = [a for a in args if a in CELLS] or list(CELLS)
    for c in cells:
        if not fixture(c).exists():
            sys.exit(f"cell {c}: missing {fixture(c)}: run t3_stage.py build first")
    f = OUT / "t3_trials.json"
    res = json.loads(f.read_text()) if f.exists() else []
    for cell in cells:
        for seed in range(first, n + 1):
            try:
                r = trial(cell, seed, save=seed in save_seeds)
            except Exception as e:     # noqa: BLE001 - a failure is a result
                r = {"cell": cell, "seed": seed, "error": f"{type(e).__name__}: {e}"}
            res = [x for x in res if not (x["cell"] == cell and x["seed"] == seed)] + [r]
            f.write_text(json.dumps(res, indent=1, default=str))
            if "error" in r:
                print(cell, seed, "ERROR", r["error"][:120], flush=True)
            else:
                w = "attacker" if r["attacker_alive"] and not r["defender_alive"] else "defender" if r["defender_alive"] and not r["attacker_alive"] else "both/none"
                print(f"{cell:5s} seed {seed:2d}: {w} wins; att {r['attacker_before']['ships']}/{r['attacker_before']['condition']} -> "
                      f"{r['attacker_after']['ships']}/{r['attacker_after']['condition']} (owner {r['attacker_after']['owner']}, army {r['att_army_before']['troops']} -> "
                      f"{r['att_army_after']['troops']} owner {r['att_army_after']['owner']}); def {r['defender_before']['ships']} -> {r['defender_after']['ships']}", flush=True)


if __name__ == "__main__":
    main()
