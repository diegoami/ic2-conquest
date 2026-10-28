# run-exp-diff084-orders: every strategic order from the same save in both games (#230, batch 1)

Task #230 (tracker #228), approved by the owner on 2026-10-28. Batch 2 (controls): `../run-exp-diff084-orders-b2/`.
Remake v0.8.4 (`d9cc71bc`), `classical-faithful`; original `fast rollingsave seed.exe`, seed 12345, Wine 10.0.
Start: `BASE.SAV` (Rome, 270 BC Spring week 1). Cases: `difftest/cases/orders230_b1.py` (47 cases).

Each case plays its order(s) then one End turn in both games (`python3 -m difftest.sweep`). The order's own
checkpoints are compared in full. The state after End turn is compared on the acting nation's records only,
because AI moves and random draws follow.

## Final verdicts (latest run of each case, `results-rejudged-*.jsonl`, the newest file)

| Verdict | Cases |
|---|---|
| same | 43, all of which also agree on Rome's own records after End turn |
| differs: Build fleet site | `fleet-10`, `fleet-25`, `fleet-two`: the original builds at Caere (82, nearest the capital), the remake at Pisae (71, first in world order). Known since `findings/2026-10-09-fleet-build-city-nearest-capital.md`; still present in v0.8.4 |
| differs: war cascade | `rel-war-carthage`: `findings/2026-10-29-war-declaration-ally-cooldown-diff230.md` |
| remake command accepts what its interface blocks | `move-sea`, `move-far`: both targets are SEA tiles. The original ignores the click, and so does the remake's map click (`godot/UI/MapClickRules.cs`: an army and a sea tile, "nothing at all"). Only the remake's `move` command walks toward the shore. Not a difference a remake player sees |

The same class as `move-sea`: the remake's `recruit-standing` command accepts amounts below the dialogs' minimum
(battalion / 5). Seen in `run-exp-diff084-tooling`; the scripts here use only amounts both dialogs allow.

## Harness corrections made during the batch (the earlier runs are kept beside the re-runs)

`results.jsonl` holds every run, in order. A re-run gets new folders (`original-r2`, `remake-r2`, ...).

1. **Recruit amount.** OCR of the dialog's field misread digits (31,400 for 700, 0 for 700, 2,000 for 2,500;
   `probe-recruit-ocr-v1/`). The adapter now computes the clicks: choosing a type sets battalion / 5, and the arrows
   step 100 and 1,000 within the limits. The intent check on the save confirms each amount. Re-run:
   `recruit-ar-min`, `recruit-hc-min`, `recruit-ar-max`, `recruit-lc-max`, `recruit-hc-max`.
2. **Recruit dialog left open** on an adapter error blocked the save (`recruit-hc-min`, `recruit-ar-max`,
   `recruit-hc-max` ended in an error). It is now always closed.
3. **Supply army.** The driver's fixed OK point (239,337) misses the button, now at (223..293, 349..374). The dialog
   stayed open (`buy-arretium-20`, `buy-heraclea-50` errors). The adapter now uses the dialog's own controls.
   `buy-heraclea-50` asked for 50 tons; both games gave 45, the army's need cap (troops / 100 + 1). The intent
   check expects the cap.
4. **Split army.** Each Transfer removes its row, and the new army takes units in transfer order. Moving rows 0
   then 1 moved units 0 and 2; moving them highest first reversed them. Units now go top to bottom, each row
   shifted by those already moved (`split-army-2units`, re-run twice).
5. **Build fleet.** The driver presses the 1s arrows first: 25 ships became 34 (`fleet-25`). The adapter now
   presses the 10s first.
6. **Far moves.** `driver.show()` resets the interface before scrolling to a tile outside the 13 × 13 view. The
   adapter now scrolls through the area map and keeps the selection (`probe-far-move-v1.json`, `-v2.json`). This
   was not the cause of `move-far`, whose target is sea; `move-far-land` (batch 2) checks a far land target.
7. **Comparison of armies and fleets.** The original keeps a removed army's record (owner −1) and re-uses it for
   the next new army, while the remake's export drops it and appends. Live armies and fleets are now compared as
   lists sorted by owner, position and size (`disband-army-0`, `split-then-join`).

## Files

Per case: `<case>/original[-rN]/` and `<case>/remake[-rN]/` with `receipt.jsonl`, `run.json`, the remake's
`commands.txt`. The checkpoint saves `aNNN.SAV` and the remake's native `aNNN.native` stay out of git: SAV hashes
are in `SAVES.sha256`, native hashes in each remake receipt. `scripts/<case>.jsonl` is each case's action script.
`results.txt` is the Markdown table of the run (archived as .txt).
