#!/usr/bin/env python3
"""#195 B03: did the original mobilise a ready slot (state 24) at a city with an army of a nation at war with the city's
owner within one tile (the remake's Faithful restraint, AiEconomyPhase.ProposeMobilization IsThreatened, which the
original's FUN_004504f4 lacks)? And did the remake mobilise that slot in the same anchored turn?

    python3 runs/experiments/audit195/b03_threatened_mobilise.py <anchored folder> <campaign dir> [...] > out.jsonl

Per turn: pre-AI state = the original's human-phase checkpoint (as x1_war_seats.py); a slot is mobilised when its
(type, troops, city) leaves the nation's state-24 multiset. Prints one line per mobilised slot at a threatened city.
Read-only.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402


def ready(s, i):
    return Counter((x["type"], x["troops"], x["city"]) for x in s["nations"][i]["recruit_slots"] if x["troops"] > 0 and x["state"] == 24)


def threatened(s, i, city):
    c = s["cities"][city]
    names = [n["name"] for n in s["nations"]]
    rel = s["nations"][i]["relations"]
    return [(a["x"], a["y"], names[a["owner"]]) for a in s["armies"]
            if a["owner"] >= 0 and a["owner"] != i and a["troops"] > 0 and abs(a["x"] - c["x"]) <= 1 and abs(a["y"] - c["y"]) <= 1
            and rel.get(names[a["owner"]]) == 3]


def main():
    folder, camps = sys.argv[1], sys.argv[2:]
    for c in map(Path, camps):
        orig = c / "original"
        for rdir in sorted((c / folder).glob("t[0-9][0-9]")):
            t = int(rdir.name[1:])
            ends = sorted(orig.glob(f"t{t:02d}-a*.SAV"))
            rends = sorted(rdir.glob("a*.SAV"))
            if not ends or not rends:
                continue
            pre_f = ends[-2] if len(ends) > 1 else (orig / "t00-start.SAV" if t == 1 else sorted(orig.glob(f"t{t - 1:02d}-a*.SAV"))[-1])
            pre, end, rend = load(pre_f), load(ends[-1]), load(rends[-1])
            for i, n in enumerate(pre["nations"]):
                if n.get("human") or not n.get("alive", True):
                    continue
                gone_o = ready(pre, i) - ready(end, i)
                gone_r = ready(pre, i) - ready(rend, i)
                for (typ, troops, city), k in gone_o.items():
                    th = threatened(pre, i, city)
                    if th:
                        print(json.dumps({"camp": c.name, "turn": t, "nation": n["name"], "slot": [typ, troops, city],
                                          "city_xy": [pre["cities"][city]["x"], pre["cities"][city]["y"]], "hostile": th,
                                          "remake_mobilised": gone_r.get((typ, troops, city), 0) > 0}), flush=True)


if __name__ == "__main__":
    main()
