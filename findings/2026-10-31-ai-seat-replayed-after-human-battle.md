# An AI seat whose army fights the human's army is played twice in the original; the remake plays it once (Instant) or replays it from the pre-turn state (Tactical)

**Tag:** [confirmed: code and Wine hook]. Seed build in Wine; the five cases come from existing hook logs.
**Task:** found while rechecking remake main `e20a6488` for #174/#176 (owner request 2026-10-31).
**Remake compared:** main `e20a6488`.

## The original

`FUN_0044fa20` (one AI seat) runs diplomacy `FB7C`, economy `FFBC`, the armies `F31C` and the fleets `F608`, in that order
(0x44FA42–0x44FA51). The dispatcher `FUN_00451fdc` calls it in a loop.

- **The interrupt flag `DAT_004a0b7c`:**
  - Set to 1 by `FUN_00437de4`, which prepares the 20 battle slots and opens the battle through `FUN_00439968`.
  - Cleared by `FUN_00436434` when that battle ends.
- **`F31C`** handles each army only `if (DAT_004a0b7c == 0)` (decompile :52924). Once an army's attack has opened a battle,
  the seat's remaining armies are skipped: no supply pass and no decision.
- **`FA20`** still calls `F608` after `F31C`, so **the fleet phase runs**. It advances the seat index only when the flag is
  clear (0x44FA56), and the dispatcher's loop stops while the flag is set (0x451FED).
- **After the battle,** the dispatcher calls `FA20` again **for the same nation**:
  - diplomacy and economy run a second time;
  - every own army's supply pass `FUN_0044e41c` runs again;
  - the armies with moves left decide;
  - the fleet phase runs a second time.
- **The first pass is not undone.** Its economy, the armies up to the attack, and its fleet moves stay applied.

**Measured** (existing hook logs, 16 starts × 5 rounds, seed 12345): **5 seats ran twice**. Each has two economy budget
lines in `run-exp-econ/orig-v1` and a doubled supply pass in `run-exp-econ2/orig-v1`.

| Start, round | Seat | Checked |
|---|---|---|
| S01 r5 | Celtiberia | two budgets |
| S02 r4 | Bithynia | its army 11 attacks Seleucid's army 5, the human's (the Galatia battle of `2026-10-31-ai-rerun-remake-8e2d9053.md`) |
| S03 r1 | Seleucid | two budgets; one of the #176 "state" seats |
| S06 r2 | Rome | two budgets; one of the #176 "state" seats |
| S08 r2 | Carthage | its army 2 attacks Celtiberia's army 10, the human's (below) |

### S08 round 2, Carthage, in order

Hook logs `run-exp-routemoves159`, `run-exp-econ`, `run-exp-econ2`:

1. **First pass:**
   - budget: own 40,509, threat 30,008;
   - army 2's supply pass at (36,64);
   - army 2 attacks army 10 (`DBA8`, caller `f31c-army>100`);
   - army 3 is skipped;
   - **fleet phase: fleet 0 has no route and goes to its port**, (86,76) → (83,78), 26 → 23 moves.
2. **Second pass:**
   - budget: own 30,220, threat 15,000 (after the battle);
   - army 2's supply pass again, now at (35,63);
   - army 3's supply pass at (87,77), then its continuation (city > 85, 9 moves). Fleet 0 is now **2 tiles away**, so
     `D9A8` writes the route (86,77) instead of embarking the army;
   - the garrison fallback;
   - **fleet phase again: stored route (86,77)**.

In the remake (`e20a6488`) the seat runs once. Fleet 0 is still adjacent, so army-3's march embarks on it ("walks 0", the
army on the fleet's tile), and fleet 0 is idle. This is the S08 r2 row of the fleet-0 attribution (correction below).

## The remake

- **`HumanBattleMode.Instant`** (the CLI default, and every equal-state comparison so far): an AI attack on a human army is
  resolved at once, and the seat continues. There is no interruption and no second pass.
- **`HumanBattleMode.Tactical`** (the Godot UI): `AiPhaseBattleGate` **abandons** the seat's turn at the attack.
  `PlaySeatTurn` then replays the turn **from the same pre-turn state**, with the finished battle injected
  (`GameSession.cs`, `PlaySeatTurn` remarks). The result is one uninterrupted turn, not the original's
  partial-pass-plus-full-pass.

**For the remake (classical-faithful), both modes:**
- When an AI army's attack opens a battle with the human, keep the seat's effects so far.
- Skip the seat's remaining armies, and still run its fleet phase.
- After the battle, run the whole seat again on the current state: diplomacy, economy, every army's supply pass, the
  armies with moves left, and the fleet phase.

## What this does not establish

- **Battles other than an AI attack on the human's army:** sieges, naval battles, or a human attack during the human's
  own turn. Only the flag's setter is known; which of those reach it is not traced.
- **The unpatched original:** the seed build's instant-battle patch automates the battle, and the seat loop is the
  original's code, unchanged. The Windows original was not played.
- **How much the second pass changes:** in these 5 seats, economy orders, merges, hires and diplomacy are not tallied
  pass by pass.
- **Rounds 6+, other seeds.**

## Evidence

- Code (pinned seed build):
  - `FUN_0044fa20` 0x44FA20–0x44FA9D;
  - `FUN_00451fdc` 0x451FDC–0x452032;
  - `FUN_0044f31c` (decompile :52918–52924);
  - `FUN_00437de4` (:38173) and `FUN_00436434` (:37927) in `all_app_functions.txt`.
- Data:
  - `runs/experiments/data/run-exp-econ/orig-v1/*-econ.jsonl` (two budget records per replayed seat);
  - `runs/experiments/data/run-exp-econ2/orig-v1/*-econ2.jsonl` (doubled supply passes);
  - `runs/experiments/data/run-exp-routemoves159/orig-v1/S08_Celtiberia_AUTO0720-routemoves.jsonl` (seq 38–44);
  - the remake's replay `runs/experiments/data/run-exp-airerun-e20a/remake-e20a6488-v1/`.
- Saves: S08 r2 = `hooked-t01-AUTO0721.SAV` → `hooked-t02-AUTO0722.SAV` (S08_Celtiberia_AUTO0720; releases
  `run-exp-aidecide`, `run-exp-routemoves159`).
