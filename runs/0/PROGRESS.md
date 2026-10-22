# Run 0 progress (resume notes)

- **Last completed turn:** 0723 → `AUTO0724.SAV` (270 BC Spring week 9), in `/home/user/ic2-conquest/artifacts/run-0/270BC-spring/`.
- **How to resume:** `python3 runs/0/bot/turn.py <turn> runs/0/turns/<turn>.orders.json` plays turn `<turn>` from `AUTO<turn>.SAV` (artifacts) with seed `12345 + turn − 720`, then `python3 runs/0/bot/turnmd.py <turn> <notes.md>` writes the turn file. `runs/0/bot/look.py <save>` and `runs/0/bot/reach.py <save> <army>` are the planning views.
- **Next turn (0724):** mobilize HI 4,000 + HC 1,000 at Rome (state 24 = average) into a second army and supply it from Rome; army 0 (30,087 HI/HC at (95,26), supplies 192/301) besieges the next Gallic city in reach (Verona 25,550 or Altinum 19,000) and resupplies from an own city when adjacent (P2).
- **Open problems:** refusal boxes of International Relations come back with empty OCR (the refusal is still seen from the relation value). Gaul has 127,000 troops queued (mobilization 100) at Nimes: a new Gallic army can appear in the west.
