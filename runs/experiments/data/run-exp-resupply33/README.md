# Immutable research33 evidence

See [the finding](../../../../findings/2026-10-17-hostile-control-recruitment-treasury-ledger.md) for exact case/save names, source pins, ledger and scope. Binary saves: [run-exp-resupply33](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-resupply33); original inputs: [run-exp-resupply31](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-resupply31).

- `decoded-initial-20261017.json`: retained raw input/loaded/post parsing, hashes and field differences. Verbose complete decoded state, retained as measured.
- `ledger-initial-20261017.json`: raw queued recruits and pinned DAT-price arithmetic. Earlier rejected zero-byte empty-slot assumption retained in `ledger-initial-failure.txt` and its source snapshot.
- `source-audit-initial.txt`, `source-provenance-initial.json`, `recruitment-disassembly-20261017.txt`, `ui-size-source-20261017.txt`: original source/instruction provenance, numbered full function extracts, UI exception.
- `replay-*.jsonl`, `environment.jsonl`: three fresh unchanged-original Wine runs; each loaded/post whole-save identity checked against the retained case. `runtime-preclick-*.json`: fresh memory read before End-turn click, not phase entry.
- `phases-*-byte-audit-20261017.json`: canonical three unmodified original-x86 four-phase controls. All debit writes recorded; raw nation UI mismatch remains false in comparison. `phases-control-seed12345-20261017.json` is the earlier deliberately supplied seed control with failed endpoint agreement. Earlier land runtime/validated outputs retain the narrower comparison and discovery of the UI exception.
- `summary-canonical-20261017.json`: joins the above, exact debits/phase changes and zero residuals. `validation-20261017-1031.json`: successful offline assertions from `runs/experiments/resupply33/validate.py`.
- `SAVES.sha256`: nine fresh saves. `release-sync-*.json` records upload, `release-verification-20261017-1031.json` independently matches all nine local hashes to published release asset digests.

Offline reproduction (no game): `python3 runs/experiments/resupply33/validate.py --output runs/experiments/data/run-exp-resupply33/validation-UNIQUE.json`. Outputs are opened exclusively; choose a fresh filename. This checks retained captures, not new Wine behavior.

Original-x86 reproduction requires Unicorn and the pinned EXE/DAT in the task layout, retained loaded/post saves and runtime JSON. Example from the worktree:

```bash
python3 runs/experiments/resupply33/phases.py --loaded /home/diego/projects/ic2-work/resupply31/artifacts/land-war-20261017-083008-11228-loaded.SAV --post /home/diego/projects/ic2-work/resupply31/artifacts/land-war-20261017-083008-11228-post.SAV --seed 4169717509 --runtime runs/experiments/data/run-exp-resupply33/runtime-preclick-20261017-101820-85339.json --all-phases --output runs/experiments/data/run-exp-resupply33/phases-land-UNIQUE.json
```

`phases.py` resolves EXE/DAT from sibling task `resupply31/wine-aboard/prefix/drive_c/IC2` relative to the recovery layout `/home/diego/projects/ic2-work/resupply33/conquest`. Their hashes are asserted before execution. `decode.py`/`ledger.py` use the same retained task layout. Wine replay is separately authorized original-game work: `replay.py` preserves each new save with a unique name; it is not needed to validate the tracked ledger. No matrix rerun is requested. Every measured failure/control and binary artifact is retained.
