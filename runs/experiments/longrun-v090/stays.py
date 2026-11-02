#!/usr/bin/env python3
""""Original stays, remake moves" rows of the anchored long runs (v0.9.0, owner 2026-11-02).

    python3 runs/experiments/longrun-v090/stays.py <campaign_dir> [...]

For each anchored turn: an AI army or fleet (not the human's) whose record ends the original's turn on the tile it started on,
while the remake's turn (from the same start state) ends with no unit of that owner and size on that tile. Each row names the
nearest city (owner, relation to the unit's owner: own / war / other) and its Chebyshev distance, and the unit's moves at the
start of the turn, so the cases can be grouped (next to own capital, next to an enemy city, in port).
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import NATIONS, load  # noqa: E402


def last(pattern):
    f = sorted(glob.glob(pattern))
    return f[-1] if f else None


def units(s, kind):
    key = "troops" if kind == "armies" else "ships"
    return [u for u in s[kind] if u[key] > 0 and u.get("countdown", -1) == -1 or kind == "armies" and u[key] > 0]


def size(u):
    return u.get("troops", u.get("ships"))


def main():
    rows, tally = [], Counter()
    for camp in map(Path, sys.argv[1:]):
        human = json.loads((camp / "turns.jsonl").read_text().splitlines()[0])["nation"]
        for line in (camp / "anchored/turns.jsonl").read_text().splitlines():
            r = json.loads(line)
            if "error" in r:
                continue
            k = r["turn"]
            st = load(camp / "original/t00-start.SAV") if k == 1 else load(last(str(camp / f"original/t{k - 1:02d}-a*.SAV")))
            eo = load(last(str(camp / f"original/t{k:02d}-a*.SAV")))
            er = load(last(str(camp / f"anchored/t{k:02d}/a*.SAV")))
            for kind in ("armies", "fleets"):
                end_o = {(u["owner"], u["x"], u["y"]) for u in units(eo, kind)}
                end_r = {(u["owner"], u["x"], u["y"], size(u)) for u in units(er, kind)}
                for u in units(st, kind):
                    if NATIONS[u["owner"]] == human or (u["owner"], u["x"], u["y"]) not in end_o:
                        continue
                    if (u["owner"], u["x"], u["y"]) in {(o, x, y) for o, x, y, _ in end_r}:
                        continue
                    where = [v for v in units(er, kind) if v["owner"] == u["owner"] and size(v) == size(u)]
                    city = min(st["cities"], key=lambda c: max(abs(c["x"] - u["x"]), abs(c["y"] - u["y"])))
                    d = max(abs(city["x"] - u["x"]), abs(city["y"] - u["y"]))
                    rel = st["nations"][u["owner"]]["relations"].get(NATIONS[city["owner"]])
                    tag = "own" if city["owner"] == u["owner"] else "war" if rel == 3 else "other"
                    cap = city["id"] == st["nations"][u["owner"]]["capital"]
                    row = {"game": camp.name, "turn": k, "kind": kind, "owner": NATIONS[u["owner"]], "at": [u["x"], u["y"]],
                           "size": size(u), "moves_at_start": u["moves"], "city": city["name"], "city_dist": d, "city_tag": tag,
                           "capital": cap, "remake_end": [[v["x"], v["y"]] for v in where][:2]}
                    rows.append(row)
                    tally[(kind, tag + ("-capital" if cap else ""), d)] += 1
    for x in rows:
        print(json.dumps(x))
    for key, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(n, key)


if __name__ == "__main__":
    main()
