#!/usr/bin/env python3.12
"""Research #117 follow-up: does the AI fleet merge FUN_00450b30 pick differently when two fleets of a nation sit in the
other table order? Unicorn on the pinned EXE with the #187 RAM snapshot (two fleets: 0 Carthage at (49,62), 1 another nation).
Staged: current nation 1; fleet 1 given to Carthage at (48,66), a sea cell 4 tiles from fleet 0 at (49,62); both 20 ships, launched (+10 = -1), not
carrying (+22 = -1), markers placed. FUN_00450b30 runs as staged and with the two records swapped (fleet records exchanged
whole). Reported: the surviving record, its cell and ships, the count word.

    python3.12 runs/experiments/armyorder117/fleet_merge.py --version v1
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core as C  # noqa: E402
import visit_order as V  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-armyorder117"
F, FL = 0x49c26c, 26


def fl(r, i, off):
    return C.short(r, F + i * FL + off)


def setf(r, i, off, v):
    C.put(r, F + i * FL + off, v)


def fixture():
    r = bytearray(C.RAM)
    C.put(r, 0x4a0320, 1)
    x, y = fl(r, 1, 0), fl(r, 1, 2)
    C.setcell(r, (x, y), fl(r, 1, 24) if fl(r, 1, 24) >= 0 else 0)       # lift fleet 1's old marker
    setf(r, 1, 0, 48); setf(r, 1, 2, 66)
    setf(r, 1, 24, C.cell(r, (48, 66)))
    for i in (0, 1):
        setf(r, i, 8, 1); setf(r, i, 18, 20); setf(r, i, 10, -1); setf(r, i, 22, -1)
        C.setcell(r, (fl(r, i, 0), fl(r, i, 2)), 300 + 1)
    return r


def swap(r):
    a, b = F - C.ORIGIN, F + FL - C.ORIGIN
    r[a:a + FL], r[b:b + FL] = bytes(r[b:b + FL]), bytes(r[a:a + FL])


def run(r):
    out, _, _ = V.run(r, 0x450b30)
    n = C.short(out, 0x4a0326)
    return {"count": n, "fleets": [{"record": i, "owner": fl(out, i, 8), "cell": [fl(out, i, 0), fl(out, i, 2)], "ships": fl(out, i, 18)}
                                   for i in range(n)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    out = DATA / f"fleet-merge-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    a = fixture()
    b = bytearray(a)
    swap(b)
    before = {"as_staged": [[fl(a, i, 0), fl(a, i, 2)] for i in (0, 1)], "swapped": [[fl(b, i, 0), fl(b, i, 2)] for i in (0, 1)]}
    ra, rb = run(a), run(b)
    out.write_text(json.dumps({"ram": "#187 snapshot (private)", "cells_before": before, "as_staged": ra, "swapped": rb}, indent=1))
    print("before", before)
    print("as staged:", ra)
    print("swapped:  ", rb)


if __name__ == "__main__":
    main()
