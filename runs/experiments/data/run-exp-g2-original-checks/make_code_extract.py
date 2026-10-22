#!/usr/bin/env python3
"""Line-numbered extract of every decompiled function that findings/2026-10-11-g2-original-checks.md cites (review fix R1), from the pinned
all_app_functions.txt (SHA-256 checked by harness.decompile.check(); the first column of the extract is that file's line number).
Writes code_extract_g2.txt beside this script, the next free version if it exists (rule 6, never overwrites)."""
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import decompile
from versioned import write_new
decompile.check()
dump = Path(decompile.DUMP); sha = decompile.PINS[dump.name]
L = dump.read_text(errors="replace").split("\n")
heads = [(i, L[i].split()[2]) for i in range(len(L)) if L[i].startswith("// ==== ")]
rng = {}
for k, (i, name) in enumerate(heads):
    end = (heads[k + 1][0] - 1) if k + 1 < len(heads) else len(L) - 1
    while end > i and not L[end].strip(): end -= 1
    rng[name] = (i, end)          # 0-based header line .. last non-blank line
# why each function is in the extract (finding section)
WHY = [
    ("TUnitMap_SelectUnit", "C3: own army marker 200..247 selected (46555-46562), buttons on (46653); the only moves test is at 46514 (attack gating)"),
    ("TUnitMap_MoveHumanArmy", "C3/C4: walk, second walk call when not there and moves remain (46728-46734), selection ended at 0 moves (46739-46741)"),
    ("TUnitMap_EndUMSelection", "C3: clears the selection"),
    ("FUN_0044d734", "C4: Bresenham walk over the tiles of the line"),
    ("FUN_0044d420", "C4: the step: line tile vs its two lateral neighbours; taken if cost <= moves left"),
    ("FUN_0044d31c", "C4: terrain cost of a tile (10 = impassable / not adjacent)"),
    ("FUN_00449018", "C4: distance used by the walk"),
    ("TChangeArmyUnits_SplitUnit", "C5c: split threshold limit*2/5 (45558), 'regular units only', 20-unit limit"),
    ("FUN_004514ec", "C7: the weekly sea block: storm damage, the call of FUN_0044b4f8 (54591), 'damaged in a storm' (54604), zero-supply decrement"),
    ("FUN_0044b4f8", "C7: storm damage to a fleet: d, ships, condition, carried army"),
    ("FUN_0044ae20", "C7: army damage: per-slot troop loss, under-limit removals"),
    ("FUN_0044ac3c", "C7: removal of one army slot"),
    ("FUN_0044a66c", "C7: span of an army's slots (last occupied index + 1)"),
    ("FUN_0044ab90", "C7: called by the slot removal when slot 0 is empty (army emptied)"),
    ("FUN_0044a80c", "C7: called by the slot removal otherwise"),
    ("FUN_0044a878", "C7: end of FUN_0044b4f8 (fleet record update)"),
    ("FUN_004494e4", "C7: tested for sign in the storm damage block"),
    ("FUN_00448fd0", "min of two shorts"),
    ("FUN_00448fd8", "max of two shorts"),
    ("FUN_0040284c", "random number 0..n-1 (LCG, high word of n*state)"),
]
out = ["# Code extract for findings/2026-10-11-g2-original-checks.md",
       f"# Provenance: {dump.name}, SHA-256 {sha} (pinned in harness/decompile.py PINS and verified by decompile.check() when this was written).",
       "# First column = line number in that file. Functions are whole (header line to last non-blank line). Index:"]
for name, why in WHY:
    a, b = rng[name]; out.append(f"#   {name}: lines {a + 1}-{b + 1}  ({why})")
for name, why in WHY:
    a, b = rng[name]; out.append(f"\n# ===== {name} (lines {a + 1}-{b + 1}) =====")
    out += [f"{j + 1}\t{L[j]}" for j in range(a, b + 1)]
print(write_new(Path(__file__).resolve().parent / "code_extract_g2.txt", "\n".join(out) + "\n"))
