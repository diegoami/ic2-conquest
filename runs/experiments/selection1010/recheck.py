#!/usr/bin/env python3
"""Re-check the v1 captures (runs/experiments/selection1010/capture.py) with the corrected tile origin: v1 cropped one pixel to the
right of the tile (UNIT_PAINT x 337; the first painted column is 336). Reads the kept screenshots only; writes recheck-<version>.json.

    python3 runs/experiments/selection1010/recheck.py --version v2
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
    out = C.DATA / f"recheck-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    m = C.image12()
    rows = []
    for row in json.loads((C.DATA / "captures-v1.json").read_text())["rows"]:
        x0, y0 = row["tile_px"][0] - 1, row["tile_px"][1]
        before = C.tile(C.ART / row["files"]["before"]["file"], x0, y0)
        pred = {k: ((~before[k]) & 0xFFFFFF if m[k] else 0) for k in before}
        tiles = {g: C.tile(C.ART / row["files"][g]["file"], x0, y0) for g in ("t0", "t1", "t2")}
        rows.append({"case": row["case"], "cell": row["cell"], "tile_px": [x0, y0],
                     "match_of_1024": {g: sum(pred[k] == t[k] for k in t) for g, t in tiles.items()},
                     "black_pixels_in_image12": sum(not w for w in m.values()),
                     "already_black_before": sum(before[k] == 0 and not m[k] for k in before),
                     "t0_t1_t2_equal": tiles["t0"] == tiles["t1"] == tiles["t2"]})
        print(rows[-1])
    out.write_text(json.dumps({"source": "captures-v1.json screenshots", "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
