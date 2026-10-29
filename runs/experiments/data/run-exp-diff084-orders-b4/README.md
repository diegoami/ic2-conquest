# run-exp-diff084-orders-b4: walks with an own city on the line (#230, batch 4)

Cases: `difftest/cases/orders230_b4.py`, written after the #232 campaign showed the difference and before these
cases ran (except `walk-line-clear-land`, added once `walk-line-clear`'s target proved to be sea). Set-up as in
`../run-exp-diff084-orders/README.md`.

| Case | Verdict |
|---|---|
| `walk-city-on-line` (army 1 to (99,32)) | differs: original (115,49), 1 move left; remake (118,52), 6 left |
| `walk-city-on-line-near` (to (116,49)) | differs: original (116,49); remake (118,52) |
| `walk-line-clear` (to (120,45)) | the target is sea: the known command gap, not a control |
| `walk-line-clear-land` (to (120,48)) | same |

Finding: `findings/2026-10-29-walk-stops-at-own-city-on-line230.md`.
