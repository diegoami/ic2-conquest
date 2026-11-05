#!/usr/bin/env python3
"""#195 X1 follow-up (research PR #207): split each same-war seat's recruit change into FUN_004504f4's two parts.

    python3 runs/experiments/audit195/x1_decompose.py <mobilise.jsonl> <artifacts dir> <anchored folder> > out.jsonl

FUN_004504f4(gap) (a) mobilises ready slots (state 24) into armies and (b) raises new slots (FUN_004501f4) while the
gap is uncovered and the mobilisation level (+0x442) < 100, paying treasury and raising the level. Per seat and game
(original, remake): the ready slots that vanished ("mobilised"), the slots that are new ("raised": (type, troops, city)
not in the pre-AI multiset, state < 24), treasury and level. Slot matching is by (type, troops, city) multiset, so a
slot that ticked (state +2) is neither. Read-only.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402


def slots(s, i, ready=None):
    return Counter((x["type"], x["troops"], x["city"]) for x in s["nations"][i]["recruit_slots"]
                   if x["troops"] > 0 and (ready is None or (x["state"] == 24) == ready))


def main():
    mob, art, folder = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    camps = {p.parent.name: p.parent for p in art.glob(f"run-exp-*/*/{folder}")}
    for l in open(mob):
        r = json.loads(l)
        c, t, n = camps[r["camp"]], r["turn"], r["declarer"]
        orig = c / "original"
        ends = sorted(orig.glob(f"t{t:02d}-a*.SAV"))
        pre_f = ends[-2] if len(ends) > 1 else (orig / "t00-start.SAV" if t == 1 else sorted(orig.glob(f"t{t - 1:02d}-a*.SAV"))[-1])
        pre, outs = load(pre_f), {"original": load(ends[-1]), "remake": load(sorted((c / folder / f"t{t:02d}").glob("a*.SAV"))[-1])}
        i = [x["name"] for x in pre["nations"]].index(n)
        rec = {"camp": r["camp"], "turn": t, "declarer": n, "pre": {"treasury": pre["nations"][i]["treasury"],
               "level": pre["nations"][i]["mobilization"], "ready": sum(slots(pre, i, True).values()),
               "ready_troops": sum(k[1] * v for k, v in slots(pre, i, True).items())}}
        for g, s in outs.items():
            mobilised = slots(pre, i, True) - slots(s, i)
            raised = slots(s, i, False) - slots(pre, i)
            rec[g] = {"treasury": s["nations"][i]["treasury"], "level": s["nations"][i]["mobilization"],
                      "mobilised": sorted(mobilised.elements()), "raised": sorted(raised.elements())}
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
