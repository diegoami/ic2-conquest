# A removed army restores the terrain under it (disband, join, battle loss); only a sunk fleet writes 0

**Status:** a draft from `ic2-conquest`, awaiting promotion. It answers research's follow-up to `2026-10-08-sunk-fleet-sets-its-tile-to-plain-sea.md` (research `4495fc6`): does an army's removal also write 0, which would leave calm sea on a land tile for good?

**Tag:** `[confirmed]` for the three paths run.

## Answer

- **No.** In all three removal paths the army's tile gets its covered cell back. Each removed army's covered-cell field (+8) was patched from its real terrain, plain (2), to forest (**4**), and the tile read **4** afterwards, in the save and in memory:

  | Case | Fixture | Removed army | Tile before → after |
  |---|---|---|---|
  | disband | run-0 start, Rome army 0 at (100,37) by Arretium | army 0 (Disband army, Confirm Yes) | 200 → **4** |
  | join | fleet-port fixture, army 0 (101,45) + army 13 (102,44) | partner army 13 (Join armies) | 200 → **4** |
  | battle | FLD-RG (Rome army 0 at (86,28) vs Gaul army 10 at (85,28)), tactical battle with Computer general | Rome army 0 ("Gaul destroys army of Rome.") | 216 → **4** |

- This fits the code. All three go through `FUN_0044ab90`, which writes the army's covered cell back to the map (:49386-49389):
  - Join armies: :46996;
  - the tactical battle: `TBattleOver_OK` :57627;
  - the instant field battle: `FUN_0044aee4` :49679, not run here.
- **The winner is re-banded.** Gaul's army 10 fell from 46,700 to 17,239 troops and its word from 222 (band 216 + owner 6) to **206** (band 200), from `FUN_0044a80c` :57626.
- **Contrast with fleets:** a sunk fleet's tile becomes 0 even on rough sea (`4495fc6`), while a fleet that sails away restores its covered cell. For armies, no removal path run here wrote 0, so the "permanent calm sea on land" case did not occur. Whatever map write of 0 the research report attributes to "army removal" was not reached by disband, join or a field-battle loss. Other army removals were not run: the last unit lost via `FUN_0044ac3c`, AI removals, sieges.

Evidence: run-exp-army-removal-tile, `disband_{PRE,BEFORE,AFTER}.SAV`, `join_*`, `battle_*` (release `run-exp-army-removal-tile`; SHA-256 in `runs/experiments/data/run-exp-army-removal-tile/SAVES.sha256`); `probe_army_tile.py`, `probe_army_tile.log`, `probe_army_tile_*.json`. The first battle attempt failed in the driver's view check (the FLD-RG save opens a 29 × 27-tile unit map, `runs/experiments/battles/common.py`); it is kept as `attempt_battle_view.tar.gz` and not cited.

## Method

Fast rollingsave seed exe, seed 12345, Xvfb :99. The pre-state patches only the +8 field of the army or armies that could be removed: in the battle both armies, since either could lose. Load, save `BEFORE`, run the order through the driver, save `AFTER`, then read the map word at each patched army's tile (offset x × 280 + y × 2) and `Game.cell`. For the battle the driver's view size is set to 29 × 27, as in the battle runners.

## Not established

- Army removal when the last unit is lost (mercenary desertion, `FUN_0044ac3c`), AI-side removals at the turn end, the instant AI-vs-AI field battle (`FUN_0044aee4`, which per the code uses the same `FUN_0044ab90`), and armies destroyed in a siege.
