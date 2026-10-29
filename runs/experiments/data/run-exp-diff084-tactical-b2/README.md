# run-exp-diff084-tactical-b2: shooting range, exact (#231, batch 2)

Cases: `difftest/cases/tactical231_b2.py`. Set-up as in `../run-exp-diff084-tactical/README.md`. A shooter at distance
1–4 (same row) shoots a heavy infantry unit. An accepted shot lowers its shots, a deterministic field.

| Shooter | d = 1 | d = 2 | d = 3 | d = 4 |
|---|---|---|---|---|
| archers 1,000 | same: shoots | same: shoots | same: refused | same: refused |
| light infantry 3,000 | same: shoots | same: shoots | same: refused | same: refused |

All 8 cases are identical on every deterministic field after the shot. The range is 2 in both games for both types.
