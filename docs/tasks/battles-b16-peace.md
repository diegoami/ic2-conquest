# Task: battles B16, the post-battle "Offer of peace" (`TBattlePols`) (given 2026-10-04)

## Scope
This task protects: **the integrity of the Yes-versus-No comparison and of the peace dataset.** A Yes/No pair must differ only in the
answer: the same save, the same seed, the same battle up to the dialog, proven byte for byte. Every number in the finding must trace to
a tracked output and a released save (CLAUDE.md rules 5 and 6).

Forbidden results (any one fails the task, and a reviewer will block on it):
- a Yes/No pair whose state before the answer differs. That covers the battle's `BATTLEnn.SAV` series, the post-battle state read
  before the click, and the dialog text. Prove it is identical; never assume it;
- the dialog answered with the other button than the run's plan says (verify which button was clicked and that the box closed);
- a Yes or No inferred from the outcome alone. The answer is recorded from the click and the box closing;
- an effect (relations, war state, reparations, news) claimed without a before/after read from a save or a captured screen;
- the condition the decompiled report gives (`[R-code]`: a human-AI battle, the winner weaker, the loser's unity above 500,
  more than 7 cities, then `Random(5) < 2`) stated as measured where the data only fails to contradict it;
- a measured output overwritten or deleted, a binary in git or a new file in `saves/`, a blind second End turn, a run on a player
  run's saves.

## Read first
- `CLAUDE.md` (rules 1-6);
- `docs/proposals/battles.md` §3.5, §4 B16 and §7 (lab versus normal build);
- `findings/2026-10-04-tactical-battle-sweep.md` (the Offer of peace in 76 of 315 rows, all after a Gaul win);
- `findings/2026-10-04-battle-exchange-hook.md`, if merged (the peace draw `Random(5)` at `0x45951C`, and the reseed at
  `0x457907` that fires only when the box opens);
- `harness/driver.py` (`play_battle(on_dialog=...)`, `answer`, `Game.load`, `end_turn_proven`);
- `runs/experiments/battles/` (trials.py, stage.py, common.py);
- `state/sav.py` (relations, money, unity, cities);
- `coverage.md` rows "Accept a post-battle peace" and "Post-battle peace offer".

## Work
Branch `experiment/battle-peace-b16` from main. Data in `runs/experiments/data/run-exp-battle-peace/`, binaries in release
`run-exp-battle-peace` as per-batch `tar.gz` archives with a tracked manifest. GitHub caps a release at 1000 assets; see
`run-exp-battle-sweep/README.md`.

1. **Driver.**
   - Add `Game.answer_battle_peace(yes: bool)`. It finds the "Offer of peace" box, reads its text and controls, clicks Yes or No,
     and verifies the box closed. It returns the text and the button clicked, and raises if the box is absent or does not close.
   - Add an offline test with a fake window. Clicking the wrong button, or the box staying open, must fail the test.
   - `play_battle(on_dialog="yes")` routes through it.
2. **Which build.** §7 says B16 runs on the normal build (`... fast rollingsave seed.exe`: seed at program start; a repeatable turn
   is `Game.load(save, seed)`).
   - First prove that the pair is repeatable. Load the same save with the same seed twice, play the same battle, and compare the
     `BATTLEnn.SAV` series (if the normal build writes none, compare the post-battle state read before the dialog is answered) and
     the dialog text.
   - If the normal build is not repeatable this way, use the lab build for the pairs, say so, and run one pair on the normal build
     as a cross-check.
3. **D-LOSS and D-WIN, 10 seeds each.**
   - D-LOSS: a battle the human nation (Rome) loses. Use FLD-RG with a weak Rome army, or a cell that B5 shows Gaul wins.
   - D-WIN: a battle Rome wins.
   - Use Computer general on both sides as in B5, unless the dialog needs a human-clicked battle; if it does, say so.
   - For each run record: whether the box opens; its title, text, buttons and controls (screenshot plus text read from the
     controls); and the strategic state the `[R-code]` condition names (unity, city counts, army strength), read from the save.
4. **Yes versus No**, on every seed where the box opens, up to 10 pairs.
   - Run the same save and seed twice: answer Yes in one and No in the other.
   - Prove the state before the answer is identical (step 2).
   - After the answer, save, then play N = 4 strategic turns with no orders (End turn only, proven each time).
   - Per turn, read: relations between the two nations (the plan expects −18), war or peace, money of both, reparations, the news
     (screen capture plus text), and anything else that differs between the Yes and No saves (a full `state/sav.py` diff).
5. **The gate.** Compare the observed open/closed pattern with the `[R-code]` condition.
   - If any seed contradicts it, report that.
   - If the rate is neither 0 nor 1, vary unity and the city count around the thresholds (500, 7) with L1 strategic edits, a few
     seeds each, and report the pattern.
   - If the B11 hook is merged, a hooked lab run of one D-LOSS seed may log the peace draw itself. That step is optional.
6. **Findings draft** `findings/2026-10-04-battle-peace-offer.md`, in the research-report format.
   - Sections: Method, Observations, Inferences, the per-seed table, the Yes/No diff table, and "What this does not establish"
     (Wine-only; Computer general; which build).
   - Mark every claim `[O]`, `[D]` or `[R-code]`, and cite saves by bare filename.
   - Update the two `coverage.md` rows with saves.
   - Add a claims audit that recomputes the finding's numbers from the raw saves and records, not from an analyser's output, with 0
     mismatches.

## Done when
- `answer_battle_peace(yes)` exists, with the offline test (a wrong button or a box that stays open fails), and the test suites pass.
- The repeatability check passes for every Yes/No pair used: its tracked output shows the pre-answer state identical.
- 10 D-LOSS and 10 D-WIN runs are recorded, each with box open or closed, its text and buttons, and the strategic state, in a tracked
  table with the saves released and hashed.
- Every pair whose box opened has a Yes/No diff over 4 turns, in a tracked output, with the saves released and hashed.
- The finding states the gate result against `[R-code]`, and what is not established.
- The claims audit gives 0 mismatches.
- Both `coverage.md` rows are updated, and each cites a save.
- CLAUDE.md rule 6 holds throughout: text outputs tracked, committed and pushed per batch and at least every 30 minutes, never
  overwritten or deleted (`common.write_new` / `common.keep`); binaries never in git, with their SHA-256 in `SAVES.sha256` and the
  files in the release.

## Rules (CLAUDE.md rule 6, in full)
Measurements are kept, committed and pushed as they are made, and never deleted.
- Every text output a finding or a PR may cite goes under the tracked `runs/experiments/data/run-exp-battle-peace/`. After each
  batch run `python3 scripts/archive_measurements.py run-exp-battle-peace --commit`.
- Commit and push after each batch, and at least every 30 minutes.
- A re-run writes new files beside the old ones. A runner that resumes appends or versions.
- Saves, screenshots and exes are never in git: their SHA-256 go in `SAVES.sha256`, and the files go to the release.
- If a release call is refused, keep the artifacts and report the exact command; do not retry another way. Never print
  `IC2_RELEASE_TOKEN`.

Driver pitfalls:
- Hover before clicking, prefer toolbar buttons, and verify every order's effect. Retry at most twice, and never retry End turn
  (use the proven End turn).
- Use your own Xvfb display and game folder, and kill only your own pids.

## Deliverables
One PR against main, "battles: B16 the Offer of peace". Its body maps every Done-when line to its evidence.
- Do not merge, and do not run the reviewer.
- If something blocks (the box never opens, the pairs are not repeatable on either build, or a decision only the player can make),
  stop, commit what was measured, and report.
