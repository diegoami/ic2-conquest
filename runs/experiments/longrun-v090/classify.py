#!/usr/bin/env python3
"""Classify the anchored per-turn differences of the v0.9.0 long runs (difftest/anchored.py output).

    python3 runs/experiments/longrun-v090/classify.py <campaign_dir> [--json out.json]

Per turn and nation, each difference gets a kind:
  position  - the nation's armies (or fleets) stand on different tiles (multiset of (x, y) differs)
  count     - a different number of armies or fleets
  owner     - a city it owns in one game and not the other
  relations - its relations row differs (war, peace, alliance, treaty values)
  size      - same tiles, different troop counts or unit mix (casualties, recruits, attrition: random draws)
  recruit   - its recruitment queue differs (unit types and sizes are drawn)
  treasury / supplies / other nation fields
Map cells: weather (sea values 0/1, storms) versus any other value. A turn whose differences are only size, recruit,
treasury, supplies and weather is "draws"; anything with position, count, owner or relations is "structural" and is
what gets attributed by hand.
"""
import json
import sys
from collections import Counter
from pathlib import Path

STRUCTURAL = {"position", "count", "owner", "relations"}


def kinds_of(d):
    out = set()
    for kind in ("armies", "fleets"):
        if kind in d:
            x = d[kind]
            if x["count"][0] != x["count"][1]:
                out.add("count")
            pa = Counter((r[0], r[1]) for r in x["only_original"])
            pb = Counter((r[0], r[1]) for r in x["only_remake"])
            out.add("position" if pa != pb else "size")
    for city, fields in d.get("cities", {}).items():
        out |= {"owner" if f == "owner" else "supplies" if f == "supplies" else f"city.{f}" for f in fields}
    for f in d.get("nation", {}):
        out.add({"relations": "relations", "recruit_slots": "recruit", "treasury": "treasury"}.get(f, f"nation.{f}"))
    return out


def classify(row, phase="ai"):
    p = row[phase]
    per = {n: sorted(kinds_of(d)) for n, d in p["nations"].items()}
    weather = sum(1 for c in p.get("first_map", []) if {c["a"], c["b"]} <= {0, 1})
    struct = {n: [k for k in ks if k in STRUCTURAL] for n, ks in per.items()}
    struct = {n: ks for n, ks in struct.items() if ks}
    return {"turn": row["turn"], "date": row["date"], "phase": phase, "fields": p["fields"], "map": p["map"],
            "map_sample_weather": f"{weather}/{len(p.get('first_map', []))}", "structural": struct,
            "verdict": "structural" if struct else "draws", "kinds": per}


def main():
    camp = Path(sys.argv[1])
    rows = [json.loads(l) for l in (camp / "anchored/turns.jsonl").read_text().splitlines() if l.strip()]
    res, tally = [], Counter()
    for r in rows:
        if "error" in r:
            res.append({"turn": r["turn"], "verdict": "error", "error": r["error"][:300]})
            tally["error"] += 1
            continue
        for phase in ("human", "ai"):
            c = classify(r, phase)
            res.append(c)
            tally[f"{phase}:{c['verdict']}"] += 1
            for n, ks in c["structural"].items():
                for k in ks:
                    tally[f"{phase}:{k}"] += 1
    for c in res:
        if c["verdict"] != "draws":
            print(c["turn"], c.get("phase"), c.get("date"), c["verdict"], json.dumps(c.get("structural") or c.get("error")))
    print(dict(sorted(tally.items())))
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps({"tally": tally, "turns": res}, indent=1))


if __name__ == "__main__":
    main()
