# A long walk whose line crosses an own city goes around it in the original; the remake stops after one side step

**Status:** promoted by research PR #94 (merge `683a484`), 2026-10-29, with the cause **established** (next section).
**Tag:** [confirmed, partial]. Single orders from the same save in both games, deterministic (a move draws nothing),
under Wine. One army, one blocking city.
**Tasks:** conquest [#230](https://github.com/diegoami/ic2-conquest/issues/230), found by the
[#232](https://github.com/diegoami/ic2-conquest/issues/232) rule-bot campaign; remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`), `classical-faithful`.

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
with an own city on the line. Which step the remake's walker refuses after the side step was not read.

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

The earlier text below asked "which step of the remake's walker refuses after the side step"; the answer is none.

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
