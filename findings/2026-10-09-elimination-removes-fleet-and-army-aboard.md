# When a nation is conquered, its fleet and the army aboard are removed with it; the fleet's tile is written 0, even over rough sea

**Status:** promoted 2026-10-09 into imperial-conquest-2-research at `c288059` (by ic2-research), [confirmed] with a synthetic pre-state. Research settled the code path (decompiled-elimination-cleanup.md): `FUN_0044C528` runs the army loop first, where `FUN_0044AB90(10)` sees cell −1, clears the carrier's +22 without a map write and tombstones the army; the fleet loop then runs `FUN_0044AD38`, which writes 0 and finds +22 already −1. This draft is kept for history; the research repo is canonical. Wine-only. Pre-state edited (see Method). This answers the open item "armies aboard a fleet at elimination", left from the army-removal series (`2026-10-09-turn-end-and-ai-army-removals-restore-their-tile.md`, research `e6b4643`).

**Tag:** `[confirmed]` (3 runs, one per case, seed 12345).

## Answer

In all three cases, Rome's third capture leaves Numidia with 5 cities, and the news reads "Rome conquers Numidia."

- **Fleet:** its record gets owner **−1**, and its carried-army field goes from 10 to **−1**. Ships (90) and position (74,71) are left as they were.
- **Army aboard (record 10):** its record gets owner **−1**. It keeps x,y = the fleet's tile, cell −1 and its 33,900 troops.
- **Fleet tile (74,71):** marker 337 → **0**, in the save and in memory.
  - When the fleet's covered cell (+24) was set to 1 (rough sea) before the sieges (`sieges_cover1`), the tile still reads **0**. The conquest writes 0; it does not restore the covered cell. This matches the battle-sunk fleet (`2026-10-08-sunk-fleet-sets-its-tile-to-plain-sea.md`).
  - The army aboard leaves nothing on the map. Its cell field is −1, and no −1 (0xFFFF) is written to the fleet's tile.
- **Numidian army on land (record 2, control):** owner −1, and its tile goes from marker 221 back to its covered cell **2**, as in the earlier conquest case.
- **After End turn** (`sieges_end_turn`, autosave `AUTO0722.SAV`): the tombstoned records are compacted away. Armies go from 14 → **12** (records 2 and 10 gone, later records shift down). The dead fleet record is gone, and Ptolemaic's fleet is now record 0. No fleet is left carrying an index into the shifted army table: every fleet's carried-army field is −1. The second fleet record in that save is a Carthaginian fleet being built (countdown 22), started during the AI turn.
- **No message** names the fleet or the army. The news has only the three captures and "Rome conquers Numidia."; no confirm box appeared (popups: none).

| Case | Fleet owner after | Fleet's army field | Army 10 owner after | Tile (74,71) after | Land army tile (42,63) after | Records after |
|---|---:|---:|---:|---:|---:|---|
| `sieges` | −1 | −1 | −1 | 0 | 2 | 14 armies, 2 fleets (tombstones kept) |
| `sieges_cover1` (fleet covered cell 1) | −1 | −1 | −1 | **0** | 2 | same |
| `sieges_end_turn` | (record removed) | – | (record removed) | 0 | 2 | 12 armies; fleets: Ptolemaic + a Carthage fleet being built |

## Method

- **Base:** `saves/siege-felsina-failed-0721.SAV` (Rome's turn, 0721). The consistent elimination pre-state of `run-exp-turn-end-army-removal`:
  - three Rome armies of 2 × 30,000 heavy infantry are placed next to Capsa, Ghadames and Ghirza (Numidia holds 8 cities);
  - Carthage army 2 at (42,63) is re-owned to Numidia;
  - Rome and Numidia are set at war.
- **Added for this test (synthetic edits):**
  - Carthage fleet 0 (90 ships, at (74,71)) is re-owned to Numidia, with marker 333 → 337 (owner 5 + 332, band unchanged).
  - Celtiberia army 10 (33,900 men, at (38,64)) is re-owned to Numidia and put aboard that fleet. This is the edit of `runs/experiments/fleet-battles/t3_stage.py`, byte-checked there against a natural embark: army x,y = the fleet's tile, moves 0, cell −1; fleet +22 = 10; the army's old tile restored to its covered cell 2.
  - `sieges_cover1` also sets the fleet's +24 to 1.
- **Run:** fast rollingsave seed exe, seed 12345, Xvfb. The three armies attack their cities in turn (`Game.attack`), and the save is taken after the third capture. `sieges_end_turn` then ends the turn and saves again.
- **Read:** the fleet and army records, the words at (74,71), (42,63) and (38,64), in the save and in game memory (`Game.cell`).

## Evidence

- **Data:** `runs/experiments/data/run-exp-elimination-army-aboard/`: `probe_aboard.py`, `probe_aboard_{sieges,sieges_cover1,sieges_end_turn}.json`, `SAVES.sha256`.
- **Saves:** release `run-exp-elimination-army-aboard`: `<case>_PRE.SAV` (edited), `<case>_BEFORE.SAV` (after the load), `<case>_AFTER.SAV`, for the cases `sieges`, `sieges_cover1` and `sieges_end_turn`. Turn 0721; `sieges_end_turn_AFTER.SAV` is at 0722.

## Not established

- **A natural pre-state:** the fleet and the army aboard come from save edits. A Numidian fleet that embarked an army in play, and an AI nation conquered in an AI-side capture, were not run.
- **Code path:** the conquest (`FUN_0044C528`) tombstones fleets and their cargo. Whether it calls `FUN_0044ad38` for the fleet and `FUN_0044ab90` for the army, or clears the army's owner directly (its cell −1 is not written to the map either way), is for research to confirm from code.
- **Other elimination paths:** defection elimination (`FUN_0044BED8`, via rebirth) was recorded by code only and was not run here.
