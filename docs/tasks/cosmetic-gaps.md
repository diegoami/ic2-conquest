# Task: the original's cosmetic gaps the clone lists in its #723 (given 2026-10-06)

For imperial_conquest_2 #723 (post-0.5.0, the cosmetic batch). The clone's issue lists five rows of the feature inventory, all
`[derived]` and provisional: the window title (M04), the ten sound effects (M06), window positions kept in the save (M05), the
area-map colour toggle (A01) and the Supply army **Buy supplies** caption (UA01). Before the clone copies any of them, each
rule needs to be exact: the literal byte for byte, the trigger, and what changes in the game.

## Scope
This task protects: **the exactness of every rule the clone will copy** (the title's format and when it changes, which event
plays which of the ten sounds, what the toggle switches between and what two clicks do, the button's exact caption and when it
is enabled, what the save's window-geometry bytes hold).
- Each rule is read from the code with its line cited (`[derived]`), or seen in play with its screenshot and save
  (`[confirmed]`). The two are never mixed. Captions, title literals and box texts are the original's own bytes, read from the
  decompile's string literal or the form's resource, never retyped from memory.

Forbidden results: a rule with neither a code line nor a play behind it; a play claim without its screenshot and save; a
staged save not labelled as staged; a measured output overwritten or deleted; a binary in git; a write to another repository;
processes killed by pattern; a click at a guessed or fixed position.

## Read first
- `CLAUDE.md` (rules 1-7, and rule 6's cadence: commit and push after each batch).
- The clone issue: `gh issue view 723 --repo diegoami/imperial_conquest_2` (read only).
- `findings/2026-10-05-player-facing-feature-inventory.md` rows M04, M05, M06, A01, UA01, and the research report
  `docs/reports/2026-10-05-player-facing-feature-inventory.md` in `/home/diego/projects/imperial-conquest-2-research`
  (read only) — the same rows with their evidence columns.
- The decompile (read only): `/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt` and `delphi_symbols.tsv`.
  The handlers: `TPremierForm_SetTurnTitle` (the title literals and their spacing), `TPremierForm_MakeSound` 0x0045bf28
  (cases 1-10 and their callers: which game event asks for which case), `TPremierForm_StoreFormPositions` 0x0045bb1c and
  its load-side counterpart, the `TAFSupply` form resource (the button's caption) with `TAFSupply_TransferSupply`
  0x0043ff98, and the `TAreaMap` form's `sb_areatog` with its click handler.
- Layout and method to copy: `runs/experiments/refusal_texts/` (verified runner, recorded clicks, `test_runner.py` guard
  against guessed clicks, `verified_reset`) and `findings/2026-10-05-end-of-game-screens.md` (a small finding's shape).
- The original's WAVS folder beside the game exe (`$IC2_WORK/prefix/drive_c/IC2/WAVS`): SOUND1.WAV … SOUND10.WAV.

## Questions
1. **Title bar (M04).** `SetTurnTitle`'s exact format — the literals, their spacing and case ("Imperial Conquest 2    ",
   "'s turn", the leader in parentheses), what happens with an empty or missing leader name, and when the title is set
   (game start, every turn change, after the leaders form, after a load). `[confirmed]` by reading the window title at those
   moments in play (the X window name is read, not OCR).
2. **Sounds (M06).** `MakeSound`'s cases 1-10: which caller asks for each case (which game event), which WAV file each plays,
   and whether anything plays when no sound device is present. As many of the ten event mappings as plays can provoke
   (`[confirmed]`, with the save and screenshot of the moment); the rest stay `[derived]` with their call sites.
3. **Toggle colour (A01).** What `sb_areatog` switches between (the two palettes, mono and terrain), what the button looks
   like in each state, and what two clicks do to the drawn markers (`[confirmed]`: area-map screenshots before, after one
   click, after two).
4. **Buy supplies caption (UA01).** The `TAFSupply` resource's exact caption bytes for the paid-path button, and when the
   button is enabled and disabled (own city versus foreign city, money, stock). `[confirmed]` by opening the dialog in play
   (own city and foreign city) with its screenshot and save.
5. **Window positions (M05).** What `StoreFormPositions` writes (which windows, which order, the 8 bytes' layout) and what a
   load restores. `[derived]` from the code plus one `[confirmed]` save pair (move a window, save, load) is enough: the clone
   is one window and expects to decide "nothing to do".

## Done when
1. Every question above is answered in `findings/2026-10-06-cosmetic-gaps.md`, each rule with its tag and citation, the
   literals byte for byte, and a "What this does not establish" line for what stayed `[derived]`.
2. Every play the finding cites is recorded by the verified runner (clicks located and verified, `verified_reset`), its saves
   and screenshots hashed in `SAVES.sha256` and uploaded to the release `run-exp-cosmetic-gaps`, none in git; the batches are
   archived with `scripts/archive_measurements.py run-exp-cosmetic-gaps --commit` and pushed after each batch (rule 6).
3. A claims audit in the style of `runs/experiments/refusal_texts/claims_audit.py`, scaled to this finding's claims (every
   literal, number and play attribution bound to its source), gives 0 mismatches; its output and the tests' outputs are
   tracked and versioned beside the earlier experiments'.
4. The task file's own Done-when lines can be run as written by a reviewer.
