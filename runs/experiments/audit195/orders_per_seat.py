#!/usr/bin/env python3
"""#195 X4: how close AI seats come to the remake's per-seat action cap (classical-faithful maxActionsPerTurn 24).

    python3 runs/experiments/audit195/orders_per_seat.py <artifacts dir> [anchored folder name]

Reads every anchored replay receipt (<artifacts>/run-exp-*/*/<folder>/tNN/receipt.jsonl) and the remake's End-turn report
lines "<Nation> (<id>) takes its turn: N orders issued.", and prints the distribution of N and the seats with N >= 20.
N counts accepted orders; the cap counts candidate-loop iterations (AiTurn.cs:241), so N < 24 does not prove the cap
never bound, but N <= 20 leaves at most 4 non-order iterations.
"""
import collections
import glob
import json
import re
import sys

root = sys.argv[1]
folder = sys.argv[2] if len(sys.argv) > 2 else "anchored-168dbc04-ts"
dist, high, games = collections.Counter(), [], set()
for rec in sorted(glob.glob(f"{root}/run-exp-*/*/{folder}/t*/receipt.jsonl")):
    game = rec.split(f"/{folder}")[0].split(root.rstrip("/") + "/")[1]
    games.add(game)
    for line in open(rec):
        r = json.loads(line)
        if r.get("kind") != "command" or not r["command"].startswith("end"):
            continue
        for out in r.get("lines", []):
            m = re.match(r"(\w+) \(\w+\) takes its turn: (\d+) orders? issued", out)
            if m:
                n = int(m.group(2))
                dist[n] += 1
                if n >= 20:
                    high.append((game, rec.split("/")[-2], m.group(1), n))
print(f"folder {folder}: {len(games)} games, {sum(dist.values())} AI seats")
print("orders issued -> seats:", ", ".join(f"{k}:{v}" for k, v in sorted(dist.items())))
print(f"max {max(dist)}; seats >= 20: {high}")
