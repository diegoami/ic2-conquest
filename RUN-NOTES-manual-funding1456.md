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
