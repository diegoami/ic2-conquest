#!/usr/bin/env python3
"""Research #117: in the original's death turns (sweep-model-<input>.json), which reorders change the relative order of two
SURVIVING armies of the same nation (what the per-nation "first eligible" picks see, e.g. FUN_004509f0's donor and receiver)
against the remake's rule (survivors keep their order)? Writes same-nation-<version>.json.

    python3 runs/experiments/armyorder117/same_nation.py --input v3 --sweep v5 --version v3

--input names the order-in-play version, --sweep the sweep-model version (default: the same as --input, as v1/v2 were run).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import order_in_play as O  # noqa: E402
from state import sav  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--sweep", help="sweep-model version (default: --input)")
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    a.sweep = a.sweep or a.input
    out = O.DATA / f"same-nation-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for r in json.loads((O.DATA / f"sweep-model-{a.sweep}.json").read_text()):
        c = O.CAMP / r["campaign"] / "original"
        pre = sav.parse((c / json.loads((O.DATA / f"order-in-play-{a.input}.json").read_text())[0]["pre"]).read_bytes()) if False else None
        rows_in = [x for x in json.loads((O.DATA / f"order-in-play-{a.input}.json").read_text())
                   if x["campaign"] == r["campaign"] and x["turn"] == r["turn"]][0]
        pre = sav.parse((c / rows_in["pre"]).read_bytes())
        owner = {i: x["owner"] for i, x in enumerate(pre["armies"])}
        pos_actual = {k: n for n, k in enumerate(r["actual"])}
        pos_remake = {k: n for n, k in enumerate(r["remake_rule"])}
        inv = []
        surv = r["actual"]
        for x in surv:
            for y in surv:
                if x < y and owner[x] == owner[y] and (pos_actual[x] < pos_actual[y]) != (pos_remake[x] < pos_remake[y]):
                    inv.append({"nation": owner[x], "pre_records": [x, y]})
        rows.append({"campaign": r["campaign"], "turn": r["turn"], "same_nation_inversions": inv})
        print(r["campaign"], r["turn"], inv)
    out.write_text(json.dumps(rows, indent=1))
    print("turns with a same-nation inversion", sum(bool(x["same_nation_inversions"]) for x in rows), "of", len(rows))


if __name__ == "__main__":
    main()
