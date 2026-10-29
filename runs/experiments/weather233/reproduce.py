#!/usr/bin/env python3
"""Reproduce the original's weather pass (FUN_00451304, research decompiled-map-code1-overlay.md) draw-exactly.

For each weather trial of the original (difftest #233, run-exp-diff084-stats/<scenario>/original-s<seed>/a001.SAV) the
observed hit set is the set of the 20 DAT centres whose central 3x3 has >= 5 rough cells. wx.c walks Delphi's LCG
(seed * 0x08088405 + 1, Random(n) = n * seed >> 32) from RandSeed = the trial's seed and lists every offset N at which the
decompiled roll (per centre Random(15) == 0, then 208 Random(2) ring draws on a hit) yields exactly that set. A rule match
for a multi-hit set at an offset of a few hundred draws (a random 3-hit set matches by chance about once per 10^4 offsets)
shows the roll is the decompiled one.

    python3 runs/experiments/weather233/reproduce.py weather30 --max 20000000 --version v1
"""
import argparse
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STATS = ROOT / "artifacts/run-exp-diff084-stats"
DATA = ROOT / "runs/experiments/data/run-exp-weather233"
ART = ROOT / "artifacts/run-exp-weather233"
CENTRES = [(10, 10), (32, 79), (74, 50), (68, 68), (92, 68), (100, 56), (105, 81), (131, 66), (126, 89), (148, 86),
           (177, 83), (206, 83), (213, 70), (180, 74), (158, 69), (153, 48), (177, 24), (191, 10), (209, 12), (233, 22)]


def mask(path):
    g = struct.unpack_from("<44800h", path.read_bytes(), 0)
    return sum(1 << i for i, (cx, cy) in enumerate(CENTRES)
               if sum(g[x * 140 + y] == 1 for x in range(cx - 1, cx + 2) for y in range(cy - 1, cy + 2)) >= 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--max", type=int, default=20_000_000)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()
    out = DATA / f"reproduce-{a.scenario}-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    ART.mkdir(parents=True, exist_ok=True)
    exe = ART / "wx"
    subprocess.run(["gcc", "-O2", "-o", str(exe), str(HERE / "wx.c")], check=True)
    obs = {}
    for d in sorted((STATS / a.scenario).glob("original-s*"), key=lambda p: int(p.name.split("-s")[1])):
        if (d / "a001.SAV").exists():
            obs[int(d.name.split("-s")[1])] = mask(d / "a001.SAV")
    inp = "".join(f"{s} {m}\n" for s, m in obs.items() if m)
    res = subprocess.run([str(exe), str(a.max)], input=inp, capture_output=True, text=True, check=True).stdout
    first, count = {}, {}
    for line in res.splitlines():
        w = line.split()
        if w[2] == "N":
            first.setdefault(int(w[1]), int(w[3]))
        else:
            count[int(w[1])] = int(w[5])
    rows = [{"seed": s, "mask": m, "hits": bin(m).count("1"), "first_offset": first.get(s), "matches_in_max": count.get(s)}
            for s, m in obs.items()]
    out.write_text(json.dumps({"scenario": a.scenario, "max_offset": a.max, "rows": rows}, indent=1))
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
