# Army paths in play match the emulator; fleets walk like armies, and the human fleet's second walk is missing in the remake

**Tag:** [confirmed, partial]: army paths observed in the running original under Wine with an observation-only hook (saves
byte-identical to the unpatched build); fleet rules from Unicorn controls on the pinned EXE; two live original-vs-remake
fleet cases. Native Windows acceptance is out of scope (owner).
**Task:** research [#42](https://github.com/diegoami/imperial-conquest-2-research/issues/42) (for
imperial_conquest_2#1012), remaining part, delegated to conquest on 2026-10-30. Remake v0.8.4 (`d9cc71bc`). Already settled
elsewhere: the army step rule (`2026-10-21-strategic-lateral-steps-and-callers.md`), the human army's second walk, the AI
army's recursion and stale word, and the walker's distance-1 tail.

## 1. Crossed tiles in play (armies)

`patches/step_hook.py` builds `… seed stephook.exe`. Its probe on the army step `FUN_0044d420`'s prologue logs, per step:
the army and its position and moves before the step, the walker's line cursor (the cell about to be taken, `[P-2]/[P-4]` of
the walker's frame) and the call site. Every register and flag is restored. Runner `difftest/probes/step_hook_run.py`;
each session was also played by the unpatched seed build: **all saves byte-identical**.

**The C4 source-save walks** (`BASE.SAV` = `run0-start-AUTO0720-seed12345.SAV`, army 0 at (100,37), 8 moves):

| Order | Steps in play (position before each step → cursor) | End |
|---|---|---|
| → (100,25) | (100,37)→(100,36), (100,36)→(100,35), (100,35)→(100,34), (100,34)→(100,33) **taken as (101,33)**, (101,33)→(100,32), then straight to (100,29) | (100,29), 0 moves |
| → (100,32) | the same first five steps, through **(101,33)** | (100,32), 3 moves |

These are the emulator's traced path through (101,33) and its endpoints (`far12` (100,29,0), `near5` (100,32,3)), now
seen in play.

**AI walks** (two End turns from the same start): 160 steps by 23 AI armies, all from the walker's line loop (call site
`0x44D873`). In 26 of 126 consecutive steps the army left its line for a lateral cell: for example, Gaul's army 9 at
(94,29) with the cursor at (95,30) went to (95,29). `ai-2-steps.jsonl` has every step.

## 2. Fleets

Unicorn controls on synthetic all-calm-sea maps (`runs/experiments/fleet42/fleet_controls.py`; calm sea costs 1, rough sea
3), fleet 0 at (10,10) with 30 ships:

| Case (walker `FUN_0044e094`) | Result |
|---|---|
| 3 calm tiles north, 8 moves | straight, (10,7), 5 left |
| rough sea on the line, both laterals calm | lateral **east** (11,9), back on the line, (10,6) with 4 left |
| rough on the line, east lateral rough | lateral **west** (9,9) |
| rough on the line, east lateral a fleet marker | lateral west (9,9): the marker blocks |
| rough on the line and both laterals | straight through the rough cell (cost 3), 2 left |
| rough target 1 away (cost 3), moves 3 / 2 / 4 | enters with 0 left (**cost == moves enters**) / stays, 2 left / enters, 1 left |
| island on the line | lateral east, then back on the line |
| land on the line and both laterals | no step, 8 moves left |

The same step rule as armies: a lateral is taken only when it is strictly cheaper, the east one first on ties, a marker
blocks, and cost == moves enters.

**Human fleet handler** (`TUnitMap_MoveHumanFleet`, `0x446E24`): like the army handler, it calls the walker again when the
fleet is still short of the target with moves left (decompile :46761/:46766). In the emulator (unit-map UI calls stubbed):
- **synthetic maps:** on 103 of 400 random obstacle maps, the handler's second call ends elsewhere than one walker call;
- **real map:** on the real map of `saves/fleet-port-antium-0734.SAV` (`search_real_map.py`), 75 targets within 14 tiles of
  Rome's fleet 2 differ.

**Remake:** `MoveFleetCommandHandler` makes one `MovementWalker.Walk`. Two of the real-map targets were run live in both
games from that save (cases written before running, `difftest/cases/orders230_b7.py`):

| Fleet 2 (101,46), 29 moves, toward | Original | Remake |
|---|---|---|
| (88,32) | (88,32), 14 left | (93,37), 19 left |
| (87,47) | (87,47), 14 left | (89,48), 16 left |

Both exactly as predicted: the original's two walks against the remake's one. **So the missing second walk
(`2026-10-29-walk-stops-at-own-city-on-line230.md`, remake #1585) applies to human fleet moves too.**

**AI fleet routine** (`FUN_0044e1fc`, called from `0x44F608`): it mirrors the AI army move. On the direct path it walks to
the target; otherwise it walks toward a point from the route finder `FUN_0044d174`; it has a no-progress fallback (1 move)
and recurses while the target is more than 1 away and moves remain; then comes a distance-1 tail. **Unlike the AI army move,
it has no stale-word issue:** its intermediate-point local is set to the target before the branch (`0x44E225`/`0x44E22A`,
`[esp+4]`/`[esp+6]`), so on the direct path the recursion test reads the target. In the emulator, a direct calm walk needed no
recursion. The route finder's branch reads sea-route tables that the game loads at run time, and which the synthetic map
lacks: its waypoints there are not meaningful (the case is kept in the data with that label), and one case faulted.

## What this does not establish

- AI fleet recursion in play: no live hook on `FUN_0044e1fc` was run; its intermediate-path behaviour needs the game's
  loaded route tables.
- Human army paths beyond the two C4 walks, and AI army paths beyond two End turns from one start.
- The remake's crossed tiles: the remake side was compared at endpoints only.
- The fleet's distance-1 tail (disembark, city contact) was read in the decompile, not controlled.
- Native Windows behaviour.

## Evidence

- Army steps: `runs/experiments/data/run-exp-step-hook42/` (`c4-far-steps.jsonl`, `c4-near-steps.jsonl`, `ai-2-steps.jsonl`,
  `*-inert.json`, `ai-2-summary.txt`), release `run-exp-step-hook42`.
- Fleet controls and real-map search: `runs/experiments/data/run-exp-fleet42/`.
- Live fleet cases: `runs/experiments/data/run-exp-diff084-orders-b7/`. Saves `fleet-second-walk-88-32/original/a001.SAV` vs
  `…/remake/a001.SAV` (turn 0734), and the same for `87-47`.
