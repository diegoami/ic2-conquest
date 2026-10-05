# The Information window: every field, its formula, and the number-to-word bands

**Status:** draft finding from `ic2-conquest` (branch `experiment/info-window`), awaiting promotion. Task: `docs/tasks/info-window.md`. For the clone's v0.5.0 task T140 (imperial_conquest_2 #728, bug #718, foreign-nation panel #614). **Wine-only where a run is cited:** the runs are the original `Imperial Conquest 2.exe` (the normal build) under Wine 9.0 on Xvfb `:730`, own copy of the game folder, crafted copies of fixture saves only (L1 edits through `runs/experiments/info_window/stage.py`). Tags: `[R-code]` read from the decompile, `[O]` observed in play (a save and a screenshot, bare file names, in the release `run-exp-info-window`), `[D]` derived, never presented as observed. Code citations `F:<n>` are line numbers of `all_app_functions.txt` in the ReTools folder (function and address in the row).

## Answer

- **Priority (a), the number-to-word bands.** Every word comes from the DAT, not from the exe: the tables are BSS filled by the DAT loader `FUN_004481a0` in a fixed read order, so their DAT offsets are computed, not searched (quality `0x1F6CA`, unity/loyalty `0x1F738`, relations `0x1F800`). Unity and loyalty share one 11-byte table and differ only in the divisor (unity `div 100`, loyalty `div 10`, both truncating); morale is the same table read from entry 4 with index `(m - 51) sar 2`; quality is an index (no band). Sections "Band tables" give every threshold with its words; **36 of 41 edges are confirmed on both sides in play** and the rest are [derived] with the reason.
- **Priority (b), the fortification bracket** is the sum of `troops` over **all** of the controlling nation's recruit slots at that city **whatever their state**, shown only when positive, on foreign cities too (row C07). The rules digest's "the queue is the garrison" is right; the help's "conscripts currently being trained" is too narrow (a state-24 trained unit counts: `61% (3,000)` for a state-0 1,000 and a state-24 2,000 at one city).
- **Priority (c), Regulars cost / Mercenary pay** (rows A10, A11): per unit slot `s = i16(trunc(troops / 200) x price[type])` (the product is stored in a signed 16-bit `short`, F:41084; i16 = wrap to signed 16 bits), then regulars (label 0) `Regulars cost = sum s` and mercenaries (label not 0) `Mercenary pay = sum trunc((s x quality) / 5)` (F:41086, 41089); the two sums are 32-bit and not narrowed; with the DAT prices (1-4) the narrowing never changes a result, and it is documented so a clone with other prices copies it; price is the unit-type table's quarterly price (`DAT_00478FD4`, record `+0x24`); plain integers, own army only. Recomputed for every own army captured (staged morale, units, qualities, troops 199/399/200 for the `div 200` truncation, regular and mercenary slots) with 0 mismatches in `claims_audit_lines*.tsv`.
- **Priority (d), the fleet's Sea word** (row F08) is `calm` when the fleet's `+0x18` field is 0, otherwise `rough`. No rule on the panel decides it: the field is the map code under the fleet, cleared and re-rolled by the weekly weather overlay and copied from the destination cell by every fleet step (see the row).
- **Priority (e), the foreign-nation panel** (rows N01-N12): exact formats are in the nation table; **"peace" really shows blank** (relation 0, and any value `<= 0`, prints nothing; the word `peace` exists in the DAT table but is never printed); the nation's Population is the stored `+0x430` field, **3000 x the sum of its cities' populations in thousands** (so Rome shows 2,577,000 while its city panels add to 859,000); Mobilized and Treasury are blank for a foreign nation.
- **Coverage:** functions 7; items 234 (literals 78, helpers 46, data symbols 110); mapped to a row 227; excluded with a reason 7; UNACCOUNTED 0 selftest (rows N06, C05 removed): 6 unaccounted -> PASS
- **Claims audit:** captures 147; row statuses: CLIPPED-right 29, CORRECTED-OCR 23, EXCLUDED-listed 11, NOT-MODELLED-OUTPUT 1, OK 1570, OK-ordinal 13, SCROLLBAR-ARTIFACT 17; FAILING (MISMATCH+MISSING+EXTRA+NOT-MODELLED) 0 band samples 501; band MISMATCH 0 (`runs/experiments/info_window/audit.py`: every captured panel line recomputed from the code model and compared with the OCR of its screenshot; every band row compared as expected word versus seen word).

## Method

