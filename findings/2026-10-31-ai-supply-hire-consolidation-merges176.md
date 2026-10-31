# AI supply and hire pass, consolidation and merges, original vs remake main: 1,192 of 1,200 seats identical; a new gap in when the post-battle peace treaty takes effect

**Tag:** [confirmed]. The original's own hook was compared with remake main's decisions on the same states (1,200
seat-turns). Each of the 8 differing seats is attributed, using two diagnostic remake builds and the original's saves.
**Task:** conquest #176, the rest (owner request 2026-10-31, "ok do 176"). It follows
`2026-10-31-ai-economy-vs-remake-main.md` (budgets, recruitment, tax).
**Remake compared:** main `8e2d9053`, not released.

## Method

- **Original:** `patches/econ2_hook.py`, an observation-only build with eight probes:
  - the army phase's supply and hire pass `FUN_0044e41c`: entry, each `FUN_0044f6d8` city transfer, each hire, and exit;
  - slot removal `FUN_0044ac3c` (consolidation joins and disbands, and merge slot moves) and slot move `FUN_0044acb4`;
  - fleet deletion `FUN_0044ad38` (the fleet merge);
  - fleet order `FUN_0044a004`;
  - each with its caller.

  It ran 16 New Game starts × 5 End turns, seed 12345 (the starts of every earlier comparison). The hooked autosaves are
  **byte-identical to the plain build in 80 of 80 turns**.
- **Remake:** the same 80 rounds, from the original's autosaves (`run-exp-airerun/remake-8e2d9053-v1`), using its AI log:
  - `resupply: N army transfers, …, T tons, P talents`;
  - `mercenary hire: N offer(s) hired across M army/armies`;
  - `faithful consolidate: joined|disbanded`;
  - `faithful merge: army|fleet`;
  - `faithful fleet order`.
- **Comparison** (`runs/experiments/econ2/compare.py`), per seat:
  - **transfers:** `FUN_0044f6d8` calls that changed the army (the remake counts a visit that changed anything,
    `AiResupplyPass.Declines`), the tons added, and the talents paid at foreign cities (owner from the round-start save);
  - **hires:** offers taken, and the armies that took one;
  - **consolidation:** joins and disbands;
  - **merges:** army and fleet merges;
  - **fleet orders.**

## Result: 1,200 seat-turns

| | Seats |
|---|---|
| **same on every item** | **1,192** |
| differs | 8: 5 state, 2 army order, 1 treaty timing (below) |

What the 80 rounds exercised in the original:

| Item | Count | Seats where the item matches |
|---|---|---|
| supply transfers | 826 (50,184 tons, 171 talents paid) | 1,197 / 1,200 (talents 1,200) |
| mercenary hires | 22 | 1,199 |
| consolidation joins | 54 | 1,198 |
| consolidation disbands | 16 | 1,200 |
| army merges | 18 | 1,199 |
| fleet merges, fleet orders | **0** (none in either game) | not exercised |

## The 8 seats

| Seat | Item | Cause |
|---|---|---|
| S01 r3 Seleucid, S03 r1 Seleucid, S06 r2 Rome, S09 r5 Media, S14 r3 Seleucid | joins, transfers, a merge, tons | **State.** The seat's budget (own and threat) already differs on 8e2d9053, from earlier differences in the round. |
| S05 r1 Seleucid, S09 r1 Seleucid | transfers and tons (original 1 transfer / 121 tons; remake 2 / 272) | **The army order gap** (`2026-10-31-army-order-within-a-seat.md`). See below. |
| S10 r2 Rome | hires (original 1, remake 0) | **New gap: when the post-battle peace treaty takes effect.** See below. |

### S05/S09 r1: downstream of the army order

- **Original:** Ptolemaic's army 6 (table index 6) decides before army 7. Army 7 is still within 10 of the capital, so
  army 6's garrison fallback (`FUN_0044ebe8`) takes the nearest-city branch.
  - Army 6 is gone after the round.
  - Seleucid's army 4 reaches its supply pass with **+600 money** (army 6's purse after its own pass) and +72 tons.
  - Army 4 then needs nothing from the four cities around it, so the original makes 1 transfer.
