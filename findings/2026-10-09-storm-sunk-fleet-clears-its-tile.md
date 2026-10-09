# A fleet lost at sea in a storm leaves no marker: its tile reads plain sea (0), or rough sea (1) where the new week's weather paints it

**Status:** promoted 2026-10-09 into imperial-conquest-2-research at `e0e1616` (by ic2-research), [confirmed]. Research settled the open question from code: the storm death check calls `FUN_0044ad38`, which writes 0, and the weekly re-roll `FUN_00451304` runs after the fleet loop of `FUN_004514ec`, so the three 1s are the new week's paint. This draft is kept for history; the research repo is canonical. Wine-only. It closes the open item "a fleet sunk by a storm" of `2026-10-08-sunk-fleet-sets-its-tile-to-plain-sea.md` (research `4495fc6`).

**Tag:** `[confirmed]` (44 storm losses: 43 in trials, 1 natural). No new game run: this reads the result saves already kept by `run-exp-storms` (`2026-10-03-storms-and-losses-at-sea.md`).

## Answer

- **No stale marker.** In every storm loss, the fleet's tile no longer holds the fleet marker (333 for Carthage, 335 for Ptolemaic). Every surviving fleet still shows its marker on the same tile.
- **Calm sea (covered field 0):** the tile reads **0** in 13 of 13 losses (K45s × 6, K45w × 7).
- **Rough sea (covered field 1 at the tick):** the tile reads **0** in 27 of 30 losses and **1** in 3 (R45s seed 3, R45w seed 2, R45sA seed 5).
  - The 1s come from the next week's rough sea, which the weekly re-roll paints after the storm. For the 15 rough-sea losses whose seed also has a condition-85 twin (R85s, R85w, R85sA, seeds 1-5), the surviving twin's covered field after the tick equals the lost fleet's tile word in 15 of 15 (1 in the three cases above, 0 in the other 12). In the same three saves the 3×3 block around (39,77) is mostly rough, too.
  - So the storm is resolved on this week's rough sea (the survivors were damaged as on rough sea), and the tile then shows whatever the new week's weather paints there.
- **Natural loss:** Ptolemaic's fleet, lost at sea at 0727 with nothing edited, was at (164,66). That tile reads 335 at `NAT_seed1_11_0726_seat02.SAV` and **0** at `NAT_seed1_13_0727_seat02.SAV`.
- **For play:** a fleet lost in a storm frees its tile at once, like a fleet sunk in battle. The tile's later state is the weekly weather's, not the fleet's.

| Losses | Covered before | Tile word after | Count |
|---|---:|---:|---:|
| calm sea, away from cities (K45s, K45w) | 0 | 0 | 13 |
| rough sea (R45s, R45w, R45sA) | 1 | 0 | 27 |
| rough sea, new week's rough painted there | 1 | 1 | 3 |
| natural, Ptolemaic, calm sea | 0 | 0 | 1 |
| survivors (H45s, K45s, K45w, R85s, R85w, R85sA, H85s, K85s, K85w; seed-1 saves and every kept low-condition save) | 0 or 1 | 333 (marker) | 14 |

## Evidence

- **Data:** `runs/experiments/data/run-exp-storm-sunk-tile/`: `storm_tiles.py` (read-only), `storm_tiles.log`, `storm_tiles.json`, `SAVES.sha256` (the 54 cited saves; each hash equals its line in `runs/experiments/data/run-exp-storms/SAVES.sha256`).
- **Saves:** release `run-exp-storms`, e.g. `ST_K45s_seed2_AUTO0721.SAV` (lost, 0), `ST_K45s_seed1_AUTO0721.SAV` (survivor, 333), `ST_R45s_seed1_AUTO0721.SAV` (lost, 0), `ST_R45s_seed3_AUTO0721.SAV` (lost, 1: new rough sea), `NAT_seed1_11_0726_seat02.SAV` / `NAT_seed1_13_0727_seat02.SAV` (natural, 335 → 0). The fleet's tile and covered field before the tick are those of `runs/experiments/data/run-exp-storms/t4_trials.json` (`before.x`, `before.y`, `before.covered`); loss = `after` is null there, matching the news "A fleet belonging to Carthage is lost at sea."
- **Map word:** at offset `x*280 + y*2` of the save (`docs/sav-layout-notes.md`).

## Not established

- **Write 0 or restore the covered cell?** Play can't tell the two apart. On calm sea both give 0. On rough sea the weekly re-roll (`FUN_00451304`, research `decompiled-map-code1-overlay.md`) clears code 1 everywhere and repaints after the storm, so a restored 1 would be cleared anyway, or repainted where the new weather puts it. The battle case (`2026-10-08-sunk-fleet-sets-its-tile-to-plain-sea.md`) showed a write of 0. That the storm loss uses the same tombstone (`FUN_0044ad38`) is research's code reading to confirm.
- **An army aboard:** in the 10 R45sA losses the army went with the fleet (storms finding). An army aboard is not on the map, so it has no tile of its own.
- **Saves:** results were saved only after the AI seats had moved. No AI fleet sailed onto (39,77), (49,62) or (164,66) in these saves; a tile word other than 0, 1 or the marker would have shown that.
