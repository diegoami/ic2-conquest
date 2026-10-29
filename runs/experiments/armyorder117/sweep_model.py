#!/usr/bin/env python3
"""Research #117: does the original's sweep (FUN_0044adb0 -> FUN_0044abe0, swap-remove from the top) explain every observed
reorder? Deaths happen during different seats and each seat is preceded by a sweep, so the test tries every ordered partition
of the dead records into successive sweeps (each sweep removes the deaths of one batch, top index first) and reports whether one
reproduces the post table's survivor order exactly. Reads order-in-play-<v>.json's transitions; writes sweep-model-<version>.json.

    python3 runs/experiments/armyorder117/sweep_model.py --input v1 --version v1
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import order_in_play as O  # noqa: E402
from state import sav  # noqa: E402


def sweep(tab, dead):
    tab = list(tab)
    k = len(tab) - 1
    while k >= 0:
        if k < len(tab) and tab[k] in dead:
            tab[k] = tab[-1]
            tab.pop()
            continue
        k -= 1
    return tab


def partitions(items):
    """Ordered set partitions of items (successive sweeps)."""
    items = list(items)
    if not items:
        yield []
        return
    for r in range(1, len(items) + 1):
        for first in itertools.combinations(items, r):
            rest = [x for x in items if x not in first]
            for p in partitions(rest):
                yield [set(first)] + p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    out = O.DATA / f"sweep-model-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for r in json.loads((O.DATA / f"order-in-play-{a.input}.json").read_text()):
        if not r["died_or_merged"]:
            continue
        c = O.CAMP / r["campaign"] / "original"
        pre, post = sav.parse((c / r["pre"]).read_bytes()), sav.parse((c / r["post"]).read_bytes())
        L, P = O.live(pre), O.live(post)
        m = O.match(L, P)
        dead = [i for i, _ in L if i not in m.values()]
        actual = [m[j] for j, _ in P if j in m]
        start = [i for i, _ in L]
        found = []
        for p in partitions(dead):
            tab = start
            for batch in p:
                tab = sweep(tab, batch)
            if tab == actual:
                found.append([sorted(b) for b in p])
        remake = [i for i in start if i not in dead]
        rows.append({"campaign": r["campaign"], "turn": r["turn"], "dead_pre_indices": dead, "actual": actual,
                     "remake_rule": remake, "differs_from_remake_rule": actual != remake,
                     "sweep_sequences_reproducing": found[:4], "explained": bool(found)})
        print(r["campaign"], r["turn"], "dead", dead, "explained", bool(found), found[:2], "differs", actual != remake)
    out.write_text(json.dumps(rows, indent=1))
    print("explained", sum(x["explained"] for x in rows), "of", len(rows), "; differ from the remake rule",
          sum(x["differs_from_remake_rule"] for x in rows))


if __name__ == "__main__":
    main()
