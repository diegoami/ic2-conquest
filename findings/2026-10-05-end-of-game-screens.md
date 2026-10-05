# The End of Game window of a human seat: five reasons, one window, and Abdicate which has none

**Status:** draft finding from `ic2-conquest`, awaiting promotion. For clone task T138 (`imperial_conquest_2` #708/#701; the clone's End of Game window merged as #748). Task `docs/tasks/end-of-game-screens.md`. **Wine-only. Every state that reaches a window is staged** (a save edited in one named field per operation, listed below); nothing here is natural play, except that the staged state is then carried by the game's own turn loop, and the conquest is a real siege click.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-end-of-game/code_extract_end_of_game.v2.txt`, which keeps the dump's line numbers). `[confirmed]` = seen in play: a screenshot of the window, its text read per label by OCR, the same text read from the game's memory, and the autosave (or the memory reading) of the fallen seat's state at that moment. The two are never mixed: a claim carries one tag.

## Answer

1. **There is one window for five reasons** (`THumanFalls`, caption **End of Game**, 450 x 347, one button **OK**) `[confirmed]`. Its first line is always `The game is over for <leader> the leader of <nation>.`; its second line is the reason; then `Your <N> years in power in <nation> produced these changes.` and a two-column start-versus-end table (population, cities, treasury). **Abdicate has no End of Game window**: it asks `Are you sure you want to abdicate ?` (Yes / No / Cancel) and Yes ends the seat at once `[confirmed]`.
2. **Reasons, verbatim `[confirmed]`** (the text is the label caption as held in game memory and as read from the screenshot; the figures are in the windows table below):
   - debt (treasury below -(population div 500) or below -20,000, tested with unity at 400 or more): `Your army have deposed you because they have not been paid.`
   - unity below 400: `Your unpopularity has forced the army to overthrow you.`
   - 250 BC reached: `You have reached the end of your allotted 20 years.`
   - victory (334 cities): `You have conquerred the Mediterranean, a unique achievement.` (staged, two ways)
   - conquered: `Your nation has been conquerred by <nation>.` (a real siege, staged state)
   - The text keeps the original's spellings: `conquerred` twice, `Your army have`.
3. **When two reasons hold, the window shows the first of this order** `[derived]`: victory (cities of 334 or more), then 250 BC, then conquered, then unity below 400, then debt. The turn-start test itself is one OR of five conditions, so it fires once whichever hold. Played: unity and debt together show the unity text (W7); 250 BC and unity together show the 250 BC text (W8); victory and 250 BC together show the victory text (W9) `[confirmed]`. Conquered against the others is `[derived]` only.
4. **After OK the seat is handed to the computer** and its leader name is redrawn (see the end-of-a-fall paragraph); if no human seat is left the game is over: the maps close, the main window is left blank with the caption `Imperial Conquest 2`, File > New / Open / Close stay enabled and every other menu item is grey; **the program keeps running** `[confirmed]`. If another human is left, the game goes on with that human `[confirmed for debt, conquest and Abdicate]`.
5. **Two humans:** one seat's End of Game **hands that seat to the computer and the other human plays on**; the game ends only when the last human has fallen (250 BC: Rome's window, then Gaul's, then the end) `[confirmed]`.

## Method

- **Code.** Read `THumanFalls_InitializeForm` @ 00455E38, `THumanFalls_OK` @ 004564E4, `FUN_00452034` (the checks at the start of a human turn), `TPremierForm_HumanLeaderFalls` @ 0045C238, `TPremierForm_Abdicate` @ 0045B24C, `FUN_00449078`, `FUN_00449050`, `FUN_0044c8f0`, the formatters `FUN_00448e74`, `FUN_00448f18`, and the callers `FUN_00451b40`, `FUN_0044bb18`, `FUN_0044bed8`, `FUN_0044c528`, `TPremierForm_NewGame` (all in the tracked extract). The form's label rectangles come from the form resource (`forms.json` of the feature-inventory data): `param_1[0x6e]` is `lbl_result2`, `[0x6f]` `lbl_result1`, `[0x74]` `lbl_changes`, `[0x7d..0x80]` `lbl_nat1`, `lbl_pop1`, `lbl_cities1`, `lbl_money1`, `[0x81..0x84]` the same four with 2 (the field order of the form's declarations; checked by every text landing in the label it is expected in on the screenshots).
- **Play.** `runs/experiments/end_of_game/run_single.py` (one human) and `run_two.py` (two humans: Rome seat 11 and Gaul seat 14 of the turn order, `SEED.TXT` 12345), on **staged copies** of `saves/run0-start-AUTO0720-seed12345.SAV` (Rome human) and of `EOG_2h_base_AUTO0720.SAV` (a New Game with Rome and Gaul human, seed 12345). Own Xvfb display (:735) and game folder; the normal build `Imperial Conquest 2 fast rollingsave seed.exe`. The staged save is loaded (`Game.load`), every edited field is read back from game memory before anything else, End turn is clicked **once** with proof that it registered (calendar, seat, autosave line or window), the End of Game window is waited for (news boxes closed on the way), then: the window's screenshot, its OCR, the label strings as held in game memory, the fallen seat's fields from memory, the autosave; OK is pressed (located with `Game.controls`, verified by that window's X id disappearing; **in every run but the conquest the first click only activated the window and the second closed it**, logged); and the state afterwards (humans, current seat, windows, caption, process alive) is read. The Abdicate menu is found by OCR of the open dropdown (a new top-level window proves it is open), Save As likewise; no fixed screen point.
- **Reading.** Per-label OCR (`ocr_labels.py`: each label rectangle of the form cut from the screenshot, 4x, tesseract psm 7) and the label captions found in game memory (`ocr_b*.jsonl`, `memory_strings`) agree with the text the code builds, label by label (`claims_audit.py`).
- **Staging.** `eog.edit_save` applies the operations of `runs/experiments/battles/stage.py` (treasury, unity, city fields, city-count word) and a calendar field setter; each operation writes only its own field, no operation leaves the file byte-identical, and every changed byte is checked to lie inside a declared field before the edit is logged (`staging_log.tsv`). One operation, `own_all`, sets the owner of all 334 cities to one nation and empties the other 15 (their city list head, count, unity, capital): used once, for the full-ownership victory.

## What the window writes, label by label (`[derived]`; `[confirmed]` where the windows table has a row)

| label | text the code builds | source |
|---|---|---|
| caption | `End of Game` (form resource) | `forms.json`; the window's title seen by `xdotool` `[confirmed]` |
| `lbl_result1` | `The game is over for ` + leader (+0x0B) + ` the leader of ` + nation (+0x00) + `.` | :56383-56387 |
| `lbl_result2` | the reason, chosen in this order: cities (+0x446, signed) not below 334: victory; else calendar year equals 250: the 250 BC text; else conquered-by (+0x44E) below 0: unity (+0x440) below 400: unpopularity, otherwise debt; else `Your nation has been conquerred by ` + the conqueror's name + `.` | :56390-56415 |
| `lbl_changes` | `Your ` + (`N years ` with N = 270 - year, only when year is below 269; otherwise ` short time `, which gives two spaces after `Your`) + `in power in ` + nation + ` produced these changes.` | :56417-56429 |
| `lbl_nat1` / `lbl_nat2` | nation + ` in 270 BC.` (a fixed text, whatever the start) / nation + ` in ` + year + ` BC.` | :56432-56433, :56454-56458 |
| `lbl_pop1` / `lbl_pop2` | `Population` + the number with thousands commas: start = wealth at start (+0x434), now = wealth (+0x430) | :56436-56437, :56461-56462 |
| `lbl_cities1` / `lbl_cities2` | `Cities   ` (three spaces) + start count (+0x448) / the count word now (+0x446) | :56441-56442, :56466-56467 |
| `lbl_money1` / `lbl_money2` | `Treasury ` + the number + ` talents`: start treasury (+0x43C) / treasury now (+0x438) | :56447-56448, :56472-56473 |

- **Number format.** `FUN_00448e74` (:47544) writes 13 characters: three spaces, then the digits with a comma before each group of three, and a `-` at index 1 for a negative value; `FUN_00448f18` (:47581) cuts the trailing spaces. So a negative treasury reads `Treasury  - 30,000 talents` (a dash, a space), and a positive one has four spaces after `Treasury` `[confirmed]` (memory strings of the windows). "Population" is the **wealth field** (`Σ pop × 3000`, rebuilt each quarter), not a head count.
- **Start values.** The three start fields (+0x434 wealth, +0x43C treasury, +0x448 city count) are **not written by any function of the decompile**: a search of the dump for the three fields (as `+ 0x434`, `DAT_00474aa4`, and the other forms) finds only the reads of `THumanFalls_InitializeForm` `[derived]`. They are part of the nation record that New Game builds and that every save carries. In the two New Game saves they equal the current values for wealth (16 of 16 nations) and the city count (16 of 16, and equal to the length of the city list), and for the treasury in 11 of 16: the other five (Seleucid, Ptolemaic, Macedonia, Galatia, Media) already differ because the AI seats before the human's first turn have played, so the start value was fixed before that (start table) `[confirmed]`. Every window's start triple equals the New Game save's triple of that nation (windows table, column `base save`): the start values are frozen from New Game to the end `[confirmed]`. Whether they are written at New Game or when each nation first plays is not separated by this data.
- **Years in power.** 270 minus the calendar word `DAT_004A0332` (the year BC), printed only below 269: the window shows `20 years` at 250 BC `[confirmed]` and ` short time ` in 270 BC `[confirmed]`; 269 BC also gives `short time` (the test is `< 0x10d`), so `1 years` never appears `[derived]`.
- **The checks.** `FUN_00452034` (run at every human turn start, from `FUN_00451fdc`, and at New Game, :58050) calls `TPremierForm_StartTurn` first, then calls `FUN_0044c8f0(current seat)` when **any** of: year equals 250, cities above 333, unity below 400, treasury below -(wealth div 500), treasury below -20,000 (:55032-55036) `[derived]`. The autosave of the turn is written before the test: the autosave of the turn start holds the state the window then shows `[confirmed]` (windows table, `AUTO` sources). The same function is called by the conquest paths (`FUN_0044bed8`, `FUN_0044c528`, only for a human nation) and by the quarterly update for **computer** nations with a one-in-nine chance (:54900), where, for a computer nation, the routine writes the news line `<nation> depose their leader <leader>.` and applies the same leader, unity and treasury changes `[derived]`.
- **What happens at the end of a human's fall.** `FUN_0044c8f0` for a human nation sets `DAT_004A032C` to the seat and calls `TPremierForm_HumanLeaderFalls`: it shows the window modally, then `FUN_00449078(seat)` (:47777): clears the human flag (+0x490), draws a leader name at random from the nation's 12 and writes it into the leader field (**first draw**, :47790-47791; it may equal the leader shown in the window), and if **no human is left** (`FUN_00449050`, :47753) closes all forms, turns the menus off and sets the caption `Imperial Conquest 2`; else, if the fallen seat is the current one, `HumanLeaderFalls` ends its turn (:59151-59154). Back in `FUN_0044c8f0`: a **second draw** (:50789-50794) that repeats until the name differs from the field's current content, which is the first draw, not the leader the window showed, so the final name can be the original one again (assuming `FUN_00405c08` returns 0 for equal strings, as a Pascal string comparison does); unity = max(unity, min(550, unity + 150)), treasury = 0 if negative else + 1000, relations of -5 to -1 reset (:50796-50816). `THumanFalls_OK` only sets the form's result to 1 and closes it (:56492-56493) `[derived]`.

## Evidence

### The windows (17, all staged; W14-W17 are re-runs)

`source` says where the fallen seat's numbers come from: `AUTO` the autosave written at that turn start, `MEM` the game's memory read while the window was open, `CAPTURE` the saves before and after the siege plus the capture rule (loser's wealth falls by the city's population x 3000 and its count by 1, :50183-50185), checked against the memory reading. Cells are the label texts the window shows, recomputed from those sources in `claims_audit.py` and compared with the per-label OCR of the screenshot and with the label strings in game memory.

<!-- table: windows -->
| id | reason | seat | source | lbl_result2 | lbl_changes | pop start | pop now | cities start | cities now | treasury start | treasury now | screenshot (sha256 prefix) | base save |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| W1 | deposed, debt below -20,000 (treasury staged -30,000) | 0 | `AUTO:EOG_debt_b1_AUTO0721.SAV` | Your army have deposed you because they have not been paid. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | - 30,000 | `EOG_debt_b1_04_window.png` (a589ba017226) | `run0-start-AUTO0720-seed12345.SAV` |
| W2 | deposed, debt below -(wealth div 500) (treasury staged -9,000) | 0 | `AUTO:EOG_debt_wealth_b1_AUTO0721.SAV` | Your army have deposed you because they have not been paid. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | - 9,000 | `EOG_debt_wealth_b1_04_window.png` (98978ec5d56d) | `run0-start-AUTO0720-seed12345.SAV` |
| W3 | deposed, unity below 400 (unity staged 100) | 0 | `AUTO:EOG_unity_b1_AUTO0721.SAV` | Your unpopularity has forced the army to overthrow you. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | 2,200 | `EOG_unity_b1_04_window.png` (f2060eeca978) | `run0-start-AUTO0720-seed12345.SAV` |
| W4 | 250 BC (calendar staged 251 BC Winter week 11) | 0 | `AUTO:EOG_y250_b1_AUTO1200.SAV` | You have reached the end of your allotted 20 years. | Your 20 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_b1_04_window.png` (bc8dd4e9321a) | `run0-start-AUTO0720-seed12345.SAV` |
| W5 | victory, count word staged 334 | 0 | `AUTO:EOG_victory_b1_AUTO0721.SAV` | You have conquerred the Mediterranean, a unique achievement. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 334 | 2,200 | 2,200 | `EOG_victory_b1_04_window.png` (c452c19da661) | `run0-start-AUTO0720-seed12345.SAV` |
| W6 | victory, all 334 cities staged as Rome's | 0 | `AUTO:EOG_victory_full_b7_AUTO0721.SAV` | You have conquerred the Mediterranean, a unique achievement. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 334 | 2,200 | 2,200 | `EOG_victory_full_b7_04_window.png` (c452c19da661) | `run0-start-AUTO0720-seed12345.SAV` |
| W7 | unity below 400 and debt together | 0 | `AUTO:EOG_unity_debt_b1_AUTO0721.SAV` | Your unpopularity has forced the army to overthrow you. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | - 30,000 | `EOG_unity_debt_b1_04_window.png` (92f28d65d26f) | `run0-start-AUTO0720-seed12345.SAV` |
| W8 | 250 BC and unity below 400 together | 0 | `AUTO:EOG_y250_unity_b1_AUTO1200.SAV` | You have reached the end of your allotted 20 years. | Your 20 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_unity_b1_04_window.png` (bc8dd4e9321a) | `run0-start-AUTO0720-seed12345.SAV` |
| W9 | victory and 250 BC together | 0 | `AUTO:EOG_victory_y250_b7_AUTO1200.SAV` | You have conquerred the Mediterranean, a unique achievement. | Your 20 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 334 | 2,200 | 58 | `EOG_victory_y250_b7_04_window.png` (7b552bfb3709) | `run0-start-AUTO0720-seed12345.SAV` |
| W10 | two humans: Gaul deposed, debt (treasury staged -30,000) | 6 | `AUTO:EOG2_debt_gaul_b3_AUTO0720.SAV` | Your army have deposed you because they have not been paid. | Your  short time in power in Gaul produced these changes. | 1,512,000 | 1,512,000 | 28 | 28 | 315 | - 30,000 | `EOG2_debt_gaul_b3_gaul_window.png` (109e23370302) | `EOG_2h_base_AUTO0720.SAV` |
| W11 | two humans: 250 BC, first window (Rome) | 0 | `MEM:states_b5.jsonl#EOG2_y250_both_b5/first_window_open` | You have reached the end of your allotted 20 years. | Your 20 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG2_y250_both_b5_first_window.png` (bc8dd4e9321a) | `EOG_2h_base_AUTO0720.SAV` |
| W12 | two humans: 250 BC, second window (Gaul) | 6 | `AUTO:EOG2_y250_both_b5_AUTO1200.SAV` | You have reached the end of your allotted 20 years. | Your 20 years in power in Gaul produced these changes. | 1,512,000 | 1,587,000 | 28 | 28 | 315 | - 64 | `EOG2_y250_both_b5_second_window.png` (dda73d7c9057) | `EOG_2h_base_AUTO0720.SAV` |
| W13 | two humans: Gaul conquered by Rome (city count word and Felsina staged) | 6 | `CAPTURE:EOG2_conquest_before_siege.SAV+EOG2_conquest_after_gaul_conquered.SAV#city=Felsina#states_b6.jsonl#EOG2_conquest_b6/gaul_window_open` | Your nation has been conquerred by Rome. | Your  short time in power in Gaul produced these changes. | 1,512,000 | 1,497,000 | 28 | 4 | 315 | 315 | `EOG2_conquest_b6_gaul_window.png` (5c4c8aa433c6) | `EOG_2h_base_AUTO0720.SAV` |
| W14 | rerun of W1 with the fixed runners | 0 | `AUTO:EOG_debt_b9_AUTO0721.SAV` | Your army have deposed you because they have not been paid. | Your  short time in power in Rome produced these changes. | 2,577,000 | 2,577,000 | 25 | 25 | 2,200 | - 30,000 | `EOG_debt_b9_04_window.png` (a589ba017226) | `run0-start-AUTO0720-seed12345.SAV` |
| W15 | rerun of W4 with the fixed runners | 0 | `AUTO:EOG_y250_b9_AUTO1200.SAV` | You have reached the end of your allotted 20 years. | Your 20 years in power in Rome produced these changes. | 2,577,000 | 2,601,000 | 25 | 25 | 2,200 | 2,221 | `EOG_y250_b9_04_window.png` (bc8dd4e9321a) | `run0-start-AUTO0720-seed12345.SAV` |
| W16 | rerun of W10 with the fixed runners | 6 | `AUTO:EOG2_debt_gaul_b9_AUTO0720.SAV` | Your army have deposed you because they have not been paid. | Your  short time in power in Gaul produced these changes. | 1,512,000 | 1,512,000 | 28 | 28 | 315 | - 30,000 | `EOG2_debt_gaul_b9_gaul_window.png` (109e23370302) | `EOG_2h_base_AUTO0720.SAV` |
| W17 | rerun of W13 with the fixed runners | 6 | `CAPTURE:EOG2_conquest_before_siege.v2.SAV+EOG2_conquest_after_gaul_conquered.v2.SAV#city=Felsina#states_b9.jsonl#EOG2_conquest_b9/gaul_window_open` | Your nation has been conquerred by Rome. | Your  short time in power in Gaul produced these changes. | 1,512,000 | 1,497,000 | 28 | 4 | 315 | 315 | `EOG2_conquest_b9_gaul_window.png` (5c4c8aa433c6) | `EOG_2h_base_AUTO0720.SAV` |

- Screenshots, saves and autosaves are in release `run-exp-end-of-game` (`batch-b1.tar.gz` ... `batch-b3.tar.gz` and the re-runs in `batch-b5.tar.gz`), hashes in `MANIFEST-*.txt` and `SAVES.sha256`; `fetch_archive.py` prepares `artifacts/` for the audit.
- The window is clipped on screen: the reason label is 394 px wide and Wine's font cuts `Your army have deposed you because they have not been pa` and `You have conquerred the Mediterranean, a unique achievem` (screenshots W1, W5); the memory string is complete `[confirmed]`. Whether the original clips on Windows (a different MS Sans Serif) is not established.
- `Cities` for a conquered nation is the **count word** `+0x446` after the capture's decrement (4), not the number of cities the nation owns (0 after the annexation): Gaul's after save still reads 4 `[confirmed]`.

### After the window

<!-- table: after_state -->
| id | scenario | seat | rule | leader before | leader after | unity before | unity after | treasury before | treasury after | conquered by after | before source | after source |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---|---|
| S1 | W1 debt below -20,000 | 0 | fall | Appius Claudius | Antiochus | 821 | 821 | - 30,000 | 0 | - | `MEM:states_b1.jsonl#EOG_debt_b1/window_open` | `MEM:states_b1.jsonl#EOG_debt_b1/after_ok` |
| S2 | W2 debt below -(wealth div 500) | 0 | fall | Appius Claudius | Antiochus | 821 | 821 | - 9,000 | 0 | - | `MEM:states_b1.jsonl#EOG_debt_wealth_b1/window_open` | `MEM:states_b1.jsonl#EOG_debt_wealth_b1/after_ok` |
| S3 | W3 unity below 400 | 0 | fall | Appius Claudius | Publius Scipio | 100 | 250 | 2,200 | 3,200 | - | `MEM:states_b1.jsonl#EOG_unity_b1/window_open` | `MEM:states_b1.jsonl#EOG_unity_b1/after_ok` |
| S4 | W4 250 BC | 0 | fall | Appius Claudius | Licinus Crassus | 836 | 836 | 2,221 | 3,221 | - | `MEM:states_b1.jsonl#EOG_y250_b1/window_open` | `MEM:states_b1.jsonl#EOG_y250_b1/after_ok` |
| S5 | W5 victory (count word) | 0 | fall | Appius Claudius | Antiochus | 821 | 821 | 2,200 | 3,200 | - | `MEM:states_b1.jsonl#EOG_victory_b1/window_open` | `MEM:states_b1.jsonl#EOG_victory_b1/after_ok` |
| S6 | W6 victory (all cities) | 0 | fall | Appius Claudius | Licinus Crassus | 821 | 821 | 2,200 | 3,200 | - | `MEM:states_b7.jsonl#EOG_victory_full_b7/window_open` | `MEM:states_b7.jsonl#EOG_victory_full_b7/after_ok` |
| S7 | W7 unity and debt | 0 | fall | Appius Claudius | Publius Scipio | 100 | 250 | - 30,000 | 0 | - | `MEM:states_b1.jsonl#EOG_unity_debt_b1/window_open` | `MEM:states_b1.jsonl#EOG_unity_debt_b1/after_ok` |
| S8 | W8 250 BC and unity | 0 | fall | Appius Claudius | Licinus Crassus | 300 | 450 | 2,221 | 3,221 | - | `MEM:states_b1.jsonl#EOG_y250_unity_b1/window_open` | `MEM:states_b1.jsonl#EOG_y250_unity_b1/after_ok` |
| S9 | W9 victory and 250 BC | 0 | fall | Appius Claudius | Licinus Crassus | 836 | 836 | 58 | 1,058 | - | `MEM:states_b7.jsonl#EOG_victory_y250_b7/window_open` | `MEM:states_b7.jsonl#EOG_victory_y250_b7/after_ok` |
| S10 | W10 two humans, Gaul debt | 6 | fall | Hengest | Arminius | 577 | 577 | - 30,000 | 0 | - | `MEM:states_b3.jsonl#EOG2_debt_gaul_b3/gaul_window_open` | `SAVE:EOG2_debt_gaul_after_gaul_falls.SAV` |
| S11 | W12 two humans, 250 BC, Gaul | 6 | fall | Hengest | Brennus | 593 | 593 | - 64 | 0 | - | `MEM:states_b5.jsonl#EOG2_y250_both_b5/second_window_open` | `MEM:states_b5.jsonl#EOG2_y250_both_b5/after_both` |
| S12 | W13 two humans, Gaul conquered | 6 | conquered | Hengest | Horsa | 562 | 0 | 315 | 1,315 | 0 | `MEM:states_b6.jsonl#EOG2_conquest_b6/gaul_window_open` | `SAVE:EOG2_conquest_after_gaul_conquered.SAV` |
| S13 | Abdicate, one human | 0 | abdicate | Appius Claudius | Appius Claudius | 821 | 821 | 2,200 | 2,200 | - | `MEM:states_b2.jsonl#EOG_abdicate_b2/confirm_open` | `MEM:states_b2.jsonl#EOG_abdicate_b2/after_yes_t16` |
| S14 | Abdicate, two humans (Rome) | 0 | abdicate | Appius Claudius | Appius Claudius | 821 | 821 | 2,200 | 2,200 | - | `MEM:states_b3.jsonl#EOG2_abdicate_rome_b3/loaded` | `SAVE:EOG2_abdicate_rome_after.SAV` |

<!-- table: after_game -->
| id | scenario | humans before | humans after | current seat after | windows after | program | year after | before source | after source |
|---|---|---|---|---:|---|---|---:|---|---|
| G1 | debt, one human | [0] | [] | 0 | caption only | keeps running | 270 | `MEM:states_b1.jsonl#EOG_debt_b1/window_open` | `MEM:states_b1.jsonl#EOG_debt_b1/after_ok` |
| G2 | debt by wealth, one human | [0] | [] | 0 | caption only | keeps running | 270 | `MEM:states_b1.jsonl#EOG_debt_wealth_b1/window_open` | `MEM:states_b1.jsonl#EOG_debt_wealth_b1/after_ok` |
| G3 | unity, one human | [0] | [] | 0 | caption only | keeps running | 270 | `MEM:states_b1.jsonl#EOG_unity_b1/window_open` | `MEM:states_b1.jsonl#EOG_unity_b1/after_ok` |
| G4 | 250 BC, one human | [0] | [] | 0 | caption only | keeps running | 250 | `MEM:states_b1.jsonl#EOG_y250_b1/window_open` | `MEM:states_b1.jsonl#EOG_y250_b1/after_ok` |
| G5 | victory (count word), one human | [0] | [] | 0 | caption only | keeps running | 270 | `MEM:states_b1.jsonl#EOG_victory_b1/window_open` | `MEM:states_b1.jsonl#EOG_victory_b1/after_ok` |
| G6 | victory (all cities), one human | [0] | [] | 0 | caption only | keeps running | 270 | `MEM:states_b7.jsonl#EOG_victory_full_b7/window_open` | `MEM:states_b7.jsonl#EOG_victory_full_b7/after_ok` |
| G7 | Abdicate Yes, one human | [0] | [] | 0 | caption only | keeps running | 270 | `MEM:states_b2.jsonl#EOG_abdicate_b2/confirm_open` | `MEM:states_b2.jsonl#EOG_abdicate_b2/after_yes_t16` |
| G8 | debt of Gaul, two humans | [0, 6] | [0] | 0 | game windows | keeps running | 270 | `MEM:states_b3.jsonl#EOG2_debt_gaul_b3/gaul_window_open` | `MEM:states_b3.jsonl#EOG2_debt_gaul_b3/after_ok_rome_turn` |
| G9 | Rome abdicates, two humans | [0, 6] | [6] | 6 | game windows | keeps running | 270 | `MEM:states_b3.jsonl#EOG2_abdicate_rome_b3/loaded` | `MEM:states_b3.jsonl#EOG2_abdicate_rome_b3/after_yes_gaul_turn` |
| G10 | 250 BC for both, two humans | [0, 6] | [] | 6 | caption only | keeps running | 250 | `MEM:states_b5.jsonl#EOG2_y250_both_b5/first_window_open` | `MEM:states_b5.jsonl#EOG2_y250_both_b5/after_both` |
| G11 | Gaul conquered by Rome, two humans | [0, 6] | [0] | 0 | game windows | keeps running | 270 | `MEM:states_b6.jsonl#EOG2_conquest_b6/gaul_window_open` | `MEM:states_b6.jsonl#EOG2_conquest_b6/after_ok` |

- **One human, any reason:** the human flag goes to 0, the leader name is redrawn (observed: it changed in every fall, S1-S12, but the code does not guarantee a change), `FUN_0044c8f0`'s unity and treasury rules apply (S1-S9), the maps close within about 8 s, the main window stays with the caption `Imperial Conquest 2` and the toolbar's Open button only; File shows New, Open and Close enabled and Save and Save As grey; Game (End turn, New player, New nation, Abdicate), Strategy and Nations items are all grey; no further window; the program keeps running (G1-G7; screenshots `EOGM_unity_b8_menu_*.png`) `[confirmed]`.
- **Abdicate** (G7, S13): `Game > Abdicate` opens the Confirm box `Are you sure you want to abdicate ?` with Yes, No, Cancel; Yes clears the flag at once (the memory reading 2 s later) and **no End of Game window opens**; unity and treasury are untouched and the leader's name did not change in these runs (the code draws a new name from the nation's 12 and does not forbid the same one; the seed is the same in every run) `[confirmed]`. With a second human (G9, S14) the turn is ended by the game and the second human's turn starts.
- **Two humans** (G8-G11): the fall hands the seat over and the game goes on with the other human (debt: Gaul falls at the start of its turn, then Rome's turn 0721 starts; conquest: Gaul's window opens during Rome's own turn, the current seat stays Rome after OK); 250 BC gives Rome's window, then Gaul's, then the game is over (G10) `[confirmed]`. The save after Gaul's fall (`EOG2_debt_gaul_after_gaul_falls.SAV`) has Gaul's human flag at 0 and Rome's at 1; the save after Rome's abdication (`EOG2_abdicate_rome_after.SAV`) has Rome 0 and Gaul 1.
- **Conquest** (S12): Rome's army 0 besieged Felsina in Rome's own turn (a real siege click, Gaul human; `EOG2_conquest_adjacent.SAV` before, `EOG2_conquest_after_gaul_conquered.SAV` after): all 28 cities in Gaul's list went to Rome (53 owned), Gaul's unity is 0 and its treasury 1,315, conquered-by 0 `[confirmed]`.

### Re-run with the fixed runners (review round 1)

The runners were reworked after review (every confirmation click is bounded and verified per window id; Save As is proven to be a file dialog before the name is typed). W1, W4, W10 and W13 were re-run from scratch as W14-W17 (batch `b9`, new files beside the old ones). The window screenshots are **byte-identical** to the first runs, and the complete `lbl_changes` caption was read from game memory this time, so the spacing `Your  short time in power in ...` (two spaces) and `Your 20 years in power in ...` are `[confirmed]` from memory for W14-W17 (the audit compares the finding's cell with that string exactly). For W1-W13 the spacing of the prefix is `[confirmed]` on the screenshot only (the memory string of those runs holds the suffix `in power in ...`), plus `[derived]` from the code.

<!-- table: rerun -->
| id | first run | re-run | screenshot sha256 prefix | memory has the complete caption |
|---|---|---|---|---|
| W14 | EOG_debt_b1_04_window.png | EOG_debt_b9_04_window.png | a589ba017226 | yes |
| W15 | EOG_y250_b1_04_window.png | EOG_y250_b9_04_window.png | bc8dd4e9321a | yes |
| W16 | EOG2_debt_gaul_b3_gaul_window.png | EOG2_debt_gaul_b9_gaul_window.png | 109e23370302 | yes |
| W17 | EOG2_conquest_b6_gaul_window.png | EOG2_conquest_b9_gaul_window.png | 5c4c8aa433c6 | yes |

### What was staged (every window)

<!-- table: staging -->
| staged input | source save | operation | old | new | changed bytes |
|---|---|---|---:|---:|---:|
| EOG_debt_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | treasury[0] | 2200 | -30000 | 4 |
| EOG_debt_wealth_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | treasury[0] | 2200 | -9000 | 4 |
| EOG_unity_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | unity[0] | 821 | 100 | 2 |
| EOG_y250_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.year | 270 | 251 | 4 |
| EOG_y250_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.season | 0 | 3 | 4 |
| EOG_y250_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.week | 1 | 11 | 4 |
| EOG_victory_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | ncities[0] | 25 | 334 | 2 |
| EOG_unity_debt_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | unity[0] | 821 | 100 | 6 |
| EOG_unity_debt_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | treasury[0] | 2200 | -30000 | 6 |
| EOG_y250_unity_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.year | 270 | 251 | 6 |
| EOG_y250_unity_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.season | 0 | 3 | 6 |
| EOG_y250_unity_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.week | 1 | 11 | 6 |
| EOG_y250_unity_b1_staged.SAV | run0-start-AUTO0720-seed12345.SAV | unity[0] | 821 | 100 | 6 |
| EOG_abdicate_b2_staged.v2.SAV | run0-start-AUTO0720-seed12345.SAV | (no operation: byte-identical copy) | - | - | 0 |
| EOG2_debt_gaul_b3_staged.SAV | EOG_2h_base_AUTO0720.SAV | treasury[6] | 315 | -30000 | 4 |
| EOG2_abdicate_rome_b3_staged.SAV | EOG_2h_base_AUTO0720.SAV | (no operation: byte-identical copy) | - | - | 0 |
| EOG2_y250_both_b5_staged.SAV | EOG_2h_base_AUTO0720.SAV | calendar.year | 270 | 251 | 4 |
| EOG2_y250_both_b5_staged.SAV | EOG_2h_base_AUTO0720.SAV | calendar.season | 0 | 3 | 4 |
| EOG2_y250_both_b5_staged.SAV | EOG_2h_base_AUTO0720.SAV | calendar.week | 1 | 11 | 4 |
| EOG2_conquest_b6_staged.SAV | EOG_2h_base_AUTO0720.SAV | ncities[6] | 28 | 5 | 4 |
| EOG2_conquest_b6_staged.SAV | EOG_2h_base_AUTO0720.SAV | city[79].loyalty | 79 | 1 | 4 |
| EOG2_conquest_b6_staged.SAV | EOG_2h_base_AUTO0720.SAV | city[79].fort | 68 | 0 | 4 |
| EOG2_conquest_b6_staged.SAV | EOG_2h_base_AUTO0720.SAV | city[79].pop | 26 | 1 | 4 |
| EOG_victory_full_b7_staged.SAV | run0-start-AUTO0720-seed12345.SAV | own_all[0] | - | - | 1058 |
| EOG_victory_y250_b7_staged.SAV | run0-start-AUTO0720-seed12345.SAV | ncities[0] | 25 | 334 | 6 |
| EOG_victory_y250_b7_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.year | 270 | 251 | 6 |
| EOG_victory_y250_b7_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.season | 0 | 3 | 6 |
| EOG_victory_y250_b7_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.week | 1 | 11 | 6 |
| EOGM_unity_b8_staged.SAV | run0-start-AUTO0720-seed12345.SAV | unity[0] | 821 | 100 | 2 |
| EOG2_debt_gaul_b9_staged.SAV | EOG_2h_base_AUTO0720.SAV | treasury[6] | 315 | -30000 | 4 |
| EOG_debt_b9_staged.SAV | run0-start-AUTO0720-seed12345.SAV | treasury[0] | 2200 | -30000 | 4 |
| EOG_y250_b9_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.year | 270 | 251 | 4 |
| EOG_y250_b9_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.season | 0 | 3 | 4 |
| EOG_y250_b9_staged.SAV | run0-start-AUTO0720-seed12345.SAV | calendar.week | 1 | 11 | 4 |
| EOG_abdicate_b9_staged.SAV | run0-start-AUTO0720-seed12345.SAV | (no operation: byte-identical copy) | - | - | 0 |
| EOG2_conquest_b9_staged.SAV | EOG_2h_base_AUTO0720.SAV | ncities[6] | 28 | 5 | 4 |
| EOG2_conquest_b9_staged.SAV | EOG_2h_base_AUTO0720.SAV | city[79].loyalty | 79 | 1 | 4 |
| EOG2_conquest_b9_staged.SAV | EOG_2h_base_AUTO0720.SAV | city[79].fort | 68 | 0 | 4 |
| EOG2_conquest_b9_staged.SAV | EOG_2h_base_AUTO0720.SAV | city[79].pop | 26 | 1 | 4 |
| EOG2_abdicate_rome_b9_staged.SAV | EOG_2h_base_AUTO0720.SAV | (no operation: byte-identical copy) | - | - | 0 |

Staged inputs: one field per operation; "changed bytes" is the total for the file. The conquest staging sets Gaul's city-count word to 5 (the capture of Felsina then leaves it below 6, :50213, so `FUN_0044c528` annexes the rest) and Felsina's loyalty 1, fortification 0, population 1 so that army 0 alone takes it; the city list of Gaul is untouched. `own_all[0]`: every city's owner is Rome, Rome's list holds all 334 cities, the other 15 nations have an empty list, 0 cities, unity 0 and no capital (W6); the game ran a full round of 15 computer seats on that state without a fault, which is all that is claimed.

### Start values (recorded before the first human turn, frozen after)

<!-- table: start -->
| save | pop equal | treasury equal | cities equal | count = list |
|---|---:|---:|---:|---:|
| run0-start-AUTO0720-seed12345.SAV | 16 | 11 | 16 | 16 |
| EOG_2h_base_AUTO0720.SAV | 16 | 11 | 16 | 16 |

### Code citations (the quote is on the cited line of the extract)

<!-- table: code -->
| claim | line | quote |
|---|---:|---|
| the first label's text | 56383 | The game is over for |
| victory test: cities below 334 is the ordinary branch | 56390 | < 0x14e |
| 250 BC test in the window | 56391 | DAT_004a0332 == 0xfa |
| not conquered: conquered-by below 0 | 56395 | < 0) |
| unity below 400 gives the unpopularity text | 56396 | < 400 |
| conquered text | 56406 | Your nation has been conquerred by |
| victory text | 56415 | You have conquerred the Mediterranean, a unique achievement. |
| years in power only below 269 | 56418 | < 0x10d |
| years in power = 270 - year | 56419 | 0x10e - |
| the left column's title is fixed | 56433 | in 270 BC. |
| left population is the start field (+0x434) | 56437 | 0x474aa4 |
| left cities is the start field (+0x448) | 56442 | 0x474ab8 |
| left treasury is the start field (+0x43C) | 56448 | 0x474aac |
| right population is the current wealth (+0x430), unpadded formatter | 56462 | FUN_00448e74 |
| right cities is the count word (+0x446) | 56467 | 0x24a |
| right treasury is the treasury (+0x438) | 56473 | FUN_00448f18 |
| OK sets the result and closes | 56492 | param_1[0x4a] = 1 |
| the autosave-time check calls the fall routine | 55036 | FUN_0044c8f0(DAT_004a0320) |
| turn start runs before the test | 55031 | TPremierForm_StartTurn |
| debt limit: wealth div -500 | 55034 | / -500 |
| debt limit: -20,000 | 55035 | < -20000 |
| HumanLeaderFalls shows the window then hands the seat over | 59150 | FUN_00449078(DAT_004a032c) |
| the current seat's turn is ended when it is the fallen one | 59151 | DAT_004a0320 == DAT_004a032c |
| the seat's human flag is cleared | 47789 | = 0; |
| the first draw of a leader name from the nation's 12 names | 47790 | FUN_0040284c(0xc) |
| the first draw is written into the leader field | 47791 | FUN_00405b00(&DAT_0047467b |
| the second draw repeats while the name equals the field (the first draw) | 50793 | while (iVar4 == 0) |
| no human left: forms closed | 47794 | TPremierForm_CloseAllForms |
| no human left: caption reset | 47797 | Imperial Conquest 2 |
| unity rule: 550 cap, +150 | 50798 | 0x226 |
| treasury rule: negative becomes 0 | 50802 | = 0; |
| treasury rule: otherwise +1000 | 50805 | + 1000 |
| the human branch of the fall routine | 50787 | TPremierForm_HumanLeaderFalls |
| conquest when the loser's count is below 6 | 50213 | < 6 |
| capture decrements the loser's count | 50185 | + -1 |
| capture removes the city's wealth from the loser | 50184 | * -3000 |
| the year counter decrements at the new year | 54674 | DAT_004a0332 + -1 |
| AI nations call the fall routine at the quarter | 54900 | FUN_0044c8f0(sVar12) |
| the conquest path tests the conqueror's count for victory | 50753 | 0x14d < |
| New Game also runs the turn-start checks | 58050 | FUN_00452034() |
| Abdicate's confirmation text | 58425 | Are you sure you want to abdicate ? |
| Abdicate Yes calls the hand-over only | 58428 | FUN_00449078(DAT_004a0320) |
| Abdicate ends the turn when a human is left | 58431 | TPremierForm_EndTurn |

## The clone's window against the original

The clone's repository is not in this environment, so this table lists what the original does; "check" is what a reviewer of the clone has to verify. Differences are bugs for the clone by the task's rule.

| item | original | check in the clone |
|---|---|---|
| caption, size, buttons | `End of Game`, 450 x 347, one OK button | same title and a single OK |
| first line | `The game is over for <leader> the leader of <nation>.` with the leader the seat had when it fell (the replacement comes after OK) | the old leader's name |
| spellings | `conquerred` (twice), `Your army have` | kept, not corrected |
| years in power | `N years` with N = 270 - year only from year 268 down; otherwise ` short time ` (two spaces after `Your`) | 20 at 250 BC; the short-time text in 270 and 269 BC; never `1 years` |
| left column title | always `<nation> in 270 BC.` | not the real start year |
| right column title | `<nation> in <year> BC.` | the calendar year at the window |
| table rows | `Population`, `Cities`, `Treasury ... talents`; population is the wealth field | not a head count |
| number format | thousands commas; negative as `- 30,000` | same |
| cities now after a conquest | the count word after the capture's decrement (4 in W13), not the number owned | same quirk or a recorded decision |
| reasons and order | victory, 250 BC, conquered, unity below 400, debt (one text) | one text; the order |
| Abdicate | a Confirm box, **no End of Game window** | none shown |
| after OK, no human left | maps close, blank main window, File > New / Open / Close usable, everything else grey, no exit | same state |
| after OK, another human | seat handed to the computer, game continues with the other human | same |
| leader names | two draws from the nation's 12 in a fall (the second differs from the first only), one draw on Abdicate; the observed names are in the after_state table; unity max(u, min(550, u + 150)), treasury 0 if negative else + 1000 (not for Abdicate) | same |
| victory by an AI nation | `[derived]` the conquest path ends with a test of the conqueror's count above 333 and then the same window for that nation, with no test that it is human (:50753-50755) | check |

## What this does not establish

- **Wine only**, one build, one seed (12345), Rome and Gaul. The clipped labels may differ with the Windows font.
- **Every state is staged.** Natural play never reached a window: a debt below -20,000, unity below 400, 250 BC (calendar edited to 251 BC Winter week 11, then one End turn), 334 cities (the count word alone for W5, all cities for W6), and the conquest (Gaul's count word and Felsina's fields edited, the siege and the capture are real). The windows show what the game does with those states, not how often they arise. The conquered nation's table is for a staged count; a natural conquest has the count at 5 or fewer and the list the same length.
- **Not played:** 269 BC `short time`/years between 2 and 19 (only 20 and `short time` seen), the capture path to 334 cities, a window for an AI conqueror, the New Game check, a fall at a seat that is not the current one by the quarterly path for a human (only through the human turn-start check and the two conquest paths), the defection-elimination path (`FUN_0044bed8`), and a fall with three or more humans.
- **Where the start values are first written** (New Game or each nation's first move) is not separated; they are frozen from before the first human turn.
- **The leader name after Abdicate** was unchanged in every run: the code redraws, so a different seed may change it.
- The OCR is a reading aid: the claims audit compares the per-label OCR with the code's text and the game's memory strings and tolerates only the clipped reason label.

## Review round 1 (what changed)

- The audit's label texts, thresholds and formatter constants are now **read from the code extract under `--data`** (`fmt.Code`); the finding's label cells are compared **exactly** (OCR is normalised, nothing else); tests alter an extract literal and thresholds, and the double space of the short-time line, and each must fail the audit.
- The leader's name is described as two draws (observed names are not a guarantee).
- Confirmation loops (End turn ?, siege Confirm, Abdicate Confirm, information boxes) track the dialog's X id, verify it is gone after each click and stop after 3 attempts in all; Save As is proven to be a file dialog before the name is typed.
- Re-runs W14-W17 (batch `b9`, release archive `batch-b5.tar.gz`) reproduce W1, W4, W10 and W13 byte for byte.
- Final audit: 1700 checks, 0 mismatches; `test_claims_audit.py`: 23 of 23 pass.

## Reproduction

```text
python3 runs/experiments/end_of_game/extract_code.py end_of_game 00455e38 ...   # the tracked code extract
python3 runs/experiments/end_of_game/run_single.py debt b1 ...                 # one-human scenarios (own display :735, game folder ~/ic2-work-eog)
python3 runs/experiments/end_of_game/run_two.py conquest b6                     # two-human scenarios
python3 runs/experiments/end_of_game/ocr_labels.py                              # per-label OCR of every captured window
python3 runs/experiments/end_of_game/fetch_archive.py                           # artifacts from the release
python3 runs/experiments/end_of_game/claims_audit.py                            # the audit; test_claims_audit.py shows a doctored save and claim fail it
```

<!-- table: counts -->
| item | value |
|---|---:|
| windows captured (rows of the windows table) | 17 |
| screenshots read per label | 17 |
| distinct reasons that produced a window | 5 |
| staged inputs (rows of the staging table, distinct files) | 21 |
| two-human scenarios (rows of after_game with two humans before) | 4 |
