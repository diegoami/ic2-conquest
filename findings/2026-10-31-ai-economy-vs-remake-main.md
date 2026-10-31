# AI economy, original vs remake main: one port gap (the order city is chosen once per turn); budgets, deployments, counts and tax match

**Tag:** [confirmed]. The original's own hook was compared with remake main's decisions on the same states (1,200
seat-turns), and the one difference was checked with a scratch patch.
**Task:** conquest #176 (strategic fidelity: economic budgets, recruitment and automatic supply decisions), owner request
2026-10-31.
**Remake compared:** main `05b02936`, not released.
**Method:** the same as `2026-10-30-ai-decisions-vs-remake-main.md` and `2026-10-30-ai-diplomacy-vs-remake-main.md`.

## Method

- **Original:** `patches/econ_hook.py`, an observation-only build with four probes in the economy phase
  `FUN_0044ffbc` and its recruiting routine `FUN_004504f4`:
  1. **0x45011E:** the own and threat sums at their comparison, with treasury, unity, mobilization and tax.
  2. **0x4501D6:** the nation after recruiting and the week-11 tax policy, before the fleet build.
  3. **0x4502D9:** each new order `FUN_004501f4` writes (entry, type, troops, city).
  4. **0x44A4E0:** each ready queue entry deployed by `FUN_0044a4e0`, with its caller.
  - Runs: 16 New Game starts × 5 End turns, seed 12345. The hooked autosaves are **byte-identical to the plain build
    in 80 of 80 turns**, and the same files as the army and diplomacy runs.
- **Remake:** the same rounds replayed from those autosaves (the diplomacy run's logs, `run-exp-diplo/remake-05b02936-v1`):
  - `faithful economy: threat T, own O`;
  - `mobilize recruitment slot N`;
  - `faithful order k: TYPE N troops at CITY`;
  - `week W: tax a -> b`.
- **Comparison** (`runs/experiments/econ/compare.py`), per seat:
  - **Budget:** own and threat. If they differ, the state already differs and the seat counts as "state".
  - **Deployments:** the set of queue entries.
  - **Order city:** compared as a set per seat.
  - **Order count:** the types and troops are `Random` draws, so the count is checked by replaying `FUN_004504f4`'s own
    stopping rule on **each side's own draws**, with the original's inputs:
    - inputs: the deficit, the queue's value in the round-start save, treasury, wealth, mobilization;
    - place while `k < 8`, value < deficit, mobilization < 100, and (treasury > −wealth/500 or `k < 3`);
    - each order adds `(troops/100)·weight` to the value, takes `(troops/200)·price` from the treasury, and sets
      mobilization to `min(100, mob + troops·1000/wealth + 1)`;
    - checked by hand on BASE: Bithynia's 5 orders reproduce its treasury 550 → −895 exactly.
  - **Tax:** the week-11 change.

## Result: 1,200 seat-turns

| | Seats |
|---|---|
| **same**: budget, deployments, order city, both order counts consistent with the rule, tax | **1,055** |
| state: the budget already differs (earlier battles or diplomacy in the round) | 141 |
| **differs** | **4**, all the order city |

Item by item, over the 1,059 seats with equal budgets:
- **deployments:** 1,059 / 1,059;
- **order city:** 1,055 / 1,059;
- **orders:** 265 seats placed them, and **both games' counts follow the original's stopping rule in 265 / 265**;
  794 seats placed none in either game;
- **week-11 tax:** **113 / 113**.

## The port gap: the order city is chosen once per turn in the original

- **Original:** `FUN_004504f4` calls `FUN_004502e0(&local_26)` **once**, before its order loop, and passes `local_26` to
  every `FUN_004501f4(entry, local_26)`. All of a turn's orders go to one city.
- **Remake:** `AiFaithfulEconomy` calls `ChooseCity(state, ruleset, nation)` **inside** the loop, on the state after the
  previous order. `FUN_004502e0`'s rule includes "more than a third of the queued orders are already at the capital",
  so the choice can flip mid-turn.
- **In play:** 4 seats.

  | Start, round, nation | Original | Remake main |
  |---|---|---|
  | S03 r2 Seleucid | 2 orders, Antioch | 3 orders: Antioch, record 206, record 246 |
  | S05 r1 Ptolemaic | 4 orders, Masada | 7 orders, one of them at record 214 |
  | S06 r4 Rome | 8 orders, Rome | 7 orders, one at Luceria (110) |
  | S13 r4 Rome | 8 orders, Luceria | 8 orders, two at Rome (85) |

- **Patch check** (`eco-city-once.patch.txt`: one `ChooseCity` before the loop, reused for every order): in those 4
  rounds every nation's orders go to one city, the original's (Antioch, Masada, Rome, Luceria).

## What this does not establish

- **Random draws:** the unit types and troop sizes (`Random(100)` buckets, `Random(size·4/5)`) are draws. Only their
  consequences (the counts) were checked, not the draws.
- **`FUN_004502e0`'s own branches** were not compared one by one: equal cities in 1,055 seats exercise the default and
  whatever branches those states reached.
- **The rest of the phase:** consolidation (`FUN_00450858`), merging (`FUN_004509f0`), `FUN_00450b30`, and the army
  phase's supply pass (`FUN_0044e41c`) and mercenary hire. The remake logs them, but they were not hooked in the
  original here.
- **Rounds 6+, other seeds.**

## Evidence

- Data: `runs/experiments/data/run-exp-econ/`:
  - `orig-v1/`: hook logs and inert checks;
  - `report-v1.json`;
  - `remake-cityonce-v1/`: the patch check;
  - `eco-city-once.patch.txt`;
  - `smoke/`: BASE.
- Release `run-exp-econ` (`econ-saves.tar.xz`, 162 saves; hashes in `SAVES.sha256`).
- Saves cited: starts `S00_Rome_AUTO0720.SAV` … `S15_thracia_AUTO0720.SAV`, with the round starts `hooked-tNN-*.SAV`.
- Code:
  - `patches/econ_hook.py`, `difftest/probes/econ_hook_run.py`;
  - `runs/experiments/econ/compare.py`.
