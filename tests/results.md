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

**2026-10-04, battles PR C (`experiment/battle-sweep-b5`)**: offline `python3 -m tests.test_driver_battle` 22 (new: `synthetic_block` refuses more units than the grid holds; `end_turn_until_over` behavioural tests with a fake battle whose only sign of progress is the half-round counter: no second click before it moves, a single click and an error when it never moves, and the test fails when the proof comparison is deleted (checked); Log files never reused), `test_battle_stage` 16, `test_battle_trials` 7 (the size-matrix cell syntax added to `test_cells`), `python3 -m tests.test_battle_b5_b8` 6 (the B8 ladder planner and thresholds, the target-rank tabulation, `BB.attribute` on words 8 and 9). Live: 315 sweep battles (`sweep_run.sh`, 52.0 s each, 0 error records), `b8_ladder.py` (15 battles, v2), `b8_layout.py`; `claims_audit.py`: 100 claims, 0 mismatches.

