# The AI capital defence (FUN_0044efc8): first 9 threats in table order, nearest by list order, run before the army loop

**Tag:** [confirmed] for the rule from the decompile and the disassembly, and in emulation, where both order effects flip with
a swapped record. [confirmed] in play: 90 AI End turns with an observation-only hook, byte-identical to the plain build; no
order effect occurred there.
**Task:** research [#123](https://github.com/diegoami/imperial-conquest-2-research/issues/123), for imperial_conquest_2
T240/#1216, delegated to conquest on 2026-10-30.
**Background:**
- `2026-10-09-ai-intercept-and-fleet-hunt-in-play.md` (research-promoted) decoded this routine as the "homeland
  intercept" and checked 109 dispatches in play.
- `2026-10-30-army-table-order-after-deaths117.md` (Addendum 1) read it as "at most 10 threats". **Corrected here: 9.**

## The rule

`FUN_0044efc8` (dump :52776–52899; disassembly 0x44EFC8–0x44F31A). The nation's capital is city `474AB4[nation]`; P is its
position.

1. **The threat list,** in table order. A record is a threat when all of these hold:
   - its owner is ≥ 0 and not the current nation;
   - it lies in the capital's region and coast side (`FUN_0044eb9c(army, P)` = 0);
   - its Chebyshev distance to P is **≤ 19 when its owner is at war with the nation** (the owner's relation to the nation is
     3), and **≤ 9 otherwise**.

   Each threat is written to `list[n]` and then `n = min(9, n + 1)` (0x44F0A5–0x44F0C2). So **the list keeps the first 9
   threats in table order**. Every later threat overwrites the uncounted tenth slot and is never considered.
2. **Responders,** in table order: own armies with moves > 0, while fewer than `n + 2` have been dispatched.
   - **Skipped** when the enemy-army pick (`FUN_0044ee60`) or the city pick (`FUN_0044ece4`) has a score above 100, and that
     target is closer than the army's moves, and the capital is more than 3 × moves away (0x44F188–0x44F1D0).
   - So a responder with a strong, reachable opportunity far from home is left to it; every other responder defends.
3. **The choice:** the nearest listed threat that is alive (owner ≥ 0) and eligible. Eligible means the nation is at war with
   its owner (relation ≥ 3, 0x44F24F), or the responder is 20 or more from the capital (0x44F257). The distance is compared
   strictly (`jge` keeps the current best, 0x44F22B), so **on a tie the earlier list entry wins**, and the list is in table
   order.
4. **The order:** both tests are on the chosen **threat**, not the responder:
   - **toward the threat** (`FUN_0044dba8(responder, threat position)`) when the **threat** is not aboard a fleet (its record
     +8 ≠ −1; 0x44F29B loads the threat's index, 0x44F2A3 tests its +8) and the nation is at war with the **threat's owner**
     (relation 3, 0x44F2CA);
   - **otherwise toward the capital** (0x44F2D2–0x44F2E7), including whenever the threat is aboard.

   The responder walks at once, within the same call. `FUN_0044efc8` never tests whether the responder is aboard; that case
   is left to `FUN_0044dba8`'s own aboard branch.

   *Correction (2026-10-30, after research #123 / Research PR #128):* the first version said "when the nation is at war with
   its owner and it is not aboard a fleet", which could be read as the responder being aboard. It is the threat.

**Relation to the enemy-army pick.** The army phase `FUN_0044f31c` calls `FUN_0044efc8` first (:52918), then visits every own
army in table order. Its per-army logic, including `FUN_0044ee60`'s target pick, runs only for armies with moves > 0
(:52928). So the capital defence does **not override** the enemy-army pick in the sense of replacing it. It **acts first**:
- a dispatched responder walks toward the threat or home and spends its moves;
- if it still has moves left, the army loop then gives it its normal turn.

## Controls (emulation)

`runs/experiments/capdef123/controls.py`, on the #187 RAM snapshot with unmodified helpers and RNG; attacks and sieges are
logged and skipped. Current nation Carthage (1), capital Carthago at (93,78); its army 3 at (93,79) is the responder. The
threats' owners are set at war with Carthage both ways (`controls-v2.json`):

| Control | As staged | One record pair swapped |
|---|---|---|
| **tie**: a Roman army at (90,79) and a Seleucid army at (96,79), both 3 from the responder | the responder goes to **(90,79)** | **(96,79)** |
| **cap**: 12 foreign armies in the capital's region within 19; the nearest to the responder, at (90,76), is the 12th threat in table order | not listed: the responder goes to **(74,79)**, a farther listed threat | swapped into record 0, it is listed: the responder goes to **(90,76)** |

In the cap control the swap also changes army 2's target, from (74,79) to (74,80): the army that was at record 0 is now beyond
the list. `controls-v1.json` placed threats without the region test, so fewer than 9 were listed and the cap control showed
nothing; it is kept.

**So a cross-nation reorder, which the original makes after deaths and the remake does not, can change which threat a
responder goes to, and which threats are considered at all.**

## In play

An observation-only hook on the routine (`patches/capdef_hook.py`, three probes):
- at 0x44F0A5, each threat appended, with the count before it;
- at 0x44F226, each listed threat a responder compares: the distance, the best so far, the owner, the relation, and the
  responder's distance to the capital;
- at 0x44F273, each threat accepted.

It ran on the same three starts as the #117 tie hook (BASE.SAV, S13 Armenia, S10 Dacia), 30 End turns each, seed 12345. The
autosaves are **byte-identical to the plain build in 90 of 90 turns**.

| Measure | Count |
|---|---:|
| calls with at least one threat | 179 |
| threats listed per call | 1 in 157 calls, 2 in 22; never more |
| threats dropped by the 9-entry cap | **0** |
| responder decisions / dispatches | 134 / 89 |
| ties between eligible threats at the chosen distance | **0** |

So in these 90 turns **no capital defence was decided by table order**. A cross-nation reorder after deaths could not have
changed one, because no list held two threats at the same distance from a responder or more than 9 threats.

## What this does not establish

- **Later or crowded games:** a capital besieged by several nations' armies (more than 9 threats, or two at equal distance)
  did not occur in 90 early turns.
- **The city pick `FUN_0044ece4`,** used here only through its score in the exemption test; it was not read for table-order
  effects.
- **A threat aboard a fleet** (sent home instead) and the exemption branch in play; neither was isolated by the hook (the
  October finding saw no aboard threat either).
- **The remake.** Main has no port of `FUN_0044efc8` yet (#1216/T240). How T240 will order its threat list is for the main
  project; for faithfulness it needs the original's table order (with the sweep, PR #1605) and the 9-entry cap.

## Evidence

- Code: decompile `all_app_functions.txt` (SHA-256 `2018c205…`) :52776–52899 and the disassembly in
  `patches/capdef_hook.py`'s docstring.
- Controls: `runs/experiments/capdef123/controls.py` → `runs/experiments/data/run-exp-capdef123/controls-v1.json` (no region
  test, kept) and `controls-v2.json`.
- In play:
  - hook: `patches/capdef_hook.py`;
  - runner: `difftest/probes/capdef_hook_run.py`;
  - analysis: `runs/experiments/capdef123/analyze.py`;
  - data: `runs/experiments/data/run-exp-capdef123/` (`*-capdef.jsonl`, `<start>/inert.json`, `summary-v1.json`,
    `SAVES.sha256`);
  - saves: release `run-exp-capdef123` (hooked and plain autosaves, t01–t30 per start).
