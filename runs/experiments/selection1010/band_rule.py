#!/usr/bin/env python3
"""Research #124: the exact black-pixel rule of TerrainList image 12 (the unit-map selection rhombus), extracted from the
pinned EXE's TUnitMap form resource (capture.image12). Tries every centre (15, 15.5, 16, 16.5 on each axis) and every
taxicab band [lo, hi] for lo, hi in 10..23, and writes the matches and the row-by-row black runs. No image is written.

    python3 runs/experiments/selection1010/band_rule.py --version v1
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture as C  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    out = C.DATA / f"band-rule-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    m = C.image12()
    black = {k for k, w in m.items() if not w}
    matches = []
    for cx2 in (30, 31, 32, 33):
        for cy2 in (30, 31, 32, 33):
            for lo in range(10, 24):
                for hi in range(lo, 24):
                    s = {(x, y) for x in range(32) for y in range(32) if 2 * lo <= abs(2 * x - cx2) + abs(2 * y - cy2) <= 2 * hi}
                    if s == black:
                        matches.append({"centre": [cx2 / 2, cy2 / 2], "taxicab_from": lo, "taxicab_to": hi})
    runs = []
    for y in range(32):
        row, r = [x for x in range(32) if (x, y) in black], []
        for x in row:
            if r and x == r[-1][1] + 1:
                r[-1][1] = x
            else:
                r.append([x, x])
        runs.append({"row": y, "black_runs": r})
    out.write_text(json.dumps({"black_pixels": len(black), "white_pixels": 1024 - len(black), "matches": matches,
                               "rows": runs}, indent=1))
    print(len(black), matches)


if __name__ == "__main__":
    main()
