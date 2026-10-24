# Fleet movement: accepted actions, cargo/ports and an AI budget discrepancy

**Tag:** [confirmed, partial: 23 synthetic original-instruction movement/phase
controls, actual native accepted-command traces, one original Wine observer/plain
trajectory, bounded live-phase replay]. Research intake pending.
**Tasks:** conquest174/171; remake [1408](https://github.com/diegoami/imperial_conquest_2/issues/1408)
(budget), [1409](https://github.com/diegoami/imperial_conquest_2/issues/1409)
(faithful policy/execution), existing1405(stored destination state).

## New isolated discrepancy

An AI fleet with **one move**, at `(49,62)`, tries adjacent rough sea `(49,63)`
costing **three**. Original low-level fleet walker `0044E094` leaves position
unchanged and clears moves to **0**. Native real `CommandDispatcher` accepts
the corresponding `MoveFleetCommand`, leaves position unchanged and retains
**1**. The faithful ruleset's controller asymmetry is enabled.

| Paired control | Original moves after | Native accepted command moves after |
|---|---:|---:|
| AI, budget1, rough cost3 | **0** | **1** |
| Human, budget1, rough cost3 | 1 | 1 |
| AI, budget3, rough cost3 | 0, destination reached | 0, destination reached |

The AI/human original low-level input RAM blocks differ **only at the Carthage
controller byte**. Original AI output changes only address `0049C278`, the fleet
Moves word; human output changes no captured game RAM. Source instruction
`0044E073` performs the AI zeroing. Native inputs verify controller, initial
budget, rough-overlay membership and cost3. This is a conditional instruction/
accepted-command counterexample, not a claimed natural Windows observation.

`MoveFleetCommandHandler` returns `walk.MovesRemaining` directly, whereas the
army handler applies the faithful controller abort rule on insufficient moves.
Issue1408 scopes a fleet correction with human, affordable and blocked-marker
regressions; it does not change weather prices, designed selection weights or
global RNG architecture. No production change was made here.

## Original live boundary validation

The new memory-only wrapper records original `F608` entry and return at the
existing call `0044FA51`. Original callee stack depth is preserved; a temporary
return address captures exit then jumps to `0044FA56`. It writes only observer
scratch and restores CPU registers/flags/stack. **120 CPU preservation/capacity
controls** pass; their synthetic test callee is used only in the CPU test.

Two isolated Wine runs use the same generated Roman start, startup seed1 and
one End turn. New saves:
`FA174-live-rom-hook-v1-before.SAV` / `FA174-live-rom-hook-v1-after.SAV`, and the
corresponding `live-rom-plain-v1` pair, original **0720 → 0721**. Complete before
saves are byte-identical, and complete after saves are byte-identical. This is
one trajectory plus an inertness control, not two independent scenarios.

The observed turn contains **15 fleet phases**, only **two with moving fleets**.
Executing actual unmodified original `F608` instructions from every captured
entry reproduces **all 15 complete captured exit RAM blocks byte-for-byte**,
without masking fields or replacing a game/presentation/RNG helper. Each block
is `0x43000` bytes from `0045E000`. This validates the original phase replay on
this real trajectory, not all synthetic states or Windows gameplay.

## Movement and accepted actions

Twenty-three new synthetic cases complete the prior14 first-destination controls
through movement, and add stored-route budgets0/1, rough affordability, a human
comparison, cargo positive/zero and protected/unprotected port cases. **20
complete**; **3 stop before naval combat** and retain their pre-combat states.
Original naval combat outcomes are not fabricated or compared.

For21 measured original first destinations, the production native command is
actually dispatched from the original pre-move state and same requested goal.
**19 accept; 2 zero-move requests reject.** Actual handler paths are collected
through the existing production strategic observer, not a replacement walker.
Ten requested paths match, ten terminals match and ten move budgets match;
**nine match all three**. These denominators include no-op/refused controls and
are not a fleet fidelity rate. Divergent macro-navigation/port callers remain
separate from the isolated low-level affordability bug.

Separately, **23 real native `AiTurn.Run` executions** use the declared harness
SplitMix stream from the imported root seed, a real `CommandDispatcher` and a
recording wrapper. All accepted/rejected commands and relevant before/after
states are retained. One execution is the human-controller no-op control;
22are AI-controlled. They contain **10 accepted fleet moves and 2 accepted naval
attacks**, zero rejections and no action-cap hits. Replaying all12 fleet commands
and21 conditioned requests with the production path observer reproduces all
**33 native accepted/rejected states** canonically; no logger-induced state
change is hidden.

The native full AI seat and original fleet-only phase have different phase
histories and RNG models. Do not call them paired whole-turn decisions or use
their economic/combat outcomes as an original-fidelity test.

Actual native accepted moves pursue the foreign fleet in peace, trade and
alliance controls, with those relationships still present at dispatch. Thus the
earlier measured proposals can become executed actions. Native sailing weights
are explicitly **designed**; this is policy evidence, not automatically an
unintended bug. Issue1409 scopes faithful decision/execution support alongside
the existing design. Original same declared fleet-phase inputs choose a port.

## Gaps closed and remaining

- **Stored route + zero moves:** original calls its movement routine, performs
  no displacement, retains zero moves and keeps the stored destination. Native
  conditioned movement refuses with no moves; its AI issues no fleet move.
  This closes the earlier untested combination **as a synthetic control**, not
  as a newly observed natural zero-move live boundary. Stored-route native state
  support remains issue1405.
- **Cargo at sea:** with moves available, the embarked army follows fleet
  coordinates in original writes and native terminal state; with zero moves
  both stay put. The native army remains off-map and linked to the fleet.
  Disembarkation/capacity/combat-loss behavior is not covered by this check.
- **Protected port:** native actually accepts an approach, but a subsequent
  adjacent attack is rejected with `battle.target-docked-at-own-city`, preserving
  state. The corresponding unprotected adjacent attack is accepted. Approaching
  and attacking are different actions; the guard is not missing.

Original full destination execution also shows why caller semantics matter:
an original requested port/intermediate route cannot be equated to a single
native straight walk at its coordinates. The live replay confirms the original
movement, including the Carthaginian `(74,69)` phase endpoint. Main1409 must
evaluate port approach and sea waypoints, not hardcode endpoints or silently
replace designed policy. Army1394 and resupply1402 remain separate.

## Evidence and limits

Runners: `runs/experiments/fleet174-actions/`.
Tracked data: `runs/experiments/data/run-exp-fleet-actions174/`:
`summary-v3.json`, `movement-ledger-v3.json/.csv`,
`accepted-fleet-ledger-v3.json`, original-actions-v1, native-actions-v2,
native-paths-v1, paired affordability and accepted port controls,
live phase records/replay, 120CPU checks and source identity.

The live remake head at start, `c22cbf69229d18fcd75d319a69b6599df9eb4b3e`,
contains planning changes only: all **349 engine/data blobs** equal the retained
tested55d96876 build. No other checkout was written. Synthetic containers such
as `affordability-v1/ai/before.SAV` and
`original-v1/cargo-positive/before.SAV` are diagnostic projections, not original
Save As or natural-progress claims. The original generic EXE is pinned9d753d5d.

Generated saves/RAM/native states/tools/data are off Git under
run-exp-fleet-actions174; binary/member hashes, explicit archive and readback
receipts are tracked. The bundle excludes original EXE/DAT, runtime prefixes,
credentials and owner1355/1388 material. Recovery runs retained native tools
against restored inputs and reproduces33path/state rows byte-for-byte.

Failed harness attempts are retained: missing C# namespace, console-format
failure after the first native case, CSV shape and argument-shadowing analysis
errors, and a verifier import error. Native-v1 partial outputs remain; native-v2
adds per-case/journal persistence. Analysisv1/v2 are superseded by v3; partial
CSV and its raw CRLF are retained, not rewritten. No original/naval result was
discarded to make a comparison pass.

This batch supplies actual accepted native actions and original live fleet
boundaries. It does not establish identical complete AI turns, naval outcomes,
all ports/cargo/provider cases, original/native global RNG equivalence or native
Windows acceptance. The unrelated battle queue remains paused.
