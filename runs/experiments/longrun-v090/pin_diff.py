#!/usr/bin/env python3
"""Position rows of two anchored replays of the same campaigns (a pin recheck, 2026-11-04).

    python3 runs/experiments/longrun-v090/pin_diff.py OLD_FOLDER NEW_FOLDER <campaign_dir> [...]

A position row is (turn, nation, armies|fleets) where, after End turn, the nation's units stand on different tiles in the
original and the remake (classify.kinds_of "position"/"count"). For each campaign: errors, row counts old -> new, and the
rows gone and new. OLD_FOLDER may be a comma list tried in order (the first that exists), e.g. anchored-a44c42fc-ts,anchored-turnseed.
The last attempt of a retried turn wins.
"""
import json
import sys
from pathlib import Path


def rows(path):
    last = {}
    for l in path.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            last[r["turn"]] = r
    return last


def positions(last):
    out, errors = set(), 0
    for t, r in last.items():
        if r.get("remake_errors") or "error" in r:
            errors += 1
        for n, d in r.get("ai", {}).get("nations", {}).items():
            for kind in ("armies", "fleets"):
                if kind in d:
                    x = d[kind]
                    pa = sorted((u[0], u[1]) for u in x["only_original"])
                    pb = sorted((u[0], u[1]) for u in x["only_remake"])
                    if pa != pb or x["count"][0] != x["count"][1]:
                        out.add((t, n, kind))
    return out, errors


def main():
    old, new, camps = sys.argv[1].split(","), sys.argv[2], sys.argv[3:]
    for c in map(Path, camps):
        o = next((c / f / "turns.jsonl" for f in old if (c / f / "turns.jsonl").exists()), None)
        n = c / new / "turns.jsonl"
        if not o or not n.exists():
            print(f"{c.name}: missing {'old' if not o else 'new'}")
            continue
        lo, ln = rows(o), rows(n)
        po, eo = positions(lo)
        pn, en = positions(ln)
        print(f"{c.name}: {len(ln)} turns, errors {eo} -> {en}; position rows {len(po)} -> {len(pn)} ({o.parent.name} -> {new})")
        print(f"   gone: {sorted(po - pn)}")
        print(f"   new : {sorted(pn - po)}")


if __name__ == "__main__":
    main()
