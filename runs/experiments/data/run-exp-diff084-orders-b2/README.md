# run-exp-diff084-orders-b2: controls for the war cascade, and a far land move (#230, batch 2)

Cases and their predictions, written before the run: `difftest/cases/orders230_b2.py`. Set-up as in
`../run-exp-diff084-orders/README.md`.

| Case | Predicted (original) | Original | Remake | Verdict |
|---|---|---|---|---|
| `rel-war-numidia` | ally Carthage (1) at war, 3 | 3 | 3 | same |
| `rel-war-dacia` | ally Thracia (15) at −18 | −18 | 3 | differs |
| `rel-war-thracia` | ally Dacia (10) at war, 3 | 3 | 3 | same |
| `rel-war-bithynia` | ally Galatia (12) at −18 | −18 | 3 | differs |
| `move-far-land` | (a far land move through the selection-keeping adapter) | | | same |

Finding: `findings/2026-10-29-war-declaration-ally-cooldown-diff230.md`.
