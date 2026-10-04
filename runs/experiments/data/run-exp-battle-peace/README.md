# run-exp-battle-peace (B16, the Offer of peace): data folder

Task: `docs/tasks/battles-b16-peace.md`. **Work stopped early on 2026-10-04 (coordinator's wind-down); the PR is NOT open.**

## Status / resume here
Done and committed:
- `Game.answer_battle_peace(yes)` in `harness/driver.py`, `play_battle` routes the box through it (`pre_answer` hook), 10 new offline tests in `tests/test_driver_battle.py` (32 pass); `tests/test_battle_b16.py` (5 pass); `stage.py` op `ncities`.
- Runner `runs/experiments/battles/b16_run.py` (normal build, private display/game folder via `b16_common.py`), analysis `b16_analyze.py` (`table`, `pairs`, `repeat`, `snapdiff`), `b16_release.py`.
- Repeatability on the NORMAL build holds for seed 1 (loss cell): four No runs equal byte for byte in the pre-answer memory snapshot, the post-answer Save As, and (two of them) all 4 End-turn autosaves (`b16-repeat-20261004-214240.json`). So no lab build is needed.
- Yes/No pair, loss seed 1 (`loss_s1_yes_r1` v `loss_s1_no_r2`): pre-answer state identical (`b16-pairs-20261004-214002.json`). Right after the answer Rome-Gaul relation is -18 (Yes) v 3 (No); after the first End turn -14 v 3; Rome keeps 30 cities with Yes, 27 after 4 turns with No (one pair, RNG diverges after the answer).
- Survey so far (trials-b16.jsonl): D-LOSS seeds 1-4 (box opened in 1, 3; closed in 2, 4; preconditions of [R-code] pass in all), D-WIN seeds 1-7 (no box; preconditions fail: Gaul unity 377 and armies(L)=0). Survey of D-WIN 8-10 and D-LOSS 5-10 NOT run.
- Binaries: release `run-exp-battle-peace`, archive `b16-batch1-*.tar.gz` (77 members, listed in `MANIFEST-b16-batch1-*.txt` and `release-manifest-*.json`).

Next (resume): export `IC2_WORK=~/ic2-work-b16 DISPLAY_IC2=:640` (second worker `~/ic2-work-b16-w2`, `:641`), start Xvfb there, then
`b16_run.py survey loss 5-10`, `survey win 8-10`; `b16_run.py pair loss <seed> --turns 4` for each opened seed (up to 10 pairs; D-LOSS opens ~40 %, so more seeds than 10 are needed for 10 pairs); gate variants with cells like `loss+unity0=526` (Rome unity after -25 = 501), `loss+unity0=525`, `loss+ncities0=8` / `=7`, `loss+weak2=500,weak13=500` on opened seeds; `b16_analyze.py table|pairs|repeat`; `b16_release.py <label>`; the finding `findings/2026-10-04-battle-peace-offer.md`, `coverage.md` rows and the claims audit are NOT written.

Half-finished state: none open. Two survey trials were killed mid-run by the stop (no record written for them). `SAVES.sha256` mixes bare names (runner) and `shots/...`-prefixed names (one run of `scripts/archive_measurements.py`, which rewrote the file once); nothing else was deleted.
