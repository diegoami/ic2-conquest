#!/usr/bin/env python3.12
"""Research #117 follow-up: cross-nation tie-breaks by table order in the AI's enemy-army pick FUN_0044ee60 (the strictly
greater score wins, so on a tie the lowest table index wins). Unicorn on the pinned EXE with the #187 RAM snapshot, through
runs/experiments/navigation187/core.py (read-only helper run, no RNG).

    python3.12 runs/experiments/armyorder117/tiebreak.py --version v1

Fixture: current nation 1 (Carthage), its army 2 (33,900 troops) at (47,62). Rome's armies 0 and 1 are re-placed at (44,62)
and (50,62), both 3 tiles away, each with one 2,000-troop light-infantry unit, and Carthage and Rome set at war (relation 3)
both ways. FUN_0044ee60(2) runs with records 0 and 1 as staged, then with the two records swapped. Reported: the chosen
record, its cell, the score and the distance; and, for contrast, the same with the two Romans at distances 3 and 4.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core as C  # noqa: E402
import visit_order as V  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-armyorder117"
REL = 0x474696                                   # nation n's relation to m: REL + n*0x494 + m*2


def fixture(east=(50, 62)):
    r = bytearray(C.RAM)
    C.put(r, 0x4a0320, 1)
    for n, m in ((1, 0), (0, 1)):
        C.put(r, REL + n * 0x494 + m * 2, 3)
    C.place_army(r, 0, (44, 62))
    C.place_army(r, 1, east)
    V.small_units(r, 0, 1, 2000)
    V.small_units(r, 1, 1, 2000)
    return r


def pick(r):
    out = C.run(0x44ee60, 2, 0x80a000, 0x80a002, args=(0x80a004,), ram=bytes(r))
    target, score, dist = out["words"][0], out["words"][1], out["words"][2]
    return {"record": target, "cell": C.xy(r, V.A + target * V.REC), "score_plus_distance": score, "distance": dist}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    out = DATA / f"tiebreak-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = []
    for name, east in (("tie: both at distance 3", (50, 62)), ("no tie: 3 and 4", (51, 62))):
        a = fixture(east)
        b = bytearray(a)
        V.swap(b, 0, 1)
        pa, pb = pick(a), pick(b)
        rows.append({"case": name, "as_staged": pa, "records_swapped": pb, "same_cell_chosen": pa["cell"] == pb["cell"]})
        print(name, "| staged:", pa, "| swapped:", pb)
    out.write_text(json.dumps({"ram": "#187 snapshot (private)", "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
