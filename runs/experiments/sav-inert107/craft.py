#!/usr/bin/env python3
"""Craft the marked inputs of run-exp-sav-inert107 (conquest issue #107).

    python3 runs/experiments/sav-inert107/craft.py OUT_DIR

- T1: saves/run0-start-AUTO0720-seed12345.SAV with a non-zero marker in each
  nation's INERT ranges (+0x450..0x46A, +0x46D, +0x491..0x493): byte = 0x80 | n
  in the first range, 0xC0 | n in the pads, so every nation and range differs.
- T2: saves/fleet-split-antium-0734.SAV with route_y = 1000 + f on every live
  fleet whose route_x is -1 (a sentinel only the absent route_y reset could clear).
Outputs are created exclusively, never overwritten (CLAUDE.md rule 6).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import sav_atlas_coverage as cov  # noqa: E402

INERT = [(0x450, 0x46A), (0x46D, 0x46D), (0x491, 0x493)]


def mark_inert(b):
    b = bytearray(b)
    blocks, _ = cov.frame(bytes(b))
    n0 = {r: o for r, o, _ in blocks}["nation"]
    for n in range(16):
        for k, (lo, hi) in enumerate(INERT):
            for o in range(lo, hi + 1):
                b[n0 + 1172 * n + o] = (0x80 if k == 0 else 0xC0) | n
    return bytes(b)


def mark_route(b):
    b = bytearray(b)
    blocks, facts = cov.frame(bytes(b))
    f0 = {r: o for r, o, _ in blocks}["fleet"]
    for f in range(facts["fleets"]):
        o = f0 + 26 * f
        rx, owner = struct.unpack_from("<h", b, o + 4)[0], struct.unpack_from("<h", b, o + 8)[0]
        if owner >= 0 and rx == -1:
            struct.pack_into("<h", b, o + 6, 1000 + f)
    return bytes(b)


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for src, fn, name in (("saves/run0-start-AUTO0720-seed12345.SAV", mark_inert, "T1M_0720_inert_marked.SAV"),
                          ("saves/fleet-split-antium-0734.SAV", mark_route, "T2M_0734_route_y_sentinel.SAV")):
        data = fn((ROOT / src).read_bytes())
        cov.frame(data)                                  # still frames to EOF
        with open(out / name, "xb") as fh:
            fh.write(data)
        print(name, len(data))


if __name__ == "__main__":
    main()
