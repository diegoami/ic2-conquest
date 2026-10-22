# run-exp-fleet-bill: is a fleet under construction billed at the quarter?

Owner-approved run, 2026-10-22 (open item 12 of research PR #57's consolidation of the #133 manual contradictions).
Runner: `runs/experiments/fleetbill/run.py`. Log: `run-20261022-104846.jsonl`. Saves: `SAVES.sha256`
(binaries: `artifacts/run-exp-fleet-bill/`, copied to Drive `IC2/artifacts/run-exp-fleet-bill/`; the source save is
also in Drive `IC2/artifacts/run-exp-manual133/saves/`).

Result: branch B (50-ship fleet ordered) ends the quarter exactly 500 talents (its build cost) below branch A; the
quarter changed both treasuries by +23. No 3 × 50 = 150 upkeep was charged. See
`findings/2026-10-22-fleet-under-construction-not-billed.md`.

The driver also wrote its environment record (Wine, exe and Xvfb versions) to `runs/experiments/data/run-exp-fleetbill/environment.jsonl`, a folder named after the runner directory; it is kept there.
