#!/usr/bin/env python3.12
"""Research #105: whole-wrapper controls of the AI army move FUN_0044dba8 when its walk makes no progress, in Unicorn on the
pinned unpatched EXE with the #187 live-RAM snapshot (runs/experiments/navigation187/core.py: no helper or RNG replaced).

    python3.12 runs/experiments/fallback105/wrapper_controls.py --version v1

Fixture: core.fresh_map() (every cell Plain, army phase flag DAT_004a0340 = 0), Rome's army 2 at ORIGIN, target east at
distance D. The march is blocked by own army markers on the three cells toward the target (armies 0, 1, 3), so the walk
FUN_0044d734 leaves moves unchanged. Varied: moves, D, the wrapper's uninitialised local_e (the #97 stale word: 0 runs the
fallback, -1 skips it), and sea pockets that change which of the eight 3-cell probes of FUN_0044cec8 succeed.
Per case: every wrapper entry, each walk's goal (the D734 calls), CEC8's origin, final cell and moves left.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
import core as C  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-fallback105"
A2 = 0x47c1ec + 2 * 656
ORIGIN = (100, 40)


def case(moves, dist, residue, pocket):
    r = C.fresh_map()
    C.place_army(r, 2, ORIGIN, 1)
    for i, p in zip([0, 1, 3], [(101, 39), (101, 40), (101, 41)]):
        C.place_army(r, i, p, 1)
    for p in pocket:
        C.setcell(r, p, 0)
    C.put(r, A2 + 6, moves)
    target = (ORIGIN[0] + dist, ORIGIN[1])
    try:
        v = C.run(0x44dba8, 2, C.point(target), ram=r, local_e=residue, readonly=False, budget=30_000_000)
    except Exception as e:                           # budget spent or stack overflow (deep recursion): recorded, not hidden
        return {"moves": moves, "target": list(target), "residue": residue, "pocket": [list(p) for p in pocket],
                "error": f"{type(e).__name__}: {e}"}
    pt = lambda w: [w & 0xFFFF if w & 0xFFFF < 0x8000 else (w & 0xFFFF) - 0x10000, w >> 16]
    calls = [(t["function"], pt(t["edx"]) if t["function"] in ("0x44d734", "0x44dba8") else pt(t["eax"])) for t in v["trace"]]
    return {"moves": moves, "target": list(target), "residue": residue, "pocket": [list(p) for p in pocket],
            "wrapper_entries": sum(f == "0x44dba8" for f, _ in calls),
            "cec8_origins": [p for f, p in calls if f == "0x44cec8"],
            "walk_goals": [p for f, p in calls if f == "0x44d734"],
            "final": C.xy(v["ram"], A2), "moves_left": C.short(v["ram"], A2 + 6),
            "calls": [f for f, _ in calls]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    out = DATA / f"wrapper-controls-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    x, y = ORIGIN
    pockets = {
        "none": [],
        "se-sea": [(x + 2, y + 2)],                                   # (1,1) probe fails: (1,0) is the last success
        "east-half-sea": [(x + i, y + j) for i in (2, 3) for j in range(y - 3 - y, 4)],  # every dx=+1 probe fails
        "ring-sea": [(x + i, y + j) for i in range(-3, 4) for j in range(-3, 4) if max(abs(i), abs(j)) == 3],  # all fail
    }
    rows = []
    for name, pocket in pockets.items():
        for moves in (1, 2, 3, 5, 8):
            for dist in (3, 6):
                for residue in (0, -1):
                    rows.append(dict(case(moves, dist, residue, pocket), pocket_name=name))
    out.write_text(json.dumps({"exe_sha256": "9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31",
                               "ram": "artifacts/run-exp-strategic-fidelity/original/N-rome-hook-v1/snapshots/000.ram (private)",
                               "origin": list(ORIGIN), "rows": rows}, indent=1))
    for r in rows:
        if "error" in r:
            print(r["pocket_name"], "m", r["moves"], "T", r["target"], "e", r["residue"], r["error"])
            continue
        print(r["pocket_name"], "m", r["moves"], "T", r["target"], "e", r["residue"], "entries", r["wrapper_entries"],
              "cec8", r["cec8_origins"], "goals", r["walk_goals"], "final", r["final"], "left", r["moves_left"])


if __name__ == "__main__":
    main()
