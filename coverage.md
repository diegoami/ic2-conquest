# Coverage: every order, dialog, message and mechanic

The secondary goal of this repository is to exercise every mechanic the game has. This file is the checklist. An entry is ticked only with a save that shows it: run, file and turn (or the test save under `$IC2_WORK/tests/`, named in `tests/results.md`).

Legend: ✅ exercised and checked on a save diff · 🟡 driven, not yet checked on a save · ⬜ not yet exercised.

## 1. Orders (the order driver, `harness/driver.py`)

| Order | UI path | Driver | Test | Status | Evidence |
|---|---|---|---|---|---|
| New game (Rome human) | File → New, tick *human* (109, 114+20·row), OK (344,194) | `Game.new_game` | seed 12345 twice → identical `AUTO0720.SAV` | ✅ | `NEW_a.SAV` = `NEW_b.SAV` = `BASE.SAV`, sha256 `050bc354…` (tests/results.md) |
| Open a save | File → Open, name field (636,450), Enter | `Game.open`, `Game.load` (restart + seed + open) | every test | ✅ | all tests |
| Save As | File → Save As, name field, Enter | `Game.save_as` | every save-diff test | ✅ | `T_*.SAV` |
| End turn | toolbar *End turn* (57,58); **no confirmation box** | `Game.end_turn` | `end_turn`, `scripted_turn_repeats` | ✅ | `T_END_AUTO0721.SAV`; scripted turn byte-identical twice |
| Move army | click the army's tile, then the destination tile (one click = whole straight-line walk) | `Game.move` | `move` | ✅ | `T_MOVE.SAV`: army 0 (100,37)→(101,36), moves 8→4 (river tile costs 4) |
| Attack a city (siege) | select the army, click the **adjacent** enemy city | `Game.attack` | `attack` | ✅ | `T_ATTACK.SAV`: army 0 23,700→21,765, "Rome fails to capture Felsina (Gaul).", Felsina loyalty 79→76, fort 68→65, pop 26→25 |
| Attack an army (field battle) | select, click the adjacent enemy army; tactical screen, *Computer general* | `Game.attack` (plays it) | — | 🟡 | battle-bar calibrated (`End turn` ~114, `Computer general` ~165); the battle window can end up *below* the game's other windows, so the auto-play is flaky |
| Recruit a unit | toolbar *Recruit* (174,58) → *Army recruits* dialog | `Game.recruit` | `recruit` | ✅ | `T_RECRUIT.SAV`: HI 3,200 at Rome (city 85), state 0; treasury 2,200→1,880; mobilization 30→32 |
| Mobilize | *Army recruits* → city row → unit row (330, 177+12r) → *Mobilize* (350,352) | `Game.mobilize` | manual | ✅ | `saves/mobilize-new-army-0720.SAV`: army 14, HI 4,000 q4, 0 supplies, 0 moves, morale 59 |
| Disband a queued unit | *Army recruits* → select a unit → *Disband* | `Game.disband_unit` | `disband_unit` | ✅ | `T_DISBAND.SAV` |
| Supply army | select the army, army toolbar *Supply army* (349,108): 10s ▲ (169,94) moves city → army; money 100s ▲ (261,272) treasury → purse; OK (239,337) | `Game.supply` | manual | 🟡 | army 0 170 → 238 t (cap `troops div 100 + 1`), Arretium 150 → 82, purse 100 → 200, treasury −100 |
| Hire mercenaries | army toolbar (372,108) → *Recruit mercenary unit* (490×165): row (103,86+12r), *Recruit unit* (410,104), OK (248,174); nothing opens if no offer is adjacent | `Game.hire_mercs` | manual | ✅ | `saves/merc-hire-free-0720.SAV`: Samnite LI 3,868 q8 joined army 1; **no price deducted** |
| Transfer unit / army-to-army | Unit map → Army → Transfer unit | — | — | ⬜ | |
| Split army | army toolbar *Split army* → two unit lists, *Transfer*, *OK* | `Game.split_army` | `split_army` | ✅ | `T_SPLIT.SAV`: armies 2 → 3, troops conserved |
| Join armies | army toolbar *Join armies* (needs two adjacent armies) | `Game.join` | `join` | ✅ | `T_JOIN.SAV`: armies 0+1 → 45,700 t, 12 units |
| Change units (rename, split, join units) | Unit map → Army → Change units | `Game.change_units_disband` | `change_units_disband` | 🟡 | Disband only (`T_CHUNITS.SAV`); rename/join/split ⬜ |
| Disband army | Unit map → Army → Disband army → *Yes* | `Game.disband_army` | `disband_army` | ✅ | `T_DISBAND_ARMY.SAV`: Roman armies 2 → 1 |
| Fortify city | click an own city, city toolbar *Fortify city* (349,108) → *Fortify <city>*: 1s ▲ (136,86), 10s ▲ (168,86), OK (123,143) | `Game.fortify` | manual | ✅ | `saves/fortify-arretium-0720.SAV`: Arretium 72 → 372 (3 pending), −99 |
| Taxation | toolbar *Taxation* → *Change tax level* (slider 0..40, LineSize 1, Home then Right×n) | `Game.taxation` | `taxation` | ✅ | `T_TAX.SAV`: Rome 10 → 20% |
| International relations | toolbar (107,58) → *International Relations* (352×436 at 23,49): radio at x = 23 + {peace 94, trade 134, ally 176, war 218}, y = 74 + 23.55·row (Rome row 0); OK (308,217), Cancel (308,283). A refusal box aborts the whole OK: one change per call | `Game.relation` | manual | ✅ | `saves/trade-numidia-0720.SAV`: Numidia accepted; 6 refusals "You cannot trade with X."; 5 silent no-ops (open) |
| Build fleet | toolbar *Build fleet* → 1s/10s ship spinners → *OK* | `Game.build_fleet` | `build_fleet` | ✅ | `T_FLEET.SAV`: 10 ships, countdown 24, −100 |
| Fleet: move, attack, embark, disembark, supply, repair, transfer, split, join, scuttle | Unit map → Fleet → … | — | — | ⬜ | |
| News, Balance sheet | toolbar (84,58), (151,58) | — | — | ⬜ | read-only |
| Accept a post-battle peace (`TBattlePols`) | Yes/No after a battle | — | — | ⬜ | |

