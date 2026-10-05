#!/usr/bin/env python3
"""Build findings/2026-10-05-player-facing-feature-inventory.md from the tracked rows, the coverage output and the prose below.
Usage: python3 runs/experiments/feature_inventory/build_findings.py"""
import os, re, collections, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import latest
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
D = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-feature-inventory')
rows = []
for l in open(os.path.join(D, 'inventory_rows.psv'), encoding='utf-8').read().split('\n')[1:]:
    if l.strip():
        f = l.split('|'); rows.append(dict(zip(('id', 'group', 'name', 'what', 'pre', 'evidence', 'tag', 'need'), f)))
ORDER = ['Main window and menu bar', 'File', 'Game', 'Strategy', 'Nations', 'Area map', 'Unit map > Army', 'Unit map > Fleet', 'Unit map > City',
         'Unit map (view and selection)', 'Help', 'Map mouse actions', 'Keyboard shortcuts', 'Dialogs reached from other dialogs',
         'Turn-start and turn-end events', 'News and messages', 'Victory and defeat', 'End-of-game screens']
assert {r['group'] for r in rows} <= set(ORDER), {r['group'] for r in rows} - set(ORDER)
idx = {r['id']: i for i, r in enumerate(rows)}
rows.sort(key=lambda r: (ORDER.index(r['group']), idx[r['id']]))
report = open(latest(os.path.join(D, 'coverage_report.txt'))).read()
cov = [l for l in report.split('\n') if re.match(r'^(form|control|toolbar|menu|help_cnt|help_topic|msgfn|string|news|ALL)\s', l)]
cell = lambda s: s.replace('|', '/').replace('\n', ' ')
nrows = len(rows)
bygroup = collections.OrderedDict((g, collections.Counter()) for g in ORDER)
for r in rows: bygroup[r['group']][r['tag']] += 1; bygroup[r['group']]['n'] += 1
tags = collections.Counter(r['tag'] for r in rows); needs = collections.Counter(r['need'] for r in rows)

P = []
P.append('# Player-facing feature inventory of the original (battle excluded)\n')
P.append('**Status:** draft finding from `ic2-conquest` (branch `experiment/feature-inventory`), awaiting promotion. Task: `docs/tasks/feature-inventory.md`. '
         '**Wine-only where a run is cited:** the runs are the original `Imperial Conquest 2 fast rollingsave seed.exe` under Wine 9.0; nothing here was seen on a desktop Windows install. '
         'The clone (`imperial_conquest_2`) was not available on this machine and was not read.\n')
P.append('## Answer\n')
P.append('- **%d feature rows**, in the groups the task names, each with a tag earned by its cited evidence: **%d [confirmed]** (a save, a screenshot or a `coverage.md` row) and **%d [derived]** (a function, a form, a help topic or a report section); **no [candidate]**. '
         'No row is inferred from the clone; inferences are in their own section.' % (nrows, tags['[confirmed]'], tags['[derived]']))
P.append('- **Coverage:** every source entry (UI entries, message families and a rules-and-events family swept from the rules digest, `coverage.md` §4 and the report titles) is mapped to a row or to a stated exclusion, **0 unaccounted**, recomputed from tracked inputs by `runs/experiments/feature_inventory/coverage_check.py` (totals below, versioned output tracked, self-test included).')
P.append('- **Every unwired item of the clone has an original row** (table "The clone\'s unwired items"); none is "no such feature in the original".')
P.append('- **Four things the sources disagree on or hide**, found on the way: the `TAFSupply` form (the Supply army / Supply fleet dialog, which the task\'s `TAF*` exclusion would have dropped, and which has a **Buy supplies** button); '
         'the About box\'s misspelled **CAncell** button opens a **Cellular Automata** window (seen in Wine); the shortcut for the leader\'s capital is **Ctrl+Q** in the code and in Wine, **Ctrl+P** in the help file; '
         'and **Split army** reuses the army-to-army transfer form.\n')
