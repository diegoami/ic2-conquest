# Late-year replays to 264 BC on remake v0.9.3; the original has no observer seat; an adapter mis-addressing after tombstones

**Tag:** [confirmed: anchored remake replays against stored original games; Wine runs of a patched build; Unicorn
emulation of the patch]. Wine only.
**Status:** draft for research.
**Task:** owner 2026-11-04: "play a game with all civilizations, and maybe play a couple of longer games", "5 games × 150
turns … save checkpoints", "we need to get to the later years"; "do we have an observation mode for this game? If not we
should add one".

Remake pin: `a44c42fc` (v0.9.3). Every replay below is anchored (`difftest/anchored.py`): each turn starts from the
original's own save, with turn seed 12345 + k (`--turn-seed 12345`). The "human" phase is the state after our orders and
before End turn; the "ai" phase is the state after End turn.

## 1. The first replays past 269 BC

Until now, every stored game stopped by 269 BC. Three long games now reach Summer 264 BC, all in `run-exp-longgames`,
played by rulebot-1 with the original only (`difftest/longgame.py`):
- **Carthage**, 150 turns: the game ends in Summer 264 BC.
- **Rome**, 47 turns: Gaul conquered Rome at turn 48 (Winter 269 BC). The End-of-Game text is in `summary.json`.
- **Rome, part 1 (`-h1`)**: from turn 48, the human seat was handed to Seleucid, the living nation with the most cities
  (`difftest/handover.py`; record in `rome-rulebot1-150t.handovers.jsonl`). It then ran 102 turns, to Spring 264 BC.

There are also eight new 40-turn games, one per civilisation not played before, in `run-exp-longrun-v093`. Seleucid
conquered Bithynia at turn 32 and Galatia at turn 24.

| game | turns | to | errors | ai fields (median / max) | human rows other than §2 |
|---|---|---|---|---|---|
| carthage-rulebot1-150t | 150 | Summer 264 BC | 0 | 16 / 333 | 4 |
| rome-rulebot1-150t | 47 | Winter 269 BC | 0 | 20 / 236 | 23 (siege draws, §2) |
| rome-rulebot1-150t-h1 (Seleucid) | 102 | Spring 264 BC | 0 | 11 / 293 | 0 |
| armenia, celtiberia, dacia, illyria, media, thracia (40t) | 40 each | Autumn 269 BC | 0 | 9.5–31.5 / 194–311 | 0–1 |
| bithynia-rulebot1-40t | 31 | Summer 269 BC | 1 (§3) | 20 / 320 | 8 |
| galatia-rulebot1-40t | 23 | Winter 270 BC | 0 | 15 / 184 | 7 |

**Results.**
- **No new failure class in late years.** None of the 2,548 replayed turns failed in the remake (exit, out of memory,
  segfault), apart from §3.
- **The AI phase stays in the same range.** The AI-phase differences in 266–264 BC have about the same median as in
  270–269 BC.
- **The AI phase is not attributed.** The differences have not been sorted into classes here; the classes already known
  (the cross-region stale word, capital defence with a pending human battle) are expected to recur.
- **The saves are kept.** The late saves of all three long games are in the save corpus (§5), so the next remake release
  can be checked in 264 BC without replaying from 270 BC.

## 2. Human-phase residuals: four normalisations on load or export, and siege draws

In the human phase, the remake has loaded the original's save and carried out our orders. Turns with no orders (for
example Carthage t128) still show the same four rows, so these rows come from the load and export, not from play.

| row | original (a) | remake (b) | where | note |
|---|---|---|---|---|
| `nations.<dead>.cities_count` | the count at elimination (4–5) | 0 | every turn after a nation falls: Bithynia, Galatia and Illyria (Carthage game); Bithynia, Numidia and Rome (h1) | The original does not clear `+0x44C` when a nation is eliminated. The information window reads this field (N04). |
| `pending_offer` with from = −1 | type 1 | type 0 | 127 of 150 Carthage turns, 83 of 102 h1 turns | With no offer, the type byte keeps its last value in the original. The remake writes 0. |
| `fleets.N.moves` of a fleet under construction | leftover moves (17–29) | 0 | 88 h1 turns, 36 Carthage turns | Already described: atlas residue (`2026-10-31-sav-export-record-lifecycle37.md`, §moves +0xC) and gate-2 policy §3, where the leftover survives launch. |
| `armies.N.moves` < 0 | −1 or −2 | 0 | Carthage t128 and t135, h1 t26, t80 and t97 | The remake's import report lists these armies under `ArmiesWithClampedMoves`, so the clamp is deliberate. |

- **The siege draws are expected.** The Rome rows `armies.N.units` (turns 2–12) are siege casualties that differ by a
  few men per unit. Our order there was `besiege`, which draws random numbers, and the turn seed is not the original's
  draw sequence.

**Question for research.** Does the original's round tick add a nation's moves to a negative value or replace it? If it
adds, the clamp gives the army 1–2 more moves on its next turn.

## 3. Our adapter mis-addresses orders after a tombstone record (harness defect, two turns)

**The error.** Bithynia t03 failed in the remake with `unresolved: Index was outside the bounds of the array` on
`move {army:11} 207 48` (`bithynia-rulebot1-40t/anchored-turnseed/t03/receipt.jsonl`).

