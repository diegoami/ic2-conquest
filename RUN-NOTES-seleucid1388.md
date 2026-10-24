# Seleucid strategic End-turn boundary — remake #1388

## Start — 2026-10-24

Owner authorized investigation: “ok can you investigate 1388 then ?”
Branch `investigate/seleucid-end-turn1388`, base `bc1c627d12ec601d28b1d94ba88183e3306f83e1`.
Live remake main is `3c1860079db6dd9b1fb11ceb8b726c7fd95293ac`.
#1388 and #1355 are open. No open conquest PRs. Findings on origin/main are
unchanged from reported/delivered baseline `e1a943d5f9de8b88787112f137ad8053a699e6e0`.
Eleven unrelated untracked owner files preserved.

Question: original End turn places defender at (212,96), native at (212,94),
from owner campaign. Starting defender (219,93), attacker (213,93).
Different RNG streams are already known; do not infer a movement defect from
terminal positions alone. Tactical matching and controlled writeback acceptance
are separate; native Windows check is incomplete and physical Escape stopped
Computer Use. Do not resume Computer Use or optional Improved AI work.

Plan: recover retained input/output identities privately; build exact pinned
remake Engine/Data in this checkout; record ordinary GameSession End-turn
decisions/routes and inspect relevant original mover/targeting code. Reuse
validated observers where possible. Conditional movement replays distinguish
target choice, path execution, state/terrain mismatch and RNG. Any original
controlled End-turn runs belong only to #1388, not the paused battle queue.
Record approval/scope on #1388 before launching a game.

Never delete/overwrite any measurement or save, even to regenerate it. Use
unique names and exclusive output creation. Public-safe outputs and scripts go
under `runs/experiments/data/run-exp-seleucid1388/` and
`runs/experiments/seleucid1388/`. Full owner states/logs and owner hashes remain
private under ignored `artifacts/run-exp-seleucid1388/private/`; no generic
archive walker. Never write to another repository. Commit/push each completed
batch and at least every 30 minutes. Relay landed findings via the documented
research procedure or supply a paste-ready message if bridge unavailable.

## Execution and bounded attribution

Approval/scope recorded on remake #1388 comment6382213610 before Wine runs.
Read findings and promoted strategic targeting/lateral movement reports first.
Compiled exact current remake Engine/Data from a read-only Git archive; all332
source blob identities verified. Normal GameSession End turn reproduced212,94
three times identically. Private decision/routes expose target207,95; western
7000-troop target191,95 rejected by native direct-walk reachability.

Seventeen guarded original CALL-site markers passed816 CPU preservation states.
Original hook-seed1-v1 / plain-seed1-v1 / hook-seed1-v2 all completed0755→0756:
before saves byte-identical, after saves byte-identical, defender212,96/78857.
Second observer captures atomic original pre-walk RAM privately, with CPU copy
checks and whole-save inertness. Actual original destination191,95 via waypoint
189,104. Actual original helpers reexecuted from that RAM: targetscore828 vs
native212; origin/targets share region-1/coast1; direct line to191,95 false.
Original full destination wrapper reproduces all656bytes of saved defender.
No local Random calls; five emulated seed variants give same target/endpoint.
All4 relevant strategic field strengths match native exactly. Both low-level
walkers match21/21 entered steps across3conditional destinations. Choosing only
the original target without routing gives213,94, so a target-only change is
insufficient. No production correction or whole-turn RNG alignment claimed.

Retained slips: dotnet absent from PATH (absolute installed path works); initial
observer layout needed larger scratch section before live use; replay v1 Random
hook address corrected to40284C in final evidence; one preserved syntax failure.
Full coordinate-log stdout retained privately rather than published; no output
or save deleted/overwritten. Private evidence manifest retained outside Git.

Public evidence audit-v1 passes; Python compilation and source checks pass.
Finding and public-safe scripts/scalars ready to publish. Native Windows remains
incomplete; physical Escape respected. Research bridge verified reachable;
Research PR68 still under its owner merge hold, unrelated to this new intake.
Next: publish PR, pass required checks, relay actual landed source, post #1388
bounded root cause and downstream paired eligibility/routing implementation work.

## END — publication and successful relay

Conquest PR167 merged at `889557fa2d8f1dd6f36bc5ef3a06bcaf3532082c`.
GitGuardian Security Checks passed: two commits scanned, no secrets. Authored
source/docs whitespace and Python compilation passed. No separate model review.
Public privacy audit excludes binary/generated files and owner hash canaries.
The earlier staging check caught generated bin/obj files; they were unstaged
and locally ignored before the first commit. No build output was published.

Reported-findings baseline and last successfully delivered findings baseline:
`889557fa2d8f1dd6f36bc5ef3a06bcaf3532082c` (2026-10-24), new file
`findings/2026-10-24-seleucid-strategic-target-routing1388.md`.
Actual main-pinned packet delivered successfully through the verified session
bridge to Research thread `01a167fa-9fb2-7570-bf21-b32682c79e6e`, with source pin,
partial tag, evidence/save/turn references, privacy and acceptance limits.
An initial local TextEncoder guard was unavailable and sent nothing; an ASCII
length guard then passed and the bridge acknowledged delivery. Research
promotion is pending, not implied by successful delivery. Existing Research
PR68 merge hold was explicitly left unchanged.

Results posted on remake1388 comment6382310107 and conquest157 comment6382310321.
Main owner-carried handoff is `docs/notes-for-main-strategic1388.md`; no direct
message to Main and no write to another repository. #1388/#1355/#157 remain
open. The investigation is complete at bounded root-cause attribution; no
production eligibility/routing correction, whole-turn RNG equivalence, optional
Improved AI work or native Windows acceptance. All original/native diagnostic
runs ended; no reviewer/delegate launched. Private evidence and source copies
retained unchanged, no measured output/save deleted. Eleven unrelated untracked
owner files preserved. Next production step belongs to Main's normal scoped
implementation/CI workflow after Research promotion; no further run pending.

## Research promotion — 2026-10-24

Research PR69 verified merged atcdb355fde49b7047d6164de26b2922054fb120ee.
Canonical1388 report read and linked from source finding/README/Main handoff.
Owner audit/helpers independently reproduced without another original game.
This is metadata promotion, not a production correction or Windows acceptance.
Joint publication/relay receipts are recorded in RUN-NOTES-strategic-fidelity.md.
