# Faithful AI: the remake's Tactical retained pass replays an interrupted AI seat like the original (5 of 5 seats); Instant play has no replay and differs in 3 of 5 (audit #195, X3)

**Tag:** [confirmed: remake replays of the original's round-start saves against the original's hook logs and end saves].
Remake only; the original side is the hook runs of 2026-10-31. No new Wine run.
**Status:** draft for research.
**Task:** research #195, cross-cutting difference X3 (a seat replayed after a human battle) in
`findings/2026-11-04-ai-audit195-inventory.md`, pass-1 step 5: "Replay the five seats the original replayed under the
remake's Tactical retained pass, and compare the second pass's draws, routes and economy". Until now the remake had never
been measured end to end on this path, because every anchored replay runs Instant.

Remake pin: **v0.9.4** = `168dbc04`. Ruleset `classical-faithful`.

## The original (recap of `2026-10-31-ai-seat-replayed-after-human-battle.md`)

When an AI army's attack opens a battle with the human's army, the battle flag `0x4A0B7C` stops `F31C`: the seat's
remaining armies are skipped, and the fleet phase still runs. After the battle, `FA20` runs the same seat again on the
current state: diplomacy, the economy, every army's support pass, the armies with moves left, and the fleets. Five seats
did this in 16 starts × 5 rounds (seed 12345): S01 r5 Celtiberia, S02 r4 Bithynia, S03 r1 Seleucid, S06 r2 Rome and S08 r2
Carthage.

## Method

`runs/experiments/audit195/x3_seat_replay.py` plays each seat's round on the remake from the original's round-start save
(`hooked-t0(r−1)` of `run-exp-aidecide`, or the S03 start save):
- the human gives no orders, as in the hook runs;
- modes Instant and Tactical, seeds 12345, 99 and 7;
- a battle that opens on the board is fought by the computer general for the human (`battle general on`, which plays
  it to the end).

**Adapter change (ours).** `difftest/remake_adapter/Program.cs` gains an opt-in `ailog` option. It subscribes to
`GameSession.EventsPublished` and writes each `AiTurnDecided` (one per AI pass: orders issued and the AI's own log
lines) to the receipt. Without the option, the adapter behaves as before. It was built into a separate folder,
`diffpin-168dbc04-ailog-build`, so the queue's 168dbc04 build is untouched.

**Comparisons.**
- `passes.jsonl`: the replayed seat's passes, against the original's two budget records per seat (`run-exp-econ/orig-v1`).
- `x3_positions.py`: the seat nation's army and fleet tiles at the end of the round, against the hook run's next save
  (`positions.jsonl`). Troops are ignored, because the battle is resolved differently.

## Results

**1. Structure.** In all 15 Tactical runs the seat runs **two passes**; in all 15 Instant runs it runs **one**. In
Tactical, pass 1 ends with "army phase interrupted; retaining the fleet pass", then runs the support/hire and fleet
phases. Pass 2 runs the Faithful economy again, the armies with moves left and the fleet phase.

**2. The economy, per pass** (own, threat; original from the hook, remake from "faithful economy: threat T, own O"):

| seat | original pass 1 | remake pass 1 (3 seeds) | original pass 2 | remake pass 2 (s12345 / s99 / s7) |
|---|---|---|---|---|
| S01 r5 Celtiberia | 14,973 / 42,027 | identical | 0 / 32,514 | 0 / 33,837; 0 / 32,451; 0 / 30,561 |
| S02 r4 Bithynia | 24,290 / 45,836 | identical | 9,638 / 41,216 | 9,638 / 37,784; 11,018 / 31,448; 9,638 / 38,444 |
| S03 r1 Seleucid | 30,836 / 96,707 | identical | 27,721 / 84,431 | 26,247; 27,855; 27,453 / 84,431 |
| S06 r2 Rome | 33,530 / 30,990 | identical | 28,361 / 15,000 | 26,171; 28,580; 27,558 / 15,000 |
| S08 r2 Carthage | 40,509 / 30,008 | identical | 30,220 / 15,000 | 29,590 / 15,000; 23,290 / 17,546; 28,470 / 15,000 |

- **Pass 1 matches exactly** in all 15 runs.
- **Pass 2 has the same shape:** the economy runs again on the state after the battle. Its values differ by the battle's
  casualties, because the remake's tactical battle is not the seed build's instant battle (S08 s99 and S02 s99 even have
  the other winner).

**3. End tiles of the seat's units** (`positions.jsonl`):

