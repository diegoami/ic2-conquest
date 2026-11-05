#!/usr/bin/env python3
"""#195 own-capital stays: the remake's own AI log (adapter option "ailog") of each stay row's nation, replayed anchored
from the original's start of the turn with the turn's own orders (seed 12345 + turn, as anchored-168dbc04-ts). Remake only.

    IC2_REMAKE=... IC2_DIFF_BUILD=<ailog build> python3 runs/experiments/audit195/stays_remake_ailog.py <out dir> > rows.jsonl
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from difftest import actions as act, remake  # noqa: E402
from difftest.anchored import end_checkpoint  # noqa: E402

A = Path("/home/diego/projects/ic2-conquest/artifacts")
ROWS = [("run-exp-longrun-v090/rome-rulebot1-40t", 10, "macedonia"), ("run-exp-longrun-v090/carthage-rulebot1-40t", 33, "ptolemaic"),
        ("run-exp-longrun-v090/carthage-rulebot1-40t", 35, "ptolemaic"), ("run-exp-longrun-v090/gaul-rulebot1-40t", 29, "seleucid"),
        ("run-exp-longrun-v091/ptolemaic-rulebot1-40t", 9, "rome"), ("run-exp-longrun-v092/numidia-rulebot1-40t", 6, "media"),
        ("run-exp-longrun-v092/numidia-rulebot1-40t", 11, "media"), ("run-exp-longrun-v092/numidia-rulebot1-40t", 11, "seleucid"),
        ("run-exp-longrun-v092/greece-rulebot1-40t", 6, "carthage")]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    done = {}
    for camp, t, nation in ROWS:
        c = A / camp
        d = out / f"{c.name}-t{t:02d}"
        if d not in done:
            rows = {json.loads(l)["turn"]: json.loads(l) for l in (c / "turns.jsonl").read_text().splitlines() if l.strip()}
            acts = [act.validate(x) for x in rows[t]["orders_original"]] + [{"op": "end_turn"}]
            remake.run(acts, end_checkpoint(c / "original", t - 1), d, log=lambda *x: None, seed=12345 + t, options=("ailog",))
            done[d] = [json.loads(l) for l in (d / "receipt.jsonl").read_text().splitlines()]
        passes = [e for e in done[d] if e["kind"] == "ai" and e["nation"] == nation]
        diplo = [x for p in passes for x in p["lines"] if "declare-war" in x or "alliance" in x or "Random(" in x]
        print(json.dumps({"camp": c.name, "turn": t, "nation": nation, "diplomacy_lines": diplo,
                          "all_lines": [x for p in passes for x in p["lines"]]}), flush=True)


if __name__ == "__main__":
    main()
