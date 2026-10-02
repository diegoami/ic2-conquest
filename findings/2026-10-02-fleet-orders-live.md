# Fleets live: build and launch, embark and unload by click, supply, repair, split, join, transfer, scuttle

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is the first live run of the fleet orders that `docs/rules-digest.md` §8 and the research reports (`supply-driven-morale-and-fleet-attrition.md`, `decompiled-unit-map-orders-and-record-fields.md`, `fleet-order-at-caere.md`) describe from code. It also answers question (f) of the unit-map experiment (`findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md`): embark and unload by click. **Fleet attack (a naval battle) was not run.**

**Answer.**
- **Build and launch:** a 30-ship fleet ordered at turn 0720 appeared at turn **0732**, twelve turns later, on the sea tile next to the build city, with **0 moves**, supplies 50, condition 100 and no army aboard. The next turn it had **32 moves** (30 − (30 − 50)/10).
- **Embark** = select the army, click the adjacent own fleet: the army moves **onto the fleet's tile**, its cell becomes −1, the fleet's carried-army field becomes the army's index, and **both units' moves become 0**. It is refused with a box that has **OK only**, "The army is too large for this fleet ?", when troops exceed `ships × 500`; the click then **selects the fleet** instead.
- **Unload** = select the fleet, click an **adjacent land tile**: the army lands there (its cell becomes the terrain code), the fleet's carried-army field becomes −1, and **both units' moves become 0** again. Both units need moves to do it.
- **Repair** at an own city costs `ships × points / 5` talents (30 ships, 3 points: **18**) and the fleet's moves become 0. **Supply fleet** moves tons from an adjacent own city (100 tons: city 330 → 230, fleet 0 → 100). **Split fleet** (30 → 20 + 10): the new fleet appears on an adjacent tile with **0 moves**. **Join fleets** has no dialog, adds the ships and sets the moves to 0. **Transfer ships** moves ships between two adjacent fleets (20/10 → 15/15). **Scuttle** asks "Are you sure you want to scuttle this fleet ?" (Yes/No/Cancel) and removes the fleet on Yes.

## Method

- **Build:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb, `SEED.TXT` = 12345, the run-0 start (`saves/run0-start-AUTO0720-seed12345.SAV`). Driver `harness/driver.py`; the scripts and tests are `tests/make_fleet_fixture.py` and `tests/test_orders.py` (the ten fleet tests).
- **Fixtures** (a fleet takes 12 turns, so it is built once): `python3 -m tests.make_fleet_fixture` orders a 30-ship fleet at the start and ends turns until it launches (`FLEET.SAV`); `… stage` ends one more turn (a fleet has 0 moves on its launch turn), sails the fleet to the sea tile (101,46) next to Antium (102,46), and marches army 0 to (101,45) beside it. The two committed saves are `saves/fleet-port-antium-0734.SAV` and `saves/fleet-split-antium-0734.SAV` (after Split fleet).
- **Each test** loads a fixture, issues one order, saves, and checks the save diff (units, fleets, cities, treasury); the selected unit and the carried-army field are also read from the game's memory (`0x4A0328` armies, `0x4A032A` fleets; the fleet table at `0x49C26C`, 26 bytes each).
- **Dialogs** were found by hovering the toolbar (tooltip names) and reading the controls of each window (`harness/win_controls.c`); screenshots are in the release.

## Observations

Saves marked *(git)* are in `saves/`; the others are in release `run-exp-fleet-orders`.

**Launch** (`FLEET.SAV` = `AUTO0732.SAV`; log of `make_fleet_fixture`). Ordered at turn 0720 ("The fleet will be built at Caere."), 30 ships, treasury 2,200 → 1,900 (cost `ships × 10`). The countdown in the fleet record fell 24 → 22 → … → 2 → −1 over the autosaves 0721–0732. At 0732: fleet 2 at (98,43), moves 0, supplies 50, money 0, condition 100, army −1, covered cell 0. At 0733: moves **32**. Moving three tiles (to (101,46)) left 29. By 0734 the fleet's condition was **97 %** and its supplies **0**.
**Caere was captured by Gaul during the twelve turns:** the city is Rome's in `run0-start-AUTO0720-seed12345.SAV` and Gaul's in `FLEET.SAV`; the fleet therefore launched next to an enemy city.

**Embark** (`saves/fleet-port-antium-0734.SAV` → `T_EMBARK.SAV`; `saves/fleet-split-antium-0734.SAV` → `T_EMBARK_REFUSED.SAV`):

| | fleet 2, 30 ships (capacity 15,000) | fleet 2, 20 ships (capacity 10,000) |
|---|---|---|
| army 0 | 10,700 troops, (101,45), 3 moves | the same |
| click on the fleet | the army **boards**: position (101,46) = the fleet's tile, moves **0**, cell **−1** (embarked); the fleet's moves 29 → **0**, carried-army field **0** | box "The army is too large for this fleet ?", **OK only**; army 0 stays at (101,45) with 3 moves; the click **selects the fleet** |

With the first save, army 0 was first 23,700 and then 16,600 troops (earlier staging steps, not kept): both were refused against the 30-ship fleet (15,000), the 10,700 one boarded. An army produced by Split army has **0 moves** and cannot be selected that turn, so it cannot embark that turn.

