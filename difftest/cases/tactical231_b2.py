"""#231 batch 2: shooting range, exact. A shooter at Chebyshev distance d (same row) shoots one enemy; an accepted
shot lowers its shots (a deterministic field), a refused one changes nothing. Written 2026-10-29 after the remake
probe: archers shoot at d = 1, 2 and are refused from 3 (`tac-range` scratch probe, seed 1)."""
CASES = []
for t, troops in (("ar", 1000), ("li", 3000)):
    for d in (1, 2, 3, 4):
        CASES.append({"id": f"range-{t}-d{d}", "note": f"{t} shoots a heavy infantry unit at distance {d}",
                      "attacker": [(t, troops, 7), ("hi", 2000, 7)], "defender": [("hi", 2000, 7), ("li", 1000, 6)],
                      "positions": {0: (3, 3), 1: (2, 2), 20: (3 + d, 3), 21: (12, 10)}, "script": ["shoot 0 20"]})
