# Run 0 progress (resume notes)

- **Last completed turn:** 0731 → `AUTO0732.SAV` (270 BC Autumn week 1), in `/home/user/ic2-conquest/artifacts/run-0/270BC-autumn/`. Checkpoints 1 (0726) and 2 (0732) posted on issue #1 (`runs/0/checkpoints/`).
- **How to resume:** `python3 runs/0/bot/turn.py <turn> runs/0/turns/<turn>.orders.json` plays turn `<turn>` from `AUTO<turn>.SAV` (artifacts) with seed `12345 + turn − 720`; turn files come from `runs/0/bot/batchmd.py <notes>` (sections `=== <turn>`). `runs/0/bot/look.py <save> [nations]` and `runs/0/bot/reach.py <save> <army> [nations]` are the planning views. Army ids change when armies merge: read them from each save.
- **Next turn (0732):** army 0 (55,192 at (97,32)) walks toward Mediolanum (stand (90,28)) to meet Gaul's 16,500 army coming east, and fights it first if adjacent; retry trade with Galatia/Dacia.
- **Open problems:** refusal boxes OCR empty; the planner's path cost undercounts some river steps (keep a 2-move margin before a siege). Carthage and Illyria are at war with Rome since 0728/0731.
