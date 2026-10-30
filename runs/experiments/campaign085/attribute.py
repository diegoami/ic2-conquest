#!/usr/bin/env python3
"""Attribute the remaining original-vs-remake differences of the #232 bot campaigns at remake v0.8.5 (owner, 2026-10-30).

For a campaign and turn, compare the original's End-turn checkpoint (paired from receipt.jsonl, memory
campaign-checkpoints-per-action) with the remake's state after the same turn in the v0.8.5 recheck
(artifacts/run-exp-recheck-1622407e/campaigns-v2/), and group the differing fields: path with record indices folded
("cities.*.supplies", "nations.Rome.treasury", "armies.*.x"), with counts and examples.

    python3 runs/experiments/campaign085/attribute.py groups <campaign> <turn> [--prev]
    python3 runs/experiments/campaign085/attribute.py all --version v1     # turn 1 of every campaign + allhuman turns 15-17
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from difftest.compare import compare  # noqa: E402
from state.sav import load  # noqa: E402

ORIG = {"allhuman": ROOT / "artifacts/run-exp-diff084-allhuman", "campaign": ROOT / "artifacts/run-exp-diff084-campaign"}
REMAKE = ROOT / "artifacts/run-exp-recheck-1622407e/campaigns-v2"
DATA = ROOT / "runs/experiments/data/run-exp-campaign085"


def orig_dir(name):
    for d in ORIG.values():
        if (d / name).exists():
            return d / name
    raise SystemExit(f"no original campaign {name}")


def remake_dir(name):
    hits = list(REMAKE.glob(f"*/{name}"))
    if not hits:
        raise SystemExit(f"no remake campaign {name}")
    return hits[0]


def orig_save(name, k):
    """The original state after End turn k (k = 0: the start)."""
    c = orig_dir(name)
    if k == 0:
        return load(c / "original" / "t00-start.SAV")
    acts = [json.loads(l) for l in (c / "original" / "receipt.jsonl").read_text().splitlines() if l.strip()]
    ends = [x["checkpoint"] for x in acts if x.get("kind") == "action" and x["action"]["op"] == "end_turn" and not x.get("error")]
    return load(c / "original" / f"{ends[k - 1]}.SAV")


def remake_save(name, k):
    t = remake_dir(name) / f"t{k:02d}"
    names = [l.split(" ", 1)[1].strip() for l in (t / "commands.txt").read_text().splitlines() if l.startswith("#checkpoint ")]
    return load(t / f"{names[-1]}.SAV") if names else load(t / "a000.SAV")


def fold(path):
    return re.sub(r"\.\d+(?=\.|$)", ".*", path)


def groups(a, b):
    d = compare(a, b)
    g = defaultdict(list)
    for f in d["fields"]:
        g[fold(f["path"])].append(f)
    rows = sorted(({"group": k, "count": len(v), "examples": [{"path": x["path"], "original": x["a"], "remake": x["b"]} for x in v[:4]]}
                   for k, v in g.items()), key=lambda r: -r["count"])
    codes = Counter((c["a"] // 100 if c["a"] >= 0 else -1, c["b"] // 100 if c["b"] >= 0 else -1) for c in d["map"]["first"])
    return {"fields": len(d["fields"]), "map_cells": d["map"]["count"], "groups": rows,
            "map_first": d["map"]["first"][:12]}


def show(r, n=30):
    print(f"  {r['fields']} fields, {r['map_cells']} map cells")
    for g in r["groups"][:n]:
        ex = "; ".join(f"{e['path']}: {e['original']!r} vs {e['remake']!r}" for e in g["examples"][:2])
        print(f"  {g['count']:4d}  {g['group']:40s} {ex[:150]}")
    for c in r["map_first"][:6]:
        print(f"  map ({c['x']},{c['y']}): {c['a']} vs {c['b']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["groups", "all"])
    ap.add_argument("campaign", nargs="?")
    ap.add_argument("turn", nargs="?", type=int)
    ap.add_argument("--version", default="v1")
    a = ap.parse_args()
    if a.what == "groups":
        r = groups(orig_save(a.campaign, a.turn), remake_save(a.campaign, a.turn))
        print(f"{a.campaign} turn {a.turn}:")
        show(r)
        return
    out = {}
    for c in sorted(p.name for p in REMAKE.glob("*/*") if p.is_dir()):
        turns = [1] if not c.startswith("allhuman") else [15, 16, 17]
        for k in turns:
            r = groups(orig_save(c, k), remake_save(c, k))
            out[f"{c}:t{k}"] = r
            print(f"{c} turn {k}:")
            show(r, 12)
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / f"groups-{a.version}.json", "x") as f:
        json.dump(out, f, indent=1, default=str)


if __name__ == "__main__":
    main()
