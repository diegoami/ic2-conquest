# The exchange hook (battles plan, B11): every `Random` draw of the tactical battle in order, an unchanged battle, and an exchange log that reproduces the decompiled formulas in 315 of 315 battles

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It is task **B11** of `docs/proposals/battles.md`
(`docs/tasks/battles-b11-hook.md`). Everything taken from the research session's decompile (`docs/reports/2026-10-04-decompiled-tactical-battle-rules.md`, read only) is tagged **[R-code]** and was checked against the game here,
never assumed. Data: `runs/experiments/data/run-exp-battle-hook/` (its `README.md` lists every file); saves, screenshots and raw hook buffers: release `run-exp-battle-hook` (one `.tar.gz` per batch, manifests tracked).
Levels as in B5: L1 staged cells from `FLD-RG` (synthetic, labelled) and the natural pair `MIX-RG`; the lab build with a baked seed (1-3).

**Answer.**
- **The hook is built and it observes only.** `patches/battle_lab.py <seed> --hook` re-points the 14 `Random` call sites of the battle module and TBattleOver to one cave that appends a 48-byte record (site, range, result, `RandSeed` before and after, half-round counter, side, battle flag, registers) to a 3 MB in-memory buffer (65,536 records; at capacity it sets an overflow flag and stops, it never wraps), puts a marker at the entry of the shot, melee and Rout routines, and takes boundary records at the battle start, at the write that clears the battle flag and just before the two instructions that reseed `RandSeed`. The harness reads the buffer through `/proc/<pid>/mem` after the battle.
- **Inert.** **322 of 322 hooked battles are byte-identical to the unhooked lab battle** of the same cell and seed: every `BATTLEnn.SAV` of the series (4,913 files) and the post-battle save. 319 of them were compared with the B5 sweep's recorded SHA-256 (all 315 B5 cells, seeds 1-3, plus the size-matrix cells; `inertness-*.json`) and 10 with an unhooked lab battle run in this task (`hi-hi-one` and `MIX-RG`, seeds 1-3). The unhooked lab exes rebuilt with the modified `battle_lab.py` are byte-identical to the B5 ones. The caves preserve every register, EFLAGS, ESP and the stack in 300 random machine states per cave under an x86 emulator (mutation-checked).
- **The log is complete.** In **321 of 322** hooked battles the overflow flag is clear and the seed chain is unbroken from the lab's seed at the battle start to the last draw: **0 breaks in 53,212 records** (at most 758 in a battle). The 322nd is the first hooked build, which could not pin the end (it had no reseed boundary yet); it is kept and superseded (`README.md`).
- **The decompiled formulas hold, exactly, on 315 B5 battles.** Replaying every shot, melee and Rout of each battle from the snapshots and the draws: **5,609 shots, 3,375 melees, 12,359 Rout tests**; the range `n` of every draw equals the report's formula in the replayed state (5,609 of 5,609 shots, 3,375 of 3,375 melees, 12,359 of 12,359 Rout tests have the predicted number of draws), the replayed troops, morale, shots and presence equal the next snapshot in **every slot of every half-round (0 differences)**, and **all 4,781 half-rounds' draws are accounted for** (no draw unexplained, none missing). So the exchange log has **no gap**: the 5,723 loss rows of the B5 diff are all explained exactly (B5 could attribute 2,682, 46.9 %, by inference).
- **Slot words 8 and 9 are what the report says** on the 315 B5 series: 3,119 of 3,119 mover slots' word 9 are adjacent (distance 1); both units' troops fall at the melee in 3,059, and in the other 60 an earlier melee of the half-round had already removed the target; word 8 (shots) only falls, only for types with shots (1,611 falls, 0 rises) and equals the markers' shot count slot by slot in 315 of 315 battles.
- **Surprises** (details below): the flag is cleared at `0x437B8C`, not at `0x45C21F`, in all 322 battles; the AI nation's +3 morale is visible in the copy-in draws (Gaul 68, Rome 65, both on Computer general); the TBattlePols reseed `0x457907` fires only when the Offer of peace box opens.

## Method

