#!/usr/bin/env python3
"""Research #117 follow-up: the original's FLEET table order across real End turns where a fleet disappears (sunk, scuttled,
merged), against the remake's rule (removed fleets filtered out, the rest kept in order; v0.8.4 AiAbsorbFleetCommandHandler,
FleetTickSystem). Sources: the #232 campaigns (End-turn pairs from receipt.jsonl, as order_in_play.py v3) and the 30-turn
tie-hook runs (consecutive hooked autosaves, the start save before turn 1), and the #233 storm30 original trials (a001 -> a002:
the End turn in which Carthage's fleet hunts Rome's fleet 2). Fleet identity: same owner, then the smallest
change in (ships, condition) and position; dead fleet records (owner -1) and records past the count are not live. The model:
every ordered grouping of the removed fleets into successive sweeps (FUN_0044ad7c: the last record into the freed slot).

    python3 runs/experiments/armyorder117/fleet_order.py --version v1
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import order_in_play as O  # noqa: E402
from sweep_model import partitions, sweep  # noqa: E402
from state import sav  # noqa: E402

LONG = O.ROOT / "artifacts/run-exp-tiehook117-long"
STORM = O.ROOT / "artifacts/run-exp-diff084-stats/storm30"      # #233: Rome's fleet 2 moves to (97,48), then End turn


def live(s):
    return [(i, f) for i, f in enumerate(s["fleets"]) if f["owner"] >= 0 and f["ships"] > 0]


def match(pre, post):
    pairs = []
    for j, b in post:
        for i, a in pre:
            if a["owner"] != b["owner"]:
                continue
            cost = abs(a["ships"] - b["ships"]) * 10 + abs(a.get("condition", 0) - b.get("condition", 0)) + max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))
            if b["ships"] > a["ships"] + 40:            # grew by more than a plausible merge/build: not the same fleet
                continue
            pairs.append((cost, i, j))
    m, used = {}, set()
    for cost, i, j in sorted(pairs):
        if i in used or j in m:
            continue
        m[j] = i
        used.add(i)
    return m


def pairs_iter():
    for c in sorted(p for p in O.CAMP.iterdir() if (p / "original" / "receipt.jsonl").exists()):
        for t, (pre, post) in enumerate(O.end_turn_pairs(c), 1):
            a, b = c / "original" / f"{pre}.SAV", c / "original" / f"{post}.SAV"
            if a.exists() and b.exists():
                yield "campaign", c.name, t, a, b
    for d in sorted(p for p in LONG.iterdir() if p.is_dir() and p.name != "starts"):
        saves = sorted(d.glob("hooked-t*-*.SAV"))
        prev = LONG / "starts" / f"{d.name}.SAV"
        for t, f in enumerate(saves, 1):
            yield "long", d.name, t, prev, f
            prev = f
    for d in sorted(STORM.glob("original-s*"), key=lambda p: int(p.name.split("-s")[1])):
        if (d / "a001.SAV").exists() and (d / "a002.SAV").exists():
            yield "storm30", d.name, 1, d / "a001.SAV", d / "a002.SAV"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    out = O.DATA / f"fleet-order-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for src, name, t, a, b in pairs_iter():
        pre, post = sav.parse(a.read_bytes()), sav.parse(b.read_bytes())
        L, P = live(pre), live(post)
        m = match(L, P)
        gone = [i for i, _ in L if i not in m.values()]
        if not gone:
            continue
        actual = [m[j] for j, _ in P if j in m]
        raw = list(range(len(pre["fleets"])))
        pre_dead = [i for i in raw if i not in dict(L)]
        found = []
        for p in partitions(gone):
            for batches in ([set(pre_dead)] + p, [set(pre_dead) | p[0]] + p[1:]) if pre_dead else (p,):
                tab = raw
                for batch in batches:
                    tab = sweep(tab, batch)
                tab = [k for k in tab if k not in gone and k not in pre_dead]
                if tab == actual:
                    found.append([sorted(x) for x in batches])
        remake = [i for i, _ in L if i not in gone]
        rows.append({"source": src, "run": name, "turn": t, "pre": a.name, "post": b.name, "pre_live": len(L), "post_live": len(P),
                     "gone": gone, "new": [j for j, _ in P if j not in m], "actual": actual, "remake_rule": remake,
                     "order_kept": actual == remake, "explained": bool(found), "sweeps": found[:2],
                     "same_owner_inversions": [[x, y] for x, y in itertools.combinations(actual, 2)
                                               if pre["fleets"][x]["owner"] == pre["fleets"][y]["owner"]
                                               and (actual.index(x) < actual.index(y)) != (remake.index(x) < remake.index(y))]})
        r = rows[-1]
        print(src, name, t, "live", r["pre_live"], "->", r["post_live"], "gone", gone, "new", r["new"], "kept", r["order_kept"],
              "explained", r["explained"], "same-owner inv", r["same_owner_inversions"])
    out.write_text(json.dumps(rows, indent=1))
    print("turns with a fleet gone", len(rows), "order kept", sum(r["order_kept"] for r in rows), "explained",
          sum(r["explained"] for r in rows), "with same-owner inversions", sum(bool(r["same_owner_inversions"]) for r in rows))


if __name__ == "__main__":
    main()
