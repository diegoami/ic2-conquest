# A player's move walks a second time in the original when the first walk ends short; the remake walks once (first seen with an own city on the line)

**Status:** promoted by research PR #94 (merge `683a484`), 2026-10-29, with the cause **established** (next section);
the two later cases promoted by research PR #95 (merge `4840439`), with both second walks replayed.
**Tag:** [confirmed, partial]. Single orders from the same save in both games, deterministic (a move draws nothing),
under Wine. One army, one blocking city.
**Tasks:** conquest [#230](https://github.com/diegoami/ic2-conquest/issues/230), found by the
[#232](https://github.com/diegoami/ic2-conquest/issues/232) rule-bot campaign; remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`), `classical-faithful`.

## In general

After a human army's move order, the original calls the army walker; if the army is still short of the target with
moves left, it calls the walker **once more** from the new position on a fresh line (`TUnitMap_MoveHumanArmy`). The
remake calls it once: its single walk equals the original's first call, step for step. A first walk ends short when
its chosen step is blocked (a city or army marker on the line) or costs more than the moves left, even if another
neighbouring tile would be affordable (the step rule of `2026-10-21-strategic-lateral-steps-and-callers.md`). Human
armies only. In the 15 finished #232 campaigns, 21 of the remake's 32 move orders ended short with moves left: those
are the moves where the original walks a second time (the second walk can be blocked too, as for Ptolemaic's army,
whose target lies across sea).

## Answer

Start: `BASE.SAV` (Rome, 270 BC Spring week 1). Rome's army 1 (8 moves) stands at (120,53). On the exact diagonal
toward the north-west, its second tile (118,51) is Venusia, Rome's own city. A city marker blocks an army's path.

| Order (army 1, one click / one `move`) | Original | Remake |
|---|---|---|
| toward (99,32), 21 tiles | ends at **(115,49)**, 1 move left | ends at **(118,52)**, 6 moves left ("spending 2 of 8 moves") |
| toward (116,49), within reach | ends at **(116,49)**, 3 moves left | ends at **(118,52)**, 6 moves left |
| north to (120,48), clear land line (control) | (120,48) | (120,48): same |

So the original's walk steps around the blocking city and goes on along the line. The remake's walk takes one
side step, to (118,52), and stops with most of its moves unspent.

The original's step rule is documented: `findings/2026-10-21-strategic-lateral-steps-and-callers.md` (cheapest of
the line cursor and two alternatives; the line is left only for a strictly cheaper one). The army navigation rule is
`findings/2026-10-24-army-navigation-rule187.md`. This case adds what that work did not observe: a human army's walk
with an own city on the line. The first draft left open which step the remake's walker refuses after the side step;
research found that no step refuses (next section).

## Cause (research PR #94, [confirmed: original instructions replayed])

`TUnitMap_MoveHumanArmy` (`0x446d9c`, dump :46713) calls the army walker `FUN_0044d734` once. If the army is still short
of the target (`FUN_00449018 > 0`) and has moves left, it calls the walker a **second time**, from the new position
on a fresh line. Research replayed the pinned unpatched EXE (`9d753d5d`) in Unicorn on
`walk-city-on-line/original/a000.SAV` (army 1):
- **one walker call:** (120,53) → (119,52) → (118,52), 6 moves left, for both targets. That is exactly the remake's
  result;
- **the handler's two calls:** (115,49) with 1 left for (99,32), and (116,49) with 3 left for (116,49). That is
  exactly the original's saves;
- **the clear-line control** (120,48) ends in one call with 3 left, in both.

So the remake's walker matches the original's single walk; the missing piece is the handler's second call. No step
refuses; the second walk is never made. Remake v0.8.4 cites `TUnitMap_MoveHumanArmy` only for the stay-selected rule
(`MapClickRules.cs:170`, `GameMapView.cs:1327`).

## Two more cases from other nations (added 2026-10-29, after the promotion)

The #232 campaigns from nine more New Game starts found two more walks that end apart. Reproduced as single orders
(run `run-exp-diff084-orders-b5`, cases written before running, turn 0720):

| Start | Order | Original | Remake |
|---|---|---|---|
| `S01_Carthage_AUTO0720.SAV` | army 3 from (93,79) toward (61,56) | (89,76), 0 moves left | (90,77), 1 left ("spending 7 of 8") |
| `S06_Gaul_AUTO0720.SAV` | army 9 from (93,28) toward (92,34) | (92,34), 1 left | (92,32), 3 left ("spending 5 of 8") |

Both fit the cause above: the remake stops with moves left, short of the target, where the original's second walk
goes on. Neither has an own city on the line, so the cause is not specific to cities. **Replayed by research (PR #94's
method, PR #95, merge `4840439`):**
- Carthage: one walker call gives (93,79) → (92,78) → (92,77) → (91,77) → (90,77) with 1 move left, the remake's
  result; two calls add (89,76) with 0 left, the original's.
- Gaul: one call gives (93,28) → (92,28) → … → (92,32) with 3 left, the remake's; two calls add (92,33) → (92,34) with
  1 left, the original's.

So the missing second walk is general: whenever the first walk ends short with moves left, the remake matches the
single call exactly. In the Gaul campaign, Rome's AI destroyed the Gaulish army where the
original's walk had put it, next to Roman territory, at (92,34); in the remake it stood two tiles away and survived.

## Found in play

The #232 campaign `rome-rulebot1-5t` (rule bot, 5 turns, seed 12345) gave both games the same orders in turns 1–3.
Rome's own records differed from turn 1 because of this walk: army 1 ordered to (99,32). Army 1's different position
then made the bot's turn-4 orders differ (it bought supplies in the original and marched in the remake). Data:
`runs/experiments/data/run-exp-diff084-campaign/`.

## Evidence

Run `run-exp-diff084-orders-b4` (turn 0720): `walk-city-on-line/original/a001.SAV` vs `walk-city-on-line/remake/a001.SAV`,
`walk-city-on-line-near/…/a001.SAV`, `walk-line-clear-land/…/a001.SAV`. The case `walk-line-clear` targets (120,45),
which is sea, so it is the known sea-target command gap, not a control
(`findings/2026-10-29-v084-known-differences-and-command-gaps.md`). Original: `fast rollingsave seed.exe`
(SHA-256 `354d8265…`), seed 12345, Wine 10.0.
