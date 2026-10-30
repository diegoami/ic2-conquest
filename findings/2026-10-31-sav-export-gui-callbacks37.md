# SAV export #37, Q2: the tax and rename refreshes write only the current nation's viewport, plus a map-click re-run

**Tags:**
- [code] for the call paths and saved-state writes: decompile and disassembly of the pinned EXE, and a static call
  closure filtered to the blocks the saver streams;
- [confirmed in emulation] for the map-click re-run, executed on the #187 RAM snapshot.

No game was run.

**Task:** research [#37](https://github.com/diegoami/imperial-conquest-2-research/issues/37) Q2 (remake #1191), delegated
2026-10-31: the GUI callbacks still marked UNVERIFIED in
`2026-10-18-sav-export-bound-tax-subset-and-binary-alias-evidence.md`.

## What the saver writes (the yardstick)

`FUN_004484d0` streams exactly these blocks, so "saved state" below means a write inside one of them:

| Block | Size or count |
|---|---|
| map 0x45E870 | +0x15E00 |
| cities 0x479590 | +0x2C5C |
| army table 0x47C1EC | count 0x4A0324 |
| fleet table 0x49C26C | count 0x4A0326 |
| nations 0x474670 | +0x4940 |
| mercenary pool slots 201–250, 0x49DA10 | 50 × 12 |
| news 0x49F994 | count 0x4A031E + 1 |
| 0x49EFE8 | +0x20 |
| 0x49F008 | +4 |
| words 0x4A0320, 0x4A0322, 0x4A0330, 0x4A0332, 0x4A032E | 2 each |
| the main form's geometry 0x4A0338, computed at save time | 8 |
| battle flag 0x4A0B7C and the battle block (0x4A0B74..7D, 0x4A0344 +0x6E0, 0x4A0A24 +0x150) | — |

The selected army and fleet 0x4A0328/0x4A032A and the information panel line 0x4A031C are **not** saved.

## 1. TChangeTax_OK (0x4540B8) → TPremierForm_RefreshForms (0x45BA6C)

- `TChangeTax_OK` writes the current nation's tax, +0x44A (0x474ABA). It then calls `TPremierForm_RefreshForms`, closes
  the dialog (`param_1[0x4A] = 1`, `FUN_0042313c`).
- `TPremierForm_RefreshForms` = `TUnitMap_PaintForm(unit map)` + `TInformation_ShowNationStatus(current nation)`.
- **`TUnitMap_PaintForm` (0x445D38)** writes the current nation's **viewport y +0x486 and x +0x488** (0x474AF6/0x474AF8).
  It reads the two scroll bars (`param_1[0x6F]/[0x70] + 0x100`), then clamps them to
  `0 .. 0x140 − cols − 1` and `0 .. 0x8C − rows − 1` (`FUN_00448fd0`/`FUN_00448fd8`). This matches the tax report's
  measured "refresh also writes/clamps +486/+488".
- `TInformation_ShowNationStatus` writes 0x4A031C (panel line index): not saved.
- **`TUnitMap_PaintForm` ends with `if (form+0x21A ≥ 0) TUnitMap_SelectUnit(form, form+0x21A)`.** It re-runs the map-click
  handler on the highlighted square: §3.
- **Static closure** (`runs/experiments/savexport37/closure.py`, direct calls only), from `TPremierForm_RefreshForms` with
  `TUnitMap_SelectUnit` excluded:
  - 145 functions;
  - the only saved-state writes are the four +0x486/+0x488 stores in `TUnitMap_PaintForm`;
  - 28 functions in it make indirect calls (VCL virtual methods and event pointers) that the closure does not follow.

## 2. The rename path, outer callbacks

- **Entry:** `TUnitMap_ChangeUnitDetails` (0x447644).
  - The army is the unit map's selected army (form `[0x88]`). When a fleet is selected (`[0x89]` ≥ 0), it is the army
    that fleet carries (fleet +0x16), and that index is written back to `[0x88]`.
  - It requires `army ≥ 0` and owner (+4) = the current nation.
  - It then creates the units dialog through `FUN_00424608` (the form-creation helper, class 0x4447F8, into
    `DAT_0045e73c`), and after it returns calls `TUnitMap_UpdateUMSelection`.
- **Inside the dialog:**
  - `TChangeArmyUnits_RenameUnit` (0x444BB0) allows exactly one selected unit, and only a regular one (+0x1EA = 0):
    "You can only rename 1 unit at a time." / "You can only rename regular units.".
  - `TRenameArmyUnit_OK` (0x443F50) copies the edit text into the dialog's copy of the army (dialog +0x1F2 +
    32 × slot) through `FUN_00405b88`.
  - **`TChangeArmyUnits_OK`** (0x445378) writes the current nation's mobilization +0x442 (0x474AB2) and copies the
    whole 656-byte army from the dialog (+0x1DA) to army `[0x75]`. As measured upstream.
