#!/usr/bin/env python3
"""AI economy decisions, original vs remake main, on equal round-start states (#176, owner 2026-10-31).

Original: difftest/probes/econ_hook_run.py (patches/econ_hook.py): per seat, the budget (own, threat, treasury, unity,
mobilization, tax), every ready entry deployed, every new order (entry, type, troops, city), and the state after the tax
policy. Remake: the same rounds replayed from the original's autosaves (the diplomacy run's AI logs): "faithful economy:
threat T, own O", "mobilize recruitment slot N ...", "faithful order k: TYPE N troops at CITY", "week W: tax a -> b".

Per seat:
  budget      own and threat equal?  (a different budget means the state already differs: "state")
  deploys     the set of queue entries mobilized
  orders      the city (FUN_004502e0) and the number of orders. The types and troops are Random draws, so the number is
              checked by replaying FUN_004504f4's own stopping rule on each side's draws, with the original's inputs
              (deficit, the queue's value in the round-start save, treasury, wealth, mobilization):
                place while: k < 8, value < deficit, mobilization < 100, and (treasury > -wealth/500 or k < 3);
                each order: value += (troops/100)·weight, treasury -= (troops/200)·price, mob = min(100, mob + troops·1000/wealth + 1)
              "rule-ok" when the side's own count equals the replayed count.
  tax         the week-11 change (before -> after), compared when the week is 11

    python3 runs/experiments/econ/compare.py <orig_dir> <remake_ailog_dir> <saves_dir> <report.json>
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs/experiments/aidecide"))
from state.sav import load  # noqa: E402
import compare as A  # noqa: E402  (round_start)

NATIONS = A.NATIONS
IDX = {n: i for i, n in enumerate(NATIONS)}
TYPES = ["light_infantry", "heavy_infantry", "archers", "light_cavalry", "heavy_cavalry"]   # original 0..4
SAVTYPE = {"li": 0, "hi": 1, "ar": 2, "lc": 3, "hc": 4}
WEIGHT = [20, 100, 40, 60, 120]
PRICE = [2, 20, 4, 15, 30]
ECON = re.compile(r"faithful economy: threat (-?\d+), own (-?\d+)")
ORDER = re.compile(r"faithful order (\d+): (\w+) (\d+) troops at (\S+)")
MOBIL = re.compile(r"mobilize recruitment slot (\d+) \((\d+) (\w+) troops")
TAX = re.compile(r"week (\d+): tax (-?\d+) -> (-?\d+)")


def replay(orders, deficit, value, treasury, wealth, mob):
    """How many of `orders` (type, troops) FUN_004504f4 places with these inputs."""
    k = 0
    for t, troops in orders:
        if not (k < 8 and value < deficit and mob < 100 and (treasury > int(-wealth / 500) or k < 3)):
            break
        value += (troops // 100) * WEIGHT[t]
        treasury -= (troops // 200) * PRICE[t]
        mob = min(100, mob + int(troops * 1000 / wealth) + 1)
        k += 1
    stopped = not (k < 8 and value < deficit and mob < 100 and (treasury > int(-wealth / 500) or k < 3))
    return k, stopped


def queue_value(save, n):
    return sum((s["troops"] // 100) * WEIGHT[SAVTYPE[s["type"]]] for s in save["nations"][n]["recruit_slots"] if s["troops"] > 0)


def remake_seats(ailog, cities):
    seats = defaultdict(lambda: {"budget": None, "orders": [], "deploys": [], "tax": None})
    for l in (ailog.read_text().splitlines() if ailog.exists() else []):
        nation, _, text = l.partition("\t")
        s = seats[IDX[nation]]
        if m := ECON.search(text):
            s["budget"] = (int(m[2]), int(m[1]))
        elif m := ORDER.search(text):
            s["orders"].append((TYPES.index(m[2]), int(m[3]), cities.get(m[4], m[4])))
        elif m := MOBIL.search(text):
            s["deploys"].append(int(m[1]))
        elif m := TAX.search(text):
            s["tax"] = (int(m[2]), int(m[3]))
    return seats


def main():
    orig, rdir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[4])
    names = json.loads((ROOT / "runs/experiments/data/run-exp-boundary144/city-record-ids.json").read_text())
    cities = {v: int(k) for k, v in names.items()}
    rows, counts = [], Counter()
    for f in sorted(orig.glob("*-econ.jsonl")):
        start = f.name[:-len("-econ.jsonl")]
        d = orig / start
        by = defaultdict(list)
        for l in f.read_text().splitlines():
            r = json.loads(l)
            by[r["turn"]].append(r)
        for t, recs in sorted(by.items()):
            save = load(A.round_start(d, t))
            rem = remake_seats(rdir / f"{start}-t{t:02d}-ailog.txt", cities)
            seats = defaultdict(lambda: {"budget": None, "orders": [], "deploys": [], "after": None})
            for r in recs:
                s = seats[r["nation"]]
                if r["kind"] == "budget":
                    s["budget"] = r
                elif r["kind"] == "order":
                    s["orders"].append((r["type"], r["troops"], r["city"]))
                elif r["kind"] == "deploy":
                    s["deploys"].append(r["entry"])
                else:
                    s["after"] = r
            for n, o in seats.items():
                if o["budget"] is None:
                    continue
                rm = rem.get(n)
                row = {"start": start, "turn": t, "nation": NATIONS[n], "orig_budget": [o["budget"]["own"], o["budget"]["threat"]],
                       "remake_budget": list(rm["budget"]) if rm and rm["budget"] else None}
                if not rm or rm["budget"] is None:
                    row["verdict"] = "no-remake-seat"
                elif tuple(row["orig_budget"]) != rm["budget"]:
                    row["verdict"] = "state"                      # the inputs differ already
                else:
                    b = o["budget"]
                    deficit = b["threat"] - b["own"]
                    wealth = o["after"]["wealth"] if o["after"] else save["nations"][n]["wealth"]
                    qv = queue_value(save, n)
                    items = {}
                    items["deploys"] = sorted(o["deploys"]) == sorted(rm["deploys"])
                    oc = {c for _, _, c in o["orders"]}
                    rc = {c for _, _, c in rm["orders"]}
                    items["order_city"] = oc == rc or not (oc and rc)
                    if deficit > 0:
                        ok_o = replay([(a, b_) for a, b_, _ in o["orders"]] + [(0, 0)] * 8, deficit, qv, b["treasury"], wealth, b["mobilization"])[0] == len(o["orders"])
                        ok_r = replay([(a, b_) for a, b_, _ in rm["orders"]] + [(0, 0)] * 8, deficit, qv, b["treasury"], wealth, b["mobilization"])[0] == len(rm["orders"])
                        items["order_count_rule_orig"] = ok_o
                        items["order_count_rule_remake"] = ok_r
                    else:
                        items["no_orders_both"] = not o["orders"] and not rm["orders"]
                    if o["after"] and b["week"] == 11:
                        items["tax"] = (rm["tax"] or (b["tax"], b["tax"])) == (b["tax"], o["after"]["tax"])
                    row.update(items=items, deficit=deficit, queue_value=qv, orig_orders=o["orders"], remake_orders=rm["orders"],
                               orig_deploys=o["deploys"], remake_deploys=rm["deploys"],
                               orig_tax=[b["tax"], o["after"]["tax"] if o["after"] else None], remake_tax=rm["tax"])
                    row["verdict"] = "same" if all(items.values()) else "differs"
                    for k, v in items.items():
                        counts[f"{k}:{'ok' if v else 'DIFF'}"] += 1
                counts[row["verdict"]] += 1
                rows.append(row)
    with open(out, "x") as fh:
        json.dump({"counts": dict(counts), "rows": rows}, fh, indent=1)
    print(dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
