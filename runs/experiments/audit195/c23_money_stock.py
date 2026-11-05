#!/usr/bin/env python3
"""#195 C23 (research intake PR #213): the army money and tail-city stock comparisons of the C23 effect, stored. For every
distinct (start, round, army, city) resupply tail in the D734 hook logs, compare at the round's end the original (the
hook run's hooked autosave) with the remake replay of c23_supply_effect.py (<supply dir>/<start>-r<round>/a001.SAV):
the army's money (same record index and owner, else "skipped: index") and the tail city's supplies (cities keep their
index). One JSON line per tail; a summary line on stderr. Read-only.

    python3 runs/experiments/audit195/c23_money_stock.py <hook dir> <supply dir> > money_stock.jsonl
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state.sav import load  # noqa: E402


def main():
    hook, sup = Path(sys.argv[1]), Path(sys.argv[2])
    cache, tally = {}, collections.Counter()
    L = lambda p: cache.setdefault(p, load(p))
    for log in sorted(hook.glob("*-d734.jsonl")):
        start = log.name[: -len("-d734.jsonl")]
        hooked = sorted((hook / start).glob("hooked-t*.SAV"))
        seen = set()
        for l in log.read_text().splitlines():
            r = json.loads(l)
            if r["kind"] != "resupply" or (r["turn"], r["army"], r["city"]) in seen:
                continue
            seen.add((r["turn"], r["army"], r["city"]))
            m = sup / f"{start}-r{r['turn']}" / "a001.SAV"
            if not m.exists():
                tally["no remake replay"] += 1
                continue
            o, mm = L(hooked[r["turn"] - 1]), L(m)
            a, c = r["army"], r["city"]
            row = {"start": start, "round": r["turn"], "army": a, "city": c,
                   "city_supplies": [o["cities"][c]["supplies"], mm["cities"][c]["supplies"]]}
            if a < len(o["armies"]) and a < len(mm["armies"]) and o["armies"][a]["owner"] == mm["armies"][a]["owner"]:
                row["army_money"] = [o["armies"][a]["money"], mm["armies"][a]["money"]]
                tally["money " + ("equal" if row["army_money"][0] == row["army_money"][1] else "differ")] += 1
            else:
                row["army_money"] = "skipped: index"
                tally["money skipped: index"] += 1
            tally["city " + ("equal" if row["city_supplies"][0] == row["city_supplies"][1] else "differ")] += 1
            print(json.dumps(row))
    print(json.dumps({"summary": True, **tally}), file=sys.stderr)


if __name__ == "__main__":
    main()
