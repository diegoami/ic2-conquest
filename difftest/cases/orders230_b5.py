"""#230 batch 5: two more walks that ended apart in the #232 nation campaigns (2026-10-29), as single orders.
Written before these cases ran. Expected (research PR #94): the original's move handler walks a second time when
the army is short of its target with moves left; the remake makes one walk.

- Carthage start (run-exp-civ-sweep S01_Carthage_AUTO0720.SAV): army 3 at (93,79) toward (61,56). Campaign:
  original (89,76), remake (90,77) "spending 7 of 8 moves".
- Gaul start (S06_Gaul_AUTO0720.SAV): army 9 at (93,28) toward (92,34). Campaign: original (92,34) with 1 move
  left, remake (92,32) "spending 5 of 8 moves".
"""
from pathlib import Path

from difftest.cases.orders230_b1 import case

ROOT = Path(__file__).resolve().parents[2]
CIV = ROOT / "artifacts/run-exp-civ-sweep"

CASES = [
    case("walk-carthage-army3", "Carthage army 3 from (93,79) toward (61,56)",
         {"op": "move", "army": 3, "x": 61, "y": 56}, start=str(CIV / "S01_Carthage_AUTO0720.SAV")),
    case("walk-gaul-army9", "Gaul army 9 from (93,28) toward (92,34)",
         {"op": "move", "army": 9, "x": 92, "y": 34}, start=str(CIV / "S06_Gaul_AUTO0720.SAV")),
]
