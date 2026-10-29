"""#230 batch 8: the remaining limits and refusals (owner, 2026-10-30), on staged copies of fixtures (difftest/stage.py).
Written before running, with the original's expected behaviour from the code and earlier play:

- 198-army cap (`findings/2026-10-08-split-army-198-armies-cap-in-play.md`; FUN_00449f08 :48725 `DAT_004a0324 < 0xc6`): the cap
  counts every nation's armies. Split army at 197 records opens the dialog and splits; at 198 nothing happens, no box. Staged
  with ("add_armies", 0, N, 3200) on BASE.SAV (14 armies) so the game holds N records; Rome's army 0 (6 units) splits row 0.
- Embark too large (R06, TUnitMap_SelectUnit :46594 `ships < troops / 500`, integer division): PORT's army 0 has 10,700
  troops (10,700 / 500 = 21). 20 ships: refused ("The army is too large for this fleet ?"). 21 ships: ACCEPTED by the
  original although 21 × 500 = 10,500 < 10,700 (the integer division). 22 ships: accepted.
- Purse past 1,000 (`findings/2026-10-05-army-purse-writes-and-the-1000-cap.md` row 7): Join armies adds the purses with no
  cap. 1,000 + 1,000 gives 2,000 (confirmed in play); 1,000 + 600 gives 1,600.

PORT = saves/fleet-port-antium-0734.SAV: army 0 at (101,45), 3 moves; fleet 2 at (101,46), carrying none; army 13 at
(102,44) is the partner the original's Join picks (R02).
"""
from difftest.cases.orders230_b1 import BASE, case
from difftest.cases.orders230_b6 import PORT, staged

SPLIT0 = {"op": "split_army", "army": 0, "units": [0]}
EMBARK = {"op": "embark", "army": 0, "fleet": 2}
JOIN = {"op": "join_armies", "army": 0, "partner": 13}

CASES = [
    staged("split-at-197", "Split army with 197 armies in the game (accepted: the 198th record)", BASE,
           [("add_armies", 0, 197, 3200)], SPLIT0),
    staged("split-at-198", "Split army with 198 armies in the game (refused silently)", BASE,
           [("add_armies", 0, 198, 3200)], SPLIT0),
    staged("embark-20-ships", "embark 10,700 troops on 20 ships (R06 refusal)", PORT,
           [("fleet_ships", 2, 20)], EMBARK),
    staged("embark-21-ships", "embark 10,700 troops on 21 ships (original accepts: 10,700 div 500 = 21)", PORT,
           [("fleet_ships", 2, 21)], EMBARK),
    staged("embark-22-ships", "embark 10,700 troops on 22 ships (accepted)", PORT,
           [("fleet_ships", 2, 22)], EMBARK),
    staged("join-purse-2000", "join two armies with 1,000 talents each (original: 2,000)", PORT,
           [("army", 0, "money", 1000), ("army", 13, "money", 1000)], JOIN),
    staged("join-purse-1600", "join 1,000 + 600 talents (original: 1,600)", PORT,
           [("army", 0, "money", 1000), ("army", 13, "money", 600)], JOIN),
]
