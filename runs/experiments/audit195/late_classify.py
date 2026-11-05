#!/usr/bin/env python3
"""#195 step 7: classify the late-year (266-264 BC) AI-phase position rows of the anchored long games by class.

    python3 runs/experiments/audit195/late_classify.py <campaign dir>:<anchored folder> [...] > rows.jsonl

A position row is (turn, nation, armies|fleets) whose units end on different tiles in the original and the remake
(runs/experiments/longrun-v090/pin_diff.py). For each row, from the original's human-phase checkpoint (pre), its end and
the remake's end, the first class that applies:
  human_phase   the nation is the human's, or its units already differ after the human's orders (the turn's "human"
                comparison): a carry-over of the human phase, not an AI decision (v2);
  diplomacy     the nation's new relations this turn (war, alliance, peace, trade) differ between the two games;
  human_battle  the nation's news this turn names the human's nation (a battle or siege with the human: X3/X6);
  battle        the nation's battle/siege news this turn differs between the games (draws);
  downstream    a nation that plays earlier in this round already has a row this turn;
  quiet         none of these: a candidate rule difference. Fleet rows are split: quiet_fleet_ports when the fleet's
                tiles in both games are next to an own city (the port-choice draws of
                2026-11-04-port-rows-and-carried-army.md), quiet_fleet otherwise; army rows stay quiet.
Read-only; one JSON line per row, then a summary line on stderr.
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs/experiments/longrun-v090"))
from pin_diff import positions, rows  # noqa: E402
from state.sav import load  # noqa: E402

LATE = ("266 BC", "265 BC", "264 BC")


def new_relations(pre, end, i):
    p, e = pre["nations"][i]["relations"], end["nations"][i]["relations"]
    return sorted((k, e[k]) for k in e if e[k] != p.get(k) and e[k] >= 0)


def news_of(s, name, base):
    """News lines naming `name` that are not in the pre state's news (this turn's)."""
    c = collections.Counter(x for x in s["news"] if name in x)
    c.subtract(collections.Counter(x for x in base["news"] if name in x))
    return +c


def main():
    tally = collections.Counter()
    for spec in sys.argv[1:]:
        camp, folder = spec.split(":")
        c = Path(camp)
        last = rows(c / folder / "turns.jsonl")
        pos, _ = positions(last)
        orig = c / "original"
        cache = {}
        for (t, nation, kind) in sorted(pos):
            if not any(y in last[t].get("date", "") for y in LATE):
                continue
            if t not in cache:
                ends = sorted(orig.glob(f"t{t:02d}-a*.SAV"))
                pre_f = ends[-2] if len(ends) > 1 else sorted(orig.glob(f"t{t - 1:02d}-a*.SAV"))[-1]
                rends = sorted((c / folder / f"t{t:02d}").glob("a*.SAV"))
                cache = {t: (load(pre_f), load(ends[-1]), load(rends[-1]))}
            pre, oend, rend = cache[t]
            names = [n["name"] for n in pre["nations"]]
            i = names.index(nation)
            human = next((n["name"] for n in pre["nations"] if n.get("human")), None)
            order = pre["turn_order"]
            hs = order.index(names.index(human)) if human in names and names.index(human) in order else 0
            round_order = order[hs + 1:] + order[:hs]                 # the AI seats after the human's End turn
            earlier = {names[j] for j in round_order[:round_order.index(i)]} if i in round_order else set()
            others = {n for (tt, n, _) in pos if tt == t}
            dip = new_relations(pre, oend, i) != new_relations(pre, rend, i)
            no, nr = news_of(oend, nation, pre), news_of(rend, nation, pre)
            hb = human and any(human in x for x in list(no) + list(nr))
            hp = nation == human or nation in last[t].get("human", {}).get("nations", {})
            cls = ("human_phase" if hp else "diplomacy" if dip else "human_battle" if hb else "battle" if no != nr
                   else "downstream" if earlier & others else "quiet")
            if cls == "quiet" and kind == "fleets":
                d = last[t]["ai"]["nations"][nation]["fleets"]
                own = [(x["x"], x["y"]) for x in oend["cities"] if x["owner"] == i]
                port = lambda u: any(max(abs(u[0] - a), abs(u[1] - b)) <= 1 for a, b in own)
                tiles = [u for u in d["only_original"] + d["only_remake"]]
                cls = "quiet_fleet_ports" if tiles and all(port(u) for u in tiles) else "quiet_fleet"
            tally[cls] += 1
            print(json.dumps({"camp": c.name, "turn": t, "date": last[t]["date"], "nation": nation, "kind": kind,
                              "class": cls, "relations": [new_relations(pre, oend, i), new_relations(pre, rend, i)],
                              "news": [sorted(no.elements()), sorted(nr.elements())],
                              "earlier_rows": sorted(earlier & others)}), flush=True)
    print(json.dumps({"summary": True, **tally}), file=sys.stderr)


if __name__ == "__main__":
    main()
