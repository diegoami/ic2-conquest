# run-exp-diff084-tooling: harness self-checks and the first original-vs-remake toy run (#229)

Task: #229 (tracker #228). Approved by the owner in the Claude session on 2026-10-28 ("ok do it"), recorded on #229.
Tooling: [`difftest/`](../../../../difftest/README.md).

- Remake: tag **v0.8.4**, commit `d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`, read-only clone at `~/projects/ic2-remake-v084`,
  built with .NET SDK 10.0.401 into the ignored `artifacts/diff084-build/`. Ruleset `classical-faithful`, world
  `classical-mediterranean`, field battles with a human side resolved instantly.
- Original: `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…`), Wine 10.0, Xvfb 1280×1024, startup
  seed 12345. Every run's environment record is in its `receipt.jsonl`.
- Start save for every run: `~/ic2-work/fixtures/BASE.SAV` (Rome human, 270 BC Spring week 1; SHA-256 `050bc354…`).

## Results

| Check | Runs | Result |
|---|---|---|
| Import → export of the start save | every remake run, checkpoint `a000` vs `BASE.SAV` | **0 differences** in every compared field and map cell |
| Remake against itself, 5 turns | `self5-remake-1` vs `-2` | **0 differences** at all 10 checkpoints (`report-self5-remake`) |
| Original against itself, 5 turns, seed 12345 | `self5-original-1` vs `-2` | **0 differences** at all 10 checkpoints (`report-self5-original`) |
| Corrupted copies must be reported | `selfcheck-corrupt-remake-a004.json`, `selfcheck-corrupt-original-a004.json` | 6 single-field controls + 1 map cell reported exactly; the unchanged copy reports nothing |
| Original vs remake, 3 turns | `toy3b-original-1` vs `toy3b-remake-1` (`report-toy3b-original-vs-remake`) | our orders (tax 20, move, recruit 1,200 HI at Rome) give **identical states**; the first divergence is the first End turn (`a004`) |

### What the toy run shows

At `a004` (Spring week 3, 270 BC) 76 fields and 190 map cells differ. They are AI actions and their consequences:
seven AI armies and two fleets stand elsewhere; Bithynia, Celtiberia and Gaul queued different recruits (Gaul's
mobilization 50 vs 63, Celtiberia's 56 vs 73); the pending offer comes from Celtiberia in the original and from
Seleucid in the remake. The 48 city supply differences are all in the cities of those AI nations (Gaul 24,
Celtiberia 18, Bithynia 3, Galatia 3), most of them 1 or 2 tons less in the remake; this follows the different AI
recruitment, so it is not counted as a separate rule difference here. AI recruitment and diplomatic draws are the
known #176/#177 families; the remake's AI was given no recorded original draws in this run.

Rome's own state (treasury, recruits, armies, cities) is equal at `a004`. Comparing only the human nation's fields
after End turn, and matching AI draws, is the next step (#230, #232).

### Two harness corrections found by the runs (kept as evidence)

1. `self5-*` and `toy3-original-1` used `recruit` 1,000 HI. The driver's `recruit()` adds arrow clicks to the dialog's
   default, so the original recruited **2,200** (default 1,200 + 1,000) and `report-self5-original-vs-remake` diverges
   at `a003` because of our adapter, not the game. The adapter now reads the "New unit" amount by OCR, steps it to the
   target and reads it again (`difftest/original.py`, `recruit_exact`). The self-checks are unaffected (both runs of
   each pair used the same code).
2. `toy3-original-1` (with the corrected adapter) shows the original **cannot go below 1,200** heavy infantry: the
   dialog clamps to battalion/5 (`rules-specification.md`, "Amounts"). The remake's dialog clamps the same way, but its
   engine command `recruit-standing`, used by the CLI and this harness, accepts any positive amount and recruited
   1,000. Scripts must use amounts a player can set in both games; `toy3-rome-1200.jsonl` does. Whether the
   command layer should enforce the clamp is a question for the remake, not a gameplay difference.

## Files

Each run folder: `run.json` (inputs, hashes, pins), `receipt.jsonl` (every action with the game's reply), the remake's
`commands.txt` and `stderr.txt`, the original's `progress.json`. Checkpoint saves (`aNNN.SAV`) and the remake's native
saves (`aNNN.native`) stay out of git; their SHA-256 are in `SAVES.sha256` (SAV) and in each remake receipt
(`nativeSha256`). Reports: `report-*.json` and `report-*.txt` (the Markdown report, archived as .txt).

Published 2026-10-28 as release [`run-exp-diff084-tooling`](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-diff084-tooling):
`run-exp-diff084-tooling.tar.gz`, 1,865,432 bytes, SHA-256 `ddd8ad682b7412c230ef47b06060c32476609b958e6018544de7ae3b8a8e9f69`
(every run folder with its `aNNN.SAV` and `aNNN.native` checkpoints, receipts and reports).
