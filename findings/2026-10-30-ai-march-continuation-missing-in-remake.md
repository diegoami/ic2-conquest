# The original's AI army move keeps walking until it arrives or runs out of moves; the remake's AI marches once

**Status:** promoted by research PR #100 (merge `d77a43e`), with a correction (next section); the frequency section
promoted by research PR #101 (merge `8c33560`): all 48 probe files reproduce. The distance after the walk is measured
to the march's aimed point (the target or the remake's intermediate point), not to the final target.
**Tag:** [derived: code] on both sides; the remake-side frequency [confirmed] (probe below). For research issue
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

## Correction (research PR #100): the direct path depends on a stale stack word

In the disassembly (pinned EXE `9d753d5d`), the intermediate point is the local `[ebp-0xa]`. Only the `FUN_0044db38`
branch writes it (`0x44dc1e`–`0x44dc26`). The direct-line branch (`FUN_0044cb40` passes, `0x44dc0f`–`0x44dc1b`) skips
the write, yet both the no-progress fallback (`0x44dc4d`) and the recursion (`0x44dc8c`) test
`cmp word [ebp-0xa],-1; jle`. So **on the direct path, the AI continues only if that stale word happens to be ≥ 0**.
Research's Unicorn replay: Rome's army 1, (120,53) → (99,32) on the direct path, ends at (118,52) with 6 left (the
remake's result) when the stale word is −1, and recurses to (115,49) with 0 left when it is 0. Carthage's army 3 →
(61,56), on the intermediate-point path, recurses three times whatever the stale word: (93,79) with 8 → (93,82) with 5
→ (93,85) with 2. What the word holds in play is open (research #97, delegated here).

## How often (remake, measured)

Probe: `RemakeAdapter aiprobe` (`difftest/remake_adapter/AiProbe.cs`). It plays 10 End turns from each of the 16 New
Game starts with 3 seeds (48 runs) and records, for every AI march the remake's AI log names, the march's own
`ArmyMoved` event (from, to, moves spent). The moves left are estimated with the remake's refill rule. Data:
`runs/experiments/data/run-exp-diff084-aiprobe/` (`summary-v1.txt`, one jsonl per run).

| | AI marches |
|---|---|
| logged | 5,105 (94 armies gone by the end of their round) |
| walked | 5,011 |
| ended within 1 tile of the aimed point | 2,984 (59.5%) |
| **ended more than 1 tile short WITH moves left** | **1,406 (28.1%)**: approach an enemy army 781, approach a city 436, mercenary run 100, garrison fallback 32, via an intermediate point 26, resupply 24, defend the resupply city 7 |
| ended short with no moves left | 621 |

Moves left in the 1,406: 1 (365), 2 (197), 3 (245), 4 (127), 5 (56), 6 (145), 7 (86), 8 (142), 9 (43). These are the
marches where the original's `FUN_0044dba8` reaches its recursion test with moves left (assuming it chose the same
path as the remake's AI, which this probe does not check). The 26 the remake routed via an intermediate point would
recurse in the original on that path. The other 1,380 went straight at the target, where the original continues only
when the stale word allows it. So **the remake's AI stops short with moves left in about 28% of its
marches; the share that ends differently in the original lies between 26/5,011 (0.5%) and 1,406/5,011 (28%)**, set by
the stale word.

## Consequence

The gap in #1585 is wider than the human move:

| Mover | Original | Remake v0.8.4 |
|---|---|---|
| human army | walker, plus **one** second walk if short with moves left (`TUnitMap_MoveHumanArmy`) | one walk |
| AI army | walker repeated (fresh line and intermediate point each time) until within 1 tile or out of moves, with a forced-cost fallback when stuck; on the direct path only when the stale `[ebp-0xa]` is ≥ 0 | one walk per turn |

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
