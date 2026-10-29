#!/usr/bin/env python3
"""Research #117 follow-up: count ties in the AI's enemy-army pick (FUN_0044ee60) in real AI turns, from the tie hook logs
(difftest/probes/tie_hook_run.py). A call is the candidate records up to its "chosen" record. A tie broken by table order = at
least two candidates share the top score; the chosen one is the first of them in table order. For each tie: the nations of
the tied candidates, their distances, and whether a farther candidate won over a nearer one. The owners come from the start
save for turn 1 and from the previous turn's hooked autosave for later turns (the table when the turn starts; an army
created or moved within the turn can still be misattributed: owners are a start-of-turn reading).

    python3 runs/experiments/tiehook117/analyze.py artifacts/run-exp-tiehook117 --version v1
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state import sav  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-tiehook117"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    out = DATA / f"summary-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    DATA.mkdir(parents=True, exist_ok=True)
    starts, totals = [], {"calls": 0, "calls_with_candidates": 0, "ties": 0, "ties_cross_nation": 0, "ties_farther_won": 0,
                          "starts": 0, "inert": 0}
    for log in sorted(a.folder.glob("*-ties.jsonl")):
        stem = log.name[:-len("-ties.jsonl")]
        tables = {1: sav.parse((a.folder / "starts" / f"{stem}.SAV").read_bytes())}
        for f in sorted((a.folder / stem).glob("hooked-t*-*.SAV")):
            tables[int(f.name[8:10]) + 1] = sav.parse(f.read_bytes())       # the table at the start of the next turn

        def owner(i, turn):
            """The owner in the table at the start of `turn` (the start save, or the previous turn's hooked autosave)."""
            t = tables.get(turn)
            return t["armies"][i]["owner"] if t and 0 <= i < len(t["armies"]) else None
        recs = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        calls, cur = [], []
        for r in recs:
            if r["kind"] == "candidate":
                cur.append(r)
            else:
                calls.append({"actor": r["actor"], "nation": r["nation"], "chosen": r["index"], "score": r["score"], "cands": cur,
                              "turn": r.get("turn", 1)})
                cur = []
        ties = []
        for c in calls:
            if not c["cands"]:
                continue
            top = max(x["score"] for x in c["cands"])
            tied = [x for x in c["cands"] if x["score"] == top]
            if len(tied) >= 2:
                d = [x["distance"] for x in tied]
                won = next(x for x in tied if x["index"] == c["chosen"])
                ties.append({"turn": c["turn"], "actor": c["actor"], "nation": c["nation"], "score": top,
                             "tied": [x["index"] for x in tied],
                             "tied_owners": [owner(x["index"], c["turn"]) for x in tied], "tied_distances": d, "chosen": c["chosen"],
                             "chosen_is_first": c["chosen"] == tied[0]["index"], "farther_won": won["distance"] > min(d)})
        inert = json.loads((a.folder / stem / "inert.json").read_text())["identical"] if (a.folder / stem / "inert.json").exists() else None
        s = {"start": stem, "calls": len(calls), "calls_with_candidates": sum(1 for c in calls if c["cands"]), "ties": ties,
             "inert": inert}
        starts.append(s)
        totals["starts"] += 1
        totals["inert"] += bool(inert)
        totals["calls"] += s["calls"]
        totals["calls_with_candidates"] += s["calls_with_candidates"]
        totals["ties"] += len(ties)
        totals["ties_cross_nation"] += sum(1 for t in ties if len(set(t["tied_owners"])) > 1)
        totals["ties_farther_won"] += sum(1 for t in ties if t["farther_won"])
    out.write_text(json.dumps({"totals": totals, "starts": starts}, indent=1))
    print(totals)
    for s in starts:
        for t in s["ties"]:
            print(s["start"], t)


if __name__ == "__main__":
    main()
