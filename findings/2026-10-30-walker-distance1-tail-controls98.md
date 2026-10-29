# The army walker's distance-1 tail: contact branches confirmed; the strict-cost re-entry never decides in these controls

**Tag:** [confirmed, partial]: 27 synthetic controls, each with the current seat's human flag off and on, run on the pinned
unpatched original EXE (`9d753d5d…`) in Unicorn. Not a Wine or Windows run; not original gameplay.
**Task:** research [#98](https://github.com/diegoami/imperial-conquest-2-research/issues/98) (for remake
[#1329](https://github.com/diegoami/imperial_conquest_2/issues/1329) item 2), delegated to conquest on 2026-10-30.
Runner: `runs/experiments/walker98/tail_controls.py` (the method of `runs/experiments/terrain42/original_steps.py`);
data `runs/experiments/data/run-exp-walker98/tail-controls-v1.json`.

## The tail (decompile :51629–51657)

After its line loop, if the army is exactly 1 from the target, `FUN_0044d734` reads the target cell:
- terrain 2..11 → walk into it again only if its cost < the army's moves (strict);
- a city marker 20..99 → siege (`FUN_0044b27c`) if the city's owner is at war with the current nation and moves > 0;
  `FUN_0044f6d8` if not at war;
- an army marker 200..247 → attack (`FUN_0044aee4`) if its owner is at war and moves > 0;
- anything else → nothing.

## Method

A synthetic all-plain 320 × 140 map; the current nation's army 0 (3,000 light infantry) at (10,10) with the case's moves.
The target is at (10,9) (1 away) or (10,8) (a 2-tile walk). Where the case needs it, a city record (owner 0 or 1) or an
enemy army record (owner 1) sits at the target, with nation 0's relation to nation 1 set to 0 or 3. Terrain costs
come from the DAT (1, 3, 1, 1, 2, 4, 4, 4, 4, 4, 4, 4). Only presentation (redraw `0x445B38`, sound `0x45BF28`) is
stubbed. The three contact routines are intercepted at their entry and recorded, not run: this checks which branch the
tail takes, not the battle, siege or supply that follows.

## Results (identical for the AI and the human flag, except where noted)

| Target 1 away | Moves | Result |
|---|---|---|
| plain (cost 1) | 1, 2 | enters; 0 / 1 left |
| forest (cost 2) | 1 | stays. **AI: moves 0; human: moves 1** |
| forest | 2 (= cost) | **enters, 0 left** |
| forest | 3 | enters, 1 left |
| mountains / river (cost 4) | 3 | stays. AI: moves 0; human: moves 3 |
| mountains / river | 4 (= cost) | enters, 0 left |
| mountains / river | 5 | enters, 1 left |
| sea | 8 | stays, 8 left, no contact |
| own city (owner 0) | 8 | stays, 8 left, **`FUN_0044f6d8`** (non-war city) |
| city of nation 1 at peace | 8 | stays, 8 left, `FUN_0044f6d8` |
| city of nation 1 at war | 8 | stays, 8 left, **siege** |
| city at war | 0 | stays, no contact |
| enemy army at war | 8 | stays, 8 left, **attack** |
| enemy army at peace | 8 | stays, no contact |
| enemy army at war | 0 | stays, no contact |

2-tile walks (one plain step first, so moves − 1 are left at the last step): forest with 2 moves stays at (10,9)
(AI 0 left, human 1); with 3 it enters with 0. Mountains with 4 stays (AI 0, human 3); with 5 it enters with 0. A city or
an army at war reached with 1 move: the first step spends it, so no siege or attack.

## Answers

1. **Contact branches:** confirmed as read: siege or attack at war with moves > 0, `FUN_0044f6d8` for a city not at war
   (own or at peace), nothing for an army not at war or with 0 moves. Entering a marker cell never happens.
2. **Cost == moves:** the step into terrain whose cost equals the moves left is taken, with 0 left. That is the line
   loop's step (`FUN_0044d420`), not the tail. In every terrain case here, the tail's own strict re-entry (cost < moves)
   **never decides**: when the loop's step enters, the tail is not needed, and when the step is refused (cost > moves),
   the strict test fails too. The tail's terrain branch could matter only when a walk ends 1 away for another reason
   (for example a lateral step on the last stretch), which these controls did not produce.
3. **Human vs AI callers:** both callers (`TUnitMap_MoveHumanArmy` `0x446d9c` and the AI move `0x44dba8`) run this same
   walker and tail, and the tail's branches are identical under both flags. The flag changes only the step's handling of
   an unaffordable step: the AI's moves fall to 0, a human's are kept. That was already seen in
   `2026-10-21-strategic-lateral-steps-and-callers.md` (`human_unaffordable_preserves` / `ai_unaffordable_zeroes`). What
   differs between the callers is what they do after the walker returns: the human handler walks once more, the AI move
   recurses (`findings/2026-10-29-walk-stops-at-own-city-on-line230.md`,
   `findings/2026-10-30-ai-march-continuation-missing-in-remake.md`).

## What this does not establish

- A case where the tail's terrain re-entry decides the outcome. No synthetic walk here ends 1 away with cost < moves
  without the loop stepping in. Whether a lateral step on the last stretch can produce one is open.
- The battle, siege or supply that follows a contact: the routines were intercepted at their entry.
- Wine or Windows behaviour, real maps, or several armies or cities interacting. The army marker code used (203) is
  a synthetic marker in the 200..247 range.
