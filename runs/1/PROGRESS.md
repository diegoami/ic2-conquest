# Run 1 progress

- **Status: finished.** All 24 turns played (0720–0743); the last save is `AUTO0744.SAV` (269 BC Spring week 1) in `/home/user/ic2-conquest/artifacts/run-1/269BC-spring/`, copied to `gdrive:IC2/artifacts/run-1`. Debrief: `runs/1/debrief.md`. Checkpoints (all posted on issue #144): `runs/1/checkpoints/0726.md`, `0732.md`, `0737-0738.md`, `0744.md`.
- **Replaying a turn:** `python3 runs/1/bot/turn.py <turn> runs/1/turns/<turn>.orders.json` plays turn `<turn>` from `AUTO<turn>.SAV` with seed `12345 + turn − 720` (new artifact names, never overwrites). Turn files: `runs/1/bot/batchmd.py <notes>` (sections `=== <turn>`). Planning: `view.py <turn>`, `whatif.py`, `dist.py`, `reach.py`, `budget.py`.
- **Old game-folder autosaves** (run 0) were moved to `~/ic2-work/prefix/drive_c/IC2/superseded-20261022-145602/` before turn 1.
- **Open problems:** the supply order does not check for an adjacent own city first (0742, three futile attempts); `goto` sometimes stops a tile short (0742) or needs a second attempt (0730). No release (artifacts are local and on Drive).
