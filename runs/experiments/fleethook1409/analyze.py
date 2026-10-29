#!/usr/bin/env python3
"""imperial_conquest_2#1409: summarise the AI fleet hook logs (difftest/probes/fleet_hook_run.py, patches/fleet_hook.py).

    python3 runs/experiments/fleethook1409/analyze.py artifacts/run-exp-fleethook1409 --version v1

Groups the records into top-level calls of FUN_0044e1fc (a call starts at an entry record whose caller is not the recursion site)
and reports per call: fleet, nation, target, start/end cell and moves, branch of each level (direct / D174 point, mapped to the
remake's ClassicalArmyNavigation waypoint id when it is one), CEC8 fallback points, recursion depth. Also: inertness per start.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "runs/experiments/data/run-exp-fleethook1409"


def waypoints():
    src = (Path.home() / "projects/ic2-remake-v084/src/IC2.Engine/Ai/ClassicalArmyNavigation.Data.cs").read_text()
    return {(int(x), int(y)): int(i) for x, y, i in re.findall(r"new\((\d+), (\d+)\), // (\d+)", src)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    out = DATA / f"summary-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    DATA.mkdir(parents=True, exist_ok=True)
    wp = waypoints()
    report = {"starts": [], "totals": Counter()}
    for log in sorted(a.folder.glob("*-fleet*.jsonl")):
        recs = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        calls, cur = [], None
        for r in recs:
            if r["kind"] == "entry_direct_test" and r["caller"] not in ("recursion", "0x44e302"):
                cur = {"turn": r["turn"], "nation": r["nation"], "fleet": r["fleet"], "target": r["target"], "start": [r["x"], r["y"]],
                       "moves_start": r["moves"], "levels": [], "cec8": [], "recursions": 0}
                calls.append(cur)
            if cur is None:
                continue
            if r["kind"] == "entry_direct_test":
                cur["levels"].append({"direct": r["direct"], "at": [r["x"], r["y"]], "moves": r["moves"]})
            elif r["kind"] == "d174_point":
                p = tuple(r["point"])
                cur["levels"][-1]["d174"] = list(p)
                cur["levels"][-1]["waypoint_id"] = wp.get(p)
            elif r["kind"] == "cec8_point":
                cur["cec8"].append({"point": r["point"], "at": [r["x"], r["y"]], "moves": r["moves"]})
            elif r["kind"] == "recursion":
                cur["recursions"] += 1
            elif r["kind"] == "after_moves" and r["caller"] not in ("recursion", "0x44e302"):
                cur["end"] = [r["x"], r["y"]]
                cur["moves_end"] = r["moves"]
        inert = json.loads((a.folder / log.name.split("-fleet")[0] / "inert.json").read_text()) if (a.folder / log.name.split("-fleet")[0] / "inert.json").exists() else None
        t = Counter()
        for c in calls:
            t["calls"] += 1
            t["levels"] += len(c["levels"])
            t["direct_levels"] += sum(l["direct"] == 1 for l in c["levels"])
            t["d174_levels"] += sum("d174" in l for l in c["levels"])
            t["d174_points_in_table"] += sum(l.get("waypoint_id") is not None for l in c["levels"])
            t["d174_none"] += sum(l.get("d174", [0])[0] == -1 for l in c["levels"])
            t["cec8_calls"] += len(c["cec8"])
            t["cec8_none"] += sum(x["point"][0] == -1 for x in c["cec8"])
            t["recursive_calls"] += c["recursions"] > 0
            t["max_depth"] = max(t["max_depth"], c["recursions"])
        report["starts"].append({"log": log.name, "records": len(recs), "counts": dict(t),
                                 "inert": None if inert is None else {"identical": inert["identical"], "per_turn": inert["per_turn"]},
                                 "calls": calls})
        report["totals"].update({k: v for k, v in t.items() if k != "max_depth"})
    report["totals"] = dict(report["totals"])
    out.write_text(json.dumps(report, indent=1))
    for s in report["starts"]:
        print(s["log"], s["records"], s["counts"], "inert", s["inert"])
    print("totals", report["totals"])


if __name__ == "__main__":
    main()
