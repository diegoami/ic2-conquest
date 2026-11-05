#!/usr/bin/env python3
"""#195 own-capital stays, step 2 of stays_hook_run.sh: check that the regenerated original games (OUT/regen/<g>-rulebot1,
seed 12345, rulebot-1, IC2_LOG_RANDSEED=1) are byte-identical to the stored ones up to each row's start, and write the
starts with their RandSeeds for the hook runs: OUT/starts/<game>-t<NN>.SAV (the stored start of turn NN) and
OUT/starts/seeds.json ({stem: the RandSeed logged right after that checkpoint}). Writes OUT/regen-check.json. Exit 1 when a
needed save differs or a seed is missing (the hooks would then not replay the original's turn).

    python3 runs/experiments/audit195/stays_seeds.py <out dir>
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

A = Path("/home/diego/projects/ic2-conquest/artifacts")
GAMES = {"rome": "run-exp-longrun-v090/rome-rulebot1-40t", "carthage": "run-exp-longrun-v090/carthage-rulebot1-40t",
         "gaul": "run-exp-longrun-v090/gaul-rulebot1-40t", "ptolemaic": "run-exp-longrun-v091/ptolemaic-rulebot1-40t",
         "numidia": "run-exp-longrun-v092/numidia-rulebot1-40t", "greece": "run-exp-longrun-v092/greece-rulebot1-40t"}
# the 9 own-capital stays rows of stays-168dbc04-ts-v1.txt other than Greece t21 (X2): (game, turn)
ROWS = [("rome", 10), ("carthage", 33), ("carthage", 35), ("gaul", 29), ("ptolemaic", 9), ("numidia", 6), ("numidia", 11),
        ("greece", 6)]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    out = Path(sys.argv[1])
    starts = out / "starts"
    starts.mkdir(exist_ok=False)
    seeds, check, bad = {}, {}, 0
    for g, t in ROWS:
        stored, regen = A / GAMES[g] / "original", out / "regen" / f"{g}-rulebot1" / "original"
        names = sorted(p.name for p in stored.glob("t*.SAV") if p.name < f"t{t:02d}-")
        diff = [n for n in names if not (regen / n).exists() or sha(regen / n) != sha(stored / n)]
        start = names[-1]
        rs = None
        for l in (regen / "receipt.jsonl").read_text().splitlines():
            r = json.loads(l)
            if r.get("kind") == "randseed_after" and r.get("checkpoint") == Path(start).stem:
                rs = r["value"]
        check[f"{g}-t{t:02d}"] = {"compared": len(names), "differ": diff, "start": start, "randseed": rs}
        if diff or rs is None:
            bad += 1
            continue
        dst = starts / f"{g}-t{t:02d}.SAV"
        shutil.copy(stored / start, dst)
        seeds[dst.stem] = rs
    (starts / "seeds.json").write_text(json.dumps(seeds, indent=1))
    (out / "regen-check.json").write_text(json.dumps(check, indent=1))
    print(json.dumps(check, indent=1))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
