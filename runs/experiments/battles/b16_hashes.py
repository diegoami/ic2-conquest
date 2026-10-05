#!/usr/bin/env python3
"""Write a NEW versioned SAVES.v<N>.sha256 in the tracked data folder: `<sha256>  <bare file name>` for every binary (.SAV, .png, .snap.gz) under
artifacts/run-exp-battle-peace/ (not archives/, not _tmp*), one form only. The older SAVES.sha256 (bare names from the runner, `shots/...`-style names from
one run of scripts/archive_measurements.py) is NOT edited. A name that occurs twice with different content (a versioned copy has its own name) is an error.

    python3 runs/experiments/battles/b16_hashes.py"""
import hashlib
import os
import sys
from pathlib import Path

os.environ.setdefault("IC2_WORK", "/nonexistent")
os.environ.setdefault("DISPLAY_IC2", ":640")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_common as B  # noqa: E402
import common as C  # noqa: E402

seen, lines = {}, []
for p in sorted(B.ART.rglob("*")):
    if p.is_file() and p.suffix.lower() in (".sav", ".png", ".gz") and "archives" not in p.parts and not p.name.startswith("_tmp"):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if p.name in seen and seen[p.name] != h:
            sys.exit("name %s occurs with two contents" % p.name)
        if p.name not in seen:
            lines.append("%s  %s" % (h, p.name))
        seen[p.name] = h
n = 2
while (B.DATA / ("SAVES.v%d.sha256" % n)).exists():
    n += 1
out = C.write_new(B.DATA, "SAVES.v%d.sha256" % n, "\n".join(lines) + "\n")
print(out, len(lines), "files")
