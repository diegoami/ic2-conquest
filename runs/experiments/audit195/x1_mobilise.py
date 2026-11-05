#!/usr/bin/env python3
"""#195 X1: in the seats where the original and the remake start the same war (x1_war_seats.py output), did the
declarer mobilise recruits in the same seat? Original FFBC (economy) runs after FB7C (diplomacy) and adds 15,000 threat
per war, mobilising the gap (FUN_004504f4); the remake's economy runs before its scored loop declares the war.

    python3 runs/experiments/audit195/x1_mobilise.py <war_seats.jsonl> <artifacts dir> <anchored folder> > out.jsonl

The declarer is read from the remake's receipt ("<A> declares war on <B>."). Per seat: wars the declarer had before
the AI phase; recruit troops (sum over slots) and treasury before, after the original and after the remake. Read-only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402


def main():
    seats, art, folder = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    camps = {p.parent.name: p.parent for p in art.glob(f"run-exp-*/*/{folder}")}
    done = set()
    for l in open(seats):
        r = json.loads(l)
        if not (r["original"] and r["remake"]):
            continue
        c, t = camps[r["camp"]], r["turn"]
        rdir = c / folder / f"t{t:02d}"
        decl = re.findall(r"(\w+) declares war on (\w+)\.", (rdir / "receipt.jsonl").read_text())
        who = {a for a, b in decl if {a, b} == set(r["pair"])}
        orig = c / "original"
        ends = sorted(orig.glob(f"t{t:02d}-a*.SAV"))
        pre_f = ends[-2] if len(ends) > 1 else (orig / "t00-start.SAV" if t == 1 else sorted(orig.glob(f"t{t - 1:02d}-a*.SAV"))[-1])
        pre, end, rend = load(pre_f), load(ends[-1]), load(sorted(rdir.glob("a*.SAV"))[-1])
        for n in who:
            if (r["camp"], t, n) in done:
                continue
            done.add((r["camp"], t, n))
            i = [x["name"] for x in pre["nations"]].index(n)
            rec = lambda s: sum(x["troops"] for x in s["nations"][i]["recruit_slots"] if x["state"] == 24)
            print(json.dumps({"camp": r["camp"], "turn": t, "declarer": n,
                              "wars_before": sorted(k for k, v in pre["nations"][i]["relations"].items() if v == 3),
                              "ready_recruits": [rec(pre), rec(end), rec(rend)],
                              "treasury": [pre["nations"][i]["treasury"], end["nations"][i]["treasury"], rend["nations"][i]["treasury"]],
                              "mobilization": [pre["nations"][i]["mobilization"], end["nations"][i]["mobilization"], rend["nations"][i]["mobilization"]],
                              "position_rows": r["position_rows"]}), flush=True)


if __name__ == "__main__":
    main()
