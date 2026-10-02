#!/usr/bin/env python3
"""T2 trials: naval battles between the two staged fleets, N seeds per cell (one fresh process per seed: RandSeed is read from
SEED.TXT at program start).

Cells (attacker v defender; strength = ships x condition / 10 from the research formula):
  P   Ptolemaic (70 ships, 63) attacks Carthage (90, 74)           441 v 666   fixture FIX_P (Ptolemaic's seat)
  C   Carthage (90, 74) attacks Ptolemaic (70, 63)                  666 v 441   fixture FIX_C (Carthage's seat)
  C70 Carthage splits 20 ships off, its 70 (74) attack Ptolemaic    518 v 441   fixture FIX_C
  C60 Carthage splits 30 off, its 60 (74) attack Ptolemaic          444 v 441   near parity
  C50 Carthage splits 40 off, its 50 (74) attack Ptolemaic          370 v 441   the attacker is the weaker

    python3 runs/experiments/fleet-battles/trials.py [cell ...] [--seeds N]
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import G, Game  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-naval-battle"
FIX = {"P": OUT / "FIX_P_0723_ptolemaic_seat.SAV", "C": OUT / "FIX_C_0723_carthage_seat.SAV"}
CELLS = {"P": ("P", 1, 0, None), "C": ("C", 0, 1, None), "C70": ("C", 0, 1, 20),
         "C60": ("C", 0, 1, 30), "C50": ("C", 0, 1, 40)}     # fixture, attacker, defender, ships split off first


def strength(f):
    return f["ships"] * f["condition"] / 10


def trial(cell, seed):
    fix, att, dfn, split = CELLS[cell]
    g = Game()
    try:
        g.load(FIX[fix], seed=seed)
        if split:
            g.split_fleet(att, split)
        a0, d0 = g.fleet_state(att), g.fleet_state(dfn)
        texts = g.attack_fleet(att, dfn)
        time.sleep(1.0)
        a1, d1 = g.fleet_state(att), g.fleet_state(dfn)
        if seed == 1:
            shutil.copy(g.save_as(f"NB_{cell}_seed{seed}.SAV"), OUT / f"NB_{cell}_seed{seed}.SAV")
        return {"cell": cell, "seed": seed, "attacker_before": a0, "defender_before": d0, "strength": (strength(a0), strength(d0)),
                "attacker_after": a1, "defender_after": d1, "boxes": texts,
                "attacker_alive": a1["owner"] != -1 and a1["ships"] > 0, "defender_alive": d1["owner"] != -1 and d1["ships"] > 0}
    finally:
        g.kill()


def main():
    args = sys.argv[1:]
    n = int(args[args.index("--seeds") + 1]) if "--seeds" in args else 10
    cells = [a for a in args if a in CELLS] or list(CELLS)
    f = OUT / "trials.json"
    res = json.loads(f.read_text()) if f.exists() else []
    for cell in cells:
        for seed in range(1, n + 1):
            try:
                r = trial(cell, seed)
            except Exception as e:     # noqa: BLE001 - a failure is a result
                r = {"cell": cell, "seed": seed, "error": f"{type(e).__name__}: {e}"}
            res = [x for x in res if not (x["cell"] == cell and x["seed"] == seed)] + [r]
            f.write_text(json.dumps(res, indent=1, default=str))
            if "error" in r:
                print(cell, seed, "ERROR", r["error"][:120], flush=True)
            else:
                w = "attacker" if r["attacker_alive"] and not r["defender_alive"] else "defender" if r["defender_alive"] and not r["attacker_alive"] else "both/none"
                print(f"{cell:3s} seed {seed:2d}: strength {r['strength'][0]:.0f} v {r['strength'][1]:.0f} -> {w} wins; "
                      f"attacker {r['attacker_before']['ships']}/{r['attacker_before']['condition']} -> " + ("sunk" if not r["attacker_alive"] else f"{r['attacker_after']['ships']}/{r['attacker_after']['condition']}") +
                      f", defender {r['defender_before']['ships']}/{r['defender_before']['condition']} -> " + ("sunk" if not r["defender_alive"] else f"{r['defender_after']['ships']}/{r['defender_after']['condition']}"), flush=True)


if __name__ == "__main__":
    main()
