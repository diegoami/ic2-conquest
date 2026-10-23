# Differential battle investigation: original IC2 and remake

Owner request: 2026-10-23. Tracking [conquest #157](https://github.com/diegoami/ic2-conquest/issues/157),
building on reproduction #154 / [remake #1355](https://github.com/diegoami/imperial_conquest_2/issues/1355).
This authorizes investigation and synthetic controls, not a production rebalance
or resumption of the unrelated paused battle queue.

## Objective and current evidence

Establish which battle behavior agrees, where it first diverges, which factors
cause the difference, and how much each proved difference affects outcomes.
Compare decisions and exchanges, not just winner/survivor totals.

The owner case already gives original48969 versus native20946survivors, with a
controlled native22090. First completed movement-half positions differ before
casualties. This prioritizes AI/movement investigation but does not exclude
exchange, morale, control-protocol or observation defects. Original50mspolling
is approximate; the former clear-claims assumption is not exact-state proof.

Freeze the ae614899 reproduction separately from current main8e5f0a3. The latter
adds PR1356 tactical information-panel changes; the inspected compare reports
no production tactical engine changes. Recheck live state at implementation.
Keep native CLI/kernel, graphical presentation and Wine/native Windows evidence
separate. Never silently mix versions or call an earlier reported test a new run.

## 1. Make the recorder trustworthy before using it as an oracle

Deliverable: validated original/native recorder pair and capability manifest.

- Reuse `patches/battle_hook.py`, `state/hook_log.py`, B11 exchange reconstruction
  and tactical25 phase observers. Existing original hooks cover14 RNG sites,
  shot/melee/rout entry markers and start/clear/reseed boundaries. They do not
  currently promise every movement, CG pass, claim or complete exchange boundary.
- Extend original observation only where needed: placement, target choice,
  movement request/each resulting step, shot/melee entry and exit, morale/rout,
  removal/repaint, setup/end-half and strategic write-back. Capture actual
  original claim state and pass identifiers; validate their addresses/layouts
  instead of filling absent values from the remake.
- Prefer hooks at semantic routine boundaries with before/after state copied
  into an append-only memory buffer. Keep registers, flags, stack, floating-point
  state and calling convention intact. No new RNG calls, reseeding, clock reads
  or file IO in observation hooks. Original binaries are private copies only.
- Validate hook cave semantics offline, then hook-on versus hook-off on the
  SAME seeded lab base: all snapshots, final state and terminal RNG identical.
  Exercise an infantry duel, ranged case and mixed multi-unit case before the
  owner battle. An unmodified original remains a separate live control.
- Fail the log on overflow, reentry/drop, sequence gap, unknown call site,
  broken RNG chain or unobserved boundary. Record a schema field as observed,
  derived/reconstructed, or unknown. Do not infer original decisions from port
  decisions and label them original observations.
- Verify the UI protocol: CGon-only versus CGon+initialEnd, same starting state
  and controlled seed. Record command timing/enabled state and whether End can
  interrupt an executing general. Use the protocol whose semantics are proved;
  no repeated End clicks or short idle watchdog during busy autoplay.
- Finish collection transactionally: result dialog, final slot state, original
  strategic SaveAs and fresh reopen. A cleared battle flag must not discard a
  completed result. Keep partial/interrupted evidence and the failure reason.

**Gate:** exact semantic coverage and inertness pass. Until then logs are
explicitly partial; no promise of an exact original battle log.

## 2. One comparison format for both engines

Every run gets a manifest: build/EXE/DAT/fixture identity, strategic and tactical
start state, nation codes, controllers and CG flags, selected side/unit, board,
claims, placement/phase flags, RNG algorithm/state, UI actions and restart mode.
Owner inputs/hashes remain private; synthetic fixtures use separate identities.

For each event, record:

| Field | Required contents |
|---|---|
| Identity | run, monotonically increasing event number, counter, side, actor/target slot; army identity distinct from table index |
| Decision | observed CG pass, candidate/order if available, chosen target/goal, relevant claim state; unknowns explicit |
| Movement | requested destination, actual step/path, blockers/occupancy, moves before/after, grid before/after |
| Exchange | shot/melee kind, troop/quality/morale/type/position/ammo/target inputs, RNGbound/result/order, loss and resulting state |
| Morale/rout | every morale change, threshold check, routed/removed units and cascades; separate from ordinary casualty loss |
| Lifecycle | copy-in, placement, half-round setup, terminal state, promotions, captured resources and write-back |
| Provenance | original site/hook where observed; any calculated formula terms labelled reconstructed rather than directly observed |

Store full40-slot/grid snapshots at semantic boundaries and deltas between them.
Screenshots are supporting evidence, not the event oracle. The remake uses its
actual event log and general decision journal: presentation frames alone omit
draw events. Never compare different actors/exchanges merely because draw
numbers happen to coincide.

## 3. Localize #1355 precisely, then shrink it

1. Compare actual prebattle armies and actual post-load/copy-in states. Separate
   strategic End-turn movement from tactical behavior; avoid comparing different
   battle-entry positions or regenerated morale accidentally.
2. Replay the original semantic event/draw stream through the unchanged port.
   Compare actor, target, pass, inputs, bound/result and after-state; stop at the
   FIRST difference. Never force a later original range onto a different port
   exchange to make the log continue.
3. Run each general on the same frozen decision input, including actual claims,
   grid, target words and current flags. Use original-machine-code helper replay
   for rapid localization, labelled as emulator evidence, then confirm the
   discriminating case in the live original.
4. Prioritize first movementhalf3/counter4 boundary and slots3/9/11/13/15/16.
   Add per-actor/pass checkpoints until a particular target/goal/path or draw
   call differs. Original/native inputs must still be equal immediately before
   that action, not only at battle start.
5. Minimize that discrepancy into a small synthetic fixture by removing
   irrelevant units/conditions. Every reduction is a new input; preserve the
   complete owner case and all rejected reductions.

**Gate:** smallest demonstrated difference with shared complete inputs, observed
original result, exact port result, and an explicit uncertainty statement.

## 4. Test competing explanations independently

| Theory | Discriminating experiment | Evidence supporting it |
|---|---|---|
| Computer general chooses differently | Same frozen state; compare target/goal/pass/order, then replay identical commands in both kernels | Identical-command exchanges match while autonomous decisions first diverge |
| Movement/occupancy/control semantics differ | Same command, grid, claims and moves; compare each step, lookup and phase transition; CGprotocol control | Same requested move produces a different path/state, or UI/control transition changes execution |
| Exchange formula or integer arithmetic differs | Identical actor/target inputs and recorded draws; manually scripted shot/melee without AI | Same exchange produces different bound, intermediate integer term or losses |
| Morale is omitted/misapplied | Hold quality/troops/draws fixed; vary army morale and tactical unit morale separately; isolate rout checks | Different response/threshold/cascade on matched inputs |
| Training/quality is omitted/mapped incorrectly | Hold tactical morale/troops/draws fixed; sweep raw quality4..9, then test readiness-to-quality initialization separately | Different quality sensitivity or copy-in despite equal other inputs |
| RNG stream/call ordering differs | Same algorithm/state; log every bound/result/site; inspect first different call/consumer | Different draw consumption/range before state changes, not merely different seed numbers |
| Grid, iteration, stale data or write-back omitted | Stacks, ties, exhausted moves/shots, dead targets, permutations and final survivor/promotion checks | A small boundary case reproduces the discrepancy on otherwise equal inputs |

Multiple theories may be true. Different AI behavior is a fidelity difference;
calling it tactically *worse* additionally requires an outcome comparison with
the exchange kernel held constant. Do not label it worse solely from one loss.

For causal impact, replay original decisions with the port exchange kernel and
port decisions with the original kernel where feasible, or use manually driven
original orders generated from the observed common state. Keep controller and
kernel variants explicit. If online cross-play is unavailable, report that
limitation rather than claiming a complete AI-quality experiment.

## 5. Synthetic campaign, expanding only after the recorder gates

Start with a12-fixture pilot spanning melee, ranged, morale, quality, movement,
multi-unit targeting and CGcontrol. Use strategic fixtures triggered normally
for end-to-end tests. For tactical-entry/kernel fixtures validate the ACTUAL
post-load state: original battle reload may normalize/reset phase or placement.
Do not route an open-battle fixture through an exporter that correctly refuses it.

Then expand:

- **Exchange kernels:**25 ordered melee type pairs across LI/HI/Ar/LC/HC;
 15 ranged actor/target pairs for the3 shoot-capable types against all5 targets,
 with legal range/ammo. Symmetric conditions and mirrored roles.
- **One-factor sensitivity:** two representative melee kernels and one ranged
 kernel, quality4..9; low/mid/high tactical morale; small/standard/large troop
 counts. Hold other inputs and draws fixed. Distinguish strategic morale,
 generated tactical morale, quality and recruitment readiness.
- **Geometry/control:** initially12 focused cases for range/line/blockers,
 zero/exhausted moves and ammunition, rout boundary, stacked/stale cell,
 dead target, slot-order ties, mirrored/equal-X/Y flank and control toggle.
- **General/full battles:** six small composition families (single-type infantry,
 ranged, cavalry and mixed formations), growing from1 to2/3battalions per type.
 Repeat attacker/defender roles and nation labels using at least Ptolemaic–
 Seleucid, Rome–Gaul and Carthage–Numidia. Keep the owner's large case as an anchor.
- **Seeds:** one fixed matched seed per minimal fixture first. Then a declared
 five-seed set 1/7/11/12345/24680 for stable families; extend selected uncertain
 outcome-distribution cases to20 paired seeds only when useful. No full Cartesian
 explosion or statistical claim from five seeds. Same number in two different
 RNGalgorithms is not a matched draw stream.

Every fixture has expected representation/phase and exact assertions, not only
survivor tolerance. Do not discard hard cases or increase tolerances to call
them passed. Synthetic/emulator/live Wine/native Windows results have distinct
coverage columns. The paused B16/etc work list is not implicitly dispatched.

## 6. Reuse the historical corpus and report extent honestly

The repository already has a318-series golden replay corpus and reported reviewed
T188/T189 improvements; later T190/T191 corrections also exist. Historical
42/36 residual counts are not current measurements. Re-establish state/draw/
write-back counts on the pinned current build and authenticated fixture revision
before adding new cases. Standard local fixture checkout/environment currently
is not configured; locate retained artifacts or recover the approved corpus.
Metadata access to the pinned private fixture commit was verified during this
preflight, so recovery is available without asking the owner to rediscover it.
No fixture bytes were downloaded or replayed by this planning step.
Do not rerun old scripts that write projects into another checkout or hardcode
obsolete commits; adapt a task-owned runner with outputs redirected here.

Deliver:

1. Exact-log capability/inertness report and any remaining unobserved fields.
2. Owner battle timeline and first-divergence report with minimal reproducer.
3. Coverage matrix: exact matches, divergent AI actions, exchange arithmetic,
   morale/quality/control/representation gaps, blocked and untested cases.
4. Outcome table: winner, per-type survivors/losses/routs, half-round count,
   repeated-run stability; distributions for declared seed studies.
5. Ranked causes with observed evidence versus hypotheses, and causal-control
   outcomes. Correction proposals identify exact method/behavior/regression.
6. After a separately scoped correction, rerun minimal fixtures, owner anchor,
   relevant synthetic families and full corpus. Report newly cleared FIRST
   divergences and whole-battle matches separately; upstream1355staysopen until
   its acceptance is actually met. No production source edit in another repo.

## Execution, preservation and first work

Owner approval covers this investigation; routine gates do not require repeated
permission. Implement phase0/1, publish the first exact-divergence report, then
expand the matrix according to the evidence. Do not run a new large campaign
before recorder validity is established. No model/subagent dispatch is implied.

Every output is immutable/versioned. Never delete/overwrite a save, even to
regenerate it; scripts use unique names. Track public-safe text under
`runs/experiments/data/run-exp-battle-parity157/`, binaries in approved artifacts,
owner inputs/full traces/private hashes outsideGit. Commit/push each batch and
at least every 30 min; preserve complete error reports/checkpoints and resume
completed work. Final synthetic artifacts go to Drive/release; EXE/DAT stay private.
Relay published findings to ic2-research for consolidation.

**Started now:** read-only tracer/corpus/source audit and existing offline hook
tests. Results in `tracing-capability-v1.json`, `hook-build-reader-v1.json` and
`hook-register-inertness-v1.json`; corpus access in `golden-corpus-access-v1.json`.
Hook build/reader checks pass, including the
real EXE site scan;2,060 emulated preservation states match plus boundary/overflow/
reentry/mutation-detection checks. This does not certify the proposed new
movement/decision hooks or supply a new live exact battle log.
