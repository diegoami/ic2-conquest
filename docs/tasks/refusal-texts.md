# Task: the original's refusal texts and their conditions (clone #721) (given 2026-10-05)

For imperial_conquest_2 #721 (post-0.5.0). The clone words several refusals its own way where the original's lines are known. The clone needs the complete list: each line verbatim, the condition that raises it, and the box it appears in.

## Scope
This task protects: **the exactness of every refusal line and condition the clone will copy.**
- Each line is the original's literal, byte for byte: spacing, punctuation, the space before "?" and typos included. It is read from the decompile's string literal at the call site, never retyped from memory or from help.
- Each condition is read from the code with its line cited (`[derived]`). A play confirmation (`[confirmed]`) cites its screenshot and save. The two are never mixed.

Forbidden results: a line not traced to its literal and call site; a condition without a code line; a play claim without its screenshot and save; a staged save not labelled as staged; a measured output overwritten or deleted; a binary in git; a write to another repository; processes killed by pattern.

## Read first
- `CLAUDE.md` (rules 1-6).
- `findings/2026-10-05-player-facing-feature-inventory.md`: rows L09 and L11, and the rows that quote refusals (UA04, UA05, UF05, D05, D06, S05, and the build-fleet, scuttle and disband rows).
- The clone issue: `gh issue view 721 --repo diegoami/imperial_conquest_2` (read only).
- The decompile (read only): `~/ic2-work/decompile/all_app_functions.txt` and `delphi_symbols.tsv`. The inventory's string dump `dump_string_literals.tsv` is in release `run-exp-feature-inventory` of this repository (`gh release download`).
- Examples of the layout: `runs/experiments/end_of_game/` (code extract, claims audit reading claims from the finding) and `runs/experiments/split_aboard/lib.py` (verified clicks, `keep_save`, `snap`).

## Questions
1. **Catalogue.** For every message box the game raises to refuse or limit a player's order (army, fleet, city, recruitment, mercenaries, relations, build fleet, change units, army to army, supply, split, join, embark, disband, scuttle, repair), give:
   - the literal verbatim;
   - the function and call-site line;
   - the box type and its buttons (MessageDlg type, or ShowMessage);
   - the exact condition (the test lines);
   - the order of the tests when an order can be refused for several reasons (which refusal shows first);
   - whether the order is then dropped or only clamped.
   Exclude the battle screen's boxes (battles are paused). List prompts (Yes / No / Cancel confirmations) separately from refusals.
2. **Play.** Confirm in Wine every refusal the clone words differently: UA04 split of a one-unit army, UA05 join over 20 units and over 100,000 troops, UF05 join fleets while one carries an army, D05 a unit too small to split, and D06 rename more than one unit or a mercenary unit. Then confirm as many others as staged saves allow in reasonable time. For each one, keep a screenshot of the box, the box text from OCR, and the save before and after (proving nothing changed, or what changed).
3. **Ordering.** Where two refusals can hold at once (for example join: over 20 units and over 100,000 troops), play one combined case and show which line appears.

## Work
- Branch `experiment/refusal-texts`; worktree `/home/diego/projects/wt-refusals`; your own Xvfb display (`:742`) and your own game folder (`~/ic2-work-refusals`, a copy of `~/ic2-work`).
- Data in `runs/experiments/data/run-exp-refusal-texts/`. Binaries go to release `run-exp-refusal-texts` as per-batch tar.gz files with a tracked manifest. Scripts go in `runs/experiments/refusal_texts/`.
- Driver pitfalls: hover before clicking; locate controls with `Game.controls` or OCR, never with fixed coordinates; verify every click's effect (memory, a window, or the save) and retry at most twice; never click End turn twice unless the first click provably did nothing; track each dialog by its X window id and bound the attempts (the last reviews blocked on exactly these points).
- **Finding:** `findings/2026-10-05-refusal-texts-and-conditions.md`, in the research-report format.
  - Method.
  - The catalogue as a table: id, order, literal, function and line, box and buttons, condition, effect, tag, evidence.
  - The prompts.
  - The orderings.
  - A table "the clone's line → the original's line" for the rows #721 lists.
  - "What this does not establish".
- **Claims audit** (`claims_audit.py`):
  - It reads every literal and condition claimed in the finding's tables, and compares each with the tracked code extract (the call-site line must contain that literal byte for byte) and with the tracked OCR readings and saves.
  - No expected result is typed into the checker.
  - Its tests show that a doctored literal in the finding (one changed space), a doctored extract line and a doctored save each fail it.

## Done when
- The catalogue covers every refusal call site in the listed form functions, with a count of literals found against literals catalogued, and every exclusion named with its reason.
- The five #721 rows are confirmed in play, and the combined-refusal case is played.
- The claims audit gives 0 mismatches and its tests pass.
- CLAUDE.md rule 6 holds throughout: commit and push after each batch and at least every 30 minutes; never delete or overwrite a measured output; saves and screenshots never go in git (their SHA-256 go in `SAVES.sha256`, the files go to the release); if a release call is refused, keep the files and report the exact command; never print `IC2_RELEASE_TOKEN`.

## Deliverables
One PR against main, "findings: the original's refusal texts and conditions". Its body maps every Done-when line to its evidence.
- Do not merge, and do not run the reviewer.
- If something blocks you, stop, commit and push what was measured, and report.
