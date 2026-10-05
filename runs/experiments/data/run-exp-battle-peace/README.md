# run-exp-battle-peace (B16, the Offer of peace): data folder

Task: `docs/tasks/battles-b16-peace.md`. **Work stopped early on 2026-10-04 (coordinator's wind-down); the PR is NOT open.**

## Status / resume here (updated 2026-10-05, paused by the coordinator; the PR is NOT open)

**All measurements are done, committed, pushed and uploaded** (release `run-exp-battle-peace`: archives `b16-batch1/2/3`, 611 binaries, members in `MANIFEST-b16-batch*.txt` and `release-manifest-*.json`; `SAVES.v3.sha256` lists every binary once as `<sha256>  <bare name>`; the old `SAVES.sha256` mixes two name forms and is not edited). No process of mine is running (Xvfb :640/:641/:642 and their Wine killed).

Done:
- Driver `Game.answer_battle_peace(yes)` + offline tests (tests/test_driver_battle.py 32, tests/test_battle_b16.py 6); runner `b16_run.py`, `b16_analyze.py` (`table`, `hook`, `pairs`, `repeat`, `snapdiff`), `b16_release.py`, `b16_hashes.py`, `b16_audit.py` (written, see below).
- Survey, normal build: D-LOSS seeds 1-30, box open in 10 (1,3,5,6,7,8,12,18,28,30); D-WIN seeds 1-10, 0 open (tests fail); D-WIN with a second Gaul army (`win+own12=6,strong12=6,unity6=600,weak2=500,weak13=500`) seeds 1-5, open in 3 and 5.
- 12 Yes/No pairs (10 D-LOSS, 2 D-WIN-ext), pre-answer state identical (outside two volatile words at 0x45E614/6), 4 proven turns each; No v No byte-identical on seeds 1 and 3 (post save + 4 turns).
- Gate cells (seeds 1,3,5): unity 501 open / 500 closed / 499 closed; city word 8 open / 7 closed; weak Rome armies closed. Hooked lab runs: 16 baseline seeds (box open exactly when the Random(5) at 0x45951C is < 2: draws 0,1,0 open; 13 closed), 9 hooked gate runs: no draw at all when a test fails.
- Finding DRAFT `findings/2026-10-05-battle-peace-offer.md` written (tables included).

Next (resume):
1. `b16_audit.py` was written but never completed a run: the first full run was too slow (it decompresses snapshots inside a loop; the edit that precomputes the diff, `differs_only_in_volatile`, was lost when a `pkill -f` killed the editing shell). Re-apply that fix (the No/No loop and the pair-identity loop), write `runs/experiments/battles/b16_expect.json` with the finding's numbers (keys used: survey_loss, survey_win, rcode_loss, rcode_win, errors, pairs, identity, rel_after, turn1..turn4, nonoise, gate, gatevals, tests_driver, tests_b16, tests_stage), run it until 0 mismatches. Check by hand the finding's wording about the second-army edit and "Dacia's army 12".
2. Update `coverage.md` rows ("Accept a post-battle peace", "Post-battle peace offer": cite `loss_s1_yes_r1_post.SAV`, `loss_s1_no_r2_post.SAV`, `loss_s1_survey_r1_dialog-Offer_of_peace-*.png`), `tests/results.md` line, and `docs/proposals/battles.md` bot status if the pattern asks.
3. Open the PR "battles: B16 the Offer of peace" mapping each Done-when line to its evidence; no reviewer.
Env for any further run: `IC2_WORK=~/ic2-work-b16 DISPLAY_IC2=:640` (second `~/ic2-work-b16-w2` :641, hooked `~/ic2-work-b16-w3` :642), start your own Xvfb; the 'Imperial Conquest' wine processes of other sessions (e.g. display :710) are not yours.

Half-finished state: none open. The audit script and the finding draft are uncommitted-before-this-commit work in progress.
