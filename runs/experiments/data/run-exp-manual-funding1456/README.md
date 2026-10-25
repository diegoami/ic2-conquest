# Manual funding while in debt — Main #1456 / conquest #206

Promoted in [Research PR77](https://github.com/diegoami/imperial-conquest-2-research/pull/77)
at `865755e04f107afc38cdb496669d882e2551aca6`:
[canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/865755e04f107afc38cdb496669d882e2551aca6/docs/reports/2026-10-25-manual-funding-in-debt1456.md),
[safe receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/865755e04f107afc38cdb496669d882e2551aca6/docs/data/manual-funding1456-intake-v1.json).
Research independently reparsed 38 saves, verified all 19 staged byte
allowlists/control/provider records, and rebuilt the unchanged native probe
with all 19 v2 rows reproduced. No new game or native UI/full-command claim.
Existing measured files remain unchanged.

Owner-authorized original UI study. `all-cases-plan-v1.json` fixes predictions
before the control batch. Each completed `<version>_<case>.json` is a distinct
real UI observation, including visible/enabled status, parsed save balances,
provider/target identifiers read from the original form, turn, save basenames
and conservation. Arrays are `[treasury, target purse, other fleet purse]`.
The other fleet is #2 for army targets and #5 for fleet targets.

Source fixture: `saves/fleet-split-antium-0734.SAV`, turn0734. Only treasury
and purse fields staged, with a byte allowlist; no coordinates, map, ownership,
units, moves, supplies or controller flags staged. No End turn or battle.
Original EXE is the retained unmodified `Imperial Conquest 2.exe`, run under
Wine 10.0 (Ubuntu 10.0~repack-12ubuntu1), win32 prefix and Xvfb1280×1024.
No native Windows claim. EXE/DAT identity, original files, private hashes,
screenshots, full fingerprints and full save states remain in ignored
`artifacts/run-exp-manual-funding1456/`. They are not release payloads.

`pilot-v1` failed before the money click: nonexistent runner hover method.
Its failure, before save, staged save and screenshot are preserved. `treasury-v2`
is the corrected three-case treasury batch. `controls-v3` is the remaining
16-case cap/reverse/fleet batch. New versions never overwrite these outputs.

`native-v1.json` calls the retained real upstream helper, choosing treasury for
all fleet targets (original routing). It does **not** test current via-fleet
dispatch for a fleet target. `native-v2.json` corrects that comparison: it uses
the current `TransferMoneyCommandHandler` dispatch (via fleet for either unit
kind), with real `TreasuryPurseTransfer` calls. Neither is a native UI or full
command integration run. Keep both outputs. Source helper, command handler and
faithful ruleset are byte-identical at live source pin
`a5cfebedbb419870985c5f86e3987f238dd587f4` and retained build pin
`b593c6e28939c1c7154f9a41d0436a8f14f352dc`; code Git blob pins are in the source
audit, not private file identities.

Runners in `runs/experiments/manual-funding1456/`:

- `run.py --version UNIQUE [--cases ID ...]`: actual original UI measurement.
- `controls.c`: read-only geometry, visibility, enablement and list geometry.
- `list-count.c`: pilot helper, retained; superseded by combined inspection.
- `Native.csproj`: actual native helper, source-verified dispatch projection.
- `audit.py --version UNIQUE`: independently reparses each saved pair, checks
  all parsed strategic state except tested balances and camera view, compares
  measured originals with native scalars, verifies private asset identity and
  public source blobs; exclusive public summary and private hash manifest.

No game logic is copied into a purported emulator. This is original UI
evidence plus a native helper comparison. Preserve T207 automatic-funding
reserve as an independent owner-selected QoL policy.
