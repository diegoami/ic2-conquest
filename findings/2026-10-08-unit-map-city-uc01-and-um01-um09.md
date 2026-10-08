# Unit map > City (UC01) and Unit map view & selection (UM01–UM09) — verification of UC01 + UM01–UM09

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows UC01 (single) and UM01–UM09 (nine). One consolidated draft because all ten rows are anchored on `TUnitMap` (the unit-map child window) and `TInformation` (the information panel). The information panel's six `<X>Details` and `<X>Units` handlers are listed once; per-row references cite the table below.

**Tags.** All ten = `[confirmed]` except UM01 = `[derived]` (the form's full control layout in `form_controls.tsv` is extracted; the `Panel1 sb_*` button strip under the canvas is the `[derived]` part). Carried from the inventory.

## Answer

### UC01 — Fortify city (form TFortifyCity)

Form `TFortifyCity` ('Fortify city' caption, `OnCreate=InitializeForm`). The form's control list reproduced (head of the form here, full listing in `form_controls.tsv`):

| Path | Class | Caption / hint | OnClick |
|---|---|---|---|
| `FortifyCity` | `TFortifyCity` | `Fortify city` | `OnCreate=InitializeForm` |
| `FortifyCity/Bevel1..6` | `TBevel` | — | (decoration) |
| `FortifyCity/Label1` | `TLabel` | `Initial` | — |
| `FortifyCity/Label2` | `TLabel` | `fortification` | — |
| `FortifyCity/Label3` | `TLabel` | `1s` | — |
| `…/Label4..N` | `TLabel` | (10s, Cost, etc.) | — |

Functions (function_list.tsv):

| Address | Function |
|---|---|
| `0x004404c0` | `TFortifyCity_InitializeForm` |
| `0x00440658` | `TFortifyCity_PrintNumbers` |
| `0x0044076c` | `TFortifyCity_ChangeFortification` |
| `0x004407e4` | `TFortifyCity_OK` |
| `0x00440838` | `TFortifyCity_Cancel` |
| `0x00448004` | `TUnitMap_Fortify` (the dispatcher) |

Live evidence: `C:§1 'Fortify city' (saves/fortify-arretium-0720.SAV: 72 → 372 pending, cost 99)`. `form_xrefs.tsv` lists `TUnitMap_Fortify @ 0x004480b6` as the single caller of `TFortifyCity`. The "at most 10 points per turn" rule is per `findings/...-fortification-orders-cost-rate-and-the-100-bug.md`. Help topic 37 ("Fortify city").

### UM01 — Unit map window (form TUnitMap)

Form `TUnitMap` with `Panel1 sb_*` button strip and the `ScrollBarH`/`ScrollBarV` scrollbars. The scrollbars are form-level: `OnScroll=UnitMapScrolled` at `TUnitMap_UnitMapScrolled @ 0x00446348` (function_list.tsv). The form's panel button strip is the per-context button row (army / fleet / city) with button placements per `coverage.md §2 'Unit map'`:

- Army selection: `Supply army` / `Recruit mercenaries` / `Transfer units` / `Split army` / `Join armies` / `Change units` / `Disband army`
- Fleet selection: `Supply fleet` / `Repair fleet` / `Transfer ships` / `Split fleet` / `Join fleets` / `Scuttle fleet`
- City selection: `Fortify city`

Live evidence: `SS:FI_b1_01_main.png` (SHA-256 `4651bc79d81e259fb8eaeeed3949a2e0943a6ceab9f9e539b8389aa3fd3870dd`, `MANIFEST-batch1.txt`); scroll-bars visible. Help topic 51 ("Unit map").

### UM02 — City details panel

`TInformation_ShowCityDetails @ 0x0043be5c` (function_list.tsv). The panel reads `pop`, `max_pop`, `allegiance`, `loyalty`, `fort`, `tribute`, `supply` (and `+0x44A tax` / `+0x44C cities_count` / `recruitment queue slots`).

Live evidence: `SS:FI_b1_24_city_left_click.png` (SHA-256 `bff18925a7c15f8f352bdc2b1690d65d8d6fcd51865f77e6b793ac8e20b852d9`). Verbatim from the inventory: *"Rome: population 181,000 (100%), loyalty excellent, fortification 78% (14,000), tribute 317 talents, supply 990 tons"*. The (14,000) figure is per `docs/rules-digest.md §4`: *"the queue is the garrison, shown as '78% (85,000)'"* — the screenshot shows `14,000` instead, indicating either a different save or a transcription difference; carrying as an open note.

Help topic 58 ("Cities") reproduces the row labels. Form-level `TInformation` (already cited in the M01–M06 draft under M03).

### UM03 — Own army panel

`TInformation_ShowArmyDetails @ 0x0043c33c` (function_list.tsv). Live evidence: `F:2026-10-02-unit-map-mouse-orders-and-tax-range.md (c) (C_1_left_click.png, C_AFTER_RIGHT_CLICK.SAV)`. Reads army record fields: `+0xA money`, `+0xB moves`, `+0xC supply`, `+0xD morale` / `+0xE cell`. Help topic 59 ("Armies").

### UM04 — Foreign army panel

Same dispatcher `TUnitMap_SelectUnit @ 0x004466cc`; `TInformation_ShowArmyDetails` is also called with a `foreign_nation` flag — foreign-army panel suppresses Moves / Supply / Morale / Money fields. Live evidence per inventory: *"R:ptolemy-run-ui-inventory-and-leader-draw.md §1 (frame IP1 021 t=140)"* — a foreign-army panel; the screenshot is from the ptolemy-run experiment. Help topic 59 ("Armies"): *"If you left-click an army you will be shown certain details about it"*. `[derived]` carry-over (no direct Wine screenshot at this exact row's evidence level).

### UM05 — Fleet panel

`TInformation_ShowFleetDetails @ 0x0043c890` (function_list.tsv). The function's literals (rows 152, 154, 155, 162, 164, 165, 166 of `dump_string_literals.v2.tsv`):

| Literal | row | role |
|---|---|---|
| `"Fleet of "` | 152 | header / nation name |
| `"Ships -"` | 154 | ship count label |
| `"Repair -"` | 155 | condition label |
| `"Capacity -"` | 162 | army-capacity label |
| `"Sea-"` | 164 | sea-state label |
| `"calm"` | 165 | Sea=calm value |
| `"rough"` | 166 | Sea=rough value |

Live evidence: `C:§1 'Fleet: move, embark, disembark, supply, repair, split, join, transfer, scuttle' (click the fleet marker, SEL_FLEET)`. Help topic 63 ("Fleets").

### UM06 — Unit list (right click)

`TInformation_ShowArmyUnits @ 0x0043cdd8` (own-army unit list); `TInformation_ShowFleetUnits @ 0x0043cf0c` (fleet-carried-army unit list — same fields). Live evidence: `F:2026-10-02-unit-map-mouse-orders-and-tax-range.md (c) (six units listed, no window opened; C_AFTER_RIGHT_CLICK.SAV)`. Help topic 51 ("Unit map"): *"If you right-click one of your armies (or fleets carrying an army) you will be shown a list of the units in that army."*

### UM07 — Mercenaries at a city (right click)

`TInformation_ShowCityUnits @ 0x0043cc40` (function_list.tsv). The function's literals (rows 168, 169 of `dump_string_literals.v2.tsv`):

| Literal | row | role |
|---|---|---|
| `"Mercenaries at "` | 168 | header, followed by city name |
| `"There are no mercenaries at "` | 169 | rejection when no offer |

Live evidence: `SS:FI_b1_25_city_right_click.png` (SHA-256 `7ee3017036e83c259503028fe7498f222a01b7c5269361a34e2f03c5cb5b1259`). Verbatim from inventory: *"There are no mercenaries at Rome" (when none is on offer, seen at Rome)*. Help topic 51 ("Unit map"): *"If you right-click any city you will be shown which mercenary units, if any, are available at that city."*

### UM08 — Scroll bars of the Unit map

Form-level `ScrollBarH` / `ScrollBarV` on `TUnitMap`, both with `OnScroll=UnitMapScrolled`. Function `TUnitMap_UnitMapScrolled @ 0x00446348`. Live evidence: `SS:FI_b1_01_main.png` (scroll bars visible). `[derived]` carry-over — the bar appearance is standard Delphi and not pinned per-row. Help topic 51.

### UM09 — Information window

Form `TInformation` with `ScrollBarV` + `ScrollBarH`. Functions:

| Address | Function |
|---|---|
| `0x0043b394` | `TInformation_PaintForm` |
| `0x0043b8b4` | `TInformation_FormScrolled` |
| `0x0043be5c` | `TInformation_ShowCityDetails` (UM02) |
| `0x0043c33c` | `TInformation_ShowArmyDetails` (UM03/UM04) |
| `0x0043c890` | `TInformation_ShowFleetDetails` (UM05) |
| `0x0043cc40` | `TInformation_ShowCityUnits` (UM07) |
| `0x0043cdd8` | `TInformation_ShowArmyUnits` (UM06) |
| `0x0043cf0c` | `TInformation_ShowFleetUnits` (UM06) |
| `0x0043ba7c` | `TInformation_ShowNationStatus` (UM09 alt mode / row N03 / row S05 cover the same dispatcher) |
| `0x0043b940` | `TInformation_PrintNews` (row S01) |

Live evidence: `SS:FI_b1_01_main.png` (the Information window visible with the news log on screen); `FI_b1_20_nation_carthage.png` / `FI_b1_21_nation_rome.png` (N03 / UM09's nation-status mode — already cited in the N01–N03 draft). Help topic 51 ("Unit map") — the information window is one of the four main windows (M03).

## What does not match — three open notes

1. **UM02's `(14,000)` vs `rules-digest.md §4`'s `(85,000)` garrison figure** — the screenshot `FI_b1_24_city_left_click.png` shows `(14,000)` for Rome; the digest's prose says the queue is the garrison and reads `(85,000)`. Either the digest's example is a different save or the screenshot transcription in the inventory is wrong. `[derived]` carry-over; reproducing would need a fresh `tests/test_orders.py` fortify-army test on the run-0 start save to confirm.
2. **UM04's foreign-army panel** is `[derived]` (no direct Wine screenshot at this evidence level). The cited IP1 frame from the ptolemy-run is the closest reproduction; carrying forward.
3. **UM08's scroll-bar appearance / handler-against-mouse events** aren't in `dump_string_literals.v2.tsv` — the standard Delphi behaviour is cited as `[derived]`. Reproducing would need capstone on `TUnitMap_UnitMapScrolled` to confirm the scroll-delta math.

## Method

- **Form + function extraction.** Same toolchain. Twelve `TInformation_*` handlers and four `TFortifyCity_*` + `TUnitMap_Fortify` enumerated above; addresses reproduced verbatim from `function_list.tsv`.
- **`TUnitMap_FormScrolled`** is the same name on a different form (`0x0043b8b4`, in `TInformation`). The `TUnitMap` form-level scroll is `TUnitMap_UnitMapScrolled @ 0x00446348`. Recorded separately to avoid confusion.
- **Reproduction cells.** Three `MANIFEST-batch1.txt` screenshot hashes recorded above. The `coverage.md §1 / §2 / §3` rows that are cited are reproduced verbatim.
- **Tag scheme.** Same as the other drafts.

## Inferences

- **`TInformation` is a single form with eight sibling Show-handlers** (ShowCityDetails / ShowArmyDetails / ShowFleetDetails / ShowCityUnits / ShowArmyUnits / ShowFleetUnits / ShowNationStatus / PrintNews). Each `TUnitMap_*` row's selection (UM02 / UM03 / UM04 / UM05 / UM06 / UM07 / UM09's nation-status mode / S01's News log) routes to one of these. A reproduction wires one form, eight mode switches.
- **`TFortifyCity` is the only UC01 form** — it stands alone; no other dialog reuses the form. The six labels (Initial, fortification, 1s, …) plus the spinner / cost / OK button is the entire shape.

## What this does not establish

- UM02's `(14,000)` vs `rules-digest.md §4`'s `(85,000)` reconciliation (`[derived]`).
- UM04's foreign-army panel direct screenshot (`[derived]`).
- UM08's scroll-bar handler specifics (`[derived]`).

## Reproduction

```bash
cd ~/projects/ic2-conquest
grep -E "TUnitMap_(Fortify|UnitMapScrolled)|TInformation_(ShowCityDetails|ShowArmyDetails|ShowFleetDetails|ShowCityUnits|ShowArmyUnits|ShowFleetUnits|PaintForm|FormScrolled)|TFortifyCity_" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -nE "TInformation_ShowFleetDetails|TInformation_ShowCityUnits" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
sha256sum runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_24_city_left_click.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_25_city_right_click.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_01_main.png
```

The form, function and literal extracts are deterministic. Re-running the S03 / S05 / UC01 tests in `tests/test_orders.py` covers the live evidence path.
