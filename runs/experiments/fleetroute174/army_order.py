#!/usr/bin/env python3
"""Army execution order, original vs remake (found during the #174 fleet-0 attribution, owner 2026-10-31).

The original's F31C runs one own army at a time in table order: each army decides on the state the earlier armies left (their
walks, attacks and kills). The remake's AiTurn picks the best candidate of all armies per pass (ties by a seat draw), so a
later army can act first, on an older state. aidecide/compare.py compares each army's FIRST remake decision record, written
before any army acted, so it cannot see this.

Here: per army row of an aidecide report (the original's decision at its turn), the army's first ACTION in a remake run's AI
log, classified and checked against the original's branch:
  army>100, e84c+army>70   -> an action at a target army
  city>100, e84c+city>85   -> an action at a city, at the original's city position
  resupply                 -> move to the resupply city
  an e84c branch also accepts the mercenary run itself (FUN_0044e84c walks to an offer first); a carried-army landing at the
  city counts as a city action, and a siege as an action at the city (its position is not in the log line)
Rows whose verdict is diplomacy or state, and branches without a definite action (e84c alone, capital defence), are
skipped.

    python3 runs/experiments/fleetroute174/army_order.py <aidecide_report.json> <out.json> <label>=<remake_dir> [...]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

CHOSE = re.compile(r"chose \[Military/([a-z\-]+)\] score \d+ of \d+ candidates -- (.*)$")
POS = re.compile(r"\((\d+), (\d+)\)")


def first_actions(ailog):
    out = {}
    for line in (ailog.read_text().splitlines() if ailog.exists() else []):
        nation, _, text = line.partition("\t")
        m = CHOSE.search(text)
        if not m:
            continue
        armies = re.findall(r"with (army-\d+)", m[2])
        if armies:
            out.setdefault((nation, armies[-1]), (m[1], m[2]))
    return out


def classify(kind, text):
    if kind == "attack-army" or "target army" in text:
        return "army", None
    p = POS.search(text)
    xy = [int(p[1]), int(p[2])] if p else None
    if "resupply city" in text:
        return "resupply", xy
    if "garrison fallback" in text or "emergency" in text:
        return "fallback", xy
    if "mercenary run" in text:
        return "mercenary", xy
    if "carried-army landing" in text:
        return "city", xy
    if text.startswith("besiege "):
        return "city", "besiege"
    if "city" in text or kind in ("siege", "attack-city"):
        return "city", xy
    return kind, xy


def expected(row):
    b = row["orig"].get("branch")
    if b in ("army>100", "e84c+army>70"):
        return "army", None
    if b in ("city>100", "e84c+city>85"):
        return "city", row.get("orig_city_xy")
    if b == "resupply":
        return "resupply", None
    return None, None


def main():
    rep, out = json.load(open(sys.argv[1])), Path(sys.argv[2])
    runs = dict(a.split("=", 1) for a in sys.argv[3:])
    cache, counts, rows = {}, Counter(), []
    for r in rep["rows"]:
        if r["verdict"] in ("diplomacy", "state", "state-battle", "state-death"):
            continue
        want, want_xy = expected(r)
        if want is None:
            continue
        row = {"start": r["start"], "turn": r["turn"], "nation": r["nation"], "army": r["army"], "orig_branch": r["orig"]["branch"],
               "orig_city_xy": want_xy}
        r = dict(r, orig_x=r["orig"]["x"], orig_y=r["orig"]["y"])
        for label, d in runs.items():
            f = Path(d) / f"{r['start']}-t{r['turn']:02d}-ailog.txt"
            if f not in cache:
                cache[f] = first_actions(f)
            dec = Path(d) / f"{r['start']}-t{r['turn']:02d}-decisions.jsonl"
            if dec not in cache:
                ids = {}
                for line in (dec.read_text().splitlines() if dec.exists() else []):
                    x = json.loads(line)
                    ids.setdefault((x["NationId"], x["ArmyX"], x["ArmyY"]), x["ArmyId"])
                cache[dec] = ids
            # the original's record index is not the remake's import id after a death (swap-remove, #117): match by
            # nation and position at the start of the turn, as aidecide/compare.py does
            aid = cache[dec].get((r["nation"], r["orig_x"], r["orig_y"]), f"army-{r['army']}")
            act = cache[f].get((r["nation"], aid))
            if act is None:
                ok, got = False, None
            else:
                cls, xy = classify(*act)
                ok = (cls == want and (want != "city" or xy in (want_xy, "besiege"))) or (
                    cls == "mercenary" and row["orig_branch"].startswith("e84c"))
                got = act[1]
            row[label] = {"action": got, "match": ok}
            counts[(label, ok)] += 1
        rows.append(row)
    labels = list(runs)
    changed = [x for x in rows if len({x[l]["match"] for l in labels}) > 1]
    summary = {l: {"match": counts[(l, True)], "differ": counts[(l, False)]} for l in labels}
    with open(out, "x") as fh:
        json.dump({"summary": summary, "changed": changed, "rows": rows}, fh, indent=1)
    print(summary)
    for x in changed:
        print(x["start"][:3], x["turn"], x["nation"], x["army"], x["orig_branch"], x["orig_city_xy"],
              *[f"| {l}: {'OK' if x[l]['match'] else 'x'} {x[l]['action']}" for l in labels])


if __name__ == "__main__":
    main()
