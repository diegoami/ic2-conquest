# A Rome v Numidia battle drawn in Wine: Numidia's battle units are lime, black and grey, exactly the recoloured templates

**Status:** draft from `ic2-conquest`, awaiting promotion. It closes the "Not established" item "a Numidian battle drawn in Wine" of `2026-10-09-battle-map-units-use-the-nation-recolour.md` (research `ef19e2c`), at the player's request. Numidia's battle sprites move from `[derived]` to `[confirmed]` (Wine).

**Tags:**
- `[confirmed]` (Wine): read from the screenshot, the saves and game memory.
- **L1 (synthetic, labelled):** two strategic edits before the attack. Placement, initiative and drawing are the game's own.

## Answer

- **The setup** (`draw-20261009-141127.jsonl`):
  - FLD-RG, Rome's army 0 next to army 10 at (85,28). Army 10 was given to Numidia (`owner` 10 → 5) and the Rome-Numidia relation set to 3, the Rome-Gaul value. Positions and units are untouched: Gaul's five LI/HI units.
  - Game memory read back army 10's owner as 5.
  - The attack opened a battle titled **"Rome  v  Numidia"** (lab build s1). Header: attacker army 0, defender army 10.
- **The drawing** (`numidia_draw_check.json`): at the placement phase, all **14 occupied cells** (9 Roman, 5 Numidian: words 21, 22 and 25 at row 9) equal the `BatMapList` templates recoloured with each side's save dwords. There are **0 differing pixels over the full 32 × 32 tile** at the known offset (0, +2).
  - Numidia's dwords are `00ff00` / `000000` / `808080`.
  - **The 5 Numidian cells are lime 3,393, black 895 and grey 832 pixels**, and nothing else: no teal anywhere.
- **The ground:** all **154 empty cells** equal `BatMapList` image 15 pixel for pixel, as research found for B2 (`010c9c2`). The lime of the Numidian sprites' background is the ground tile's base lime, but it has no grass pattern, so each Numidian unit shows as a flat lime square with a black outline and a grey fill.
- **The same after one End turn:** the second phase's save and block give the same 14 cells and 154 ground cells, all exact. Its screenshot is byte-identical to the placement one, so this is one distinct image.

## Evidence

- **Data:** `runs/experiments/data/run-exp-battle-numidia-colour/`: `draw_numidia_battle.py`, `draw-20261009-141127.jsonl`, `check_battle_recolour.py`, `numidia_draw_check.json`, `SAVES.sha256`, `README.md`.
- **Release** [`run-exp-battle-numidia-colour`](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-battle-numidia-colour): `20261009-141127_NUM_start.SAV` (the L1 start), `20261009-141127_NUM_placement.SAV` and `20261009-141127_NUM_placement_window.png`, `20261009-141127_NUM_after_end_turn_1.SAV` and `…_window.png`, and the `BATTLE*.SAV` the lab build wrote.
- **Source save:** `FLD-RG_0743_rome_army0_at_86_28.SAV` (SHA-256 `39edecd1…`, release `run-exp-battle-sweep`).
- **Templates:** `TBattleMap_BatMapList.bmp` (release `run-exp-unit-icon-resources`).

## Not established

- **A natural Numidian battle** (no edit). The sprites follow only the army's owner and the nation's three dwords (`2026-10-09-battle-map-units-use-the-nation-recolour.md`), so nothing else is expected to differ `[derived]`.
- **The rest of the battle:** it was not played out. The process was killed after the second phase.
- **The desktop original.**
