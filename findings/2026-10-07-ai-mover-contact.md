# AI-mover contact resolution: the mover onto an occupied tile (in-play corroboration)

**Status:** draft from `ic2-conquest`, awaiting promotion. Research pending request (2026-10-07,
from imperial-conquest-main via the research session): whether `FUN_0044d734`'s contact resolution
differs when the mover is AI. Wine-only.

**Tags.** `[derived]` = the decompile's reading (research repo, `docs/reports/2026-10-07-strategic-ai-turn.md`
and this experiment's own reads of the whole-application dump). `[confirmed]` = this run's saves
(bare filenames; SHA-256 in `runs/experiments/data/run-exp-ai-contact/SAVES.sha256`, binaries in
release `run-exp-ai-contact`, one tar.gz per batch).

## Answer (filled as batches land)

- placeholder

## Method

- **Environment.** A dedicated Wine prefix (`ic2-work-contact`), Xvfb `:601` and a copy of the game
  folder, so other sessions' games cannot interfere; the driver patch in this branch selects the
  game pid by its working directory (the first pgrep match could be another session's game).
- **The decompile read.** `FUN_0044d734` walks the mover to its destination and dispatches on the
  destination cell: an army band (200–247) calls `FUN_0044aee4` **only** when the nations are at war
  and the mover has moves left — otherwise nothing happens at all; a city (20–99) at war calls the
  siege `FUN_0044b27c`, not at war the resupply `FUN_0044f6d8`. The human twin
  `TUnitMap_MoveHumanArmy` calls the same `FUN_0044d734`. `FUN_0044aee4` is the instant resolution:
  it requires both nations' computer-seat flags, zeroes the mover's moves, transfers the loser's
  supplies and money to the winner, destroys the loser (army removed, news line) — no tactical
  battle screen on that path.
- **Batches.**
  - `b1` (control): fresh `new_game` seed 424242, Rome idle, one save per turn 0720–0732; must
    reproduce the ai-turn run's snapshots turn for turn (`control_vs_ai_turn.txt`). It re-collects
    the natural evidence: the AI-mover-vs-human-army contact of 0721→0722 and the Celtiberian
    sieges (`natural_evidence.txt`).
  - `b2`: extension of the same game past 0732, watching for a both-computer army contact (the
    instant `FUN_0044aee4` branch).
  - `b3` (human-mover control): the run-0 start (`BASE.SAV`), the proven join-and-march sequence
    to Gaul's army, then a MOVE (not the attack click) whose destination is the enemy army's tile;
    `humanmover_log.json` records position, popups, battle window and the army record around the
    contact.

## Observations

- placeholder

## Inferences

- placeholder

## What this does not establish

- placeholder

## Reproduction

```bash
source harness/env.sh   # with IC2_WORK=/home/diego/ic2-work-contact DISPLAY_IC2=:601 for a dedicated prefix
python3 runs/experiments/ai_contact/contact.py control 732
python3 runs/experiments/ai_contact/contact.py control 740 --resume
python3 runs/experiments/ai_contact/contact.py humanmover
python3 runs/experiments/ai_contact/compare_control.py
python3 runs/experiments/ai_contact/analyze_natural.py
python3 runs/experiments/ai_contact/archive_batch.py b1
```
