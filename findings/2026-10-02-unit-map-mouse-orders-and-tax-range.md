# The Unit map's mouse orders (select, move, attack prompt, Shift+X, split position) and the Taxation range, measured live

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It answers the questions (a)–(e) and (g) relayed from the `imperial_conquest_2` main session for the clone's click-army-then-target model (bug #555 depends on (e); task T103 on (g)). **(f) (embark and unload by click) was not run.**

**Answer.**
- **(a)** With an army selected, a left-click on a reachable tile moves it at once; the army **stays selected while it has moves left** and is **deselected when its moves reach 0**.
- **(b)** Clicking an adjacent enemy **city** with the army selected: **at war, no prompt**, the siege resolves on the click. **At peace, a Yes/No/Cancel box "Are you sure you want to attack this city?"**; **No** changes nothing (relation, position, moves, selection all unchanged); **Yes writes war** (relation 0 → 3, news "ROME DECLARES WAR ON GREECE.") and the siege follows on the same click. An adjacent army was not tried.
- **(c)** A left-click on the own army selects it and the Information panel shows its details; a right-click on it replaces the panel with the unit list. Neither opens a window.
- **(d)** Shift+X drops the selection (selected army index 0 → −1); nothing else changes.
- **(e)** Split army puts the new army on an **adjacent tile (one step diagonally)**, not on the same tile.
- **(g)** The Taxation slider runs **0 to 40**, one step per arrow key, **5 per Page key**; 40 is the control's real maximum, not the driver's assumption. OK writes the value to nation `+0x44A`.

## Method

- **Build and seed:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb 1280×1024, `SEED.TXT` = 12345, every scenario from a fresh process and the run-0 start save (`run0-start-AUTO0720-seed12345.SAV` = `BASE.SAV`: Rome, 270 BC Spring week 1, army 0 at (100,37) with 23,700 troops and 8 moves). Relations (nation `+0x26`): Rome–Gaul 3 (war), Rome–Greece 0 (peace).
- **Driver:** `harness/driver.py` clicks and keys through `xdotool`; the selected army is read from the game's memory (`0x4A0328`, −1 = none), armies, moves and relations from memory and from the saves. The scripts are `runs/experiments/unit-map-mouse/` (`a_c_d_e.py`, `b2_attack_prompt.py`, `g_taxation.py`); the saves and screenshots are staged in the gitignored `artifacts/run-exp-unitmap-mouse/` until the release `run-exp-unitmap-mouse` is created (CLAUDE.md rule 1).
- **(g)** needed a new helper, `harness/win_slider.c` (`win_slider.exe`), which asks a trackbar for its own range and steps (`TBM_GETRANGEMIN/MAX`, `GETPOS`, `GETLINESIZE`, `GETPAGESIZE`) instead of inferring them from keys.
- **(b)** went to a planner path (`planner/path.py`) one tile per click, ending a turn next to the city so the click is made with a full turn's moves (9). The box is **captured, not auto-answered** (`Game.attack` answers Yes), then answered No, the click is repeated, and answered Yes.

## Observations

