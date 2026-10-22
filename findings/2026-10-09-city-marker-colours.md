# City markers for every owner: five fixed three-colour templates; their colours equal the unit icons' for 15 owners. Numidia's fill is teal on cities and grey on unit icons

**Status:** promoted 2026-10-09 into imperial-conquest-2-research at `cdffb27` (by ic2-research), `[confirmed]` (Wine); this draft is kept for history, the research repo is canonical. **Addition (research review, `[derived]`):** in the capital temple (variant 4) the 334-px "outline" role is most of the glyph (roof, columns, base) and the 108-px fill is the gaps between the columns, so a by-eye reading of the 2026-09-29 strip could swap the roles; that may be all Macedonia's swap is. Gaul, Illyria and Media remain real colour differences, left for the desktop check. Wine-only (palette caveat below). Done at ic2-research's request for the player. It settles the five mismatches recorded at research `74fd9b5` / `ba103a0` (`2026-10-09-owner-colours-by-band.md`), as far as Wine shows them.

**Tag:** `[confirmed]` (Wine) for the drawing of each word. The words are written into the map, and real unpatched cities serve as controls (all match).

## Answer

- **Every one of the 80 words (20 + owner + 16 × variant, owners 0-15, variants 0-4) draws a distinct icon.** There are 16 distinct inset hashes per variant.
- **Each variant is a fixed template.** Every icon has exactly 3 colours, and each colour class covers the same pixels for all 16 owners. Role sizes in the 28×28 inset:

  | Variant | Glyph | Background | Outline | Fill |
  |---|---|---:|---:|---:|
  | 0 (pop < 25) | small house | 673 | 65 | 46 |
  | 1 (25-49) | house | 582 | 102 | 100 |
  | 2 (50-99) | small castle | 446 | 170 | 168 |
  | 3 (≥ 100) | large castle | 278 | 210 | 296 |
  | 4 (capital) | temple | 342 | 334 | 108 |

  Within each variant, background, outline and fill are fixed pixel sets. The outline is the glyph's edge and inner lines (white for Rome, black for Numidia); the fill is the glyph's body (blue for Rome, teal for Numidia). See `montage_cities.png`, one row per owner and one column per variant.
