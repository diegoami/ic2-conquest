# run-exp-battle-numidia-colour

Does the battle map recolour unit sprites like the unit map, so that Numidia's units are grey there too? (research `[derived]` in
`findings/2026-10-09-unit-icon-recolour-and-nation-glyphs.md`; HANDOVER 2026-10-09 optional item 3.) Static read plus an offline check
against existing Wine screenshots; no new game run, no new saves or screenshots.

- `xrefs.py` → `xrefs.txt`: every `call 0x44a6c8` and every operand on the recolour dwords in `Imperial Conquest 2.exe` (capstone 5.0.7, read-only).
- `disasm_range.py`: linear sweep of a VA range; `battlemap_sprites_436fb4.asm` = the battle form's sprite build (0x436fb4-0x437196).
- `check_battle_recolour.py` → `battle_recolour_check.json`: BatMapList templates 0-14 (from `artifacts/run-exp-unit-icon-resources/TBattleMap_BatMapList.bmp`,
  release `run-exp-unit-icon-resources`) recoloured with the save's dwords of the attacker's and the defender's owner, compared with every
  occupied cell of B2's three window screenshots (release `run-exp-battle-sweep`; save and screenshot SHA-256 already in
  `../run-exp-battle-sweep/SAVES.sha256`). `b2_placement_window.png` and `b2_after_end_turn_1_window.png` are byte-identical (same hash), so
  there are 2 distinct images for 3 saves.
- Exe SHA-256 `9d753d5de78801f2…` (full hash in `../run-exp-unit-icon-resources/imagelists.json`).

## A Rome v Numidia battle drawn in Wine (2026-10-09, the player's request)

- `draw_numidia_battle.py` → `draw-20261009-141127.jsonl`: an L1 edit of `FLD-RG_0743_rome_army0_at_86_28.SAV` (`stage.edit`: army 10 owner → 5,
  relation Rome-Numidia → 3, the Rome-Gaul value; positions and units untouched), lab build s1. Rome's army 0 attacks; at the placement phase
  and after one End turn: a window screenshot, File > Save As and the live battle block. The process is then killed (the battle is not played out).
- `check_battle_recolour.py` (now takes other pairs, and checks the empty cells against BatMapList image 15) → `numidia_draw_check.json`.
- Binaries: release `run-exp-battle-numidia-colour` (`20261009-141127_*`), SHA-256 appended to `SAVES.sha256`. The two window screenshots
  are byte-identical (the screen does not change across the first End turn), so this is one distinct image.
