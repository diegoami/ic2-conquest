# In play, the original's AI move always walks again: the stale word it tests is never −1

**Status:** promoted by research PR #102 (merge `0a30a80`; research re-compared the hooked and plain autosaves itself, all
identical), with one correction (call sites, below); rules consolidated in research `docs/rules-specification.md` (PR #103).
**Tag:** [confirmed, partial]: observed in the running original under Wine with an observation-only hook, 5 starts × 5 AI End
turns (seed 12345). The hooked build's autosaves are byte-identical to the unpatched seed build's in all 25 turns.
**Task:** research [#97](https://github.com/diegoami/imperial-conquest-2-research/issues/97) (for remake
[#1585](https://github.com/diegoami/imperial_conquest_2/issues/1585)), delegated to conquest on 2026-10-30. Follows
`findings/2026-10-30-ai-march-continuation-missing-in-remake.md` (research PR #100's stale-word correction).

## Question

`FUN_0044dba8` keeps its intermediate point in the word `[ebp-0xa]`, written only by the `FUN_0044db38` branch. On the
direct-line branch (`FUN_0044cb40` non-zero) the word is not written, yet the no-progress fallback (`0x44DC4D`) and the
recursion (`0x44DC8C`) test `cmp word [ebp-0xa],-1; jle`. So on the direct path, whether the AI walks again depends on a
stale stack word. What does it hold in play?

## Method

`patches/walk_hook.py` builds `… seed walkhook.exe` from the seed build with three probes; each saves and restores
EFLAGS and every register:
- **A:** the call to `FUN_0044cb40` at `0x44DC06`. Logs the direct-line result, the army, the target, `[ebp-0xa]` at
  entry, the army's position and moves, and the return address of `FUN_0044dba8` (the call site).
- **B:** the recursion test at `0x44DC8C`, reached only when the target is more than 1 away with moves left.
- **C:** the no-progress test at `0x44DC4D`.

`difftest/probes/walk_hook_run.py` played 5 End turns from each start (Rome, Carthage, Gaul, Seleucid, Armenia New Game
starts), the human seat giving no orders, read the log from game memory after each turn, then replayed the same turns
with the unpatched build. **All 25 autosaves are byte-identical**, so the hook changes nothing.

## Results (666 records)

| | Count |
|---|---|
| A: AI moves past the fleet branch | 424: **direct path 346**, intermediate path 78 |
| `[ebp-0xa]` at entry, direct path | **49 (207), 71 (133), 0 (6): never −1** |
| `[ebp-0xa]` at entry, intermediate path (before `FUN_0044db38` writes it) | 49 (49), 71 (19), 0 (10) |
| B: recursion tests (short of the target, moves left) | 152: **all pass**: 131 on the direct path, 21 on the intermediate path |
| C: no-progress tests | 90 on the direct path: **all pass** (the fallback point is tried) |
| lowest word seen at B and at C | 0 |
| moves left at B | 1 (6), 2 (13), 3 (18), 4 (16), 5 (83), 6 (12), 7 (4) |

So in play, the stale word on the direct path is a leftover stack value (49, 71 or 0 here), never −1, and **the AI always
walks again when a walk ends more than 1 short with moves left**, on either path. Research's replay showed both
outcomes are possible in principle (stale −1: one walk, the remake's result; stale 0: recursion). In these 25 turns only
the second occurs.

**Consequence for the frequency:** the bracket in the AI march finding (0.5–28% of AI marches end differently in the
original) collapses to its upper end. **About 28% of the remake's AI marches stop where the original's would walk on**
(still assuming the original takes the same path).

## Call sites

`FUN_0044dba8` is called from **10** sites plus its own recursion (`0x44DCA1`). A byte scan of the pinned EXE for
`E8` calls into `0x44DBA8` finds `0x44E913, 0x44EC7D, 0x44ECD6, 0x44F2E7, 0x44F2F9, 0x44F409, 0x44F43F, 0x44F47C,
0x44F4A3` and **`0x44F4C7`**. The last is missing from #97's list of 9: it moves the army to a city's coordinates
(`[0x47959E + 34·i]`). Calls seen (A records, by return site): recursion 152, `0x44F47C` 117, `0x44F43F` 52, `0x44F409` 49,
`0x44F2F9` (intercept toward a threat army) 23, `0x44E913` 12, `0x44F4C7` 10, `0x44F4A3` 5, `0x44EC7D` 2, `0x44ECD6` 2.
`0x44F2E7` (intercept toward the capital) was not seen. By each B record's own return address, the recursion tests were
reached mostly in top-level calls (141): `0x44F47C` 93, `0x44F43F` 18, `0x44F409` 15, `0x44F2F9` 11, `0x44E913` 2,
`0x44ECD6` 1, `0x44EC7D` 1. Only 11 were in recursive frames. (Corrected after research PR #102: the first version linked
each B to the latest A record of the same army, which after a recursion is the inner call's, and said "mostly within
recursive calls (138)".)

## What this does not establish

- That the word can never be −1 in play: 5 starts × 5 turns, one seed. Its value is whatever an earlier call left in that
  stack slot (49, 71 and 0 here), so other call histories could leave −1.
- Which earlier routine leaves 49, 71 or 0 there.
- That the original would take the same path as the remake's AI for the same march (the frequency's assumption).

## Evidence

Data: `runs/experiments/data/run-exp-walk-hook97/`: `t5/<start>-walk.jsonl` (decoded records with the turn), `t5/summary-v1.txt`,
`t5/<start>/inert.json` (the 5 hooked and 5 plain autosave hashes per start and their equality). Saves:
`t5/<start>/hooked-tNN-AUTOnnnn.SAV` and `plain-tNN-…` (release `run-exp-walk-hook97`). The earlier 2-turn smoke run on
`BASE.SAV` is kept beside them. Hooked build: `patches/walk_hook.py` from `fast rollingsave seed.exe` (SHA-256 `354d8265…`),
whose code is the pinned EXE's (`9d753d5d…`) apart from the seed and autosave patches.
