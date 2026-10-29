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
        # v3: the raw pre table. Dead records already in it (the previous round's last AI seats) are swept by this End
        # turn's first sweep; a death whose record is still a dead record in the post table was never swept (it happened
        # after the last sweep), so it leaves the live order without moving anything.
        raw = list(range(len(pre["armies"])))
        pre_dead = [i for i in raw if pre["armies"][i]["owner"] < 0]
        post_tomb_sigs = [O.sig(x) for x in post["armies"] if x["owner"] < 0 and O.sig(x)]
        post_tomb_cells = [(x["x"], x["y"]) for x in post["armies"] if x["owner"] < 0]
        # a dead record keeps its cell; one emptied by its battle also has all unit troops at 0 (no signature left)
        unswept = [i for i in dead if O.sig(pre["armies"][i]) in post_tomb_sigs
                   or (pre["armies"][i]["x"], pre["armies"][i]["y"]) in post_tomb_cells]
        swept = [i for i in dead if i not in unswept]
        found = []
        for p in partitions(swept):
            # the old dead records go in the End turn's first sweep, alone or with the first batch of new deaths
            options = [[set(pre_dead)] + p, [set(pre_dead) | p[0]] + p[1:]] if (pre_dead and p) else [[set(pre_dead)] + p if pre_dead else p]
            for batches in options:
                tab = raw
                for batch in batches:
                    tab = sweep(tab, batch)
                tab = [k for k in tab if k not in unswept and k not in pre_dead and k not in swept]
                if tab == actual:
                    found.append([sorted(b) for b in batches])
        if not swept and pre_dead:
            tab = [k for k in sweep(raw, set(pre_dead)) if k not in unswept]
            if tab == actual:
                found.append([])
        start = [i for i, _ in L]
        remake = [i for i in start if i not in dead]
        rows.append({"campaign": r["campaign"], "turn": r["turn"], "dead_pre_indices": dead, "pre_dead_records": pre_dead,
                     "unswept_deaths": unswept, "actual": actual,
                     "remake_rule": remake, "differs_from_remake_rule": actual != remake,
                     "sweep_sequences_reproducing": found[:4], "explained": bool(found)})
        print(r["campaign"], r["turn"], "dead", dead, "explained", bool(found), found[:2], "differs", actual != remake)
    out.write_text(json.dumps(rows, indent=1))
    print("explained", sum(x["explained"] for x in rows), "of", len(rows), "; differ from the remake rule",
          sum(x["differs_from_remake_rule"] for x in rows))


if __name__ == "__main__":
    main()
