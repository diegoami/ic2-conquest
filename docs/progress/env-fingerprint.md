# env-fingerprint (branch tooling/env-fingerprint)

Claims about the game cite a save; the others say plainly they are about code or tests only.

- [x] harness/environment.py, Game record, baseline, scripts/environment_check.py, docs/environment.md (code and docs: not about a game state).
- [x] tests/test_environment.py, 12 checks pass (fake commands/registry: no game, no save).
- [x] Wine run 1 (pre-review): save `saves/run0-start-AUTO0720-seed12345.SAV`, turn 0720; `smoke.jsonl` "load" line of 2026-10-10T20:32:05: load 16.4 s.
- [x] Rework 1 (R1-R7): sinks in runner logs, bounded probes, sanitised errors, cache key. Wine run 2: same save, turn 0720, `smoke.jsonl` line 45 (`step: environment`, pid 1004825), load 16.0 s.
- [x] Rework 2:
  - Budget 0.9 s for the whole fingerprint, enforced by parallel daemon threads with one deadline; worst case (all probes hang) measured 0.90 s in the test.
  - The record now hangs on `Game.pid` assignment (a property): every start ends by setting it, so overrides, `attach()`, nested `super().start()` and a start replaced by assignment (`Game.start = start`, run-exp-cellauto-rule/trace_save_before_n.py) all record. Only a live process whose cmdline starts with "Imperial Conquest" counts, so unit tests with fake pids write nothing (checked: environment.jsonl unchanged by test_driver_battle, test_end_turn_reclick, test_battle_b16, test_battle_trials).
  - Wine run 3: same save, turn 0720, `smoke.jsonl` line 49 (`step: environment`, pid 1105684), load 15.4 s.
  - Launch paths found (all set `pid` after launching, so all covered): Game.start; MyGame x5 libs (attach); PeaceGame (b16_common); HookGame (super); iw_lib.launch (`g.pid = ps[0]`); trace_save_before_n.py (assigns pid). Not game launches: leaders_form/play_lib and unit-map-mouse/common run helper exes (state tool, slider) through Wine; tests/test_battle_hook_build emulates, no Wine. Only `Game.start =` assignment in the repo: trace_save_before_n.py:21.
- [x] PR #69 open (not merged)
- [x] Rework 3 (code and tests only, no game state; no Wine run, the Wine path did not change since run 3):
  - `_logged` is keyed per game process (pid): two restarts in one Python process each log through self.log and the sinks (test, fake live-process check).
  - `environment.folder_sink(folder, key)`: for runners with no log file, each start writes `environment-<stamp>[-n].json` (exclusive create) in the folder. Where each record lands:
    - info_window (iw_lib and its batch scripts): tracked `runs/experiments/data/run-exp-info-window/` (its log is the CAPLOG tsv, so the json sits beside it).
    - pair2/{phase1,phase2,trials}.py: `artifacts/run-exp-pair2/`.
    - fleet-battles/{probe_attack,stage_p2,stage_cells,trials}.py: `artifacts/run-exp-naval-battle/`; t3_trials.py, t3_natural_embark.py: `artifacts/run-exp-naval-battle-cargo/`; peace_prompt.py: `artifacts/run-exp-peace-prompt/`.
    - storms/{t4_natural,t4_probe,t4_trials}.py: `artifacts/run-exp-storms/`.
    - two-humans/{t0,t0_phase2}.py: `artifacts/run-exp-two-humans/`.
    - unit-map-mouse/common.py (all its scripts): `artifacts/run-exp-unitmap-mouse/`.
    - gallic-army.py: tracked `runs/experiments/gallic-army/`.
    - Scripts without Game (stage/analysis only: t4_stage, t3_stage, random_term, t4_analysis, ...) start no game. Finished `runs/experiments/data/run-exp-*/` scripts unchanged (environment.jsonl covers them).
