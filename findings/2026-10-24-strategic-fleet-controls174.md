# Fleet continuation: stored destinations need native state support

**Tag:** [confirmed, partial: fourteen synthetic original-instruction/native
fleet controls; not fresh original gameplay or accepted native action parity].
**Tasks:** [#174](https://github.com/diegoami/ic2-conquest/issues/174), parent171;
new [remake1405](https://github.com/diegoami/imperial_conquest_2/issues/1405).
Intaken by [Research PR70](https://github.com/diegoami/imperial-conquest-2-research/pull/70),
main `ebe8acb530f9b0250855aded20e1988f94d4c873`.
[Canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/ebe8acb530f9b0250855aded20e1988f94d4c873/docs/reports/2026-10-24-strategic-fleet-controls174.md).
Promotion changes no measurement or production/Windows acceptance claim.
Remake source/data pin55d96876.

## Answer

Original fleet stored destinations affect which destination routine is called.
The native model cannot distinguish the measured absent/A/B route states.
This is explicitly documented as unsupported native state with canonical export
reset, rather than a hidden violation of the current converter's policy.

The original phase chooses port `(45,68)` when no route is stored. With routes
A=`(48,66)` or B=`(47,67)`, it calls `0044E1FC` through the stored-route site
`0044F667` with A or B respectively. The resulting diagnostic SAVs differ from
the absent-route control **only in fleet0's four route bytes, +4/+6**.

All three import to identical serialized native GameState hashes and offer
identical native fleet-march proposals. `OriginalSaveExportFieldMapping` states
that `OriginalFleet.RouteX/RouteY` have no native field and writes absent-route
sentinels. A faithful stored-route feature needs explicit native state and
decision support, with save/load/export lifecycle tests; changing proposal
weights alone does not represent the missing destination.

## What was actually executed

The batch begins with the retained generated original decision snapshot from
`SF-N-rome-hook-v1-before/after.SAV`, turn0720→0721, then constructs fourteen
synthetic fleet-phase inputs. No owner1355/1388 input or fresh game run is used.
Original current nation is set to computer Carthage. Fleet0 is at `(49,62)`;
another fleet is placed on verified sea cells at distance3 or18. Relations,
fleet strengths, construction/moves and stored-route fields are varied as
declared in `case-manifest-v1.json` before execution.

Actual unmodified original `FUN0044F608` instructions execute their automatic
supply/repair prepass, port selector and hunt scorer. The collector stops at the
first `FUN0044E1FC` entry, **before movement**, or at normal phase return when
there is no move. No port, strength, movement or Random helper is replaced.

Original fleet strength really consumes `Random(4)`. Bounds, results, caller
returns and before/after seeds are retained. Stored-route cases consume zero
hunt draws; ordinary peace consumes one actor-strength draw, and eligible war
targets consume two. Separate actual scorer replays verify returned scores
253/90/1797 and the strict **100 versus101** port/hunt boundary. The original
uses the real seeded instruction stream, not an injected favorable outcome.

Native production `AiMilitaryPhase.ProposeFleetMarches` is invoked on imported
original pre-move state, after verifying fleet and relation inputs (**3568
checks**). Its real outer launched/moves guards are respected. This measures
**proposals**, not the winner of the entire native greedy AI loop.

| Control | Original first destination | Native offered fleet march |
|---|---|---|
| Peace / trade / alliance | Port `(45,68)` | Foreign fleet `(48,65)` |
| War, baseline / weaker enemy | Enemy `(48,65)` | Enemy `(48,65)` |
| War, stronger enemy | Port `(45,68)` | Enemy `(48,65)` |
| Stored A / B | Stored A / B | Same proposal as absent route |
| Original hunt score100 /101, distance18 | Port / enemy | No march proposal in either |
| Zero actor moves / actor under construction | No move | No proposal |
| Target under construction / same owner | Port | No proposal |

The zero-moves control in this packet has no stored route: stored route plus
zero moves was not tested by this packet. The [accepted-movement follow-up](2026-10-24-fleet-accepted-movement174.md)
adds that synthetic combination and live-phase/accepted-action coverage.
Original route absence tests the signed X word. Automatic prepass
and port selection still run before the stored/absent-route branch.

The native sailing weights and minimum score are explicitly marked **designed**
in the ruleset. The distance18 proposal cutoff and relationship/strength
differences are therefore measured policy differences requiring faithful versus
designed-mode reconciliation, **not automatically unintended defects**. No
accepted-action, naval combat or full fleet strategy equivalence is claimed.

## Evidence and follow-up

Tracked text: `runs/experiments/data/run-exp-strategic-fleet/`:
`summary-v1.json`, `original-fleet-controls-v1.json`,
`native-fleet-controls-v1.json`, `original-score-controls-v1.json`,
`stored-route-byte-control-v1.json`, manifest, build and execution receipts.
Runners: `runs/experiments/strategic-fleet/`.

Synthetic diagnostic containers are named
`controls-v1/<case>/pre-move.SAV`, with input and pre-move RAM beside them.
They are not original Save As files or turn-progress claims. Generated binary
evidence/tools/data are off Git; archive hashes and upload receipts are tracked.
Original EXE/DAT, runtime trees, credentials and owner material are excluded.

Remake1405 scopes stored-route state support and actual accepted-behavior tests.
Existing1394 owns army target eligibility/routing;1402 owns the independently
controlled resupply selector. Scorer1216's approved tie policies remain separate.
Research174 next needs actual fleet-phase observations and accepted native
command traces, protected ports, provider thresholds, cargo and routing/contact.
Research175–178 track homeland, economy, diplomacy and later campaign expansion.
No production correction, new native schema, live fleet run or Windows acceptance
is implied by this conditional batch.
