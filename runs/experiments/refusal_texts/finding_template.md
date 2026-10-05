# The original's refusal texts and their conditions: 57 refusals, 13 prompts, 3 notices, every line from the decompile

**Status:** draft finding from `ic2-conquest`, awaiting promotion. For clone issue `imperial_conquest_2` #721 (the clone words several refusals its own way). Task `docs/tasks/refusal-texts.md`; branch `experiment/refusal-texts`; run `run-exp-refusal-texts` (data `runs/experiments/data/run-exp-refusal-texts/`, binaries in the release of that name, hashes in `SAVES.sha256` and `MANIFEST-*.txt`).

**Tags.** `[derived]` = read from the decompile (function, call line and cited test lines of `all_app_functions.txt`; the functions are kept in `code_extract_refusals.txt`, whose first column is that file's line number). `[confirmed]` = seen in Wine: the box's screenshot, its OCR, and the save before (the control save) and after. The two are never mixed: the catalogue has one column for each. Every play on a **staged** save says so in the plays table (the edited fields are listed there and in `staging_log.tsv`); nothing staged is presented as natural play.

## Answer

1. **The game has 74 message-box calls** (all go through `FUN_0042d750`, the VCL `MessageDlg(Msg, DlgType, Buttons, HelpCtx)`): **57 refusals**, **13 prompts** (Yes / No / Cancel), **3 notices** (an OK box that is not a refusal) and **1 excluded** (the battle screen's Surrender prompt). The 63 call sites that pass a literal text are the 63 literals found; all 63 are catalogued (62 in the three tables, the 63rd is the excluded Surrender prompt); the other 11 sites build their text at run time and are catalogued by their pieces. [derived]
2. **Every refusal is an information box with one OK button** (`mtInformation`, title `Information`) except one: embark's *"The army is too large for this fleet ?"* is passed as type `mtConfirmation` with an OK-only button set, so its title is `Confirm` (row R06, confirmed in play E01). [derived, confirmed]
3. **The five lines the clone words differently** (issue #721), each confirmed in Wine on a save and an unchanged control save: see the plays table, plays UA04, UA05a, UA05b, UF05, D05a, D05b, D06 (rows R01, R03, R04, R16, R36, R37, R41).
   - `You can not split an army containing only 1 unit.` (R01)
   - `These 2 armies combined contain more than 20 units.` (R03) and `These 2 armies combined contain more than 100,000 troops.` (R04)
   - `You cannot join fleets if one is carrying an army.` (R16)
   - `You can only rename 1 unit at a time.` (R36), `You can only rename regular units.` (R37), `This unit is too small to split.` (R41)
4. **When two refusals hold, the first tested is shown, and only one box appears** (the orderings table). Joining armies over 20 units **and** over 100,000 troops shows the **20 units** line (play UA05c); joining fleets over 100 ships **and** with one carrying an army shows the **100 ships** line (play UF05c). The transfer dialog is the exception: its 20-unit and 100,000-troop refusals are an else-if, but the fleet-capacity refusal is a separate second box.
5. **Most refusals drop the order and change nothing; five clamp** (the transfer dialog's three per unit, the disband paths of the transfer and Change units dialogs, Mobilize): the units that pass are still moved or removed and one box follows the loop. The effect column says which.

## Method

- **Code.** `sites.py` finds every call of `FUN_0042d750` in `all_app_functions.txt`, parses the call (first argument, the type in the last argument of `CONCAT31`, the button word) and reads the button-set word at the address the call names from the original `Imperial Conquest 2.exe` (an `mbOK` set is `0x0004`, Yes+No+Cancel `0x000b`). `call_sites.tsv` is the result (74 rows). `make_extract.py` writes the functions that hold a call, and the helpers their tests use, to `code_extract_refusals.txt`. The conditions are read by hand from those functions and cited with their lines (`L<line> «text of the line»` in the tables); the record offsets come from `docs/sav-layout-notes.md` and the research report `decompiled-unit-map-orders-and-record-fields.md`. Each literal is also a NUL-delimited string of the executable.
- **Scan.** `scan_literals.py` lists every string literal of every `T*_*` function (`literals_in_scope.tsv`) and classifies it: a message-box literal, a fragment of a message built at run time, or other (captions, panel labels, resource names). `class_table.py` lists the classes of `delphi_symbols.tsv` with their call counts, so that a class without any call is visible as such.
- **Play.** `play_lib.py` + `scenarios.py` + `run_play.py`: each play loads a save (a staged copy, or an earlier session's save used unedited) in a fresh Wine process on a private display and game folder, writes a **control save** (File > Save as, the state the game holds), issues one order with no box dismissal, captures every box that appears (X window id, title, geometry, Wine's control list, a screenshot of the box and of the screen, two OCR readings), closes it with a tracked click (each box tracked by its X id, three attempts at most), writes an **after save** and compares it with the control byte for byte. Toolbar buttons are found by tooltip (`Game.calibrate_*`), dialog controls by `Game.controls`, menus by OCR (`eog.menu_pick`, `eog.save_as_ocr`); no fixed coordinate is used.
- **Staging.** `play_lib.stage_edit` applies `battles/stage.py` operations (unit lists, city fields, relations) and three more (a fleet's ships, a nation word, an army's moves); the changed bytes are checked to lie inside the declared fields and logged with the source and result hashes in `staging_log.tsv`.
- **Audit.** `claims_audit.py` reads the finding's tables and recomputes each claim from the code extract, the executable, the tracked OCR and play records and the saves; `test_claims_audit.py` shows that a doctored literal, a doctored extract line, a doctored save and a doctored reading each fail it.

## The catalogue

### Counts

{{TABLE:counts}}

Every call line of the extract is catalogued exactly once (the audit checks the sets are equal). The scan of the `T*_*` functions finds the same 63 message-box literals; its 20 fragments (strings of two or more characters; the one-character pieces `s` and `.` are not listed) are the pieces of the 11 built messages, and its 235 other strings are captions, labels and names.

**Exclusions.** X01, the Surrender prompt of `TBattleMap_Surrender` (battles are paused: the task excludes the battle screen). The three `MessageBoxA` calls of the program (`FUN_00403f7c`, the Delphi runtime-error handler; `FUN_00406618` and `FUN_0042479c`, library code) are not reached by any order and are not message-box calls of the game's forms; they are not counted. The three notices N01-N03 are OK boxes that report, not refuse. The `FUN_004597d8` strings (*"An army of yours cannot afford to pay its mercenary units."*) go to the news list, not to a box.

### Classes searched

{{TABLE:classes}}

Every class of the symbol list was searched, so the classes with 0 calls are real: the supply dialogs (`TAFSupply`), `TFleetToFleet`, `TRepairFleet`, `TFortifyCity`, `TSplitArmyUnit`, `TRenameArmyUnit`, `TChangeTax`, `TBalanceSheet` and the information window have **no message-box call**: their limits (a supply cap, a repair cap, a spinner range, an empty name) are not refusals with a line; the dialogs clamp the value. [derived, by absence]

### Refusals

The literal column is the call site's string, byte for byte, as the decompile prints it with C escapes undone (`\'` is an apostrophe) and as it stands in the executable. The apostrophe of R48 and the space before every `?` and `!` are the original's. "Test order" is the order in which the function runs its tests, so the first failing test is the box the player sees.

{{TABLE:catalogue}}

### Prompts (Yes / No / Cancel)

A prompt is `mtConfirmation` with Yes, No and Cancel; the call returns 6 for Yes and the code acts only on 6. The disband prompts build their text from the count of selected units (`unit` plus `s` when more than one).

{{TABLE:prompts}}

### Notices and the exclusion

{{TABLE:notices}}

### Orders that fail without a box [derived]

- Join armies with no army one tile away (`L46975 «if (-1 < (short)uStack_10) {»`), Join fleets with no partner fleet (`L47232 «if (-1 < (short)local_10) {»`): nothing happens.
- Split army after R01 passes: no free tile next to the army, or 198 armies already: nothing happens (`L48725 «(-1 < (short)local_12) && (DAT_004a0324 < 0xc6)»`).
- Recruit mercenaries with no offer one tile away: the button does nothing (`L46882 «if (-1 < (short)local_14) {»`).
- Embark: an army without moves, a fleet that is not one tile away, or a fleet already carrying an army: the click only selects the fleet (`L46592 «if ((bVar4) && ((&DAT_0049c282)[*(short *)(param_1 + 0x224) * 0xd] == -1)) {»`).
- Rename unit, Split unit with no unit selected, Join units with fewer than two, the transfer and disband paths with nothing selected, Recruit unit with no unit type chosen: nothing happens (`L45489 «if (iVar2 == 1) {»`, `L45609 «if (1 < iVar6) {»`, `L55959 «if (-1 < *(short *)(param_1 + 0x23e)) {»`).

### Orderings

{{TABLE:orderings}}

The transfer dialogs run the tests per selected unit, last slot first, and open their boxes after the loop: the 20-unit box if any unit hit the 20-unit test, else the 100,000-troop box if any unit hit that, and then, separately, the fleet box (`L44154 «if (bVar2) {»`, `L44158 «else if (bVar3) {»`, `L44163 «if (bVar4) {»`). The rows R25-R27 of the mercenary dialog and R46-R48 of the recruit dialog are plain if/else ladders in the order listed.

## Plays

Every play ran on the private Wine game (`run-exp-refusal-texts`, display :742). **A play on a staged save is labelled STAGED with the fields it changed**; an unedited earlier save is `fixture, unedited`. The two UF05 plays that embark an army issue a normal embark order before the control save (so the control already holds the cargo). The OCR column is the tesseract reading of the box (`ocr_b*.jsonl`, 3x grey psm 6, and `ocr_reread.jsonl`); it is noisy (an icon read as a digit, `nat` for `not`), and the audit accepts a reading only when it matches the row's literal at a ratio of 0.85 or more. The exact text is the code's literal; the OCR proves the box that appeared and which row it was.

{{TABLE:plays}}

**The two UI bytes.** A control-to-after difference of one or two bytes at nation 0 `+0x486`/`+0x488` appears whenever an army is selected or a dialog is opened and closed (play SEL01 selects an army and issues no order: it shows the same bytes); these words lie in the nation record's UI block (`+0x46B`..`+0x48F`, `docs/sav-layout-notes.md` section 5, "UI fields"), not in an army, fleet, city or economy field. The audit requires every differing byte of every play to lie in that block. No refusal changed an army, a fleet, a city, a relation, a treasury or a queue.

## The clone's lines, and the original's

Issue #721 lists the clone's lines; the original's lines are the catalogue's. The clone's wording is quoted as the issue gives it (not re-read here: the clone repository is read only). The issue's own third join line, `... troops ...`, is an ellipsis there. The task text pairs `D05` with the too-small split and `D06` with rename; the inventory's rows are the other way (D05 Rename unit, D06 Split unit); the table uses the inventory's numbering and all three lines are covered.

{{TABLE:clone}}

Further differences the issue lists as already the clone's words (40 units, 100 % mobilisation, *"You cannot mobilise a unit at this time."*, the trade refusals, the 100-ship join, the disband-army and repair-fleet refusals, the docked-fleet attack, the embark capacity box) match rows R46, R47, R49, R50-R54, R15, R05, R13-R14, R07 and R06 respectively: the clone should compare each against these literals, spaces included (R06 and R07 keep a space before `?` and `!`).

## What this does not establish

- **The OCR is not the literal.** The play proves that the box of that row appeared (title, the row's line at a ratio of 0.85 or more, the screenshot is kept); the exact bytes are the call site's literal and the executable's string. A reader can compare the screenshots in the release.
- **Rows without a play are `[derived]` only.** The catalogue's play column names every play; the rows without one (for example R10 the enemy-city mercenary refusal, R19 no free fleet slot, R22 a city under siege, R27, R48 fortification below 75, R49 Mobilize, R55-R57 Build fleet, the transfer's fleet refusals R30 and R33) were not reached: they need an enemy next to a city, a full fleet table, a queue near-falling fortification, a nation without a coast, or an army aboard a fleet in the transfer dialog, and no earlier save had them. Their conditions are read from the code only.
- **Helper functions are read by what they do, not named.** `FUN_004494e4` (an own city within one tile), `FUN_004492a0` (distance one), `FUN_00449d64` / `FUN_00449dd8` (the partner army / fleet), `FUN_00449d08` (a mercenary offer one tile away), `FUN_004497cc` (an enemy army next to a city), `FUN_004496e0` (a free coastal city) are described from their code in the extract; their exact edge cases (for example how many tiles around a city count as "near") were not tested beyond the plays.
- **The type size limit** that Split unit and Join units compare against (`DAT_00478fca`, field +10 of a 40-byte unit-type record) is named from its use; its values per type were not tabulated here (the plays use troop counts far below and far above it).
- **The after save proves "nothing changed" for the fields the save holds**, not for the game's memory outside the save (the selected army, the open dialogs).
- **Natural versus staged.** Most plays use staged unit lists, fleet sizes and relations to make a refusal reachable; the refusal logic does not depend on how the state arose, but only plays on unedited saves (UA04, UF05b's source fleets, the F04 scuttle prompt, E01, S01) show it on a natural position.
- **Same-session behaviour of the UI.** Dialogs were closed with Cancel or OK after each play; a later order in the same session was never tried.

## Reproduce

`python3 runs/experiments/refusal_texts/fetch_archive.py` (the release's archives into `artifacts/run-exp-refusal-texts/`), `python3 runs/experiments/refusal_texts/claims_audit.py`, `python3 -m unittest runs/experiments/refusal_texts/test_claims_audit.py`. The plays: `run_play.py BATCH ID...` (ids in `scenarios.py`), after `setup/setup.sh` and a copy of the game folder (`~/ic2-work-refusals`).