## 2. Dialog layouts (1280×1024 Xvfb, the default window layout of a new game)

**These coordinates are a reference, not what the driver clicks.** Under some Wine builds the font metrics differ, so the toolbar buttons and the dialog controls sit at a different pitch and the numbers below drift (a `recruit` click lands on Balance sheet; the Army recruits dialog's OK moves from (155,345) to about (167,372)). The driver derives both at run time: the toolbar from each button's tooltip window (`Game.calibrate_toolbar`, cached in `$IC2_WORK/toolbar.json`), and the dialog controls from the running game with the `win_controls` helper (`Game.controls`, `harness/win_controls.c`). The numbers here remain the fallback and the record of the layout.

**Main window.** Title `Imperial Conquest 2    Rome's turn   (<leader>)`, at (0,26), 650×300. Menu bar y = 36: File 14, Game 45, Strategy 97, Nations 148, Area map 202, Unit map 259, Help 304. Menu items start at y = 56, 16 px apart. Toolbar y = 58: Open 12, Save 35, End turn 57, News 84, International relations 107, Taxation 129, Balance sheet 151, Recruit unit 174, Build fleet 196, then the 16 nation icons and *All*.

- **Menus under Wine with no window manager:** an item click that arrives together with the pointer move is ignored, and after a dialog closes a menu click can be swallowed or re-open the last dialog. The driver hovers before every click, resets menu state (Escape ×2, a click on the bare root window at (1000,900)), and uses toolbar buttons wherever one exists.
- **An open menu** is an unnamed X window (the Game menu is 91×70 at (29,45)).
- **A click on an inactive window only activates it.** Message boxes and the unit map sometimes need a second click; the driver verifies every click's effect (the box closed, the army is selected) and repeats at most twice.

**Area map** (2,74), 328×196. The picture is 1 px per tile, tile (x,y) at screen (6+x, 126+y). **A click on it puts that tile at column 6, row 7 of the unit map** (checked at four places).

**Unit map** (332,74), 439×487. 32-px tiles, 13 columns × 13 rows visible; the paint box starts at (337,96) and the tiles at y = 126 (a 30-px strip above them). The view's top-left tile is the current nation's record `+0x488` (x) and `+0x486` (y); the game's click handler (`0x446420`) computes `x = X div 32 + [+0x488]`, `y = (Y − 30) div 32 + [+0x486]`. So the screen centre of tile (x,y) is `(337 + 32·(x−ox) + 16, 126 + 32·(y−oy) + 16)`. With an army selected, an army toolbar appears in its top strip.

**Information panel** (2,269), 328×730: the news log, or the nation panel.

**Message boxes** ("Information", about 238×92 at (521,479)): one *OK* button at the bottom centre, (x + w/2, y + h − 24). Text is read by OCR (tesseract) before dismissing.

**Army recruits** (toolbar *Recruit*), window 560×360 at (23,49):

| Control | Screen (x,y) |
|---|---|
| Unit type: Light infantry / Heavy infantry / Archers / Light cavalry / Heavy cavalry | (93,96) / (93,128) / (93,161) / (93,193) / (93,225) |
| Troops: 100s ▲ ▼, 1000s ▲ ▼ | (183,102) (183,120), (230,102) (230,120) |
| *Recruit unit* | (93,279) |
| *OK* | (155,345) |
| Cities to recruit at (list; rows 12 px apart, first at y = 75) | (365,75) |
| Units at <city> (list) | (405,…) from y = 177 |
| *Mobilize*, *Disband* | (350,352), (461,352) |
| New unit / Initial cost / Quarterly cost (read-only) | (208,193) / (208,235) / (208,276) |

- Picking a type shows the default size `standard/5` (HI 1,200); each 1000s ▲ adds 1,000 (HI + 2 × 1000s = 3,200). Initial cost = `troops div 200 × initialPrice` (HI 3,200 → 320), quarterly = `troops div 200 × quarterlyPrice` (32).
- **The city list** at the start (Rome, 270 BC) is `Luceria`, `ROME` (a capital is written in capitals). The rule, read from the code at `0x454582`: an own city is listed if its fortification is ≥ 75 (a pending order counts its built part), or it is the capital, or it already holds one of your queued units. See `findings/2026-09-29-recruiting-cities-need-fortification-75.md`.

**Toolbars (tooltips read by hovering).** Army selected (unit map strip, y = 108): Supply army 349, Recruit mercenaries 372, Transfer units 397, Split army 421, Join armies 445, Change units 468, Disband army 493, Cancel selection 519. City selected: Fortify city 349, Cancel selection 372. Area map (y = 108): Toggle colour 18, Show cities 44, capital 65, armies 87, fleets 108, all 129, mercenaries by type 153/175/196/218/239, all mercenaries 261, Find a city 285. **Dialogs can end up under the main window** (no window manager): the driver raises a dialog (`xdotool windowraise`) before clicking in it.

**Save As / Open**: the Wine common file dialog. The name field keeps the last name with the caret at the start, so the driver clears it (End, Shift+Home, BackSpace) before typing.

**Battle screen**: title `<A> v <B>`; *Computer general on* (158,112), *End turn* (110,112), result window "Battle ended", *OK* (220,478) (from `harness/battle_auto.sh`).

## 3. Messages and refusals

All 72 message strings in the executable's code segment, by the order that shows them. ✅ = seen in play (with the save), ⬜ = not yet seen.

| Where | Message | Seen |
|---|---|---|
| Army recruits | "You have reached your limit of 40 units." | ⬜ |
| Army recruits | "Your mobilisation rate is already 100%." | ⬜ |
| Army recruits | "You cannot mobilise a unit at this time." | ⬜ |
| Army recruits | "Are you sure you want to disband …" | ⬜ |
| Attack | "Are you sure you want to attack this city ?" (not shown when already at war: `T_ATTACK.SAV`) | ⬜ |
| Attack | "Are you sure you want to attack this army ?" | ⬜ |
| Attack | "Are you sure you want to attack this fleet ?" | ⬜ |
| Attack | "You cannot attack a fleet docked at its own city !" | ⬜ |
| Embark | "The army is too large for this fleet ?" | ⬜ |
| Mercenaries | "Your army has too little money to pay these mercenaries." | ⬜ |
| Mercenaries | "An army can not contain more than 100,000 troops." | ⬜ |
| Mercenaries | "This fleet has too little space for these mercenaries." | ⬜ |
| Mercenaries | "This army already has 20 units." · "This army cannot get any bigger." · "You cannot recruit from an enemy city." · "Your fleet cannot carry any more troops." | ⬜ |
| Transfer | "This army already has 20 units." · "An army can not hold more than 100,000 troops." · "This fleet can not carry any more troops." | ⬜ |
| Disband unit | "An army must be near its own city to disband a regular unit." | ⬜ |
| Change units | "You can only rename 1 unit at a time." · "You can only rename regular units." · "You can only split 1 unit at a time." · "You can only split regular units." · "This unit is too small to split." · "You can only join regular units together." · "You can only combine units of the same type." · "These units are too large to be combined." | ⬜ |
| Join armies | "An army on a fleet cannot be combined with another." | ⬜ |
| Split army | "You can not split an army containing only 1 unit." | ⬜ |
| Disband army | "An army must be near its own city to disband." · "Are you sure you want to disband this army ?" | ⬜ |
| Fleet | "The fleet can only be repaired at one of your cities." · "A fleet cannot be repaired while it is carrying an army." · "You cannot join fleets if one is carrying an army." · "You can not split a fleet containing less than 20 ships." · "You can not split a fleet carrying an army." · "You can not make any more fleets at this time." · "A fleet cannot be scuttled while it is carrying an army." · "To scuttle a fleet it must be near one of your cities." · "Are you sure you want to scuttle this fleet ?" | ⬜ |
| Build fleet | "The fleet will be built at …" · "… ships will be ready in …" · "You do not have a free coastal city at this time." · "You cannot build a fleet at this time." | ⬜ |
| Fortify | "You cannot fortify a city which is under siege." · "This city cannot be fortified any further." · "This city is already being fortified." | ⬜ |
| Relations | "You cannot trade with …" | ✅ `saves/trade-numidia-0720.SAV` (Ptolemaic, Seleucid, Greece, Celtiberia, Dacia) |
| Relations | "… does not want to make peace at this time." · "You can only trade with 3 nations." · "… does not want to trade with you." · "… does not want to ally with your nation." | ⬜ |
| End turn (warnings) | "An army of yours cannot afford to pay its mercenary units." · "One of your fleets is not docked at its own city." | ⬜ |
| Game over | "You have conquerred the Mediterranean, a unique achievement." · "You have reached the end of your allotted 20 years." · "Your army have deposed you because they have not been paid." | ⬜ |
| Battle | "Are you sure you want to surrender ?" | ⬜ |
| Game menu | "Are you sure you want to start a new game ?" · "… quit ?" · "… lead a different nation ?" · "… abdicate ?" | ⬜ |
| Turn start (AI offers) | "<Nation> wants to trade with Rome." | ✅ `BASE.SAV` turn 0720 (Bithynia), test end-turn turn 0721 (Celtiberia) |

## 4. Mechanics

| Mechanic | Status | Evidence |
|---|---|---|
| Deterministic turn under a fixed seed | ✅ | tests/results.md: `scripted_turn_repeats`; `findings/2026-09-29-loading-a-save-does-not-reseed.md` |
| Siege attempt, failure, attacker attrition, city erosion | ✅ | `T_ATTACK.SAV` (turn 0721) |
| City capture | ⬜ | |
| Defection cascade | ⬜ | |
| Conquest (a nation under 6 cities annexed) | ⬜ | |
| Field battle (tactical, Computer general) | ⬜ | |
| Post-battle peace offer | ⬜ | |
| Supply consumption and seasonal rates | ⬜ | |
| Winter attrition of city stocks | ⬜ | |
| Morale from supply | ⬜ | |
| Auto-resupply next to an own city | ⬜ | |
| Recruitment readiness and mobilization | ✅ | `saves/mobilize-new-army-0720.SAV` |
| Mercenary hire, pay, desertion | 🟡 hire only | `saves/merc-hire-free-0720.SAV` (no up-front price) |
| Quarterly billing and taxes | ⬜ | |
| Fortification build | 🟡 ordered | `saves/fortify-arretium-0720.SAV` |
| Trade income | 🟡 trade made | `saves/trade-numidia-0720.SAV` |
| Fleets: build, launch, storms, loss at sea | ⬜ | |
| Embark, disembark, supply from a fleet | ⬜ | |
| Rebellion, rebirth | ⬜ | |
| Weather | ⬜ | |
| AI declares war on Rome | ⬜ | |
