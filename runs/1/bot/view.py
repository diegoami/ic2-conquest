"""Run 1 helper: the planning view of AUTO<turn>.SAV: budget (P10), armies, queue, P1 ratios, Rome/Gaul cities, news.

    python3 runs/1/bot/view.py <turn> [nation ids, default 0 6 1] [--cities]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import sav  # noqa: E402
import budget  # noqa: E402
import strength  # noqa: E402
import turn as T  # noqa: E402


def main(turn, nations, cities):
    p = T.save_path(turn)
    s = sav.load(p)
    print(p.name, s["date"])
    b = budget.budget(s)
    print("budget:", ", ".join("%s %s" % kv for kv in b.items()))
    for n in nations:
        r = s["nations"][n]
        print("%-9s cities %2d treasury %6d unity %3d mob %3d tax %2d rel %s" % (
            r["name"], len(sav.owned_cities(s, n)), r["treasury"], r["unity"], r["mobilization"], r["tax"],
            {k: v for k, v in r["relations"].items() if v}))
    for a in sav.live_armies(s):
        if a["owner"] in nations:
            print("army %3d %-9s (%3d,%3d) troops %6d sup %4d/%4d mor %2d purse %4d mv %2d %s" % (
                a["id"], sav.NATIONS[a["owner"]], a["x"], a["y"], a["troops"], a["supplies"], a["troops"] // 100 + 1,
                a["morale"], a["money"], a["moves"],
                " ".join("%s%d/q%d%s" % (u["type"], u["troops"], u["quality"], "m" if u["merc"] else "") for u in a["units"])))
    q = s["nations"][0]["recruit_slots"]
    print("queue:", " ".join("%d:%s%d@%d/s%d" % (k, x["type"], x["troops"], x["city"], x["state"]) for k, x in enumerate(q)))
    rom = sav.live_armies(s, 0)
    for e in sav.live_armies(s):
        if e["owner"] != 0 and e["owner"] in nations:
            for a in rom:
                d = max(abs(a["x"] - e["x"]), abs(a["y"] - e["y"]))
                print(strength.line(a, e), "dist %d" % d)
    if cities:
        for c in s["cities"]:
            if c["owner"] in nations:
                print("city %3d %-12s %-6s (%3d,%3d) loy %3d stock %4d fort %3d pop %3d def %6d" % (
                    c["id"], c["name"], sav.NATIONS[c["owner"]][:6], c["x"], c["y"], c["loyalty"], c["supplies"], c["fort"],
                    c["pop"], sav.siege_defence(s, c)))
    if "--fleets" in sys.argv:
        for f in s["fleets"]:
            if f.get("owner") in nations:
                print("fleet", {k: v for k, v in f.items() if k not in ("raw",)})
    print("news:", [n.strip() for n in s["news"]][-14:])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(int(args[0]), tuple(int(x) for x in args[1:]) or (0, 6, 1), "--cities" in sys.argv)
