"""Run 1 helper: a planning view of one save (Rome, Gaul and their neighbours).

    python3 runs/1/bot/look.py <save> [nation ids, default 0 6]

Prints the nations' summary, the listed nations' armies (units, supplies, morale, purse, moves),
their cities (loyalty, stock, fortification, population, siege defence), Rome's queue, the
mercenary offers and the P1 strength of every Roman army against every enemy army.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state import sav  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import strength  # noqa: E402


def main(path, nations=(0, 6)):
    s = sav.load(path)
    print(sav.summary(s))
    print()
    for a in sav.live_armies(s):
        if a["owner"] in nations:
            print("army %3d %-9s (%3d,%3d) troops %6d sup %4d/%4d morale %2d purse %4d moves %2d %s" % (
                a["id"], sav.NATIONS[a["owner"]], a["x"], a["y"], a["troops"], a["supplies"], a["troops"] // 100 + 1,
                a["morale"], a["money"], a["moves"],
                " ".join("%s%d/q%d%s" % (u["type"], u["troops"], u["quality"], "m" if u["merc"] else "") for u in a["units"])))
    print()
    for n in nations:
        r = s["nations"][n]
        print(r["name"], {k: r[k] for k in ("treasury", "unity", "mobilization", "tax", "wealth", "capital")})
        print("  relations:", {k: v for k, v in r["relations"].items() if v})
        if n == 0:
            for q in r["recruit_slots"]:
                print("  slot", q)
    print()
    for c in s["cities"]:
        if c["owner"] in nations:
            print("city %3d %-12s %-6s (%3d,%3d) loy %3d stock %4d fort %3d%s pop %3d def %6d recruit %s" % (
                c["id"], c["name"], sav.NATIONS[c["owner"]][:6], c["x"], c["y"], c["loyalty"], c["supplies"], c["fort"],
                "+%d" % c["fort_pending"] if c["fort_pending"] else "", c["pop"], sav.siege_defence(s, c),
                sav.can_recruit_at(s, c["owner"], c)))
    print()
    print("mercenary offers:", [(m["x"], m["y"], m["type"], m["troops"], m["quality"]) for m in s["mercenaries"]])
    print()
    me = s["nations"][0]
    cands = []
    for n in s["nations"][1:]:
        if not n["alive"]:
            continue
        partners = sum(1 for v in n["relations"].values() if v in (1, 2))
        cands.append((n["tax_base"], n["name"], n["id"], me["relations"][n["name"]], partners))
    print("trade: Rome partners %d; candidates (tax base, nation, id, relation to Rome, its partners):" % sum(
        1 for v in me["relations"].values() if v == 1))
    for c in sorted(cands, reverse=True):
        if c[3] == 0 and c[4] < 3:
            print("  ", c)
    print("pending offer:", s["pending_offer"])
    print()
    rom = [a for a in sav.live_armies(s, 0)]
    for e in [a for a in sav.live_armies(s) if a["owner"] in nations and a["owner"] != 0]:
        for a in rom:
            print(strength.line(a, e))


if __name__ == "__main__":
    ns = tuple(int(x) for x in sys.argv[2:]) or (0, 6)
    main(sys.argv[1], ns)
