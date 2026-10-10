"""Before/after table read from the SAVES (state/sav.py, read-only): ships, supplies (+14), money (+16), owner of fleets 2 and 5, Rome's treasury.
python3 table_from_saves.py > table_from_saves.md  (run from anywhere; saves in artifacts/run-exp-fleet-empty-transfer/)"""
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from state import sav
A = R / "artifacts/run-exp-fleet-empty-transfer"
print("| Case | Save | Fleet 2 (owner, ships, +14 supplies, +16 money) | Fleet 5 (owner, ships, +14, +16) | Rome treasury |\n|---|---|---|---|---|")
for case in sorted({p.name.split("_")[0] for p in A.glob("Td*_after.SAV")}):
    for kind in ("before", "after"):
        for p in sorted(A.glob(f"{case}_*_{kind}.SAV")):
            s = sav.load(p); f = s["fleets"]
            fmt = lambda i: f"{f[i]['owner']}, {f[i]['ships']}, {f[i]['supplies']}, {f[i]['money']}"
            print(f"| {case} | `{p.name}` | {fmt(2)} | {fmt(5)} | {s['nations'][0]['treasury']} |")
