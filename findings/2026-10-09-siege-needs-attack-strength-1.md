# Siege: an army needs an attack strength of at least 1 (80 men, or 27 archers) to besiege

**Status:** a draft from `ic2-conquest`, awaiting promotion. It is an addendum to `2026-10-09-siege-removed-army-restores-its-tile.md` (research `99899ac`) and checks research's reading of `FUN_0044a930`: atk = Σ troops (archers × 3) div 80 × morale.

**Tag:** `[confirmed]` for the boundary. `[derived]` for the cause (the division by zero at 0x0044B249 per research).

## Answer

| Army 0 | Σ troops (archers × 3) | div 80 | Result |
|---|---:|---:|---|
| 79 heavy infantry | 79 | 0 | **no siege**: moves stay 8, Felsina unchanged, army unchanged |
| 80 heavy infantry | 80 | 1 | **siege** (Felsina fort 65 → 62), army removed by attrition |
| 26 archers | 78 | 0 | **no siege** |
| 27 archers | 81 | 1 | **siege**, army removed by attrition |

- The boundary is exactly where Σ troops (archers counted × 3) div 80 reaches 1. Morale was 70 in every case.
- The armies that besieged were then removed by attrition (units under 600 men are deleted, per research). Their tiles read **5**, the patched covered cell, as in the 99/100/150 cases.
- The armies that did not besiege kept their moves (8), so the order left no trace: no siege, no move spent, no box.

Evidence: run-exp-siege-army-removal, `u79_*`, `u80_*`, `ar26_*`, `ar27_*` `{PRE,BEFORE,AFTER}.SAV` (release `run-exp-siege-army-removal`; SHA-256 in `runs/experiments/data/run-exp-siege-army-removal/SAVES.sha256`); `probe_siege.v2.py`, `probe_siege.v2.log` (batch 2), `probe_siege_u79_u80_ar26_ar27.json`.

## Method

As in `2026-10-09-siege-removed-army-restores-its-tile.md`:
- The fixture is `saves/siege-felsina-failed-0721.SAV`. The patch gives Rome army 0 at (99,32) moves 8, covered cell 5, and a single quality-7 unit: heavy infantry (type 1) or archers (type 2).
- Fast rollingsave seed exe, seed 12345, Xvfb :99. Then `g.attack(0, 98, 31)`.
