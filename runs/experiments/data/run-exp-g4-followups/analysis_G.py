#!/usr/bin/env python3
"""Check G, offline: the storm outcomes of g4_checks-G-<stamp>.jsonl (`storm_trial` lines) per arm (where = near an own city / away; cell = covered-cell word 0 calm / 1 rough; condition).
Prediction from the decompile (FUN_004514ec 54553-54591, spring/summer/autumn): roll = Random(100 - cond); local = max(1, roll div 10); rough: local = min(8, 3 local);
 own city marker in the 3 x 3 (FUN_004494e4): local div 2; none: 2 local + 1. local < 6: condition -= local; else FUN_0044b4f8 (ships and condition both fall by about local-dependent 24-29 %, news 'is damaged in a storm').
Per arm the observed condition loss, ships lost and the storm news line are tabulated, with the number of trials; every trial is one draw of one RNG stream in one process.
Output analysis_G.txt (next free version)."""
import collections, json, sys
from pathlib import Path
D = Path(__file__).resolve().parent; sys.path.insert(0, str(D))
from versioned import write_new


def predicted(cond, rough, near):
    out = collections.Counter(); n = 100 - cond
    for roll in range(n):
        loc = max(1, roll // 10)
        if rough: loc = min(8, loc * 3)
        loc = loc // 2 if near else loc * 2 + 1
        out["loss%d" % loc if loc < 6 else "ships(local=%d)" % loc] += 1
    return {k: v / n for k, v in sorted(out.items())}


def main(files):
    L = ["# analysis_G: storm outcomes per arm"]; arms = collections.defaultdict(list)
    for f in files:
        for line in open(f):
            d = json.loads(line)
            if d.get("step") != "storm_trial" or not d.get("fleet2_after"): continue
            b, a = d["fleet2_before"][0], d["fleet2_after"]
            news = [t for t in d["autosave_news"] if "fleet belonging" in t]
            arms[(d["where"], d["cell"], d["cond"])].append((b[10] - a[10], b[9] - a[9], tuple(news), d["tag"], d["kept"]))
    for key in sorted(arms, key=lambda k: (k[2], k[0], k[1])):
        rows = arms[key]; where, cell, cond = key; cnt = collections.Counter((r[0], r[1], r[2]) for r in rows)
        L.append(f"{where:5s} {cell:5s} cond {cond}: {len(rows)} trials; (condition lost, ships lost, news) -> count: {dict(sorted(cnt.items(), key=lambda kv: str(kv[0])))}")
        L.append(f"      code prediction (distribution of the final local value): {predicted(cond, cell == 'rough', where == 'near')}")
        L.append("      trials: " + ", ".join(r[3] for r in rows))
    return L


if __name__ == "__main__":
    print(write_new(D / "analysis_G.txt", "\n".join(main(sorted(D.glob("g4_checks-G-*.jsonl")))) + "\n"))