P.append('## Method\n')
P.append('- **Extraction (scripts in `runs/experiments/feature_inventory/`, outputs in `runs/experiments/data/run-exp-feature-inventory/`).**')
P.append('  - `extract_forms.py`: reads every `TPF0` form resource of `Imperial Conquest 2.exe` (29 forms, 908 controls: `forms.json`, `form_controls.tsv` with captions, hints, event handlers and Delphi `ShortCut` values decoded to `Shift+W` etc.). The `TMainMenu` stream is inside `TPremierForm`. **Every extractor and EXPLORE script writes through `common.write_new` or a versioned screenshot path and refuses to overwrite: a re-run writes `<name>.v2.<ext>` beside the old file (rule 6); readers use the newest version.**')
P.append('  - `form_xrefs.py`: finds each form\'s VMT and every reference to it, so "reached from" claims come from code (`form_xrefs.tsv`).')
P.append('  - `extract_dump_strings.py` and `extract_strings.py`: every string literal of the whole-application Ghidra dump by function (`dump_string_literals.tsv`: 376 literals with a letter; `dump_string_literals.v2.tsv`: 485 literals in 106 functions, now including punctuation-only ones such as the single space and the 59-dash banner that the news check needs) and every `AnsiString` literal of the exe (`exe_strings.tsv`); `delphi_symbols.tsv` is a copy of the symbol table.')
P.append('  - `hlp_dir.py`, `hlp_topics.py`, `extract_help.py`, `hlp_check.py`: a small WinHelp 3.x reader written for this task (no tool installed): directory B+tree, LZ77 topic blocks, the Win95 phrase table (`|PhrIndex`, `|PhrImage`). The phrase-code decoder is **recovered empirically**, not from a specification: the text is readable but loses a few characters in most paragraphs (`help_decode_check.txt`: 66 of 247 compressed records have the declared length). Outputs: `help_topics.tsv` (71 topics), `help_contents_entries.tsv` (the 89 `.cnt` entries; the `.cnt` itself is a game file and is not tracked). The WinHelp viewer of Wine shows the real text (`FI_b1_06_help_topics.png`).')
P.append('  - `show_fn.py` prints a function of the dump by name or address; `extract_report_titles.py` snapshots the research reports\' titles (`report_titles.tsv`) for the rules sweep.')
P.append('- **Existing reports first.** Rows cite the research repository\'s `docs/reports/` (`R:`), this repository\'s `findings/` (`F:`), `coverage.md` (`C:`) and `tests/results.md`; nothing of them is redone.')
P.append('- **EXPLORE batch 2 (rework, Wine, about 15 minutes, `explore_b2.py`).** The three Unit-map submenus are located by OCR, hovered and **proven open (expected item names read back, hash different from the parent menu) before the screenshot is kept**: the batch-1 Fleet and City submenu shots were byte-identical to the parent menu (same SHA-256) and no row cites them any more. It also shows the **Show hints** toggle (the speed-button hint present, absent after one click, back after a second) and runs the Shift and Ctrl map keys while another nation is viewed. 18 screenshots, `MANIFEST-batch2.txt`, release asset `FI_batch2_screenshots.tar.gz`.')
P.append('- **EXPLORE batch 1 (Wine, about 40 minutes, own Xvfb `:700`, own copy of the game folder, fixture `BASE.SAV` = the run-0 start, seed 12345; scripts `explore_*.py`, text log `explore/b1.log`).** It settled what the sources left open: the Help menu, About and its CAncell button, Help topics, New player / New nation / Abdicate prompts, every menu, Balance sheet, Find a city, the nation status panel (own and foreign), Show mercenaries, a city\'s left and right click, Ctrl+Q against Ctrl+P. No End turn was clicked, no order was issued, no player save was touched. 43 screenshots, hashed in `SAVES.sha256`, are in the release `run-exp-feature-inventory` as `FI_batch1_screenshots.tar.gz` with the tracked `MANIFEST-batch1.txt`.')
P.append('- **Evidence labels in the table.** `R:` research report and section; `F:` finding of this repository; `C:§n` a `coverage.md` row; `X:` a function of the dump (addresses in `delphi_symbols.tsv`); `form` a `TPF0` resource; `H:` a help topic; `SS:` a screenshot of batch 1 (bare file name). Saves are cited by bare file name (`T_*.SAV` are the order-test saves of `tests/results.md`).')
P.append('- **Tags.** `[confirmed]`: seen in play, with a save, a screenshot listed in the tracked manifest, or a `coverage.md` row with status ✅ cited; **a report or a log is never confirmation**. The tag covers what the cited evidence shows; sentences marked `[code]`, `[help]`, `[report]` or `[form]` inside a row are attributed to that source and were not tested, and the Preconditions column comes from the cited code, help or report unless a save is named. `[derived]`: read from the code, a form, a help topic or a report, not seen in play here. `[candidate]`: reserved for Wine-only or inferred; none needed.')
P.append('- **Need.** needed / useful / cosmetic is the author\'s reading of whether a player needs the feature to play a game end to end; it is a judgment, not evidence (see Inferences).\n')
P.append('## The inventory table\n')
P.append('Columns: name the original uses (exact caption where there is one), what it does, preconditions, evidence, tag, need. Row counts per group and tag are in the next section.\n')
for g in ORDER:
    gr = [r for r in rows if r['group'] == g]
    if not gr: continue
    P.append('### %s\n' % g)
    P.append('| Id | Name | What it does | Preconditions | Evidence | Tag | Need |')
    P.append('|---|---|---|---|---|---|---|')
    for r in gr:
        P.append('| %s | %s | %s | %s | %s | %s | %s |' % tuple(cell(r[k]) for k in ('id', 'name', 'what', 'pre', 'evidence', 'tag', 'need')))
    P.append('')
