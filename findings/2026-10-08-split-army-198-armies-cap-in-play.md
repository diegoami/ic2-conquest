# Split army: the 198-army cap in play (row L11, 198 armies)

**Status:** promoted 2026-10-08 into imperial-conquest-2-research at `11157ca` (by ic2-research); this draft is kept for history, the research repo is canonical. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows L11 and UA04, and to `findings/2026-10-05-refusal-texts-and-conditions.md` R01 (which reads the gate from the code and says "nothing happens, no box").

**Tag:** `[confirmed, partial]` for the 198-armies bullet of L11, tested on Split army only (the same helper `FUN_00449f08` also gates Mobilize (R49) and new armies from recruitment; those paths were not run).

## Answer

- The cap counts **every nation's armies together**. It is the game's army count `DAT_004a0324` (memory 0x4A0324, the save's army count at offset 100,956), not a per-nation count.
- `TUnitMap_SplitArmy` (0x0044755C) calls `FUN_00449f08` **before** it opens the dialog (`code_extract_rework_extra.txt` :47046-47048). `FUN_00449f08` creates the new record only when `DAT_004a0324 < 0xc6` (:48725), so the record is taken (count + 1) as soon as the dialog opens.
- **197 armies:** Split army opens its dialog (610×430) and the count goes from 197 to 198 at once.
- **198 armies:** nothing happens. No dialog and no box appear, the count stays at 198 and army 0 keeps its 6 units. The save shows 198 armies.

| Total armies before | Dialog | Count after the click | Result |
|---:|---|---:|---|
| 197 | opens (610×430) | 198 | accepted |
| 198 | none (only the button's 51×15 tooltip) | 198 | refused silently |

Evidence: run-exp-l11-198-armies, `T_SPLIT_198_ARMIES.SAV` (sha256 `af56f25bbfae35f7…`), `probe-197-after-split-click.png`, `probe-198-after-split-click.png` (release `run-exp-l11-198-armies`); `runs/experiments/data/run-exp-l11-198-armies/` (`test_run_1.log`, `test_run_2.log`, `probe.log`, `probe198.py`, `SAVES.sha256`). The tests are `tests/test_orders.py` `split_army_197_armies` and `split_army_198_armies_cap`, and both passed twice.

## Corrections to earlier notes on this side

1. The 2026-10-08 evening handover said "the game clamps Rome's armies to 188 on load". It does not. That save held 200 armies (12 AI + 188 Rome), and the memory table has room for exactly 198 records (0x47C1EC + 656 × 198). Reading the first 198 records gave 12 AI + 186 Rome = 198, and the earlier count of 188 came from that reading, not from a clamp. A save with more than 198 armies overflows the table and is not a valid pre-state.
2. The same handover said "no `controls("Split army")`, the gate fires before the dialog or the click misses". The gate did fire. `Game.open_dialog` also reported the dialog as open, because **Wine's tooltip window for a toolbar button has the button's caption as its window name**. A title match alone is therefore not proof that a dialog opened. The new tests require a window wider than 200 px. Other `open_dialog` calls on toolbar buttons have the same latent false positive, which has not been fixed yet.

## Method

- Pre-state: `_make_patched_save_with_n_armies(BASE, n_rome_target = total − 12)` appends Rome dummy records at (305,130), each with one 3,200-man heavy infantry unit. BASE.SAV (270 BC Spring week 1, Rome human) has 14 armies: 2 Rome and 12 others.
- Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, check `i16(0x4A0324) == total`, select army 0 at (100,37), which has 6 units (the selection is checked through `SEL_ARMY`, so a missed click is ruled out), click Split army on the army toolbar (x 415, y 108) at most twice, then read the count and the windows.

## Not established

- The other callers of `FUN_00449f08` (Mobilize R49, recruitment, AI splits) at 198.
- What a Cancel in the Split army dialog does with the record already taken at 197 (is it freed?).
