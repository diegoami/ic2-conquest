# run-exp-diff084-orders-b3: fleet orders, mobilization and unit orders (#230, batch 3)

Cases: `difftest/cases/orders230_b3.py` (14). Set-up as in `../run-exp-diff084-orders/README.md`. Starts:
`saves/fleet-port-antium-0734.SAV`, `saves/fleet-split-antium-0734.SAV` and `BASE.SAV`.

## Final verdicts (newest `results-rejudged-*.jsonl`)

The two fleet saves start with two differences from the import → export round trip (three conquered cities'
marker variant and the empty offer's type): `findings/2026-10-29-export-city-marker-variant-and-empty-offer230.md`.
The verdicts set them aside, since they are present at `a000` and unchanged after the orders.

| Case | Order(s) | Verdict |
|---|---|---|
| `embark`, `embark-sail`, `scuttle`, `join-fleets`, `mobilize-port-0`, `mobilize-base-3`, `disband-unit`, `join-units-hi`, `split-transfer-unit` | as named | same, also on Rome's records after End turn |
| `embark-turn-disembark`, `repair-3`, `split-fleet-10`, `transfer-ships-5` | as named | the orders give the same state. After End turn, one Roman fleet's condition differs by 1 point: the storm draw, which is random and statistically consistent between the games (#233 `storm30b`) |
| `fleet-sail` | fleet 2 sails to (97,48) | the order gives the same state. After End turn, Carthage's fleet has sunk Rome's in the original only: the AI fleet hunt, `findings/2026-10-29-ai-fleet-hunt-absent-in-remake233.md` |

No harness correction was needed in this batch.
