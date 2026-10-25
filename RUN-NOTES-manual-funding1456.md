# Manual army/fleet funding in debt — Main #1456 / conquest #206

## 2026-10-25 — START

Owner authorizes focused original UI research in the active session and
Main #1456 comment6400324520. Conquest #206 records scope before execution.
Branch `research/manual-funding1456`; base main `727a785`.

Plan: inspect pinned original form, caller and money-handler code; run real
original UI transfers at treasury -100/0/+50 with purse 100 and +100 request;
test at/over-cap, reverse and insufficient fleet-provider controls, and fleet
targets. Save and parse every before/after pair. Use unmodified original EXE
in isolated Wine/Xvfb. No End turn, battle, campaign or native Windows access.
Keep T207 automatic reserve policy separate. Recommend only; no remake writes.

Measurements are immutable and versioned; never delete or overwrite saves.
Private original files, hashes, full states and screenshots remain in ignored
`artifacts/run-exp-manual-funding1456/`. Sanitized case results and code/probes
belong to `runs/experiments/data/run-exp-manual-funding1456/` and
`runs/experiments/manual-funding1456/`. Commit and push each measurement batch
and at least every 30 minutes. Keep failed attempts as evidence.

Startup: main clean except eleven pre-existing unrelated untracked files;
no open conquest PRs. Main #1456 OPEN; v0.8.1 scope. Remake main source pin
`a5cfebedbb419870985c5f86e3987f238dd587f4` (will recheck before recommendation).

Findings comparison: fetched origin; none new/changed since last reported and
delivered baseline `6b9a3f35236de4329ded00d908d05ff39ea80828`.
Research relay pending new finding; do not advance delivered SHA prematurely.

Pilot-v1: isolated original started, loaded and wrote its before save. Real
money TUpDown was visible/enabled. Runner failed before clicking because it
called a nonexistent Game.hover method. Preserved staged/before saves,
screenshot, private Wine log and tracked failure/plan. Fixed runner to use
xdotool mousemove + short hover; no game behavior inferred from the failed
attempt. Treasury-v2 begins fresh with unique filenames.

Treasury-v2 complete: 3/3 requested original UI controls match predictions.
At treasury -100/0/+50 and purse 100, +100 produces treasury -200/-100/-50
and purse 200. Each real money control visible/enabled; parsed before/after
saves at turn0734, no End turn/battle, totals conserved. Full fingerprints,
private files and hashes kept under ignored artifacts; shared recorder's two
fingerprints moved intact to private evidence before publication because this
handoff explicitly requires original identities/hashes private. New runner
records full environment privately rather than automatically mirroring it.

Controls-v3 starts with 16 remaining predeclared cases; inspection helper now
includes list geometry/count to reduce repeated Wine helper launches. No game
logic edits. Native helper blob 884097638b6708f5152ae3a5b53c8d1ca72149bc is
byte-identical between audited b593c6e archive build and live a5cfebe Main.

Mid-batch: original cap1000 no-op; overcap1100 ->1000 credits100;
reverse100 and reverse-limited50 debit only available target purse;
fleet-provider50 transfers50, empty0 transfers0, treasury unchanged.
First nine saved pairs independently reparsed in pair-integrity-pilot-v1:
no parsed strategic differences except tested balances and camera view.

Native-v2 corrects native-v1's intentionally treasury-only fleet-target
comparison: current handler dispatches any via-fleet request to purse/purse.
V1 retained and scope disclosed. Both use real upstream helper, not a copied
formula; v2 is authoritative for comparing actual current dispatch. Handler
blob9a66af8 and faithful ruleset blob4e04ca3 also identical at a5cfebe.
source-audit-v2 replaces approximate v1 line ranges with exact starts/ends
located automatically in the pinned decompile. Both retained.

Controls checkpoint: all twelve army cases and all three fleet debt cases now
match the predeclared predictions through actual UI and saved pairs. Fleet
reverse receiving cap950 ->1000 limits a requested100 to50. Original fleet
funding at treasury -100/0/+50 also supplies100 in full. Four fleet controls
remain. Each measurement is immediately task-owned; no binary/public hashes.

## Completed measurement / self-review

19/19 original UI cases complete. Final audit-v1 independently reparses every
saved pair: all predictions match, all controls visible/enabled, all totals
conserved; parsed strategic state unchanged except tested balances and camera
view. EXE/DAT match private known original pins and remain unchanged. Private
manifest includes failed pilot, all save pairs, screenshots and fingerprints.
No End turn/battle/native Windows, no original patch or running-memory write.

