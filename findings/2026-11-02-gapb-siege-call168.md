# Gap B: the AI siege is the walk's end check (`FUN_0044d734` → `FUN_0044b27c`), not E84C; and where the 9 moves came from

**Tag:** [confirmed: Wine hook] for the call order, call sites, moves and the five sieges. [code] for `D734`'s guards (seed build
disassembly 0x44D895–0x44D949, and the Ghidra listing of `FUN_0044d734`). Wine only, no native Windows run.
**Task:** research issue [#168](https://github.com/diegoami/imperial-conquest-2-research/issues/168) (for remake #1724), routed
by the owner 2026-11-02. No remake change is requested here.
**Starts:** the published `run-exp-longrun-v090` saves `aab4starts/rome-t03end.SAV` (before Rome-game turn 4),
`rome-t06end.SAV` (turn 7), `rome-t01end.SAV` (turn 2), `carthage-t35end.SAV` (Carthage-game turn 36). One End turn each, seed 12345.

## Method

`patches/gapb_hook.py`: an observation-only build. At the entry of each function it logs the caller's return address, EAX, EDX
and ECX, the acting army's position and moves, the seat (0x4A0320), and the moves of two watched armies (table indices 2 and 5)
at every event. The functions are:
- FA20 (seat), F31C (army phase), E41C (supply pass), E84C (mercenary run);
- DBA8 (walk), D734 (line walk and end check);
- B27C (siege), AEE4 (attack army), F6D8 (non-war city);
- EBE8 (garrison fallback), AAB4 (fallback gate), plus AAB4's return at F31C 0x44F4CC.

Runner: `difftest/probes/fleetphase_hook_run.py` with `IC2_FLEET_HOOK=gapb_hook`. Data: `run-exp-longrun-v090/hooks-gapb-v1/`.
The hooked autosaves are byte-identical to the plain build in 4 of 4 (`inert.json`).
Analysis: `runs/experiments/gapb168/analyze.py` → `gapb168-analysis-v2.json`.

## 1. Which call besieges

Every AI siege in the four runs is `FUN_0044b27c`, called from **0x44D949**: the end of `FUN_0044d734`, the line walk that the
walk `FUN_0044dba8` calls. After walking its line toward the target, `D734` checks the target tile [code]:

| Address | Test | Then |
|---|---|---|
| 0x44D895–0x44D89E | `FUN_00449018(target, army position) == 1` (the army is next to the target) | else return |
| 0x44D8B6–0x44D8DC | map code 2–11 (land) and the army's moves > that terrain's cost | `D734` again (one more step) |
| 0x44D8EF–0x44D8F9 | map code 20–99: a city | |
| 0x44D929 | relation of the seat's nation (0x4A0320) to the city's **owner** == 3 (war) | else `FUN_0044f6d8(city, army)` |
| 0x44D93C | army moves (+6) > 0 | **`FUN_0044b27c(army, city)`**: the siege; it sets moves to 0 (research `decompiled-defection-and-siege-attrition.md`, 0x44B36C) |
| 0x44D950–0x44D98C | map code 200–247 (an army), at war, moves > 0 | `FUN_0044aee4`: attack the army |

`D734` doesn't test the city score, the mercenary offer, or which branch chose the target. Those decide only whether F31C walks
at that city.

**Measured sieges** (each `B27C@0x44D949`, reached through `DBA8 0x44DC16 → D734`):

| Start (turn) | Army | City | F31C walk that led to it | Moves at the siege | E84C before |
|---|---|---|---|---|---|
| rome-t03end (4) | Carthage 2 at (37,62) | 19 Castulo (36,61) | 0x44F4C7, the `e84c+city>85` continuation | 9 | yes, no walk of its own |
| rome-t06end (7) | Seleucid 5 at (178,41) | 202 Astacus (177,41) | 0x44F4C7, continuation | 10 | yes, no walk of its own |
| rome-t03end (4) | Seleucid 5 at (178,41) | 202 Astacus | 0x44F43F, `city>100` | 10 | no |
| rome-t03end (4) | Gaul 9 from (101,33) | 80, target (98,39) | 0x44F43F, `city>100` | 3 (after walking) | no |
| rome-t06end (7) | Carthage 3 from (51,43) | 31, target (49,41) | 0x44F43F, `city>100` | 6 (after walking) | no |

**The stage of the gap-B sieges:**
- They are not in E84C: E84C ran and made no walk call, so no offer drove a run.
- They are in the **continuation walk** at 0x44F4C7: `DBA8(army, city tile)`. The army is already next to the city, so `D734`
  takes no step and its end check besieges.
- They are not in the fallback: AAB4 = 1 after the siege, so EBE8 does not run.
- They are not in a later pass.

**Which callers were measured:** only F31C's 0x44F4C7 (continuation) and 0x44F43F (`city>100`) were seen ending in a siege. E84C's
own run walk (0x44E913) and F31C's 0x44F409 and 0x44F47C reached `D734` in these runs, but never next to an enemy city.
The end check is the same code for every caller [code], but its outcome wasn't observed through them. The human's Besiege order
is a separate caller, 0x44683C.

**Remake:** the continuation's `MarchAtCityTarget` (`AiMilitaryPhase.cs:433–440`) is a plain march. Its walk has no end check
that besieges an adjacent at-war city, so the army steps to another tile next to the city.

## 2. The move counts

| Row | Source | Moves |
|---|---|---|
| AAB4 table (PR #302), Carthage 2 "0 moves" | `hooks-aab4-v2/rome-t03end`, the AAB4 entry after the walk, in Carthage's seat | 0: the value right after B27C |
| "Carthage kept 9 moves" (#300's limitation) | `hooks-decide-v1/t03-a03/hooked-t01-AUTO0724.SAV`, the next autosave | 9: read **after a mid-round refill** |

`hooks-gapb-v1/rome-t03end`, the watched army 2 = Carthage 2:

| Seq | Event | Moves |
|---|---|---|
| 0–10 | F31C, E41C, E84C, DBA8, D734 and the B27C entry | 9 |
| 11 | AAB4 entry, after the siege | 0 |
| 33 | Illyria's FA20, the first event after Celtiberia's seat | 9; unchanged to the end of the round |

So the autosave shows 9. Seleucid 5 (`rome-t06end`) runs the other way round:
- 0 at the start of the round (left from the previous turn's siege);
- refilled to 10 at Illyria's FA20 (seq 19);
- 10 at the siege in its own seat, which comes after the refill, and 0 after it (seq 51).

That's why its save shows 0.

In all four runs both watched armies were restored to full **between Celtiberia's seat and Illyria's**. So a save's moves
depend on whether the nation's seat comes before or after that point. This is measured for the two watched armies only; the
refill's function wasn't hooked.

## 3. AAB4's full-budget test against a per-command comparison

- **What was compared,** for all 38 armies AAB4 rated in the four runs:
  - AAB4's measured predicate: AL = 1 when the army's moves differ from its recomputed full budget;
  - a per-command test: did the **last** F31C walk spend moves (moves at that DBA8 entry against moves at AAB4's entry).
- **They never differ (0 of 38).**
- **Earlier spending did occur, but the last walk always spent too:**
  - Carthage 3 (`rome-t03end`): E84C's run walk took 9 → 7, then the continuation 7 → 5;
  - Armenia 1 (`carthage-t35end`): E84C's run walk 10 → 3, and no continuation walk; AAB4 = 1.
- **The case where they could differ was not observed:** an earlier spend (capital defence, or an earlier continuation)
  followed by a last command that spends nothing. Capital defence wasn't hooked, and these starts didn't exercise it.
- **Keep the measured full-budget predicate.** These runs don't show it equals a per-command test.
- **The only AAB4 = 0** is Celtiberia 2 in `carthage-t35end`: F31C 0x44F409, DBA8 with no `D734` step and 8 moves. EBE8 ran
  for it (seq 11, called from 0x44F4D9).

## Open

- The guards in D734's end check are [code]. Only their "pass" side was measured: adjacent, city tile, at war, moves > 0.
- E84C with an offer in reach next to an enemy city: does its run walk away before the continuation? Not observed.
- The function behind the mid-round refill.
- Native Windows confirmation.
