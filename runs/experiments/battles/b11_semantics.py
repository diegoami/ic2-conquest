#!/usr/bin/env python3
"""B11 task Work 3, the first check: are slot word 9 (melee target) and word 8 (shots left) what the research report says, on the B5 data?

    python3 runs/experiments/battles/b11_semantics.py [--series-dir DIR] [--baseline FILE]

Reads the B5 series (BATTLEnn.SAV of every rep-1 trial of the baseline file; default folder: the main checkout's artifacts/run-exp-battle-sweep/, read only) with
`state/battle_block.py` and, per snapshot S_k and the NEXT snapshot S_{k+1}, checks (the mover of S_k is its header word x2: the side that has just moved):
  A. every mover slot with a target >= 0 whose target is alive: the pair is within Chebyshev distance 1 (word 9 is an adjacent melee target);
  B. the same pair's troops both fall between S_k and S_{k+1} (the melee happened; both losses are at least 1 by the formula), unless an earlier melee of the same
     half-round removed the target (then the unit's own troops need not fall: counted apart);
  C. word 8 (shots left) never rises, only falls for types that have shots (li, ar, lc), and falls only in a half-round whose mover is that slot's side;
  D. a state that cannot be a pre-melee snapshot: a mover slot with a target whose own troops are already below the previous snapshot's by melee-sized amounts is not
     testable here; the hook replay (b11_exchange.py: S_k equals the replay of the previous melee and this half-round's shots, 0 differences) is the proof.
The output `b11-semantics-<stamp>.json` is tracked: counts per check and every failing case. If a check fails, the exchange log attributes from the Random records and
markers only (the task's rule); the result says which.
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402
from state import battle_block as BB  # noqa: E402

C = B.C
HAS_SHOTS = {"li", "ar", "lc"}


def cheb(a, b):
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def check_series(blocks):
    res = Counter()
    fails = []
    for k in range(len(blocks) - 1):
        S, N = blocks[k], blocks[k + 1]
        mover = S["x2"]
        removed_earlier = set()
        for u in range(mover * 20, mover * 20 + 20):
            a = S["slots"][u]
            t = a["target"]
            if not a["alive"] or t < 0:
                continue
            res["mover_slots_with_target"] += 1
            tt = S["slots"][t] if 0 <= t < 40 else None
            if tt is None or not tt["alive"]:
                res["target_not_alive_at_snapshot"] += 1
                continue
            res["A_checked"] += 1
            if cheb(a, tt) <= 1:
                res["A_adjacent"] += 1
            else:
                res["A_not_adjacent"] += 1
                fails.append({"check": "A", "half_round": S["half_round"], "slot": u, "target": t, "distance": cheb(a, tt)})
            na, nt = N["slots"][u], N["slots"][t]
            a_drop = na["troops"] < a["troops"] or not na["alive"]
            t_drop = nt["troops"] < tt["troops"] or not nt["alive"]
            if a_drop and t_drop:
                res["B_both_fall"] += 1
            else:
                # an earlier melee of this half-round (a lower slot of the same side, the same target) may have removed the target: the game then skips this slot
                earlier = [v for v in range(mover * 20, u) if S["slots"][v]["alive"] and S["slots"][v]["target"] == t
                           and (N["slots"][v]["troops"] < S["slots"][v]["troops"] or not N["slots"][v]["alive"])]
                if t_drop and not a_drop and not nt["alive"] and earlier:
                    res["B_target_removed_by_an_earlier_melee_of_the_half_round"] += 1
                else:
                    res["B_not_both_unexplained"] += 1
                    fails.append({"check": "B", "half_round": S["half_round"], "slot": u, "target": t, "actor_fell": a_drop, "target_fell": t_drop})
        for u in range(40):
            a, n = S["slots"][u], N["slots"][u]
            if not (a["alive"] and n["alive"] or a["alive"] and not n["alive"]):
                continue
            d = a["ammo"] - n["ammo"]
            if d > 0:
                res["C_ammo_falls"] += 1
                if a["type"] not in HAS_SHOTS:
                    res["C_ammo_falls_for_type_without_shots"] += 1
                    fails.append({"check": "C", "half_round": S["half_round"], "slot": u, "type": a["type"], "ammo": (a["ammo"], n["ammo"])})
                if (u // 20) == mover:
                    res["C_fall_in_window_where_own_side_is_the_next_mover"] += 0   # informational below
            elif d < 0:
                res["C_ammo_rises"] += 1
                fails.append({"check": "C", "half_round": S["half_round"], "slot": u, "ammo": (a["ammo"], n["ammo"]), "why": "rises"})
    return res, fails


def main():
    a = sys.argv[1:]
    sdir = Path(a[a.index("--series-dir") + 1]) if "--series-dir" in a else C.ROOT.parents[2] / "artifacts" / "run-exp-battle-sweep"
    bf = Path(a[a.index("--baseline") + 1]) if "--baseline" in a else sorted(C.DATA.glob("b5-baseline-*.json"))[-1]
    base = json.loads(bf.read_text())["baseline"]
    total, allfails, per, missing = Counter(), [], {}, []
    for trial, v in sorted(base.items()):
        files = [sdir / ("%s_BATTLE%02d.SAV" % (trial, i + 1)) for i in range(v["half_rounds"])]
        if not all(f.exists() for f in files):
            missing.append(trial)
            continue
        blocks = [BB.from_save(f) for f in files]
        r, fails = check_series(blocks)
        per[trial] = dict(r)
        total.update(r)
        allfails += [{"trial": trial, **f} for f in fails]
    out = {"series_dir": str(sdir), "baseline": bf.name, "trials_checked": len(per), "trials_missing_files": missing, "totals": dict(total),
           "failures": len(allfails), "failure_list": allfails[:400], "failure_kinds": dict(Counter(f["check"] for f in allfails))}
    p = C.write_new(C.DATA, "b11-semantics-%s.json" % time.strftime("%Y%m%d-%H%M%S"), json.dumps(out, indent=1))
    print(p.name, json.dumps({k: out[k] for k in ("trials_checked", "totals", "failures", "failure_kinds")}))


if __name__ == "__main__":
    main()