**Unload** (`T_EMBARK.SAV` → end turn → `T_DISEMBARK.SAV`): after the turn army 0 had 9 moves and fleet 2 had 25 (still aboard, same tile). Select fleet 2, click the land tile (101,45): army 0 at (101,45), cell 2 (plain), moves **0**; the fleet's moves **0**, carried-army −1; both selected-unit variables −1.

**Supply** (`T_SUPPLY_FLEET.SAV`): the dialog "Supply fleet" lists the providers ("Supplies at Antium: 330"), "Fleet's supplies" 0, a national balance (1,730) and "Fleet's money" 0, each with 10s/100s arrows. One 100s press: fleet supplies 0 → 100, Antium 330 → 230.
**Repair** (`T_REPAIR_FLEET.SAV`): "Original state of repair 97 %", 1s/10s arrows, "New state of repair" and "Cost of repairs". Three 1s presses: condition 97 → 100, treasury 1,730 → 1,712 (**18**), fleet moves 29 → **0**.
**Split** (`T_SPLIT_FLEET.SAV`): the dialog is a two-column table, "First fleet's" and "Second fleet's" ships, supply and money, with 1s/10s (ships) and 10s/100s (supply, money) arrows; the **down** arrows move to the second fleet, the up arrows back (30/0 → 20/10 → 19/11 on screen). Result: fleet 2 (101,46), 20 ships, 29 moves; **new fleet 5 at (101,47)**, 10 ships, **0 moves**.
**Join** (`T_JOIN_FLEETS.SAV` from `saves/fleet-split-antium-0734.SAV`): one click, no dialog: a single fleet of 30 ships with moves **0**.
**Transfer** (`T_TRANSFER_SHIPS.SAV`): the window is "Fleet to fleet transfer", the same layout as Split fleet; five ships down: 20/10 → 15/15.
**Scuttle** (`T_SCUTTLE_FLEET.SAV`): "Are you sure you want to scuttle this fleet ?" with Yes, No and Cancel; Yes: Rome has no fleet.
**Move** (`T_MOVE_FLEET.SAV`): select the fleet, click a sea tile two away: (101,46) → (99,46), moves 29 → 27.

**Refusals seen in probes (no save kept):** with the fleet at (98,43), next to Caere (Gaul's by then), Repair fleet said "The fleet can only be repaired at one of your cities." and Scuttle "To scuttle a fleet it must be near one of your cities." Join fleets and Transfer ships with no second fleet adjacent showed nothing.

**Also seen** (UI, Wine): the Build fleet dialog **stays open** after the order ("The fleet will be built at …"); a second OK would order a second fleet. The click selects the fleet marker (`SEL_FLEET`), and the fleet toolbar (Supply fleet, Repair fleet, Transfer ships, Split fleet, Join fleets, Scuttle fleet, Cancel selection) appears in the same strip as the army's.

Screenshots in the release: `embark_box.png`, `embark_ok.png`, `disembark.png`, `fleet_sel.png`, `fleet_split.png`, `sp2_all.png`, `fleet4_supply.png`, `fleet4_repair.png`, `fleet4_scuttle.png`, `fleet4_join.png`, `fleet4_transfer.png`.

## Inferences

- The numbers agree with the research formulas: 12 turns to launch; moves 32 for 30 ships (`30 − (ships − 50)/10`); embark needs `ships ≥ troops/500` (15,000 accepted, 10,000 refused for 10,700); repair `ships × points / 5` = 18. The fleet starting at supplies 50 and condition 100 also matches. So these are confirmations of the code reports, now live; the new facts are the UI ones (the selection after a refusal, where the army sits when aboard, what Join does with moves, the dialogs).
- "Both units' moves become 0" on embark and on unload makes a landing a whole turn for both; a fleet that is out of moves cannot unload.
- The fleet's condition was 97 % about two turns after launch (supplies had also fallen from 50 to 0); what caused the 3 points (a storm, rough sea on the way) was not traced, and no storm message was looked for.
- The fleet's launch tile is the sea tile next to the build city; Caere (99,42) and the fleet (98,43) are diagonal neighbours.

## What this does not establish

- **Naval battles** (clicking an enemy fleet), **with or without an army aboard**: not run. Nothing here tests `ships × condition/10 + siegeStrength/50 + random`.
- **Storms and losses at sea**: not run on purpose; the 97 % condition is the only trace of damage and it is unexplained.
- Repair at a city *tile* (the fleet was adjacent to Antium, not in it); Supply fleet against another fleet; Join with a fleet carrying an army; Split on a fleet carrying an army; the "20 ships minimum" for Split (30 was used) and the "fewer than 100 combined" for Join; scuttle next to a city that is not Rome's.
- Whether the new fleet's tile after Split is a rule: one observation, (101,46) → (101,47).
- **Wine-only.** Window layout, dialog titles and the click handling are what this Wine build does; the code reports are the source of truth.

## Reproduction

```text
setup/setup.sh
mkdir -p ~/ic2-work/fixtures && cp saves/run0-start-AUTO0720-seed12345.SAV ~/ic2-work/fixtures/BASE.SAV
python3 -m tests.test_orders embark_refused embark disembark supply_fleet repair_fleet scuttle_fleet split_fleet join_fleets transfer_ships move_fleet
python3 -m tests.make_fleet_fixture && python3 -m tests.make_fleet_fixture stage     # to rebuild the fixtures (about 12 turns)
```
