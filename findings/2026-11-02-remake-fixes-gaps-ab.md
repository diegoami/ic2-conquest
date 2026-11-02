# Remake fixes for the long-run AI gaps A and B (Faithful), from the confirmed original behaviour

**Tag:** [derived] from two promoted reports: research PR #165/#167 `2026-11-02-longrun-v090-ai-gaps.md` and research PR
#169 `2026-11-02-gapb-siege-call168.md`. Both causes are [confirmed: Wine hook]; no native Windows run. No new measurement here.
**Task:** owner 2026-11-02: what the IC main session should change, as a finding for intake and not a prompt only.
**Remake:** v0.9.0, `88c1989b` (code references at that commit). Both gaps are older (v0.8.4, `8e2d9053`, `e20a6488`).
**Correction:** the longrun finding's gap-A wording "test spent moves (moves after the command < moves before)" is replaced
by the full-budget gate below (the original's test). The two agreed in all 38 measured walks, but they were never compared
where they could differ.

## Gap A: gate the garrison fallback on the full budget, not on the tile

- **Original:** after a walk, F31C calls `FUN_0044aab4`. The fallback `FUN_0044ebe8` runs only when it returns 0.
  `AAB4 = (recomputed full moves != the army's moves)`: the army spent part of its allowance anywhere in the seat.
- **Remake:** `AiTurn.cs:336–351` (T156) runs `RunGarrisonFallback` when the command was accepted and
  `beforeTile == afterTile` with moves > 0. An out-and-back walk (the original's swing) leaves the tile unchanged and spends
  moves, so the remake runs a fallback the original skips. Capital armies drift away every turn (410 rows over four games).
- **Fix (Faithful):** run the fallback only when the army's moves still equal its full allowance for the turn; drop the
  tile comparison.
  - Use the allowance the remake gives the army at the start of its seat, the counterpart of AAB4's recomputed value.
  - Not "moves after this command == moves before it". The original's test also counts moves spent earlier in the seat (an
    E84C run walk, capital defence).
- **Expected after the fix:** Macedonia 8 at (144,42), the Media, Thracia, Ptolemaic and Antioch capital armies, and Armenia 1
  at Van stay on their tile, as in the original.
- **Side fix:** the log line "garrison fallback moved army-N to (x, y)" prints the target; print where the army ended.

## Gap B: the AI walk's end check besieges or attacks the adjacent target

- **Original:** the walk `FUN_0044dba8` calls the line walk `FUN_0044d734`, which steps along its line and then checks the
  target tile (0x44D895–0x44D98C):
  - the army is next to the target: `FUN_00449018(target, army) == 1`;
  - **a city** (map code 20–99): if the seat's nation is at war with the city's **owner** and the army has moves > 0, it calls
    `FUN_0044b27c(army, city)`, the siege (moves → 0). Not at war: `FUN_0044f6d8(city, army)`;
  - **an army** (map code 200–247), at war, moves > 0: `FUN_0044aee4`, the attack;
  - land the army can enter with its moves: one more step.
  
  The check doesn't test the city score, the offer or the branch.
- **Measured:** all 5 AI sieges came from this check, through F31C's walk at:
  - 0x44F4C7, the `e84c+city>85` continuation: the gap-B armies, Carthage 2 at Castulo and Seleucid 5 at Astacus;
  - 0x44F43F, `city>100`: 3 sieges.
- **Remake:** the MercenaryRun continuation `MarchAtCityTarget` (`AiMilitaryPhase.cs:433–440`) is a plain `MoveArmyCommand`. The
  walker can't enter the city and moves the army onto another adjacent tile, so there's no siege. The remake already
  besieges in the `AttackCity` path (city score ≥ 102), which matches the original's `city>100` outcome.
- **Fix (Faithful):** when an AI march at a city target ends with the army next to that city, the city's owner at war with
  the army's nation and moves > 0, besiege it (moves → 0) instead of stepping aside. When the target tile holds an army at
  war, attack it.
  - **Scope it to what was measured:** the continuation after the mercenary run, and the attack-city walk.
  - **Not observed, so not claimed:** E84C's own run walk (0x44E913), and the 0x44F409 / 0x44F47C walks ending next to an
    enemy city. The original's end check is shared code, so the same rule likely applies there too.
- **Expected after the fix:** Castulo loses 3 loyalty points a turn (80 → 77 → 74 → 71) and Astacus 2 (52 → 50 → … → 44),
  the army loses 500–1,100 troops a turn, and the army stays on its tile.

## Reading moves in saves

AI armies' moves are refilled to full between Celtiberia's seat and Illyria's, in every measured round. A save shows spent
moves for seats after that point and full moves for seats before it. Rechecks of both fixes should compare positions,
loyalty and troops, or read moves at the seat's own end (the hook), not in the save.

## Recheck plan

On the fixing pin: `python3 -m difftest.pin build <ref>`, then the anchored long runs (`difftest/anchored.py`) on the stored
original games and `runs/experiments/longrun-v090/stays.py`. Expected result: the 410 capital-army rows and the 17
enemy-city rows go to 0. The remaining rows are draws.
