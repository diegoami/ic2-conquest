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
| Army decisions (749), by cause | 422 same, 250 #925 resupply, 8 #925 fallback, 14 "city > 85" target, 41 diplomacy, 14 state | **691 same**, 41 diplomacy, 16 state, **1 unattributed** (labelled `h925-fallback` by `attribute.py`; see Open) |
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

## Open

- **One army row:** S02 (Seleucid start), round 4, Galatia army 0. The original takes the mercenary run
  (`FUN_0044e84c` finds an offer, then army score 91 > 70 attacks army 5). The remake makes no such decision and ends in
  the garrison fallback.
  - Before T250 this row was one of the 8 "#925 fallback" rows. With the faithful fallback in place, it shows up as its
    own difference.
  - **Correction (research review, PR #152):** this finding first said the remake "misses an offer" because of its line
    "mercenary hire: 0 offer(s) hired across 0 army/armies". That line (`AiMercenaryHirePass.cs:100`) counts offers
    **hired**, not offers found, so the log does not show that the remake found no offer.
  - `attribution-aidecide-v1.json` still labels the row `h925-fallback`. `attribute.py`'s rule matches every
    "no remake decision + garrison fallback" row, but in faithful mode that fallback is the original's own `FUN_0044ebe8`
    pick, not the #925 tier. Read the label as **unattributed**.
  - The next step is a probe of the remake's offer search on `hooked-t03-AUTO0723.SAV`.
  - It is not the #144 offer-range boundary. There the remake is the more permissive side (`<= 20` against the
    original's `< 20`). The open #144 corrections (capital radius `< 10`, offer range `< 20`, ties in table order) are not
    in this commit.
- **Carthage fleet 0 (#174):** unchanged, as T250–T252 did not touch the fleet phase. Two rows changed verdict (S02 r4
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
- Code: the comparers are unchanged, except that `runs/experiments/aidecide/compare.py remake` now also passes `events=`,
  so one replay serves all four comparers.
