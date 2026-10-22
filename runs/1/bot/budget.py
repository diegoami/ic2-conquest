"""Run 1 helper: the debt floor (P10) and the next quarter's bill, from a save.

    python3 runs/1/bot/budget.py <save>

line  = -(wealth div 500)           (deposition below it, tested at each human turn start)
floor = line + 1,000                (the owner's margin; every spending order keeps the treasury >= floor)
Quarterly change (docs/rules-digest.md §3):
    - 3 x ships - sum regular units (troops div 200) x qprice - sum queue slots (troops div 200) x qprice
    + taxBase x tax div 100 + taxBase div 4 - cities x 7 - wealth div 20000 + sum partners' taxBase div 12
Mercenaries are paid from their army purse, not the treasury.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state import sav  # noqa: E402

QPRICE = {"li": 1, "hi": 2, "ar": 1, "lc": 3, "hc": 4}
IPRICE = {"li": 2, "hi": 20, "ar": 4, "lc": 15, "hc": 30}
FULL = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}


def budget(s, n=0):
    r = s["nations"][n]
    line = -(r["wealth"] // 500)
    floor = line + 1000
    armies = sum((u["troops"] // 200) * QPRICE[u["type"]] for a in sav.live_armies(s, n) for u in a["units"] if not u["merc"])
    queue = sum((q["troops"] // 200) * QPRICE[q["type"]] for q in r["recruit_slots"])
    ships = sum(f.get("ships", 0) for f in s.get("fleets", []) if f.get("owner") == n) if s.get("fleets") else 0
    tb = r["tax_base"]
    trade = sum(s["nations"][sav.NATIONS.index(k)]["tax_base"] // 12 for k, v in r["relations"].items() if v in (1, 2))
    income = tb * r["tax"] // 100 + tb // 4 - len(sav.owned_cities(s, n)) * 7 - r["wealth"] // 20000 + trade
    net = income - armies - queue - 3 * ships
    return {"treasury": r["treasury"], "wealth": r["wealth"], "line": line, "floor": floor,
            "room": r["treasury"] - floor, "income": income, "trade": trade, "upkeep_armies": armies,
            "upkeep_queue": queue, "ships": ships, "net_quarter": net, "mobilization": r["mobilization"],
            "unity": r["unity"], "tax": r["tax"], "tax_base": tb,
            "room_after_bill": r["treasury"] + min(0, net) - floor}


def cost(kind, troops):
    return (troops // 200) * IPRICE[kind]


def mob_gain(troops, wealth):
    return 1 + troops * 1000 // wealth


if __name__ == "__main__":
    s = sav.load(sys.argv[1])
    b = budget(s)
    for k, v in b.items():
        print("%-16s %s" % (k, v))
    w = b["wealth"]
    print("per full battalion: " + ", ".join("%s %d t, +%d mob, +%d/qtr" % (k, cost(k, FULL[k]), mob_gain(FULL[k], w),
                                                                              (FULL[k] // 200) * QPRICE[k]) for k in FULL))
