# The #925 reachable tiers: Improved preset only; classical-faithful marches like the original (owner decision)

**Tag:** owner decision, 2026-10-31, with the evidence it rests on ([confirmed], cited).
**Decision (the owner, 2026-10-31):** the remake's #925 "Hazards" tiers apply **in the Improved preset only**. In
**classical-faithful**, AI armies march at the original's destination, as the original does. The tiers are:
- the reachable resupply city;
- the reachable garrison fallback;
- the emergency move.

The owner had adopted them on 2026-10-10 on remake #925.

## What the tiers change

| | Original | Remake (tiers on) |
|---|---|---|
| destination | `FUN_0044e670`'s home city (resupply), or `FUN_0044ebe8`'s nearest city / capital (garrison) | the same pick, kept only if the remake's walker would move toward it this turn (`IsUsableDestination`); otherwise the next reachable candidate, then the first reachable garrison city, then an emergency move to a reachable tile near an own city |
| the march | `FUN_0044dba8` marches at the pick. Next to the city it swings out and back (the no-progress fallback, research #105) or stays; it never checks beforehand | only towards a destination already shown to be reachable |

## Evidence

- **`2026-10-30-ai-decisions-vs-remake-main.md` §3** (749 decisions, 16 New Game starts × 5 rounds, each round from the
  original's own autosave):
  - **252 resupply rows and 8 fallback rows** differ through the tiers. That is the largest group after "same".
  - **238** of the 252 have the army standing next to its home city. The original keeps it there (BASE turn 1:
    Macedonia army 8 swings out to (147,44) and ends at (144,42) next to Pella). The remake walks it to another city
    (Thessalonica).
  - In the other **14**, with the tier skipped, the remake's own `ScoreResupplyCity` picks exactly the original's city
    (14/14).
- **Recheck on `05b02936`:** 250 + 8 rows remain, and every other army decision matches.
- **`2026-10-30-ai-diplomacy-vs-remake-main.md` and `2026-10-31-ai-economy-vs-remake-main.md`:** no tier involvement.

## For the remake

- In `classical-faithful` (`AiEconomyModel.Original` / `ClassicalArmyNavigation.Applies`):
  - `ResolveResupplyCity` should return `ScoreResupplyCity`'s pick;
  - `GarrisonFallback` should return the nearest city of any owner (strict `<`, first in the city table), or the
    capital;
  - the emergency tier should not run.

  The army then marches with the original walk, including the no-progress swing and the "stays put" case.
- The §4 boundary items of the same finding, also confirmed in execution (`2026-10-30-garrison-and-mercenary-boundaries144.md`),
  belong to the same functions: capital radius `< 10`, offer range `< 20`, ties by table order.
- After the change, the comparison expects the 238 + 14 resupply rows and the 8 fallback rows to match. They can be
  rechecked with `runs/experiments/aidecide/compare.py` on the new build.
- The Improved preset keeps the tiers unchanged.

## What this does not decide

- Anything about the Improved preset beyond keeping the tiers.
- The remake's implementation. This is the owner's direction and the original's behaviour, not a patch.
