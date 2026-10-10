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
