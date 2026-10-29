# The original's AI army move keeps walking until it arrives or runs out of moves; the remake's AI marches once

**Tag:** [derived: code] on both sides; not measured in play. For research issue
[#97](https://github.com/diegoami/imperial-conquest-2-research/issues/97) (remake
[#1585](https://github.com/diegoami/imperial_conquest_2/issues/1585)). Remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`). Original decompile: `all_app_functions.txt`
(SHA-256 `2018c205…`), :51792.
**Related:** the human-move gap, `findings/2026-10-29-walk-stops-at-own-city-on-line230.md` (the human handler's single
second walk, missing in the remake).

## Answer

**Original.** The AI army move `FUN_0044dba8(army, target)` (:51792):
1. **Aboard a fleet:** the army moves the fleet (`FUN_0044cd08`) and loses 2 moves; no walk.
2. **Otherwise:** if the direct line passes `FUN_0044cb40`, it walks toward the target (`FUN_0044d734`, the same
   walker as human moves). Else it walks toward an intermediate point from `FUN_0044db38`.
3. **No progress:** if the army's moves are unchanged by that walk (it did not move), moves remain and the point
   is valid, it walks toward a fallback point from `FUN_0044cec8`, then spends 1 move whatever happened.
4. **Recursion:** if the Chebyshev distance to the target (`FUN_00449018`) is still more than 1, moves remain, and
   the point and target are valid, it **calls itself again** from the new position, with a fresh line and a fresh
   intermediate point.

So an AI army re-walks until it is next to its target or out of moves. There is no fixed number of re-walks. Step 3's
forced move cost guarantees an end. This is the AI's counterpart of the human handler's second walk, and it is not
limited to one.

**Remake.** An AI march is one `MoveArmyCommand` (`AiMilitaryPhase.AddMarchCandidate`), aimed at the target or at a
single intermediate point (`ClassicalArmyNavigation.Intermediate`), and executed once by the same handler as human
moves: one walk. The army is then added to `marched`, and "an army that has already marched this turn is offered
only the attack its target allows, never a second march" (`AiMilitaryPhase.cs`, the `ProposeArmyTree` summary;
`AiTurn.cs` loop). An AI walk that ends short with moves left therefore stops there.

## Consequence

The gap in #1585 is wider than the human move:

| Mover | Original | Remake v0.8.4 |
|---|---|---|
| human army | walker, plus **one** second walk if short with moves left (`TUnitMap_MoveHumanArmy`) | one walk |
| AI army | walker repeated (fresh line and intermediate point each time) until within 1 tile or out of moves, with a forced-cost fallback when stuck | one walk per turn |

A fix that adds one second walk to the shared `move` command would match human moves, but would still leave AI
armies short of the original's continuation. The AI needs the recursion (or an equivalent loop) of `FUN_0044dba8`,
including its no-progress step.

## What this does not establish

- No AI walk was replayed or observed here. The #232 campaigns cannot isolate it, because the two games' AI chose
  different targets after the first End turn. Research's replay method (Unicorn on the pinned EXE, as for the human
  walk) can confirm the recursion on a known AI army and target.
- How often an AI walk ends short with moves left in play. In the remake, a probe of the AI log ("approach … N tiles
  away") against the army's final position would count it.
- The exact semantics of `FUN_0044cb40` (direct-line test) and `FUN_0044cec8` (fallback point); this reads only
  their use.
