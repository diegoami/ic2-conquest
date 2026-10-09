# Army and fleet icons are three Rome-coloured templates recoloured from three per-nation colour dwords set at new game; Numidia's fill there is grey (hard-coded), its artwork teal. The toolbar glyphs equal the capital icons

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Done at ic2-research's requests for the player: why Numidia's unit fill is grey; the toolbar nation-button glyphs; the Gaul, Illyria and Media question.

**Tags:**
- `[confirmed: resources]`: the image lists and glyphs, read-only from `Imperial Conquest 2.exe`.
- `[confirmed: decompile]`: capstone disassembly; the excerpts are tracked.
- `[confirmed]` (Wine): the screen matches.

## Answer

### Numidia's grey: recoloured from data set in code, not baked into the artwork

- **The unit map's image lists** (form `TUnitMap`, in `TPF0` resources) `[confirmed: resources]`:
  - `ArmiesList` and `FleetsList`: **3 images each**, one per band, 32×32, 8-bit;
  - `Cities1List` to `Cities4List` and `CapitalsList`: **16 images each**, one per owner;
  - `TerrainList`: 13 images.
- **The army and fleet templates are drawn in Rome's colours:** purple `800080` background, white `ffffff` outline, blue `0000ff` fill, black border.
- **The city images carry each owner's colours in the artwork.** Numidia's city and capital images are lime / black / **teal `008080`**.
- **The paint routine** (`unitmap_paint_445b.asm`, around 0x445bf2 to 0x445d04) `[confirmed: decompile]`:
  - A city word indexes its city list directly (word − 0x14, 0x24, 0x34, 0x44 or 0x54), with no recolouring.
  - An army word takes `ArmiesList` (field 0x1B4) image (word − 200) / 16, then calls `FUN_0044a6c8(owner = (word − 200) mod 16, bitmap)`.
  - A fleet word does the same with `FleetsList` (field 0x1B8) and word − 300.
- **`FUN_0044a6c8`** walks the 32×32 pixels through `Canvas.Pixels` `[confirmed: decompile]`:
  - TColor `0x800080` (purple) → the dword at `0x474a94 + 0x494 × owner`;
  - `0xFFFFFF` (white) → `+4`;
  - `0xFF0000` (blue, as a Delphi TColor) → `+8`.

  0x474a94 − 0x474670 = **+0x424** in the 1,172-byte nation record, so the recolour colours are nation-record fields **+0x424 (background), +0x428 (outline), +0x42C (fill)**. They are saved with the record.
- **`FUN_00448aa4`** (new-game nation setup, edi = 0x474670; called from 0x45a93a and 0x45aa32) writes all 48 dwords as immediates (0x448c9b to 0x448e63) `[confirmed: decompile]`. Numidia's are at 0x448d2f to 0x448d41: `[edi+0x1b08] = 0xff00` (lime), `[edi+0x1b0c] = 0` (black), **`[edi+0x1b10] = 0x808080` (grey)**. They are also in the save: `saves/run0-start-AUTO0720-seed12345.SAV`, Numidia +0x424/+0x428/+0x42C = `00ff00`, `000000`, `808080`.
- **So Numidia's unit fill is grey because the code's colour table says grey, while its city artwork is teal.** The other 15 owners' three dwords equal their city colours exactly (`compare_roles.json`). It is a data inconsistency inside the original, not a renderer or palette effect, and not something Wine introduces `[derived]`.

### The toolbar's 16 nation buttons

