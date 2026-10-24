# #187 garrison and mercenary caller follow-up

Finding: `findings/2026-10-24-garrison-mercenary-caller-guards187.md`.
Promoted by Research PR73 at `2420f67295e39d3a37ce4ff4f7adf242822fe1cb`;
canonical report: `docs/reports/2026-10-24-garrison-mercenary-caller-guards187.md`
in imperial-conquest-2-research. Production behavior and Main scope/labels unchanged.

Authoritative audit: `summary-v3.json`, `paired-inputs-v3.json`,
`observer-identity-v3.json`, `verification-execution-v3.log`. Results:
`controls-v1.json` (24 isolated callers), `parent-controls-v1.json` (24 full
F31C calls), `history-controls-v1.json` (32 histories), `progress-controls-v1.json`
(8 progress-then-block histories). These are 88 controls, not games. All complete
with zero original RNG calls. Unobserved reruns match every complete game-RAM
and 64-KiB stack block. Twenty offer pairs differ only at signed WORD49DA18.

Root callers leave the guard uninitialized. Actual F31C mercenary entry inherits
EE60's exhausted loop counter0. Ordinary no-movement destination/garrison history
inherits coordinateY; a refused nested mercenary route can instead pass−1 to
garrison. Both garrison call sites are covered. Negativity suppresses cleanup/
recursion, not the initial direct walk. Progress controls preserve the original
unconditional extra decrement, including observed signed terminal budget−1.

## Reproduction and privacy

Pinned original EXE/listing/generated reference inputs are required; see
`source-ledger-v1.json` and existing navigation187/core.py. The runtime used is
`/home/diego/.local/bin/python3.12` with Unicorn. No package installation or
live game is needed. Source runners are under `runs/experiments/navigation187-callers/`.

Run `controls.py`, `parent_controls.py`, `history_controls.py` and
`progress_controls.py`, each with a fresh `--version LABEL`. Never reuse an
existing label. `verify.py --version LABEL` audits the retained v1 input/control
ledgers and writes a new verification version. To validate newly named source
runs, select those input stems explicitly in a new task-owned verifier version.
Exclusive file creation prevents overwrites. Never delete an old save to rerun.

The retained raw artifacts are in the private task directory
`artifacts/run-exp-navigation187-callers/private/`, one folder per runner/version
and case: before/after RAM and projected SAV plus full stack/movement-write trace.
Private hash manifests are beside them. Per #187, these bytes, full traces and
private hashes stay out of Git and public comments; no public binary release or
owner-state archive is created. Only original asset identity pins and synthetic
scalar/provenance ledgers are published. No owner #1355/#1388 inputs were read.

The fixture changes world geometry for a diagnostic corridor. These projected
containers are not asserted to be a playable new scenario or original Save As.
No native caller implementation, full-turn comparison, tactical result, fresh
Windows game or universal contract for every interception/embarked caller.

## Preserved audit attempts

Verification v1's expected endpoint for an isolated clear garrison request was
wrong: eight moves reach108,40, not target−2. It failed before writing a summary;
the log remains. Corrected v2 checks80 controls. Expanded v3 checks all88 and20
paired inputs. No original measured output was overwritten. The proposal's
initial nearest/capital address labels were reversed; source-ledger-v1 records
capitalEC7D, nearestECD6, mercenaryE913. Semantic case names were correct.
