# run-exp-sav-aboard107: a natural embark, for the aboard-link invariants

The owner approved the run in the session on 2026-10-22; the proposal is in
[issue #107](https://github.com/diegoami/ic2-conquest/issues/107#issuecomment-6335008208).
Seed build `354d8265…532f`, seed 12345, headless Wine. Script:
`runs/experiments/sav-inert107/aboard.py`. Step log (memory dumps of army 0,
fleet 2 and two map cells): `aboard-20261022-071303.jsonl`. Receipt:
`invariants-aboard-20261022-071303.json`. Hashes: `SAVES.sha256`.

- **Embark.** Army 0 (101,45) embarked on fleet 2 (101,46) by a click.
  - The army moved to the fleet's tile, with cell −1 and moves 0.
  - The fleet now holds cargo index 0 and has moves 0.
  - The army's old tile went back to its terrain (2). The fleet's tile shows
    the fleet marker (owner + 316: 30 ships).
- **End turn.** The link survives. The tick gave the aboard army 9 moves and
  the fleet 25.
- **Invariants.** Both aboard links hold in both saves (2/2 each). The other
  invariants hold too.

Saves: `gdrive:IC2/artifacts/run-exp-sav-aboard107/` (`rclone check`: 2
matching); this container has no release token. To publish them, copy them
from Drive first, then:
`gh release create run-exp-sav-aboard107 artifacts/run-exp-sav-aboard107/*/*.SAV`