| seat | Tactical (s12345 / s99 / s7) | Instant (all 3 seeds) |
|---|---|---|
| S01 r5 Celtiberia | match / match / match | match |
| S02 r4 Bithynia | match / **army 11 survives** / match | **army 11 survives** at (173,48) |
| S03 r1 Seleucid | match / match / match | army 5 at (178,47); the original has (178,48) |
| S06 r2 Rome | match / match / match | army 0 stays at (94,29). In the original's second pass it joins army 1 at (105,39) (35,190; Tactical 33,013) |
| S08 r2 Carthage | match / **army 2 destroyed** / match | army 3 embarks at (86,76) and fleet 0 stays; the original has army 3 at (88,79) and fleet 0 on its stored route at (86,77) |

- **Tactical** matches the original's end tiles in 13 of 15 runs. The 2 misses are battles won by the other side
  (S02 s99, S08 s99), not the seat replay.
- **Instant** matches in 3 of 15 runs (S01 r5 only).
  - In S03, S06 and S08 (all seeds), it misses what the original's second pass does: army 5's step, army 0's join, and
    army 3's march with fleet 0's route. In S08, Tactical reproduces the original's traced sequence: pass 1 sends fleet 0
    to port, then pass 2 writes the route (86,77) and the fleet takes it with 20 moves left.
  - S02's Instant row is the battle's outcome, not the replay: Bithynia's army 11 (32,800) is destroyed in the seed
    build's instant battle and survives the remake's (20,802). The seed build's instant battle is the fixtures' patch,
    not an original rule, so this is noted for X6 and not claimed.

**4. Diplomacy draws (E18, A13): not observable here.**
- None of the 30 runs logs a war, alliance or peace roll in either pass.
- One trade swap (S08 s99, Greece for Rome) is chosen in pass 1 in Instant and in pass 2 in Tactical. The interrupted
  pass 1 never reached the diplomacy candidate in the scored loop. The end state is the same in both modes. The original
  did not swap in this seat, and neither did the remake's other seeds, so the swap is a draw.
- The question "does pass 2 draw fresh (original) or repeat pass 1's named streams (remake)?" therefore stays
  **UNAUD**. It needs a seat where a war or alliance roll fires in pass 1.

**5. Capital defence while the battle is pending.**
- In S03 and S06 the attack is capital defence's own (army-4 → army-6; army-0 → army-9). In Tactical, pass 1 then logs a
  second capital-defence move (army-5 / army-1 toward the threat). That is T277's `continuePending` (#1741), and it does
  not show in Instant.
- Both seats' Tactical end tiles match the original.

## What this settles and what it does not

- **Narrowed at intake (research PR #210):** "in state" means the end tiles of the seat nation's units only (troops
  ignored; pass 2's budgets differ by casualties), and the two Tactical misses are attributed to the battle outcome by
  inference from which army survives, not traced in the receipts.
- **The remake's Tactical path matches the original's seat replay in state:** 5 of 5 seats wherever the battle ends as in
  the original, with pass 1's economy identical and a second economy pass. Rows A12, B33, C02, D30 and F34 move from
  AMB toward **MATCH (Tactical, iv)**.
- **Instant and headless play have no replay.** That is the CLI, every anchored replay, and every observer game
  (`UsesAiPhaseBattleGate` needs Tactical, a living human and no watch mode; research PR #206). Their seats differ from
  the original wherever the second pass would have moved something (3 of 5 here). This is the same gate as X2.
- **Candidate remake fix (as for X2):** in Faithful, interrupt and replay the seat when an AI attack on the human's army
  opens a battle, whatever the battle mode. For Instant, resolve the battle at the interruption point and then run the
  second pass.
- **Not settled:**
  - E18/A13, the fresh draws in pass 2 (see 4);
  - D19, a stored route that survives into pass 2 in a seat where pass 1 already stored one (S08's route is written in
    pass 2);
  - battles other than an AI attack on the human's army.

## Evidence

- `runs/experiments/data/run-exp-audit195/x3-seat-replay-v1/`: `passes.jsonl` (30 runs), `positions.jsonl`, and per run
  `commands.txt`, `receipt.jsonl` (with the `ai` pass records) and `stderr.txt`; hashes in `SAVES.sha256`.
- Saves:
  - **Remake:** release `run-exp-audit195`, `audit195-x3-saves.tar.gz` (SHA-256 `a8c2087a7a1b9d45…`).
  - **Original round starts and ends:** releases `run-exp-aidecide` (`aidecide-saves.tar.xz`: `hooked-t0N-AUTO072N.SAV` of S01, S02, S06 and
    S08) and `run-exp-civ-sweep` (`S03_Ptolemaic_AUTO0720.SAV`).
- Original hook logs: `runs/experiments/data/run-exp-econ/orig-v1/*-econ.jsonl`.
- Tooling: `runs/experiments/audit195/x3_seat_replay.py`, `x3_positions.py`; `difftest/remake_adapter/Program.cs`
  (`ailog`).
