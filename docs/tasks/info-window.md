# Task: the Information window, every field and its word bands (given 2026-10-05)

For the clone's v0.5.0: T140 "The information panels show the original's fields" (imperial_conquest_2 #728, bug #718) "starts after a research read of the Information window's word bands (`TInformation_Show*`)". This task is that read.

## Scope
This task protects: **the exactness of every field and band the clone will copy.**
- Each field's caption, value, formula, unit and format is read from the code.
- Each number-to-word band's exact thresholds and words are read from the code, with every edge confirmed or contradicted in play.
- Nothing is guessed from screenshots alone, and nothing is written to another repository.

Forbidden results (any one fails the task, and a reviewer will block on it):
- a band threshold or word not read from the code (comparison operator included: `<` versus `<=`);
- a field whose formula or source record field is stated without the code line;
- a band edge claimed as confirmed in play without a save and a screenshot at the value on each side of it;
- a [derived] field presented as [confirmed];
- a measured output overwritten or deleted, a binary in git, a write to another repository, a blind second End turn.

## Sources (all read-only)
- The decompile, `~/ic2-work/decompile/`:
  - `all_app_functions.txt`, with `delphi_symbols.tsv`;
  - the panel routines `TInformation_ShowNationStatus` 0x0043ba7c, `ShowCityDetails` 0x0043be5c, `ShowArmyDetails` 0x0043c33c, `ShowFleetDetails` 0x0043c890, `ShowCityUnits` 0x0043cc40, `ShowArmyUnits` 0x0043cdd8 and `ShowFleetUnits` 0x0043cf0c;
  - the helpers they call: word-band functions, number formatters such as `FUN_00448e74`, and string tables.
- The exe: `~/ic2-work/build/Imperial Conquest 2.exe`, for string literals.
- The research reports in `/home/diego/projects/imperial-conquest-2-research/docs/reports/`, especially `decompiled-sav-file-layout.md` and `decompiled-unit-map-orders-and-record-fields.md`, which give the record fields.
- This repository:
  - `findings/2026-10-05-player-facing-feature-inventory.md`, rows UM02, UM03, UM04, UM05, UM07, N03 and UM09, with their screenshots in release `run-exp-feature-inventory`;
  - `state/sav.py`;
  - `harness/driver.py`;
  - `runs/experiments/feature_inventory/explore_lib.py`, for runs.

## Priority (from the imperial_conquest_2 main session, 2026-10-05; T140 needs them in this order)
a. The number-to-word bands: unity (N03, the nation panel), loyalty and morale (UM02 city, UM03 army), and quality if it has a word.
b. What the city's fortification bracket counts. The help file and the rules digest disagree; settle it from the code and in play.
c. One army's "Regulars cost" and "Mercenary pay": the formula and its inputs.
d. What decides a fleet's Sea word, calm or rough. If no field or rule decides it, say so.
e. The foreign-nation panel's fields (clone #614): population, unity, tax rate and the relations row. Give their exact format, and say whether "peace" really shows blank.
Everything else in the panels comes after (a)-(e). Commit and push (a)-(e) first, so the coordinator can relay them early.

## Work
Branch `experiment/info-window`. Data goes in `runs/experiments/data/run-exp-info-window/`; scripts in `runs/experiments/info_window/`; binaries to release `run-exp-info-window` as per-batch tar.gz archives with a tracked manifest.

1. **Read every panel routine and its helpers.** For each line the panel prints, give:
   - the caption text;
   - the value's source (save record and offset, via `state/sav.py` names where they exist);
   - the formula, with integer division and rounding as written;
   - the unit and format (thousands separators, percent, padding);
   - when the line is shown or hidden (own versus foreign unit, capital, at war, and so on).

   For each word band, give the exact thresholds with their operators and every word, in order. Cover every word field: loyalty, unity, morale, quality, sea state and any other found.
2. **Confirm the bands in play.**
   - For each band edge, craft saves with an L1 edit through `state/sav.py` or `stage.py` (copies only, never a player run's saves): the value on each side of the edge.
   - Open each save on the normal build, click the city, army, fleet or nation, and capture the panel.
   - Read the word from the screenshot (OCR, then check by eye) and record it in a tracked table: value, expected word, seen word.
   - Also capture one foreign army and one foreign fleet, to see what a foreign panel shows.
3. **Write a claims audit** that recomputes every band row from the code extract and the tracked capture table: 0 mismatches.

## Deliverable
A findings draft, `findings/2026-10-05-information-window-fields-and-bands.md`, titled "The Information window: every field, its formula, and the number-to-word bands", in the research-report format. It has these sections:
- Method;
- one table per panel (nation, city, own army, foreign army, fleet, the unit lists): caption, source field, formula, format, condition;
- the band tables, one per word field, with each edge marked confirmed (citing save and screenshot) or derived;
- "Where the sources disagree" (help versus code);
- "What this does not establish".

Tag every claim `[O]`, `[D]` or `[R-code]`, and cite saves by bare filename.

## Done when
- Every line of every `TInformation_Show*` panel is in a table with a code citation. A coverage check lists every string literal and every called helper of those functions, each mapped to a table row or excluded with a reason, and reports 0 unaccounted.
- Every band edge of every word field is confirmed in play on both sides, or explicitly left [derived] with the reason it could not be staged.
- The claims audit reports 0 mismatches, and the offline tests and checks pass.
- CLAUDE.md rule 6 holds throughout.

## Rules (CLAUDE.md rule 6, in full)
Measurements are kept, committed and pushed as they are made, and never deleted.
- Every text output a finding or a PR may cite goes under the tracked data folder above.
- Commit and push after each batch, and at least every 30 minutes.
- A re-run writes new files beside the old ones: versioned writers, never overwrite.
- Saves, screenshots and exes never go in git: their SHA-256 go in `SAVES.sha256`, and the files go to the release.
- If a release call is refused, keep the artifacts and report the exact command.
- Never print `IC2_RELEASE_TOKEN`.
- Never write to another repository: the research repository, the decompile folder (`~/ic2-work/decompile/`) and `~/ic2-work/build` are read-only inputs.

Driver pitfalls: hover before clicking, verify every click's effect, retry at most twice, use your own Xvfb display and game folder, and kill only your own pids.

## Deliverables
One PR against main, "findings: the Information window, fields and word bands". Its body maps every Done-when line to its evidence. Do not merge, and do not run the reviewer. If something blocks, stop, commit what was found, and report.