P.append('## Row counts\n')
P.append('| Group | Rows | [confirmed] | [derived] |')
P.append('|---|---:|---:|---:|')
for g, c in bygroup.items():
    P.append('| %s | %d | %d | %d |' % (g, c['n'], c['[confirmed]'], c['[derived]']))
P.append('| **All** | **%d** | **%d** | **%d** |\n' % (nrows, tags['[confirmed]'], tags['[derived]']))
P.append('By need: needed %d, useful %d, cosmetic %d.\n' % (needs['needed'], needs['useful'], needs['cosmetic']))
P.append('## Coverage totals\n')
P.append('Recomputed by `python3 runs/experiments/feature_inventory/coverage_check.py` from the tracked extracts, `coverage_map.cfg` and `news_templates.cfg`; output in `coverage_report.txt` and `coverage_entries.tsv` (one line per entry with its rule and rows). '
         'An entry is *mapped* to rows or *excluded* with a stated reason; the exclusions are the tactical battle (`TBattleMap`, `TBattleDelays` and their strings and help topics), decoration (bevels and image strips), menu separators, contents headings without a topic, two prose help pages (Improvements, Fonts) and two empty topic records.\n')
P.append('```text'); P.extend(cov); P.append('```\n')
P.append('`control` counts every control of every form, including menu items and speed buttons; `menu` and `toolbar` list those two again as the task asks. '
         '`msgfn` is one entry per game function that holds string literals (the message families: confirmations, refusals, panel text, news writers); `string` is the two exe literals no function claims ("Fleet\'s", a label of the Supply dialog); `news` is the 21 news templates of `R:news-log-format-and-messages.md` Q4 plus the DAT seed and the offer dialog, each template\'s exact literal found in the function named for it; `rule_head`, `mechanic` and `report` are the rules family of the next section. '
         'The script also validates every row\'s tag against its evidence (see "The checker\'s own test"): 0 violations.\n')