- **Build** (`patches/battle_hook.py`, applied by `battle_lab.py --hook` on top of the lab caves). *Refuses* unless: each of the 14 sites is `E8 rel32` to `Random` (`0x40284C`); a scan of the whole `CODE` section for every reference to `Random` (`E8`/`E9` rel32, `FF 15`/`FF 25`, any absolute dword; **53 found, all `E8`**) lists exactly those 14 inside the battle module and the TBattleOver unit (**39 are outside**: `b11-static-20261004-200058.json`); the bytes at the three routine entries, the two flag-clear writes and the two reseed writes are the ones recorded in the first build; no `rel32` branch of `CODE` lands inside a displaced range. `tests/test_battle_hook_build.py` has the refusal cases (a site that is `E9`, a wrong target, zeros, an unhooked 13th call inside the module or TBattleOver, an indirect reference, changed entry bytes, a branch into displaced bytes) and the log reader tests (it stops at the write index, reports the overflow flag, finds dropped, duplicated, wrong-seed and wrong-site records).
- **Module ranges.** The report lists the 12 + 2 sites but not the address ranges of `TBattleOver_InitializeForm/OK`. I derived them from the exe: the battle module is `0x436FB4` (`StartBattle`) to `0x43ADAB` (the last `ret` of its last function, `FUN_0043ABB4`, whose data follows); the TBattleOver unit is `0x458BC8` (the first code byte after the unit's published-method names, `InitializeForm`, `OK`) to `0x45958A` (the last `ret` before the next data). Both post-battle sites (`0x4592BD`, `0x45951C`) fall inside the second.
- **The cave** (`random`): switch to a private stack inside the control page, save flags and registers, write the record, restore, `call Random` with the caller's registers untouched, save, complete the record (result, `RandSeed` after), restore, `ret`. Markers and boundaries move the displaced instructions into their cave (7/7/5 bytes at the entries; 7 at the flag clear; 5 and 6 at the reseeds) and re-execute them. **Nothing is written to the program's stack below ESP** (the private stack), only to the hook's own control block and buffer. Tests: `tests/test_battle_hook_caves.py` (needs `unicorn`): for each cave, 300 random machine states (all registers, the arithmetic flags and DF, a random stack) are run once as the unhooked game runs and once through the cave; EAX-EDI, ESP, EFLAGS, `RandSeed`, the stack from ESP up and **every byte of memory below the control block** must be equal. Random cave 300, markers 3 x 300, flag-clear 2 x 200, reseed 2 x 200: all equal. A cave that does not restore EFLAGS is reported (`test_a_broken_cave_is_detected`). The run of all B11 tests and of the existing offline battle tests is `tests-b11-20261004-211824.txt` (all exit 0). The overflow path (capacity reached: flag set, nothing written past the end, `Random` still runs) and the seed cave are tested too. (An earlier design pushed on the program's stack; the emulator showed it left residue in the callee's uninitialised frame, so it was replaced by the private stack.)
- **Runs** (`b11_run.py`): one fresh process per battle, the same L1 staging as B5 (`FLD-RG` with the cell's edits; size-matrix cells `a-d-<size>-<size>` repeated from PR #40's `trials.py`, which is not in main yet) and `MIX-RG` (`FLD-RG` unedited: Rome's army 0 against Gaul's army 10, the B0 battle), both sides on Computer general, the Offer of peace box declined. Six private game folders and displays in parallel (7 rounds of 48); each worker kills only its own pids. Unhooked runs use `Imperial Conquest 2 lab s<seed>.exe`, hooked runs `... lab hook s<seed>.exe` (SHA-256: `EXES-sha256-20261004-195346.txt`).
- **Replay** (`b11_exchange.py`): the lab snapshot `BATTLEnn` is taken at the entry of the half-round end, **after the side's moves and shots and before its melee** [R-code, confirmed: the replay needs exactly that]; the records carry the half-round counter, so the records of counter *k* are the moves phase of half-round *k* (shots, Rout tests, flank draws), the melee marker, then its melee phase. The state at the next snapshot is replayed from the previous snapshot: the melee of *k* on `S_k` (the pairs from slot order and the snapshot's word 9; the four draws' ranges `nA, nA, nD, nD` confirm the pair), then the shots and Rout tests of *k+1* in record order (actor and target are the shot marker's EAX and EDX), and compared slot by slot with `S_{k+1}` (troops, morale, shots, presence). The Random results are facts; the formulas turn them into losses and morale. Nothing is averaged: every miss is a row in `exchange-check-<trial>.json`.

## Observations

### The call-site table (315 hooked B5 battles; `callsites-*.csv`)

