# run-exp-manual133: screenshots for the user manual (issue #133)

Screenshots of every screen, menu, dialog and typical message of *Imperial Conquest 2* (1996), for the user manual.
Approved by the owner on 2026-10-22 (issue #133).

- **PNGs**: `/home/user/ic2-conquest/artifacts/run-exp-manual133/shots/` (gitignored, rule 1). Never overwritten or
  deleted: a re-take gets `_v2`. `shots.csv` holds each file's SHA-256.
- **Saves written by this run** (not in git, rule 1): `/home/user/ic2-conquest/artifacts/run-exp-manual133/saves/`, all
  prefixed `M133_`; hashes in `SAVES.sha256` beside this README. To go to the release `run-exp-manual133`.
- **Index**: `shots.csv` (file, chapter, what it shows, source save, turn, exe, sha256). `run-log.jsonl`: every load,
  shot and end turn. `state.json`: what the helper believed was loaded (fills the source-save column).
- **Scripts** (`runs/experiments/manual133/`): `m.py` (helpers `start`, `attach`, `snap`, `wins`, `ctl`), `rel.py`
  (one relation change, shoot the box), `endturn.py` (End turn, shoot every box), `menuprompt.py` (menu item, shoot the
  box, answer No), `finish_battle.py` (play a tactical battle to the end with shots). The shots were driven step by step
  with short `python3 -c` calls importing `m.py`, each PNG checked by eye before going on.
- Environment: Xvfb 1280x1024, Wine 9.0, no window manager (no title bars on any window), the seed build
  `Imperial Conquest 2 fast rollingsave seed.exe` with SEED.TXT 12345, except the `M06_15`..`M06_23` battle shots
  (original `Imperial Conquest 2.exe`).
- Full-screen shots are cropped to the game area (0,26)-(772,1001) or its top part; the rest of the root window is black.
- File-name prefix = manual chapter: M01 start, M02 screen, M03 armies, M04 cities, M05 fleets, M06 combat,
  M07 diplomacy and nations, M08 turn, M09 Game-menu prompts. (The csv `chapter` column is the authority: a few
  M07 area-map shots are filed under "2 Screen", the M09 File prompts under "1 Start".)

## Sources

| Shots | Source |
|---|---|
| M01_01..06 | program start, File > New, Rome ticked, OK (new game, seed 12345) |
| M01_07..08, M02, M03 (most), M04, M07 | `saves/run0-start-AUTO0720-seed12345.SAV`, 0720, plus the orders shown in earlier shots of the same load (see `run-log.jsonl`) |
| M08_*, M09_*, M06_01..08 | the same game played on: End turn to 0721..0726 (autosaves kept as `M133_session1_AUTO07xx.SAV`); the tactical battle M06_01..08 happened during the AI turn after 0723 (Gaul attacked the new Roman army) |
| M05_01..09 | `saves/fleet-port-antium-0734.SAV`; M05_10..12 `saves/fleet-split-antium-0734.SAV`; M05_13..16 run0 start |
| M06_09..14 | new game as Seleucid (`M133_seleucid_new_0720.SAV`, seed 12345), then End turn (`M133_seleucid_AUTO0721.SAV`) |
| M06_15..23 | `M133_session1_AUTO0722.SAV` in the original exe: Rome's army 0 moved next to the Gaul army 9 and attacked it; Rome won (23,700 -> 10,746 against 44,757 -> 0, captured 96 talents and 316 tons), news "Rome destroys army of Gaul.", no peace offer (the loser was destroyed). The battle took about 15 minutes with the default delays |

## Progress

- [x] 1 Start: program start, File menu, New game form (empty and with Rome ticked), first screen, first offer box,
  Save As and Open dialogs, File > New / Close confirmations
- [x] 2 Screen: every top menu, the Unit map and Area map submenus, About box, WinHelp, toolbar and hints, area map in
  every overlay, Find city dialog, unit map views
- [x] 3 Armies: army selected, toolbar hint, Supply army (before / after arrows), move, Split army, Army to army transfer,
  Change units, Rename unit, Split unit, two refusals, Disband army Confirm and refusal, Join armies, mercenaries
- [x] 4 Cities: own and foreign city, city panel, Fortify (dialog, cost, refusal), Army recruits (recruit, mobilize,
  disband Confirm), new army, Change tax level
- [x] 5 Fleets: fleet selected, toolbar, Supply / Repair / Split fleet, Fleet to fleet transfer, scuttle Confirm,
  embark, refusal with an army aboard, move, Build fleet (dialog, cost, notices)
- [x] 6 Combat: tactical battle (seed build: placement, unit info, surrender Confirm, Battle ended), siege capture and
  failed siege, attack-city Confirm, original-exe battle (placement, Change delays, mid-battle x6, end)
- [x] 7 Diplomacy and nations: Balance sheet, News, nation panels, International Relations (before / after), four refusals
- [x] 8 Turn: End turn ? box, news after End turn, after a battle turn, season change, a trade offer at turn start
- [x] 9 Game menu: New nation, Abdicate, New player
- [ ] Release upload of the saves (see "Skipped")

## Re-takes and shots to ignore

| Shot | Why | Use instead |
|---|---|---|
| `M01_01_program_start.png` | full root window, mostly black | `M01_01_program_start_v2.png` |
| `M02_31_unit_map_after_find_carthago.png` | the Find city dialog was still open (the first OK click only activated it) | `..._v2.png` |
| `M03_18_after_join_armies.png` | the join did nothing (armies not adjacent, army 0 had no moves) | `..._v2.png` |
| `M03_19_before_join_two_armies.png` | a ghost of the closed Split army dialog (no window manager: the area behind a closed dialog is repainted 1-3 s later) | `..._v2.png` |
| `M04_02_city_info_panel_rome.png` | crop cut the Supply line | `..._v2.png` |
| `M04_03_city_toolbar_tooltip_v2.png` | the hint did not show; `M04_03_city_toolbar_tooltip.png` shows it at the bottom edge | the first one |
| `M05_08_fleet_with_army_aboard.png` | crop cut the army part of the panel | `..._v2.png` |
| `M06_04_battle_unit_selected.png` | the click missed the unit (nothing selected) | `..._v2.png` |
| `M06_07_battle_computer_general_placed.png` | in the seed build the whole battle ran at the Computer general click: this shows the battle's end state with the last combat report (ATTACKS / UNIT LOSSES, Defender routed), and the lower half was not repainted | keep as "combat report"; use the M06_15.. series for the battle itself |
| `M06_17_orig_battle_unit_placed.png` | the placement click was outside the allowed rows, nothing moved | `..._v2.png` |
| `M06_15_orig_battle_start_placement.png` | csv text says own units at the bottom: in fact the attacker's (Rome's) units wait in the top row and the defender (Gaul) is already placed at the bottom | (text correction only) |
| `M06_11_captured_city_info.png` | csv text says Allegiance to Ptolemaic: the panel shows Allegiance to Seleucid (pop 64%, loyalty excellent, fort 40%) | (text correction only) |
| `M06_19_orig_battle_computer_general_placed.png` | the battle had already started moving: units advanced | (text correction only) |
| `M07_05_nation_panel_all_nations.png` | All nations does not change the Information panel (it still shows the last nation) | `M07_07` shows what All does |
| `M07_06_area_map_carthage_cities.png` | shows all cities: the nation-button selection had been set to All before | none (see notes) |
| `M07_08b_international_relations_trade_ticked.png` | the trade radio is not yet drawn as ticked | `M07_15` |

