#!/usr/bin/env python3
"""Fleet routes, original vs remake main, per round (#174 fleet-0 attribution, owner 2026-10-31).

Original: difftest/probes/fleetphase_hook_run.py with IC2_FLEET_HOOK=fleetroute_hook (patches/fleetroute_hook.py) logs, per
seat, every route the army phase writes (FUN_0044d9a8's ferry rendezvous, FUN_0044dba8's aboard landing cell) and every fleet
the fleet phase FUN_0044f608 handles. Remake: the same rounds from those autosaves, `RemakeAdapter aiprobe ... fleetlog=`:
OriginalFleetRouteRequested and OriginalFleetDecision events, attributed to the seat whose AiTurnDecided marker follows them.

Per (start, round, nation, fleet): the route writes and the branch on each side. The fleet phase (F608) itself agrees wherever
both see the same route and moves (findings/2026-10-31-ai-fleets-vs-remake-main.md), so a differing branch is classified by
its input:
  same              equal branch ("none" in the original = "idle" in the remake: no route, no hunt, no port move)
  route-written     the army phase wrote a route on one side only (or different routes); the nation's army rows in the
                    army comparison (report-aidecide) are attached, with their verdicts
  moves             equal route state; the original's fleet has 0 moves at its turn (spent earlier in the round)
  other             anything else

    python3 runs/experiments/fleetroute174/compare.py <orig_dir> <remake_dir> <aidecide_report.json> <out.json>
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "patches"))
import fleetphase_hook as FH  # noqa: E402

NATIONS = ["rome", "carthage", "seleucid", "ptolemaic", "macedonia", "numidia", "gaul", "greece", "celtiberia", "illyria",
           "dacia", "bithynia", "galatia", "armenia", "media", "thracia"]


def original(path):
    """{(turn, nation, fleet): {"writes": [...], "branch": ..., "rec": ...}}"""
    by = defaultdict(list)
    for line in path.read_text().splitlines():
        r = json.loads(line)
        by[r["turn"]].append(r)
    out = defaultdict(lambda: {"writes": [], "branch": None})
    for t, recs in by.items():
        for i, r in enumerate(recs):
            key = (t, NATIONS[r["nation"]], r["fleet"])
            if r["kind"] in ("rendezvous", "aboard"):
                out[key]["writes"].append({k: r[k] for k in ("kind", "route", "army_point", "army", "target") if k in r})
            elif r["kind"] == "fleet":
                nxt = recs[i + 1] if i + 1 < len(recs) else None
                hunt = nxt if nxt and nxt["kind"] == "hunt" and nxt["fleet"] == r["fleet"] else None
                br, dest = FH.branch(r, hunt)
                out[key].update(branch=br, dest=dest, route=r["route"], pos=r["pos"], moves=r["moves"])
    return out


def remake(path):
    out = defaultdict(lambda: {"writes": [], "branch": None})
    pending = []
    for line in (path.read_text().splitlines() if path.exists() else []):
        e = json.loads(line)
        if "seat" in e:
            for ev in pending:
                d = ev["data"]
                fleet = int(d["FleetId"].split("-")[1])
                key = (e["seat"], fleet)
                if ev["type"] == "OriginalFleetRouteRequested":
                    out[key]["writes"].append({"route": [d["X"], d["Y"]]})
                elif ev["type"] == "OriginalFleetDecision":
                    out[key].update(branch=d["Branch"], dest=[d["X"], d["Y"]] if d["X"] is not None else None, port=d["PortId"])
            pending = []
        elif e["type"] in ("OriginalFleetRouteRequested", "OriginalFleetDecision"):
            pending.append(e)
    return out


def main():
    orig_dir, rdir, rep_path, out_path = (Path(a) for a in sys.argv[1:5])
    army_rows = defaultdict(list)
    for r in json.load(open(rep_path))["rows"]:
        army_rows[(r["start"], r["turn"], r["nation"])].append(
            {"army": r["army"], "verdict": r["verdict"], "diffs": r.get("diffs"), "orig_branch": r["orig"].get("branch"),
             "remake_kind": (r.get("remake") or {}).get("Kind"), "remake_target_army": (r.get("remake") or {}).get("TargetArmyId")})
    rows, counts = [], Counter()
    for f in sorted(orig_dir.glob("*-fleet.jsonl")):
        start = f.name[:-len("-fleet.jsonl")]
        o = original(f)
        for t in range(1, 6):
            rm = remake(rdir / f"{start}-t{t:02d}-fleetlog.jsonl")
            keys = {(n, fl) for (tt, n, fl) in o if tt == t} | set(rm)
            for n, fl in sorted(keys):
                a, b = o.get((t, n, fl)), rm.get((n, fl))
                if not a or a["branch"] is None or not b or b["branch"] is None:
                    if (a and a["branch"]) or (b and b["branch"]):
                        counts["one-side"] += 1
                        rows.append({"start": start, "turn": t, "nation": n, "fleet": fl, "cause": "one-side",
                                     "orig": a and dict(a), "remake": b and dict(b)})
                    continue
                ob = "idle" if a["branch"] == "none" else a["branch"]
                ow = [w["route"] for w in a["writes"]]
                rw = [w["route"] for w in b["writes"]]
                if ob == b["branch"]:
                    cause = "same"
                elif (ow[-1:] or None) != (rw[-1:] or None):
                    cause = "route-written"
                elif a["moves"] <= 0:
                    cause = "moves"
                else:
                    cause = "other"
                counts[cause] += 1
                rows.append({"start": start, "turn": t, "nation": n, "fleet": fl, "cause": cause, "orig": dict(a),
                             "remake": dict(b), "army_rows": army_rows.get((start, t, n), []) if cause != "same" else None})
    with open(out_path, "x") as fh:
        json.dump({"counts": dict(counts), "rows": rows}, fh, indent=1)
    print(dict(counts))
    for r in rows:
        if r["cause"] not in ("same",):
            print(r["start"][:3], r["turn"], r["nation"], r["fleet"], r["cause"], "orig", r["orig"] and r["orig"].get("branch"),
                  r["orig"] and [w["route"] for w in r["orig"]["writes"]], "| remake", r["remake"] and r["remake"].get("branch"),
                  r["remake"] and [w["route"] for w in r["remake"]["writes"]], "| armies",
                  [(x["army"], x["verdict"]) for x in (r.get("army_rows") or [])])


if __name__ == "__main__":
    main()