| site | module | what the game does there [R-code] | battles | records | EAX (range) seen |
|---|---|---|---:|---:|---|
| `0x43801A` | TBattleMap | copy-in, attacker slots: `Random(q*4)` per live slot | 315 | 525 | 24 (q 6) |
| `0x43812F` | TBattleMap | copy-in, defender slots | 315 | 525 | 24 |
| `0x43820D` | TBattleMap | AI placement `Random(5)` (formation row) | 315 | 630 | 5 (2 per battle: both sides place by AI) |
| `0x438FFB` | TBattleMap | Rout test, first `Random(morale)` | 78 | 164 | 28-39 (the morale) |
| `0x439006` | TBattleMap | Rout test, second `Random(morale)` | 78 | 164 | 28-39 |
| `0x439188` | TBattleMap | shot, first `Random(n)` | 261 | 5,609 | 1-699 |
| `0x439191` | TBattleMap | shot, second `Random(n)` (loss = sum) | 261 | 5,609 | 1-699 |
| `0x439557` | TBattleMap | melee, attacker's first `Random(nA)` | 300 | 3,375 | 1-10,528 |
| `0x43955F` | TBattleMap | melee, attacker's second | 300 | 3,375 | 1-10,528 |
| `0x4395CE` | TBattleMap | melee, defender's first `Random(nD)` | 300 | 3,375 | 1-16,161 |
| `0x4395D8` | TBattleMap | melee, defender's second | 300 | 3,375 | 1-16,161 |
| `0x43AA88` | TBattleMap | flank step `Random(3)` | 14 | 19 | 3 |
| `0x4592BD` | TBattleOver_OK | promotion `Random(4)` per surviving winner unit | 315 | 535 | 4 |
| `0x45951C` | TBattleOver_OK | the peace test `Random(5)` | 182 | 182 | 5 |
| hooks | | `0x43910C` shot entry (EAX shooter, EDX target): 5,609; `0x4393EC` melee entry: 4,781 (one per half-round); `0x438FB0` Rout entry (EAX the slot): 12,359; flag clear `0x437B8C`: 315; flag clear `0x45C21F`: **0**; reseed `0x457907`: 75; reseed `0x450C7B`: **0** | | | |

The calling convention (range in EAX, result in EAX) holds: every Random record's result equals `(range * RandSeed_after) >> 32`, and `RandSeed_after = RandSeed_before * 0x08088405 + 1` (mod 2^32): 0 misses in 53,212 records (`chains-summary-*.json`). The disassembly context printed in `b11-static-*.json` is the 12 bytes before each site and is mis-synchronised for five of them (data in the instruction stream, or too few bytes to decode); the record check above is the evidence for the convention.

### Inertness (task Work 1 and 4; `inertness-*.json|csv`, `trials-b11.jsonl`)

