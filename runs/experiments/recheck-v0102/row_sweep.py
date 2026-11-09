#!/usr/bin/env python3
"""Recheck v0.10.2 (2026-11-09): is a position row that a pin change made appear or disappear a draw or a rule?

    IC2_ROOT=<conquest checkout with the artifacts> python3 runs/experiments/recheck-v0102/row_sweep.py \
        <out dir> <seeds, e.g. 5001-5020> <pin> [<pin> ...] -- <campaign>:<turn>:<Nation>:<armies|fleets> [...]

For every row and pin, the anchored turn is replayed from the original's own start (as difftest.anchored does) once per
seed, and the nation's live armies (x, y, troops) or launched fleets (x, y, ships) at the end are compared with the
original's end state. A row whose match rate is about the same on both pins is draw-sensitive (the anchored seed only
picked a different draw); a rate that drops to 0 on one pin is a rule change. Remake only; no Wine. The output folder
must not exist (rule 6); each replay folder is kept, and rows.jsonl holds one line per (row, pin, seed).
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from difftest import actions as act, remake  # noqa: E402
from difftest.anchored import end_checkpoint  # noqa: E402
from state.sav import NATIONS, load  # noqa: E402

DATA = Path(os.environ.get("IC2_ROOT", ROOT))


def units(s, nation, kind):
    n = NATIONS.index(nation)
    if kind == "armies":
        return Counter((a["x"], a["y"], a["troops"]) for a in s["armies"] if a["owner"] == n and a["troops"] > 0)
    return Counter((f["x"], f["y"], f["ships"]) for f in s["fleets"]
                   if f["owner"] == n and f["ships"] > 0 and not f.get("building"))


def main():
    argv = sys.argv[1:]
    cut = argv.index("--")
    out, seeds, pins, rows = Path(argv[0]), argv[1], argv[2:cut], argv[cut + 1:]
    lo, hi = (int(x) for x in seeds.split("-"))
    out.mkdir(parents=True, exist_ok=False)
    log = open(out / "rows.jsonl", "x")
    summary = []
    for spec in rows:
        camp_name, k, nation, kind = spec.split(":")
        k = int(k)
        camp = DATA / "artifacts" / camp_name
        rec = {json.loads(l)["turn"]: json.loads(l) for l in (camp / "turns.jsonl").read_text().splitlines() if l.strip()}
        orig = camp / "original"
        start = orig / "t00-start.SAV" if k == 1 else end_checkpoint(orig, k - 1)
        acts = [act.validate(x) for x in rec[k]["orders_original"]] + [{"op": "end_turn"}]
        ref = units(load(end_checkpoint(orig, k)), nation, kind)
        for p in pins:
            r = json.loads((DATA / f"artifacts/diffpin-{p}-build/pin.json").read_text())
            remake.REMAKE, remake.BUILD = Path(r["remake_dir"]), Path(r["build_dir"])
            remake.ADAPTER = remake.BUILD / "adapter/bin/RemakeAdapter/release/RemakeAdapter.dll"
            hits = 0
            for seed in range(lo, hi + 1):
                d = out / f"{camp.name}-t{k:02d}-{nation}-{kind}" / p / f"s{seed}"
                remake.run(acts, start, d, log=lambda *x: None, seed=seed)
                names = act.checkpoint_names(acts)
                got = units(load(d / f"{names[-1]}.SAV"), nation, kind)
                same = got == ref
                hits += same
                log.write(json.dumps({"row": spec, "pin": p, "seed": seed, "match": same}) + "\n")
                log.flush()
            summary.append({"row": spec, "pin": p, "seeds": hi - lo + 1, "match": hits})
            print(f"{spec} {p}: original's end matched in {hits}/{hi - lo + 1} seeds", flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