- **Code read.** The seven routines `TInformation_ShowNationStatus` 0x0043BA7C, `ShowCityDetails` 0x0043BE5C, `ShowArmyDetails` 0x0043C33C, `ShowFleetDetails` 0x0043C890, `ShowCityUnits` 0x0043CC40, `ShowArmyUnits` 0x0043CDD8, `ShowFleetUnits` 0x0043CF0C and the helpers they call were read from `all_app_functions.txt` (`show_fn.py` of the inventory task). `TInformation_PaintForm` (0x0043B394) draws each 61-byte line by splitting it at its **first `-`**: the left part at x, the right part 100 pixels to the right; so every `Caption -value` string below is a two-column row, and a line without a `-` is one string. A line that starts with `   (` is drawn red (the conquered-nation row).
- **Tables from the DAT.** `FUN_004481a0` (ReTools `scratch/datload.txt`) reads the DAT sequentially: the map `0x15E00`, the cities `0x2C5C`, 15 armies, 2 fleets, 16 nations, then the tables at `0x00478FB0`, ... (read sizes and addresses in `panel_model.LOADER`). The running sum of the read sizes puts `DAT_0047938C` at DAT offset `0x1F6CA`, which is where the first `not ready` is (a cross-check of the loader read against the file, `code_word_tables.tsv`). `panel_model.py` rebuilds the memory image (unfilled bytes are 0) and implements every panel, citing the decompile lines; it reproduces what the game does when an index runs past a table (loyalty -10 prints `ite`, from the end of the previous table).
- **Staging.** For every band, saves were crafted with the value on each side of every edge (`batch_a*.py`, one value per city, nation, army or fleet, so one save carries many edges), opened on the normal build, the object clicked (left click for the details panel, right click for the unit list or the mercenary list) and the Information window cropped (`import -crop`, 330 x 730) and OCR'd (tesseract). Every panel line is compared row by row, exactly, with the model (`rowcompare.py`, `audit.py`). The statuses the audit can assign: `OK`, `OK-ordinal` (the OCR reads the 1 of `1st` as `l`), `CLIPPED-right` / `CLIPPED-left` (only for a list row whose pixel extent is individually evidenced to touch the window edge, `row_extents.tsv`, with at least 25 visible glyphs and a strictly shorter exact prefix/suffix; partial evidence, no band evidence), `CORRECTED-OCR` (a glyph misread, each row listed with a reason and eye check in `ocr_corrections.v2.tsv`), `NOT-MODELLED-OUTPUT` (real game output the model does not produce, listed per row in `game_output_differences.v2.tsv`; never counted as a successful comparison), `SCROLLBAR-ARTIFACT` (the scroll-bar arrows read as text, each listed in `scrollbar_artifacts.tsv`), `EXCLUDED-listed` (`capture_exclusions*.tsv`), and the failing `MISMATCH`, `MISSING`, `EXTRA`, `NOT-MODELLED` (a capture kind with no model and no listed exclusion). Short rows, headers and fully visible rows must match exactly. Words were also **checked by eye** on contact sheets of the cropped word lines (loyalty, unity, morale, tribute, sea) and on the scrolled unit lists (quality): no disagreement with the OCR.
- **One caveat found on the way.** After File > Open the nation panel is not refreshed when the same nation is chosen again (it showed the previous save's values); batch a7 captured it that way, four shots are listed in `capture_exclusions.tsv` and were re-captured in batch a7b after choosing another nation first. Six first-run nation shots (batch a3, rows 9-14 clicked at the wrong menu pitch) are excluded by the audit because their panel names another nation than the one staged; they stay in `captures.tsv`.
- **Rule 6.** Text outputs under `runs/experiments/data/run-exp-info-window/` (never overwritten; versions as `.vN`), binaries in the release `run-exp-info-window` as per-batch tar.gz with `MANIFEST-<batch>.txt` and `SAVES.sha256`.

## The nation panel (N03 of the inventory)

| id | line | caption | source field | formula | format | shown when | evidence |
|---|---|---|---|---|---|---|---|
| N01 | 0 | Nation | nation record +0x00 (11-byte string), `sav.parse_nation` name | none | text | always | [R-code] F:40815 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N02 | 1 | Leader | nation +0x0B (string at 0x0047467B), `leader` | none | text | always | [R-code] F:40817 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N03 | 2 | Capital | city name (city record +0x00) of the city index in nation +0x444 (0x00474AB4), `capital` | name[capital] | text | always (a capital of -1 would read before the city table: not staged) | [R-code] F:40819 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N04 | 3 | Cities | nation +0x446 (0x00474AB6), `cities_count` | none | decimal, no separators (`Str`) | always | [R-code] F:40823 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N05 | 4 | Population | nation +0x430 (0x00474AA0, int32), `wealth` in sav.py | none: the field itself is sum(city pop in thousands) x 3000 (nation-tax-base-and-city-economy-fields.md; Rome 859 x 3000 = 2,577,000 and Carthage 1607 x 3000 = 4,821,000 in BASE.SAV) | thousands separators; value copied from index 3 of a 14-char field, so a negative prints without its sign; 12-char field with trailing blanks; a value of 10^9 or more prints junk after the digits | always | [R-code] F:40826 (ShowNationStatus); [O] `A8_cur1_nation00.png` |
| N06 | 5 | Unity | nation +0x440 (0x00474AB0), `unity` | word = table[ trunc(unity / 100) ] | word, 11-byte table at DAT_004793fc (band table 1) | always | [R-code] F:40828 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N07 | 6 | Tax rate | nation +0x44A (0x00474ABA), `tax` | none | decimal + "%" | always | [R-code] F:40834 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N08 | 7 | Mobilized | nation +0x442 (0x00474AB2), `mobilization` | none | decimal + "%" | only when the nation shown is the current nation (DAT_004a0320); otherwise the line is two blanks | [R-code] F:40840 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N09 | 8 | Treasury | nation +0x438 (0x00474AA8, int32), `treasury` | none | thousands separators (FUN_00448f3c); a negative prints as `- 1,500` (minus, blank, digits); then " talents" | only for the current nation; otherwise two blanks | [R-code] F:40843 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N10 | 9 | (spacer and heading) | literal | none | a blank line, then `      INTERNATIONAL RELATIONS` (six leading blanks) | always | [R-code] F:40852 (ShowNationStatus); [O] `A3_nation_00_Rome.png` |
| N11 | 11-26 | <other nation name> (16 rows, one per nation) | name of nation m (+0x00) at the left; relation = shorts at this nation +0x26 + 2m (0x00474696), `relations` | word = table6[ relation ] only when relation > 0 | name, then `  -`, then the 6-byte word of DAT_004794c8 (`peace` `trade` `ally ` `war  `); the painter splits the line at the first `-` | the nation's own row is two blanks; relation <= 0 prints nothing, so peace (0) is blank; values >= 6 read other memory | [R-code] F:40869 (ShowNationStatus); [O] `A3_nation_01_Carthage.png` |
| N12 | 11-26 | ( <name> conquerred by <name> ) | row is chosen when nation m's unity (+0x440) == 0; the conqueror is nation m +0x44E (`conquered_by`) | none | `   ( X conquerred by Y )` (sic); drawn in red | unity of nation m is 0 | [R-code] F:40860 (ShowNationStatus); [O] `A3_nation_01_Carthage.png` |
| H1 | - | helpers: string copy / append, number to text, line buffer | FUN_00405B00 (strcpy), FUN_00405BC8 (strcat), FUN_004028C4 + FUN_00402978 (Str(v) to a C string), `TInformation_PrintInfo` (draws the 61-byte lines of DAT_0049F00C; line count DAT_004A031C) | none | see N05, N09 for the three thousands formatters | always | [R-code] F:40815 (ShowNationStatus) |

Notes: the relations row of nation `n` lists nation `m`'s name and **nation n's own relation value toward m** (`n`'s record, `+0x26 + 2m`); the conquered test uses nation m's unity (0) and m's `+0x44E`. A conquered nation's menu item is greyed, so its own panel cannot be opened (screenshot `t4_menu.png`, in the release manifest, checked by eye; it is a menu shot, not a panel capture in `captures.tsv`).

## The city panel (UM02), left click on any city tile, own or foreign

| id | line | caption | source field | formula | format | shown when | evidence |
|---|---|---|---|---|---|---|---|
| C01 | 0 | City | city record +0x00 name (0x00479590 + 0x22 i); index from the clicked tile by FUN_004498d8 (position at +0x0E, +0x10) | none | name, plus `  (capital of <controller>)` when the city index is some nation's capital (+0x444), the name printed is the CONTROLLER's (+0x12), not the nation whose capital it is | always | [R-code] F:40903 (ShowCityDetails); [O] `A6_city097_Cales.png` |
| C02 | 1 | Controlled by | city +0x12 (0x004795A2), `owner` | none | nation name | always | [R-code] F:40912 (ShowCityDetails); [O] `A1_city_085_Rome.png` |
| C03 | 2 | Allegiance to | city +0x14 (0x004795A4), `allegiance` | none | nation name | always | [R-code] F:40914 (ShowCityDetails); [O] `A1_city_120_Heraclea.png` |
| C04 | 3 | Population | city +0x1C (0x004795AC) `pop` (thousands) and +0x1E (0x004795AE) `max_pop` | pop x 1000;  then `(` trunc(pop x 100 / max_pop) `%)` | thousands separators in a 12-char field (so a gap), then `(nn%)` joined to it | always | [R-code] F:40917 (ShowCityDetails); [O] `A1_city_085_Rome.png` |
| C05 | 4 | Loyalty | city +0x16 (0x004795A6), `loyalty` | word = table[ trunc(loyalty / 10) ] | word, 11-byte table at DAT_004793fc (the same bytes as unity) | always | [R-code] F:40925 (ShowCityDetails); [O] `A1_city_085_Rome.png` |
| C06 | 5 | Fortification | city +0x1A (0x004795AA), raw field (`fort` and `fort_pending` in sav.py are its split) | raw < 101: raw;  raw >= 101: raw mod 100 | decimal + "%"; when raw >= 101 also `  (under construction)` | always | [R-code] F:40928 (ShowCityDetails); [O] `A1_city_085_Rome.png` |
| C07 | 5 | the number in brackets after the fortification | the controller's 40 recruit slots, record +0x2E4 + 8k: slot +4 (troops, 0x2E8) where slot +6 (city, 0x2EA) == this city index | sum of troops over ALL matching slots, whatever their state (a trained state-24 unit counts); shown only when the sum > 0 | `   (` thousands-separated sum `)` appended to the fortification text | own or foreign city alike; slots of other nations never count | [R-code] F:40921 (ShowCityDetails); [O] `A2_city_090_Alba Fucens.png` |
| C08 | 6 | Tribute (own city) | city +0x20 (0x004795B0) `tribute`, via FUN_004498b0 | trunc(tribute x pop / max_pop), as a 16-bit value | decimal + `  talents` | city controlled by the current nation | [R-code] F:40963 (ShowCityDetails); [O] `A1_city_085_Rome.png` |
| C09 | 6 | Tribute (foreign city) | city +0x20 `tribute`, unsigned 16-bit | u <= 10 `poor`; 11-30 `moderate`; 31-100 `rich`; 101-10000 `very rich`; above 10000 no word is set and the talents number text of C08 stays (so 10001 prints `10001`, 40000 prints `-25536`) | the four literals | city NOT controlled by the current nation | [R-code] F:40980 (ShowCityDetails); [O] `A2_city_004_Banasa.png` |
| C10 | 7 | Supply | city +0x18 (0x004795A8), `supplies` | none | decimal + `  tons` | own city only; otherwise one blank | [R-code] F:40987 (ShowCityDetails); [O] `A1_city_085_Rome.png` |

## The army panel (UM03 own, UM04 foreign), left click on an army

| id | line | caption | source field | formula | format | shown when | evidence |
|---|---|---|---|---|---|---|---|
| A01 | 0 | Army of | army record +4 (0x0047C1F0) `owner`; the army is found from the clicked tile by FUN_00449920 (position, owner >= 0) | none | `Army of <nation>` | always | [R-code] F:41033 (ShowArmyDetails); [O] `A4_army_00_left.png` |
| A02 | 1 | Moves | army +6 (0x0047C1F2) `moves` | none | decimal | own army; foreign: caption only | [R-code] F:41037 (ShowArmyDetails); [O] `A4_army_03_left.png` |
| A03 | 2 | Supply | army +10 (0x0047C1F6) `supplies`; total troops from FUN_0044A698 | tons; percent = trunc(supplies x 10000 / total troops) (a total of 0 counts as 1) | decimal + ` tons  (` pct `%)` | own army | [R-code] F:41046 (ShowArmyDetails); [O] `A4_army_00_left.png` |
| A04 | 3 | Morale | army +14 (0x0047C1FA) `morale` | i = m - 51; if i < 0 then i = m - 48;  word = table[ i sar 2 ] | word, table at DAT_00479428 (= the unity table from entry 4; band table 3) | own army | [R-code] F:41052 (ShowArmyDetails); [O] `A4_army_03_left.png` |
| A05 | 4 | Money | army +12 (0x0047C1F8) `money` | none | decimal + ` talents` | own army | [R-code] F:41062 (ShowArmyDetails); [O] `A4_army_00_left.png` |
| A06 | 5 | Terrain | army +8 (0x0047C1F4) `cell`, the map code under the army | none | name from the 14-byte table at DAT_004792e4 (`Sea` `Sea` `Plain` `Desert` `Forest` `Mountains`, then `River` x6) | cell >= 0 (embarked armies have -1: no Terrain line, every later line moves up one) | [R-code] F:41071 (ShowArmyDetails); [O] `A4_army_01_left.png` |
| A07 | b+1..b+5 | <unit type> (5 lines: Light infantry, Heavy infantry, Archers, Light cavalry, Heavy cavalry) | the 20 unit slots at army +0x10 + 0x20 k: type +2, troops +4 | sum of troops of the slots of that type (all 20 slots) | `<type name>-` then the sum in the 12-char thousands field (FUN_00448f9c); the type name is the 16-byte string of DAT_00478fb0 + 0x28 t | always (also for a foreign army); b = 6 with Terrain, 5 without; line b is blank | [R-code] F:41030 (ShowArmyDetails); [O] `A4_army_00_left.png` |
| A08 | b+6 | Total troops | sum of troops (+4) of the 20 slots (FUN_0044A698; 1 if the sum is 0) | none | thousands separators (12-char field) | always | [R-code] F:41107 (ShowArmyDetails); [O] `A4_army_00_left.png` |
| A09 | b+7 | No. of units | FUN_0044A66C: (index of the LAST slot with troops > 0) + 1 -- not a count when a slot in the middle is empty | none | decimal | own army | [R-code] F:41111 (ShowArmyDetails); [O] `A6_army1_left.png` |
| A10 | b+9 | Regulars cost | slots with label (+0) == 0; troops +4, type +2; price = DAT_00478FD4 + 0x28 t (unit-type record +0x24, quarterly price) | per slot  s = i16( trunc(troops / 200) x price[type] )  -- the product is stored in a signed 16-bit `short` (F:41084), then  Regulars cost = sum of s  (32-bit sum, not narrowed). With the DAT prices 1-4 and troops <= 32767 the narrowing never changes a result (163 x 4 = 652) | decimal + `  talents per quarter` | own army | [R-code] F:41117 (ShowArmyDetails); [O] `A4_army_00_left.png` |
| A11 | b+10 | Mercenary pay | slots with label (+0) != 0; quality +6; same price | per slot the same narrowed  s = i16( trunc(troops / 200) x price[type] ),  then  Mercenary pay = sum of trunc( (s x quality) / 5 )  (int product of the narrowed s and the quality, signed truncating division F:41089; 32-bit sum, not narrowed) | decimal + `  talents per quarter` | own army | [R-code] F:41122 (ShowArmyDetails); [O] `A4_army_02_left.png` |

**Foreign army** (the same routine; every `own` condition is false): lines 1-4 (Moves, Supply, Morale, Money) show only their captions, Terrain and the five type lines and Total troops are shown, and No. of units, Regulars cost and Mercenary pay do not exist (the last line index is `b + 6`). A left click on a foreign army does not select it (`SEL_ARMY` stays -1) and a right click on it prints nothing new: the left-click panel stays [O] `A5_foreign_army2_left.png`, `A5_foreign_army2_right.png`, `A5_foreign_army7_left.png`, `A5_foreign_army4_left.png`.

## The fleet panel (UM05), left click on a fleet marker

| id | line | caption | source field | formula | format | shown when | evidence |
|---|---|---|---|---|---|---|---|
| F01 | 0 | Fleet of | fleet record +8 (0x0049C274) `owner`; the fleet is found from the tile by FUN_00449970 | none | `Fleet of <nation>` | always | [R-code] F:41177 (ShowFleetDetails); [O] `A5_f5a_fleet2_left.png` |
| F02 | 1 | Moves | fleet +12 (0x0049C278) `moves` | none | decimal | own fleet; foreign: caption only | [R-code] F:41181 (ShowFleetDetails); [O] `A5_f5a_fleet2_left.png` |
| F03 | 2 | Ships | fleet +18 (0x0049C27E) `ships` | none | decimal | always | [R-code] F:41187 (ShowFleetDetails); [O] `A5_f5a_fleet0_left.png` |
| F04 | 3 | Repair | fleet +20 (0x0049C280) `condition` | none | decimal + `%` | own fleet | [R-code] F:41191 (ShowFleetDetails); [O] `A5_f5a_fleet2_left.png` |
| F05 | 4 | Supply | fleet +14 (0x0049C27A) `supplies` | percent = trunc(supplies x 100 / (ships x 8)) | decimal + ` tons  (` pct `%)` | own fleet | [R-code] F:41201 (ShowFleetDetails); [O] `A5_f5a_fleet2_left.png` |
| F06 | 5 | Money | fleet +16 (0x0049C27C) `money` | none | decimal + ` talents` | own fleet | [R-code] F:41210 (ShowFleetDetails); [O] `A5_f5a_fleet2_left.png` |
| F07 | 6 | Capacity | fleet +18 `ships` | ships x 500 | thousands separators + ` troops` | always | [R-code] F:41216 (ShowFleetDetails); [O] `A5_f5a_fleet0_left.png` |
| F08 | 7 | Sea | fleet +24 (0x0049C284), the map code under the fleet (sav.py names it `cell`) | field == 0 | `calm` when 0, otherwise `rough` (any other value, also negative) | always (also foreign fleets) | [R-code] F:41224 (ShowFleetDetails); [O] `A5_f5a_fleet0_left.png` |
| F09 | 8- | (embarked army) | fleet +22 (0x0049C282) `army` >= 0: the army at the same tile is shown by ShowArmyDetails and its lines 2.. are moved down 8 lines | none | line 8 blank, line 9 `Army`, then the army's Supply, Morale, Money, (no Terrain), blank, the five types, Total troops, [No. of units, blank, Regulars cost, Mercenary pay] | fleet carries an army; the army lines follow the own/foreign rule of the army panel | [R-code] F:41156 (ShowFleetDetails); [O] `A5_f5a_fleet2_left.png` |

**Foreign fleet:** Fleet of, Ships, Capacity and Sea are shown; Moves, Repair, Supply and Money are blank [O] `A5_f5a_fleet0_left.png`, `A5_f5b_fleet1_left.png`. A foreign fleet that carries an army shows that army as a foreign army (composition only) under `Army` [O] `A5_f5c_fleet0_left.png`. **What decides Sea:** `FUN_00451304` (weather overlay, `F:54272`) zeroes `+0x18` of every fleet each week, clears and re-rolls the code-1 cells (rough sea) around 20 DAT centres, and sets `+0x18 = 1` for a fleet whose marker a new patch lands on (`F:54264`); every fleet step (`FUN_0044DD70`, `F:51965-51972`) stores the destination cell's code into `+0x18` (a fleet can only enter cells with code 0 or 1); a new fleet starts at 0 (`F:48794`). The panel only tests `+0x18 == 0`. [R-code][O] values 0 (`calm`), 1, 2, -1 (`rough`) in `A5_f5a_fleet2_left.png`, `A5_f5a_fleet0_left.png`, `A5_f5b_fleet0_left.png`, `A5_f5a_fleet1_left.png`. See also decompiled-map-code1-overlay.md and decompiled-weather-events.md of the research repository.

## The unit lists (UM06, UM07), right click

| id | line | caption | source field | formula | format | shown when | evidence |
|---|---|---|---|---|---|---|---|
| U1 | 0-n | Mercenaries at / There are no mercenaries at | merc pool (50 records of 12 bytes, DAT_0049DA10): x, y, name index, type, troops, quality; rows whose (x, y) is the clicked tile and troops >= 0 | name = DAT_0049CC94 + 20 i (52 names) | row: `<name>    <type name>` + the troops in a 14-char thousands field (FUN_00448e74, not trimmed) + `<quality word>` (band table 4) | right click on any city tile, own or foreign | [R-code] F:41265 (ShowCityUnits); [O] `A6_merc_rome.png` |
| U2 | 0-20 | Army of <nation> + one row per unit | army slots 0..19: name +8 (24 bytes), type +2, troops +4, quality +6 | the list stops at the first slot with troops <= 0 | row: `<name>   <type name>` + troops (FUN_00448f18: 3 lead blanks, thousands separators) + `   ` + `<quality word>` | right click on an own army (the current nation's); a foreign army prints nothing and the left-click panel stays | [R-code] F:41290 (ShowArmyUnits); [O] `A6_army0_right_scrolled.png` |
| U3 | - | (fleet units) | fleet +22 `army` >= 0 -> ShowArmyUnits for the tile | none | as U2 | right click on a fleet that carries an army; otherwise nothing (the panel stays) | [R-code] F:41320 (ShowFleetUnits); [O] `A5_f5a_fleet2_right.png` |

Helpers (not captions): `FUN_00405B00` strcpy and `FUN_00405BC8` strcat build every line; `FUN_004028C4` + `FUN_00402978` turn a number into its decimal text (no separators; a negative keeps `-`); the three thousands formatters are `FUN_00448E74` (a 14-character field: blank, sign, blank, then the digits with `,` every three, left-aligned), `FUN_00448F18` (trailing blanks cut), `FUN_00448F3C` (left part cut: `1,500`, or `- 1,500` for a negative: the minus, a blank, the digits [O] `A7_nation00_treasury0.png`), `FUN_00448F9C` (12 characters copied from index 3: no sign, trailing blanks kept); `FUN_004498D8`, `FUN_00449920`, `FUN_00449970` find the city, army or fleet at the clicked tile (the army and fleet must have an owner >= 0); `FUN_0044A698` total troops (1 if 0), `FUN_0044A66C` highest used slot + 1, `FUN_0044B8D0` is-a-capital, `FUN_004498B0` tribute x pop / max pop.

## Band tables

Words are the DAT strings (11-byte entries; the relation entries are 6 bytes). An edge is **confirmed** only when both sides were captured in play with the expected word seen; the screenshot and save of each side are cited. `[derived]` edges are the ones that were not or could not be staged, with the reason.

### Unity (nation panel), `trunc(unity / 100)` into the table at `DAT_004793FC`

| from | to | word |
|---|---|---|
| 0 | 499 | very low |
| 500 | 599 | low |
| 600 | 699 | normal |
| 700 | 799 | high |
| 800 | 899 | very high |
| 900 | 999 | excellent |
| 1000 | 1199 | (blank) |

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| 499 | 500 | very low | low | **confirmed**: 499 `A3_nation_02_Seleucid.png` (A3_nations_unity_relations.SAV), 500 `A3_nation_03_Ptolemaic.png` (A3_nations_unity_relations.SAV) |
| 599 | 600 | low | normal | **confirmed**: 599 `A3_nation_04_Macedonia.png` (A3_nations_unity_relations.SAV), 600 `A3_nation_05_Numidia.png` (A3_nations_unity_relations.SAV) |
| 699 | 700 | normal | high | **confirmed**: 699 `A3_nation_06_Gaul.png` (A3_nations_unity_relations.SAV), 700 `A3_nation_07_Greece.png` (A3_nations_unity_relations.SAV) |
| 799 | 800 | high | very high | **confirmed**: 799 `A3_nation_08_Celtiberia.png` (A3_nations_unity_relations.SAV), 800 `A3_nation_09_Illyria.v2.png` (A3_nations_unity_relations.SAV) |
| 899 | 900 | very high | excellent | **confirmed**: 899 `A3_nation_10_Dacia.v2.png` (A3_nations_unity_relations.SAV), 900 `A3_nation_11_Bithynia.v2.png` (A3_nations_unity_relations.SAV) |
| 999 | 1000 | excellent | (blank) | **confirmed**: 999 `A3_nation_12_Galatia.v2.png` (A3_nations_unity_relations.SAV), 1000 `A3_nation_13_Armenia.v2.png` (A3_nations_unity_relations.SAV) |

Unity 0 is not a word: the nation is conquered (row N12). Unity is kept within 300-990 by the game's own quarterly update (nation-tax-base / city-population-growth reports), so the blank at 1000 and above is not reachable in play [D]; it was staged only to read the code's edge (`A3_nation_13_Armenia.v2.png` blank at 1000, `A3_nation_14_Media.v2.png` blank at 1100).

### Loyalty (city panel), `trunc(loyalty / 10)` into the same table

| from | to | word |
|---|---|---|
| 0 | 49 | very low |
| 50 | 59 | low |
| 60 | 69 | normal |
| 70 | 79 | high |
| 80 | 89 | very high |
| 90 | 99 | excellent |
| 100 | 109 | (blank) |

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| -20 | -19 | ry good | ite | [derived] (outside the range the game produces / staged range; code only) |
| -10 | -9 | ite | very low | **confirmed**: -10 `A1_city_071_Pisae.png` (A1_cities_loyalty_fort.SAV), -9 `A1_city_080_Tarquinii.png` (A1_cities_loyalty_fort.SAV) |
| 49 | 50 | very low | low | **confirmed**: 49 `A1_city_090_Alba Fucens.png` (A1_cities_loyalty_fort.SAV), 50 `A1_city_091_Fregellae.png` (A1_cities_loyalty_fort.SAV) |
| 59 | 60 | low | normal | **confirmed**: 59 `A1_city_096_Hadria.png` (A1_cities_loyalty_fort.SAV), 60 `A1_city_097_Cales.png` (A1_cities_loyalty_fort.SAV) |
| 69 | 70 | normal | high | **confirmed**: 69 `A1_city_100_Capua.png` (A1_cities_loyalty_fort.SAV), 70 `A1_city_101_Neapolis.png` (A1_cities_loyalty_fort.SAV) |
| 79 | 80 | high | very high | **confirmed**: 79 `A1_city_106_Paestum.png` (A1_cities_loyalty_fort.SAV), 80 `A1_city_110_Luceria.png` (A1_cities_loyalty_fort.SAV) |
| 89 | 90 | very high | excellent | **confirmed**: 89 `A1_city_111_Rhegium.png` (A1_cities_loyalty_fort.SAV), 90 `A1_city_113_Teanum Apulum.png` (A1_cities_loyalty_fort.SAV) |
| 99 | 100 | excellent | (blank) | **confirmed**: 99 `A1_city_115_Venusia.png` (A1_cities_loyalty_fort.SAV), 100 `A1_city_116_Locri.png` (A1_cities_loyalty_fort.SAV) |

Saves hold 38-96 (702 saves, 4,000+ city records); a negative loyalty is read before the table (-10..-19 prints `ite`, the tail of `elite` of the quality table; -20.. prints other bytes): staged only at -10 and -9 [O] `A1_city_071_Pisae.png` (`ite`), `A1_city_080_Tarquinii.png` (`very low`); edges below -10 are [D].

### Morale (own army panel), index `((m - 51), or (m - 48) when that is negative) sar 2` into the table at `DAT_00479428` (= the unity table from entry 4)

| from | to | word |
|---|---|---|
| 40 | 54 | very low |
| 55 | 58 | low |
| 59 | 62 | normal |
| 63 | 66 | high |
| 67 | 70 | very high |
| 71 | 74 | excellent |
| 75 | 80 | (blank) |

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| 54 | 55 | very low | low | **confirmed**: 54 `A4_army_02_left.png` (A4_armies_own.SAV), 55 `A4_army_03_left.png` (A4_armies_own.SAV) |
| 58 | 59 | low | normal | **confirmed**: 58 `A4_army_04_left.png` (A4_armies_own.SAV), 59 `A4_army_05_left.png` (A4_armies_own.SAV) |
| 62 | 63 | normal | high | **confirmed**: 62 `A4_army_06_left.png` (A4_armies_own.SAV), 63 `A4_army_07_left.png` (A4_armies_own.SAV) |
| 66 | 67 | high | very high | **confirmed**: 66 `A4_army_08_left.png` (A4_armies_own.SAV), 67 `A4_army_09_left.png` (A4_armies_own.SAV) |
| 70 | 71 | very high | excellent | **confirmed**: 70 `A4_army_10_left.png` (A4_armies_own.SAV), 71 `A4_army_11_left.png` (A4_armies_own.SAV) |
| 74 | 75 | excellent | (blank) | **confirmed**: 74 `A4_army_12_left.png` (A4_armies_own.SAV), 75 `A4_army_13_left.png` (A4_armies_own.SAV) |

Saves hold 51-73 (the research report supply-driven-morale-and-fleet-attrition.md says 51-70 and "five 4-wide tiers"; the code has a sixth tier, `excellent` 71-74, and saves such as `fleet-split-antium-0734.SAV` (army 3, morale 73) are in it). Below 51 the `m - 48` branch applies: 48-50 are index 0 (`very low`; 50 staged [O] `A4_army_00_left.png`); 40-47 read the unity table's entries 3 to 1 before the morale table's start, which are also `very low` [D] (not staged); below about 36 the index leaves the table [D]. 75 and above prints nothing [O] (75 staged, `A4_army_13_left.png`).

### Quality of a unit (unit lists, mercenary lists), the field `0..9` is the table index (`DAT_0047938C`)

| from | to | word |
|---|---|---|
| 0 | 3 | not ready |
| 4 | 4 | very poor |
| 5 | 5 | poor |
| 6 | 6 | average |
| 7 | 7 | good |
| 8 | 8 | very good |
| 9 | 9 | elite |
| 10 | 11 | (blank) |

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| -1 | 0 | er | notready | [derived] (outside the range the game produces / staged range; code only) |
| 3 | 4 | notready | verypoor | **confirmed**: 3 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 4 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |
| 4 | 5 | verypoor | poor | **confirmed**: 4 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 5 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |
| 5 | 6 | poor | average | **confirmed**: 5 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 6 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |
| 6 | 7 | average | good | **confirmed**: 6 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 7 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |
| 7 | 8 | good | verygood | **confirmed**: 7 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 8 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |
| 8 | 9 | verygood | elite | **confirmed**: 8 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 9 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |
| 9 | 10 | elite | (blank) | **confirmed**: 9 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV), 10 `A6_army0_right_scrolled.png` (A6_lists_quality_mercs.SAV) |

Indexes 0-3 print the same word (`not ready`: the mobilized quality is `state / 4`, a unit under 16 weeks of training); 10 and 11 print nothing [O] `A6_army0_right_scrolled.png`. The word is checked space-free in the audit because the OCR sometimes drops a blank inside a row; the shot was checked by eye.

### Tribute of a FOREIGN city (found on the way), the city's `+0x20` field as an unsigned 16-bit

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| 10 | 11 | poor | moderate | **confirmed**: 10 `A2_city_004_Banasa.png` (A2_bracket_tribute.SAV), 11 `A2_city_005_Gades.png` (A2_bracket_tribute.SAV) |
| 30 | 31 | moderate | rich | **confirmed**: 30 `A2_city_006_Lixus.png` (A2_bracket_tribute.SAV), 31 `A2_city_013_Malaca.png` (A2_bracket_tribute.SAV) |
| 100 | 101 | rich | very rich | **confirmed**: 100 `A2_city_016_Rusaddir.png` (A2_bracket_tribute.SAV), 101 `A2_city_018_Sexi.png` (A2_bracket_tribute.SAV) |
| 10000 | 10001 | very rich | <number> | **confirmed**: 10000 `A2_city_025_Carthago Novo.png` (A2_bracket_tribute.SAV), 10001 `A2_city_026_Helice.png` (A2_bracket_tribute.SAV) |

Above 10000 no word is chosen and the talents number text (row C08's) stays: 10001 prints `10001`, 20000 prints `20000`, 40000 prints `-25536`, 65535 prints `-1` [O] `A2_city_026_Helice.png`, `A2_city_030_Akra Leuke.png`, `A2_city_033_Icosium.png`, `A2_city_035_Cissa.png`.

### Relations (nation panel), `DAT_004794C8 + 6 x value` only when `value > 0`

| value | word |
|---|---|
| <= 0 | (blank) |
| 1 | trade |
| 2 | ally |
| 3 | war |
| 4, 5 | (blank) |
| 6, 7, 100 | other memory (one stray character, `5` `[` `,` seen) |

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| 0 | 1 | (blank) | trade | **confirmed**: 0 `A3_nation_00_Rome.png` (A3_nations_unity_relations.SAV), 1 `A3_nation_00_Rome.png` (A3_nations_unity_relations.SAV) |
| 1 | 2 | trade | ally | **confirmed**: 1 `A3_nation_00_Rome.png` (A3_nations_unity_relations.SAV), 2 `A3_nation_01_Carthage.png` (A3_nations_unity_relations.SAV) |
| 2 | 3 | ally | war | **confirmed**: 2 `A3_nation_01_Carthage.png` (A3_nations_unity_relations.SAV), 3 `A3_nation_00_Rome.png` (A3_nations_unity_relations.SAV) |
| 3 | 4 | war | (blank) | **confirmed**: 3 `A3_nation_00_Rome.png` (A3_nations_unity_relations.SAV), 4 `A3_nation_01_Carthage.png` (A3_nations_unity_relations.SAV) |
| 5 | 6 | (blank) | 5 | [derived] (outside the range the game produces / staged range; code only) |
| 6 | 7 | 5 | [ | [derived] (outside the range the game produces / staged range; code only) |
| 7 | 8 | [ | R | [derived] (outside the range the game produces / staged range; code only) |

The DAT table also holds `peace` at value 0, which the code never prints. Values stored in saves are -18..3 (the negatives are other state of the diplomacy matrix); only 0-3 are meaningful.

### Sea (fleet panel)

| `+0x18` | word |
|---|---|
| 0 | calm |
| anything else | rough |

| last value below | first value above | word below | word above | status |
|---|---|---|---|---|
| -1 | 0 | rough | calm | **confirmed**: -1 `A5_f5a_fleet1_left.png` (A5_f5a.SAV), 0 `A5_f5a_fleet2_left.png` (A5_f5a.SAV) |
| 0 | 1 | calm | rough | **confirmed**: 0 `A5_f5a_fleet2_left.png` (A5_f5a.SAV), 1 `A5_f5a_fleet0_left.png` (A5_f5a.SAV) |

### Other branches that are not words

- **Fortification** `raw <= 100`: `raw%`; `raw >= 101`: `raw mod 100%  (under construction)`: staged 0, 50, 99, 100, 101, 150, 199, 200, 250 [O] `A1_city_*` (100 prints `100%`, 101 prints `1%  (under construction)`).

## Where the sources disagree

- **Help topic "Cities" versus the code (bracket).** The help says the number in brackets after the fortification is "the number of conscripts currently being trained at that city". The code (C07) sums every slot of the controller's queue at that city whatever its state, trained ones included, and does it for foreign cities as well. [R-code][O] `A2_city_090_Alba Fucens.png` (state 0 + state 24 = `(3,000)`). The digest line "the queue is the garrison" matches the code.
- **Help topic "Nations" versus the code.** The help lists "tribute payed" and "trade earned" among the details of the own nation; `ShowNationStatus` prints neither (the inventory's N03 already noted the screenshots do not show them). [R-code][O] `A7b_nation00_treasury1.png` (Rome as current nation: Mobilized and Treasury present) and `A8_cur1_nation00.png` (Rome seen from Carthage: neither).
- **Research report `supply-driven-morale-and-fleet-attrition.md`** says the morale field is bounded 51-70, exactly five 4-wide tiers; the code has six tiers and saves reach 73 (see Morale above).
- **Research report `rome-city-recruitment-and-nations.md`** lists the loyalty adjective thresholds as "not decoded"; they are in the Loyalty table above.
- **Inventory rows UM04 and UM05** were [derived]; they are now observed (foreign army: composition, terrain and total only; fleet panel: fields and Sea).
- **Nation-tax-base report names `+0x430` "wealth"**; the panel prints it as **Population**. [O] the panels of the unmodified BASE.SAV nations show Rome `2,577,000` (`A8_cur1_nation00.png`) and Carthage `4,821,000` (`A8_cur1_nation01.png`). [D] those equal 3000 x the sum of the cities' `pop` fields of that save (Rome 859, Carthage 1607, computed with `state/sav.py` from `BASE.SAV`, not a capture), which is the report's formula.

## What this does not establish

- **Model-versus-game output not reproduced (1 row, `NOT-MODELLED-OUTPUT`):** a nation Population of 2,147,483,647 (`A3_nation_07_Greece.png`, panel line 4) prints junk glyphs after the digits; the code explains the overrun (`FUN_00448F9C` copies 12 characters of a 14-character field without a terminator) but the junk is stale stack content the model cannot know; the value is unreachable (10^9 or more). The relation-100 stray `,` after Dacia, once listed as a disagreement, is now modelled: the index runs into the city table loaded from the save (byte `0x2C`), and the row compares OK apart from an OCR misread of the comma.
- Edges outside the values the game produces (loyalty below 0 or above 109, unity 1000 and above, morale below 48 and above 75, relation values above 5, quality -1 and 10 and above) are the code's reading of other memory and are [derived]; the ones staged are marked confirmed only where both sides were seen.
- OCR was the reader; the by-eye check covered contact sheets of the cropped word lines and the 22 corrected rows, not every one of the 1,500 panel lines. 31 clipped list rows are partial evidence only (their last word is cut by the window); the quality words are evidenced by the scrolled / short lists.
- `Population` of a nation of 10^9 or more prints junk after the digits; not a reachable value.
- Carthage as current nation was re-captured with a verified refresh (`A8_cur1_nation01.png`: Mobilized 12%, Treasury 7,777 talents); the first attempt (`A7_cur1_nation01.png`) showed a stale Rome panel and is excluded.
- A nation panel whose `Capital` is -1, a city with `max_pop` 0 (division by zero in `ShowCityDetails`) and a city whose allegiance is -1 were not staged.
- The panel is rebuilt only on a click or a menu choice; whether the game redraws it after an order or an end of turn was not studied.
- Wine 9.0 only; no real Windows run.
- The news-log, battle `BattleUnitMoves` and the other Information-window uses are out of this task.

## Evidence index

`runs/experiments/data/run-exp-info-window/`: `captures.tsv` (every capture: save, target, staged values, screenshot, SHA-256, OCR), `claims_audit_*` (the audit), `band_samples.tsv`, `band_edges.tsv`, `code_word_tables.tsv`, `coverage_report.tsv` and `coverage_summary.txt`, `MANIFEST-*.txt`, `SAVES.sha256`, `capture_exclusions.tsv`. Scripts in `runs/experiments/info_window/`. Binaries: release `run-exp-info-window`.
