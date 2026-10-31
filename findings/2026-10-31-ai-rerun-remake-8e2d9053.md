# The AI comparisons rerun on remake main 8e2d9053: the T250–T252 corrections close every attributed gap

**Tag:** [confirmed]. The same equal-state replays as the four earlier comparisons, on the new remake commit.
**Task:** owner request 2026-10-31, after remake #1650 merged the corrections. Remake main `8e2d9053` ("T250–T252: correct
Faithful AI destinations, trade swaps and recruitment city"), not released.
**Method:** unchanged from `2026-10-30-ai-decisions-vs-remake-main.md`, `2026-10-30-ai-diplomacy-vs-remake-main.md`,
`2026-10-31-ai-economy-vs-remake-main.md` and `2026-10-31-ai-fleets-vs-remake-main.md`. These are the original's same hook
logs: 16 New Game starts × 5 rounds, seed 12345, with each round replayed in the remake from the original's own autosave.

## Result

| Comparison | 05b02936 | **8e2d9053** |
|---|---|---|
| Army decisions (749), by cause | 422 same, 250 #925 resupply, 8 #925 fallback, 14 "city > 85" target, 41 diplomacy, 14 state | **691 same**, 41 diplomacy, **17 state** (16, plus the Galatia row attributed below; `attribute.py` labels it `h925-fallback`) |
| Diplomacy seats (1,280) | 1,088 same; first divergences: 10 deterministic, 21 draw, 19 battle | **1,110 same**; first divergences: **0 deterministic**, 22 draw, 21 battle |
| Economy seats (1,200) | 1,055 same, 4 order city differs, 141 state | **1,063 same, 0 differ**, 137 state |
| Fleet decisions (150) | 124 same, 26 differ (Carthage fleet 0) | 123 same, 27 differ (**still only Carthage fleet 0**) |

"Diplomacy", "state", "draw" and "battle" rows are not port gaps. In them the round already differs through random
battle draws or through wars that changed during the round, before the compared decision. The earlier findings define
these categories.

- **#925 (T250):** in classical-faithful the AI now marches at the original's destination. All 250 resupply rows match,
  and 7 of the 8 fallback rows match.
- **"City > 85" and capital defence:** the 14 rows stay fixed, as they were in T249.
- **Swap pass (T251):** none of the 10 deterministic diplomacy divergences remains. Every remaining first divergence is
  a draw or a battle.
- **Order city once per seat (T252):** the 4 economy seats now match. Deployments, order counts (both games follow the
  original's stopping rule, 263/263) and the week-11 tax (113/113) all match.

## The Galatia row is a battle draw (attributed 2026-10-31, owner request)

- **The row:** S02 (Seleucid start), round 4, Galatia army 0 at (195,42). The original takes the mercenary-run branch,
  then attacks army 5 because its score of 91 is above 70. The remake ends in the garrison fallback.
- **Diagnostic** (`diag-galatia-v2/`, `tree-diag-v2.patch.txt`):
  - a scratch build of `8e2d9053` with two stderr lines, never pushed;
  - its AI log is identical to the v1 run's.
- **The remake's tree takes the same branch and the same city:** `MercenaryRun`, aradus (221,65), score 77, distance 26.
- **The army target differs:** the remake's is army-4 at (223,65), score 57. That is below the continuation threshold of
  71, and the city's 77 is not above 85. So the continuation is `None`, there is no offer to run to, no command is
  offered, and the fallback runs.
- **Why army 5 is missing:** it was fought earlier in the same round.
  - Both games play the seats in the same order from the human seat (Seleucid): `thracia … bithynia … galatia`.
  - Both games make Bithynia's army 11 attack Seleucid army 5 before Galatia's turn. That row is "same" in the report:
    score 1112, distance 5.
  - **Original:** the attack fails. Army 5 survives with 26,137 of 37,300 troops, and Bithynia's army is gone (round-end
    save `hooked-t04-AUTO0724.SAV`). Galatia then scores the weakened army 5 at 91, distance 23.
  - **Remake:** the attack wins (power 14,652 against 14,388, `events.jsonl`: `BattleArmyDestroyed`), so army 5 no
    longer exists for Galatia.
- **Cause: state.** This is a random battle result earlier in the round, not a port gap.
  - `compare.py`'s state flag missed it: it flags an army's own battle or death, not the death of its target army.
  - `attribution-aidecide-v1.json` is kept as measured.
- **So on `8e2d9053` no army decision in these 80 rounds remains unexplained.**
- **Earlier wording, corrected (research review, PR #152):** a first version of this finding read the remake's
  "mercenary hire: 0 offer(s)" line as "found no offer". That line (`AiMercenaryHirePass.cs:100`) counts offers hired,
  and the offer search plays no part in this row.

## The #144 boundaries are in 8e2d9053 (correction, 2026-10-31)

Earlier versions of this finding said the #144 corrections were not in this commit. **They are:** T250 made all three
faithful-only (`AiArmyTargetTree.cs`):
- the garrison fallback's capital radius is `< 10`, and its nearest city is taken in city-table order (strict `<`);
- the mercenary run skips offers at `>= 20` and walks the pool in slot order (strict `<`).

**Executed:** the #144 synthetic controls, rerun with `RemakeAdapter helperprobe` on `8e2d9053` (both layouts, 15
controls each), against the original's emulated answers (`controls-v1.json`, `controls-v2.json`):

| Remake | Controls matching the original |
|---|---|
| `10d3bb81` | 14 of 30 |
| **`8e2d9053`** | **28 of 30** |

- **Distance and tie controls:** all matched, in both layouts. That covers capital distance 9/10/11, offers at
  19/20/21, the 19-vs-20 pairs, the EBE8 table-order ties and the four E84C slot-order ties.
- **The two remaining:** the control "capital index −1", once per layout.
  - The original has no capital guard: it reads "city record −1" (the bytes before the table) and walks to (153,48).
  - The remake returns no destination.
  - The #144 finding already lists this as an ambiguity of the original. It is not a boundary.

## Open

- **Carthage fleet 0 (#174):** unchanged, as T250–T252 did not touch the fleet phase. Three rows changed verdict (S02 r4
  now the same; S02 r5 and S15 r3 now differ) because earlier moves in those rounds changed. The cause is still the
  route and moves state at the fleet's turn (see the fleet finding's "Open").
- **Not covered, as before:** rounds 6 and later, other seeds, the hunt branch, and the rest of #176.

## Evidence

- Data: `runs/experiments/data/run-exp-airerun/`:
  - `remake-8e2d9053-v1/`: the 80 replays;
  - the four reports and `attribution-aidecide-v1.json`;
  - `README.md`.
- The original's side: the hook runs and releases `run-exp-aidecide`, `run-exp-diplo`, `run-exp-econ` and
  `run-exp-fleetphase`. Saves cited: starts `S00_Rome_AUTO0720.SAV` … `S15_thracia_AUTO0720.SAV`, with round starts
  `hooked-tNN-*.SAV` (S02 round 4 = `hooked-t03-AUTO0723.SAV`).
- Galatia diagnostic: `runs/experiments/data/run-exp-airerun/diag-galatia-v1/` and `diag-galatia-v2/` (the scratch
  patch and the round's stderr, AI log, decisions and probe).
- #144 controls on 8e2d9053: `runs/experiments/data/run-exp-boundary144/native-8e2d9053-v1.jsonl`, `-v2.jsonl`.
- Code: the comparers are unchanged, except that `runs/experiments/aidecide/compare.py remake` now also passes `events=`,
  so one replay serves all four comparers.
