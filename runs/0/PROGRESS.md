# Run 0 progress

- **Status: finished.** All 24 turns played (0720-0743); the last save is `AUTO0744.SAV` (269 BC Spring week 1) in `/home/user/ic2-conquest/artifacts/run-0/269BC-spring/`, copied to `gdrive:IC2/artifacts/run-0`. Debrief: `runs/0/debrief.md`. Checkpoints (all posted on issue #1): `runs/0/checkpoints/0726.md`, `0732.md`, `0737-0738.md`, `0744.md`.
- **Replaying a turn:** `python3 runs/0/bot/turn.py <turn> runs/0/turns/<turn>.orders.json` plays turn `<turn>` from `AUTO<turn>.SAV` with seed `12345 + turn − 720` (it writes new artifact names and never overwrites). Turn files come from `runs/0/bot/batchmd.py <notes>`; `runs/0/bot/look.py` and `reach.py` are the planning views.
- **Open problems:** refusal boxes OCR empty; the planner undercounts some river walks by one move; no release (artifacts are local and on Drive).
- **Release command for the player** (the session cannot create releases): `gh release create run-0 /home/user/ic2-conquest/artifacts/run-0/*/* --repo diegoami/ic2-conquest --title "Run 0 (Rome pilot)" --notes "Autosaves, shots and logs of run 0; hashes in runs/0/SAVES.sha256"`