## UI notes for the manual text (exact labels)

### Main window
- Title: `Imperial Conquest 2    Rome's turn   (Appius Claudius)` (nation, then the leader's name). During the AI seats the
  title shows the AI nation (`Gaul's turn   (Hengest)`).
- Menu bar: **File, Game, Strategy, Nations, Area map, Unit map, Help**.
- File: New, Open, Save, Save As, Close (Save / Save As greyed with no game loaded). Before a game is loaded the toolbar
  has only the Open button.
- Game: End turn, New player, New nation, Abdicate.
- Strategy: News (Shift+W), International relations, Taxation, Balance sheet (Shift+B), Recruit unit, Build fleet.
- Nations: Rome, Carthage, Seleucid, Ptolemaic, Macedonia, Numidia, Gaul, Greece, Celtiberia, Illyria, Dacia, Bithynia,
  Galatia, Armenia, Media, Thracia, All nations (the chosen one ticked).
- Area map: Show cities (Shift+C), Show capital (Shift+P), Show armies (Shift+A), Show fleets (Shift+F), Show all (Shift+L),
  Show mercenaries > (Light infantry Shift+1, Heavy infantry Shift+2, Archers Shift+3, Light cavalry Shift+4,
  Heavy cavalry Shift+5, All mercenaries Shift+M), Find a city (Shift+D).
- Unit map: Army > (Supply army, Recruit mercenaries, Transfer unit, Split army, Join armies, Change units, Disband army);
  Fleet > (Supply fleet, Repair fleet, Transfer ships, Split fleet, Join fleets, Scuttle fleet); City > (Fortify city);
  Cancel selection (Shift+X).
- Help: Help topics (opens the WinHelp file `Imperial Conquest 2.hlp`: buttons Summary / Index / Back, first page
  "Introduction"; **the original help file exists and is a source for the manual**), Show hints (ticked), About Imperial Conquest.
- About box: "Imperial Conquest 2 v1.01", "This is the full/freeware version of Imperial Conquest 2, feel free to copy and
  distribute it.", "copyright Serious Games 1997"; buttons **OK** and **CAncell** (sic).
- Main toolbar hints, left to right: Open saved game, Save game position, End player's turn, News, International relations,
  Taxation, Balance sheet, Recruit unit, Build fleet, then one button per nation (hint = its name) and All nations.
  Hints only show while the main window is the active window.
- The nation buttons (and the Nations menu) choose the nation shown in the Information panel's nation view
  (Nation, Leader, Capital, Cities, Population, Unity, Tax rate; for your own nation also Mobilized and Treasury; then
  INTERNATIONAL RELATIONS: one line per nation with trade / ally / war, blank = peace) and, it seems, whose cities,
  armies, fleets the area map Show buttons mark (Carthage: black dots on the African coast; All nations: every city).
  The selection looked cumulative in one test; not established.
- File dialogs (Save As, Open) are the Wine common dialogs ("Save in:"/"Look in:", File name, Files of type: Saved games,
  Save/Open, Cancel, Open as read-only); under Windows 95 they look different.

### New game form (File > New; also Game > New player), title "Human and computer leaders"
- Columns **Nation**, **human** (check box), **Leader's name** (edit box, greyed until human is ticked). Default leaders:
  Rome Appius Claudius, Carthage Agis, Seleucid Darius, Ptolemaic Thutmose, Macedonia Alexander, Numidia Abu-Simbel,
  Gaul Hengest, Greece Pergamus, Celtiberia Octavian, Illyria Epaminondas, Dacia Theudebert, Bithynia Stesichorus,
  Galatia Androcles, Armenia Mesa, Media Samuramat, Thracia Anacreon. Buttons **OK**, **Cancel**.
- Game > New player opens the same form with the current human nations ticked.
- The game starts at Week 1 Spring 270 BC; the Information panel shows the news of 272 and 271 BC, then turn-start boxes
  ("Bithynia wants to trade with Rome", Information box, OK).

### Confirm boxes (all Yes / No / Cancel, title "Confirm")
- File > New with a game loaded: "Are you sure you want to start a new game ?"; File > Close: "Are you sure you want to quit ?"
- Game > New nation: "Are you sure you want to lead a different nation ?"; Game > Abdicate: "Are you sure you want to abdicate ?"
- Disband army: "Are you sure you want to disband this army ?"; Army recruits > Disband: "Are you sure you want to disband 1 unit ?"
- Scuttle fleet: "Are you sure you want to scuttle this fleet ?"; battle Surrender: "Are you sure you want to surrender ?"
- Attack a city of a nation not at war: "Are you sure you want to attack this city ?" (Yes declared war, news
  "SELEUCID DECLARES WAR ON GREECE.", and the siege followed at once: "Seleucid fails to capture Pergamum (Greece).")

### Area map
- Toolbar hints: Toggle colour, Show cities, Show capital, Show armies, Show fleets, Show all, Light infantry,
  Heavy infantry, Archers, Light cavalry, Heavy cavalry, All mercenaries, Find a city.
- Toggle colour switches between the political view (own land pink, other land green, sea grey) and the terrain view
  (sea blue, desert yellow-brown, forest, mountains, white borders). Mercenary buttons mark the offers with symbols per type.
- A click on the area map centres the unit map there.
- **Find city** dialog: the chosen nation's name on top, its cities in a list (capital in capitals), one button per nation, **OK**.

### Unit map and Information panel
- 13 x 13 tiles with scroll bars; a strip above the tiles holds the toolbar of the selected army, fleet or city (an army
  aboard a fleet: both toolbars).
- Own city: City, Controlled by, Allegiance to, Population (181,000 (100%)), Loyalty (excellent, high...),
  Fortification (78% (14,000); "72% (under construction)" after a Fortify order), Tribute (317 talents), Supply (990 tons).
  Foreign city: no Supply; Tribute as a word (moderate).
- Own army: Army of Rome, Moves, Supply (170 tons (71%)), Morale (very high...), Money (100 talents), Terrain, troops by
  type (Light infantry, Heavy infantry, Archers, Light cavalry, Heavy cavalry), Total troops, No. of units,
  Regulars cost (232 talents per quarter), Mercenary pay. Foreign army: name and troops only.
- Fleet: Fleet of Rome, Moves, Ships, Repair (97%), Supply, Money, Capacity (15,000 troops = 500 per ship), Sea (calm);
  with an army aboard, the army's lines follow.

### Army dialogs
- Toolbar hints: Supply army, Recruit mercenaries, Transfer units, Split army, Join armies, Change units, Disband army,
  Cancel selection. (Menu wording: "Transfer unit".)
- **Supply army**: "Supplies at <city>" / 10s 100s arrows / "Army's supplies"; "National balance" / 10s 100s / "Army's money"; OK.
- **Split army** and **Army to army transfer** (same layout): "Units in first army" / "Units in second army" lists
  (name, type, troops, quality), Transfer and Disband under each, "<n> units  <troops> troops"; "First army's supply" /
  10s 100s / "Second army's supply"; the same for money; OK, Cancel. Supplies are divided in proportion at the split.
  After Split army the old army has 0 moves, the new one 0 moves too.
- **Change units**: "Units in army" list; Rename unit, Join units, Split unit, Disband; OK, Cancel.
  **Rename unit**: Current name, New name, OK, Cancel. **Split unit**: Unit to split; "Size of new units" with 100s and
  1000s arrows (starts half and half); OK, Cancel.
- **Recruit mercenary unit**: "Units at <city>" (e.g. "Samnite  Lit inf  3,868  very good"), "Quarterly cost", Recruit unit, OK.
  The dialog closes itself after the last offer is hired.
- Join armies has no dialog.
- Refusals seen: "This unit is too small to split.", "You can only combine units of the same type.",
  "An army must be near its own city to disband."

### City dialogs
- City toolbar: Fortify city, Cancel selection.
- **Fortify <city>**: Initial fortification, 1s 10s arrows, New fortification, Cost of modification; OK, Cancel.
  Refusal: "This city is already being fortified."
- **Army recruits** (Strategy > Recruit unit): "Create unit at <city>" with buttons Light infantry, Heavy infantry, Archers,
  Light cavalry, Heavy cavalry; 100s / 1000s arrows ("Troops"); New unit, Initial cost, Quarterly cost; Recruit unit; OK.
  Right: "Cities to recruit at" list (capital in capitals), "Units at <city>" (type, troops, readiness: not ready,
  very poor, ...), Mobilize, Disband. Mobilize with a "not ready" unit does nothing (no box). A mobilised unit becomes a
  new army in the city: 0 moves, 0 supplies, morale normal.
- **Change tax level**: Current tax, New tax, Current income, New income, "Set tax level" slider; OK, Cancel.

### Fleets
- Toolbar hints: Supply fleet, Repair fleet, Transfer ships, Split fleet, Join fleets, Scuttle fleet, Cancel selection.
- **Supply fleet**: as Supply army ("Supplies at Antium", "Fleet's supplies", "National balance", "Fleet's money").
- **Repair fleet**: Original state of repair, 1s 10s, New state of repair, Cost of repairs; OK, Cancel.
- **Split fleet** / **Fleet to fleet transfer**: First/Second fleet's ships (1s 10s), supply (10s 100s), money (10s 100s); OK, Cancel.
- **Build fleet**: Ships (1s 10s), Initial cost, Quarterly cost, Troop capacity; OK, Cancel. After OK: "The fleet will be
  built at Caere." Next time: "A fleet of 20 ships will be ready in 24 weeks at Caere." before the dialog.
  (20 ships: initial 200, quarterly 60, capacity 10,000.)
- Refusal seen: "You can not split a fleet carrying an army."

### Combat
- Battle window title: `<attacker>  v  <defender>          <nation> to place units.` / `... to move units.`
- Battle toolbar hints: Unit moves, Friendly units, Enemy units, Cancel selection, End turn, Change pauses,
  Computer general on, Surrender. Change pauses opens **Change delays**: Shot delay (secs) and Attack delay (secs),
  0.1 and 1.0 arrows (defaults 2.0 and 3.0 secs); OK, Cancel.
- Placement: the units to place wait in a row on your edge; click one, then a tile of the allowed rows.
- Unit panel: "Rome's army", unit name, type, Troops, Quality, Morale, Moves, Shots; enemy unit: name, type, Troops.
- Combat reports in the Information panel: "<unit> ATTACKS <unit>  UNIT LOSSES Attacker n Defender n|routed" and
  "<unit> SHOOTS AT <unit>  TROOP LOSSES n".
- **Battle ended**: "<A>'s army defeats <B>'s army.", start / finish troops per type for both sides, "The army of <A>
  captured no money.", "... captured no suuplies." (sic); OK.
- In the seed ("fast") build the whole battle ran on the Computer general click; in the original exe each End turn
  click plays a half-round with the delays above.
- A siege at war has no box: news "Damascus (Ptolemaic) falls to Seleucid." or "Seleucid fails to capture Pergamum (Greece)."

### Diplomacy
- **International Relations**: columns peace, trade, ally, war; one row per nation (own row empty); OK, Cancel.
- Refusals: "You cannot trade with Carthage", "Gaul does not want to make peace at this time.",
  "Illyria does not want to ally with your nation", "You can only trade with 3 nations". Accepted proposals (trade with
  Numidia, Bithynia) and a war declaration (Media) give no box; the next turn's news shows "ROME DECLARES WAR ON MEDIA."
  and "ROME DECLARES WAR ON ARMENIA." (Media's ally).
- **Balance sheet**: Revenue (Taxes, Tribute, Trade, Total), Expenditure (Administration, Fleets, Army recruits,
  Regular units, Mercenary units, Total), Balance, Debt limit; OK.

### Turn
- End turn: the seed build plays all AI seats at once (1-2 s). Each turn is 2 weeks; 6 turns a season.
- **End turn ?** (420x265): "An army of yours needs supplies." in a list, "If you have not finished your turn click
  MAKE MORE MOVES. If you are finished moving this turn click END TURN."; buttons **End turn**, **Make more moves**.
- Turn-start offers: "Dacia wants to trade with Rome." (Information, OK).
- The news log groups events under "Week n  Season  year BC".

## Skipped (with reason)

| Item | Reason |
|---|---|
| "Offer of peace" after a battle | random (about 1 in 3 defeats); did not appear in the two battles here. An earlier screenshot exists: `loss_s1_survey_r1_dialog-Offer_of_peace-1791142747.png` (release `run-exp-battle-peace`) |
| Attack-army and attack-fleet Confirm boxes | no own unit next to a foreign army or fleet of a nation at peace in the saves at hand; the attack-city box (same wording pattern) is `M06_12`. The fleet box exists in release `run-exp-peace-prompt` (`PP_yes_seed1.SAV`) |
| Join fleets result, Disembark | no dialog of their own (instant orders); left out for count |
| Embark refusal "The army is too large for this fleet ?" | needs a larger army; not tried |
| A tooltip of the city toolbar on a clean background | the hint shows only while the unit map is active; `M04_03` has it at the edge |
| The AI turn in progress (other nation's title with moving armies) | the seed build plays AI seats in about 1 s; only the battle during Gaul's turn was caught (`M06_01`) |
| Release upload of the `M133_*` saves | not done by this agent (no release token used here); the files and their hashes are listed in `SAVES.sha256` |
