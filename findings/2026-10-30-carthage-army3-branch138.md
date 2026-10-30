# Carthage army 3, turn 1: the original takes the mercenary run, and remake main still scores army 10 without the region halving

**Tag:** [confirmed]. Research #138 (remake #1628). The original's side comes from its own hooks on BASE.SAV (seed 12345,
plain End turns). The remake's side comes from its own decision log on the same save and seed, at three commits.
Follows `2026-10-30-campaign-differences-v085.md` and research's correction (Research PR #136).
**Remake compared:** branch `main` at `d8e7a646` (T247, #1634, 2026-10-30; not yet released), with v0.8.5 (`1622407e`)
and the intermediate `dab3a2ea` (T246) for the bisection. Turn 1's End-turn state is checkpoint t01-a01 in the campaigns.

## 1. What the original does (F31C, army phase, Carthage = nation 1, army 3 at (93,79), 8 moves)

| Step (F31C order) | Original value | Taken? |
|---|---|---|
| City scorer ECE4 → osca (49,41) | 91 at distance 44 (the remake's value, same rule, see §3) | — |
| Army scorer EE60 → army 10 (34,63) | candidate 34 at distance 59, **returned 93** (tie hook) | — |
| army > 100 (0x44F409) | 93 | no |
| city > 100 (0x44F43F) | 91 | no |
| **resupply** (0x44F47C): `FUN_0044a698(army)/500 >= supplies`, or no city target | 24600 / 500 = 49 against 246 supplies (values after the supply pass; see the correction below); osca exists | **no** |
| `FUN_0044e84c` (0x44F485): nearest table entry within 20, walk via DBA8 (call 0x44E913) | **(111,69)**, 18 away; walks to (88,77), 0 moves left | **yes** |
| army > 70 (0x44F4A3) → toward army 10 | 93 > 70: called toward (34,63) with 0 moves | yes (no movement) |

So the answer is:
- **Branch:** the `FUN_0044e84c` walk (the remake calls it the mercenary run), then the "army > 70" step.
- **Destination:** (111,69) for the walk, then army 10 at (34,63).
- **Final position:** (88,77).
- **Deciding predicates:** the army score 93 is not over 100, and the resupply test is false because the city target exists
  and 49 < 246.
- The resupply branch first appears at turn 2 (call site f47c, home city (93,78)).

Sources:
- `run-exp-walk-hook97/BASE-walk.jsonl`: nation 1, army 3, seq 2 (e913) and seq 3 (f4a3), turn 1; seq 27 (f47c), turn 2.
- `run-exp-tiehook117-long/rome-BASE-ties.jsonl`: seq 5–6.
- Army 3's troops and supplies are from BASE.SAV.

## 2. Why v0.8.5 took the resupply branch: no target at all

The remake's decision log for army 3 at v0.8.5 (`1622407e`):
- `MoveToResupplyCity`;
- no city and no army target;
- `Skipped: 20`.

Every candidate was refused. v0.8.5 still required `IsReachable` for a target in a different geography, on top of CAB4's
"same geography, or any own fleet" rule. Army 3 is in Africa, and the candidates are across the sea. With no city target,
F31C's "no city target" clause sends the army to resupply, so the resupply selector was never the cause.

T247 (`d8e7a646`, `AiArmyTargetTree.ScoreCityTarget` / `ScoreArmyTarget`) dropped that extra gate. T246 alone (`dab3a2ea`)
still takes the resupply branch.

## 3. Remake main: the same cell, a different branch, from one missing rule

Main's log: `AttackArmy` (army > 100) toward army 10, army score **126**, with a stored route (34,63). It walks
(93,79) → (88,77). Turn 1 ends on the original's cell, but by the "> 100" branch rather than the mercenary run and the
"> 70" step.

**The rule: EE60 halves a candidate when the target's geography differs from the actor's.**

The original's code:
- `0x44EF44: call FUN_0044eb9c(target pos, actor pos)`, then `score -= score/2` (a signed shift, truncating toward zero).
- `FUN_0044eb9c` returns 1 when `FUN_0044eb18` classifies the two points differently.
- `FUN_0044eb18` is the CA30 classifier: last strict-interior box of 8, plus the coordinate-split bit from 6 splits. The
  remake has it as `ClassicalArmyNavigation.Classify`.
- All three callers use the same test: the city scorer (0x44EDC8), the army scorer (0x44EF44) and the capital defence
  (0x44F040).

Remake main:
- The city scorer and `AiCapitalDefence` use `Classify` under faithful navigation.
- **The army scorer still uses `RegionOf`, the nearest-city region (`AiArmyTargetTree.cs` line 293).**

For army 3:
- (93,79) is on side 1 and (34,63) on side 0 (split (44,78)); neither point is inside a box.
- The original: 67 − 67/2 = **34**, returned 34 + 59 = **93**.
- The remake's nearest-city regions are equal, so there is no halving: 67 + 59 = **126**.

Army 2 at (47,62) is in the same geography as army 10. It is not halved in either game: 113 + 13 = 126 in both.

**Check:** a scratch copy of main with only that line changed (`ee60-classify.patch.txt`: `Classify` under faithful
navigation, `RegionOf` otherwise) gives:
- `MercenaryRun`, army score **93**, city osca 91;
- aim **(111,69)**;
- walk (93,79) → (88,77).

That is the original's branch, destination and position.

*Correction (2026-10-30, from the decision hook of `2026-10-30-ai-decisions-vs-remake-main.md`):* the first version read
army 3's troops and supplies from BASE.SAV (18,600 and 90). F31C calls the supply pass `FUN_0044e41c` for each army just
before deciding it. At the decision the army holds 246 supplies and `FUN_0044a698` returns 24,600 (hook record, BASE turn 1).
The branch is unchanged: 49 < 246.

## What this does not establish

- **Later turns:** the stored route (34,63) that main's `AttackArmy` leaves, and anything after turn 1. A main recheck of
  the #232 campaigns has not been run; the v0.8.5 recheck stands.
- **The other 12 campaigns,** which start from other seats' saves. The probe is BASE.SAV only. They share the turn-1 round,
  but this was not checked campaign by campaign.
- **`FUN_0044e84c`'s table** (0x49DA18, 12-byte entries, slots 0xC9–0xFA): the remake calls it the mercenary run and
  chose the same point here. Its full contract was not compared.
- **The original's city score 91** was not hooked. It is the remake's value under the same `Classify` rule, and it does not
  matter here, since every branch threshold it meets (> 100, existence) gives the same answer for any value from 0 to 100.
- **`FUN_0044a698` = troops:** taken from the remake's documented gate (`troops / 500 < supplies`). With 49 against 246,
  the margin is wide.
- **The remake's own `IsReachable` gate** outside faithful navigation (the improved preset) is not affected or judged.

## Evidence

- Original:
  - `runs/experiments/data/run-exp-walk-hook97/BASE-walk.jsonl`
  - `runs/experiments/data/run-exp-tiehook117-long/rome-BASE-ties.jsonl`
- Remake: `runs/experiments/data/run-exp-army3-138/` (README.txt):
  - `decisions-<commit>-t1.jsonl` (the remake's `DecisionRecord`s)
  - `probe-*` / `aiprobe-*` (marches)
  - `ee60-classify.patch.txt`
- Probe: `difftest/remake_adapter/AiProbe.cs`, new `decisions=<file>` option. Pins are built with
  `python3 -m difftest.pin build main` and `build dab3a2ea`.
- Save: the BASE fixture (`/home/diego/ic2-work/fixtures/BASE.SAV`), turn 1, seed 12345.
