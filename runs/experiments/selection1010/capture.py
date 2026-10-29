#!/usr/bin/env python3
"""imperial_conquest_2#1010 (delegated by research 2026-10-30): controlled captures of the unit-map selection in the original.

    python3 runs/experiments/selection1010/capture.py --version v1

The code (TUnitMap_SelectUnit -> FUN_004465a8): when the selected cell is in view, image 12 of TerrainList (a 32x32 rhombus outline,
black on white, mask all opaque) is drawn on the tile with CopyMode SRCERASE (0x00440328: dest = src AND NOT dest), then CopyMode is
set back to SRCCOPY. Prediction per pixel: white image pixel -> the tile's colour inverted; black image pixel -> black.

One fresh process (seed 12345) per case on saves/fleet-port-antium-0734.SAV (Rome, 270 BC): click the cell, then screenshots before,
right after, +1.0 s and +2.5 s (a blink would show as a frame-to-frame change on the tile). Each tile is checked pixel by pixel
against the prediction. Cases: own army 0 (101,45), own fleet 2 (101,46), own town Fregellae (104,44), own capital Rome (101,43),
foreign town Caere (99,42, Gaul). Screenshots go to artifacts/run-exp-selection1010/ (release run-exp-selection1010), their SHA-256 to
the tracked data folder; the per-case table is tracked.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R))
from harness.driver import Game, UNIT_PAINT, VIEW_COLS, VIEW_ROWS, sh  # noqa: E402

ART = R / "artifacts/run-exp-selection1010"
DATA = R / "runs/experiments/data/run-exp-selection1010"
START = R / "saves/fleet-port-antium-0734.SAV"
EXE = Path.home() / "ic2-work/build/Imperial Conquest 2.exe"
CASES = [("army0", 101, 45), ("fleet2", 101, 46), ("town-fregellae", 104, 44), ("capital-rome", 101, 43), ("foreign-town-caere", 99, 42)]


def image12():
    """TerrainList image 12 from the TUnitMap form resource of the pinned EXE: True = white pixel."""
    b = EXE.read_bytes()
    i = b.find(b"\x0aTImageList\x0bTerrainList")
    assert i > 0
    j = b.find(b"\x06Bitmap\x0a", i)
    n = struct.unpack_from("<i", b, j + 8)[0]
    d = b[j + 12:j + 12 + n]
    size, count = struct.unpack_from("<ii", d, 0)
    assert count == 13
    bmp = d[8:8 + size]
    off = struct.unpack_from("<I", bmp, 10)[0]
    return {(x, y): bmp[off + (127 - (96 + y)) * 128 + x] == 255 for x in range(32) for y in range(32)}


def tile(png, x0, y0):
    out = subprocess.run(["convert", str(png), "-crop", f"32x32+{x0}+{y0}", "+repage", "txt:-"], capture_output=True, text=True,
                         check=True).stdout.splitlines()[1:]
    d = {}
    for line in out:
        xy, rest = line.split(":", 1)
        x, y = map(int, xy.split(","))
        d[(x, y)] = int(rest.split("#")[1][:6], 16)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    ART.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"captures-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    mask = image12()
    rows = []
    for name, x, y in CASES:
        g = Game()
        g.load(START, seed=12345)
        try:
            ox, oy = g.view_origin()
            c, r = x - ox, y - oy
            if not (0 <= c < VIEW_COLS and 0 <= r < VIEW_ROWS - 1):
                g.reset_ui()
                g.click(6 + x, 126 + y, pause=0.8)
                ox, oy = g.view_origin()
                c, r = x - ox, y - oy
            x0, y0 = UNIT_PAINT[0] - 1 + 32 * c, UNIT_PAINT[1] + 30 + 32 * r   # the paint box starts one column left of UNIT_PAINT (v1 used +0: off by one)
            nx, ny = g.neutral_point()
            sh("xdotool", "mousemove", str(nx), str(ny))
            time.sleep(1.0)
            shots = {}

            def snap(tag):
                p = ART / f"{v}-{name}-{tag}.png"
                if p.exists():
                    raise SystemExit(f"{p} exists")
                g.shot(str(p))
                shots[tag] = p

            snap("before")
            g.click(x0 + 16, y0 + 16, pause=0.6)
            sh("xdotool", "mousemove", str(nx), str(ny))
            time.sleep(0.4)
            snap("t0")
            time.sleep(1.0)
            snap("t1")
            time.sleep(1.5)
            snap("t2")
            before = tile(shots["before"], x0, y0)
            pred = {k: ((~before[k]) & 0xFFFFFF if mask[k] else 0) for k in before}
            row = {"case": name, "cell": [x, y], "view_origin": [ox, oy], "tile_px": [x0, y0], "files": {}, "match": {}, "unchanged": {}}
            for tag in ("t0", "t1", "t2"):
                t = tile(shots[tag], x0, y0)
                row["match"][tag] = sum(pred[k] == t[k] for k in t)
                row["unchanged"][tag] = sum(before[k] == t[k] for k in t)
            row["t0_equals_t1_equals_t2"] = tile(shots["t0"], x0, y0) == tile(shots["t1"], x0, y0) == tile(shots["t2"], x0, y0)
            for tag, p in shots.items():
                row["files"][tag] = {"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            rows.append(row)
            print(name, "match/1024", row["match"], "unchanged", row["unchanged"], "stable", row["t0_equals_t1_equals_t2"], flush=True)
        finally:
            g.kill()
    out.write_text(json.dumps({"exe_for_image": "Imperial Conquest 2.exe (9d753d5d...)", "game_exe": "seed build via harness.driver",
                               "start": START.name, "rows": rows}, indent=1))
    with open(DATA / "SAVES.sha256", "a") as f:
        for r in rows:
            for t in r["files"].values():
                f.write(f"{t['sha256']}  artifacts/run-exp-selection1010/{t['file']}\n")


if __name__ == "__main__":
    main()
