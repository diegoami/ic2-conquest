# Disband army and Scuttle fleet next to an own city: the unit's money goes to the treasury and its supplies to the city, in full

2026-10-22. **[confirmed]** (code + one play each, Wine). Catalogue rows P01 and P02 of
`2026-10-05-refusal-texts-and-conditions.md`, until now `[code]` for what Yes does; run `run-exp-manual-gaps` (items B7, B8).

## Answer

- **Code** (P01 `TUnitMap_DisbandArmy`, P02 `TUnitMap_ScuttleFleet`): on Yes the unit's money is added to the nation's
  treasury (nation `+0x438`) and its supplies to the own city next to it (city `+0x18`), then the unit is deleted.
- **Play** (seed build `354d8265…`, seed 12345). The whole decoded save changes only in these fields:

  | Order | Save before → after | Unit before | Treasury | City supplies | Other changes |
  |---|---|---|---:|---:|---|
  | Disband army 0 next to Arretium (turn 0720) | `MG_B7_before_disband.SAV` → `MG_B7_after_disband.SAV` | 23,700 troops, money 100, supplies 170 | 2,200 → **2,300** (+100) | Arretium 150 → **320** (+170) | army 0 owner 0 → −1; map (100,37) 200 → 2 (the marker gives back the plain) |
  | Scuttle fleet 2 next to Antium (turn 0734) | `MG_B8_before_scuttle.SAV` → `MG_B8_after_scuttle.SAV` | 20 ships, money 100, supplies 100 | 1,630 → **1,730** (+100) | Antium 230 → **330** (+100) | fleet 2 owner 0 → −1; map (101,46) 300 → 0 |

  Both boxes read "Are you sure you want to disband this army ?" / "... scuttle this fleet ?" (Yes, No, Cancel), answered Yes.
- Nothing is lost and nothing is capped: the whole purse and the whole stock move (Arretium ends at 320, above its 150
  start; no city supply cap applied here). The troops and ships themselves are simply gone (no refund for them).

## What this does not establish

- One play each. A unit next to **two** own cities (which city receives the supplies) was not tried; the code takes the city
  `FUN_004494e4` returns.
- Fleet 2's money and supplies were put there in the same session through Supply fleet (100 tons from Antium, 100 talents
  from the treasury: Antium 330 → 230, treasury 1,730 → 1,630), so the scuttle gives back exactly what that order took.

## Evidence

- `runs/experiments/data/run-exp-manual-gaps/`: `B7-disband-diff.txt`, `B8-scuttle-diff.txt` (`diff_saves.py`),
  `run-log.jsonl` (events `B7_disband`, `B8_scuttle`, read from game memory before and after), `SAVES.sha256`.
- Saves (Drive `IC2/artifacts/run-exp-manual-gaps/saves/`, release `run-exp-manual-gaps` when made):
  `MG_B7_before_disband.SAV` (`f41e579b8e10…`; a Save As of `MG_A1_staged_carthage_army3_at_101_37.SAV`, which is
  `run0-start-AUTO0720-seed12345.SAV` with Carthage's army 3 moved next to Rome's army 0 for item A1, whose attack prompt
  was answered No and changed nothing), `MG_B7_after_disband.SAV`
  (`07cf02bdc661…`); `MG_B8_before_scuttle.SAV` (`afd343d6695c…`, from `saves/fleet-split-antium-0734.SAV` plus the Supply
  fleet order), `MG_B8_after_scuttle.SAV` (`1ad22962bf53…`).
