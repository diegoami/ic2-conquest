# Machine move: checks on the new computer (2026-10-10)

New computer: Ubuntu 26.04 (WSL), Wine 10.0 (old: 9.0), ImageMagick 7.1.2-18 (old: 6.9), tesseract 5.5.0 (old: 5.3), ffmpeg 8.0 (old: 6.1),
python3 3.14.4 with apt capstone 5.0.7, unicorn 2.1.4, pefile 2024.8.26 (old: 3.12). Binaries (screenshots, the prefix's registry before the
first Wine 10 start) are in `artifacts/run-exp-machine-move/` and release `run-exp-machine-move`, hashes in `SAVES.sha256`.

## 1. Wine smoke test: pass

- `smoke.py --fixtures` (`smoke.jsonl`): `saves/run0-start-AUTO0720-seed12345.SAV` with seed 12345 loaded on the **first** start in 22.6 s
  (`S 0000012345`, box "@ Bithynia wants to trade with Rome."), then all **38/38** `T_*.SAV` fixtures opened in the same process (9-10 s each).
- **Wine 10 updated the old prefix silently** at the first start (no dialog, no extra start delay beyond the 22.6 s): `.update-timestamp`
  1711946478 -> 1774378103; `system.reg` 635 changed lines; `user.reg` 20, of which 18 are new `Software\Wine\Fonts\External Fonts` entries for the
  **Liberation** fonts (Mono, Sans, Sans Narrow, Serif) and 2 are the host name. The registry before the update is kept in
  `artifacts/run-exp-machine-move/prefix-before/`.

## 2. Version differences

| Tool | Result | Evidence |
|---|---|---|
| Wine 10 + its font set | **differs: text rendering.** The Information panel's text uses a narrower font (the Liberation fonts now registered). Same words, same lines; long lines no longer clip ("damaged in a storm." now shows its full stop). Window title bars and scroll-bar arrows differ by a few hundred pixels. **Map tiles, city markers and the toolbar icons are identical.** | `shot_compare.py`: `1_rome_270_winter_11.sav`, seed 12345, against the old `b0-normal-20261004-081149-01-loaded.png` (run-exp-battle-probe): same size (1280x1024) and window geometry; 53,375 pixels differ: Information panel 51,778 (22.6 % of it), menu/toolbar strip 1,052 (all in the 322x11 menu-text band), unit map 477 (title text and two 15x15 scroll arrows), area map 85 (title text) |
| tesseract 5.5 | **popup OCR identical; Information-panel OCR worse with the new font.** | "@ Bithynia wants to trade with Rome." read exactly as on the old computer (2,178 earlier log lines). On the Information panel crop, about 4 wrong lines on the old image (`lllyria`, `Week 3.`, `2708`) against about 15 on the new (`2708C` twice, `lyri`, `Seleucia`, `Week §`, `trom`, dropped full stops, a leading `‘`): `infoA.txt` (old) vs `infoN.txt` (new). Same tesseract 5.5 on both images, so the font, not tesseract, causes it |
| ImageMagick 7 | **no difference.** `convert` and `import` still exist, print no deprecation warning, and give the same bytes as `magick` | `analyse_colours.py` (run-exp-owner-colours) and `analyse_cities.py` (run-exp-city-marker-colours) re-run on their saved screenshots reproduce their tracked JSON exactly |
| ffmpeg 8 | **not exercised:** no script in the repo calls ffmpeg (only `setup/setup.sh` installs it and docs mention per-season video); no run with video is going | – |

## 3. Python 3.14: pass

- The harness (`smoke.py`, `shot_compare.py`), `state/sav.py --summary`, and the offline tests run on the system python3 3.14: `test_ai_hook` and
  `test_battle_hook_caves` (unicorn + capstone), `test_battle_b5_b8` 7, `test_battle_exchange`, `test_battle_hook_build`, `test_driver_battle`
  32, `test_end_turn_reclick` 14, `test_sea_path` 6, `test_reviewer_prompt`, `external_review.py --self-test`: all pass. Nothing needs 3.12.
- `tests/test_info_window.py`: 2 failures, not Python: `call_extraction` and `coverage_zero_unaccounted` read
  `/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt`, a Ghidra export on the old computer's Windows side that was not moved.

## 4. Which fonts (2026-10-10, follow-up)