- **Each is a `TSpeedButton`** `sb_<Nation>` on the main form: `OnClick = ChangeNation`, `NumGlyphs = 2`. `Glyph.Data` is a 40×20, **4-bit BMP with its own 16-colour palette**: a 20×20 up glyph, then a 20×20 second glyph (silver or white 348 px, black 52 px) `[confirmed: resources]`.
- **The up glyph's roles:** background 180 px, outline 104 px, a margin 76 px, fill 40 px.
  - The margin is the transparent colour (the bitmap's bottom-left pixel): **yellow `ffff00`** for owners 0-4 and 15, **white `ffffff`** for owners 5-14.
  - A TSpeedButton draws the transparent colour as the button face, so the margin never shows on screen.
- **The glyphs equal the capital map icons (variant 4) in all three roles for all 16 owners,** and the unit recolour dwords for 15 (Numidia's fill: teal in the glyph, grey in the dwords).
- **The glyphs are drawn unchanged in Wine.** The up glyph of 15 buttons matches the Wine toolbar pixel for pixel, 0 of 324 opaque pixels differing (`toolbar_match.json`), at x = 254 + 24·(owner − 1), y = 49. Rome's button is pressed (current nation) and drawn 1 px lower, with 52 mismatches at the best offset.
- **Correction to my `d684f24` draft:** the `analyse_cities.json → toolbar` numbers came from 22×22 crops at a guessed x (229 + 24·owner), which do not line up with the buttons. The "white in the fill role for owners 5-14" read from them is a cropping artefact. The buttons show their fill colour: Numidia teal, Gaul grey, Illyria cyan, Media purple. See the enlarged toolbar in `cities_screen1.png`, y 46-72.

### The 2026-09-29 table against the stored glyphs, all 16 owners

| Owner | Nation | Glyph (bg, outline, fill) | Margin (transparent) | 2026-09-29 (outline, fg) | Match |
|---:|---|---|---|---|---|
| 0 | Rome | 800080, ffffff, 0000ff | ffff00 | ffffff, 0000ff | = |
| 1 | Carthage | ff0000, 000000, ffffff | ffff00 | 000000, ffffff | = |
| 2 | Seleucid | 808000, ffffff, 800000 | ffff00 | ffffff, 800000 | = |
| 3 | Ptolemaic | 000080, ffffff, ff00ff | ffff00 | ffffff, ff00ff | = |
| 4 | Macedonia | ffffff, 0000ff, 808080 | ffff00 | 808080, 0000ff | swapped |
| 5 | Numidia | 00ff00, 000000, 008080 | ffffff | 000000, 008080 | = |
| 6 | Gaul | 800000, 00ffff, 808080 | ffffff | ffffff, 00ffff | = (margin, outline) |
| 7 | Greece | 00ffff, 000000, ff00ff | ffffff | 000000, ff00ff | = |
| 8 | Celtiberia | ffff00, 000000, ff0000 | ffffff | 000000, ff0000 | = |
| 9 | Illyria | 000080, 808000, 00ffff | ffffff | ffffff, 808000 | = (margin, outline) |
| 10 | Dacia | 008000, 000000, ffff00 | ffffff | 000000, ffff00 | = |
| 11 | Bithynia | 008080, 000000, 0000ff | ffffff | 000000, 0000ff | = |
| 12 | Galatia | 0000ff, 000000, 00ffff | ffffff | 000000, 00ffff | = |
| 13 | Armenia | ff00ff, 000000, ff0000 | ffffff | 000000, ff0000 | = |
| 14 | Media | ff0000, c0c0c0, 800080 | ffffff | ffffff, 800080 | neither (white = margin; purple = fill) |
| 15 | Thracia | 808080, ffffff, 000000 | ffff00 | ffffff, 000000 | = |

`[derived]`:
- **Gaul and Illyria:** the table's "white outline" equals the glyph's white transparent margin, and its foreground equals the glyph's outline. A strip read from the raw glyph bitmaps, with the transparent margin visible, would give exactly those pairs. **Media** fits the same reading only in part: white is its margin, and purple its 40-px fill.
- **Macedonia:** the swap fits the role confusion research already noted for the temple shape (`cdffb27`).
- **No row of the table needs a palette other than the glyphs' own 16 colours.** The glyphs are 4-bit with their own palette, so a desktop at 16 colours or more should draw the same colours; this is not checked on the desktop.

## Evidence

- **Data:** `runs/experiments/data/run-exp-unit-icon-resources/`:
  - `extract_imagelists.py`, `decode_imagelists.py`, `imagelists.json`, `imagelists_decoded.json` (counts, sizes, colours per image);
  - `extract_glyphs.py`, `glyphs.json`, `match_toolbar.py`, `toolbar_match.json`, `compare_roles.py`, `compare_roles.json`;
  - `FUN_00448aa4.asm`, `FUN_0044a6c8.asm`, `unitmap_paint_445b.asm`, `disasm_note.md`;
  - `SAVES.sha256`.
- **Exe:** `Imperial Conquest 2.exe` (SHA-256 in `imagelists.json`).
- **Release** `run-exp-unit-icon-resources`: the `TUnitMap_*` image lists and the 16 `glyph_sb_*` glyphs as BMP and PNG.
- **Screenshot:** `cities_screen1.png` (release `run-exp-city-marker-colours`).

## Not established

- **Whether the original programmer meant Numidia to be teal:** only the inconsistency is shown.
- **Saves edited to other colours:** the recolour reads the save's fields, so a save edit would recolour units, but this was not drawn.
- **Where the 2026-09-29 strip came from:** the reading above is a hypothesis. The player is asked in `runs/experiments/data/run-exp-desktop-palette/STEPS.md`.
