# run-exp-manual133: screenshots for the user manual (issue #133)

Screenshots of every screen, menu, dialog and typical message of *Imperial Conquest 2* (1996), for the user manual.
Approved by the owner on 2026-10-22 (issue #133).

- **PNGs**: `/home/user/ic2-conquest/artifacts/run-exp-manual133/shots/` (gitignored, rule 1). Never overwritten or
  deleted: a re-take gets `_v2`, `_v3`.
- **Index**: `shots.csv` (file, chapter, what it shows, source save, turn, exe, sha256). `run-log.jsonl`: every load and shot.
  `state.json`: what the helper thinks is loaded (used by `snap` to fill the source-save column).
- **Script**: `runs/experiments/manual133/m.py` (helpers: `start`, `attach`, `snap`, `wins`, `ctl`). The shots were driven
  step by step from short `python3 -c` calls that import it, each one verified by looking at the PNG.
- Environment: Xvfb 1280x1024, Wine 9.0, no window manager (no title bars), seed build
  `Imperial Conquest 2 fast rollingsave seed.exe` with SEED.TXT 12345 unless the row says otherwise.
- Full-screen shots are cropped to the game's area (0,26)-(772,1001) (the rest of the root window is black).

## Progress

(updated as batches finish)

- [x] 1 Start: program start, File menu, New game form (leaders form), first screen of a new game, first offer box
- [x] 2 Screen: every top menu, the Unit map and Area map submenus, About box, WinHelp, main toolbar and hints,
  area map in every overlay, Find city dialog, unit map views
- [ ] 3 Armies
- [ ] 4 Cities (city selected, info panel, foreign city done; fortify, recruit, mobilize, taxation to do)
- [ ] 5 Fleets
- [ ] 6 Combat
- [ ] 7 Diplomacy and nations
- [ ] 8 Turn
- [ ] 9 Nation menu prompts

## Re-takes and shots to ignore

| Shot | Why | Use instead |
|---|---|---|
| `M01_01_program_start.png` | full root window, mostly black | `M01_01_program_start_v2.png` |
| `M02_31_unit_map_after_find_carthago.png` | the Find city dialog was still open (the first OK click only activated it) | `..._v2.png` |
| `M04_02_city_info_panel_rome.png` | crop cut the Supply line | `..._v2.png` |
| `M04_03_city_toolbar_tooltip_v2.png` | the hint did not show (window not active); `M04_03_city_toolbar_tooltip.png` shows it at the bottom edge | the first one |

## UI notes for the manual text (exact labels)

### Main window
- Menu bar: **File, Game, Strategy, Nations, Area map, Unit map, Help**.
- File: New, Open, Save, Save As, Close (Save / Save As greyed with no game loaded). Before a game is loaded the toolbar has
  only the Open button.
- Game: End turn, New player, New nation, Abdicate.
- Strategy: News (Shift+W), International relations, Taxation, Balance sheet (Shift+B), Recruit unit, Build fleet.
- Nations: Rome, Carthage, Seleucid, Ptolemaic, Macedonia, Numidia, Gaul, Greece, Celtiberia, Illyria, Dacia, Bithynia,
  Galatia, Armenia, Media, Thracia, All nations (the current one ticked).
- Area map: Show cities (Shift+C), Show capital (Shift+P), Show armies (Shift+A), Show fleets (Shift+F), Show all (Shift+L),
  Show mercenaries > (Light infantry Shift+1, Heavy infantry Shift+2, Archers Shift+3, Light cavalry Shift+4,
  Heavy cavalry Shift+5, All mercenaries Shift+M), Find a city (Shift+D).
- Unit map: Army > (Supply army, Recruit mercenaries, Transfer unit, Split army, Join armies, Change units, Disband army);
  Fleet > (Supply fleet, Repair fleet, Transfer ships, Split fleet, Join fleets, Scuttle fleet); City > (Fortify city);
  Cancel selection (Shift+X).
- Help: Help topics (opens the WinHelp file `Imperial Conquest 2.hlp`: Summary / Index / Back buttons, "Introduction" page),
  Show hints (ticked: the toolbar hints), About Imperial Conquest.
- About box: "Imperial Conquest 2 v1.01", "This is the full/freeware version of Imperial Conquest 2, feel free to copy and
  distribute it.", "copyright Serious Games 1997"; buttons **OK** and **CAncell** (sic).
- Main toolbar hints (left to right): Open saved game, Save game position, End player's turn, News, International relations,
  Taxation, Balance sheet, Recruit unit, Build fleet, then one button per nation (hint = the nation's name) and All nations.
  Hints only show while the main window is the active window.
- Window title: `Imperial Conquest 2    Rome's turn   (Appius Claudius)` (nation, then the leader's name).

### New game form (File > New), title "Human and computer leaders"
- Columns **Nation**, **human** (check box), **Leader's name** (edit box, greyed until human is ticked; default names:
  Rome Appius Claudius, Carthage Agis, Seleucid Darius, Ptolemaic Thutmose, Macedonia Alexander, Numidia Abu-Simbel,
  Gaul Hengest, Greece Pergamus, Celtiberia Octavian, Illyria Epaminondas, Dacia Theudebert, Bithynia Stesichorus,
  Galatia Androcles, Armenia Mesa, Media Samuramat, Thracia Anacreon). Buttons **OK**, **Cancel**.
- The game starts at Week 1 Spring 270 BC; the Information panel shows the news of 272 and 271 BC; then turn-start boxes
  (e.g. "Bithynia wants to trade with Rome", an Information box with OK).

### Area map
- Toolbar hints: Toggle colour, Show cities, Show capital, Show armies, Show fleets, Show all, Light infantry,
  Heavy infantry, Archers, Light cavalry, Heavy cavalry, All mercenaries, Find a city.
- Toggle colour switches between the political view (own land highlighted, others green, sea grey) and the terrain view
  (sea blue, desert, forest, mountains, borders in white). The show buttons mark only the current nation's own items;
  the mercenary buttons mark the mercenary offers (+, x, #, diamond, circle symbols per type).
- A click on the area map centres the unit map there.
- **Find city** dialog: a list of the chosen nation's cities (capital in capitals), one button per nation, **OK**.

### Unit map and Information panel
- 13 x 13 tiles, scroll bars; a strip above the tiles holds the toolbar of the selected army, fleet or city.
- City clicked (own): toolbar Fortify city, Cancel selection; Information panel: City, Controlled by, Allegiance to,
  Population (e.g. 181,000 (100%)), Loyalty (excellent, high...), Fortification (78% (14,000)), Tribute (317 talents),
  Supply (990 tons).
- Foreign city: the same without Supply; Tribute given as a word (moderate).
- Foreign army: "Army of Gaul", Moves / Supply / Morale / Money left blank, Terrain, then troops by type
  (Light infantry, Heavy infantry, Archers, Light cavalry, Heavy cavalry, Total troops).

## Skipped (with reason)

(none yet)