P.append('## The clone\'s unwired items and the original rows\n')
P.append('| Clone item | Original caption | Original row | Notes |')
P.append('|---|---|---|---|')
for a in [
 ('Unit map > Army > Supply army', 'Supply army (help and speed button: Supply army)', 'UA01, D01', 'Dialog TAFSupply with providers (cities and own fleets one tile away), supply and money spinners and a Buy supplies button.'),
 ('Unit map > Army > Recruit mercenaries', 'Recruit mercenaries', 'UA02, D02', 'Dialog "Recruit mercenary unit"; opens only when an offer is within one tile.'),
 ('Unit map > Army > Transfer unit', 'Transfer unit (menu), Transfer units (speed button, help)', 'UA03, D03', 'Dialog "Army to army transfer".'),
 ('Unit map > Army > Split army', 'Split army', 'UA04, D03', 'Reuses the army-to-army dialog, titled "Split army".'),
 ('Unit map > Army > Join armies', 'Join armies', 'UA05', 'No dialog.'),
 ('Unit map > Army > Change units', 'Change units', 'UA06, D05, D06, D07', 'Rename unit, Split unit, Join units, Disband.'),
 ('Unit map > Army > Disband army', 'Disband army', 'UA07', 'Confirmation box.'),
 ('Unit map > Fleet > Supply fleet', 'Supply fleet', 'UF01, D01', 'Same TAFSupply form, titled "Supply fleet".'),
 ('Unit map > Fleet > Repair fleet', 'Repair fleet', 'UF02', 'Dialog "Repair fleet".'),
 ('Unit map > Fleet > Transfer ships', 'Transfer ships', 'UF03, D04', 'Dialog "Fleet to fleet transfer".'),
 ('Unit map > Fleet > Split fleet', 'Split fleet', 'UF04, D04', 'Same dialog, titled "Split fleet".'),
 ('Unit map > Fleet > Join fleets', 'Join fleets', 'UF05', 'No dialog.'),
 ('Unit map > Fleet > Scuttle fleet', 'Scuttle fleet', 'UF06', 'Confirmation box.'),
 ('Unit map > City > Fortify city', 'Fortify city', 'UC01', 'Dialog "Fortify city"; the city must be selected by a click.'),
 ('Area map > Show mercenaries', 'Show mercenaries (submenu: Light infantry ... All mercenaries; help: All types)', 'A07, UM07', 'Six items, each also an Area-map speed button; the per-city list is the right click (UM07).'),
 ('Strategy > Taxation', 'Taxation', 'S03', 'Slider 0 to 40.'),
 ('Strategy > Balance sheet', 'Balance sheet', 'S04', 'Read-only; Shift+B.'),
 ('Strategy > Recruit unit', 'Recruit unit (dialog "Army recruits")', 'S05, S05a, S05b', 'Recruit, Mobilize, Disband.'),
 ('Strategy > Build fleet', 'Build fleet', 'S06', 'Dialog "Build fleet".')]:
    P.append('| %s | %s | %s | %s |' % a)
P.append('\nAll 19 clone items have an original row. None is "no such feature in the original".\n')
P.append('## Original features that no menu item lists\n')
P.append('The clone could not be read, so "features the clone\'s menu never listed" is answered from the original side: features the original has that **none of its own menus lists**, which a clone built only from the menu would miss, plus the original features outside the task\'s list of unwired items.\n')
P.append('| Feature | Row | How the original reaches it |')
P.append('|---|---|---|')
for a in [
 ('Toggle colour (mono / terrain map)', 'A01', 'Area-map speed button only; no menu item'),
 ('Cellular Automata window', 'H04', 'About box > CAncell; no menu item'),
 ('Right-click lists: units of an army, mercenaries of a city', 'UM06, UM07', 'mouse only'),
 ('Select, move, attack, embark, disembark by clicks', 'MM01-MM09', 'mouse only (the Unit map menu only holds the orders that need a dialog)'),
 ('Buy supplies from a foreign city', 'UA01', 'button inside the Supply dialog'),
 ('Click on the Area map to move the Unit map; the unit-map rectangle', 'A09, A10', 'mouse only'),
 ('Nation status of the current / own nation', 'K02, N03', 'Shift+N, Ctrl+N, or choosing a nation'),
 ('Own-nation area-map keys', 'K03', 'Ctrl+C, A, F, L, N, Q'),
 ('"End turn ?" warning box', 'D08, L12', 'raised by End turn'),
 ('Post-battle Offer of peace (and the two-human variant)', 'D09, D10', 'raised by a tactical battle'),
 ('Turn-start diplomatic offer box', 'E01', 'raised at the start of a human turn'),
 ('New player, New nation, Abdicate', 'G02-G04', 'Game menu (not in the task\'s list)'),
 ('News, International relations, Find a city, Cancel selection, All nations', 'S01, S02, A08, UA08, N02', 'menus (not in the task\'s list)'),
 ('Help topics, Show hints, About', 'H01-H03', 'Help menu'),
 ('End of Game screen and the three ways to reach it', 'EG01, V01-V04', 'event')]:
    P.append('| %s | %s | %s |' % a)
