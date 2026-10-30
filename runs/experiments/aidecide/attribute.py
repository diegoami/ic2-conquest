#!/usr/bin/env python3
"""Attribute every row of a compare.py report to one cause (owner 2026-10-30, AI decisions vs remake main).

    python3 runs/experiments/aidecide/attribute.py <report.json> <out.json>

Causes, checked in this order (the finding 2026-10-30-ai-decisions-vs-remake-main.md gives the evidence for each):
  same                 the branch, targets and scores agree (or the remake's unlogged garrison move after a run without offer)
  diplomacy            the nation's wars changed during the original's round, or differ from the remake's at its end
  state                an attack or a death earlier in the round (battle results are random draws)
  capdef-attack        the remake's capital defence dispatched this army; the original's responder had attacked the threat
                       on arrival (FUN_0044dba8), so it was dead before this army's turn
  f4c7-city-target     after the mercenary run, "city > 85" marches at the CITY TARGET in the original (0x44F4C7, [esp+2]);
                       the remake marches at the resupply city (DefendResupplyCity)
  h925-resupply        the resupply destination differs: the remake's reachable-resupply tier (#925) replaced F670's pick
  h925-fallback        the remake's chosen branch offered no usable command and its #925 garrison/emergency tier moved the army
  unattributed         anything else (listed in the output)
"""
import json
import sys
from collections import Counter


def cause(r):
    v = r["verdict"]
    if v in ("same", "same-unlogged"):
        return "same"
    if v == "diplomacy":
        return "diplomacy"
    if v in ("state-battle", "state-death", "state"):
        return "state"
    if r.get("remake_capdef"):
        return "capdef-attack"
    if r["orig"]["branch"] == "e84c+city>85":
        return "f4c7-city-target"
    if v == "differs" and r.get("diffs") == ["resupply-city"]:
        return "h925-resupply"
    if v == "no-remake-decision" and (r.get("remake_why") or "").startswith(("garrison fallback", "emergency move")):
        return "h925-fallback"
    return "unattributed"


def main():
    rep = json.load(open(sys.argv[1]))
    counts, left = Counter(), []
    for r in rep["rows"]:
        c = cause(r)
        r["cause"] = c
        counts[c] += 1
        if c == "unattributed":
            left.append(r)
    out = {"counts": dict(counts), "rows": len(rep["rows"]), "unattributed": left}
    with open(sys.argv[2], "x") as f:
        json.dump(out, f, indent=1)
    print(dict(counts))
    for r in left:
        print(r["start"][:3], r["turn"], r["nation"], r["army"], r["verdict"], r.get("diffs"), r["orig"]["branch"],
              (r.get("remake") or {}).get("Kind"), r.get("remake_why"))


if __name__ == "__main__":
    main()