- **After the dialog:** `TUnitMap_UpdateUMSelection` (0x446EF4) shows the city, army or fleet details for the
  highlighted square, then `TUnitMap_PaintForm` and `TInformation_PrintInfo`.
- **Static closure** from `TUnitMap_UpdateUMSelection` with `TUnitMap_SelectUnit` excluded: 154 functions, the same
  only saved writes (+0x486/+0x488), the same 28 indirect-call functions.

**So both callbacks end in the same `TUnitMap_PaintForm`.** Their saved writes are:
- the commit itself: tax +0x44A; or mobilization +0x442 plus the army record;
- the current nation's viewport +0x486/+0x488;
- whatever the map-click re-run does.

## 3. The map-click re-run on refresh [confirmed in emulation]

`TUnitMap_SelectUnit` (0x4466CC) is the unit map's click handler. With an army selected (0x4A0328) that has moves and
stands at distance exactly 1 (`FUN_004492a0`), a click on an enemy city or army asks or attacks. The city branch ends in
`FUN_0044b27c`, the army branch in `FUN_0044aee4`, and both may first call the war setter `FUN_00449b40`. Every one of
those branches, and the embark branch, ends with the selected army **reset to −1**. So a later re-run on the same square
cannot repeat them: an own army's own square is at distance 0, and the re-run just re-selects it.

**The enemy-fleet branch is the exception.** It never resets the selected fleet 0x4A032A. Control
(`runs/experiments/savexport37/selectunit.py`, `selectunit-v1/v2.json`):
- the original `SelectUnit` runs twice on the snapshot, the click and then the refresh's re-run on the same square;
- an own fleet (moves 8) is selected next to an enemy fleet on open sea;
- presentation calls are stubbed and MessageDlg answers as scripted;
- in v2 the naval battle `FUN_0044b5d0` and the setter run unmodified.

| Case | Click | Refresh re-run |
|---|---|---|
| at war | naval battle runs; attacker moves → 0; the loser fleet is deleted | **nothing** (moves 0, the square is empty) |
| at peace, answer No | "Are you sure you want to attack this fleet ?" | **the same question again** |
| at peace, answer Yes | question, war set (`FUN_00449b40`), naval battle | **nothing** |

v1, with the battle stubbed, shows the branch structure. v2 shows that the battle's own `moves = 0` (line
`(&DAT_0049c278)[attacker*0xd] = 0`) is what stops a repeat.

**So a tax or rename refresh writes saved state beyond the viewport only in one case:** the player had answered No to
an attack-fleet question, that fleet is still selected and highlighted, and the player now answers Yes to the repeated
question. Without that, the re-run writes nothing saved.

## For the exporter

A tax-only or rename-only edit's serialized effect is:
- **tax:** +0x44A;
- **rename:** army record + +0x442;
- **both:** the current nation's +0x486/+0x488, clamped by the window's map size.

The clamp depends on the unit map's client size (`FUN_00412880`/`FUN_004128c4`): the window geometry, not game state.
The map-click re-run adds nothing in the normal case. Its only writing path needs the extra player answer above.

## What this does not establish

- **The 28 functions with indirect calls** (VCL virtual methods, event pointers) are not followed.
- **No live GUI run:** which square is highlighted, and what is selected, when the tax or units dialog opens is the
  player's doing and was not observed.
- **Native Windows** VCL behaviour.
- **Windows messages:** `TInformation_*` drawing and any message pumping inside the modal dialogs (which could run other
  handlers) are outside the closure.

## Evidence

- Code:
  - `runs/experiments/savexport37/closure.py` (call closure; the saved-block list is read from `FUN_004484d0`);
  - `runs/experiments/savexport37/selectunit.py`.
- Data: `runs/experiments/data/run-exp-savexport37/selectunit-v1.json`, `selectunit-v2.json`.
- Private, not published: the pinned decompile dump and EXE, and the #187 RAM snapshot (paths in `core.py` and
  `closure.py`).
