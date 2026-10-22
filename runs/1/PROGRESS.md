# Run 1 progress

- **Status: running.** Rome, `strategies/rome-v2.md` (k = 3), approved on issue #144 (2026-10-22). Branch `run/1`.
- **Last turn done:** 0720 → `AUTO0721.SAV` (`/home/user/ic2-conquest/artifacts/run-1/270BC-spring/`).
- **Next plan:** 0721 recruit HI ×2 at Arretium; armies 0 and 1 join at (103,36); 0722 attack Gaul's army 9 if the joined ratio is ≥ 3; mobilise the southern army at Rome from the starting queue by 0724–0726 (P12).
- **Playing a turn:** `python3 runs/1/bot/turn.py <turn> runs/1/turns/<turn>.orders.json` (loads `AUTO<turn>.SAV` from `artifacts/run-1/<season>/`, seed `12345 + turn − 720`; never overwrites). Turn files: `runs/1/bot/turnmd.py <turn> <notes>`. Planning: `look.py`, `reach.py`, `budget.py` (debt floor and next quarter's bill).
- **Old game-folder autosaves** (run 0) were moved to `~/ic2-work/prefix/drive_c/IC2/superseded-20261022-145602/` before turn 1.
- **Problems:** none yet.
