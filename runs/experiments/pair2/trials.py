#!/usr/bin/env python3
"""Pair 2 battles: Seleucid's new fleet (2: 60 ships, condition 97) and Ptolemaic's (1: 70 ships, condition 89), adjacent at sea, both
supplied (170 and 190 tons), at war, neither next to an own city (fixtures of phase2.py, turn 0735). Cells: S = Seleucid attacks (582 v 623,
ratio 0.93, fixture at Seleucid's seat), P = Ptolemaic attacks (623 v 582, ratio 1.07, fixture at Ptolemaic's seat). One process per seed.

    python3 runs/experiments/pair2/trials.py [S|P ...] [--seeds N]
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import Game  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-pair2"
FIX = {"S": (OUT / "FIX_S2_seleucid_seat_0735.SAV", 2, 1), "P": (OUT / "FIX_S2_ptolemaic_seat_0735.SAV", 1, 2)}   # fixture, attacker, defender
OUT.mkdir(parents=True, exist_ok=True)


def need_fixtures(cells):
    for c in cells:
        if not FIX[c][0].exists():
            sys.exit(f"cell {c}: missing fixture {FIX[c][0]}: run phase1.py and phase2.py first")


def trial(cell, seed):
    fix, att, dfn = FIX[cell]
    g = Game()
    try:
        g.load(fix, seed=seed)
        a0, d0 = g.fleet_state(att), g.fleet_state(dfn)
        texts = g.attack_fleet(att, dfn)
        time.sleep(1.0)
        a1, d1 = g.fleet_state(att), g.fleet_state(dfn)
        if seed == 1:
            shutil.copy(g.save_as(f"P2B_{cell}_seed{seed}.SAV"), OUT / f"P2B_{cell}_seed{seed}.SAV")
        return {"cell": cell, "seed": seed, "attacker_before": a0, "defender_before": d0, "attacker_after": a1, "defender_after": d1, "boxes": texts,
                "attacker_alive": a1["owner"] != -1 and a1["ships"] > 0, "defender_alive": d1["owner"] != -1 and d1["ships"] > 0}
    finally:
        g.kill()


def main():
    args = sys.argv[1:]
    n = int(args[args.index("--seeds") + 1]) if "--seeds" in args else 10
    cells = [a for a in args if a in FIX] or list(FIX)
    need_fixtures(cells)
    f = OUT / "trials.json"
    res = json.loads(f.read_text()) if f.exists() else []
    for cell in cells:
        for seed in range(1, n + 1):
            try:
                r = trial(cell, seed)
            except Exception as e:     # noqa: BLE001
                r = {"cell": cell, "seed": seed, "error": f"{type(e).__name__}: {e}"}
            res = [x for x in res if not (x["cell"] == cell and x["seed"] == seed)] + [r]
            f.write_text(json.dumps(res, indent=1, default=str))
            if "error" in r:
                print(cell, seed, "ERROR", r["error"][:150], flush=True)
            else:
                w = "attacker" if r["attacker_alive"] and not r["defender_alive"] else "defender" if r["defender_alive"] and not r["attacker_alive"] else "both/none"
                print(f"{cell} seed {seed:2d}: {w} wins; att {r['attacker_before']['ships']}/{r['attacker_before']['condition']} -> {r['attacker_after']['ships']}/{r['attacker_after']['condition']} (owner {r['attacker_after']['owner']}); "
                      f"def {r['defender_before']['ships']}/{r['defender_before']['condition']} -> {r['defender_after']['ships']}/{r['defender_after']['condition']} (owner {r['defender_after']['owner']})", flush=True)


if __name__ == "__main__":
    main()
