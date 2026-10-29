#!/usr/bin/env python3
"""Research #123: summarise the capital-defence hook logs (difftest/probes/capdef_hook_run.py, patches/capdef_hook.py).

    python3 runs/experiments/capdef123/analyze.py artifacts/run-exp-capdef123 --version v1

A call of FUN_0044efc8 = its threat records followed by its compare/accept records (a new threat record after a compare,
or a new nation or turn, starts the next call). Per call: threats listed (count_before < 9) and dropped by the cap
(count_before = 9: the record overwrites the uncounted tenth slot). Per responder: its candidates (compare records), the
eligible ones (the current nation at war with the owner, relation >= 3, or the responder 20 or more from its capital), the
chosen threat (the last accept) and its distance; a TIE when two or more eligible candidates share the chosen distance (the
first in list order wins, and the list is in table order); CROSS-NATION when their owners differ.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "runs/experiments/data/run-exp-capdef123"


def calls(recs):
    cur, prev = None, None
    for r in recs:
        new = cur is None or r["turn"] != cur["turn"] or r["nation"] != cur["nation"] or (r["kind"] == "threat" and prev != "threat")
        if new:
            if cur:
                yield cur
            cur = {"turn": r["turn"], "nation": r["nation"], "threats": [], "dropped": [], "responders": {}}
        if r["kind"] == "threat":
            (cur["threats"] if r["count_before"] < 9 else cur["dropped"]).append(r["threat"])
        else:
            resp = cur["responders"].setdefault(r["responder"], {"compares": [], "accepts": []})
            resp["compares" if r["kind"] == "compare" else "accepts"].append(r)
        prev = r["kind"]
    if cur:
        yield cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"summary-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    tot = {"calls": 0, "calls_with_threats": 0, "calls_with_dropped_threats": 0, "dropped_threats": 0, "decisions": 0,
           "dispatches": 0, "ties": 0, "ties_cross_nation": 0}
    starts = []
    for log in sorted(a.folder.glob("*-capdef.jsonl")):
        recs = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        ties, drops = [], []
        for c in calls(recs):
            tot["calls"] += 1
            tot["calls_with_threats"] += bool(c["threats"])
            if c["dropped"]:
                tot["calls_with_dropped_threats"] += 1
                tot["dropped_threats"] += len(c["dropped"])
                drops.append({"turn": c["turn"], "nation": c["nation"], "listed": len(c["threats"]), "dropped": len(c["dropped"])})
            for resp, d in c["responders"].items():
                tot["decisions"] += 1
                if not d["accepts"]:
                    continue
                tot["dispatches"] += 1
                chosen = d["accepts"][-1]
                elig = [x for x in d["compares"] if x["threat_owner"] >= 0 and (x["relation"] >= 3 or x["responder_to_capital"] >= 20)]
                tied = [x for x in elig if x["distance"] == chosen["distance"]]
                if len({x["threat"] for x in tied}) >= 2:
                    owners = sorted({x["threat_owner"] for x in tied})
                    tot["ties"] += 1
                    tot["ties_cross_nation"] += len(owners) > 1
                    ties.append({"turn": c["turn"], "nation": c["nation"], "responder": resp, "distance": chosen["distance"],
                                 "tied_threats": [x["threat"] for x in tied], "owners": owners, "chosen": chosen["threat"]})
        starts.append({"log": log.name, "ties": ties, "drops": drops,
                       "inert": json.loads((a.folder / log.name[:-len('-capdef.jsonl')] / "inert.json").read_text()).get("per_turn")
                       if (a.folder / log.name[:-len('-capdef.jsonl')] / "inert.json").exists() else None})
    out.write_text(json.dumps({"totals": tot, "starts": starts}, indent=1))
    print(tot)
    for s in starts:
        for t in s["ties"]:
            print(s["log"], "TIE", t)
        for d in s["drops"]:
            print(s["log"], "CAP", d)


if __name__ == "__main__":
    main()
