#!/usr/bin/env python3
"""Decoded diff of two saves (map cells, cities, armies, fleets, nations, mercenaries, news, calendar): one line per changed field.

    python3 runs/experiments/manual_gaps/diff_saves.py BEFORE AFTER
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state import sav  # noqa: E402


def flat(prefix, v, out):
    if isinstance(v, dict):
        for k, x in v.items():
            flat(f"{prefix}.{k}", x, out)
    elif isinstance(v, list) and prefix.endswith(("cities", "armies", "fleets", "nations", "mercenaries")):
        for i, x in enumerate(v):
            flat(f"{prefix}[{i}]", x, out)
    else:
        out[prefix] = v


def diff(a_path, b_path):
    a, b = sav.load(a_path), sav.load(b_path)
    lines = []
    for x in range(sav.MAP_W):
        for y in range(sav.MAP_H):
            va, vb = a["map"][x * 140 + y], b["map"][x * 140 + y]
            if va != vb:
                lines.append(f"map({x},{y}): {va} -> {vb}")
    fa, fb = {}, {}
    for k in ("cities", "armies", "fleets", "nations", "mercenaries"):
        flat(k, a[k], fa)
        flat(k, b[k], fb)
    for k in ("news", "turn_order", "pending_offer", "current_nation", "week", "year_bc", "season", "battle_flag"):
        fa[k], fb[k] = a[k], b[k]
    for k in sorted(set(fa) | set(fb)):
        if fa.get(k) != fb.get(k):
            if k == "news":
                new = [n for n in fb[k] if n not in fa[k]]
                lines.append(f"news: +{new}")
            else:
                lines.append(f"{k}: {fa.get(k)} -> {fb.get(k)}")
    return lines


if __name__ == "__main__":
    for line in diff(sys.argv[1], sys.argv[2]):
        print(line)
