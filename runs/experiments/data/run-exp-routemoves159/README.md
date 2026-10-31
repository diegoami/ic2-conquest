# run-exp-routemoves159: the army's moves at the original's ferry-route write (research #159, remake #1652)

Owner request 2026-10-31 (the zero-move proof first). Finding: `findings/2026-10-31-ferry-route-written-at-zero-moves159.md`.

- `orig-v1/`: `IC2_FLEET_HOOK=routemoves_hook IC2_HOOK_LOG=routemoves python3 -m difftest.probes.fleetphase_hook_run <out> 5
  S06_Gaul_AUTO0720.SAV S08_Celtiberia_AUTO0720.SAV S13_armenia_AUTO0720.SAV` (seed 12345).
  - `<start>-routemoves.jsonl`: kinds `dba8` (every AI march, with its caller and the army's moves) and `route-write`
    (every D9A8 route write, with the army's moves at the write), plus `fleet`/`hunt` (the fleet phase's inputs).
  - `<start>/inert.json`: the hooked autosaves against the plain build's, 15/15 identical.
- The saves are in release `run-exp-routemoves159`, with hashes in `SAVES.sha256`.
