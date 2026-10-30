# What still differs in the #232 campaigns at remake v0.8.5: weather, the unported fleet phase, one army decision

**Tag:** [confirmed, partial]. The original's End-turn saves were compared field by field with the v0.8.5 recheck's remake
saves. Turn 1 of all 16 bot campaigns and turns 15–17 of the all-human campaign were grouped, and one remake decision was read
from the remake's own AI probe. Follows `2026-10-30-recheck-v085.md`.
**Scope (owner, 2026-10-30):** attribute the remaining differences; stop at anything not yet implemented in the remake.

## All-human campaign: the jump at turn 16 is weather

Each "turn" here is one seat's End turn, so the date only moves when all 16 seats have played. Turns 1–15 are identical. At
turn 16 the first weekly weather redraw happens (spring week 1 → week 3):
- the original draws **0** rough-sea cells, the remake **520** (map code 1);
- the only other difference is fleet 1's condition, 70 vs 72, which is storm damage from that weather.

At the next redraw (turn 32) they draw 185 and 176, on different cells. Weather is a random draw and the two games use
different generators. #233's `weather60h` scenario is consistent in distribution, so **there is no rule difference in 32
turns of the all-human game.**

## Bot campaigns, turn 1 (one full round of 15 AI seats)

| Difference | Campaigns | Original → remake | Attribution |
|---|---|---|---|
| Carthage fleet 0 | 13 of 16 | sails (49,62) → (74,71) / stays at (49,62) | **Not ported:** the original fleet phase F608/E1FC (port pick, D174 waypoint; `2026-10-30-fleet-move-contract131.md`). Remake #1405/#1409. |
| Nation 3's fleet 1 | 13 of 16 | the swing next to a land target, 28 → 5 moves (189,93) / untouched, 28 moves (190,93) | **Not ported:** the same contract (no-progress swing, `2026-10-30-ai-fleet-moves-in-play1409.md`) |
| Carthage army 3, from (93,79) | 13 of 16 (all but the Carthage, Celtiberia and Gaul campaigns) | (88,77), toward the west / (94,78), 1 cell, 8 moves unused | Target choice: the remake's resupply branch (#1402); below |
| City supplies ±1–2, AI recruitment, mobilisation and treasury, relations, map cells | all | small and varying | **Random draws.** The original's own values vary from campaign to campaign: city 1 holds 74–79 after the same round. These were not attributed further. |
| Later turns and the Gaul campaign's army table | — | — | Follow-on divergence (different positions, deaths, and table order after deaths, #117) |

**Carthage army 3.** One decision, two known open items:
- **Original** (tie hook, `run-exp-tiehook117-long` `rome-BASE-ties.jsonl`, turn 1): the army's only enemy-army candidate is
  army 10, 59 away, score 34 + 59 = 93. That is not over 100, so no attack. The army goes west to (88,77): F31C's "score > 70
  → toward the army target" branch, or a city target. The capital defence `FUN_0044efc8` gives Carthage no dispatch in that
  turn (capdef hook data).
- **Remake** (its AI probe, `aiprobe-rome-t1.jsonl`): army-3 "move to the resupply city", aim (95,77), 2 away. It walks 1 cell
  to (94,78) and stops with 8 moves unused.
- So the difference is the **target choice**: the remake takes the resupply branch where the original does not. Resupply
  selection is tracked separately (remake #1402, `2026-10-16-strategic-ai-regions-resupply.md`).

  *Correction (2026-10-30, research intake, Research PR #136):* the first version also blamed the missing march continuation,
  because the remake's walk stops 1 cell short with 8 moves left. That is wrong. The original's `FUN_0044dba8` continues only
  while the distance is > 1, so at distance 1 it stops too. The continuation plays no part in this move.

## Not done (owner: stop at unimplemented work)

- Every field of later turns.
- The branch the original takes for army 3 (the army target or a city), and its resupply test values.
- Whether the city-supply ±1 differences are entirely random. A statistic over seeds would settle it.

## Evidence

- Script: `runs/experiments/campaign085/attribute.py` (`groups`, `all`).
- Data: `runs/experiments/data/run-exp-campaign085/groups-v1.json` (the grouped fields) and `aiprobe-rome-t1.jsonl` (the
  remake's v0.8.5 AI probe from BASE.SAV, one turn, seed 12345).
- Saves:
  - original: `artifacts/run-exp-diff084-*/<campaign>/original/` (End turns paired from `receipt.jsonl`);
  - remake: release `run-exp-recheck-1622407e` (`campaigns-v2/<campaign>/tNN/`).
- Original decisions: `runs/experiments/data/run-exp-tiehook117-long/rome-BASE-ties.jsonl` and
  `run-exp-capdef123/rome-BASE-capdef.jsonl`.
