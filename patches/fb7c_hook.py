#!/usr/bin/env python3
"""The AI diplomacy hook (#195 own-capital stays, research intake PR #213, 2026-11-05): an observation-only build of the
seed exe that logs what FUN_0044fb7c decides each AI seat: the war target its search found, whether the Random(10) war
roll hit, and the alliance it formed.

    python3 patches/fb7c_hook.py <game folder>   # reads "... seed.exe", writes "... seed fb7chook.exe"

FUN_0044fb7c (pinned seed build): after the loop over the 16 nations, [esp+8] holds the war target (-1 for none);
`if target >= 0 && Random(10) == 0` declares war (FUN_00449b40(me, target, 3), 0x44FD47); with no war,
`Random(20) == 0` runs the alliance search, which declares an alliance with FUN_00449b40(me, ESI, 2) at 0x44FE5A.
Probes (each over whole position-independent instructions, re-run in the cave after pushfd/pushad, so the game runs the
same instructions on the same values and flags):
  1  0x44FD22  `cmp word [esp+8],-1` (6 bytes): every seat; the war target word (-1: none).
  2  0x44FD38  `mov cx,3; mov dx,[esp+8]` (9 bytes): only when the Random(10) roll hit; the target.
  3  0x44FE4E  `mov cx,2; mov edx,esi` (6 bytes): an alliance formed; the partner (ESI).
A 40-byte record (patches/walk_hook.py layout): +0 kind, +4 value, +0x18 nation, +0x1C week, +0x24 sequence.
Log: CTL 0x565000 (+0 count, +4 'FB7C', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import econ2_hook as E  # noqa: E402
import walk_hook as W  # noqa: E402

MAGIC = 0x43374246                      # 'FB7C'
DST = "Imperial Conquest 2 fast rollingsave seed fb7chook.exe"
SITES = {
    0x44FD22: (1, "66837c2408ff", [E.stack16(8)]),
    0x44FD38: (2, "66b90300668b542408", [E.stack16(8)]),
    0x44FE4E: (3, "66b902008bd6", [E.reg16("esi")]),
}
KINDS = {1: "war_target", 2: "war_declared", 3: "alliance"}


def build(b):
    saved = E.SITES, E.MAGIC
    E.SITES, E.MAGIC = SITES, MAGIC
    try:
        return E.build(b)
    finally:
        E.SITES, E.MAGIC = saved


def decode(buf, n):
    out = []
    for i in range(n):
        kind, a, _, _, _, _, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        out.append({"seq": seq, "nation": nation, "week": week, "kind": KINDS.get(kind, kind),
                    "nation_arg": struct.unpack("<h", struct.pack("<H", a & 0xFFFF))[0]})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