- **Remake `8e2d9053`:**
  - Army-7 scores higher and moves first, so army-6 marches on the capital (190,94).
  - Seleucid's army-4 reaches the pass with the round-start 300 supplies and 100 money (`remake-e41c-diag-v1`), and
    takes 151 tons. 151 = 451 − 300, its troops/100 minus its supplies.
- **Table-order diagnostic** (`remake-order-diag-v2` of run-exp-fleetroute174): both seats match. The comparison against
  it has 1,194 same seats (`report-order-diag-v1.json`).

### S10 r2 Rome: the remake applies the post-battle treaty at the seat's end

- **Original:**
  - Rome and Gaul are at war at round start (relation 3, `hooked-t01-AUTO0721.SAV` of S10).
  - Rome's capital defence (`FUN_0044efc8`, before the army loop) marches army 0 to (97,31). There it attacks Gaul's army
    9 on arrival and destroys it. `FUN_00450c68`'s treaty follows the AI–AI battle.
  - Then army 0's supply pass **hires offer 14** at Felsina (98,31), a Gaul city: 4,257 troops, mercenary label 37.
    `FUN_0044e41c` skips any city whose owner is at relation 3 with the nation, so **the war had already ended when
    the pass ran**.
  - Round end: army 9 is gone, and army 0 has 22,989 troops (23,700 + 4,257 − the battle's losses).
- **Remake:** the same capital-defence attack, the same battle, and the same `PeaceTreatyTriggered`. Diagnostic
  `remake-e41c-diag-v2` at the hire:

  `hire-gate rome army-0 city felsina owner gaul: moneyGate True atWar True freeSlot True inRadius True warWithOwner True`

  So **no hire**. The treaty is applied by `PeaceTreatySystem`, registered at `TurnPhase.SeatEnd`, after the whole seat.
  The relation after the round is the same in both games (−18).
- **For the remake (classical-faithful):** apply the post-battle treaty immediately after the AI–AI battle that triggers
  it, as `FUN_00450c68` runs. The rest of the seat should then see the peace: the hire gate here, and also later armies'
  targets and war candidates. This was observed once in 80 rounds; how often it changes a decision elsewhere is not
  measured.

## Also measured, and not compared

- **Own-city purse moves** (`FUN_0044f6d8`): the army's purse is capped at 1,000, with the excess going to the treasury,
  and topped up by 500 from the treasury when below 500. They are in the original's logs (`own_purse` in the report);
  the remake does not log them.
- **The consolidation's slot numbers:** the original logs the removed slot; the remake's line names another slot (S05 r1
  Seleucid: original slots 7 and 10, remake "slot 6" and "slot 9"). Only the counts are compared.

## What this does not establish

- **Fleet merges and fleet orders:** none occurred in these 80 rounds in either game.
- **The hire's mercenary label and troops per hire:** compared only as counts per seat.
- **A remake build with the treaty applied immediately:** not made. The original's timing follows from the hire under
  a round-start war, and the remake's from its diagnostic and its code.
- **Rounds 6+, other seeds.**

## Evidence

- Data: `runs/experiments/data/run-exp-econ2/`:
  - `orig-v1/`: hook logs and the inert checks;
  - `smoke/`;
  - `report-v1.json`, `report-order-diag-v1.json`;
  - `remake-e41c-diag-v1/` (each army at its supply pass, all 80 rounds), `remake-e41c-diag-v2/` (S10 r2, the hire
    gates);
  - `e41c-diag*.patch.txt`: scratch patches of 8e2d9053, never pushed;
  - `README.md`.
- Release `run-exp-econ2` (`econ2-saves.tar.xz`; hashes in `SAVES.sha256`).
- Saves cited: starts `S00_Rome_AUTO0720.SAV` … `S15_thracia_AUTO0720.SAV`, and the round starts `hooked-tNN-*.SAV`:
  - S10 r2 = `hooked-t01-AUTO0721.SAV`, its end `hooked-t02-AUTO0722.SAV`;
  - S05/S09 r1 = the starts.
- Code:
  - `patches/econ2_hook.py`;
  - `difftest/probes/fleetphase_hook_run.py` (`IC2_FLEET_HOOK=econ2_hook IC2_HOOK_LOG=econ2`);
  - `runs/experiments/econ2/compare.py`.
