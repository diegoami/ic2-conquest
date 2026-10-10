# env-fingerprint (branch tooling/env-fingerprint)

- [x] harness/environment.py, Game.start() record, baseline, scripts/environment_check.py, docs/environment.md
- [x] tests/test_environment.py (11 checks pass)
- [x] Wine run 1 (smoke.py, pre-review): load 16.4 s, environment line printed. Save: `saves/run0-start-AUTO0720-seed12345.SAV`, turn 0720 (smoke.jsonl, "load" line of 2026-10-10T20:32:05).
- [x] Review rework R1-R7 (commit per fix):
  - R1: Game.record_environment after every start -> `$IC2_WORK/environment.jsonl` (time, pid, argv0, cwd) + sinks. Covered runner logs: battles/common.py Log (b0_probe, b2, b8, b11, b16, trials, fixtures), feature_inventory/explore_lib.py, the 5 MyGame libs (end_of_game, leaders_form, refusal_texts, v050_rules, split_aboard; leaders_form/play_lib uses leaders_form/lib), supply_transfer.py, smoke.py, shot_compare.py (g.environment in its record). NOT covered (only environment.jsonl): pair2/trials.py, fleet-battles/trials.py, unit-map-mouse/common.py, storms/*, gallic-army.py, two-humans/*, info_window/*, finished one-off data/run-exp-* scripts (peace_radio, build_city, numidia, cellauto; history is not rewritten).
  - R2: Game.__init_subclass__ wraps every start override (MyGame x5, PeaceGame, HookGame); nested super().start() records once.
  - R3: 0.8 s per probe, 2 s whole fingerprint. R4: errors sanitised. R5: cache key (prefix, exe path, display). R6: tests.
- [x] Wine run 2 (smoke.py, after rework): `smoke.jsonl` line 45 (`"step": "environment"`, pid 1004825) then load ok in 16.0 s; same record in `~/ic2-work/environment.jsonl`. Save: `saves/run0-start-AUTO0720-seed12345.SAV`, turn 0720.
- [x] PR #69 open (not merged)
