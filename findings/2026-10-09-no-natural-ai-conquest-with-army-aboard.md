# No natural AI conquest of a nation with a loaded fleet in 11 idle seeds (334 end turns): only Carthage, Ptolemaic and Greece load fleets, and none of them falls; an idle Rome is conquered within 29-50 end turns

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Wine-only. A negative result for ic2-research's request (for the player), "natural AI conquest of a nation whose launched fleet carries an army", the open "natural pre-state" item of research `c288059`. The edited-pre-state result stands (`2026-10-09-elimination-removes-fleet-and-army-aboard.md`).

**Tag:** `[confirmed]` for what was observed. The absence is a sample, not a rule.

## Answer

- **Existing saves:** a scan of all 7,618 saves under `artifacts/`, `runs/`, `saves/` and `~/ic2-work` found **no natural case**:
  - the only AI conquest in them is "Seleucid conquers Galatia." (Galatia owned no fleet), already part of the shared history of most fixtures;
  - the only launched fleets with an army aboard are Carthage's early ones and the experiments' own edits.
- **Seeded idle runs:**
  - From `saves/run0-start-AUTO0720-seed12345.SAV` (Rome human, only ending turns), seeds 1-3 and 10-17: 11 seeds, 334 completed end turns, 0721 to 0769.
  - **Conquests seen in the news:** "Seleucid conquers Galatia." in 7 seeds, at 0731-0735 (Galatia had no army and no fleet in the save before), and, at the end of 8 seeds, **Rome itself** conquered (by Gaul ×4, Carthage ×2, Illyria ×2) at end turn 29 to 50. Rome never had a loaded fleet.
  - **Launched fleets with an army aboard:** only **Carthage** (all 11 seeds), **Ptolemaic** (3 seeds, 0745-0759) and **Greece** (1 seed, 0759), each carrying its own army. None of the three lost a city count near conquest in these runs.
  - **No case of an army of another nation aboard** a fleet.
- **For a natural case** one would need a nation that both launches a loaded fleet and is conquered: Carthage, Ptolemaic or Greece, or another nation late in the game. An idle human Rome ends the game too early for that. A longer game would need the human to survive, by playing it or by a stronger starting nation.

| Seed | End turns | Last turn | How it ended | Conquests (turn) | Loaded fleets seen (owner: turns) |
|---:|---:|---:|---|---|---|
| 1 | 3 | 0723 | trial | – | Carthage 0723 |
| 2 | 28 | 0748 | stuck: Offer of peace (fixed in `2ad4ebb`) | Galatia 0735 | Carthage 0723-0724 |
| 3 | 6 | 0726 | stopped for the fix | – | Carthage 0726 |
| 10 | 49 | 0769 | End of Game: Rome conquered by Illyria (stuck before `cee96e0`) | Galatia 0734 | Carthage 0723-0762 |
| 11 | 29 | 0749 | End of Game: Rome conquered by Carthage (stuck before `cee96e0`) | Galatia 0735 | Carthage 0730-0732 |
| 12 | 44 | 0764 | Rome conquered by Gaul | Galatia 0731 | Carthage 0723-0764 |
| 13 | 28 | 0748 | Rome conquered by Gaul | Galatia 0735 | Carthage 0726-0737 |
| 14 | 39 | 0759 | Rome conquered by Gaul | – | Carthage, Ptolemaic 0758-0759, Greece 0759 |
| 15 | 37 | 0757 | Rome conquered by Illyria | – | Carthage, Ptolemaic 0745-0756 |
| 16 | 30 | 0750 | Rome conquered by Carthage | – | Carthage 0730-0732 |
| 17 | 41 | 0761 | Rome conquered by Gaul | Galatia 0731 | Carthage, Ptolemaic 0751-0758 |

## Harness fixes made on the way

- **`end_turn` answers the post-battle "Offer of peace" box** (`2ad4ebb`, default No, verified). An AI army attacking the human's opened it and blocked until the timeout.
- **`end_turn` raises `GameOver(text)`** on the "End of Game" window (`cee96e0`). Seen working live in seeds 12-17.

Both are in `tests/results.md`.

## Evidence

- **Data:** `runs/experiments/data/run-exp-ai-conquest-aboard/`: `idle_watch.py`, `idle_watch_seed<k>.jsonl` (one line per end turn: loaded fleets, new conquest lines, cities per owner), `idle_summary.json` (`summarise.py`), `idle_watch.log`, `SAVES.sha256`.
- **Release** `run-exp-ai-conquest-aboard`: every autosave with a loaded fleet or a new conquest line (`IW_seed<k>_<end>_<turn>.SAV`), and the `STUCK_*` / `GAMEOVER_*` screenshots.
- **The existing-save scan** was a one-off read with no saved output. Its result is stated above and can be redone with the same test: launched fleets with `+22 >= 0` and news lines matching "X conquers Y".

## Not established

- Any natural case. The cleanup on conquest is established only with the edited pre-state (`c288059`) and in code.
- A defection elimination (`FUN_0044BED8`) in play.
