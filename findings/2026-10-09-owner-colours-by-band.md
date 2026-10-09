# Every owner's army and fleet icons: one background colour per owner, the same three band shapes for all; 96 distinct icons

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Wine-only. It closes "other owners' colours by band", left open by `2026-10-08-army-icon-follows-the-size-band.md` (research `e18eaad`) and `2026-10-08-fleet-marker-band-and-icon.md` (research `bff6bff`).

**Tag:** `[confirmed]` for the drawing of each stored word. The words were written into the save, not produced by play.

## Answer

- **All 96 words draw distinct icons:** army 200/216/232 + owner and fleet 300/316/332 + owner, for owners 0-15. Each (kind, band) has 16 different icons, one per owner (hashes over the 28×28 inset).
- **Shape is set by the band, colour by the owner.** Every owner gets the same three soldiers (small, medium, large with mace) and the same three ships (small, medium, large), drawn in its own colours (`montage_army.png`, `montage_fleet.png`: one row per owner, one column per band).
- **One background colour per owner,** the same in all six of its icons. 14 backgrounds for 16 owners:
  - Carthage (1) and Media (14) share red;
  - Ptolemaic (3) and Illyria (9) share navy;
  - the figure colours of each pair differ (table).
- **The terrain under the icon does not show.** The icon is opaque: four repeats of 200 (Rome army), 238 (Gaul army) and 333 (Carthage fleet) on other tiles, over the map words 0, 2 and 36, are pixel-identical inside a 2 px border. Only the dotted tile edges differ, which follow the neighbouring tiles.
- **Control:** Rome army 1's own tile (120,53), word 200, left unpatched, matches the earlier Rome 200 icon of `run-exp-army-marker-icon` pixel for pixel inside the border (`e6129bbc48e5e3ee` for both). The earlier full-tile hashes differ only by the dotted edges, and by the earlier hash being taken on 16-bit RGB.

| Owner | Nation | Background | Next two colours (figure) |
|---:|---|---|---|
| 0 | Rome | `#800080` purple | `#0000ff`, `#ffffff` |
| 1 | Carthage | `#ff0000` red | `#000000`, `#ffffff` |
| 2 | Seleucid | `#808000` olive | `#800000`, `#ffffff` |
| 3 | Ptolemaic | `#000080` navy | `#ff00ff`, `#ffffff` |
| 4 | Macedonia | `#ffffff` white | `#0000ff`, `#808080` |
| 5 | Numidia | `#00ff00` lime | `#000000`, `#808080` |
| 6 | Gaul | `#800000` maroon | `#00ffff`, `#808080` |
| 7 | Greece | `#00ffff` cyan | `#000000`, `#ff00ff` |
| 8 | Celtiberia | `#ffff00` yellow | `#000000`, `#ff0000` |
| 9 | Illyria | `#000080` navy | `#00ffff`, `#808000` |
| 10 | Dacia | `#008000` green | `#000000`, `#ffff00` |
| 11 | Bithynia | `#008080` teal | `#000000`, `#0000ff` |
| 12 | Galatia | `#0000ff` blue | `#000000`, `#00ffff` |
| 13 | Armenia | `#ff00ff` magenta | `#000000`, `#ff0000` |
| 14 | Media | `#ff0000` red | `#800080`, `#c0c0c0` |
| 15 | Thracia | `#808080` grey | `#000000`, `#ffffff` |

The "next two" are the second- and third-most frequent colours of each tile's inset, across the owner's six icons: the figure's colours, not a palette reading.

## Method

- **Save:** `artifacts/run-exp-army-marker-band/t24999_AFTER.SAV` (Rome army 1 at (120,53)). The unit-map view is at origin (114,46) after the load, checked in memory: 13 × 12 tiles, (120,53) at screen (545,366).
- **Patch:** every visible tile except (120,53) gets one word: the 96 words above, then 12 repeats (200, 238, 333 four times each) on other tiles. Map words only; no records changed.
- **Run:** fast rollingsave seed exe, seed 12345, Xvfb. Load, `Game.show(120,53)` (the view does not move), pointer parked off the map, one screenshot.
- **Measure:** every tile cropped at `UNIT_PAINT + 32·(c, r)` and hashed as 8-bit RGB, whole and inset by 2 px. The memory word of every tile equals the patched word (`mem_word`).

## Evidence

- **Data:** `runs/experiments/data/run-exp-owner-colours/`: `probe_colours.py`, `analyse_colours.py`, `probe_colours.json`, `analyse_colours.json` (per tile: word, terrain under, memory word, hashes, top colours), `SAVES.sha256`.
- **Release** `run-exp-owner-colours`: `colours_PRE.SAV`, `colours_AFTER.SAV`, `colours_screen.png`, `montage_army.png`, `montage_fleet.png`, `montage_both.png`, and `tiles.tar.gz` (the 109 cropped tiles).

## Not established

- **Real armies and fleets of each owner:** the words were written into the map, not produced by armies of those owners. The earlier Rome tests showed the icon follows the stored word (`e18eaad`), so this should hold for every owner (`[derived]`).
- **The desktop palette:** Wine draws a 16-colour palette here. On the original Windows the colours should be the same standard 16, but this was not checked.
- **Owner words above 15 and the other marker families** (cities, etc.) were not drawn.
