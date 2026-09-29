# Test results

Last full run: 2026-09-29, `python3 -m tests.test_orders`, build `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`), Wine 9.0, Xvfb 1280×1024. Start save `BASE.SAV` = a new game as Rome with seed 12345 (`AUTO0720.SAV`, SHA-256 `050bc354f1cbbe37…`, 270 BC Spring week 1). Test saves are kept under `$IC2_WORK/tests/` (not in git).

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
PASS move (41s): army 0 (100,37) -> (101,36), moves 8 -> 4, cell 2 -> 8, diff runs 8, popups []
PASS recruit (47s): slot {'slot': 4, 'state': 0, 'type': 'hi', 'troops': 3200, 'city': 85}, treasury 2200 -> 1880 (cost 320), mobilization 30 -> 32, popups []
PASS end_turn (39s): T_BASE.SAV turn 720 -> AUTO0721.SAV turn 721 (Spring week 3, 270 BC); popups []
PASS scripted_turn_repeats (94s): T_SCRIPTED_a_AUTO0721.SAV == T_SCRIPTED_b_AUTO0721.SAV byte for byte (131679 B, seed S 0000012345); Spring week 3, 270 BC; army 0 at (101,36), Rome queue 5 slots
PASS attack (57s): army 0 23700 -> 21765 troops; Felsina owner 6 -> 6, loyalty 79 -> 76, fort 68 -> 65, pop 26 -> 25; news tail [' ', 'Week  3      Spring      270BC', 'Rome fails to capture Felsina   (Gaul).']; popups []
```

- **move**: the only army record that changes is army 0: position, moves (8 → 4: the river tile (101,36) costs 4) and covered cell (plain 2 → river 8).
- **recruit**: the new slot, the treasury (−320 = 3,200 div 200 × 20) and the mobilization (30 + 1 + 3,200 × 1000 div 2,577,000 = 32) all match the research formulas (`decompiled-recruitment-cost-formula.md`).
- **scripted_turn_repeats** is phase 0's done criterion: one scripted turn (a move plus a recruit, then End turn) reproduces the same save twice.
- **attack**: a siege by army 0 alone on Felsina, over two turns. It fails, as the siege formula predicts (attack 20,720 against defence 34,050), and costs 8.2 % of the army (formula: `troops/(Random(15)+105) × min(15, def×6 div atk)` = ×9 → 7.5–8.6 %).

Earlier failures, fixed in the driver: a menu item click that arrives with the pointer move is ignored; a menu click after a dialog closed can re-open that dialog; file dialogs keep the last name; the first click into an inactive window only activates it; a second End turn click queued during the AI phase ends two turns (the retry now waits 8 s for any sign of the turn starting).