**The cause.**
- In `t03-a00.SAV`, the original holds 12 army records, and record 0 is a tombstone (owner −1, 0 troops). This is the
  compaction residue of `2026-10-31-sav-export-record-lifecycle37.md`.
- The remake's importer skips that record (`SkippedArmies: [{Index: 0}]`) and imports 11 armies.
- `difftest/remake_adapter/Program.cs` resolves `{army:N}` as `state.Armies[N]`, so every record after a skipped one is
  off by one. Record 11 was off the end of the list.
- At t02 (tombstone at index 9), `{army:11}` resolved to `army-12`, Galatia's army. The remake rejected it ("belongs to
  'galatia', not 'bithynia'").

**The scope.** Across all 2,548 anchored turns (`run-exp-*/…/anchored*/t*/receipt.jsonl`), 100 turns had skipped records.
Only these two had an order that addressed a record after the skipped one. In both, the remake carried out none of our
orders, and no other army was moved. The Bithynia t02/t03 human-phase rows (8) are this defect, not a remake difference.

**The fix (ours, not the remake's).** Resolve `{army:N}` and `{fleet:N}` by original record index, mapping through the
import report's skipped indices, then re-run the two turns.

## 4. The original has no observer seat; a patched build adds one

**The original.** With no human seat, the original's dispatcher (`FUN_00451fdc`) asks `FUN_00449050` whether any seat is
human. When the answer is no, the game ends (research `2026-10-05-end-of-game-screens.md` §4). An all-AI game cannot run.

**The build.** `patches/observer_build.py` patches the seeded rollingsave exe into
`Imperial Conquest 2 fast rollingsave seed observer.exe`. It adds three stubs, all switched by one byte, OBS at
`0x565000`, which the harness sets after a load:
- **P1:** `FUN_00449050` answers 1.
- **P2:** after each AI seat (`FUN_0044fa20`), when the seat index wraps to 0 and no battle is pending, the round is
  complete. The stub then clears the pending offer (`0x49F008` = −1), calls the autosave cave, which writes `AUTOnnnn.SAV`
  and starts the turn, and returns.
- **P3:** End turn does not advance the seat, so seat 0's AI also plays.

Every human flag (`+0x490`) is 0, so every rule that treats humans differently follows its AI path. With OBS = 0, the
build behaves exactly like the seed build.

**Checks.**
- **Offline:** `tests/test_observer_build.py` makes byte checks and runs P1–P3 under Unicorn (5/5).
- **Wine, v1** (`run-exp-observer/wine-check-v1/result.json`): one autosave per round, every 11.7 s. A stale "Bithynia
  wants to trade with Illyria" box appeared at every pause. Clearing the offer in P2 fixed it.
- **Wine, v2:** two rounds with no texts.
- **Campaign:** `smoke-campaign-v1` ran two observer rounds through `difftest.campaign --observer`.

**The remake.** Given an original save with no human seat, the remake plays exactly one round of 16 seats per `end` and
stops (`remake-noseat-check-v1`). An all-AI original game can therefore be replayed anchored, turn by turn, like a human
one.

**Running now.** `runs/experiments/longgames/run_queue.sh` began Ptolemaic, observer, 150 turns, on 2026-11-04 at 19:42.
The queue goes on to Seleucid and Macedonia as observer games, then the same three nations under rulebot-2 (a defensive
bot: `difftest/bot2.py`, tests 8/8).

## 5. Save corpus

The release `ic2-save-corpus` holds 30 assets, mirrored to `gdrive:IC2/artifacts/save-corpus/`. It has packs every 25
turns for the long games, up to Summer 264 BC. The index is `runs/experiments/data/save-corpus/index.jsonl`, append-only.
`python3 -m difftest.save_corpus fetch` restores a pack, and `difftest/late_starts.py` lists the late start saves.

## Open

1. Fix the adapter's record mapping (§3) and re-run Bithynia t02–t03.
2. Research: the round tick on negative moves (§2); whether the stale dead-nation `cities_count` is shown anywhere.
3. Attribute the AI-phase differences in the late years (266–264 BC) by class.
4. The six queued 150-turn games (§4), their anchored replays and corpus packs.

## Evidence

- `runs/experiments/data/run-exp-longgames/{carthage-rulebot1-150t,rome-rulebot1-150t,rome-rulebot1-150t-h1}/`:
  `turns.jsonl`, `summary.json`, `anchored-turnseed/turns.jsonl`, `*.anchored-turnseed.log`, `*.handovers.jsonl`.
- `runs/experiments/data/run-exp-longrun-v093/*-rulebot1-40t/`, the same layout.
- `runs/experiments/data/run-exp-observer/{wine-check-v1,wine-check-v2,smoke-campaign-v1,remake-noseat-check-v1}/`.
- Saves, hashed in each folder's `SAVES.sha256`:
  - **Original games:** release `ic2-save-corpus` (packs every 25 turns) and `run-exp-longrun-v093`
    (`<nation>-rulebot1-40t-saves.tar.gz`, which include `bithynia-rulebot1-40t/original/t02-a00.SAV` and `t03-a00.SAV`
    for §3).
  - **Remake replays:** release `run-exp-longgames` (`<game>-anchored-saves.tar.gz`, including Carthage
    `anchored-turnseed/t128` for §2).
  - **Observer checks:** release `run-exp-observer` (`observer-saves.tar.gz`).
