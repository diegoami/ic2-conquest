# Navigation #187 evidence and reproduction

Start with `findings/2026-10-24-army-navigation-rule187.md` and
`docs/navigation187-rule.md`. This package changes no production game code.
The interpreted data and public scalar ledgers are tracked in
`runs/experiments/data/run-exp-navigation187/`.

`model.py` needs only Python's standard library, those interpreted tables and a
`cell(x,y)` callback. It imports neither original binaries nor private state.
`public-test-matrix-v1.json` describes 15 portable semantic fixtures for Main.
Unsupported isolated stack-dependent cases raise `OriginalUndefined`.

To audit the retained results without running the game, from the repository root:

```bash
python3 runs/experiments/navigation187/audit.py --version review-UNIQUE
```

Choose a new version every time. This writes a new summary with exclusive file
creation and checks retained ledgers; it does not rerun original instructions.
The recorded publication audit is `summary-v3.json` / `audit-execution-v3.log`.

Original-instruction replay requires Unicorn and the separately retained assets
whose hashes/paths are pinned in `core.py` and `source-pin-v1.json`: original
EXE, DAT, listing, generated Rome snapshot, and the prior generated snapshots
for extraction/topology controls. These assets are not included in Git.
The recorded runtime is `/home/diego/.local/bin/python3.12` with Unicorn.

For a new **authorized** replay, set a unique `NAV187_REPLAY_TAG` and execute
`extract.py`, `controls.py`, `branches.py`, `caller.py`, `caller_full.py`,
`topology.py`, then `advanced.py` from this directory. Each is invoked separately
with the same environment variable. Public outputs go into a new tagged
subdirectory of the tracked data directory; RAM/traces go into a corresponding
private artifacts directory. Existing outputs cannot be overwritten. Inspect,
archive and commit the new public outputs after each batch. No live game or RNG
is needed by those bounded original-instruction controls.

`private_regression.py`, `PrivateWalk.csproj` and `Program.cs` are the final
conditional #1388 check. They additionally require retained private owner
material and the pinned native build. They are not part of the public synthetic
replay; never publish their inputs, RAM, complete traces or private hashes.
The public native v2 audit supersedes v1's narrower identity gates; both remain.
No owner material or raw original asset is uploaded to a public release.

Keep the caller-specific stop condition: the normal F31C context is covered,
other original caller histories are not universally resolved. Promotion through
Research is required before Main uses this rule to change behavior.
