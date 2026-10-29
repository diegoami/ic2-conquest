# An AI fleet at war hunts and sinks a nearby enemy fleet in the original; in the remake it stays in port

**Tag:** [confirmed, partial]. 30 seeds in each game from the same save, under Wine. One start state.
**Task:** conquest [#233](https://github.com/diegoami/ic2-conquest/issues/233) (tracker #228); remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`), `classical-faithful`. Found by the pre-registered scenario
`storm30` (`difftest/cases/stats233.py`), which was meant to measure storm damage.

## Answer

Start: `saves/fleet-port-antium-0734.SAV` (Rome human, Autumn week 5, 270 BC; Rome and Carthage at war).
Order: Rome's fleet 2 (30 ships, condition 97, empty) sails from Antium (101,46) to open calm sea at (97,48).
Then End turn.

| | Original (startup seeds 1–30) | Remake (state seeds 1–30) |
|---|---|---|
| Carthage's fleet (90 ships at (110,63)) | sails 14 tiles to (98,49), next to Rome's fleet, and attacks | does not move (stays at (110,63), condition 100) |
| Rome's fleet survives the turn | **0 of 30** (all 30 ships lost) | **30 of 30** (0 ships lost; condition −3 or −4) |

The permutation test gives p = 0.0001 (Holm-corrected 0.0012) for survival; the samples do not overlap at all.
In the original, Carthage's fleet loses 3 ships and falls to condition 93 in the battle (seed 1).

The original's behaviour is its documented AI fleet hunt
(`findings/2026-10-09-ai-intercept-and-fleet-hunt-in-play.md`: the hunt-or-port decision in `FUN_0044f608`, seen
firing as decompiled). In the remake, the same state, with Carthage at war with Rome, never produces a hunt.

## What this does and does not establish

- **Established:** for this state, the remake's AI does not hunt a reachable enemy fleet at sea, while the
  original's does in every seed. A remake player can therefore leave a fleet at sea next to a hostile navy without
  the loss the original inflicts.
- **Not established:** whether the remake ever hunts (other distances, fleet sizes or nations); which step
  differs (the hunt scorer, its eligibility, or the movement). Earlier #174 work compared fleet decisions only on
  synthetic inputs, at remake pins `55d96876` and `195a588e`
  (`findings/2026-10-24-strategic-fleet-controls174.md`, `findings/2026-10-24-fleet-accepted-movement174.md`).
- The storm damage that `storm30` set out to measure could not be compared, because no original fleet survived.
  `storm30b` repeats it with Rome and Carthage staged at peace.

## Evidence

Data: `runs/experiments/data/run-exp-diff084-stats/`. `trials.jsonl` has one line per trial with its metrics
(the first 30 `naval30` remake lines are a metric bug, kept and re-run), `analysis-*.json` and `.txt` hold the
tests, and per trial `storm30/<side>-s<seed>/receipt.jsonl`. Saves (run `run-exp-diff084-stats`, release of the
same name): `storm30/original-s1/a001.SAV` (turn 0734, after the sail: Rome's fleet at (97,48)), `a002.SAV`
(turn 0735: Carthage's fleet at (98,49), Rome's gone); `storm30/remake-s1/a002.SAV` (Rome's fleet at (97,48),
condition 93; Carthage's at (110,63)). The same names hold for seeds 1–30. Original: `fast rollingsave seed.exe`
(SHA-256 `354d8265…`), Wine 10.0.
