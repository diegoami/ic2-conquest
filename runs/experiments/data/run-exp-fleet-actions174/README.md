# #174 actual movement and accepted actions

Finding: `findings/2026-10-24-fleet-accepted-movement174.md`.
Authoritative analysis: **summary-v3.json**, movement-ledger-v3.json/.csv and
accepted-fleet-ledger-v3.json. Raw original-actions-v1, native-actions-v2 and
native-paths-v1 remain immutable. Main follow-ups1408(budget),1409(faithful fleet
policy/execution), existing1405(stored-route state). Research intake pending.

23synthetic original controls:20complete,3stop before naval combat.21conditioned
native requests:19accept,2reject at zero moves. Native full AiTurn23runs accepts
10fleet moves and2naval attacks, with zero rejections/caps; its phase history and
declared harness SplitMix stream are not equivalent to original F608alone.
One of the23executions is the human-controller no-op control;22are AI-controlled.
Production path observer33replays preserves every native result.9of21conditioned
requests match original path+terminal+budget; no-op/refused controls are included,
so this is not a general fleet fidelity rate. Policy/navigation mismatches are
separate from the isolated AI affordability discrepancy.

Paired affordability input RAM differs only at Carthage controller byte: original
AI clears its one remaining move, human retains1; native accepted commands keep1
for both. Rough cost3 verified. Positive affordable budget3 agrees. Protected
adjacent attack is rejected without state mutation; unprotected accepts. At-sea
cargo positive/zero coordinates and link checks pass. Stored-route+zero now
tested synthetically; no displacement, route retained by original, native no
accepted AI fleet move. No new native route implementation is implied.

## Actual original boundary gate

New generated Roman input ROM720.SAV, startupseed1, one End turn0720→0721:
FA174-live-rom-hook-v1-before/after.SAV and corresponding plain pair. All complete
before and after SAV bytes match between observer/plain. New F608entry/return
wrapper passes120CPU preservation/capacity checks; synthetic test callee exists
only in CPU tests.30live snapshots form15phases, two moving. Actual unmodified
original instructions replay all15captured exit RAM blocks byte-identically.
No game, RNG, movement or presentation helper is replaced. No human battle
order or native Computer Use. This is one trajectory and its control, not two
independent campaigns or native Windows acceptance.

## Artifact storage and replay

Drive folder: <https://drive.google.com/drive/folders/19FVgahM2dSCOBxYyHV0ZR2P4TEyU2d5D>.
File1fFCIu5lKk3LuUO-ILGSI9FR8UYa7055d, `fleet-actions-batch01.tar.gz`:
**466members,8322493bytes**, SHA256
`3189e5084511e54e926c74222e766658f6e8c4d2aef0a3f12c1e93662deabecd`.
Explicit generated inputs/outputs/RAM/native states, dataJSON+terrain sidecars,
compiled Actions/Paths/PortChecks tools and selected authoritative text.
No original EXE/DAT, prefix/runtime tree, credential or owner1355/1388 input.
Local466member hashes verified; fresh recovery reruns retained Paths and all33
rows equal byte-for-byte. Remote size/parent readback is not a digest download.

Recover to a NEW tree and run:

```bash
dotnet tools/Paths.dll ROOT ROOT ROOT/data-text/native-actions-v2.json NEW.json
dotnet tools/PortChecks.dll ROOT ROOT NEW-port.json
```

Original CPU replay additionally needs pinned original EXE9d753d5d externally.
Live Wine runner needs the documented installed seed354d/prefix/helpers, a NEW
label and the declared input. Synthetic .SAVs are diagnostic projections, not
original Save As. Source55d96876/349engine-data blobs remain identical at the
start livec22cbf69planning head. Another repository was never written.

## Retained failures and versions

Native buildv1 missed Naval.Commands namespace; v2built, then console used a
format overload on JSON. Its first native case partial states/logs remain in
native-v1. Programv3adds per-case result/journal persistence and correct logging;
native-v2is final. Analysisv1wrote valid provisionalJSON but partial CRLF CSV,
then failed on mismatched fields; its limit text also overcounted combat stops.
Analysisv2failed because its argument variable was shadowed by RAM bytes.
Analysisv3uses complete fixed columns/LF and the correct three stopped cases.
No measured output was deleted/overwritten. Recoveryv1failed on missing json
import; v2uses a standalone verifier and passes. Preserve all old attempts.
Use new labels/versions for any rerun, commit/push batches/30min, archive explicit
allowlists only. Full AI parity, naval outcomes, disembarkation/providers and
Windows acceptance remain outside this batch.
