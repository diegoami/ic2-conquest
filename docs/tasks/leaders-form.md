# Task: the original's "Human and computer leaders" form (clone #719) (given 2026-10-06)

For imperial_conquest_2 #719 (post-0.5.0). The clone's New Game makes one human seat and keeps each nation's leader name. The
original's leaders form (TPickLeaders, inventory row F02) ticks several humans and edits the names. The clone needs the form's
exact behaviour: what it shows, what it accepts and refuses, and what it writes into the game.

## Scope
This task protects: **the exactness of every rule of the form the clone will copy** (layout and captions, defaults, which
ticks and names are accepted or refused and with which text, what OK and Cancel do, and where the result lands in the game
state).
- Each rule is read from the code with its line cited (`[derived]`), or seen in play with its screenshot and save
  (`[confirmed]`). The two are never mixed. Captions and box texts are the original's literals, byte for byte, read from the
  decompile's string literal or from the form's resources, never retyped from memory.

Forbidden results: a rule with neither a code line nor a play behind it; a play claim without its screenshot and save; a
staged save not labelled as staged; a measured output overwritten or deleted; a binary in git; a write to another repository;
processes killed by pattern; a click at a guessed or fixed position.

## Read first
- `CLAUDE.md` (rules 1-7).
- The clone issue: `gh issue view 719 --repo diegoami/imperial_conquest_2` (read only).
- `findings/2026-10-02-two-human-seats.md` (two humans ticked, the human flags in the save, the turn order) and
  `runs/experiments/two-humans/` (`Game.new_game(rows=[...])`).
- The research report `docs/reports/ptolemy-run-ui-inventory-and-leader-draw.md` §2 in
  `/home/diego/projects/imperial-conquest-2-research` (read only): names drawn per game from what looks like a per-nation pool,
  editable text boxes.
- `findings/2026-10-05-player-facing-feature-inventory.md` row F02 (and G02-G04 for context only).
- The decompile (read only): `/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt` and `delphi_symbols.tsv`. The
  form's handlers: `TPickLeaders_InitializeForm` 0x004571a8, `TPickLeaders_HumanOrComputer` 0x0045730c, `TPickLeaders_OK`
  0x00457404, `TPickLeaders_Cancel` 0x00457590; follow their callers and callees (New Game, and where the draw happens).
- Layout and method to copy: `runs/experiments/refusal_texts/` (code extract, claims audit, verified runner `Game2.open`,
  recorded clicks, `test_runner.py` guard against guessed clicks) and `findings/2026-10-05-refusal-texts-and-conditions.md`.

## Questions
1. **The form.** Its caption, every control (class, caption, order on screen, tab order if read from the code), the
   per-nation row (nation name, human tick box, leader name box), the defaults when it opens from New Game (which rows are
   ticked, which names are shown, when they are drawn), and what `HumanOrComputer` does (greying, enabling, what changes in a
   row when a tick is set or cleared).
2. **Names.** The name box limits (maximum length, allowed characters), and what happens to an empty name, a name of spaces,
   a duplicate name and a very long name: accepted, refused with which text, or changed. Whether an edited name for a
   computer nation is possible and kept. Where the name lands (the nation record's offset in memory and in the save) and where
   it shows (title bar, news lines).
3. **Ticks.** What OK does with 0, 1, several and all 16 humans ticked: accepted or refused, with which text; what the human
   flags in the save become; who plays first.
4. **OK and Cancel.** What each does (back to which screen, what is kept or discarded), and the order of the checks in `OK`
   when several could fail at once (play one combined case if there is one).
5. **The draw.** From the code: where the leader names come from (DAT table, pool per nation, its size), when they are drawn,
   and whether reopening the form or a second New Game draws again. Confirm with two or three seeds that the names differ and
   stay inside the nation's pool.
Out of scope: the Game menu's New player, New nation and Abdicate (G02-G04), except one line in the finding saying which of
the form's code paths they reuse, if the code shows it; battles (paused).

## Work
- Branch `experiment/leaders-form`; worktree `/home/diego/projects/wt-leaders`; your own Xvfb display (`:743`) and your own
  game folder (`~/ic2-work-leaders`, a copy of `~/ic2-work`).
- Data in `runs/experiments/data/run-exp-leaders-form/`. Binaries go to release `run-exp-leaders-form` as per-batch tar.gz files
  with a tracked manifest. Scripts go in `runs/experiments/leaders_form/`.
- Driver pitfalls: hover before clicking; locate controls with `Game.controls` or OCR, never with fixed coordinates; verify
  every click's effect (memory, a window, or the save) and retry at most twice; track each dialog by its X window id and bound
  the attempts; a box without the control you need stops the run, never a guessed click. Every intermediate click (a tick, a
  name edit) is checked to have registered before the next one. Do not edit `harness/driver.py`.
- **Finding:** `findings/2026-10-06-leaders-form.md`, in the research-report format: Method; the form (controls table); the
  rules (names, ticks, OK/Cancel, ordering) as a table with id, rule, literal if any, function and line, tag, evidence; the
  draw; a table "the clone today → the original" for #719; "What this does not establish".
- **Claims audit** (`claims_audit.py`): reads every literal, rule and count claimed in the finding's tables and compares each
  with the tracked code extract, the recorded plays (clicks, OCR, saves, screenshots) and the saves' bytes. No expected result
  is typed into the checker; no check compares the finding with itself. Every required play (questions 2-4) must exist and be
  cited. Its tests show that a doctored literal, a doctored extract line, a doctored save, a missing screenshot and a claim
  removed consistently from two tables each fail it.

## Done when
- The form's controls and every rule of questions 1-5 are in the finding, each `[derived]` with its code line or
  `[confirmed]` with its screenshot and save; what could not be settled is listed under "What this does not establish".
- Plays cover: 0, 2 and 16 humans ticked; an empty, a duplicate and an over-long name; an edited computer-nation name; Cancel;
  two or three seeds for the draw.
- The claims audit gives 0 mismatches and its tests and the runner tests pass, with their outputs tracked.
- CLAUDE.md rule 6 holds throughout: commit and push after each batch and at least every 30 minutes; never delete or overwrite
  a measured output; saves and screenshots never go in git (their SHA-256 go in `SAVES.sha256`, the files go to the release); if
  a release call is refused, keep the files and report the exact command; never print `IC2_RELEASE_TOKEN`.

## Deliverables
One PR against main, "findings: the original's leaders form", with this task file in it. Its body maps every Done-when line to
its evidence.
- Do not merge, and do not run the reviewer.
- If something blocks you, stop, commit and push what was measured, and report.
