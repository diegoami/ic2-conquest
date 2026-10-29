# run-exp-diff084-orders-b6: limits and refusals on staged saves (#230, batch 6)

Cases: `difftest/cases/orders230_b6.py` (17), written before running. Each starts from a staged copy of a fixture
(`difftest/stage.py`; the copy and its edits are in `staged/<case>.SAV` and `.json`), the same bytes for both games.
Set-up as in `../run-exp-diff084-orders/README.md`.

| Limit | Inside | Outside | Both games |
|---|---|---|---|
| Join armies: 20 units | 12 + 8 accepted | 12 + 9 refused (R03) | same |
| Join armies: 100,000 troops | exactly 100,000 accepted | 102,000 refused (R04) | same |
| Recruit: 40 slots | the 40th accepted | the 41st refused (R46) | same |
| Join fleets: 100 ships | 60 + 40 accepted | 60 + 41 refused (R15) | same (the later difference is one condition point, a storm draw) |

The single refusals are all the same in both games: split a one-unit army (R01), transfer into a 20-unit army (R28),
recruit at mobilisation 100 (R47), fortify a full city (R23) or one already being fortified (R24), split a fleet of
19 (R17), hire a mercenary into a 20-unit army (R08) or with 10 tons for 22,000 troops (R11). Recruiting 1,200 heavy
infantry (120 talents) with 50 in the treasury is **accepted by both**: the treasury goes into debt.

Harness corrections (earlier runs kept beside the re-runs, `-r2`):
- When a refusal box replaces the expected dialog, the adapter now keeps the box text as the game's answer
  (`original_refusals` in the results), not as a harness error.
- Order dialogs left open by a refusal are closed before each checkpoint save, and this is recorded in the receipt.

Re-run: `split-one-unit`, `transfer-into-20`, `fortify-full`, `fortify-in-progress`, `split-fleet-19`.
