# Task: player-facing feature inventory of the original (battle excluded) (given 2026-10-05)

A research request from the imperial_conquest_2 main session, relayed by the player. The clone's v0.5.0 "Playable" release must let a
player play a scenario end to end with every one of the original's orders reachable. This inventory is what the clone is checked against.

## Scope
This task protects: **the completeness and the honesty of the inventory.**
- Every player-facing feature the original offers, outside the tactical battle, appears as a row.
- Each row's confidence tag is earned by its evidence, never by inference dressed as fact.
- Nothing is written to imperial_conquest_2 or the research repository.

Forbidden results (any one fails the task, and a reviewer will block on it):
- A form or dialog class, menu item, toolbar button, help topic or news/message string family found in the sources that has no row and
  no stated reason for leaving it out. The coverage check below must show 0 unaccounted entries.
- A row tagged `[confirmed]` without a cited save, screenshot or `coverage.md` row showing it in play.
- A row tagged `[derived]` without a cited function or form name, or a report and section.
- A behaviour, precondition or name inferred from a clone's menu, or from what "a game like this" would have, stated as the original's.
- An inference outside the "Inferences" section. The table holds evidence only.
- A write to another repository, a binary in git, a measured output overwritten or deleted, a blind second End turn, or a run on a
  player run's saves.

## Sources (in this order; all read-only)
1. **The decompile.**
   - The whole-application Ghidra dump: `/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt`, about 1,900 functions.
   - The recovered Delphi RTTI symbols: `delphi_symbols.tsv` / `.json`, 282 methods across 31 classes.
   - The topic dumps beside them: `news_log_decomp.txt`, `calendar_and_endturn.txt`, `army_recruits.txt`, `army_to_army.txt`, etc.
   - The exe itself, `~/ic2-work/build/Imperial Conquest 2.exe`. Read only. Its `TPF0` form resources, the `TMainMenu` stream and the
     string literals can be read with a script; the research repo's `menu-and-toolbar-inventory.md` says where.
   - Every form and dialog class except `TAF*` and `TBattle*` (the tactical battle) gets its controls listed.
   - Note: `TBattlePols`, the post-battle Offer of peace, is strategic and stays in scope. `TBattleOver`, the result box, is the
     boundary; list it once.
2. **The help file.**
   - `~/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.cnt` is plain text: the table of contents.
   - `Imperial Conquest 2.hlp` is WinHelp. Extract its topic titles and text with a small script or `strings`. If a proper decompiler
     is needed, `helpdeco` may be built in a scratch folder; do not install anything system-wide.
3. **The existing reports**, in `/home/diego/projects/imperial-conquest-2-research/docs/reports/` (read only). Use them; do not redo them.
   Especially:
   - `menu-and-toolbar-inventory.md` and `impconq2-initial-report.md`;
   - `2026-10-02-unit-map-mouse-orders-and-tax-range.md` and `decompiled-unit-map-orders-and-record-fields.md`;
   - `news-log-format-and-messages.md`, `ptolemy-run-news-log-vocabulary-verified.md` and `decompiled-news-log-identified.md`;
   - `decompiled-diplomacy-peace-terms-and-instant-battles.md` and `decompiled-ai-offers-to-human-seats.md`;
   - `decompiled-elimination-cleanup.md`;
   - the economy, naval and siege reports.
   Also this repository's `coverage.md`, `docs/rules-digest.md` and `findings/`.
4. **Short EXPLORE runs under Wine**, only where a feature's behaviour is unclear and a run would settle it. Mark such rows `[candidate]`
   until the run, and `[confirmed]` after it, citing the save or screenshot.
   - Budget: at most about 1 hour of runs in total.
   - Use the normal build (`... fast rollingsave seed.exe`), from fixtures or experiment saves only.
   - Use your own Xvfb display and game folder.

## Inventory table
One row per feature, grouped by where the player meets it:
- main menu; File; Game; Strategy; Nations;
- Area map; Unit map (Army, Fleet, City); Help;
- map mouse actions; keyboard shortcuts; dialogs reached from other dialogs;
- turn-start and turn-end events; news and messages;
- victory and defeat; end-of-game screens.

Columns:
- the name the original uses (exact caption);
- what it does, in one or two lines;
- its preconditions (for example within one tile, own city, not at war);
- its evidence: the function or form name, the help topic, or the report and section; for `[confirmed]`, the save or screenshot;
- its tag: `[confirmed]` seen in play, `[derived]` from the code, or `[candidate]` Wine only or inferred;
- whether a player needs it to play a game end to end: needed, useful, or cosmetic.

## Coverage check (makes "complete" checkable)
Write a tracked machine-readable list of every source entry, each mapped to its inventory row or to a stated exclusion, and a script that
recomputes it. Report the totals; a reviewer will rerun the script. The entries are:
- each form class and its controls;
- each menu item and toolbar button;
- each help topic in the `.cnt`;
- each news/message string family.

## Work
Branch `experiment/feature-inventory`. The first commit is this task file, already pushed.
- Data goes in `runs/experiments/data/run-exp-feature-inventory/`: the extracts (menu, forms, strings, help topics), the coverage list,
  any run's logs.
- Scripts go in `runs/experiments/feature_inventory/`.
- Any saves or screenshots go to release `run-exp-feature-inventory`, as per-batch tar.gz archives with a tracked manifest. GitHub caps
  a release at 1000 assets.

## Deliverable
The findings draft `findings/2026-10-05-player-facing-feature-inventory.md`, titled "Player-facing feature inventory of the original
(battle excluded)", in the research-report format. Its sections:
- Method;
- the inventory table;
- the coverage totals;
- Inferences, kept apart;
- "What this does not establish".

It must also list, for the clone's known unwired items, the matching original rows:
- Unit map > Army: Supply army, Recruit mercenaries, Transfer unit, Split army, Join armies, Change units, Disband army;
- Unit map > Fleet: Supply fleet, Repair fleet, Transfer ships, Split fleet, Join fleets, Scuttle fleet;
- Unit map > City: Fortify city;
- Area map > Show mercenaries;
- the Strategy dialogs (Taxation, Balance sheet, Recruit unit, Build fleet).

## Done when
- Every source entry is mapped. The coverage script reports 0 unaccounted entries, and its output is tracked.
- Every row has a tag earned by its cited evidence: `[confirmed]` cites a save, screenshot or `coverage.md` row; `[derived]` cites a
  function, form or report section.
- The draft has the sections above, and the clone's unwired items are mapped to original rows (or marked "no such feature in the
  original", with evidence).
- Any run's saves are released and hashed (`SAVES.sha256`) and cited by bare file name.
- CLAUDE.md rule 6 holds throughout.

## Rules (CLAUDE.md rule 6, in full)
Measurements are kept, committed and pushed as they are made, and never deleted.
- Every text output a finding or PR may cite goes under the tracked data folder above.
- Commit and push after each batch, and at least every 30 minutes.
- A re-run writes new files beside the old ones.
- Saves, screenshots and exes are never in git: their SHA-256 go in `SAVES.sha256`, and the files go to the release.
- If a release call is refused, keep the artifacts and report the exact command.
- Never print `IC2_RELEASE_TOKEN`.
- Never write to another repository; the research repo and the ReTools folder are read-only inputs.

## Deliverables
One PR against main, "findings: player-facing feature inventory of the original (battle excluded)". Its body maps every Done-when line to
its evidence. Do not merge, and do not run the reviewer. If something blocks, stop, commit what was found, and report.
