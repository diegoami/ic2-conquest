# Supply providers, Transfer ships and the Transfer unit clamps in the original: no army provider, silence when there is none, a fleet-scan quirk, no capacity test on Transfer ships, and an army lost with its emptied fleet

**Status:** draft from `ic2-conquest`, awaiting promotion. It does the original-side checks 1, 2 and 6 of the v0.5.0 gap analysis (`runs/experiments/data/run-exp-gap-v050/rows_g2.md`, "Original-side checks needed"; research `docs/reports/2026-10-09-remake-v050-gap-analysis.md` rows UA01, UF01, UF03, UA03). The player picked these next.

**Tags:**
- `[confirmed]` (Wine): read from game memory, the boxes, the screenshots and the saves.
- `[code]`: capstone on `Imperial Conquest 2.exe`, addresses below.
- `[derived]`: the rule as stated.
- The remake side is the gap analysis's own reading (CLI and code), not repeated here.

## Answer

### 1. Supply providers (UA01, UF01)

| Case | Unit and position | What is within one tile | Supply army / Supply fleet | Log, file |
|---|---|---|---|---|
| P1 | army 0 at (100,34) | nothing | **nothing opens, no box** | P1-192914, `army_alone_nothing.png` |
| P1 | army 0 at (100,34), after Split army | own army 14 at (101,35) only | **nothing, no box** | `army_next_to_own_army_nothing.png` |
| P1 | army 14 at (101,35) | own army 0 only | **nothing, no box** | `new_army_next_to_own_army_nothing.png` |
| P1 control | army 0 at (100,35) | own city Arretium | dialog opens | `control_army_next_to_arretium_dialog.png` |
| P2 | army 0 at (99,32), Rome–Gaul staged at peace (L1) | Felsina (Gaul) | dialog: "Supplies at Felsina", **Buy supplies** panel | P2-193103, `army_next_to_felsina_peace_dialog.png` |
| P3 | army 0 at (99,32), unstaged (Rome–Gaul at war, 3) | Felsina (Gaul) | **nothing, no box** | P3-193155, `army_next_to_felsina_war_nothing.png` |
| P4 | army 0 at (105,48) | own fleet 2 at (104,48) only | dialog: "Supplies on fleet", **Fleet's money / Army's money** panel | P4-193254, `army_next_to_own_fleet_dialog.png` |
| P4 | fleet 2 at (104,48) | own army 0 only | **nothing, no box** | `fleet_next_to_own_army_nothing.png` |
| P5 | fleet 2 at (97,46), open sea | nothing | **nothing, no box** | P5-193415, `fleet_alone_nothing.png` |
| P5 | fleet 2 at (97,46), after Split fleet | own fleet 5 at (98,47) | dialog opens | `fleet2_next_to_new_fleet_dialog.png` |
| P5 | fleet 5 at (98,47) | own fleet 2 at (97,46) | **nothing, no box** | `new_fleet_next_to_fleet2_nothing.png` |

- **Armies are never providers** `[confirmed]`, for an army or a fleet.
- **With no provider, the order does nothing and shows no box** `[confirmed]`. The remake says "No city or fleet of yours, or of a nation at peace with you, within one tile." (UA01 b).
- **An army can supply from an own fleet** `[confirmed]` (P4). A foreign city counts only when its owner is not at war with the player `[confirmed]` (P2 vs P3).
- **A fleet supplies from another own fleet, but only from one direction** `[confirmed]` (P5: fleet 2 from fleet 5 opens; fleet 5 from fleet 2 does not). The code explains why `[code]`:
  - `TUnitMap_SupplyFleet` (`0x4477fc`) first looks for a city (`FUN_004495c8`: an own city in the 3×3, else any city whose owner is not at war, relation 3). Failing that, it calls `FUN_00449e50` on the fleet's own tile and opens the dialog only if the fleet found differs from the selected one.
  - `FUN_00449e50` scans x−1..x+1 (outer) and y−1..y+1 (inner), keeps the **last** own-fleet marker found, and does not skip the fleet's own tile.
  - So **a partner fleet at x−1 (any row) or directly north (x, y−1) is overwritten by the fleet itself, and nothing opens.** A partner to the south (x, y+1) or at x+1 works. In P5, fleet 5's partner was at x−1.
  - The dialog's own list, `TAFSupply_FindProviders` (`0x43f468`), does exclude the fleet itself. It offers up to 2 cities not at war and 3 own fleets within one tile, and no army `[code]`.
- **`TUnitMap_SupplyArmy`** (`0x446f50`) has the same city test, then `FUN_00449e50` on the army's tile `[code]`. No army marker matches the fleet test there, so the quirk does not hit an army.

### 2. Transfer ships (UF03)

`saves/fleet-split-antium-0734.SAV`: fleet 2 at (101,46), fleet 5 at (101,47). Ta*: fleet 2 staged to 30 ships (L1), and army 0 (10,700 troops) embarked on it by a normal order. Tb1: fleets staged to 95 and 10 ships.

