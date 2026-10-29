#!/usr/bin/env python3.12
"""Research #123: emulated controls of the AI capital defence FUN_0044efc8 (the homeland intercept) with swapped records.
Unicorn on the pinned EXE with the #187 RAM snapshot through runs/experiments/armyorder117/visit_order.run (unmodified
helpers and RNG; the attack and siege calls are logged and skipped, the redraw and sound stubbed). Every army move the
routine starts (FUN_0044dba8: army in EAX, target point in EDX) is logged.

    python3.12 runs/experiments/capdef123/controls.py --version v1

Fixture: current nation 1 (Carthage), capital Carthago at (93,78); its army 3 at (93,79) is the responder (moves 8, next to
the capital, so it is never exempted). The foreign armies used as threats are re-placed on free land cells and their owners
set at war with Carthage both ways (relation 3). Threat cells are taken only where FUN_0044eb9c(cell, capital) = 0 (v2;
v1 did not check the region, so fewer than 9 threats were listed and the cap case showed nothing).
- tie: Rome's army 0 at (90,79) and Seleucid army 4 at (96,79), both 3 tiles from the responder: as staged, then with
  records 0 and 4 swapped.
- cap: all 12 foreign armies re-placed within 19 of the capital; the nearest to the responder is record 13 (the 12th threat
  in table order, beyond the 9-entry list): as staged, then with records 0 and 13 swapped.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
sys.path.insert(0, str(ROOT / "runs/experiments/armyorder117"))
import core as C  # noqa: E402
import visit_order as V  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-capdef123"
REL = 0x474696
CAP = (93, 78)


def war(r, a, b):
    C.put(r, REL + a * 0x494 + b * 2, 3)
    C.put(r, REL + b * 0x494 + a * 2, 3)


def same_region(r, p):
    """FUN_0044eb9c(p, capital) == 0: the game's own "same region and coast side" test the threat list uses."""
    return C.run(0x44eb9c, C.point(p), C.point(CAP), ram=bytes(r))["eax"] & 0xFF == 0


def land_cells(r, near, lo, hi, avoid, region=False):
    cells = [(x, y) for x in range(near[0] - hi, near[0] + hi + 1) for y in range(near[1] - hi, near[1] + hi + 1)
             if lo <= max(abs(x - near[0]), abs(y - near[1])) <= hi and 2 <= C.cell(r, (x, y)) <= 11 and (x, y) not in avoid]
    return [p for p in cells if same_region(r, p)] if region else cells


def base():
    r = bytearray(C.RAM)
    C.put(r, 0x4a0320, 1)
    return r


def moves_of(log):
    return [{"army": e["army"], "target": [e["edx"] & 0xFFFF, e["edx"] >> 16]} for e in log if e["call"] == "army_move"]


def run(r):
    out, log, draws = V.run(r, 0x44efc8)
    return {"moves": moves_of(log), "skipped_attacks": [e for e in log if e["call"] in ("attack_army", "siege_city")], "draws": draws}


def tie_case():
    r = base()
    for owner in (0, 2):
        war(r, 1, owner)
    C.place_army(r, 0, (90, 79))
    C.place_army(r, 4, (96, 79))
    s = bytearray(r)
    V.swap(s, 0, 4)
    return {"case": "tie: Roman (90,79) and Seleucid (96,79), both 3 from the responder",
            "as_staged": run(r), "records_0_and_4_swapped": run(s)}


def cap_case():
    r = base()
    foreign = [i for i in range(C.short(r, 0x4a0324)) if C.short(r, V.A + i * V.REC + 4) not in (1, -1)]
    for i in foreign:
        war(r, 1, C.short(r, V.A + i * V.REC + 4))
    occupied = {tuple(C.xy(r, V.A + i * V.REC)) for i in range(C.short(r, 0x4a0324))} | {CAP}
    cells = land_cells(r, CAP, 8, 19, occupied, region=True)
    cells.sort(key=lambda p: -max(abs(p[0] - 93), abs(p[1] - 79)))         # far from the responder first
    placed = {}
    for i in foreign[:-1]:
        p = cells.pop(0)
        C.place_army(r, i, p)
        placed[i] = p
    near = land_cells(r, (93, 79), 2, 3, occupied | set(placed.values()), region=True)[0]
    C.place_army(r, foreign[-1], near)                                    # record 13: the nearest, 12th in table order
    placed[foreign[-1]] = near
    s = bytearray(r)
    V.swap(s, foreign[0], foreign[-1])
    listed = sum(1 for i in foreign if same_region(r, tuple(C.xy(r, V.A + i * V.REC)))
                 and max(abs(C.xy(r, V.A + i * V.REC)[0] - CAP[0]), abs(C.xy(r, V.A + i * V.REC)[1] - CAP[1])) <= 19)
    return {"case": f"cap: {len(foreign)} threats ({listed} in the capital's region within 19); record {foreign[-1]} nearest "
                    f"to the responder at {near}",
            "threat_cells": {str(k): v for k, v in placed.items()},
            "as_staged": run(r), f"records_{foreign[0]}_and_{foreign[-1]}_swapped": run(s)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"controls-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = [tie_case(), cap_case()]
    out.write_text(json.dumps({"ram": "#187 snapshot (private)", "rows": rows}, indent=1))
    for row in rows:
        print(row["case"])
        for k, val in row.items():
            if isinstance(val, dict) and "moves" in val:
                print("  ", k, val["moves"])


if __name__ == "__main__":
    main()
