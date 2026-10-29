# run-exp-diff084-stats: random outcomes over many seeds in both games (#233)

Task #233 (tracker #228), approved by the owner on 2026-10-28. Scenarios, metrics, sample sizes and the test were
fixed in `difftest/cases/stats233.py` before any trial ran; `storm30b` was added, also before it ran, after
`storm30` showed it could not measure storms. Runner: `python3 -m difftest.stats`.

- Original: `fast rollingsave seed.exe`, startup RandSeed = the seed, a fresh process per trial; Wine 10.0.
- Remake v0.8.4 (`d9cc71bc`): the imported state's RandomSeed replaced by the seed (adapter option `seed=N`).
  A seed override changes the draws, and the same seed repeats exactly (checked 2026-10-28).
- Test: two-sided permutation test on the difference of means, 10,000 permutations, Holm over all metrics, alpha
  0.05.

## Results (newest analysis-*.txt, 2026-10-29)

| Scenario | Start | Result |
|---|---|---|
| `naval30` | `saves/fleets-adjacent-at-sea-0723.SAV`: Ptolemaic fleet 1 (70 ships) attacks Carthage's fleet 0 (90) | **consistent**: the attacker sinks in 30/30 in both games; the defender loses 12.6 vs 13.0 ships on average, ending at condition 63.8 vs 63.5 |
| `siege10` | `fixtures/siege-felsina-start.SAV` (built once, see below): army 0 besieges Felsina | **consistent**: no capture; army losses 1,869 vs 1,880 on average; loyalty −3, fortification −3 and population −1 in every trial of both games |
| `storm30` | `saves/fleet-port-antium-0734.SAV`: Rome's fleet sails to open sea, End turn | **differs**, but through the AI, not storms: Carthage's fleet sinks Rome's in 30/30 original trials and never moves in the remake. `findings/2026-10-29-ai-fleet-hunt-absent-in-remake233.md` |
| `storm30b` | the same with Rome–Carthage staged at peace (`fixtures/fleet-port-antium-peace-carthage.SAV`) | **consistent** on every pre-registered metric (Holm over 17 tests): condition lost 3.35 vs 3.60. Observed after the run: Carthage declared war on Rome in 4/30 original and 5/30 remake trials, and only in the original did the fleet hunt follow (4/4 vs 0/5): fleet-hunt finding |

## Fixtures (built once, kept)

- `fixtures/siege-felsina-start.SAV` and `.json`: by `python3 -m difftest.fixtures siege-felsina`. BASE.SAV,
  seed 12345: army 0 to (99,34), End turn, then next to Felsina. Saved before the siege, turn 0721.
- `fixtures/fleet-port-antium-peace-carthage.SAV`: by `stage_storm_peace()`. The storm fixture with relation 0
  between Rome and Carthage both ways (two words changed).

## Files

`trials.jsonl`: every trial, including the first 30 `naval30` remake trials, which hit a metric bug (an index into
the fleet list, which the remake shortens when a fleet sinks); they are kept, and the scenario was re-run with
fleets matched by owner. Per trial: `<scenario>/<side>-s<seed>/` with `receipt.jsonl` and `aNNN.SAV` (hashes in
`SAVES.sha256`; binaries in release `run-exp-diff084-stats`). `analysis-<stamp>.json` and `.txt` hold the tests.
