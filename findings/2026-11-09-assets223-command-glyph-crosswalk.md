# Toolbar glyphs → remake command keys; glyph transparency; unit icons; area-map lists (research #223)

**Status:** promoted 2026-11-09 into imperial-conquest-2-research at `963c58d` (research PR #225, by ic2-research, from `d85154c6`); this draft is kept for history, the research repo is canonical. Research reran the scan (equal to `command-glyphs-v1.json`), checked the 44 keys against the remake manifest at `55bd7fce` and the cited dump lines; pixel decoding and the MapsList tile table were not redone independently. Research corrected cosmetic-gaps §3 and two rows of the #218 spec accordingly, and closed #223. Original status line follows.

**Original status:** draft from `ic2-conquest`, waiting for ic2-research intake. Answers
[research #223](https://github.com/diegoami/imperial-conquest-2-research/issues/223) (parent #218), which blocks
diegoami/imperial_conquest_2#1850. It builds on `docs/reports/2026-11-07-original-assets218-extraction-spec.md` and the
accepted extractor (conquest `1544d666`, v1.0.1, whose `glyph_semantic` tables hold the same 44 candidates).

**Pins.** Original EXE `9d753d5d…ba31`. Decompile `all_app_functions.txt` `2018c205…87d8` (59,228 lines; every `:line`
below is in this file) and its `delphi_symbols.tsv` (published method tables). Extractor
`scripts/extract_original_assets.py` `5d266a07…97f5`. Remake key source `55bd7fce…` (`assets/packs/authored/manifest.json`).
Scalar receipt: `runs/experiments/data/run-exp-assets223/command-glyphs-v1.json`, produced by `scan_command_glyphs.py`
beside it (reproduce: that folder's README). No game was run and no media was exported.

**Tags.** `[confirmed: code]`: a decompile line, a DFM property path or a published field/method table entry in the EXE.
`[measured]`: a scalar read from the EXE's stored resources by the scan. `[derived]`: inferred, and the reason is given.

## Answer

1. All 44 keys (36 `ui.command.*`, 8 `battle.toolbar.*`) have one original glyph each. Each one comes from a
   `TSpeedButton.Glyph.Data` whose `OnClick` handler does exactly the command the key names (table A). Every key has an
   original counterpart. Glyphs with no key: `TAreaMap.sb_areatog` (Toggle colour), `TPremierForm.sb_Allnations`, the
   16 nation sheets and `TCellAuto.sb_Save` (the About easter-egg window; the same picture as `sb_Save`).
   Two pairs of keys take an identical stored image: `ui.command.end_turn.icon` = `battle.toolbar.end_turn`, and
   `ui.command.cancel_selection.icon` = `battle.toolbar.cancel_selection` `[measured]`.
2. Every glyph is a 4-bit BMP with the standard 16-colour Windows palette and no mask. Transparency is a **colour
   key**: the colour of the sheet's bottom-left pixel, which VCL reads at run time `[confirmed: code]`. That pixel is
   palette index 11 (yellow) on 43 sheets, 15 (white) on 19 and 13 (magenta) on one, `sb_areatog` `[measured]`.
3. `unit.<type>.icon`: take the area-map mercenary button glyph of that type, `TAreaMap.sb_area{li,hi,arch,lc,hc}`
   `[derived]`. The area-map 8×8 point `PointsList[type+4]` is the original's on-map marker, so it is the alternative
   for that use (section C).
4. `PointsList` index meanings are confirmed in code: 0 city, 1 capital, 2 army, 3 fleet, 4–8 mercenary pool of
   type 0–4, 9 unused and blank. `MapsList[0]` is a two-tone land/sea map and `MapsList[1]` a per-terrain colour map,
   one pixel per map tile `[measured]`; `Toggle colour` picks between them (section D).

## A. Component → key crosswalk

Property path = `<Form>.Panel1.<component>.Glyph.Data`. Every one is 20×20, `NumGlyphs` 1, 4 bpp, 16 entries. "Key"
is the palette index of the transparent colour, and "field" the component's published field offset in its form.
Handler addresses come from the published method table (`delphi_symbols.tsv`). The `:line` is the handler's body
in the dump. The binding component → handler is the DFM `OnClick` identifier `[confirmed: code]` for every row.

### TPremierForm (main toolbar), 9 keys

| component | hint | OnClick → handler | field | key | remake key | evidence |
|---|---|---|---|---|---|---|
| sb_Open | Open saved game | OpenGameFile @0045aad4 | 0x2f8 | 15 | `ui.command.open.icon` | :58057 |
| sb_Save | Save game position | SaveGameFile @0045ab84 | 0x2fc | 11 | `ui.command.save.icon` | :58103 |
| sb_Endturn | End player's turn | EndTurn @0045b0a8 | 0x300 | 15 | `ui.command.end_turn.icon` | :58338 |
| sb_News | News | StrategicDecision @0045b2bc | 0x304 | 15 | `ui.command.news.icon` | :58443 → :58464 `TInformation_PrintNews` |
| sb_Pols | International relations | StrategicDecision | 0x308 | 15 | `ui.command.relations.icon` | :58444-58445 → `TPolitics` |
| sb_Tax | Taxation | StrategicDecision | 0x30c | 15 | `ui.command.taxation.icon` | :58450-58451 → `TChangeTax` |
| sb_Balance | Balance sheet | StrategicDecision | 0x310 | 15 | `ui.command.balance_sheet.icon` | :58447-58448 → `TBalanceSheet` |
| sb_Newunit | Recruit unit | StrategicDecision | 0x314 | 15 | `ui.command.recruit_unit.icon` | :58453-58454 → `TArmyRecruits` |
| sb_Newfleet | Build fleet | StrategicDecision | 0x318 | 15 | `ui.command.build_fleet.icon` | :58456-58457 → `TPremierForm_BuildNewFleet` → `TBuildFleet` :58541 |

The six strategy buttons share one handler that compares `Sender` with fields 0x304–0x318 (and the menu items at
0x1e0–0x1f4). The field offsets come from the EXE's published field table, and the dialog classes from the
class-name slot of the VMTs that the dump passes to the form-show helper (`FUN_00424608`): 0x452208 `TPolitics`,
0x4533cc `TBalanceSheet`, 0x453c44 `TChangeTax`, 0x454138 `TArmyRecruits`, 0x455600 `TBuildFleet` `[measured]`
(receipt `dialogs`).

### TAreaMap (area-map toolbar), 12 keys

| component | hint | OnClick → handler | field | key | remake key | evidence |
|---|---|---|---|---|---|---|
| sb_areacits | Show cities | ShowCities @0043e210 | 0x1b4 | 11 | `ui.command.show_cities.icon` | :41821 |
| sb_areacap | Show capital | ShowCapital @0043e288 | 0x1b8 | 11 | `ui.command.show_capital.icon` | :41850 |
| sb_areaarms | Show armies | ShowArmies @0043e31c | 0x1bc | 11 | `ui.command.show_armies.icon` | :41884 |
| sb_areaflts | Show fleets | ShowFleets @0043e3ac | 0x1c0 | 11 | `ui.command.show_fleets.icon` | :41924 |
| sb_areaalln | Show all | ShowAll @0043e440 | 0x1c4 | 11 | `ui.command.show_all.icon` | :41964 |
| sb_areali | Light infantry | ShowMercsLI @0043e4d8 → ShowMercs(0) | 0x1c8 | 11 | `ui.command.show_mercs_light_infantry.icon` | :42013 |
| sb_areahi | Heavy infantry | ShowMercsHI @0043e4e0 → ShowMercs(1) | 0x1cc | 11 | `ui.command.show_mercs_heavy_infantry.icon` | :42023 |
| sb_areaarch | Archers | ShowMercsAr @0043e4ec → ShowMercs(2) | 0x1d0 | 11 | `ui.command.show_mercs_archers.icon` | :42033 |
| sb_arealc | Light cavalry | ShowMercsLC @0043e4f8 → ShowMercs(3) | 0x1d4 | 11 | `ui.command.show_mercs_light_cavalry.icon` | :42043 |
| sb_areahc | Heavy cavalry | ShowMercsHC @0043e504 → ShowMercs(4) | 0x1d8 | 11 | `ui.command.show_mercs_heavy_cavalry.icon` | :42053 |
| sb_areaallm | All mercenaries | ShowMercsAll @0043e510 → ShowMercs(5) | 0x1dc | 11 | `ui.command.show_mercs_all.icon` | :42063 |
| sb_findcity | Find a city | UseFindCity @0043e51c → `TFindCity` | 0x1e8 | 11 | `ui.command.find_city.icon` | :42075-42078 |

### TUnitMap (unit-map order toolbar), 15 keys

All are `Visible = False` in the DFM; the form shows them according to the selection. Which buttons are shown when
is not part of this draft.

| component | hint | OnClick → handler | field | key | remake key | evidence |
|---|---|---|---|---|---|---|
| sb_supplyarmy | Supply army | SupplyArmy @00446f50 | 0x1d8 | 11 | `ui.command.army_supply.icon` | :46827 |
| sb_recruitmercs | Recruit mercenaries | RecruitMercenaries @00446ff4 | 0x1dc | 11 | `ui.command.army_recruit_mercenaries.icon` | :46858 |
| sb_transferunit | Transfer units | ArmyToArmyTransfer @00447288 | 0x1e0 | 11 | `ui.command.army_transfer_unit.icon` | :46922 |
| sb_splitarmy | Split army | SplitArmy @0044755c | 0x1e4 | 11 | `ui.command.army_split.icon` | :47021 |
| sb_joinarmies | Join armies | JoinArmies @004472fc | 0x1e8 | 11 | `ui.command.army_join.icon` | :46950 |
| sb_changeunit | Change units | ChangeUnitDetails @00447644 | 0x1ec | 11 | `ui.command.army_change_units.icon` | :47057 |
| sb_disbandarmy | Disband army | DisbandArmy @004476ac | 0x1f0 | 11 | `ui.command.army_disband.icon` | :47081 |
| sb_supplyfleet | Supply fleet | SupplyFleet @004477fc | 0x1f4 | 11 | `ui.command.fleet_supply.icon` | :47124 |
| sb_repairfleet | Repair fleet | RepairFlt @004478c8 | 0x1f8 | 11 | `ui.command.fleet_repair.icon` | :47161 |
| sb_transferships | Transfer ships | FleetToFleetTransfer @004479f4 | 0x1fc | 11 | `ui.command.fleet_transfer_ships.icon` | :47195 |
| sb_splitfleet | Split fleet | SplitFleet @00447cac | 0x200 | 11 | `ui.command.fleet_split.icon` | :47270 |
| sb_joinfleets | Join fleets | JoinFleets @00447a48 | 0x204 | 11 | `ui.command.fleet_join.icon` | :47218 |
| sb_scuttle | Scuttle fleet | ScuttleFleet @00447e34 | 0x208 | 11 | `ui.command.fleet_scuttle.icon` | :47317 |
| sb_fortifycity | Fortify city | Fortify @00448004 | 0x20c | 11 | `ui.command.city_fortify.icon` | :47370 |
| sb_cancel | Cancel selection | CancelSelection @00448170 | 0x210 | 11 | `ui.command.cancel_selection.icon` | :47409 |

### TBattleMap (tactical toolbar), 8 keys

| component | hint | OnClick → handler | field | key | remake key | evidence |
|---|---|---|---|---|---|---|
| sb_unitmoves | Unit moves | UnitsSetMoves @00437718 | 0x1cc | 11 | `battle.toolbar.unit_moves` | :37769-37775 |
| sb_friendlyunits | Friendly units | MyUnitDetails @00437724 | 0x1d4 | 11 | `battle.toolbar.friendly_units` | :37779-37825 |
| sb_enemyunits | Enemy units | EnemyUnitDetails @004378f8 | 0x1d0 | 11 | `battle.toolbar.enemy_units` | symbol table only (`delphi_symbols.tsv:38`); the dump has no separate body |
| sb_cancel | Cancel selection | CancelSelection @00437a60 | 0x1b8 | 11 | `battle.toolbar.cancel_selection` | :37827 |
| sb_endturn | End turn | EndTurn @00437a94 | 0x1c4 | 15 | `battle.toolbar.end_turn` | :37841 |
| sb_pauses | Change pauses | ChangePauses @00437aa0 → `TBattleDelays` | 0x1bc | 11 | `battle.toolbar.change_pauses` | :37852-37857 |
| sb_compgen | Computer general on | ComputerGeneral @00437ab8 | 0x1c8 | 11 | `battle.toolbar.computer_general` | :37862 |
| sb_surrender | Surrender | Surrender @00437ad8 | 0x1c0 | 11 | `battle.toolbar.surrender` | :37878 |

### Glyphs with no key, and keys with no glyph

| glyph | hint / handler | why there is no key |
|---|---|---|
| `TAreaMap.sb_areatog` (key 13) | Toggle colour / ToggleMap @0043dfd4 :41725 | The remake has no colour-toggle command (gap A01, remake #723) |
| `TPremierForm.sb_Allnations` (key 11) | All nations / ChangeNation @0045b6f0 :58575 | The remake builds its nation rows from the world; there is no all-nations row among the 100 keys |
| 16 × `TPremierForm.sb_<Nation>` (2 frames) | ChangeNation | Settled separately (spec #218); no nation-button keys among the 100 |
| `TCellAuto.sb_Save` (key 11) | Save structure as .BMP / SaveBMP @004569c0 :56663 | The About easter-egg window (`findings/2026-10-08-about-imperial-conquest-h03.md`); same image as `TPremierForm.sb_Save` |

Keys with no original glyph: none among the 44.

Identical stored images (palette indices and palette, compared in full) `[measured]`: `TPremierForm.sb_Endturn` =
`TBattleMap.sb_endturn`; `TUnitMap.sb_cancel` = `TBattleMap.sb_cancel`; `TPremierForm.sb_Save` = `TCellAuto.sb_Save`.
Each of the other glyphs is unique.

## B. Palette and transparency of the glyphs

**Storage** `[measured]`: every one of the 63 `Glyph.Data` sheets is one 4-bit BITMAPINFOHEADER DIB, bottom-up,
16 palette entries in the standard Windows order (0 black … 7 silver `c0c0c0`, 8 grey `808080`, … 11 yellow `ffff00`,
13 magenta `ff00ff`, 15 white `ffffff`). There is no 1-bit mask: a speed-button glyph is a single image, unlike the
`TImageList` sheets, which carry a separate mask BMP. The key colour fills exactly one palette slot on every sheet,
so "pixels of the key colour" and "pixels of the key index" are the same set.

**Key per sheet** `[measured]`: palette index 11 (yellow) on 43 sheets: all of TUnitMap, all of TAreaMap except
`sb_areatog`, TBattleMap except `sb_endturn`, `TPremierForm.sb_Save`, `TCellAuto.sb_Save`, `sb_Allnations`, and
6 nation sheets (owners 0–4 and 15). Index 15 (white) on
19 sheets: `sb_Open`, `sb_Endturn` (both forms), the six strategy buttons and 10 nation sheets. Index 13 (magenta)
on one sheet, `sb_areatog`. Per command glyph, the receipt gives the count of key pixels (`frames[].key_pixels`).
For example, the white-keyed glyphs have 208–360 key pixels out of 400, so white inside such a picture is
transparent too.

**How VCL applies it** `[confirmed: code]`, VCL code linked into the EXE:

- `FUN_0041d220` :24568-24585 is `TBitmap.TransparentColor`: `Canvas.Pixels[0, Height-1]` (the bottom-left pixel,
  through the `GetPixel` wrapper `FUN_0041a0bc` :22154), or white for a monochrome bitmap, OR `0x02000000`.
- The glyph-changed handler `FUN_0042e480` :32240-32256 stores it in the button glyph's field +0x1C (the
  constructor's default is `0x8080`, :32200) and discards the cached state images.
- `FUN_0042e544` :32272-32516 builds each state image. Up and Down (state 0, 2): `TCanvas.BrushCopy`
  (`FUN_00419a88`, call at :32507) of the frame onto a bitmap filled with `clBtnFace` (`0x8000000F`), with the
  key as the transparent colour. Key-coloured pixels become button face, and the result is added to the glyph list
  without a mask. Down falls back to frame 0 when `NumGlyphs < 3` (:32315-32317).
  Exclusive (state 3): the frame is copied and added with `ImageList_AddMasked(…, key)` (`FUN_0042e148`, :32496).
  Disabled (state 1) is synthesised with the `0x00E20746` raster operation. It is not a stored frame.
- `FUN_0042eaec` :32519-32557 draws the state with `ImageList_DrawEx`: `ILD_NORMAL` on `clBtnFace` for states
  0–2, and `ILD_TRANSPARENT` for state 3.

For a static conversion: alpha = 0 exactly where the palette index equals the sheet's bottom-left index. That is
what the accepted extractor's `TSpeedButton-bottom-left-key` already does `[derived]`. A consumer that draws
on a face colour reproduces the up state. Pressed and disabled looks are VCL synthesis (see Not established).

## C. The five `unit.<type>.icon` keys

**What the remake uses them for** (source at `55bd7fce`):

1. `godot/UI/AreaMapView.cs:646-676`: one marker per mercenary pool on the area map, drawn untinted
   (`DrawTextureRect(texture, rect, false)`) at tile scale.
2. `godot/UI/GameCommandTable.cs:116-122`: the `area_map.show_mercs_<type>` menu and toolbar rows take
   `unit.<visual>.icon` in place of `ui.command.show_mercs_<type>.icon` when the ruleset gives the unit type a
   `VisualTypeId`.

**Original candidates** `[confirmed: code / measured]`:

| type (code) | toolbar glyph (20×20, key 11) | area-map point (8×8) | tactical sprite (32×32) |
|---|---|---|---|
| light infantry (0) | `TAreaMap.sb_areali` | `PointsList[4]` | `BatMapList[0..2]` |
| heavy infantry (1) | `TAreaMap.sb_areahi` | `PointsList[5]` | `BatMapList[3..5]` |
| archers (2) | `TAreaMap.sb_areaarch` | `PointsList[6]` | `BatMapList[6..8]` |
| light cavalry (3) | `TAreaMap.sb_arealc` | `PointsList[7]` | `BatMapList[9..11]` |
| heavy cavalry (4) | `TAreaMap.sb_areahc` | `PointsList[8]` | `BatMapList[12..14]` |

`ShowMercs` :41983-42011 draws `PointsList[slot type + 4]` for each of the 50 pool slots (:41994-41996). The type
codes 0–4 are those of `ShowMercsLI…HC` :42013-42061.

**Recommendation** `[derived]`: `unit.<type>.icon` ← the toolbar glyph `TAreaMap.Panel1.sb_area<type>.Glyph.Data`,
frame 0, yellow key. The reasons:

- For use 2, this glyph is the original's own picture of that command. The toolbar then looks the same whether or
  not the remake replaces the command's key with the unit key.
- It is the only original picture of each unit type that has no owner. Mercenary pools have no nation, and the
  remake draws use 1 untinted.
- The tactical sprites are already mapped to `battle.unit.<type>.<size>`. Their purple, white and blue pixels are
  nation recolour slots (spec #218, point 5), so drawn without a nation they show the template colours, not a
  finished picture.

`PointsList[type+4]` is the faithful original look for use 1 (the on-map marker). It is an opaque black-on-white 8×8
cell drawn with a raster operation (section D), not an alpha sprite. A consumer that wants the original marker
should get a dedicated key with SRCAND compositing rather than this key. The glyph is 20×20, while the remake's
authored `unit.*.icon` is 32×32 (`docs/asset-specification.md` §1 at the pin), so the consumer has to scale or pad it.

## D. TAreaMap.PointsList and MapsList

**PointsList** (`TAreaMap.PointsList.Bitmap`, field 0x1e4; 10 cells of 8×8, sheet 32×32, 8-bit colour + 1-bit
mask): the only reader is `TAreaMap_PrintBitmap` :41793. Its callers fix the index meanings `[confirmed: code]`:

| index | meaning | drawn by | black px of 64 `[measured]` |
|---|---|---|---|
| 0 | city (every city, or the Find-a-city result when it is not a capital) | ShowCities :41834; ShowFindCity :42094 | 4 |
| 1 | capital (each nation's capital, or the Find-a-city result when it is a capital: `FUN_0044b8d0` :50015) | ShowCapital :41865-41867; ShowFindCity :42097-42098 | 16 |
| 2 | army | ShowArmies :41905 | 34 |
| 3 | fleet (built fleets only: the build-countdown word is −1) | ShowFleets :41945 | 36 |
| 4–8 | mercenary pool of type 0–4 (LI, HI, archers, LC, HC) | ShowMercs :41996 (`type + 4`) | 13, 13, 28, 12, 20 |
| 9 | no caller | none | 0 (blank) |

All 10 cells are distinct, all are fully opaque in the mask (64 of 64 opaque) and contain only black and white
`[measured]`. Cities, capitals, armies and fleets are drawn for the nation in view, or for every nation when the
view is "All nations" (`0x10`).

**Compositing** `[confirmed: code]`, `TAreaMap_PrintBitmap` :41779-41816:

- `ImageList.GetBitmap(index)` (`FUN_00417200` :20168, which draws through `ImageList_DrawEx`). Then
  `Canvas.StretchDraw` (`FUN_00419f1c` :22031) with `Canvas.CopyMode` set to `SRCAND` (`0x008800C6`) when the form
  byte +0x1EE is 0, and to `MERGEPAINT` (`0x00BB0226`) otherwise. `SRCCOPY` is restored afterwards (:41794-41815).
- Destination: x from `W·(tx−4)/320`, y from `(H−30)·(ty−4)/140 + 30`, size `8·W/320` × `8·(H−30)/140`. Here
  W×H is the client area, 30 the toolbar, and (tx, ty) the map tile. The 8×8 cell therefore spans tiles tx−4…tx+3
  on the 320×140 map, scaled with the window.
- Each Show routine flips +0x1EE once after drawing its whole layer (:41839-41844 and the matching lines in each
  routine). `PaintForm` sets it to 0 before replaying the stored draw list (:41672). `ShowFindCity` sets it to 1 and
  does not flip it (:42091).

What follows from the truth tables `[derived]`: with SRCAND, white source pixels leave the map unchanged and black
ones paint black. With MERGEPAINT (NOT src OR dst), white leaves the map unchanged and black paints **white**. So
consecutive layers alternate between black and white symbols, and the Find-a-city marker is white. One consequence
of the code alone: `ShowAll` (:41964-41978) runs cities, capital, fleets, armies in that order, so the capital and
army layers would be white when it starts from 0. This was not observed in play here.

**MapsList** (field 0x1e0; 2 cells of 320×140, sheet 1280×280, mask fully opaque): `PaintForm` stretches
`MapsList[1]` over the client area below the toolbar when the nation-record byte +0x46C is 0, and `MapsList[0]`
when it is non-zero (:41654-41663). `ToggleMap` XORs that byte (:41730) and clears the draw list (:41732, +0x2B8).
Each map pixel is one map tile. Compared tile by tile with the terrain codes of `saves/fortify-arretium-0720.SAV`
`[measured]`:

| terrain (save code) | tiles | `MapsList[1]` colour | `MapsList[0]` colour |
|---|---|---|---|
| sea (0, 1) | 12,211 | `0000ff` (all) | `808080` (all) |
| plain (2) | 11,958 | `008000` (11,955; 3 are sea-coloured) | `008000` (11,955) |
| desert (3) | 11,407 | `808000` (all) | `008000` |
| forest (4) | 4,749 | `000000` (all) | `008000` |
| mountains (5) | 2,983 | `800000` (all) | `008000` |
| river (6–11) | 1,142 | `c0c0c0` (1,139) | `008000` |
| city/army/fleet marker (≥ 12) | 350 | the colour of the terrain beneath | land or sea |

So `MapsList[0]` is a two-tone land/sea map and `MapsList[1]` a terrain-colour map. This corrects the open point in
`findings/2026-10-06-cosmetic-gaps.md` §3: there are two different stored images, not one image drawn two ways, and
the names "two-tone" and "terrain" are now established statically. That draft's run observed byte 1 (MapsList[0],
the longer uniform runs), which agrees.

## Does not establish

- The original UI layout or placement in forms. DFM `Left`/`Top` are in the receipt, but no on-screen layout or
  visibility rule is claimed, including when the TUnitMap buttons show.
- How VCL synthesises button states: the pressed (bevel offset), disabled (monochrome) and exclusive looks are read
  from the code paths above, not rendered.
- Remake consumer suitability or rendering: scaling the 20×20 glyphs, the untinted area-map drawing, the menu-row
  swap and a SRCAND point consumer are not tested.
- Native Windows acceptance. No Wine or Windows run was made for this draft.
- `TBattleMap_EnemyUnitDetails`'s body: its binding comes from the DFM and the method table. Its code is not
  decompiled separately in this dump, so its behaviour was not re-read here.
- That the MERGEPAINT layers really appear white in play. This is inferred from the raster-operation codes only.
- Which MapsList image a new game starts with (the initial value of nation byte +0x46C).

## Reproduce

```bash
sha256sum "$IC2_DECOMPILE/all_app_functions.txt"   # 2018c205…87d8, wc -l = 59228
python3 -I runs/experiments/data/run-exp-assets223/scan_command_glyphs.py \
  --exe "$ORIGINAL_EXE" --extractor scripts/extract_original_assets.py \
  --symbols "$IC2_DECOMPILE/delphi_symbols.tsv" --dump "$IC2_DECOMPILE/all_app_functions.txt" \
  --save saves/fortify-arretium-0720.SAV --repo . --out <new receipt name>.json
sed -n '58440,58466p;41779,41816p;41983,42011p;24568,24585p;32240,32256p;32490,32510p' "$IC2_DECOMPILE/all_app_functions.txt"
grep -n -E '"(ui\.command|battle\.toolbar)\.' assets/packs/authored/manifest.json   # remake at 55bd7fce: 44 keys, lines 39-74, 98-105
```