- **One colour triple per owner, the same in all five variants** (16 of 16). The background equals the unit icons' background for every owner.
- **City (outline, fill) = the unit icons' (A, B) for 15 owners.** The roles also line up: the 740-px role A is the outline colour, and the 607-px role B is the fill.
- **The exception is Numidia.** Its city fill is **teal `#008080`**, while its unit icons' B is grey `#808080`. Both were drawn in the same Wine session, so in Wine Numidia's cities and units really use different fills.
- **Against the 2026-09-29 table (outline, foreground):** the cities match it for 12 owners, including Numidia (black, teal). They do not match for 4:
  - Macedonia: city (blue, grey), table (grey, blue): swapped;
  - Gaul: city (cyan, grey), table (white, cyan);
  - Illyria: city (olive, cyan), table (white, olive);
  - Media: city (silver, purple), table (white, purple).

  For these four, the cities agree with the unit icons, not with the table. So, of the five mismatches at `74fd9b5`, Numidia is explained (the table read a city, and Numidia's city fill differs from its unit fill), while Macedonia, Gaul, Illyria and Media remain differences between the Wine drawing and the 2026-09-29 strip.
- **Which variant the strip's temples are:** variant 4 (the capital) is the only temple on a coloured square, so the strip's temples are variant-4 icons or the toolbar's nation buttons (below). Where the strip came from (desktop or Wine) is unknown here.
- **The toolbar's 16 nation buttons** (temples, 22×22 crops at y 48) are a different drawing. Each shows the background, the outline colour as the main glyph colour (104 px) and white (about 41 px, part of it the button bevel). They carry no fill colour (no teal for Numidia, no blue for Rome beyond 40 px). This is in `analyse_cities.json` → `toolbar` and not interpreted further.

| Owner | Nation | Background | Outline (city) | Fill (city) | Unit A, B | 2026-09-29 (outline, fg) |
|---:|---|---|---|---|---|---|
| 0 | Rome | `800080` | `ffffff` | `0000ff` | = | = |
| 1 | Carthage | `ff0000` | `000000` | `ffffff` | = | = |
| 2 | Seleucid | `808000` | `ffffff` | `800000` | = | = |
| 3 | Ptolemaic | `000080` | `ffffff` | `ff00ff` | = | = |
| 4 | Macedonia | `ffffff` | `0000ff` | `808080` | = | grey, blue (swapped) |
| 5 | Numidia | `00ff00` | `000000` | `008080` | black, **grey** | = |
| 6 | Gaul | `800000` | `00ffff` | `808080` | = | white, cyan |
| 7 | Greece | `00ffff` | `000000` | `ff00ff` | = | = |
| 8 | Celtiberia | `ffff00` | `000000` | `ff0000` | = | = |
| 9 | Illyria | `000080` | `808000` | `00ffff` | = | white, olive |
| 10 | Dacia | `008000` | `000000` | `ffff00` | = | = |
| 11 | Bithynia | `008080` | `000000` | `0000ff` | = | = |
| 12 | Galatia | `0000ff` | `000000` | `00ffff` | = | = |
| 13 | Armenia | `ff00ff` | `000000` | `ff0000` | = | = |
| 14 | Media | `ff0000` | `c0c0c0` | `800080` | = | white, purple |
| 15 | Thracia | `808080` | `ffffff` | `000000` | = | = |

## Controls and checks

- **Real cities, unpatched:** 15 of 15 match the patched copy of their word pixel for pixel inside the 2 px border:
  - screen 1: five Roman variant-1 cities, word 36;
  - screen 2, the view around Rome: Rome itself (84, the capital), Carsioli, Alba Fucens, Fregellae and Hadria (20), and Tarquinii, Arretium, Caere, Antium and Cales (36).
- **Rome army 1's tile** (120,53), word 200, matches `run-exp-owner-colours` (inset `e6129bbc48e5e3ee`).
- **Opacity:** 12 repeats of 20, 84 and 22 over map words 0 and 2 are identical to their first copies.
- **Memory:** each patched tile's memory word equals its word.

## Method

- **Save:** `artifacts/run-exp-army-marker-band/t24999_AFTER.SAV`, view origin (114,46), 13 × 12 tiles. The 80 words go on the visible tiles in order; the controls (Rome army 1, and the five Roman cities with word 36) are skipped; then the 12 repeats.
- **Run:** fast rollingsave seed exe, seed 12345, Xvfb. Screen 1 is taken after `Game.show(120,53)`. Screen 2 is taken after `Game.show(101,43)` (an Area map click), where the real cities around Rome are unpatched.
- **Measure:** crops at `UNIT_PAINT + 32·(c, r)`, 8-bit RGB, inset 2 px. Templates are compared as pixel sets per colour.
- **Comparisons:** against the research reports `2026-10-09-owner-colours-by-band.md` (`ba103a0`, columns A and B) and `2026-09-29-nation-marker-colours.md`, parsed in `analyse_cities.py`.

## Evidence

- **Data:** `runs/experiments/data/run-exp-city-marker-colours/`: `probe_cities.py`, `analyse_cities.py`, `probe_cities.json`, `analyse_cities.json`, `SAVES.sha256`.
- **Release** `run-exp-city-marker-colours`: `cities_PRE.SAV`, `cities_AFTER.SAV`, `cities_screen1.png`, `cities_screen2.png`, `montage_cities.png`, `tiles.tar.gz`.

## Not established

- **The desktop original:** the 2026-09-29 strip's origin and the desktop palette were not checked. The player will run the desktop check later (steps prepared separately).
- **Why Numidia's unit icons use grey** where its cities use teal: not read from code. It could be in the bitmaps themselves; the resources were not inspected.
