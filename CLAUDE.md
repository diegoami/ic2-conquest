# ic2-conquest: rules for Claude sessions

Purpose: find strategies that dominate the map in the original *Imperial Conquest 2* (1996) and prove it with per-turn saves, logs and plans; secondarily, exercise every mechanic (`coverage.md`). Read `README.md`, then the active strategy in `strategies/`.

## Hard rules

1. **No game file in git**: no EXE, DAT, SAV, screenshot or video. Git holds text only: code, plans, logs, metrics. A run's saves, screenshots and videos go in a GitHub release `run-<id>` of this repository and are cited by bare filename.
   - Releases: the session's GitHub proxy refuses release calls ("Creating, editing, or deleting releases is not permitted for this session type"; tested again 2026-09-29 with `IC2_RELEASE_TOKEN`: HTTP 403 from the proxy). Use `IC2_RELEASE_TOKEN` only for release calls, as `Authorization: Bearer`; never print, log or write it. While the proxy refuses, keep a run's artifacts in the gitignored `artifacts/run-<id>/`, one folder per season, and at the end of the run post the exact `gh release create run-<id> …` command for the player.
2. **Never write to another repository.** Rule discoveries go to `findings/` here, in the research repo's report format, with the saves cited. The player promotes them.
3. **The player's words in a strategy file are never edited.** The bot writes only in its own sections ("Bot validation", "Trials").
4. **No run starts before the player approves it** in the run's GitHub issue.
5. **Every claim of progress cites a save**: run, file and turn (e.g. "run 0, `AUTO0731.SAV`, turn 0731").

## Environment

- `setup/setup.sh` (root, Ubuntu 24.04): installs Wine (32-bit prefix), Xvfb, xdotool, imagemagick, ffmpeg, tesseract; clones the pinned research and fixtures repos (`setup/pins.txt`) under `/home/user/diegoami`; builds the executables into `$IC2_WORK/build` and the game folder `$IC2_WORK/prefix/drive_c/IC2` (`IC2_WORK` defaults to `~/ic2-work`, outside git).
- The bot plays **`Imperial Conquest 2 fast rollingsave seed.exe`**: instant battles; every human turn writes `AUTOnnnn.SAV` + an `AUTOSAVE.LOG` line; `RandSeed` comes from `SEED.TXT` beside the exe at **program start and New Game only** (loading does not reseed: `findings/2026-09-29-loading-a-save-does-not-reseed.md`). So a repeatable turn = restart the game with the seed, open the save, issue the orders (`Game.load`).
- `nnnn` = `(300 − yearBC) × 24 + season × 6 + (week − 1) / 2`; 0720 = 270 BC Spring week 1.

## Code map

- `harness/driver.py`: the order driver (`Game`): process control, read-only game memory via `/proc/<pid>/mem`, menus/toolbar, dialogs, tile targeting, orders. Layouts in `coverage.md` §2.
- `state/sav.py`: SAV → dict/JSON (layout: `docs/sav-layout-notes.md`); `state/metrics.py`: `runs/<id>/metrics.csv`, `armies.csv`, `state/nnnn.json`.
- `planner/path.py`: army paths (DAT terrain costs).
- `patches/seed_patch.py`: the seed option on top of the fixtures' `patch_exe.py`.
- `tests/test_orders.py`: each order issued headless and checked on the save diff; `tests/results.md`.
- `docs/rules-digest.md`: the researched rules, with sources. `findings/`: drafts for the research repo.

## Driver pitfalls (Wine, no window manager)

Hover before clicking; prefer toolbar buttons to menus; reset menu state before a menu; the first click into an inactive window may only activate it, so verify every order's effect (memory or save) and retry at most twice; never click End turn twice unless the first click provably did nothing.

## Runs

A run is `runs/<id>/`: `turns/nnnn.md` (intent, orders, expected vs actual, surprises), `metrics.csv`, `armies.csv`, `checkpoints/`, `debrief.md`, `viewer.md`; its binary artifacts (saves, screenshots, per-season video) go to release `run-<id>` or `artifacts/run-<id>/`. One GitHub issue per run holds the conversation: proposal before, checkpoint comments during, debrief after.
