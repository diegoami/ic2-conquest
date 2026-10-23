# Battle parity #157

Plan: `docs/proposals/battle-parity-investigation1355.md`.
Finding: `findings/2026-10-23-battle-general-later-pass-iteration1355.md`.
Runners: `runs/experiments/battle-parity157/`.

Reference restored at fixture6319802,17 files only. `reference-cgonly-v2-validation.json`
is the complete325draw/15wholeSAV gate. Earlier v1 collectors intentionally fail
the strict whole-log gate because they stop before five post-result draws; none
of their measurements was overwritten. Both v1 protocols match combat/boundaries.
The reference native comparator validates28 pass1 engagements and full movement
phases; version6 adds actual first-actor-order checks and full battle controls.

`owner-iteration-audit-v3.json` is the latest public scalar audit (v1/v2 retained). All owner original
inputs, hashes and full states/traces live privately under ignored artifacts.
Never run the generic archive walker on this experiment: it includes private
owner/runtime trees. `archive_public.py` has a strict explicit public-asset list.

First public batch: `reference-batch01.tar.gz`,1,419,660bytes,
SHA256 `5feaf72645a0d93eea1681368c6d9eea0b339892edcf1ff8902e01b1e9d07ddd`.
Drive file `1q-BM_9QjvpvLDCu-TYSi6wm4xuY_J6Uh`, folder
`173YEC10JxoJDJpQ8P4xUbiZbf50-rKjm` (IC2/artifacts/run-exp-battle-parity157).
Upload metadata readback confirms size and parent; archive members/hashes verified
locally, no remote-download digest verification claimed. Original EXE/DAT and
runtime/prefix excluded. No release token was assumed or credential file read.
Owner release fallback, if desired:

```bash
gh release create run-exp-battle-parity157 artifacts/run-exp-battle-parity157/reference-batch01.tar.gz --title 'Battle parity investigation (#157)' --notes 'Evidence and limitations: findings/2026-10-23-battle-general-later-pass-iteration1355.md'
```

Synthetic pilot: `pilot-manifest-v1.json` declares12 cases before running; actual
original starts then native replay from measured entry. Not fresh-new-game or
JSON/export-conversion coverage. `pilot.py run` resumes completed cases and
retains failures for review. `audit_pilot.py` produces a new numbered receipt,
compares complete slots/grid/counter/RNG, combat draws and available boundaries.
Native iteration alternatives are diagnostic controls, not a production patch.

Expanded semantic observer has isolated B11 configuration, full-counter snapshots
and guarded movement-step/routine-exit markers. CPU receipt `semantic-cpu-v1.json`
and build `semantic-build-v1.json` are followed by passing reference and owner
live inertness gates. Reference normalized logs/comparison-v2 are tracked. Owner
complete346-action interleaving,498draw equality and historical48969/counter21
assumption control are summarized only in the safe audit. All private logs and
inputs remain private. Individual placement-write/silent-target-write order and
native strategic writeback are not claimed.

Pilot `pilot-audit-v2.json`:12/12 complete,1528combat draws and225boundaries;
production and each diagnostic alternative match original measured results in
these small fixtures. Coverage is explicitly bounded. Second public bundle is
`pilot-semantic-batch02.tar.gz`,7,038,349bytes,SHA256
`e0f6d4976054a3ccdf3144c2d9eb85cd1cb797c1e46250a870eb414395a238d8`.
It contains synthetic input SAVs, completed original pilot/reference semantic
boundary/post/reopen SAVs, screenshots and raw reference state buffer; no owner
files/EXE/DAT/prefix. Both bundles reside in the same Drive experiment folder.
