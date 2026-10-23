# Paste-ready handoff to the remake main session

Owner decision: reproduce the original Computer general faithfully first
(#1355). Investigate a separate improved controller selectable in Settings
afterward (#1362, dependent on faithful acceptance; relates to #1361).
Keep faithful behavior as the default. Do not implement the optional controller
as part of the fidelity correction.

Conquest has prepared and compiled an actual source correction, not just a
diagnostic replacement controller. Packet on diegoami/ic2-conquest main:

- `runs/experiments/data/run-exp-faithful-general157/README.md`
- `faithful-general-portable.patch` and `source-pin-v2.json` in that folder
- `verification-v1.json`, before/after regression and build/apply receipts
- `runs/experiments/faithful-general157/Regression.cs` and `Replay.cs`
- Finding: `findings/2026-10-23-battle-general-later-pass-iteration1355.md`.

Research consolidation is pending; follow the normal promoted-report intake
before treating the finding as canonical. Check its live status rather than
assuming the conquest relay means promotion or acceptance.

The patch is against remake main8e5f0a35c9dd45a8ec31b38154406843b131013a.
It preserves pass one's type order, adds lazy live-slot iteration, and switches
pass two and every pass-three helper/entrypoint to slot order. No combat formula,
controller option or save-schema change. Source blob and SHA256 pins preserve
the original mixed encodings; use raw Git blob bytes if fetching legacy files.
Both proposed patches pass read-only application checks. Rebase deliberately
if current main differs; preserve unrelated work.

Please triage #1355 through the remake's normal workflow, apply the scoped
correction on the appropriate branch, and bring the meaningful regression
cases into the normal test suite. Two actual API tests fail before and pass
after: threat movement and shooting visit slot0 before slot1 despite their
types; also retain first-pass type ordering, defender bounds, live liveness and
battle-end guards.

The compiled production general passes14 recorded controls:2331combat draw
tuples,253available boundaries, terminal tactical states/RNG, reference185 and
owner346 combined movement/shot/melee/removal actions. Historical-entry control
recovers48969survivors/counter21; its missing old runtime fields remain explicit
assumptions. Owner inputs/hashes/full replays remain private. Conquest did not
modify the remake checkout or merge a production fix.

Run the full318-series corpus and relevant tactical tests, assess #1107/#1324
residuals explicitly, and obtain normal green CI before merge. Never blanket
refresh known failures or close #1355 from a candidate build alone. Native
Windows, independent strategic copy-in and writeback acceptance were not
performed by this packet. Do not launch the unrelated paused conquest battle
queue. Keep the optional improved-general design in #1362 separate.
