# Naval battle: the loser's tile word goes to 0, and the survivors are re-banded

**Status:** promoted 2026-10-08 into imperial-conquest-2-research at `0389684` (by ic2-research); this draft is kept for history, the research repo is canonical. It answers the piece left open in research `f9d061a`: whether tombstoning a losing fleet (`FUN_0044ad38`) clears its map word. No new play: these are the saves of release `run-exp-naval-battle` (`findings/2026-10-02-naval-battles.md`) read again.

**Tag:** `[confirmed]` for "the word goes to 0 at the loser's tile" and for the survivors' bands, on sea tiles.

## Answer

- **The loser's tile word becomes 0.** The losing fleet is tombstoned (owner −1), keeping its pre-battle ships field. All nine losing fleets (PROBE_AFTER and the NB_* cells: Ptolemaic fleet 1 in seven saves, Carthage fleet 0 in C50 and P60) had word 335 or 333 at their tile before the battle and **0** after.
- **The survivors are re-banded.** Every surviving fleet's word equals owner + band of its ships after the battle, for example:
  - Carthage fleet 0 at 81 ships: 333; at 40 ships: 317.
  - Ptolemaic fleet 1 at 54 ships: 335; at 48 ships: 319.
  - Carthage fleet 2 at 20 ships: 301.

  That is 15 surviving fleets across the 9 saves. It fits research's code reading, `FUN_0044b4f8` calling `FUN_0044A878` for the winning fleet.
- **Cleared or restored?** The covered-cell field (+24) of every fleet here is **0** (sea), so these saves cannot tell "the word is cleared to 0" from "the covered terrain is restored". On rough sea (covered cell 1) the two readings would differ (`[derived]`).

| Save | Loser (tile, word after) | Survivors: ships → word (expected) |
|---|---|---|
| fixture (before) | | f0 90 → 333 (333); f1 70 → 335 (335) |
| PROBE_AFTER | f1 (111,73): 0 | f0 80 → 333 |
| NB_C | f1: 0 | f0 81 → 333 |
| NB_C50 | f0 (110,73): 0 | f1 48 → 319; f2 40 → 317 |
| NB_C55 | f1: 0 | f0 40 → 317; f2 35 → 317 |
| NB_C60 | f1: 0 | f0 46 → 317; f2 30 → 317 |
| NB_C65 | f1: 0 | f0 53 → 333; f2 25 → 317 |
| NB_C70 | f1: 0 | f0 59 → 333; f2 20 → 301 |
| NB_P | f1: 0 | f0 72 → 333 |
| NB_P60 | f0: 0 | f1 54 → 335; f2 30 → 317 |

Every survivor's word matched its expected band.

Evidence: release `run-exp-naval-battle` (`PROBE_AFTER.SAV`, `NB_*_seed1.SAV`) and the fixture `saves/fleets-adjacent-at-sea-0723.SAV`; their SHA-256 and the read-out are in `runs/experiments/data/run-exp-naval-loser-word/` (`SAVES.sha256`, `naval_words.log`, `read_naval_words.py`).

## Not established

- A loser on rough sea, which would separate "cleared to 0" from "covered terrain restored".
- Storm losses in play (research's code reading covers them).
