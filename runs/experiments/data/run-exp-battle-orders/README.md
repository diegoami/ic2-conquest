# run-exp-battle-orders: data folder notes (battles plan B7 and B12)

Task: `docs/tasks/battles-b7-b12.md`. Code: `harness/battle_orders.py` (`BattleGame`: the six orders), `tests/test_battle_orders.py` (25 offline tests, all pass),
`runs/experiments/battles/b7_common.py`, `b7_survey.py`, `b12_plans.py`, `b12_run.py`, `b12_pairs.py`. Binaries: release `run-exp-battle-orders` (archive `b7-dev-batch-01.tar.gz`,
manifest `release-manifest-b7-dev-batch-01.json`, SHA-256 in `SAVES.sha256`). Hooked lab exes for seeds 1-30 built in a private copy of the build folder: `EXES-sha256.txt`
(seeds 1-3 equal the B11 v2 hashes).

## Status / resume here (work PAUSED by the coordinator, 2026-10-05; the PR is NOT open)

Done:
- B7 driver orders (`battle_place/move/attack/shoot/end_turn/surrender`) with offline tests (25/25). Verified live: place (9 units), move, End turn (proven), Surrender No and Yes.
  `battle_attack` and `battle_shoot` were exercised live only inside the P-FOCUS dev battle below (42 orders, all verified), not yet in a dedicated "each order once" run.
- B7 button survey, 3 sessions: `b7-survey-buttons-20261005-151145` is the first with the tooltip check passing (all 8 buttons matched; the two earlier `buttons` files
  and the first two `surrender_yes` files are failed attempts, kept: tooltip hover sent to the wrong display, Cancel on "Change delays" needing a retry, the Battle ended box opening ~3 s after
  Yes); `b7-survey-surrender_yes-20261005-151837` (Yes: Rome's army 37,081 -> 0, Gaul captures 156 talents, "Battle ended" box after ~3 s); `b7-survey-computer-20261005-151457`.
  The button table is not yet written up. The final `buttons` run's Surrender No: block byte-identical.
- B12 plans written (`b12_plans.py`), runner and pair analysis written. One dev battle: `mix-rg_p-focus_s1_r1` (batch `dev`, Rome lost, 8 half-rounds, 125 s, hook check passed). Two earlier
  dev attempts errored on over-strict partial-move checks (kept in `trials-b12.jsonl`; the check was relaxed in `battle_orders.py`).

Not done: the 5 played battles in a row, "each order once" live run, the pairing proof on one pair (baseline `cg` run through `b12_run.py` vs a plan run: compare `open` blocks
in `trials-b12.jsonl` and run `b12_pairs.py`), the 3 x (30 + 10 + 10) batches plus 50 baselines, repeatability, finding, claims audit, coverage.md rows, PR.

Resume with (own folder `~/ic2-work-b7` holds the prefix and hooked exes; pick a free private display, e.g. :710):
`export IC2_WORK=~/ic2-work-b7 DISPLAY_IC2=:710 B12_WORKER=-w1; python3 runs/experiments/battles/b12_run.py run cg,p-focus mix-rg --seeds 1 --batch pairing`, then `b12_pairs.py`.
Notes: ~2 min per plan battle on S-PAR; `dev` batch trials are not part of the B12 tables. No Wine/Xvfb process of this task is left running.
