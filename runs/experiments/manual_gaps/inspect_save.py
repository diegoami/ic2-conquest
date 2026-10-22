#!/usr/bin/env python3
"""Print a save's date, the human nations (and the given ones), and live armies/fleets (all, or only those of the given nations).

    python3 runs/experiments/manual_gaps/inspect_save.py SAVE [nation ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state import sav  # noqa: E402


def main():
    s = sav.load(sys.argv[1])
    only = [int(a) for a in sys.argv[2:]]
    print(s["date"], "turn", s["turn"], "current", s["current_nation"])
    for n in s["nations"]:
        if n["human"] or n["id"] in only:
            print("N", n["id"], n["name"], "human" if n["human"] else "", "treas", n["treasury"], "wealth", n["wealth"], "unity",
                  n["unity"], "mob", n["mobilization"], "cities", n["cities_count"], "neigh", n["neighbours"])
            print("  rel", n["relations"])
    for a in s["armies"]:
        if a["owner"] >= 0 and a["troops"] > 0 and (not only or a["owner"] in only):
            print("A", a["id"], sav.NATIONS[a["owner"]], (a["x"], a["y"]), "troops", a["troops"], "money", a["money"], "sup",
                  a["supplies"], "moves", a["moves"], "aboard" if a["embarked"] else "")
    for f in s["fleets"]:
        if f["owner"] >= 0 and (not only or f["owner"] in only):
            print("F", f["id"], sav.NATIONS[f["owner"]], (f["x"], f["y"]), "ships", f["ships"], "cond", f.get("condition"),
                  "build" if f["building"] else "", "money", f["money"], "sup", f["supplies"], "army", f["army"], "moves", f["moves"])


if __name__ == "__main__":
    main()
