#!/usr/bin/env python3
"""#195 X1 (phase order): the turns where a war starts during the AI phase, in the original or in the remake, and
whether the warring nations' units end on different tiles in the anchored replay.

    python3 runs/experiments/audit195/x1_war_seats.py <anchored folder name> <campaign dir> [...] > out.jsonl

In the original, diplomacy (FB7C) runs before the army phase (F31C, with capital defence EFC8 at its entry), so a war
declared this seat already counts for that seat's threat budget, capital-defence radius and hire gate. In the remake the
war candidate competes inside the scored loop, after capital defence and the hire pass. A seat that starts a war is the
place where that order can show.

Per turn: the pre-AI state is the original's human-phase checkpoint (as difftest.anchored), the ends are the original's
last checkpoint and the remake's last aNNN.SAV. A war "starts" when a relation that was not 3 becomes 3. Each output line:
{camp, turn, pair, original, remake, position_rows: {nation: [kinds]}}. Read-only; writes stdout only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402

sys.path.insert(0, str(ROOT / "runs/experiments/longrun-v090"))
from pin_diff import positions, rows  # noqa: E402


def wars(s):
    out = set()
    for n in s["nations"]:
        for m, v in n["relations"].items():
            if v == 3:
                out.add(tuple(sorted((n["name"], m))))
    return out


def main():
    folder, camps = sys.argv[1], sys.argv[2:]
    for c in map(Path, camps):
        art = c / folder
        last = rows(art / "turns.jsonl")
        pos, _ = positions(last)
        for t, r in sorted(last.items()):
            if r.get("remake_errors") or "error" in r:
                continue
            orig = c / "original"
            ends = sorted(orig.glob(f"t{t:02d}-a*.SAV"))
            rdir = art / f"t{t:02d}"
            rends = sorted(rdir.glob("a*.SAV"))
            if len(ends) < 1 or not rends:
                continue
            pre = ends[-2] if len(ends) > 1 else (orig / "t00-start.SAV" if t == 1 else sorted(orig.glob(f"t{t - 1:02d}-a*.SAV"))[-1])
            w0, wo, wr = wars(load(pre)), wars(load(ends[-1])), wars(load(rends[-1]))
            for pair in sorted((wo | wr) - w0):
                prow = {n: sorted(k for (tt, nn, k) in pos if tt == t and nn == n) for n in pair}
                print(json.dumps({"camp": c.name, "turn": t, "pair": pair, "original": pair in wo, "remake": pair in wr,
                                  "position_rows": {n: k for n, k in prow.items() if k}}), flush=True)


if __name__ == "__main__":
    main()