P.append('')
P.append('## Where the sources disagree\n')
P.append('| Item | One source says | Another says | Seen |')
P.append('|---|---|---|---|')
for a in [
 ('Shortcut for the leader\'s capital', 'help "Short cut keys": Ctrl+P', 'code `TPremierForm_KeyPressed` handles Ctrl+Q (and no Ctrl+P)', 'Wine: Ctrl+Q drew the capital, Ctrl+P changed nothing (`FI_b1_30_area_ctrl_q.png`, `FI_b1_30_area_ctrl_p.png`)'),
 ('Name of the army transfer command', 'menu: "Transfer unit"', 'speed-button hint and help: "Transfer units"', 'form data and `FI_b1_13_menu_unit_army_submenu.png`'),
 ('Name of the city search', 'menu and hint: "Find a city"', 'help topic and dialog title: "Find city"', 'form data, `FI_b1_17_find_city_dialog.png`'),
 ('Last mercenary view', 'menu and hint: "All mercenaries"', 'help: "All types"', 'form data, `FI_b1_12_menu_area_mercs_submenu.png`'),
 ('Nation panel of the own nation', 'help: unity, population, cities, treasury, tribute paid, trade earned, tax rate, mobilisation', 'the panel shows Nation, Leader, Capital, Cities, Population, Unity, Tax rate, Mobilized, Treasury (no tribute, no trade)', '`FI_b1_21_nation_rome.png`'),
 ('Join fleets', 'help: at most one (or neither) fleet may carry an army; total not larger than 100', 'code `TUnitMap_JoinFleets`: refuses when either fleet carries an army; refuses when the sum is 101 or more', 'row UF05'),
 ('Join armies troop limit', 'help: combined troops less than 100,000', 'code string: refuses "more than 100,000" (100,000 itself is allowed)', 'row UA05'),
 ('The number after the fortification percentage', 'read as a fortification value', 'help topic Cities: the troops training at the city (the recruitment queue)', 'row UM02, `FI_b1_24_city_left_click.png`'),
 ('Ctrl+C, A, F, L, Q', 'help: the leader\'s cities, armies, fleets, all, capital', 'code: the same handlers as the Shift keys, acting on the selected nation', 'row K03, `FI_b2_05_carthage_viewed_ctrl_q_after.png` (viewing Carthage)'),
 ('Terms of the human Offer of peace', 'the form `TBattlePols` holds reparation and end-trade text branches', 'the gate in `TBattleOver_OK` lets only the honourable treaty through (R:decompiled-war-cascade-and-peace-paths.md §2.3)', 'row D09'),
 ('Which forms are tactical battle', 'task: `TAF*` excluded with `TBattle*`', '`TAFSupply` is the Supply army / Supply fleet dialog (strategic)', '`form_xrefs.tsv`: opened from `TUnitMap_SupplyArmy` and `TUnitMap_SupplyFleet`')]:
    P.append('| %s | %s | %s | %s |' % a)
P.append('')
sweep = [r for r in rows if re.match(r'E(1[2-9]|2[0-9])$', r['id'])]
P.append('## Rules and automatic events found by the completeness sweep\n')
P.append('Mapping every extracted UI entry does not show that the strategic rules are complete. The sweep therefore adds a **rules family** to the coverage: every heading of `docs/rules-digest.md`, every mechanic of `coverage.md` §4 and every title in the research repository\'s `docs/reports/` (92, snapshot in `report_titles.tsv`) is an entry, mapped to rows or excluded (tactical battle, harness, save formats). It found rules with no row, now rows (all `[derived]`, from reports and code; none was run here, and `coverage.md` §4 lists most as not yet seen):\n')
P.append('| Id | Feature | Source |')
P.append('|---|---|---|')
for r in sweep:
    P.append('| %s | %s | %s |' % (r['id'], cell(r['name']), cell(r['evidence'])))
