# Original AI probes, October 16

Owner-authorized original-game probes for research issues #22, #23, #24 and
#26; #5 is an existing-evidence audit, #25 is prerequisite-gated. See
`docs/progress/original-ai-oct16.md` for authorization, order and scope.

All text evidence goes here, exclusively named or append-only. Binaries go
to `artifacts/run-exp-ai-oct16/`, with `SAVES.sha256` here and release
`run-exp-ai-oct16` uploads after each measured batch. Never delete or overwrite
a measured save; every script uses unique names. Record staging and instrumentation
separately from unmodified original execution. Keep code-derived, Wine and native
Windows evidence distinct. No native confirmation is claimed by these probes.

## Evidence and reproduction

- `observations-20261016-152721.md` / `.json`: verified 28 supply/fleet cases,
  seven byte-identical plain/observed region pairs and 109 tactical boundaries.
  `summarize.py` names the authoritative logs explicitly and checks their saved
  fields and every artifact hash; exploratory and failed attempts remain kept.
- `city-regions-20261016-145216.csv`: all 334 city IDs/names and both region
  components. The prior CSV came from an interrupted summary write, not a
  second independent measurement. `region-audit-20261016-145216.json` records
  482 original-x86 classifier comparisons.
- `code-truth-tables-20261016-150205.json`: original-x86 predicate combinations
  and signed score rounding; this is emulator evidence, not Wine evidence.
- `targeted-code-extract.txt`, `targeted-source-callers.json`, input manifests
  and environment records: source provenance for the bounded claims.
- `issue5-evidence-audit.json`: existing promoted evidence, no new run.
- `issue25-*.json`: historical/current registry inventory only; replay remains
  gated on the general-control correction. Public registry snapshots are text
  inputs, not original game data or replacement expectations.

Use an installed original-game prefix copied to a **private** `IC2_WORK` and a
private `DISPLAY_IC2`. Do not run against a shared prefix/display. The existing
seeded EXE and lab seed-1 EXE must be present; hashes are recorded. The selected
strategic source is tracked in `saves/`. Battle inputs are the unchanged
`gate2_a_BATTLE01/02/03.SAV` assets of release `run-exp-battle-probe`, downloaded
to `artifacts/run-exp-ai-oct16/original-inputs/`, with hashes in the first input
manifest. Never overwrite an existing input download.

```bash
export IC2_WORK=/path/to/private/ic2-work
export DISPLAY_IC2=:716
python3 runs/experiments/data/run-exp-ai-oct16/preflight.py
python3 runs/experiments/data/run-exp-ai-oct16/supply_probe.py aboard land a_dist4 a_dist5 a_empty a_positive a_zero a_repeat a_hostile
python3 runs/experiments/data/run-exp-ai-oct16/supply_probe.py f99t101 f99t100 f100t101 f101t101 f0t101 f94 f95 f96 f_y3 f_y4 f94t101 f94grant f94s91 f_repeat f_cap f_empty f_hostile
python3 runs/experiments/data/run-exp-ai-oct16/general_probe.py plain_off human_off human_on ai_control reload_on interrupt_on
```

`preflight.py`, `supply_probe.py` and `general_probe.py` record logs directly
here and exclusively name artifacts. General probes build their task-local
observer from the installed lab seed-1 EXE. For region probes first build the
task-local score observer from the seeded EXE (the builder preserves a copy and
hashes, exclusively creates outputs and verifies an existing build), then run:

```bash
python3 runs/experiments/data/run-exp-ai-oct16/score_hook.py "$IC2_WORK/prefix/drive_c/IC2"
python3 runs/experiments/data/run-exp-ai-oct16/test_score_hook.py
python3 runs/experiments/data/run-exp-ai-oct16/region_probe.py same_right same_left boundary same_only cross_only fallback_same fallback_cross
```

For the region audit, pass the seeded EXE path and optionally the **explicit
preflight log path** as a second positional argument. It refuses to guess among
multiple runtime-table records. The committed `summarize.py` revalidates this
recorded batch; a new measurement batch needs its new log filenames selected
explicitly before comparing it. Original draws and fixtures never change.

The task-local battle observer can be tested offline by importing
`general_hook` before `tests.test_battle_hook_caves` in the same Python process,
then calling the latter's `main()`; its added markers and recorded flag word
are included in the unchanged test's CPU/stack/memory equivalence checks.
Python packages Unicorn and Capstone are prerequisites for those offline x86
checks. Wine execution is a separate validation layer.
