#!/usr/bin/env python3
"""Research #117: the original's army-table order across real AI turns (End turn), against the remake's rule (dead armies
filtered out, the rest kept in order, new armies appended).

    python3 runs/experiments/armyorder117/order_in_play.py --version v1

Inputs: the #232 bot campaigns (artifacts/run-exp-diff084-campaign/<campaign>/original/tNN-aKK.SAV): for each turn, the last
save before End turn (tNN-a<last>) and the next turn's first (tNN+1-a00). Each live record (owner >= 0, troops > 0) is
identified by (owner, its unit names); a post record is matched to the pre record of the same owner sharing the most unit
names (at least one). Pre records left unmatched died (or merged); post records left unmatched are new. Also counted: dead
records still in the raw table (tombstones, owner -1) in the post save.
Output: runs/experiments/data/run-exp-armyorder117/order-in-play-<version>.json and a printed summary.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
from state import sav  # noqa: E402

CAMP = ROOT / "artifacts/run-exp-diff084-campaign"
DATA = ROOT / "runs/experiments/data/run-exp-armyorder117"


def live(s):
    return [(i, a) for i, a in enumerate(s["armies"]) if a["owner"] >= 0 and a["troops"] > 0]


def names(a):
    return {u.get("name", "") for u in a["units"] if u.get("troops", 0) > 0} - {""}


def sig(a):
    return {(u.get("name", ""), u["type"], u["quality"]) for u in a["units"] if u.get("troops", 0) > 0}


def score(a, b):
    """v2: same owner; shared (name, type, quality) units first, then equal troops per unit, then the distance moved.
    (v1 matched on unit names only: AI armies of one nation share names such as "1st Foot Battalion".)"""
    shared = len(sig(a) & sig(b))
    if not shared:
        return None
    troops = len({(u.get("name"), u["troops"]) for u in a["units"] if u.get("troops", 0) > 0}
                 & {(u.get("name"), u["troops"]) for u in b["units"] if u.get("troops", 0) > 0})
    dist = max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))
    return (shared, troops, -dist)


def match(pre, post):
    """Greedy on the best global pairs (not post-order first), so a later record cannot steal an earlier one's twin."""
    pairs = sorted(((score(a, b), i, j) for j, b in post for i, a in pre if a["owner"] == b["owner"] and score(a, b)),
                   key=lambda t: t[0], reverse=True)
    used_i, m = set(), {}
    for sc, i, j in pairs:
        if i in used_i or j in m:
            continue
        m[j] = i
        used_i.add(i)
    return m


def transition(pre_s, post_s):
    pre, post = live(pre_s), live(post_s)
    m = match(pre, post)
    survivors_pre_order = [i for i, _ in pre if i in m.values()]
    post_order = [m[j] for j, _ in post if j in m]               # survivors, by their pre index, in the post table's order
    died = [i for i, _ in pre if i not in m.values()]
    new = [j for j, _ in post if j not in m]
    tomb = sum(1 for a in post_s["armies"] if a["owner"] < 0)
    # The remake's rule: survivors keep their relative order.
    return {"pre_live": len(pre), "post_live": len(post), "died_or_merged": len(died), "new": len(new),
            "post_tombstones": tomb, "post_raw": len(post_s["armies"]),
            "order_preserved": post_order == survivors_pre_order,
            "moved": sum(1 for a, b in zip(post_order, survivors_pre_order) if a != b),
            "new_positions": new, "post_len": len(post)}


def end_turn_pairs(c):
    """v3: the receipt's end_turn actions. pre = the checkpoint before the End-turn click (t00-start for the first action),
    post = that action's checkpoint, the autosave written just before the human's StartTurn, after every AI seat.
    (v1/v2 paired the last checkpoint of turn NN with turn NN+1's a00, which is the next End turn's autosave only when the
    turn had no orders; otherwise it is the save after the next turn's first order, so those pairs missed the AI round.)"""
    acts = [json.loads(l) for l in (c / "original" / "receipt.jsonl").read_text().splitlines() if l.strip()]
    acts = [x for x in acts if x.get("kind") == "action" and x.get("checkpoint")]
    prev = "t00-start"
    for x in acts:
        if x["action"]["op"] == "end_turn" and not x.get("error"):
            yield prev, x["checkpoint"]
        prev = x["checkpoint"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--pairs", choices=["v2", "receipt"], default="receipt")
    a = ap.parse_args()
    v = a.version
    out = DATA / f"order-in-play-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    DATA.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in sorted(p for p in CAMP.iterdir() if (p / "original").is_dir()):
        if a.pairs == "receipt":
            if not (c / "original" / "receipt.jsonl").exists():
                continue
            for t, (pre, post) in enumerate(end_turn_pairs(c), 1):
                pre_f, post_f = c / "original" / f"{pre}.SAV", c / "original" / f"{post}.SAV"
                if not (pre_f.exists() and post_f.exists()):
                    continue
                r = transition(sav.parse(pre_f.read_bytes()), sav.parse(post_f.read_bytes()))
                rows.append(dict(campaign=c.name, turn=t, pre=pre_f.name, post=post_f.name, **r))
            continue
        saves = {}
        for f in (c / "original").glob("t*-a*.SAV"):
            t, k = re.match(r"t(\d+)-a(\d+)", f.stem).groups()
            saves.setdefault(int(t), {})[int(k)] = f
        for t in sorted(saves):
            if t + 1 not in saves or 0 not in saves[t + 1]:
                continue
            pre_f = saves[t][max(saves[t])]
            post_f = saves[t + 1][0]
            r = transition(sav.parse(pre_f.read_bytes()), sav.parse(post_f.read_bytes()))
            rows.append(dict(campaign=c.name, turn=t, pre=pre_f.name, post=post_f.name, **r))
    out.write_text(json.dumps(rows, indent=1))
    n = len(rows)
    deaths = [r for r in rows if r["died_or_merged"]]
    print("transitions", n, "with deaths", len(deaths), "order kept", sum(r["order_preserved"] for r in rows),
          "order kept when deaths", sum(r["order_preserved"] for r in deaths), "with tombstones", sum(r["post_tombstones"] > 0 for r in rows))
    for r in deaths[:40]:
        print(r["campaign"], r["turn"], "died", r["died_or_merged"], "new", r["new"], "kept", r["order_preserved"], "moved", r["moved"],
              "tomb", r["post_tombstones"], "new at", r["new_positions"][:5], "of", r["post_len"])


if __name__ == "__main__":
    main()