P.append('\nThe two the review named are E12 (automatic resupply on a move) and E13 (rebellion and rebirth); the caveat for each is its `coverage.md` §4 line, not yet seen on a controlled save.\n')
P.append('## The checker\'s own test\n')
P.append('`coverage_check.py` runs from tracked files only (extracts, `coverage_map.cfg`, `news_templates.cfg`, `coverage.md`, `docs/rules-digest.md`, `saves/`, `findings/`, the manifests); it no longer reads the Ghidra dump. News templates are matched **exactly** against the literals of the function named for them. Tags are validated strictly (manifest screenshots, named saves, ✅ `coverage.md` rows; duplicate hashes refused unless declared in `same_screen.cfg`). `coverage_selftest.py` feeds it bad rows and bad literals; its output is `coverage_selftest_output.txt`:\n')
P.append('```text'); P.extend(open(latest(os.path.join(D, 'coverage_selftest_output.txt'))).read().rstrip('\n').split('\n')); P.append('```\n')
P.append('## Inferences\n')
P.append('Nothing in the table rests on these.\n')
P.append('- **Need column.** "needed" marks what the author judges a player must be able to do to finish a game: end the turn, move and attack, recruit and mobilize, tax, relations, supply, fortify, build fleets and embark (the help says a fleet is essential to cross seas), and the end-of-game screens. This is a judgment from the help text and the rules digest, not a measurement.')
P.append('- **Cellular Automata.** A window reached only through a misspelled button of the About box is probably a development leftover or an easter egg; the code gives no purpose. The row is "cosmetic" on that reading.')
P.append('- **Show hints.** The item is ticked by default and the main form has `ShowHint = True`; that it switches the speed-button hints on and off is read from its name, not tested.')
P.append('- **Two empty help topics.** The last two topic records have no title and no text in the decoder; they are probably images or jump targets, not pages a player reads.')
P.append('- **A clone check.** A clone that wires every row marked `[confirmed]` or `[derived]` as "needed" and "useful" reaches every order of the original; whether it then plays "end to end" depends on rows outside this inventory (the tactical battle).\n')
P.append('## What this does not establish\n')
P.append('- **The clone.** It was not on this machine; the answer to "which features the clone\'s menu never listed" is given from the original side only.')
P.append('- **The tactical battle** is excluded as asked (`TBattleMap`, `TBattleDelays`, their strings and help topics). `TBattleOver` is listed once (row D11).')
P.append('- **Desktop Windows.** Every `[confirmed]` row was seen under Wine 9.0 with the patched `fast rollingsave seed` build, not on the original install.')
P.append('- **`[derived]` rows were not run.** In particular: File > Save (the driver uses Save As), the Area-map armies / fleets / all views, the foreign-army panel, the fleet panel, the human-against-human peace box, the AI alliance line, the capital-move and fleet-launch news lines, the quarterly tick, supply use by season, victory at 334 cities, the 250 BC end, conquest, and both deposition screens. `coverage.md` §4 lists most of them as not yet seen.')
P.append('- **Help text.** The decoder is empirical and loses characters (`help_decode_check.txt`); it was used for captions, numbers and nouns, and the Wine WinHelp viewer was shown for the first topic only.')
P.append('- **The 71 decoded topics versus the 89 `.cnt` entries.** The `.cnt` repeats topics (a command is listed under Menu Commands and again under Area map or Unit map) and has 13 headings with no topic; the mapping is by title and is in `coverage_entries.tsv`.')
P.append('- **Whether each help claim holds in play** (for example the 15 percent supply rule for mercenaries, the 1,000-talent cap on money moved while supplying): cited from help and code, not measured here.')
P.append('- **The sweep rows E12 to E29 were not run.** They are `[derived]` from reports and code; the completeness claim is bounded by the three sources swept (rules digest, `coverage.md` §4, the report titles) and by whatever those omit.')
P.append('- **Win and defeat rows** come from `THumanFalls_InitializeForm` and the reports; none was reached in play.\n')
P.append('## Reproduction\n')
P.append('```text')
P.append('python3 runs/experiments/feature_inventory/extract_forms.py   ~/ic2-work/build/"Imperial Conquest 2.exe" runs/experiments/data/run-exp-feature-inventory')
P.append('python3 runs/experiments/feature_inventory/extract_help.py    ~/ic2-work/prefix/drive_c/IC2/"Imperial Conquest 2.hlp" ~/ic2-work/prefix/drive_c/IC2/"Imperial Conquest 2.cnt" runs/experiments/data/run-exp-feature-inventory')
P.append('python3 runs/experiments/feature_inventory/coverage_check.py --check   # tracked inputs only; compares with the newest tracked version')
P.append('python3 runs/experiments/feature_inventory/coverage_selftest.py       # bad inputs must be rejected')
P.append('python3 runs/experiments/feature_inventory/build_findings.py          # regenerates this file from the rows')
P.append('```')
P.append('Release: <https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-feature-inventory> (batch 1 and 2 screenshots).')
out = os.path.join(ROOT, 'findings', '2026-10-05-player-facing-feature-inventory.md')
open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
print('wrote', out, len(P), 'blocks;', nrows, 'rows')
