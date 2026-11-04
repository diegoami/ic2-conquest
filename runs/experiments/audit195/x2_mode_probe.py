#!/usr/bin/env python3
"""#195 X2: does the remake's per-army support/hire timing (its Tactical retained pass, AiTurn PrepareArmy) change an
anchored turn, compared with the up-front pass of Instant mode? Remake only; the original side is the stored game.

    python3 runs/experiments/audit195/x2_mode_probe.py <campaign dir> <turn> <out dir> [--seeds 12345+k,...] [--nation N]

For each seed and mode (instant, tactical) the turn is replayed from the original's own start (as difftest.anchored does)
and the armies of every AI nation are compared with the original's end state: the (x, y, troops) multisets that differ.
Never overwrites: <out dir> must not exist.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from difftest import actions as act, remake  # noqa: E402
from difftest.anchored import end_checkpoint  # noqa: E402
from state.sav import NATIONS, load  # noqa: E402


def armies(s, nation=None):
    """Live armies and launched fleets per nation: {"<Nation>": Counter((x, y, troops))}, {"<Nation> fleets": ...}."""
    out = {}
    for a in s["armies"]:
        if a["owner"] >= 0 and a["troops"] > 0 and (nation is None or NATIONS[a["owner"]] == nation):
            out.setdefault(NATIONS[a["owner"]], Counter())[(a["x"], a["y"], a["troops"])] += 1
    for f in s["fleets"]:
        if f["owner"] >= 0 and f["ships"] > 0 and not f.get("building") and (nation is None or NATIONS[f["owner"]] == nation):
            out.setdefault(NATIONS[f["owner"]] + " fleets", Counter())[(f["x"], f["y"], f["ships"])] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("camp"), ap.add_argument("turn", type=int), ap.add_argument("out")
    ap.add_argument("--seeds", default="")
    ap.add_argument("--nation")
    a = ap.parse_args()
    camp, k, out = Path(a.camp), a.turn, Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    rows = {json.loads(l)["turn"]: json.loads(l) for l in (camp / "turns.jsonl").read_text().splitlines() if l.strip()}
    orig = camp / "original"
    start = orig / "t00-start.SAV" if k == 1 else end_checkpoint(orig, k - 1)
    acts = [act.validate(x) for x in rows[k]["orders_original"]] + [{"op": "end_turn"}]
    o_end = load(end_checkpoint(orig, k))
    ref = armies(o_end, a.nation)
    seeds = [int(x) for x in a.seeds.split(",") if x] or [12345 + k]
    res = []
    for seed in seeds:
        for mode in ("instant", "tactical"):
            d = out / f"{mode}-s{seed}"
            opts = ("tactical",) if mode == "tactical" else ()
            replies = remake.run(acts, start, d, log=lambda *x: None, seed=seed, options=opts)
            names = act.checkpoint_names(acts)
            got = armies(load(d / f"{names[-1]}.SAV"), a.nation)
            diff = {n: {"only_original": sorted((ref.get(n, Counter()) - got.get(n, Counter())).elements()),
                        "only_remake": sorted((got.get(n, Counter()) - ref.get(n, Counter())).elements())}
                    for n in sorted(set(ref) | set(got)) if ref.get(n) != got.get(n)}
            r = {"seed": seed, "mode": mode, "errors": [x for x in replies if x.get("error")], "differing_nations": diff}
            res.append(r)
            print(json.dumps({"seed": seed, "mode": mode, "nations": sorted(diff)}))
    (out / "result.json").write_text(json.dumps({"camp": str(camp), "turn": k, "start": start.name, "runs": res}, indent=1))


if __name__ == "__main__":
    main()
