# Desktop palette check: steps for the player (Windows, the original game)

Why: the army, fleet and city marker colours (`findings/2026-10-09-owner-colours-by-band.md`, `findings/2026-10-09-city-marker-colours.md`) were drawn under Wine only. ic2-research asks whether the desktop original draws the same 16 colours and the same templates, and where the 2026-09-29 colour strip came from.

## What to download

From the GitHub releases of diegoami/ic2-conquest:
- `colours_PRE.SAV` (release `run-exp-owner-colours`): the 96 army and fleet words, plus repeats.
- `cities_PRE.SAV` (release `run-exp-city-marker-colours`): the 80 city words, plus repeats.

Copy both into the game folder on Windows.

## Steps (for each of the two saves)

1. Start the original game (any build that loads saves; the seed does not matter, because nothing is played).
2. File > Open, and pick the save.
3. In the Area map, click Italy's heel so that tile (120,53) is in the Unit map. The patched block is the top-left 13 × 9 tiles of the view; the game opened it at view origin (114,46) under Wine, and it should open there on the desktop too.
4. Move the mouse off the map, and take a full-screen screenshot (PrtScn, saved as PNG, not JPEG).
5. Note the display's colour depth (Settings > Display > Advanced display, or "16 colours / 256 / 16-bit / 32-bit").

Also, if you can:
- one screenshot of a natural Unit map with several owners' armies, fleets and cities in view (for example the `1_rome_270_summer_7_1` position);
- whether you still have the 2026-09-29 strip of 16 temples, whether it came from the desktop or from Wine, and **what it was cropped from**: the toolbar's 16 nation buttons, the map's capital icons, or the raw button bitmaps (for example in a resource viewer, where the transparent margin shows white or yellow);
- a screenshot of the **toolbar's 16 nation buttons** on the desktop (the row right of the £ button), at 100 % zoom.

## What to send back

The PNG screenshots (they go to a release, not git) and the colour depth. The bot crops the tiles at the Wine coordinates, re-registered on the desktop window, compares the hashes and colour sets with the Wine tables, and writes the finding. The result is tagged `[confirmed]` for the desktop only where it was seen there.
