#!/usr/bin/env python3
"""#195 D05: original saves in which a fleet under construction belongs to a city owned by another nation (a captured
building city). Ends with one summary line on stderr: campaigns, saves, building-fleet records, distinct builds,
foreign build cities. A fleet under construction has countdown >= 0 and stands at (0,0); its +20 field is then the build-city index ("build_city" in
state/sav.py) (docs/sav-layout-notes.md, fleet +10/+20). The original's busy test (4496E0) counts only the builder's own fleets there; the remake's
(AiFaithfulEconomy.cs:647) counts any nation's. Prints one line per (campaign, save, fleet). Read-only.

    python3 runs/experiments/audit195/d05_foreign_build.py <campaign dir> [...] > out.jsonl
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402


def main():
    camps = saves = records = foreign = 0
    builds = set()
    for c in map(Path, sys.argv[1:]):
        camps += 1
        for f in sorted((c / "original").glob("t*.SAV")):
            s = load(f)
            saves += 1
            for fl in s["fleets"]:
                if fl["owner"] >= 0 and fl.get("building") and 0 <= fl["build_city"] < len(s["cities"]):
                    k = fl["build_city"]
                    city = s["cities"][k]
                    records += 1
                    builds.add((c.name, fl["id"], k, fl["owner"]))
                    if city["owner"] != fl["owner"]:
                        foreign += 1
                        print(json.dumps({"camp": c.name, "save": f.name, "fleet": fl["id"], "builder": fl["owner"],
                                          "city": k, "city_owner": city["owner"], "countdown": fl["countdown"], "xy": [city["x"], city["y"]]}), flush=True)

    print(json.dumps({"summary": True, "campaigns": camps, "saves": saves, "building_records": records,
                      "distinct_builds": len(builds), "foreign_build_city_records": foreign}), file=sys.stderr)


if __name__ == "__main__":
    main()
