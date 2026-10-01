# Test results

Last full run: 2026-10-01, `python3 -m tests.test_orders`, build `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`), Wine 9.0, Xvfb 1280×1024. Start save `BASE.SAV` = a new game as Rome with seed 12345 (`AUTO0720.SAV`, SHA-256 `050bc354f1cbbe37…`, 270 BC Spring week 1). Test saves are kept under `$IC2_WORK/tests/` (not in git). All twelve tests pass. The toolbar, army-toolbar, battle-toolbar and dialog-control positions are derived at run time (`harness/driver.py`), because they drift with the Wine build.

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
```

- **move**: the only army record that changes is army 0: position, moves (8 → 4: the river tile (101,36) costs 4) and covered cell (plain 2 → river 8).
- **recruit**: the new slot, the treasury (−320 = 3,200 div 200 × 20) and the mobilization (30 + 1 + 3,200 × 1000 div 2,577,000 = 32) all match the research formulas (`decompiled-recruitment-cost-formula.md`).
- **scripted_turn_repeats** is phase 0's done criterion: one scripted turn (a move plus a recruit, then End turn) reproduces the same save twice.
- **attack**: a siege by army 0 alone on Felsina, over two turns. It fails, as the siege formula predicts (attack 20,720 against defence 34,050), and costs 8.2 % of the army (formula: `troops/(Random(15)+105) × min(15, def×6 div atk)` = ×9 → 7.5–8.6 %).
- **join**: two turns to bring armies 0 and 1 adjacent (the run-0 plan's route), then *Join armies*. The combined army at (103,36) holds 45,700 troops in 12 units, the two armies' exact sum.
- **taxation**: the Change tax level slider runs 0..40 with LineSize 1; Home then Right × 20 sets 20 %.
- **disband_unit / disband_army / split_army / change_units_disband**: the Army recruits and army-toolbar dialogs are read from the running game (`win_controls`), so the clicks do not depend on the font metrics. A confirmation is a Yes/No/Cancel *Confirm* box, answered **Yes** by button — the bottom-centre OK misses it.
- **build_fleet**: 10 ships costs 100 talents and starts a 24-week countdown at a free coastal city.

Earlier failures, fixed in the driver: a menu item click that arrives with the pointer move is ignored; a menu click after a dialog closed can re-open that dialog; file dialogs keep the last name; the first click into an inactive window only activates it; a second End turn click queued during the AI phase ends two turns (the retry now waits 8 s for any sign of the turn starting).
