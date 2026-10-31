#!/usr/bin/env python3
"""AI fleet-phase decisions, original vs remake main, on equal round-start states (#174, owner 2026-10-31).

Original: difftest/probes/fleetphase_hook_run.py (patches/fleetphase_hook.py) logs, per own launched fleet, the port pick,
the stored route, position, moves, and FUN_0044f4f8's hunt score and target; the branch follows from F608's own tests
(fleetphase_hook.branch). Remake: the same rounds from the original's autosaves (the diplomacy run's AI logs):
"fleet phase: fleet-N BRANCH, support S, hunt H" (OriginalFleetPhase).

Per (start, round, nation, fleet index): branch and hunt score equal? A fleet the other side did not handle is listed.

    python3 runs/experiments/fleetphase/compare.py <orig_dir> <remake_ailog_dir> <report.json>
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "patches"))
import fleetphase_hook as FH  # noqa: E402

NATIONS = ["rome", "carthage", "seleucid", "ptolemaic", "macedonia", "numidia", "gaul", "greece", "celtiberia", "illyria",
           "dacia", "bithynia", "galatia", "armenia", "media", "thracia"]
LINE = re.compile(r"fleet phase: fleet-(\d+) ([a-z-]+), support (-?\d+), hunt (-?\d+)")


def main():
    orig, rdir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    rows, counts = [], Counter()
    for f in sorted(orig.glob("*-fleet.jsonl")):
        start = f.name[:-len("-fleet.jsonl")]
        by = defaultdict(list)
        for l in f.read_text().splitlines():
            r = json.loads(l)
            by[r["turn"]].append(r)
        for t in range(1, 6):
            o = {}
            recs = by.get(t, [])
            for i, r in enumerate(recs):
                if r["kind"] != "fleet":
                    continue
                nxt = recs[i + 1] if i + 1 < len(recs) else None
                hunt = nxt if nxt and nxt["kind"] == "hunt" and nxt["fleet"] == r["fleet"] else None
                br, dest = FH.branch(r, hunt)
                o[(r["nation"], r["fleet"])] = {"branch": br, "hunt": hunt["score"] if hunt else None, "dest": dest,
                                                "pos": r["pos"], "moves": r["moves"]}
            rem = {}
            ail = rdir / f"{start}-t{t:02d}-ailog.txt"
            for l in (ail.read_text().splitlines() if ail.exists() else []):
                nation, _, text = l.partition("\t")
                if m := LINE.search(text):
                    rem[(NATIONS.index(nation), int(m[1]))] = {"branch": m[2], "hunt": int(m[4]), "support": int(m[3])}
            for key in sorted(set(o) | set(rem)):
                a, b = o.get(key), rem.get(key)
                if a is None or b is None:
                    verdict = "only-original" if b is None else "only-remake"
                else:
                    hunt_eq = a["hunt"] is None or a["hunt"] == b["hunt"]
                    verdict = "same" if a["branch"] == b["branch"] and hunt_eq else "differs"
                counts[verdict] += 1
                rows.append({"start": start, "turn": t, "nation": NATIONS[key[0]], "fleet": key[1], "verdict": verdict,
                             "orig": a, "remake": b})
    with open(out, "x") as fh:
        json.dump({"counts": dict(counts), "rows": rows}, fh, indent=1)
    print(dict(counts))


if __name__ == "__main__":
    main()
