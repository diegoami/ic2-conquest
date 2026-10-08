# A sunk fleet's tile becomes plain sea (0), even on rough sea; a fleet that sails away restores its tile

**Status:** a draft from `ic2-conquest`, awaiting promotion. It settles the open item of `2026-10-08-naval-battle-loser-clears-its-tile.md` (research `0389684`): "cleared to 0" or "covered terrain restored".

**Tag:** `[confirmed]` for the observed behaviour. `[derived]` for its consequence on the map.

## Answer

- **Battle loss: cleared to 0.**
  - **Setup:** the losing fleet's covered-cell field (+24) was set to **1** (rough sea).
  - **After:** its tile reads **0** in the save and in memory.
  - **Unpatched control** (covered cell 0): also 0.
  - **Same battle both times:** seed 12345, the fixture of `run-exp-naval-battle`. Carthage sinks Ptolemaic's fleet and keeps 80 ships; the news line "Carthage sinks fleet of Ptolemaic." appears in both.
- **Sailing away: restored.** With the same covered cell **1**, Ptolemaic's fleet sailed from (111,73) to (111,74). The old tile went back to **1** and the fleet's marker moved to (111,74) as 335. So the game does use the covered-cell field when a fleet leaves a tile; tombstoning a fleet (`FUN_0044ad38`, research reading) writes 0 instead.
- **Consequence (`[derived]`):** a fleet sunk on a rough-sea tile turns that tile into plain sea. The map word is the only store of the tile's terrain once a marker covers it, so the change is permanent: rough sea costs 3 moves per tile, sea 1 (`docs/rules-digest.md`). The same would apply to any covered terrain under a sunk fleet.

| Case | Loser's covered cell before | Order | Word at (111,73) after | Save = memory |
|---|---:|---|---:|---|
| cover0 | 0 | attack, Ptolemaic sunk | **0** | yes |
| cover1 | 1 | attack, Ptolemaic sunk | **0** | yes |
| move_cover1 | 1 | Ptolemaic sails to (111,74) | **1** (marker 335 now at (111,74)) | yes |

Evidence: run-exp-naval-loser-rough-sea, `cover0_{PRE,BEFORE,AFTER}.SAV`, `cover1_*`, `move_cover1_*` (release `run-exp-naval-loser-rough-sea`; SHA-256 in `runs/experiments/data/run-exp-naval-loser-rough-sea/SAVES.sha256`); `probe_rough.py`, `probe_rough.log`, `probe_rough_*.json`. One control attempt that targeted a land tile ((112,73), word 2, so the fleet did not move) is kept in `attempt_move_to_land.tar.gz` (release) and not cited.

## Method

- **Fixture:** `saves/fleets-adjacent-at-sea-0723.SAV` (Ptolemaic's turn, at war with Carthage): Ptolemaic fleet 1 (70 ships) at (111,73), Carthage fleet 0 (90 ships) at (110,73).
- **Patch:** both fleets' covered-cell field (+24) set to 1 for cover1 and move_cover1. Check: the `BEFORE` save of cover1 shows 1 in both records after the load.
- **Run:** fast rollingsave seed exe, seed 12345, Xvfb :99. Select fleet 1, then click Carthage's fleet (attack) or the sea tile (111,74) (move). Save, then read the words at (110,73), (111,73) and (111,74) and `Game.cell` for each.

## Not established

- A fleet sunk by a storm, or a loser on a real (unpatched) rough-sea tile. The patched field is what the game reads, so the result should carry over (`[derived]`).
- Armies: whether a destroyed army also writes 0, or restores its covered cell.
