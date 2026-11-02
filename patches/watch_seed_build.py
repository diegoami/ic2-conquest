#!/usr/bin/env python3
"""The seeded WATCH build (owner 2026-11-02: "do not use no delay, use one of the watch"): async sound, the battle delay kept
but pumping window messages (patch_exe.pumping_delay), the rolling autosave and the SEED.TXT seed, i.e. patches/seed_patch.py
on "watch rollingsave" instead of "fast rollingsave". Built in memory from the fixtures' untouched original and written only
into the game folder (nothing is written into the fixtures repo).

    python3 patches/watch_seed_build.py <fixtures dir> <game folder>

Check: the same build without the seed must equal the owner's "Imperial Conquest 2 watch rollingsave.exe" (sha256 printed).
"""
import hashlib
import sys
from pathlib import Path

FIX, GAME = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.argv = [sys.argv[0], str(FIX)]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import seed_patch as S  # noqa: E402
P = S.P

orig = P.ORIGINAL.read_bytes()
ws = bytearray(orig)
for p in (P.async_sound, P.pumping_delay, P.autosave):
    p(ws)
print("watch rollingsave (rebuilt):", hashlib.sha256(ws).hexdigest())
S.seed_from_file(ws)
out = GAME / "Imperial Conquest 2 watch rollingsave seed.exe"
out.write_bytes(bytes(ws))
print("wrote", out, hashlib.sha256(ws).hexdigest())