- **What the game asks for** (`wine10_font_trace.txt`, `WINEDEBUG=+font`, game start only): "MS Sans Serif" (menus, dialogs: Wine replaces it with
  its own Tahoma, the same `Replacements` entry in the old and the new prefix), "System" (Wine's `vgasys.fon`), and for the Information panel
  **"Book Antiqua"**, height -13, a Windows serif font that neither computer has. Wine picks the best match from the fonts it knows.
- **New computer:** "Book Antiqua" -> **Liberation Sans** (trace: `Chosen: L"Liberation Sans"`).
- **Old computer:** the old prefix's `External Fonts` list (the fonts its host had) has DejaVu, URW (Nimbus), Ubuntu, Droid and Noto, **no
  Liberation**. The old panel's line "Macedonia declares war on Greece." measures **211 x 10 px**; rendered at the same size **DejaVu Sans is
  211 x 10** (Tahoma 192, Nimbus Sans 195, Ubuntu 192). The new panel's 195 x 9 equals Liberation Sans' 195 x 9. So the old computer drew the
  panel in **DejaVu Sans**, and the change comes from the host's fonts (`fonts-liberation` installed here), not from Wine 9 vs 10.

## 5. The font experiment (2026-10-10): the old font set reproduces the old rendering

The owner ran `font-experiment.sh remove` (removes `fonts-liberation`, `fonts-liberation-sans-narrow`; installs `fonts-wine`; `fc-list`: 0
Liberation). The owner also confirmed the old computer has `fonts-wine` and no Liberation fonts (`fc-list`: 0).
- **Font:** on a prefix copy whose registry is the pre-Wine-10 backup (`~/ic2-work-fonttest`), Wine 10 now maps "Book Antiqua" to **DejaVu
  Sans** (trace: `Chosen: L"DejaVu Sans"`), and the test line measures 211 x 10, as on the old computer.
- **Pixels** (`shot_compare.jsonl`, `shot-winter11-20261010-193356.png` against the old `b0-normal-20261004-081149-01-loaded.png`): 30,358 pixels
  differ (was 53,375), all faint anti-aliasing: with a 5 % tolerance the area map and the unit map differ in 0 pixels, the menu/toolbar strip
  in 12, the Information panel in 4 (with 20 %: 0 everywhere). Same glyphs, same positions; only edge shading differs (Wine 10 / FreeType).
- **OCR** of the Information panel (`infoF.txt`): the same text as the old computer's except 2 characters (`lllyria` -> `tllyria`; `and:` ->
  `and;`, the latter now correct). With Liberation it was about 15 wrong lines.
- **The main prefix needs no copy:** `~/ic2-work/prefix` dropped its Liberation entries by itself at the next start and its screenshot is
  pixel-identical (0 differing pixels) to the copy's (`shot-winter11-20261010-193538.png`).
- **Conclusion:** with the old font set, Wine 10 renders like the old computer up to anti-aliasing. Pixel comparisons of text against old
  screenshots need a small tolerance (5 % covers maps and menus; 20 % covers everything); exact-byte comparisons of text areas do not carry over.

## 6. Replay check (2026-10-10, Wine 10 with the old font set): game state identical

- **Orders, no end of turn** (`run-exp-supply-transfer-clamps/supply_transfer.py P1`, log `supply_transfer-P1-20261010-193650.jsonl` there): the
  two saves are **byte-identical** to the old computer's (`P1_*_alone.SAV` `bb848892b3aa7508…`, `P1_*_split.SAV` `f0921d93f353df78…`, both
  equal to the two old runs), and so are its three screenshots (`62a33590f3d8…`, `dc8e1077e3cd…`, `119a8a57b6f6…`, each equal to one of the
  old runs').
- **New Game + two End turns with the AI** (`civ_sweep_replay.py 0`, a copy of `runs/experiments/civ-sweep/sweep.py` that writes to
  `artifacts/run-exp-machine-move/civ-sweep-replay/`; Rome, seed 12345): `S00_Rome_AUTO0720/0721/0722.SAV` differ from the old
  `run-exp-civ-sweep` saves in **4 bytes each, all in the trailer's main-window geometry** (UI state, `docs/sav-layout-notes.md` §8): old
  `(-4, -4, 281, 650)`, new `(-4, -4, 979, 1280)`. Every game byte is the same. The sweep's record differs only in `view_origin_mem[0]`
  (unit-map scroll column 107 old, 97 new), a consequence of the larger window. All sweep steps passed.
- **Consequence:** Wine 10 opens the main window larger after New Game (1280 x 979 instead of 650 x 281). A save comparison across the two
  computers must mask the trailer's 8 geometry bytes (offsets 46-53); the driver's targeting reads the view origin from memory and coped.
