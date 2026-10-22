#!/usr/bin/env python3
"""G5: byte differences between X as opened (G5_<stamp>_X_original_before_anything.SAV) and X after File > Save (..._X_after_save.SAV), for the
`patched` and `original` runs. Writes g5_diff.txt (next free version)."""
import sys
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]; sys.path.insert(0, str(D)); sys.path.insert(0, str(R))
from versioned import write_new
from state import sav
A = R / "artifacts/run-exp-g1-original-checks"
out = []
for before in sorted(A.glob("G5_*_X_original_before_anything.SAV")):
    stamp = before.name.split("_")[1]; after = A / f"G5_{stamp}_X_after_save.SAV"
    if not after.exists(): continue
    b, a = before.read_bytes(), after.read_bytes()
    diffs = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    runs = []
    for i in diffs:
        if runs and i - runs[-1][1] <= 1: runs[-1][1] = i
        else: runs.append([i, i])
    out.append(f"{before.name} ({len(b)} bytes) vs {after.name} ({len(a)} bytes): {len(diffs)} differing bytes in {len(runs)} runs")
    out += [f"   0x{s:x}-0x{e:x} ({e - s + 1} bytes)  before {b[s:e + 1][:16].hex()}  after {a[s:e + 1][:16].hex()}" for s, e in runs[:40]]
    sb, sa = sav.parse(b), sav.parse(a)
    out.append("   parsed: " + ("identical (turn, week, nations, armies, cities, map)" if all(sb[k] == sa[k] for k in ("turn", "week", "nations", "armies", "cities", "fleets", "map")) else "differs"))
print("\n".join(out)); print(write_new(D / "g5_diff.txt", "\n".join(out) + "\n"))