Native-v2:12/19 helper+source-dispatch projections match;7 differences are the
six debt/insufficient treasury cases and fleet target with via-fleet dispatch.
Actual current native helper calls, not native UI/full command execution.
Remake main rechecked: still a5cfebedbb419870985c5f86e3987f238dd587f4.

Finding: findings/2026-10-25-manual-funding-in-debt1456.md. Recommend manual
national treasury semantics without source-balance clamp, preserving signed
cap/pullback, army/fleet-provider limits/reverse cap and T207 automatic reserve.
Original fleet targets always use national treasury, even when a fleet is
selected for supplies; actual native UI caller must be checked before calling
its generic CLI via behavior a UI defect. No remake implementation.

Validation: Python compile, C helpers compiled, native probe built/evaluated19,
public source blobs verified, full parsed save-pair audit19, diff --check.
Self-review only; no external reviewer launched. Earlier pilot/line-reference/
native-dispatch comparison scopes retained and disclosed, not silently replaced.

## Publication, relay and END

Commits: first measured batch `94daa86`; control/source checkpoint `9658d0d`;
fleet checkpoint `6cb0439`; final finding/audit
`e06c1becc368ec7a580dfa94ff4a5b84c15a0068`. PR207 merged at
`92314c83449c11285cdccb76e61a47c3b0481158`. Exact final head GitGuardian
SUCCESS; PR mergeable/clean, no review comments. No external review claimed.

New finding reported and successfully delivered:
`findings/2026-10-25-manual-funding-in-debt1456.md` — original manual army
and fleet funding can drive treasury negative; fleet-provider limits and
fleet-target national-treasury routing measured separately.

Last reported findings baseline and last delivered SHA:
`92314c83449c11285cdccb76e61a47c3b0481158`, 2026-10-25. Verified Research
thread `01a167fa-9fb2-7570-bf21-b32682c79e6e` title `ic2-research`; relay tool
returned that thread ID and `isError:false`. This records **delivery only**;
canonical intake/promotion remains Research's next step. A pre-send length
guard rejected an overlong message locally; the shortened message sent once.

Durable issue checkpoints:

- Main #1456: https://github.com/diegoami/imperial_conquest_2/issues/1456#issuecomment-6400629590
- Conquest #206: https://github.com/diegoami/ic2-conquest/issues/206#issuecomment-6400629742

END: bounded measurement and authorized handoff complete. All game/helper
processes from the final runner ended through its own-prefix cleanup. No
Windows access, paused battles/bots, new campaign, original patch, remake
write, release/tag change or extra reviewer. Eleven unrelated untracked files
preserved. Private evidence stays local/ignored; no public release attempted
because the owner's current handoff explicitly requires original files and
hashes private. Return checkout to main after this receipt merges. Next work
is Research consolidation, then Main's #1456 implementation using promoted
evidence; T207 automatic reserve remains a separate owner policy.

## Research promotion — 2026-10-25

Research peer reported PR77; verified live MERGED at
`865755e04f107afc38cdb496669d882e2551aca6`, exact head
`5c75f6cba10e27c2c736bfe2b5b6059f96caf6cf`, GitGuardian SUCCESS. Read the full
canonical report and safe receipt from that pinned merge:

- `docs/reports/2026-10-25-manual-funding-in-debt1456.md`
- `docs/data/manual-funding1456-intake-v1.json`

Independent offline re-audit: 38 retained saves/full 19-case audit exact;
19 staged byte allowlists, visible/enabled control and target/provider records
pass; plans match all 19 predictions. Three source blobs verified against
authoritative a5cfebe; fresh unchanged native probe reproduces every field of
all 19 native-v2 rows (12 match/seven differ). No fresh original game/UI,
native UI/full command, installed-build or native Windows acceptance; no
external reviewer. T207 automatic reserve unchanged. Research updated the
earlier purse report to distinguish old unmeasured debt coverage from this
new runtime evidence. Source finding and data README now mark promotion.

Findings comparison at this reply's start: none changed on origin/main since
reported/delivered baseline92314c8. This promotion changes metadata and adds
the independent verification receipt; no existing measured outputs change.
Next: land promotion metadata, relay it to Research, post canonical evidence
on Main #1456 and record actual delivery. Main implementation remains separate.
