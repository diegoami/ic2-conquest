# run-exp-new-providers: wiring alibaba-token-plan and minimax into the review scripts (PR #64)

Not a game experiment: the tracked evidence for the provider wiring the owner asked for on 2026-10-06.

- `probes.v1.txt`: each new model id probed once (`opencode run -m <id> [--variant v] "Reply with just: ok"`,
  one small billed call), 2026-10-06, with wall-clock times. Verbatim task output; every id answered `ok`.
- `self-test.v1.txt`: `python3 scripts/external_review.py --self-test` after the round-1 fixes (52/52), run 2026-10-06.

The variants each id offers were read from `opencode models --verbose` (2026-10-06) and are recorded in
`scripts/opencode_watched.py`'s `OFFERS` table and in `docs/environment.md`'s model table.
