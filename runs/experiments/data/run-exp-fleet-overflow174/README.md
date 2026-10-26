# Fleet overflow174: retained controls and final audit

Bounded [finding](../../../../findings/2026-10-26-fleet-overflow-receiver 174.md),
conquest #174 / PR223. No production change, Research promotion or new game.

Original has 16 declared controls, 13 byte-distinct inputs; native has 15 dispatched
commands. All input projection and real World terrain gates pass. Use
`comparison-v2.json` / `native-v2.json`; v1 remains immutable. Post-board placement
queries are diagnostics using unchanged production helpers, not fixes.
`checkpoint-v1.json` preserves the old owner-requested pause and duplicate groups;
it is a historical receipt, not current completion status.

The final read-only `audit-v2.json` verifies 32 original RAM/SAV/JSON endpoints,
32 retained CPU/call/write traces,15 native full-state projections, 30 placement
queries,128 initial private hashes and 8 current public source/data blobs.
It corrects the preliminary 8-discrepancy label: 7 rows differ only in receiver
position/moves; `single-all-overflow` also differs in resources (original live
receiver 33 money/30 supply versus native 100/90). Original source 0 is a raw
tombstone retaining 67/60; no ABE0 raw compaction occurs in this call chain.
Keep native T216's conservation and atomic-refusal policies.

Classification totals remain 8 accepted discrepancies (5 distinct inputs), 3 exact
measured projection matches, 2 intended full-table refusals,1 raw-table/live-model
boundary, 1 non-equivalent human helper entry,1 helper-only no-land diagnostic.
The proposed union-neighborhood control has **not run**. Do not infer a measured
false no-safe-receiver refusal. No experiments were repeated during final audit.

## Files and provenance

- `original-v1-plan/index/baseline.json` and `original-v1_*.json`: declarations,
  recovered prior complete-RAM baseline and16 scalar original results. Two
  declared CPU variants each; no original Random call or seed change.
- `native-v2.json`, `native-v2_*.json`, `comparison-v2.json`: latest native
  dispatched results and preliminary classifications. Expected corrupt original
  outputs are compared directly, never reimported/normalized.
- `source-pins-v1.json`: Main pin4d70275aac4e155c0370a3ee23525cf34450a908,
  also observed current Main on2026-10-26, and 8 fetched public git blob SHAs.
- `audit-v2.json`, `audit-execution-v2.txt`: author's final retained-artifact
  audit. `audit-v1-failure.txt` preserves a tuple/JSON-array comparison failure.
- `native-build-v1/v2/v3.txt`, `native-execution-v1/v2.txt`: retained attempts.
  Build-v1's runner LoyaltyPercent typo failed; corrected to Loyalty. Build-v3
  completed 0 warnings/0 errors. It was committed while appending; completed suffix
  was preserved. No fresh build or command execution is claimed by audit.

Full states, original EXE/RAM/SAV, input hashes and raw traces are **private**.
Ignored local `artifacts/run-exp-fleet-overflow174/` contains
`private-original-v1/`, `private-native-v1/`, `private-native-v2/` and NEW private
`closure-v2.json` (255 files; excludes its own manifest). Initial
`private-original-v1/hashes.json` is preserved and all 128 entries verify.
Git push does not back these artifacts up. No public originals release/upload
or per-input hash publication is authorized by this packet. Projected SAVs are
diagnostic containers, not Original Save As outputs.

## Audit reproduction without repeating experiments

From repository root, with retained private inputs and dependencies available:

```bash
python3 runs/experiments/fleet-overflow174/audit.py --version UNIQUE
```

Choose a genuinely unused version; writes are exclusive. Audit imports read-only
projector helpers, checks stock original identity, disassembles relevant functions
into a NEW private file and verifies retained artifacts. It never constructs an
emulator, imports a native SAV through .NET, dispatches a command or launches a
game. New closure manifests stay private; publish only the safe scalar receipt.
Full serialized refusal equality is a retained dispatcher observation; audit
independently checks the measured input projection is unchanged, without claiming
a fresh full import/command replay.

Runners are in `runs/experiments/fleet-overflow174/`. `original.py --version`
would execute ALL 16 controls and is **not a resume command**. Do not repeat
existing versions or run it to complete this packet. The optional extra control
requires case selection support and a separately declared new output version
first; it is unnecessary for the bounded finding and remains unrun.

Native.cs links to retained ignored Main source at
`artifacts/run-exp-restrictions85/remake4d70275a/`. Native gates include unit
names/types/quality, army resources/covered cell/moves, launched fleets and
carried links, city names/values and declared nation values. Projection equality
is not every SAV byte or full game equivalence. Source/CPU entry, native command,
live game, UI and Windows acceptance remain distinct.

Never delete/overwrite a measured output, save or failure. New work must use
unique paths/versions; preserve tracked scalar evidence, private hashes and
T216 owner safety. See RUN-NOTES-fleet-overflow174.md latest END for publication
and relay state; do not start #178 or paused battles/bots.