| comparison | hooked battles | identical (series and post save) |
|---|---:|---:|
| `hi-hi-one` and `MIX-RG`, seeds 1-3, hooked vs unhooked lab exe of this task (rep 3) | 6 vs 6 | 6 of 6 (e.g. `hi-hi-one_s1_r3_hook` and `_plain`: 19 files, post `1043d0aa…`; `mix-rg_s3_r3`: 28 files, post `d7c6c303…`) |
| B5 re-run: 315 cells x seed, hooked vs the B5 rep-1 SHA-256 (`b5-baseline-*.json`, commit `7dea580` of PR #40) | 315 (314 + 1 stand-in) | **315 of 315** |
| all hooked trials, any rep, vs plain (10) or B5 (319) | 322 | **322 of 322**; 4,913 series files |

### Seed chain and boundaries (task Work 2; `hookcheck-<trial>.json`, `chains-*.csv`)

322 hooked battles, 53,212 records: overflow set 0, chain breaks **0**, every first record the battle-start boundary carrying the lab's seed, a recorded flag-clear in every battle, no reseed before it. The end is pinned by a **reseed record** (just before `RandSeed := a + b` at `0x457907`, which follows the last post-battle site; 79 battles, the Offer of peace box opened) or, in the other 242, by `RandSeed` read from memory after the battle's windows closed, equal to the last record's seed-after. In every battle with a reseed record the chain continues to it, so nothing is drawn between the last post-battle site and the reseed. One battle (the first hooked trial, an earlier build) fails the end pin by construction.

Live address checks (`b11-live-20261004-200346.json`, hooked seed 1, `ar-ar-one`): the battle flag is 0 before the attack and 1 in the open battle, **0 when the Battle ended box is first seen** and after `play_battle`; the header words at `0x4A0B74..0x4A0B7D` (attacker 0, defender 10, side 0, counter 2, y1 0) equal both `Game.battle_state()` and the Save As block (`B11_open.SAV`, block 12: the parsed block, header, 40 slots with names and the grid, is **equal field by field**); `RandSeed` in memory equals the last record's seed-after at the open battle; the flag-clear record is at `0x437B8C` (counter 16) and the reseed at `0x457907`.

### Draw order against the report (task Work 2; `exchange-check-<trial>.json`, `sweep-table-b11-*.csv`)

| draws | report's order [R-code] | observed in 315 battles |
|---|---|---|
| copy-in | `Random(q*4)` per live slot, attacker 0..19 then defender | count and range equal in 315 of 315; morale = clamp(draw + base, 60, 90) with base **65 (Rome)** and **68 (Gaul)** in all 315 staged battles (both armies saved at morale 65): the +3 of the AI nation shows although Rome is also on Computer general. (`MIX-RG`, the natural armies, gave bases 64 and 58: not interpreted here.) |
| placement | `Random(5)` per computer-controlled side | exactly 2 per battle (both half-rounds 1 and 2) |
| shot | 2 draws then Rout(target) | 5,609 x 2; `n` as predicted (the doubling for archers at distance 1 recognised by `n`) |
| melee | 4 draws then Rout(a), Rout(d) | 3,375 x 4; `nA, nA, nD, nD` exactly as predicted |
| Rout test | 2 draws only when troops >= floor and 20 < morale <= 39 | 12,359 tests: the draw count is the predicted one in all; 164 tests drew; 515 units removed (cascade included) |
| flank | `Random(3)` per flank | 19 draws in 14 battles; **observed only**: which unit flanks depends on the AI's moves inside the half-round, not on the snapshot |
| post-battle | `Random(4)` per surviving winner unit, then `Random(5)` | promotion draws = survivors in 315 of 315 (535; 146 are 0, a promotion); peace draw in 182 battles, **the Offer of peace box opened exactly when the draw was < 2 (76 of 76)** |

**Mismatches with the report's draw order: none.** The only item the snapshot cannot predict is the flank draw count.

### Slot words 8 and 9 (task Work 3 first check; `b11-semantics-20261004-200530.json`)

On the 315 B5 series (read-only from the main checkout's `artifacts/run-exp-battle-sweep/`): A 3,119 of 3,119 mover slots with a target are within Chebyshev distance 1 of it; B in 3,059 both troops fall between the snapshot and the next, in 60 the target had been removed by an earlier melee of the half-round (lower slot, same target; classified, 0 unexplained); C word 8 fell 1,611 times, never rose, and only for li/ar/lc. The hook adds: shot markers per slot = the ammo drop between the first and the last snapshot in 315 of 315 battles (`b11-entries-*.json`) and the melee marker count = the number of half-rounds in 315 of 315. Attribution therefore uses the snapshot's targets and the markers' arguments, and each is **confirmed** by the draws' ranges (`unconfirmed_exchanges`: 0).

### The exchange log and the sweep table (task Work 3 and 4; `sweep-table-b11-*.csv`, `sweep-table-b11-summary-*.json`)

| | B5 (diff only) | B11 (hook) |
|---|---:|---:|
| loss rows (a slot's troops fell between two snapshots), 315 battles | 5,723 | 5,723 |
| attributed with actor, kind and amount | 2,682 (**46.9 %**, "unambiguous") | **5,723 (100 %)** (replayed troops equal the snapshot) |
| exchanges rebuilt | | 5,609 shots + 3,375 melees (+ 12,359 Rout tests) |
| exchanges whose predicted `n` and loss the formulas reproduce | | **8,984 of 8,984** (0 misses, 0 state differences, 0 unaccounted draws) |

Per exchange a row has actor, target, types, `n`, the draws, the predicted loss and morale change; the observed loss is checked at the next snapshot, per slot, and per exchange where a unit is hit once in the window. Where a unit is hit several times in a window only the sum is observable, and the replay reproduces the sum.

## Inferences

- **The hook is an observer.** Its writes go to its own page; the program's stack and registers are as a direct call leaves them (emulator); and 322 hooked battles equal their unhooked counterparts byte for byte, which is what the plan needs before B5's action columns can use it. [D from the tests, O from the runs]
- **The report's formulas are right in every case the 315 battles reach**, including the melee matrix at DAT `0x1F7A6` (the `nA`/`nD` ranges depend on it; `b11-mutation-20261004-211750.json` changes one constant of the formulas at a time on real battles and the replay notices: M[hi][hi] 5 -> 6 makes 4 of the 63 melees of `mix-rg_s3_r3_hook` miss, vuln[li] 17 makes 37 of its 80 shots miss, a rout floor of 100 for hi gives 6 differences from the snapshots), the shot formula with its archer doubling, the cap `min(raw, 40 % of troops) + 1`, the morale rules (+2/-3 by the troop ratio, shot -min(3, 35 loss/(troops+1)), Rout cascade -6/+5), the Rout floor `std div 25` and the 20 < morale <= 39 test. The int32 wrap the report warns about was not needed to explain any melee. [D]
- **Which exchange hit whom is no longer inferred** in this lab: the B5 columns "actor", "kind" and the split of a loss between shooting and melee can be filled for every row from `exchanges-<trial>.jsonl`. The B5 target-choice tables are unchanged by this (they rank the enemy a unit's word 9 named in the snapshot).
- The AI general's *choices* (who it targets, where it moves) remain observed; the hook shows each effect, not the decision.

## What this does not establish

- **Wine only.** One build of the original under Wine 9.0 on Xvfb; the desktop original was not run. The lab reseed (`RandSeed := seed` at every battle start) is part of the lab build, so the draws seen are the lab's, not those of a natural game's seed history; what is established is the rule given the state, not the sequence a player would get.
- **The AI general's choices are observed, not decompiled here.** The hook records draws and routine entries; which unit the AI moves where, and why, is inferred from snapshots (B5), not from this task. The flank draw count is not predicted.
- The staged cells are synthetic (L1: uniform armies of one type, quality 6, morale 65); `MIX-RG` is the only natural pair, with three seeds. Terrain, sieges, the human order set and the instant resolver (AI v AI) are other tasks; the hook sees none of them.
- **Human play is not covered:** every battle ran with Computer general on both sides. A human-clicked shot or melee goes through the same routines, but this task did not exercise it.
- The module ranges of `TBattleOver_InitializeForm/OK` are derived from the exe (the report names the functions, not their ranges), and `0x45C21F` (the TPremierForm clean-up that also clears the flag) and `0x450C7B` (a second reseed) never fired in 322 battles: their caves are tested only in the emulator.
- The Offer of peace box is declined in every run; what follows a Yes is not logged. The hook ends at the reseed (or at the memory read): draws after the TBattlePols form are not recorded.
- A battle that ends in the moves phase (no melee marker in its last half-round) did not occur in the 315, so that path of the replay is untested on real data.

## Reproduction

```
IC2_WORK=~/ic2-work-b11 DISPLAY_IC2=:577 ...                       # a private game folder (copy of the prefix) and display are required
setup/build_lab_exes.sh --hook 1 2 3                                # hooked exes; SHA-256 -> runs/experiments/data/run-exp-battle-hook/EXES-sha256*.txt
python3 -m tests.test_battle_hook_build ; python3 -m tests.test_battle_exchange ; python3 -m tests.test_battle_hook_caves     # the last needs `pip install unicorn`
python3 runs/experiments/battles/b11_addresses.py static            # call-site table, scan, displaced bytes (needs capstone)
python3 runs/experiments/battles/b11_addresses.py live ar-ar-one 1  # header words, flag, seed, Save As
python3 runs/experiments/battles/b11_run.py run hook hi-hi-one mix-rg --seeds 1-3 --rep 3 ; ... run plain ...   # inertness batch
python3 runs/experiments/battles/b11_compare.py baseline ; python3 runs/experiments/battles/b11_batch.py plan
python3 runs/experiments/battles/b11_pipeline.py 1 7 --size 48 --workers 6      # the B5 re-run (rounds, replay, inertness, archive, push)
python3 runs/experiments/battles/b11_semantics.py ; b11_compare.py inertness ; b11_table.py ; b11_chains.py ; b11_callsites.py ; b11_aggregate.py
```