**(a) Select and move** (`a_c_d_e.py`; the state is read from the game's memory after each click, with **no save between the clicks** (a save sets the selected-army variable to −1, see Pitfalls); `A_AFTER_CLICKS.SAV` is saved once after both; `A_1_selected.png`, `A_2_after_moves.png`).

| Step | Selected army | Army 0 | Moves |
|---|---|---|---|
| start (`BASE.SAV`) | −1 | (100,37) | 8 |
| click on the army | 0 | (100,37) | 8 |
| click on (101,36) | **0** | (101,36) | **4** |
| click on (102,36) | **−1** | (102,36) | **0** |

No box appeared for either move.

**(b) Attack prompt** (`b2_attack_prompt.py`; `B2_WAR_FELSINA_*`, `B2_PEACE_GENUA_*`, screenshots `B2_*_click1.png`, `B2_PEACE_GENUA_click2.png`).

| | Felsina (Gaul), at war | Genua (Greece), at peace |
|---|---|---|
| relation before | 3 | 0 |
| army before the click | (97,32), 9 moves, 23,700 troops | (90,30), 9 moves, 23,700 troops |
| box after the click | **none** | **Confirm: "Are you sure you want to attack this city?"**, buttons Cancel, &No, &Yes |
| after **No** | – | relation 0, army (90,30), moves 9, **still selected** (read from memory right after the click on No, `b2_attack_prompt.py`, `b2_attack_prompt.json`; the save `B2_PEACE_GENUA_AFTER_NO.SAV` is written afterwards and by itself would read −1) |
| after the second click and **Yes** | – | box again; relation **3**; news "ROME DECLARES WAR ON GREECE." |
| result | no box; siege: troops 21,846 (−1,854), moves 0, Felsina loyalty 79→76, fort 68→65, pop 26→25; "Rome fails to capture Felsina (Gaul)." | siege: troops 22,036 (−1,664), moves 0, Genua loyalty 69→66, fort 58→56, pop 30→29; "Rome fails to capture Genua (Greece)." |
| tactical battle screen | none (a city is a siege) | none |

**(c) Click on a unit** (`C_1_left_click.png`, `C_2_right_click.png`, `C_AFTER_RIGHT_CLICK.SAV`). Selected army 0 after the left-click, and it stays 0 after the right-click on the same tile. The Information panel after the left-click reads "Army of Rome, Moves 8, Supply 170 tons (71%), Morale very high, Money 100 talents, Terrain Plain", then the troops per type (Light infantry 4,800, Heavy infantry 16,100, Archers 0, Light cavalry 900, Heavy cavalry 1,900), Total troops 23,700, No. of units 6, Regulars cost 232 talents per quarter, Mercenary pay 0. After the right-click the same panel lists the six units one per line (name, type, troops, quality: "1st Foot Battalion, Light infantry, 4,800, average" …). No new window opened (the window list is unchanged).

**(d) Shift+X** (`D_1_selected.png`, `D_2_after_shift_x.png`, `D_AFTER_SHIFT_X.SAV`): selected army 0 before, **−1** after; army 0 stays (100,37) with 8 moves; the army toolbar strip empties and the selection diamond on the map tile disappears, **but the Information panel still shows the army's details** (it is not cleared by Shift+X).

**(e) Split army** (`E_AFTER_SPLIT.SAV`, driver `split_army(0, unit_rows=(0,))`): before, Rome has armies 0 (100,37) and 1 (120,53). After, army 0 (100,37) 18,700 troops, army 1 unchanged, and the **new army 14 at (101,38)** with 5,000: one step diagonally (+1,+1), distance 1. `tests/test_orders.py::split_army` (`T_SPLIT.SAV`) gives the same positions.

**(g) Taxation** (`g_taxation.py`; `G_TAX_MIN.SAV`, `G_TAX_MAX.SAV`; `tax_open.png`, `tax_home.png`, `tax_end.png`). The slider (class `TTrackBar`) reports **min 0, max 40, line size 1, page size 5**. Keys, each read from the control: Home → 0; Right → +1; Left → −1; End → 40; Page Down (`Next`) → +5 and **clamped at 40** (39 → 40); Page Up (`Prior`) → −5 (40 → 35); Page Up at 0 stays 0; Right at 40 stays 40. The dialog (title "Change tax level") shows Current tax and income, New tax and income, and the slider; at Home/End it showed New tax 40 with New income 1,011 against Current tax 10 with income 252. OK with the slider at Home wrote **nation `+0x44A` = 0** (`G_TAX_MIN.SAV`, tax 0), at End **40** (`G_TAX_MAX.SAV`, tax 40); both saves are turn 720, treasury 2,200 (no turn ended). The slider opened at 15 although the tax was 10, because the driver's focusing click lands on the track and pages it by 5; that is the driver's click, not the dialog's opening position.

**Also seen** (`X_end_turn_supplies_prompt.png`): when an army needs supplies, End turn opens an **"End turn ?"** box, "An army of yours needs supplies. If you have not finished your turn click MAKE MORE MOVES. If you are finished moving click END TURN.", with buttons End turn and Make more moves. The driver now answers it (`harness/driver.py`, `end_turn`).

## Inferences

- The prompt belongs to **non-war targets**: it appeared at peace and not at war, and Yes is what writes the war (relation 0 → 3, the news line), in line with `rules-digest.md` §Attack confirmation. The clone can treat "target nation not at war with the actor" as the trigger and "Yes declares war, then resolves the attack" as the sequence; a No leaves the order unissued and the army selected.
- A click on the own army selects it and only a selected army can issue move or attack orders; the selection ends when moves reach 0 or on Shift+X (so the clone's selection state is: none, or one army with moves > 0).
- For bug #555: the new army from Split army sits at distance 1, so Join armies and Army to army transfer have their partner in reach right after a split. Whether the game picks the tile by a rule (first free neighbour in some order, terrain, owner) is not established; the one observation is (+1,+1).
- The Taxation range for the clone's set-tax command (T103) is the integers 0–40 with a keyboard step of 1 and a page step of 5.

## What this does not establish

- **(f)**: embark by clicking an adjacent own fleet and unload by clicking an adjacent land tile were **not run** (a fleet needs 12 turns to launch; the run was cut short). Nothing here says anything about fleets.
- **(b)** was observed on a **city** only. An adjacent enemy army or fleet was not clicked, and so the Yes path's tactical battle was not seen; the siege path was. The prompt text in the saved OCR is garbled ("(7) ‘Ate you sure"); the wording above is from the screenshot, not the decompiled string.
- **(a)** was one army, one seed, two clicks; the click on a tile it cannot afford (partial walk, blocked path) was not tried, nor a click on sea (fleet move). The selection rule "stays selected while moves remain" is one case (moves 4 left).
- **(c)** was an own, selected army. A left- or right-click on an **unselected** own army, on an enemy army, or on a city was not tried (a click on a city with nothing selected only showed the city in the Information panel, by accident, in an early attempt).
- **(e)** is one split, one seed; whether the new army's tile depends on terrain or occupancy is unknown. **(g)**: whether the slider's *opening* position equals the current tax was not measured cleanly (the driver's click moves it).
- **Wine-only.** Window layout, key handling and the selection reset below are what this Wine build does; the original's source of truth is the decompiled code (`TUnitMap_SelectUnit`, `CheckForMove`).

## Pitfalls found on the way (they cost two runs)

- **The File → Save menu sets the selected-army variable to −1, and an attack click needs it set.** Measured (select army 0 → `0x4A0328` = 0; save → **−1**; a click on the reachable tile (101,36) still **moved** the army to (101,36) with 4 moves and set the variable back to 0; a second save gave −1 again). The (a) table was first taken with a save between its two clicks and was **re-run without one** (as it stands now): the same result, so the deselect at 0 moves is the move's own effect, not the save's. But a script that selects an army, saves (`keep`), then clicks an enemy city got the city only *selected* (its details in the Information panel), no attack and no prompt (`b_attack_prompt.py`, `b1_first_attempt.json`). The cause of that difference (the move path not reading the variable the attack path reads) is an inference, not measured. Select the army after saving.
- **The first check after End turn can race the UI:** a select that fails right after End turn succeeds a few seconds later (`b2_attack_prompt.py` retries with a pause).
- **`Game.attack` answers the prompt Yes by itself** (`dismiss_popups`); an experiment on the prompt has to capture it before.

## Reproduction

```text
setup/setup.sh                      # builds win_controls.exe and win_slider.exe too
mkdir -p ~/ic2-work/fixtures && cp saves/run0-start-AUTO0720-seed12345.SAV ~/ic2-work/fixtures/BASE.SAV
python3 runs/experiments/unit-map-mouse/g_taxation.py
python3 runs/experiments/unit-map-mouse/a_c_d_e.py
python3 runs/experiments/unit-map-mouse/b2_attack_prompt.py     # about 10 minutes (a few turns)
```
