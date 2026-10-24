# Approved #176 / #177 / #174 continuation — batch 1

Finding: `findings/2026-10-24-strategic-economy-diplomacy-fleet-continuation.md`.
Main follow-up #1412: faithful AI embark overflow. Research intake pending.

Authoritative ledgers: `summary-v1.json` / `audit-execution-v1.log`,
`native-phases-v2.json`, `native-synthetic-v1.json`,
`fleet-native-providers-v1.json`, `fleet-native-v2.json`, `fleet-native-v3.json`.
Original phase/draw evidence: `phase-replay-v1.json`, `phase-facts-v1.json`,
`live-inertness-v1.json`. Source and declared input pins are separate ledgers.

One generated ROM720 startup-seed-1 trajectory, 0720→0721, plus plain observer
control. Complete before/after saves match. Original exit replay matches all
45 phases, including RNG. The 54 original draws were logged during those
unmodified instruction replays, not by a live per-draw hook. No human battle
orders, owner saves, production changes, or native Windows access.

35 conditional economy comparisons match; 24 local diplomatic busy/war-target
comparisons match; 23 provider comparisons match. Twelve valid cargo controls
have seven matches and five overflow discrepancies. Native import gates check
227,833 fields across 94 comparisons. These are not independent games, a
full-feature fidelity percentage, or whole-turn/random-stream equivalence.

## Generated archive and recovery

Drive folder: <https://drive.google.com/drive/folders/1Fzspq5V6nRtcDmxUpGlH6bh0hR0w5OvJ>.
File: <https://drive.google.com/file/d/1SEmZSpSXU2l3VnPt-FkR8x7nEnnjTMN_/view?usp=drivesdk>.
`strategic-tracks-batch01.tar.gz`, 19,787,823 bytes, 1,131 members including its
manifest. SHA256:
`d29926a6e430039072ec8e025f30ec0dcd8d412cabd775204aba429116649188`.

The explicit allowlist includes generated saves/RAM, native states, interpreted
ledgers, compiled diagnostic tools and pinned remake data JSON/terrain sidecars.
It excludes original EXE/DAT, runtime/prefix trees and owner #1355/#1388 data.
All 1,130 payload hashes verified locally; Drive metadata readback verified
parent and size, not a downloaded remote digest. `SAVES.sha256` records the
first capture batch; `SAVES-v2.sha256` adds the complete archive binary set.

Fresh recovery v2 verifies every payload and runs retained Tracks.dll on the
30 captured native phase inputs and FleetChecks.dll on four mixed-unit cases.
Both result files match the authoritative public JSON byte-for-byte. No
original executable or owner data is required for these native replays.

After extraction to a NEW directory ROOT, with a compatible .NET 10 runtime:

```bash
dotnet ROOT/tools/Tracks.dll ROOT ROOT/phase-replay-v1 ROOT/data-text/phase-facts-v1.json NEW-STATES NEW-PHASES.json
dotnet ROOT/tools/FleetChecks.dll ROOT ROOT/fleet-controls-v3 ROOT/data-text/fleet-original-v3.json NEW-FLEET-STATES NEW-FLEET.json
```

Original replay additionally needs the authorized original EXE/DAT/listing and
retained generated inputs pinned by the source ledger. Current runners use
exclusive/versioned names and fail if output exists; select fresh paths/versions
before repeating. Never delete a save or overwrite a measured output. Commit
public measurements and archive explicit generated evidence after each batch.

## Retained attempts and limits

The eight initial cargo-v1 fixtures used invalid quality 50. Native import
rejected the first; all original v1 outputs and the failed log remain excluded
from valid cargo comparisons. Twenty-three complete provider case results were
already persisted and recovered without rerunning. Valid cargo v2/v3 use quality
7. Native-phases-v1 predates the extra original local-gate ledger; v2 is final.

Recovery v1 was started while the archive was still being written and failed
with EOF before extracting payloads. Its log/empty destination remain. After
bundle completion, fresh recovery v2 passes. No archive or measured output was
replaced. The archive's data-text snapshot precedes its own final receipts.

Diplomacy alliance/trade/swap execution, mobilization/consolidation/mercenary
edges, overflow receiver/allocation failure paths and coincident after-arrival
fleet routing remain explicitly open. Stored-route support stays Main #1405;
T212/navigation187 remains a separate dependency and its blocked label is untouched.
