# The battle map recolours its unit sprites with the same routine and nation dwords as the unit map: Numidia's units are grey-filled in battle, and their background is the battlefield's own lime

**Status:** draft from `ic2-conquest`, awaiting promotion. It checks research's `[derived]` consequence added at `4ef90ec` to `2026-10-09-unit-icon-recolour-and-nation-glyphs.md` ("battle-map units use the same recolour, so Numidia's units should be grey in battle too").

**Tags:**
- `[confirmed: decompile]`: capstone disassembly; the excerpt is tracked.
- `[confirmed]` (Wine): the recolour reproduces Rome's and Gaul's drawn battle sprites pixel for pixel.
- `[derived]`: Numidia's battle sprites. No Numidian battle was drawn.

## Answer

- **The battle form builds its 30 sprites with `FUN_0044a6c8`, the unit map's recolour routine** `[confirmed: decompile]` (`battlemap_sprites_436fb4.asm`, from 0x436fb4):
  - It runs when the battle flag `0x4A0B7C` is set.
  - Images 0-14 of the list at form field `+0x1AC` are each copied, recoloured with `owner` = army `[0x4A0B74]`'s owner word, and added to the list at `+0x1B0` (0x4370fb to 0x437137). `0x4A0B74` is the attacker's army.
  - The same 15 images are then recoloured with army `[0x4A0B76]`'s owner, the defender's, and added as images 15-29 (0x437139 to 0x43717a).
  - The army records are read at `0x47C1EC + 0x290 × army + 4`, which is the owner field.
- **There are only two other callers of `FUN_0044a6c8`, both in the unit map** (0x445cbe/0x445cff and 0x445f91/0x445fd5; `xrefs.txt`). The recolour dwords at `0x474a94 + 0x494 × owner` (+0/+4/+8) are read only inside `FUN_0044a6c8` and written only by `FUN_00448aa4`.
- **The templates are `TBattleMap.BatMapList` images 0-14** (17 images in all): Rome's purple `800080` background, white and blue, plus a 28 px lime `00ff00` frame. These are the 15 sprites type × size class, matching the grid word `side × 20 + 3 × type + size` of `2026-10-04-tactical-battle-sweep.md`.
- **In Wine this reproduces the drawn sprites exactly** `[confirmed]`. All 42 occupied cells of B2's 3 save/screenshot pairs match with 0 differing pixels over the whole 32×32 tile: 14 cells per pair, Rome as attacker and Gaul as defender, 2 distinct screenshots (`battle_recolour_check.json`). Each cell is the sprite of its grid word, the template recoloured with its side's owner dwords from the save.
  - **Pixel offset correction:** the tiles are drawn at window y = 30 + 32·row, which is 2 px lower than the `y0 = 28` of `b2_probe.py`. That script's occupied-or-empty test, 4 px inside the corner, is not affected.
- **So Numidia's units in battle** `[derived]`: with Numidia's dwords (`00ff00`, `000000`, `808080`), the purple background becomes **lime**, the white outline black, and the blue fill **grey**. In the large sprite (template 4) that gives lime 684 px, black 174 px and grey 166 px.
  - The battlefield's empty ground is pure lime `00ff00` (the test in `b2_probe.py`), and so is the templates' frame. **A Numidian sprite's background is the same colour as the ground**: only its black outline and grey fill stand out.
- **Grey fill is not unique to Numidia in battle:** the fill dword is `808080` for Macedonia, Numidia and Gaul (`recolour_check.json` of `run-exp-unit-icon-resources`). Gaul's B2 sprites were drawn grey-filled. Numidia is the only one whose city artwork's fill (teal) differs from that dword.

## Evidence

- **Data:** `runs/experiments/data/run-exp-battle-numidia-colour/`: `xrefs.py`, `xrefs.txt`, `disasm_range.py`, `battlemap_sprites_436fb4.asm`, `check_battle_recolour.py`, `battle_recolour_check.json`, `README.md`.
- **Inputs:** `B2_placement.SAV`, `B2_after_end_turn_1.SAV`, `B2_after_end_turn_2.SAV` and `b2_placement_window.png`, `b2_after_end_turn_1_window.png`, `b2_after_end_turn_2_window.png` (release `run-exp-battle-sweep`, SHA-256 in `runs/experiments/data/run-exp-battle-sweep/SAVES.sha256`); `TBattleMap_BatMapList.bmp` (release `run-exp-unit-icon-resources`).
- **Exe:** `Imperial Conquest 2.exe`, SHA-256 `9d753d5d…` (full hash in `run-exp-unit-icon-resources/imagelists.json`).

## Not established

- **A Numidian battle drawn in Wine:** none was run. It would need a battle with a Numidian army, for example an L1 owner edit of the defender army, or a game played as Numidia.
- **Images 15 and 16 of `BatMapList`** (lime, green, olive, white and black; white and black): not recoloured and not identified here.
- **The desktop original:** Wine only, as for the unit map.
