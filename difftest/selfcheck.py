"""Negative controls for the comparison (#229): a deliberately corrupted state must be reported.

    python3 -m difftest.selfcheck CHECKPOINT.SAV OUT.json

Each control changes one field of a parsed copy of the checkpoint (in memory: no save is written or changed)
and checks that `compare` reports exactly that field, then that an unchanged copy reports nothing.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest.compare import compare  # noqa: E402
from state.sav import load  # noqa: E402

CONTROLS = [
    ("nations.Rome.treasury", lambda s: s["nations"][0].__setitem__("treasury", s["nations"][0]["treasury"] + 1)),
    ("cities.85.loyalty", lambda s: s["cities"][85].__setitem__("loyalty", s["cities"][85]["loyalty"] - 1)),
    ("armies.0.x", lambda s: s["armies"][0].__setitem__("x", s["armies"][0]["x"] + 1)),
    ("armies.0.units", lambda s: s["armies"][0]["units"][0].__setitem__("troops", s["armies"][0]["units"][0]["troops"] - 100)),
    ("nations.Rome.relations", lambda s: s["nations"][0]["relations"].__setitem__("Carthage", 3)),
    ("week", lambda s: s.__setitem__("week", s["week"] + 2)),
]


def run(path):
    base = load(path)
    results = [{"control": "unchanged copy", "reported": [f["path"] for f in compare(base, copy.deepcopy(base))["fields"]],
                "map": compare(base, copy.deepcopy(base))["map"]["count"]}]
    results[0]["pass"] = not results[0]["reported"] and not results[0]["map"]
    for field, change in CONTROLS:
        s = copy.deepcopy(base)
        change(s)
        d = compare(base, s)
        reported = [f["path"] for f in d["fields"]]
        results.append({"control": field, "reported": reported, "pass": reported == [field]})
    s = copy.deepcopy(base)
    m = list(s["map"])
    m[100 * 140 + 37] = m[100 * 140 + 37] + 1
    s["map"] = tuple(m)
    d = compare(base, s)
    results.append({"control": "map (100,37)", "map": d["map"]["count"], "pass": d["map"]["count"] == 1 and not d["fields"]})
    return {"checkpoint": str(path), "controls": results, "all_pass": all(r["pass"] for r in results)}


if __name__ == "__main__":
    r = run(sys.argv[1])
    out = Path(sys.argv[2])
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps(r, indent=1))
    print("all controls pass" if r["all_pass"] else "FAILED: " + json.dumps([c for c in r["controls"] if not c["pass"]]))
