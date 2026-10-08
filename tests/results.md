# Test results

Last full run: 2026-10-01, `python3 -m tests.test_orders`, build `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`), Wine 9.0, Xvfb 1280×1024. Start save `BASE.SAV` = a new game as Rome with seed 12345 (`AUTO0720.SAV`, SHA-256 `050bc354f1cbbe37…`, 270 BC Spring week 1). Test saves are kept under `$IC2_WORK/tests/` (not in git). All seventeen tests of the original suite pass (the first twelve in one full run; the five change-units tests re-run after the driver's OK-retry fix, since the full run was interrupted). The eleven fleet tests (2026-10-02, below) were run separately, so the file documents twenty-eight tests and no single run of all of them. The toolbar, army-toolbar, battle-toolbar and dialog-control positions are derived at run time (`harness/driver.py`), because they drift with the Wine build.

## Seed patch (phase 0)

| Run | Seed | `AUTO0721.SAV` after one End turn from `BASE.SAV` |
|---|---|---|
| a | 12345 | `48857fdd89c22f1260682318dc42083c73967c8dd3a926064a1103734cec1a1e` |
| b | 12345 | `48857fdd89c22f1260682318dc42083c73967c8dd3a926064a1103734cec1a1e` (**identical**) |
| c | 999 | `5dc52eab…9816` (592 bytes differ from a) |
| d | clock | `ee4550c1…62eb` (298 bytes differ from a) |
| e | clock | `61723814…a4bb` (492 bytes differ from d) |

New game, Rome, seed 12345, twice: `NEW_a.SAV` = `NEW_b.SAV` = `BASE.SAV`.

## Order tests

```text
PASS move (40s): army 0 (100,37) -> (101,36), moves 8 -> 4, cell 2 -> 8, diff runs 8, popups []
PASS recruit (47s): slot {'slot': 4, 'state': 0, 'type': 'hi', 'troops': 3200, 'city': 85}, treasury 2200 -> 1880 (cost 320), mobilization 30 -> 32, popups []
PASS end_turn (41s): T_BASE.SAV turn 720 -> AUTO0721.SAV turn 721 (Spring week 3, 270 BC); popups ['@ Celtiberia wants to trade with Rome.']
PASS scripted_turn_repeats (99s): T_SCRIPTED_a_AUTO0721.SAV == T_SCRIPTED_b_AUTO0721.SAV byte for byte (131679 B, seed S 0000012345); Spring week 3, 270 BC; army 0 at (101,36), Rome queue 5 slots
PASS attack (54s): army 0 23700 -> 21765 troops; Felsina owner 6 -> 6, loyalty 79 -> 76, fort 68 -> 65, pop 26 -> 25; news tail [' ', 'Week  3      Spring      270BC', 'Rome fails to capture Felsina   (Gaul).']; popups []
PASS join (59s): armies {0: 23700, 1: 22000} -> army 0 at (103,36), 45700 troops, 12 units; popups []
PASS taxation (33s): Rome tax -> 20%, treasury 2200, unity 821
PASS disband_unit (52s): Rome queue 4 -> 4 (recruit +1, disband -1), treasury 1880
PASS disband_army (36s): Roman armies 2 -> 1, treasury 2300
PASS build_fleet (36s): Rome fleets 0 -> 1 (ships 10, building True, countdown 24); treasury 2200 -> 2100
PASS split_army (36s): Roman armies 2 -> 3 (troops 45700 -> 45700); [(0, 100, 37, 18700), (1, 120, 53, 22000), (14, 101, 38, 5000)]
PASS change_units_disband (39s): army 0 23700 t / 6 units -> 18900 t / 5 units
PASS transfer_units (63s): army0 23700t/6u -> 18700t/5u; army1 22000t/6u -> 27000t/7u
PASS change_units_rename (49s): '1st Foot  Battalion' -> 'Legio Test'
PASS change_units_split (50s): units 6 -> 7; troops [4800, 5000, 5200, 5900, 900, 1900] -> [4800, 3000, 5200, 5900, 900, 1900, 2000]
PASS change_units_join (61s): split then join: units 6 -> 6; troops [4800, 5000, 5200, 5900, 900, 1900]
PASS change_units_refusals (61s): split row 0: '@ this unit is too small to split'; join rows 1+2: 'e these units ate too lage to be combined. ak'; units unchanged [4800, 5000, 5200, 5900, 900, 1900]
```

- **change units**: Rename types into a pre-filled box. Splitting a 5,000 unit opens at 2,500 / 2,500 and each 100s arrow moves 100 to the original (3,000 + 2,000 after five presses); the new unit is appended as the last row. Refusals: the 4,800 unit is "too small to split"; 5,000 + 5,200 heavy infantry are "too large to be combined" (so the join test rejoins the two halves). Saves: `T_RENAME.SAV`, `T_SPLITUNIT.SAV`, `T_JOINUNITS.SAV`, `T_CHUNITS_REFUSED.SAV`. The OK of Change units, Split unit and Rename unit sometimes needs up to three clicks (an inactive window); the driver clicks until the dialog is gone and raises otherwise.
- **move**: the only army record that changes is army 0: position, moves (8 → 4: the river tile (101,36) costs 4) and covered cell (plain 2 → river 8).
- **recruit**: the new slot, the treasury (−320 = 3,200 div 200 × 20) and the mobilization (30 + 1 + 3,200 × 1000 div 2,577,000 = 32) all match the research formulas (`decompiled-recruitment-cost-formula.md`).
- **scripted_turn_repeats** is phase 0's done criterion: one scripted turn (a move plus a recruit, then End turn) reproduces the same save twice.
- **attack**: a siege by army 0 alone on Felsina, over two turns. It fails, as the siege formula predicts (attack 20,720 against defence 34,050), and costs 8.2 % of the army (formula: `troops/(Random(15)+105) × min(15, def×6 div atk)` = ×9 → 7.5–8.6 %).
- **join**: two turns to bring armies 0 and 1 adjacent (the run-0 plan's route), then *Join armies*. The combined army at (103,36) holds 45,700 troops in 12 units, the two armies' exact sum.
- **taxation**: the Change tax level slider runs 0..40 with LineSize 1; Home then Right × 20 sets 20 %.
- **disband_unit / disband_army / split_army / change_units_disband**: the Army recruits and army-toolbar dialogs are read from the running game (`win_controls`), so the clicks do not depend on the font metrics. A confirmation is a Yes/No/Cancel *Confirm* box, answered **Yes** by button — the bottom-centre OK misses it.
- **build_fleet**: 10 ships costs 100 talents and starts a 24-week countdown at a free coastal city.
- **transfer_units**: two turns to put armies 0 and 1 adjacent, then a 5,000-troop unit moves from army 0 to army 1, the total unchanged.
- The field battle is not a unit test: it lives in `runs/experiments/gallic-army/` (see that README). Rome destroys Gaul's army early in all four seeds, and a battle turn is byte-repeatable.

**Fleet orders (2026-10-02, run from the fixtures `saves/fleet-port-antium-0734.SAV` and `fleet-split-antium-0734.SAV`, because a fleet takes 12 turns to build):**

```text
PASS embark_refused (33s): army 0 10700 troops stays at (101,45), fleet 2 20 ships carries -1; box ['The army is too large for this fleet ?']
PASS embark (28s): army 0 (101,45) moves 3 -> aboard at (101,46) moves 0; fleet 2 moves 29 -> 0, carries 0
PASS disembark (43s): army 0 landed at (101,45) moves 0; fleet 2 moves 0, carries -1
PASS supply_fleet (33s): fleet supplies 0 -> 100; Antium 330 -> 230
PASS repair_fleet (35s): condition 97 -> 100, moves 29 -> 0, treasury 1730 -> 1712 (cost 18)
PASS scuttle_fleet (32s): Rome fleets 1 -> 0; box ['Are you sure you want to scuttle this fleet ? Yes No Cancel']
PASS split_fleet (34s): Rome fleets 1 -> 2: [(2, 101, 46, 20, 29), (5, 101, 47, 10, 0)]
PASS join_fleets (31s): Rome fleets 2 -> 1: ship 30, moves 0
PASS transfer_ships (39s): fleet 2: 20 -> 15, fleet 5: 10 -> 15
PASS transfer_ships_back (39s): fleet 2: 20 -> 25, fleet 5: 10 -> 5
PASS move_fleet (28s): fleet 2 (101,46) -> (99,46), moves 29 -> 27; popups []
```

These eleven ran on their own. After the two driver changes they depend on (`Build fleet` now closes its dialog; `answer` accepts a Confirm with OK only) six of the older tests were re-run and pass: `build_fleet`, `disband_unit`, `disband_army`, `change_units_disband`, `attack`, `end_turn`. The other eleven were not re-run, so "Last full run" above is not a run of all twenty-eight. Fleet attack (a naval battle) is not tested: it needs an enemy fleet next to ours.

Earlier failures, fixed in the driver: a menu item click that arrives with the pointer move is ignored; a menu click after a dialog closed can re-open that dialog; file dialogs keep the last name; the first click into an inactive window only activates it; a second End turn click queued during the AI phase ends two turns (the retry now waits 8 s for any sign of the turn starting).

**2026-10-03, T0 of the chatbot plan** (`Game.end_turn(reclick, strict_confirm)`): `python3 -m tests.test_orders end_turn` still passes with the defaults, 40 s, `T_BASE.SAV` turn 720 -> `AUTO0721.SAV` turn 721 (Spring week 3, 270 BC), popups `['@ Celtiberia wants to trade with Rome.']`. The new behaviour is covered offline by `python3 -m tests.test_end_turn_reclick` (scripted game, no live strict run: no unknown Confirm box has been seen).

**2026-10-04, battles PR A (`experiment/battle-sweep`)**: offline, `python3 -m tests.test_driver_battle` (16 at PR A, 18 now with `battle_state` and the never-retry End turn helper: the neutral click point derived off an oversized unit map, `Game.open` with a modal box, `play_battle` with proven End turn clicks and `on_dialog` capture/no/yes/strict on the "Offer of peace" box), `python3 -m tests.test_battle_stage` (10 at PR A, 16 now with the L2 block edits: L1 edits are no-ops when unchanged, each edit local, `state/battle.py` diff incl. the B0 pair when its saves are present), `python3 -m tests.test_battle_trials` (6 at PR A, 7 now with the writers-survive test: the cell table, end_condition from both destroyed flags, dry run against a fake Game, resume, errors recorded and not retried, same-seed compare, `keep` never overwrites). `tests.test_end_turn_reclick` was adapted (its scripted battle now ends at the first End turn click: `play_battle` no longer re-clicks blindly). Live: `python3 -m tests.test_battle_stage live` (the game reads back the edited army 0 and Rome's unity), `python3 -m tests.make_battle_fixtures` (FLD-RG twice byte-identical, `39edecd1…`), `python3 -m tests.test_orders end_turn` still passes (41 s), one live trial `trials.py run hi-hi-one --seeds 1` (55 s).

**2026-10-04, battles PR B (`experiment/battle-sweep-b`)**: offline `python3 -m tests.test_battle_stage` now has 16 cases in all, 6 of them L2 (no-op identical, local edits, army mirroring by (name, type) incl. a defender slot on a real B0 save, bad input incl. grid bounds and header keys, round trip and diff on the real B0 series when present). Live: `python3 runs/experiments/battles/b2_probe.py` (memory = Save As block, 168 of 168 slot-occupancy cells on screen, 3 phases), `b3_crafted.py` (14 crafted resumes), `trials.py run hi-hi-one --seeds 1-3 --reps 4` (12 battles, same-seed runs byte-identical, 53.4 s each).

**2026-10-04, battles PR C (`experiment/battle-sweep-b5`)**: offline `python3 -m tests.test_driver_battle` 22 (new: `synthetic_block` refuses more units than the grid holds; `end_turn_until_over` behavioural tests with a fake battle whose only sign of progress is the half-round counter: no second click before it moves, a single click and an error when it never moves, and the test fails when the proof comparison is deleted (checked); Log files never reused), `test_battle_stage` 16, `test_battle_trials` 7 (the size-matrix cell syntax added to `test_cells`), `python3 -m tests.test_battle_b5_b8` 7 (the B8 ladder planner and thresholds, the target-rank tabulation, `BB.attribute` on words 8 and 9). Live: 315 sweep battles (`sweep_run.sh`, 52.0 s each, 0 error records), `b8_ladder.py` (15 battles, v2), `b8_layout.py`; `claims_audit.py`: 104 claims, 0 mismatches (`claims-audit-20261004-195251.md`).

**2026-10-04, battles B11 (`experiment/battle-hook-b11`, the exchange hook)**: offline `python3 -m tests.test_battle_hook_build` (7 cases: the build refuses a site that is not `E8 rel32` to `Random`, an unhooked 13th call inside the module or TBattleOver, an indirect reference, changed entry or reseed bytes and a branch into displaced bytes; the log reader stops at the write index, reports the overflow flag, and the chain check finds dropped, duplicated, wrong-seed and wrong-site records), `python3 -m tests.test_battle_exchange` (3 hand-computed cases: a melee, a shot and a Rout), `python3 -m tests.test_battle_hook_caves` (needs `unicorn`; 300 random machine states per cave: the `Random` cave, the three marker caves, the two flag-clear caves and the two reseed caves leave every register, EFLAGS, ESP, the stack and all memory below the control block as the unhooked code does; the overflow path, the seed cave and a deliberately broken cave are covered). Output of all of them and of the existing offline battle tests (all exit 0): `runs/experiments/data/run-exp-battle-hook/tests-b11-20261004-211824.txt`. Live: `b11_addresses.py live` (`b11-live-20261004-200346.json`), 322 hooked battles (`inertness-*.json`: all byte-identical to the unhooked ones).

**2026-10-05, battles B16 (`experiment/battle-peace-b16`)**: offline `python3 -m tests.test_driver_battle` 32 (10 new: `answer_battle_peace` with a fake window of button rectangles: Yes presses Yes, No presses No, swapped on-screen buttons still follow the control text, a box that stays open raises after 3 clicks of the same button, a first click that only activates, an absent box and a box without Yes/No raise without clicking, `pre_click` runs before the click, `play_battle(on_dialog="yes")` routes through it, `pre_answer` sees the box before the answer), `python3 -m tests.test_battle_b16` 6 (`strategic`/`rcode` on a synthetic memory snapshot, `ncities` and `owner` edit only their word, `diff_offsets`, `save_diff`), `test_battle_stage` 16. Live: `b16_run.py` (D-LOSS 30 seeds, D-WIN 10, 12 Yes/No pairs of 4 proven End turns, 6 gate cells, 25 hooked lab runs), `b16_audit.py`: 30 claims, 0 mismatches (`b16-claims-audit-*.md`).

**2026-10-05, battles B16 rework (PR #45 review R1-R3)**: `python3 -m tests.test_battle_b16` 12 (new: `PeaceGame` kills only the pid tree it launched (a fake /proc tree with a matching foreign game process on the same display and prefix is never signalled), `start` refuses an occupied display or prefix without launching or killing, no `b16_*` script contains a kill or adopt by pattern, the number-map check fails on an unmapped line, an unchecked number, a failing claim and a stale map entry, the number inventory skips file spans and dates), `test_driver_battle` 32, `test_battle_stage` 16. Offline: `b16_fulldiff.py` (24 runs), `b16_audit.py`: 74 claims, 0 mismatches (6 tables cell by cell, 215 prose tokens checked by claims and 9 exempt with reasons, `b16-number-map-*.md`).

**2026-10-05, battles B16 rework round 2 (PR #45 review)**: `python3 -m tests.test_battle_b16` 19 (new: the audit and `b16_raw` name no analyser output outside `compare_with_analyser`; the skeleton states no unregistered number; the finding equals the rendering of the skeleton from the raw data and an edit of "-18 becomes -14" to "-18 becomes -18", of "10 of 30 seeds" to "11 of 30 seeds" or of a table cell fails; a data folder with a doctored full-diff file and a doctored repeat file leaves every audit value and the rendering unchanged and is reported; `PeaceGame.stop` skips a pid whose start time changed (an owned child recycled by a foreign process with foreign children, a recycled launcher pid with a foreign tree, a swap while the pidfd is opened) and signals nothing foreign). Each new test was shown to fail with its fix reverted (raw code reading the analyser file, finding check always true, literal-number lint disabled, `stop()` trusting remembered pids). `b16_audit.py`: 41 claims, 0 mismatches; `b16_render.py --check`.

**2026-10-05, battles B16 rework round 3 (skeleton lint bypass)**: `python3 -m tests.test_battle_b16` 23 (new: hardcoding `%%box_w%%`/`%%box_h%%` is caught by the lint (also with a stray double percent in front of any 4th line), a pasted table or a table row with a literal number is caught, a stray or unknown double percent is an error (and `render` refuses it), freezing every one of the 295 markers in turn is caught: 0 pass; the lint now removes only valid markers line by line, reads headings and table rows, and rejects literal True/False and the computed text values). With the lint reverted to the greedy whole-skeleton regex the stray-percent, table and freeze-every-marker tests fail; on the old skeleton the old lint missed 15 of 248 numeric single freezes. `b16_audit.py`: 42 claims, 0 mismatches.

**2026-10-05, battles B16 rework round 4 (final Sol review R1-R4)**: `python3 -m tests.test_battle_b16` 27 (new: a parent replaced between its verification and the listing of its children adopts nothing, a child swapped while its pidfd is opened is not adopted, signals name only the processes discovered; swapping `%%rel_yes_t1%%` for `%%rel_yes_ans%%` on skeleton line 17 is caught by the tracked bindings although the regenerated finding, the lint and the freeze sweep accept it; `` `999 * 360` `` in place of the box markers is linted and a registry entry that is not a real file reference is flagged; a suite crash with nonzero exit and empty stdout is a failure). Each fails with its fix reverted. `b16_audit.py`: 45 claims, 0 mismatches (suites checked for exit code and defined test count, skips counted apart).

**2026-10-08, Join-fleets 100-ship boundary regression (`run-exp-join-fleets-cap-in-play`)**: `python3 -m tests.test_orders join_fleets_99 join_fleets_100 join_fleets_101`. Three regression tests on a temp FLEET_SPLIT copy patched by `_make_patched_fleet_split_save(f2, f5)` (layout-independent content scan at the (x, y, owner) signature, +18 ships field). Locks the gate at `< 101` combined ships; the harness docstring was tightened in this commit ("fewer than 100 combined" → "fewer than 101 combined" + a cross-link to findings/2026-10-08-join-fleets-cap-in-play.md). Each test ran in ~31-34 s under Xvfb display :99 with the fast rollingsave seed exe and seed 12345; the patched pre-state is unlinked at the end of the test (no permanent artifact beyond the regression test itself; the run-exp-join-fleets-cap-in-play release keeps the 132-KB pre/post SAVs that produced these numbers live, not the regression's temp files).

```text
PASS join_fleets_99 (31s): 50+49=99 -> ACCEPTED (survivor ships=99, moves=0)
PASS join_fleets_100 (31s): 50+50=100 -> ACCEPTED (survivor ships=100, moves=0)
PASS join_fleets_101 (34s): 50+51=101 -> REFUSED (no merge; [50, 51] preserved)
```

`join_fleets_99` and `join_fleets_100` are the off-by-one cell on the gate (the harness docstring's loose "fewer than 100" is wrong; the live-tested gate is `< 101` matching the decompile `< 0x65`). `join_fleets_101` is the gate's REFUSED side, byte-identical to the pre-state. The three together pin row L11 of `findings/2026-10-05-player-facing-feature-inventory.md` at `[confirmed, partial]`. The other six L11 gate constants (20 units / 100k troops / 40 recruit slots / 500 troops per ship / 198 armies / 100% mob) remain `[derived]` carry-over in the inventory; only the Join-fleets 100-ship gate is promoted.

**2026-10-08, L11 gate regressions + G03 New-nation Yes path (commits `189226a`, `062aa3d`)**:
- `test_embark_over_500_per_ship` (28s) — 18,001 troops / 30-ship fleet 2 in FLEET_PORT, manual `select_army` + `click_tile` (bypassing the dismiss_popups Confirm-auto-Yes path that errors on missing controls). Army 0 stays ashore at (101,45) with troops preserved; fleet 2 ships unchanged. The 500/ship bullet is now `[confirmed, partial]`. The earlier 15,001/30-ship run was accepted at the gate's slack; the 18,001/30-ship run is a clear overage.
- `test_join_armies_over_100k_troops` (32s, prior batch) — 100,001 troops on army 0 joining army 12; gate fires ("These 2 armies combined contain more than 100,000 teops."). The 100,000-troops bullet is now `[confirmed, partial]`.
- `test_recruit_100pct_mobilization` (1920s, prior batch) — Rome mob=100, recruit refused. The 100%-mobilization bullet is now `[confirmed, partial]`.
- `test_new_nation_yes` (WIP, `062aa3d`) — `Game.new_nation()` opens the Game menubar at y=14, clicks the New nation item at y=88, and dismisses the resulting popup via a manual OK click (the harness's `dismiss_popups` Confirm-auto-Yes path errors when the box's win_controls title isn't found). Test still fails on the post-state assertion (current_nation unchanged at 0, Rome's `human` flag still True) — likely a menubar-geometry or New-nation-Yes-path-mismatch issue. The test code is in for further iteration; closes the morning intake's open note *"[code, Yes not run]"* once it actually passes. The 20-units L11 gate is still deferred (the 20-slot army record cap makes "21 units" uncacheable).

**2026-10-08, G03 New-nation Yes path closure**:
- `test_new_nation_yes` (58s) — `Game.new_nation()` rewritten to drive Game menu (y=36 per coverage.md) → New nation item, then `xdotool click --window <wid>` on the Confirm's Yes button (the click goes directly to the window — without `--window` the no-WM Xvfb build misroutes the click). After Yes, the leaders form ('Human and computer leaders') is read by title via `win_controls.exe` (50 controls: 16 TPanel nation rows, 16 TEdit leader-name fields, 16 TCheckbox human ticks, OK and Cancel). The new nation (default Carthage, sorted alphabetically) is ticked by matching `TPanel.text` (space-padded) and clicking the adjacent TCheckbox; then OK is clicked with a 3-iteration retry (first hit may only raise the form). Post-state: `rome.human = False`, `current_nation = 1` (Carthage). The morning intake's open note *"[code, Yes not run]"* is now closed; the `[confirmed]` G03 row is unchanged (it predates the missing-Yes-run note). The earlier `disband_army` flake (the same `controls("Confirm") → no controls found` race this fix dodges) remains to be patched in `dismiss_popups`/`answer` — separate fix.
  ```text
  PASS new_nation_yes (57-58s): G03 Yes: texts = []; rome.human = False; current_nation = 1
  ```

**2026-10-08, L11 40-recruited-units gate regression**:
- `test_recruit_40_slots_cap` (51s) — Patcher `_make_patched_save_full_slots(nation_index=0, city_id=85, n_slots=40)` fills all 40 recruit-slot records at offset 0x2E4 in nation 0's record (each slot is `<4h>` state/type/troops/city). After `fresh_save(pre)`, the test confirms 40 slots at city 85 (Rome), then issues a 41st recruit order at Rome and asserts (a) the slot count stays at 40 (the gate held) and (b) a refusal popup was captured (the OCR text is mangled but contains "40" — `You have reached your lint of 40 units aK`). The 40-recruited-units bullet is now `[confirmed, partial]`. The 20-units-per-army gate stays deferred (uncacheable in 21 units); the 198-armies gate stays queued.
  ```text
  PASS recruit_40_slots_cap (51s): L11 40 slots: 40 in, 40 out (gate held); refusal text = 'e ‘You have reached your lint of 40 units aK'; popups = ['e ‘You have reached your lint of 40 units aK']
  ```

**2026-10-08, L11 198-armies gate (`run-exp-l11-198-armies`)**: `python3 tests/test_orders.py split_army_197_armies split_army_198_armies_cap`. BASE padded to 197 / 198 armies in total (the cap is the game-wide count at 0x4A0324, `< 0xc6` in `FUN_00449f08`, which Split army calls before it opens its dialog). At 197 the dialog opens and the count goes to 198. At 198 there is no dialog and no box, the count stays at 198 and army 0 keeps its 6 units. The dialog is detected by size because the button's tooltip is a Wine window also titled "Split army" (51×15); that tooltip was the earlier session's false "opened". Two runs, both PASS; `split_army` still passes. Finding: `findings/2026-10-08-split-army-198-armies-cap-in-play.md`.
  ```text
  PASS split_army_197_armies (26s): 197 armies: Split army opened, army count 197 -> 198
  PASS split_army_198_armies_cap (36s): 198 armies: Split army REFUSED silently (no dialog), count 198 -> 198; windows ['Area map 328x196', 'Unit map 439x487', 'Information 328x730', 'Split army 51x15']
  ```
