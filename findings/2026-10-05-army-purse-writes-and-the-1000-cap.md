# An army's purse: every write in the original, which ones cap it at 1,000, and what Join armies does (2,000 in play)

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 1 of `docs/tasks/v050-rule-reads.md` (clone task T72, `imperial_conquest_2` #317, bug #315). **Wine-only: every play result is a candidate until the desktop original confirms it.** Natural state, nothing edited; fixture saves only, as copies.

**Tags.** `[derived]` = read from the decompile only (function, address and line of `all_app_functions.txt`, kept in `runs/experiments/data/run-exp-v050-rules/code_extract_q1_purse.txt` with those line numbers). `[confirmed]` = seen in play with a before and after save, listed in the evidence table. A rule is never tagged `[confirmed]` for the part only the code shows.

**Answer.**
- **Only three paths cap a purse at 1,000, and all three are minimum rules in a dialog or an own-city refill**: the Supply army money arrows, the Army to army transfer money arrows (both `min(step, 1000 - receiver's purse)`, with no floor at 0), and the own-city refill `FUN_0044F6D8` (purse above 1,000: the excess goes to the treasury). **Every other path that adds to a purse adds without any cap**: Join armies, the merge of an emptied army in Army to army OK, the captured purse of a won battle, and the AI's merge of a small army. **The clone's cap at 1,000 on Join armies is not in the original.**
- **Join armies adds the purses** `[derived]` and `[confirmed]`: two armies of 1,000 each gave one army of **2,000** (`Q1_05_before_join.SAV` → `Q1_06_after_join.SAV`). This is how the original's save IP016 holds 1,066.
- **Nothing trims the 2,000 afterwards, except the Supply army dialog**: one click on its money up arrow moved `min(100, 1000 - 2000) = -1,000`, so the purse fell to 1,000 and the treasury gained 1,000 `[confirmed]` (`Q1b_01_after_one_up_click.SAV`). A purse over 1,000 is also cut by the own-city refill, but that refill is **not reachable from a human move** (below).
- **The refill on a move (E12) is an AI path.** The human walk (`TUnitMap_CheckForMove` → `MoveHumanArmy` → `FUN_0044D734`) only takes terrain tiles as targets; a click on a city is an attack or a selection. An army that ended its move next to two own cities with stock kept purse 100 and supplies 170, and a click on an adjacent own city did nothing `[confirmed]` (two negative observations, `Q1_01_army0_at_100_42.SAV`, `state_log.jsonl`). The code that tops a purse up (+500 from the treasury when the purse is under 500 and the treasury is above 0) is run for the AI by `FUN_0044E41C` every turn for each non-hostile city within 4 tiles `[derived]`.

## Method

- **Code.** Every reference to the army record's purse (`+0x0C`: `DAT_0047C1F8`, 328 shorts per record, and the pointer forms `psVar[4]` of loops over `&DAT_0047C1F0`) in `all_app_functions.txt` was listed: 53 symbol references plus the whole-record copies (the `0xA4`-int loops) and the pointer loops of 14 functions, each read. Functions with a purse write are in the table; functions that only copy a record or read the purse are listed under "Not a write".
- **Play.** `runs/experiments/v050_rules/q1_purse.py` and `q1b_overcap_trim.py` on copies of `mobilize-new-army-0720.SAV` (Rome, treasury 2,101, army 0 at (100,37) purse 100, army 1 at (120,53) next to Heraclea purse 100) with the normal build `Imperial Conquest 2 fast rollingsave seed.exe`, `SEED.TXT` 12345, a private Xvfb display and game folder. Each order was issued through the UI (`harness/driver.py`, with the Supply army arrows located by `win_controls` because this environment's metrics differ from `Game.supply`'s fixed points), and the game was saved with File > Save as after each order. No End turn. The saves are parsed with `state/sav.py`; the numbers below are read from the saves, not from the log.

## The writes (the rule, by path)

Line numbers are of `all_app_functions.txt`. "Cap" = whether the result is limited to 1,000 or another value.

| # | Path (player action) | Function @ address, lines | What it does to the purse | Cap |
|---|---|---|---|---|
| 1 | **Supply army**, money arrow up (treasury, or the supplying fleet, to the army) | `TAFSupply_ChangeMoney` @ 0044005C, :43117-43136 | `step = min(10 or 100, 1000 - purse)`, then (fleet provider) `min(step, fleet's purse)`; treasury (or fleet) `-= step`, purse `+= step`. **No floor at 0 and no check of the treasury's sign.** | **1,000, by `min`.** A purse already above 1,000 gets a negative step: money flows back, purse becomes 1,000 `[confirmed]` |
| 2 | **Supply army**, money arrow down | same, :43153-43170 | `step = min(10 or 100, purse)`; purse `-= step`; treasury (or fleet) `+= step` | floor 0 |
| 3 | **Buy supplies** (Supply army at a foreign, non-hostile city: the "buy" amount in tons) | `TAFSupply_ChangeBuyAmount` @ 0043FE4C, :43032-43043; `TAFSupply_TransferSupply` @ 0043FF98, :43079-43082 | The amount is limited to `purse × 5` (:43039-43042). On the transfer: purse `-= tons div 5` and the city owner's treasury `+= tons div 5` (:43070-43073). | none (it only subtracts) |
| 4 | **Army to army transfer**, money arrows | `TArmyToArmy_ChangeMoney` @ 00442448, :44044-44088 | `step = min(10 or 100, 1000 - receiver, giver)`; giver `-=`, receiver `+=` on the dialog's working copies. **No floor at 0**: a receiver above 1,000 gives a negative step and sends money back. | **1,000, by `min`** |
| 5 | **Army to army transfer OK** (also the OK of **Split army**: the same form) | `TArmyToArmy_OK` @ 00442EF8, :44585-44603 | Writes both working copies back over the real records (the whole 656-byte record, purse included, taken from the dialog's values). The supply push (steps 4-5 of `2026-10-03-army-to-army-ok-supply-rebalancing.md`) does not touch money. | none added here |
| 5b | **OK, an army left empty** (every unit moved out) | same, :44623-44644 | `survivor.purse += emptied.purse`, then the emptied army is deleted (`FUN_0044AB90`). | **none** (uncapped) |
| 6 | **Split army** (new partner) | `TUnitMap_SplitArmy` @ 0044755C :47046 → `FUN_00449F08` @ 00449F08, :48740 | The partner is created with purse 0 (moves 0, supplies 0, morale 59 = 0x3B). Money moves only through row 4. | 0 at creation |
| 7 | **Join armies** | `TUnitMap_JoinArmies` @ 004472FC, :46992-46993 (also :46994-46995 supplies, :46997 moves := 0) | `kept.purse += partner.purse` (16-bit add), the partner is deleted. Refused only for: an army aboard a fleet, more than 20 units, more than 100,000 troops (:46976-47012). | **none** `[confirmed]`: 1,000 + 1,000 = 2,000. A 16-bit wrap above 32,767 `[derived]` |
| 8 | **Disband army** (must be near an own city) | `TUnitMap_DisbandArmy` @ 004476AC, :47109-47110 | The whole purse goes to the owner's treasury (`treasury += purse`), the supplies to the nearest own city (`+= supplies`, :47113-47114), the army is deleted. | none |
| 9 | **Change units**, Disband or Rename, OK | `TChangeArmyUnits_OK` @ 00445378, :45820-45827 | Writes the dialog's working copy of the whole record back (the purse is unchanged by that dialog; it also commits the mobilisation value). | none |
| 10 | **Automatic resupply** at a city (**AI**, see below) | `FUN_0044F6D8` @ 0044F6D8, :53092-53103 (own city), :53105-53111 (other city) | **Own city** (the city's owner is the army's owner): if `purse > 1000`, `treasury += purse - 1000` and `purse := 1000`; then if `purse < 500` **and** `treasury > 0`: `purse += 500`, `treasury -= 500`. The tons are filled from the city's stock up to `troops div 100` (:53088, :53112-53113). **Other non-hostile city:** the tons are bought, `tons = min(room, stock, purse div 5)` (:53106), purse `-= tons div 5`, the city owner's treasury `+= tons div 5`. | **1,000 (own city), by moving the excess to the treasury** |
| 11 | **Quarterly tick**, mercenary pay and desertion | `FUN_00451b40` @ 00451B40, :54750-54766, :54772-54773 | Per army, per unit slot 0 → 19: a mercenary slot (`+0 ≠ 0`) is paid `(troops div 200 × price) × quality div 5` from the **purse** if `purse > 0` (:54765, the last payment may leave it negative); if `purse ≤ 0` the unit is removed with `troops div 100` tons of the army's supplies (:54759-54761, `FUN_0044AC3C`). After the army: purse and supplies are floored at 0 (:54772-54775). Regular units are billed to the treasury (:54754) and never leave. **The tick never adds to a purse.** | no cap; floor 0 |
| 12 | **Captured treasury of a won battle** (tactical battle) | `TBattleOver_OK` @ 00459220, :57618-57619 | `winner.purse += loser.purse` (16-bit), loser deleted. The panel says "The army of X captured N talents." (`TBattleOver_InitializeForm` :57532-57539). Supplies are capped right after (:57621-57625), **money is not**. | **none** |
| 12b | The same for a battle between two computer nations resolved at once | `FUN_0044AEE4` @ 0044AEE4, :49648-49649 and :49687-49688 | The stronger army's purse `+=` the loser's. | **none** |
| 13 | AI merges a small army into a nearby own one | `FUN_004509F0` @ 004509F0, :53981 | `target.purse += small.purse`, supplies likewise, units moved. (Armies under 20,000 troops, own army within 17 tiles, combined under 20 units and 80,000 troops.) | **none** |
| 14 | AI splits a landing army | `FUN_0044F8FC` @ 0044F8FC, :53201-53203 (called from `FUN_0044B79C` :49978-49979 when the fleet cannot carry all) | New army gets `purse div 3`, the old keeps the rest. | n/a |
| 15 | An army loses its last unit (a mercenary walks out, or every unit is moved or disbanded) | `FUN_0044AC3C` @ 0044AC3C, :49454-49456 → `FUN_0044AB90` | The army is deleted; its purse and supplies are gone (not paid to the treasury). | n/a |
| 16 | Load of a save | the SAV table is copied as is | IP016's 1,066 is a loaded value; the code that makes it is row 7 (or 5b, 12, 13). | n/a |

### Reachability of row 10 (automatic resupply)

- `FUN_0044F6D8` has two callers: `FUN_0044E41C` (:52246), which the AI runs for each of its armies every turn (`FUN_0044F31C` :52926) for each city within 4 tiles (:52242) that is its own with stock, or non-hostile with stock when the army has a purse (:52244-52245); and the tail of `FUN_0044D734` (:51654-51655), when the walk's **target tile** holds a city marker.
- The human path is `TUnitMap_UnitMapClick` @ 00446420 (:46384-46386): a click on a terrain tile goes to `CheckForMove` → `MoveHumanArmy` → `FUN_0044D734` with that **terrain** tile as target; a click on a city, army or fleet marker goes to `TUnitMap_SelectUnit` (:46427) instead, which only attacks (:46532-46553, other nation) or selects (own city). So for a human army the tail's city branch is not reached `[derived]`, and in play it was not: army 0 ended at (100,42), next to Rome (101,43) and Caere (99,42), purse 100 → 100, supplies 170 → 170, treasury 2,101 → 2,101; army 1 clicked its adjacent own city Heraclea: nothing happened, the selection was dropped `[confirmed]`.
- The feature inventory's row E12 ("when a human army's move ends against a non-hostile city, the army is filled…") describes the AI path; it should be re-tagged for humans.

### Not a write

- **Weekly tick** (`FUN_004514EC` :54493-54530): changes moves (+6), supplies (+10), morale (+14); not the purse.
- **City capture** (`FUN_0044B27C`, `FUN_0044BB18`) and **peace reparations** (`FUN_00450C68` :54160): money moves between nation treasuries, no army purse is read or written (no reference to `+0x0C` in them).
- **Recruit mercenaries** (`TRecruitMercs_RecruitMercUnit` @ 00441360, :43633-43636): the purse is only **tested** (`purse < price` → "Your army has too little money to pay these mercenaries."); nothing is subtracted (see the T113 finding of this task).
- **Compaction of the army array** (`FUN_0044ABE0` :49418-49424): copies the last record into a freed slot, purse intact. **Move unit** (`FUN_0044ACB4`), **mobilise** (`FUN_0044A4E0` → `FUN_00449F08`, purse 0): no purse change.

## Evidence (play)

All from copies of `mobilize-new-army-0720.SAV`; saves in release `run-exp-v050-rules` (`batch-q1-q3.tar.gz`), hashes in `runs/experiments/data/run-exp-v050-rules/SAVES.sha256`, the values below parsed from the saves with `state/sav.py`.

| Save | Treasury | Army 0 (100,37 → 100,42): moves / supplies / purse | Army 1 (120,53): moves / supplies / purse / troops | Army 15 (split off, (121,54)): purse |
|---|---|---|---|---|
| `Q1_00_start.SAV` | 2,101 | 8 / 170 / 100 | 8 / 176 / 100 / 25,868 | – |
| `Q1_01_army0_at_100_42.SAV` | 2,101 | **0 / 170 / 100** (moved next to Rome and Caere: no refill) | 8 / 176 / 100 | – |
| `Q1_03_army1_supply_11x100.SAV` (11 clicks of "+100") | **1,201** (-900) | 0 / 170 / 100 | 8 / 176 / **1,000** | – |
| `Q1_04_after_split.SAV` | 1,201 | | 8 / 176 / 1,000 / 20,368 | **0** |
| `Q1_05_before_join.SAV` (partner supplied, 11 clicks) | **201** (-1,000) | | 8 / 176 / 1,000 / 20,368 | **1,000** |
| `Q1_06_after_join.SAV` (Join armies, army 1 selected) | 201 | | **0** / 176 / **2,000** / 25,868 (7 units); army 15 deleted | gone |
| `Q1b_01_after_one_up_click.SAV` (Supply army, one "+100" click, from `Q1_06`) | **1,201** (+1,000) | | 0 / 176 / **1,000** | |

- **Supply army cap (row 1).** 11 clicks of 100 from 100 cost 900: the 10th and 11th clicks did nothing (`min(100, 1000 - 1000) = 0`).
- **Join armies (row 7).** 1,000 + 1,000 = 2,000 in the kept army (the selected one), no message, no cap; moves of the kept army 8 → 0 (:46997).
- **Over-cap trim (row 1).** From the 2,000, one "+100" click: treasury 201 → 1,201, purse 2,000 → 1,000; a second click changed nothing (`Q1b_02` in the state log). The prediction was written from the code before the run (`q1b_overcap_trim.py` docstring).
- **No refill for a human move (row 10).** `Q1_00` → `Q1_01` (purse and supplies unchanged); the click on the own city is in `state_log.jsonl` (`Q1_02_army1_after_click_on_own_city`: nothing changed, selection -1).
- A first run of `q1_purse.py` was cut short by a mis-aimed click on Rome's tile (which only deselects) and by the driver's fixed Supply army coordinates; its entries stay in `steps.log` and `state_log.jsonl`, its saves are `Q1_00_start.SAV`, `Q1_01_army0_after_move_to_Rome.SAV` (army 0 did not move) and `Q1_00_start.v2.SAV` in the archive.

## What this does not establish

- **The own-city refill (row 10, own city) was not seen in play**: no human path reaches it, and the AI path needs an End turn (a quarter or a turn of AI armies next to their own cities would show a `+500` or a `purse - 1000 → treasury` in a save pair). It stays `[derived]`. A save pair exists in the research repo's `upkeep-payment-and-desertion.md` ("purse exactly +500 over the prediction", 4 of 39 army-quarters, `FUN_0044F6D8`), which is the AI case.
- **Rows 3, 8, 12, 13 and 14 are `[derived]` only.** Buy supplies needs an army next to a non-hostile foreign city (not staged); Disband army and the captured purse were not run for this finding (the captured purse and its "captured N talents" panel are in `findings/2026-10-04-battle-probe.md` territory but the purse was not read there).
- **The 16-bit wrap** of a purse above 32,767 (repeated joins of rich armies) is code only.
- **Row 4 and the Split dialog's money arrows** were not pressed in play; they share `min(step, 1000 - receiver)` with row 1 by the code.
- **Wine-only**, one nation (Rome), one turn (0720).

## Reproduction

```text
python3 runs/experiments/v050_rules/extract_code.py q1_purse 0043ff98 0044005c ...      # the code extract (already tracked)
python3 runs/experiments/v050_rules/q1_purse.py            # about 5 minutes, own display :733 and game folder ~/ic2-work-v050
python3 runs/experiments/v050_rules/q1b_overcap_trim.py    # needs Q1_06_after_join.SAV from the first script
python3 runs/experiments/v050_rules/claims_audit.py        # recomputes every number above from the saves and the extract
```