| Case | Order | After | Box |
|---|---|---|---|
| Ta1 | carrying fleet 2 gives 5 | 25 / 15; army 0 still aboard | none |
| Ta2 (re-run 194517) | carrying fleet 2 gives 10 | **20 ships carrying 10,700 troops** (room 10,000) | none |
| Ta3 | fleet 5 gives 5 to the carrying fleet | 35 / 5 | none |
| **Ta4** | carrying fleet 2 gives **all 30** | **fleet 2 deleted, and army 0 with it** (owner −1, 10,700 troops lost); fleet 5 has 40 | **none, no prompt** |
| Tb1 | fleet 5 gives 8 to a 95-ship fleet | **100 / 5**: the arrows stop at 100 (the dialog showed 5 and 100 before OK) | none |
| Tc1 | fleet 5 gives all 10 | fleet 5 deleted; fleet 2 has 30 | none |
| Tc2 | fleet 2 gives all 20 | fleet 2 deleted; fleet 5 has 30 | none |

- **The arrows clamp; OK applies; nothing is refused** `[confirmed]` `[code]`. The ship arrow handler (`0x443924`) moves `min(step, ships left on the giving side, 100 − ships on the receiving side)`. The OK handler (`0x443b48`) writes both fleet copies back and re-bands both markers (`FUN_0044a878`).
- **A fleet left with 0 ships is deleted, and the other fleet takes its money and supplies** (`FUN_0044ad38`). That function also deletes a carried army, so emptying a carrying fleet destroys its army without a word `[confirmed]` (Ta4).
- **No army or capacity test** anywhere in `TFleetToFleet` `[code]`. A carrying fleet can give or take ships, and can end below the army's needs `[confirmed]` (Ta2).
- **The remake** refuses all three (an armed fleet, over 100 ships, every ship moved), so it differs. Ta4's army loss is likely an original defect the remake need not copy; that is for the remake to decide.

### 3. Transfer unit clamps (UA03, R29, R30)

`saves/fleet-port-antium-0734.SAV`, Transfer unit with three units selected in the left list (`probe_transfer20.py`'s steps).

| Case | Staging (L1) | After | Box |
|---|---|---|---|
| U1 | army 0: 3 × HI 1,000; armies 12, 13: 8 × HI 12,250 = 98,000 | partner (army 13): **10 units, exactly 100,000**; army 0 keeps 1 unit | one: "An army can not hold more than 100,000 troops." |
| U2 | army 12 (moves 3): 3 × LI 1,600 into army 0 aboard fleet 2 (30 ships); army 13 owner 1 (TR3's staging) | army 0: **13,900** (two moved); army 12 keeps 1,600 | one: "This fleet can not carry any more troops." |
| U3 | army 12: 1 × LI 4,799 | army 0 aboard: **15,499 troops on 30 ships** (nominal capacity 15,000); army 12 emptied and removed | none |
| U3b | army 12: 1 × LI 4,800 | unchanged (10,700) | "This fleet can not carry any more troops." |

- **Both are per-unit clamps** `[confirmed]`: the units that fit move, the others stay, and one box follows. The 20-unit case was already known to behave this way (`2026-10-08-transfer-dialog-20-units-and-slot-gaps.md`).
- **100,000 itself is allowed** `[confirmed]` (U1), matching the pass test `< 100,001` (R29).
- **The fleet test truncates** `[confirmed]`: it refuses only when `ships < (troops + unit) div 500`. 15,499 div 500 = 30, so 30 ships take 15,499 troops; 15,500 is refused (U3, U3b). A full fleet can hold up to 499 troops over `ships × 500`.
- **The remake** refuses the whole order at 100,000 and does not test the fleet at all (UA03), so both differ.

## Evidence

- **Data:** `runs/experiments/data/run-exp-supply-transfer-clamps/` (`supply_transfer.py` with the code reading in its docstring, `supply_transfer-<case>-<stamp>.jsonl`, `SAVES.sha256`, `README.md`).
  - Ta1, Ta3, Tb1, Tc1 and Tc2 ran with a first OK loop that pressed Cancel when the dialog was still on screen after the first OK. In every case OK had already applied (the before-OK screenshots, and the memory and saves after).
  - The loop was then fixed: wait for the dialog to close, never press Cancel. Ta2 was re-run with the fix and Ta4 run with it; both needed one OK.
- **Release:** [`run-exp-supply-transfer-clamps`](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-supply-transfer-clamps): every `<case>_<stamp>_*.SAV` (before/after/staged) and screenshot named above.
- **Code:** `TUnitMap_SupplyArmy` `0x446f50`, `TUnitMap_SupplyFleet` `0x4477fc`, `FUN_004494e4` (own city), `FUN_004495c8` (city not at war), `FUN_00449e50` (fleet marker, last match), `FUN_00449970` (fleet at tile), `TAFSupply_FindProviders` `0x43f468`, the TFleetToFleet ship arrows `0x443924`, supply arrows `0x4439dc`, OK `0x443b48`, Cancel `0x443c58`.

## Not established

- **Tiles in the fleet quirk:** only x−1 (P5) was played. The north tile (x, y−1) and the diagonals rest on the code.
- **The Supply dialog with several providers:** whether the player can choose among them, and in what order they are listed.
- **A purchase from a foreign city at peace:** the dialog was opened and closed, but nothing was bought.
- **An army aboard a fleet as Supply army's target** (the selected-fleet branch of `0x446f50`).
- **The desktop original.**
