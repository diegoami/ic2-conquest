# run-exp-sav-fleetmoves107: does a new fleet keep its index's leftover moves?

The owner approved the run in the session on 2026-10-22; the proposal is in
[issue #107](https://github.com/diegoami/ic2-conquest/issues/107#issuecomment-6329381290).
Setup as `run-exp-sav-inert107`: seed build `354d8265…532f`, seed 12345,
headless Wine. Script: `runs/experiments/sav-inert107/fleetmoves.py`. The step
logs (with fleet-table memory dumps) are `T4-*.jsonl` and `T5-*.jsonl`; the
receipt is `analysis-T4-T5-20261022.json` and the hashes are in
`SAVES.sha256`.

- **T4, natural path** (`saves/fleet-split-antium-0734.SAV`).
  - Scuttle fleet 2 tombstones it (owner −1).
  - At End turn, compaction moves the last fleet (5) into slot 2, and the
    count drops to 5. Index 5, now past the count, keeps a full copy of the
    old fleet 5. The copy was taken before the round tick: its moves are 0
    and condition 97, while the live copy has 31 and 96.
  - Build fleet (10 ships) orders the new fleet at index 5. It writes owner,
    countdown 24, ships, city and army, and keeps the copy's x,y (101,47),
    route (0;0), moves, supplies, money and cell. Those leftovers are in the
    saved record.
  - The next tick sets route_x to −1.
- **T5, direct effect.** A crafted copy gives fleet 3 (under construction) to
  Rome with countdown 2 and moves 17; the control holds moves 0. After End
  turn the fleet has launched (countdown −1, placed at (219,55), supplies 50,
  condition 100). Its moves are **17** in memory and in the autosave; the
  control has 0.

**Conclusion.** A new fleet keeps the leftover moves of its table index
through launch until the following tick. In T4 the leftover was 0, because
compaction copies before the tick refreshes moves. A non-zero leftover needs
the moved fleet to have had moves at compaction time. Whether the owner can
spend leftover moves on the launch turn was not exercised.

Saves: `gdrive:IC2/artifacts/run-exp-sav-fleetmoves107/` (`rclone check`: 7
matching). No release token is set in this container. To publish them:
`gh release create run-exp-sav-fleetmoves107 artifacts/run-exp-sav-fleetmoves107/*/*.SAV`
(copy them from Drive first).
