# Owner #1355: Ptolemaic–Seleucid Computer general gap reproduced

**Status:** [confirmed, partial], 2026-10-23. Outcome reproduction and bounded
first-phase localization under Wine; no production fix or exact original
instruction/draw attribution.
Promoted 2026-10-23 into imperial-conquest-2-research at
[`32f1e60`](https://github.com/diegoami/imperial-conquest-2-research/blob/32f1e605d5c60497f1e0815851c5e755b8157f8d/docs/reports/2026-10-23-ptolemaic-seleucid-computer-general-gap1355.md)
(research PR #66). Source measurements and limitations are retained.
**Tasks:** [remake #1355](https://github.com/diegoami/imperial_conquest_2/issues/1355),
[conquest #154](https://github.com/diegoami/ic2-conquest/issues/154).

## Answer

The owner's result gap is real in this reproduction:

| Run | Ptolemaic start | Seleucid start | Ptolemaic survivors | Seleucid survivors |
|---|---:|---:|---:|---:|
| Actual remake sequence, Computer general | 73564 | 78857 | **20946** | 0 |
| Unmodified original, Computer general | 73564 | 78857 | **48969** | 0 |
| Controlled remake tactical replay from measured original entry state and original Delphi RNG state | 73564 | 78857 | **22090** | 0 |

The original preserves about 2.34 times the remake's survivors. The native
control uses the production tactical routines unchanged; adding the built-in
general decision journal reproduces its final state exactly.

This is not evidence of different exported starting troop counts. A fresh
export from the owner's exact JSON using the supplied template is
**byte-identical** to the supplied SAV. Owner/installed original EXE and DAT
identities match. At battle entry the live slots agree on troops, type,
quality, moves and ammunition; natural runs differ in randomized tactical
morale and defender placement. The controlled replay starts with the original's
actual board/slots/morale and original RNG algorithm/state, yet the gap persists.
It cannot be dismissed merely as different initial dice streams.

## Reproduction and evidence privacy

Owner supplied `classical-mediterranean-saveyy.json`, its exported `.sav`, and
`AUTO0742.SAV` as template, then instructed End turn, attack as Ptolemaic and use
Computer general. These are actual private owner inputs, not generated #153
cases. All originals remain unchanged. Their copies, hashes, complete state,
screenshots and traces are **outside Git and public artifacts**, under the
private experiment folder; no owner file is in the broad-conversion Drive
bundle.

Public-safe probe/audit code and aggregate evidence:
[`runs/experiments/data/run-exp-battle1355/`](../runs/experiments/data/run-exp-battle1355/).
Authoritative aggregate audit: `public-safe-audit-v2.json`. Private local alias:
`artifacts/run-exp-battle1355/private-v1/`; private input manifest is beside the
copied inputs. No private hashes are emitted by the public audit.

Production source pin is remake `ae614899d63ac721ee46d1e3213191fe1f43a676`, matching
the owner's Windows checkout. The Linux engine's exact two-file production
overlay/build is pinned by the broad #153 packet. Original unmodified EXE
identity is the same `9d753d5d…` binary documented there; Wine10.0, private
display155 at2560×1440, no active owner game touched. A larger display was needed
to fit the owner's saved map window without editing the save.

The actual native flow loads/migrates format4, ends the turn, opens the tactical
battle through `GameSession`, and submits `battle general on`. Complete actual
mutation frames and typed tactical events/draws remain private. Read-only
reflection retains the actual session's controller solely to read its public
event log; no production state, rule or draw is changed.

The original flow stays in **one process** from opening the exported input
through End turn, approach and battle. It toggles Computer general once and
presses the initial battle End turn once, then only observes. No repeated turn
clicks are injected during autoplay. Offers after combat are declined by policy.

## Before battle

After End turn both games reach Autumn week1,269BC (original turn0756):

- Ptolemaic army73564troops, strategic morale63, at(213,93).
- Seleucid army78857troops, strategic morale62. Native ends at(212,94);
  original at(212,96) in the retained runs.
- Native entity IDs are army-11/army-4; corresponding original record indices
  are9/4. Original approach moves the attacker to(213,95) before clicking the
  adjacent defender. Clicking a nonadjacent enemy only selected its information.

Original prebattle evidence includes private
`B1355-flow-v3-AFTER-END.SAV`, turn0756, and the measured battle-entry memory
snapshot after approach. Native equivalents are `native-after-end.json` and
`native-battle-entry-strategic.json`. The position difference is already a
strategic divergence; it is not by itself an explanation of the casualty gap.

The original battle result dialog was visually read:73564→48969 against
78857→0. Its per-type survivors sum to48969 and independently agree with the
terminal memory slot totals. The original reaches counter21; the controlled
native replay reaches counter29. These are observations for these runs, not
an outcome distribution over seeds.

## First completed-phase divergence localized

The controlled replay constructs the measured original counter2/side0 board,
live slots, grid, tactical morale and current RandSeed, using the existing
`DelphiBattleDraws` seam and unchanged `ComputerGeneral`/tactical routines.
Computer flags follow the human attacker/AI defender. General claims are
assumed clear at placement; that hidden runtime assumption remains a limit.

By counter4, side-to-move1, the first attacker movement half has completed in
both observed traces and **neither side has casualties yet**. These attacker
positions differ consistently throughout the captured counter4/side1 states:

| Slot | Original | Controlled native |
|---:|---|---|
|3|(11,2)|(12,2)|
|9|(9,2)|(7,2)|
|11|(9,0)|(11,1)|
|13|(8,1)|(12,3)|
|15|(13,3)|(11,3)|
|16|(8,0)|(6,1)|

This bounds a divergence to the first computer movement phase, before later
damage/rout cascades. It points to general decisions/movement and draw
consumption/order as the next investigation, rather than a balance tweak or
save-byte repair. It does **not** identify the exact first original instruction
or prove which production method is wrong. Original polling is50ms and not
instruction-atomic; setup transitions require both counter and side filtering.

The native production decision journal and full event/draw log are private
supporting evidence. Related existing tracks were read:
[ #1107 targeting/draw divergence](https://github.com/diegoami/imperial_conquest_2/issues/1107),
[ #1324 grid/rout/lookup/Walk differences](https://github.com/diegoami/imperial_conquest_2/issues/1324),
[ #1329 strategic move callers](https://github.com/diegoami/imperial_conquest_2/issues/1329).
No one of them is assigned as the cause from this result.

## Collection failures and limits

All attempts remain private and are not silently replaced:

- Initial display too small for the saved oversized map; larger display fixed
  the UI-only problem. A first enemy click at distance3 made no movement;
  the explicit free-land approach fixed the protocol.
- An18-second original capture was stopped by the generic driver's8-second
  half-round proof while combat was visibly advancing. The complete run used
  once-only controls and a900-second observation allowance instead.
- The complete original battle **finished**, but the recorder then requested
  battle state after the original cleared its battle flag and raised. Result
  dialog, terminal memory totals and full poll are preserved. Consequently no
  postbattle original SaveAs/reopen or write-back validation is claimed here.
  The future collector guards that cleared flag; no rerun was used to hide it.
- The first aggregate audit included a transient native setup side in its
  counter4 boundary. Corrected side1 filtering is recorded, without changing a
  game output. The final aggregate audit passes preservation, outcomes,
  repeated-control equality and the completed-half movement differences.

Only one complete unmodified-original outcome and one normal native outcome
are asserted, plus the repeated controlled native result. This is not native
Windows execution, an exact original instruction/draw replay, a seed sweep,
independent model review, or a production fix. The original UI control
transition and hidden runtime claims still require care in exact attribution.

The broader #153 conversion matrix remains valid for its sampled strategic
round trips; it explicitly does not certify Computer general parity. #1355
remains open for evidence-backed tactical investigation. Do not rebalance from
this single battle or claim ordinary RNG variance resolves it.
