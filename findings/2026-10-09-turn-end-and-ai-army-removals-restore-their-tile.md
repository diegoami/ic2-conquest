# Turn-end and AI-side army removals also restore the tile; record compaction keeps markers right

**Status:** promoted 2026-10-09 into imperial-conquest-2-research at `e6b4643` (by ic2-research); this draft is kept for history, the research repo is canonical. The desertion rule is confirmed there (upkeep-payment-and-desertion.md): an unpaid all-mercenary army of n units loses ceil(n/2) per quarter. The player asked for it through ic2-research on 2026-10-09: the four paths named in `decompiled-elimination-cleanup.md` and `upkeep-payment-and-desertion.md`, after `2026-10-09-siege-removed-army-restores-its-tile.md` (research `99899ac`).

**Tag:** `[confirmed]` for each path below. All four could be forced.

## Answer

In every path the removed army's tile got its **covered cell back**: the value patched into the record's +8, distinct from the real terrain. No path wrote 0, and none left a marker without an army. Record compaction at the next AI pass moved the last record into the hole with its marker and covered cell intact.

| Path | How it was forced | Removed army | Tile before → after |
|---|---|---|---|
| 1. Nation elimination, conquest `FUN_0044C528` | Rome took 3 of Numidia's 8 cities in one turn (Capsa, Ghadames, Ghirza: 7 → 6 → 5 < 6): "Rome conquers Numidia." | Numidian army (record 2, owner 5) at (42,63), covered cell 2 → 4 | 221 → **4** (owner −1) |
| 2. Mercenary desertion at the quarterly tick | FLD-RG save (winter week 11), Rome army 13 with **one** mercenary unit and purse 0, End turn | army 13 at (93,28), covered cell 5 → 4 | 216 → **4** |
| 3. AI-vs-AI field battle | Carthage army 2 (42,63) and Celtiberia army 10 placed at (43,63), at war; Rome ends its turn: "Celtiberia destroys army of Carthage." | Carthage army 2, covered cell 2 → 4 | 217 → **4** |
| 4. Record compaction | the end turn after path 1 (and after path 3) | Media's army moved from record 13 to record 2 | marker and covered cell unchanged (2 → 2); 0 marker mismatches among live armies |

**Extras:**
- **Desertion removes only some units per tick.**
  - The run: with 7 mercenary units and purse 0, one tick removed 4 and left 3: 13,534 + 3,406 + 5,251 = 22,191 men (`merc_desertion`).
  - The cause: the pay loop runs slots 0 → 19, and each removal moves the last unit into the hole (`FUN_0044ac3c`). The unit moved in is skipped, because the loop goes on to the next slot. With slots [4,751, 2,678, 4,649, 4,186, 5,251, 3,406, 13,534] that rule leaves exactly the three survivors.
  - So an all-mercenary army with no money takes several quarters to disappear. A single-unit army goes at once (`merc_desertion_single`).
  - `[derived]` for the rule; the loop body is in research's `upkeep-payment-and-desertion.md`.
- **In the same `merc_desertion` run, Gaul attacked Rome's army 0 in the AI turn** (a battle-screen battle, played by the driver's Computer general) and destroyed it. Its tile (86,28) went 216 → 2, its own unpatched covered cell.
- **In the AI battle the winner moved off afterwards.** (43,63) also read 4, the covered cell put back on leaving.
- **A stale band exists in a natural save.** Seleucid's army 9 at (197,62) has 37,821 troops but word 234 (band 50,000+) in the FLD-RG fixture before any order. Some troop loss lowered it without a re-band. It is not caused by compaction.
- **Numidia's city count stays 5** after the conquest, as research's report says (it is never decremented for the annexed cities).

**Caution for edited saves:** the first elimination attempt only patched Gaul's city count (+0x446) to 6 and left its city list and the city owners as they were. The conquest then corrupted the nation table: Numidia's and Gaul's records came out 2 bytes shifted, and Macedonia's recruitment slots were overwritten. An inconsistent city count is not a valid pre-state. That attempt is kept as `attempt_elimination_patched_count.tar.gz` and not cited. The cited run kept every count, list and owner consistent: the game made the three captures itself.

Evidence: run-exp-turn-end-army-removal, `<case>_{PRE,BEFORE,AFTER}.SAV` for merc_desertion, merc_desertion_single, elimination_numidia, elimination_end_turn and ai_battle (release `run-exp-turn-end-army-removal`; SHA-256 in `runs/experiments/data/run-exp-turn-end-army-removal/SAVES.sha256`); `probe_turnend.py`, `probe_turnend.log`, `probe_turnend_*.json`.

## Method

- **Run:** fast rollingsave seed exe, seed 12345, Xvfb :99.
- **Removed armies:** each army that the path removes has its covered cell (+8) patched to a value its real terrain is not. After the order or the end turn, read the map word at its tile (save and `Game.cell`). Every live, not-embarked army is then checked for marker = owner + band(troops).
- **Moved armies** (paths 1 and 3) are placed consistently, with `place_army`:
  - the old tile gets the record's covered cell;
  - the new covered cell is the new tile's terrain;
  - the marker is written to the new tile.
- **Re-owned records** get a matching marker.
- **Relations** are set with the symmetric write at nation +0x26.
- **Fixtures:**
  - paths 2 and 4 use `FLD-RG_0743_rome_army0_at_86_28.SAV` (turn 0743, winter week 11; its 29 × 27-tile view is set in the driver);
  - paths 1, 3 and 4 use `saves/siege-felsina-failed-0721.SAV`.

## Not established

- The defection elimination path `FUN_0044BED8` (by code the same army loop: `FUN_0044AB90`).
- Armies aboard a fleet when their nation is eliminated.
