# Original army navigation: eligibility, waypoints and caller limits

**Tag:** [confirmed, partial]. Pinned original instructions, 396 public control
rows, static-domain checks and a final private conditional regression.
**Tasks:** [#187](https://github.com/diegoami/ic2-conquest/issues/187),
[Main T212 / #1394](https://github.com/diegoami/imperial_conquest_2/issues/1394).
Promoted by [Research PR72](https://github.com/diegoami/imperial-conquest-2-research/pull/72)
at `c863a97cb1fc66206e23521c7bdd024548ba41dd`.
Use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/c863a97cb1fc66206e23521c7bdd024548ba41dd/docs/reports/2026-10-24-army-navigation-rule187.md).
T212 is now in progress under a narrowed enemy-army target-tree contract;
no production code changed here.

Research separately reproduced the bounded controls and retained native walker.
Its [safe receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/c863a97cb1fc66206e23521c7bdd024548ba41dd/docs/data/actions-navigation187-intake-v1.json)
documents four older branch rows with added DBA8 observer entries: removing only
those entries restores the retained call lists; no game result was normalized.
This was offline replay of retained builds, not an independent rebuild, new
caller experiment, fresh game or Windows acceptance. The newer PR190
continuation remains separately queued and unpromoted.

Follow-up: the requested garrison/mercenary caller tests are now recorded in
[the caller-history finding](2026-10-24-garrison-mercenary-caller-guards187.md),
promoted by [Research PR73](https://github.com/diegoami/imperial-conquest-2-research/pull/73)
at `2420f67295e39d3a37ce4ff4f7adf242822fe1cb`. It proves reachable zero and negative guards
through F31C, so the earlier stop must not be replaced with universal zero.
The historical tests, stop condition and blocked wording below retain their
original packet scope; they do not describe T212's current label. The promoted
follow-up resolves its specified caller histories without automatically widening
Main's approved implementation contract.

## Reusable rule and navigation data

[The implementation specification](../docs/navigation187-rule.md) and the
source-shaped reference model define eligibility, direct destinations,
intermediate waypoints and fallback choices. Interpreted tables, source pins,
results and a portable test matrix are in
[runs/experiments/data/run-exp-navigation187/](../runs/experiments/data/run-exp-navigation187/).

| Data | RAM address | DAT offset | Layout |
|---|---|---|---|
| Navigation points | 4790AC | 1F3EA | 58 signed 16-bit (X,Y) pairs, IDs 1–58 |
| Route sequences | 479194 | 1F4D2 | 3 groups × 7 rows × 8 signed 16-bit IDs; −1 padding |
| Geographic regions | 4794E8 | 1F81E | 8 strict-interior rectangles |
| Coordinate splits | 479528 | 1F85E | 6 signed 16-bit (Xlimit,Ylimit) pairs |

Addresses and offsets are hexadecimal. Point lookup uses base 4790A8 + 4×ID;
index 0 overlaps earlier data and is invalid. Groups are sea (1–25, hub 9),
Africa/Asia side (26–39, hub 32), Europe side (40–54, hub 43) and islands
(55–58). There is **no fourth route matrix or initialized island hub**.

The loader reads 232/336/64/24 bytes. These blocks match unique DAT slices and
all 30 retained generated live snapshots. They are static world data, not SAV
sections. Public files contain interpreted values and semantic pins; original
bytes stay private. The source ledger pins original EXE 9d753d5d and listing
2018c205, with function addresses and source lines.

1. **Geography:** the last matching strict-interior rectangle wins, otherwise
   region = −1. The coordinate-side bit starts at 1 and becomes 0 if any split
   has x < Xlimit and y < Ylimit. The historical “coast flag” is a coordinate
   partition, not water adjacency.
2. **Eligibility (CAB4):** the army and target share both geographic values,
   **or any fleet belongs to the army owner**. Direct line, reachability, fleet
   launch/cargo/moves/range are irrelevant here. EE60 first filters live,
   unembarked enemy candidates at war. An accepted target can be unreachable.
3. **Direct line (CB40):** medium continuity along the original integer line,
   excluding a mismatch at the final sampled point. Codes < 2 or ≥ 300 are sea;
   army/city markers are land and fleet markers sea. Adjacent destinations pass
   even across medium. Occupancy and contact belong to the walker.
4. **First destination:** a direct line selects the requested target. Otherwise
   DB38 calls D174 for matching geography or the ferry protocol for different
   geography. Already embarked armies use a separate ferry-target protocol.
5. **D174 waypoint:** prefer a common-visible point nearest the origin. Otherwise
   choose origin-visible entries and the target-visible node nearest the
   **origin**, then minimize route-row index separation. A primary connection
   always beats the hub fallback. Strict improvements preserve first ties.
   This is neither geometric shortest-path search nor nearest-to-target routing.
6. **Local fallback:** no origin entry uses CEC8 at origin; no target-side node
   uses CEC8 at target, with recursive waypoint selection when necessary. CEC8
   tests three clamped cells per direction, dx outer/dy inner, and the **last**
   successful direction wins. Failure is X = −1; Y then has no meaning.

The specification includes signed widths, endpoint rules, route sentinels,
index order and pseudocode. Every point in groups 0–2 appears in a route row
containing its hub, so a nonempty origin-entry list has a secondary route.

## Fleet and contact boundaries

A usable ferry is narrower than eligibility's any-own-fleet test: D9A8 requires
current-nation ownership, launched, empty and positive moves. Nearest wins;
first record wins ties. Foreign, building, loaded and zero-move fleets fail.
An adjacent usable fleet embarks immediately and spends both move budgets,
while returning intermediate X = −1. Negative output is not always failure.

A distant ferry control from army (98,40) to ship (105,40), with the shore at
x = 100/101, selects army approach (100,40) and ship destination (101,40).
Already at shore still writes a ferry request despite army X = −1. An embarked
army instead scans from its requested land target toward the ship, stores the
last land approach and spends two army moves. Oversized cargo trimming and
CD08's eastern coordinate exception are source evidence, not separately tested
capacity or special-area acceptance.

At final adjacent contact, a hostile army with budget dispatches AEE4, a hostile
city with budget B27C, and a non-war city F6D8 supply. Non-war army and zero-budget
hostile-army controls do not attack. Controls stop before the resolvers; battle,
siege and transfer outcomes are outside this result.

## Controls and exact stop condition

The public ledger contains 331 scalar controls, 20 ferry/contact/stack controls,
3 actual caller-entry controls, 3 full caller controls, 4 advanced score/fallback
controls and 35 original-line spot checks. These are **396 result rows, not
396 games**. Original RNG was never called in these bounded controls.

In the synthetic two-enemy fixture, changing one intermediate land cell to sea
keeps selected army 6, score 1010 and distance 10. Routing changes from the direct
target to point 32 (221,94), with separate eight-step traces and terminals.
Target-local fallback success, refusal and no-node refusal are also covered.

Two original artifacts require explicit limits:

- **Island graph:** forced group-3 graph controls read unrelated terrain words
  and uninitialized state. Enumeration of all 329 classical island land/land-marker
  cells finds at most one visible island point per region. Valid same-island
  pairs therefore share that point or use local fallback; graph fallback is
  unreachable in this fixed-world domain. This does not cover arbitrary maps.
- **Direct continuation:** DBA8 does not initialize its post-walk guard locally.
  With identical game state and three friendly blockers, a negative inherited
  word returns without movement and retains eight moves; a nonnegative word
  performs fallback/recursion and finishes at (100,41) with zero moves. Source
  data flow and three filled-stack controls resolve the normal F31C target-tree
  context and its tested recursive calls as nonnegative. Other caller histories
  are not universally established.

**Stop the broader continuation branch here.** Do not invent universal guard
initialization. The smallest next original control is the same generated
friendly-marker wall, capturing entry ESP−14 and ensuing movement at EC7D/ECD6
(garrison) and E913 (mercenary) call sites. No new owner save or screen is needed.
Keep T212 blocked for any contract requiring those unresolved callers; review
and promote the covered scope before Main changes behavior.

CB40's isolated coincident input also reads an uninitialized temporary. D174's
actual origin-then-target sequence makes target-node coincidence visible after
a preceding nonzero origin line; origin-node distance zero is excluded. The
reference model raises on unsupported isolated cases instead of inventing a rule.

## Final private regression and native boundary

After the public controls, the retained private #1388 pre-command state passes:
geography/model agreement, eligibility, blocked direct line, target 24 / score
828 / distance 28, waypoint 31 (189,104), and original terminal (212,96), zero moves.
Owner state, RAM, complete traces and private hashes remain private.

Native build 933a5d4a imports a private diagnostic container and verifies actor
units/type/quality/morale/resources/controller, all relations, and relevant
terrain/passability/occupancy. Its accepted MoveArmy, **supplied with the original
waypoint**, reaches (212,96), zero moves. This confirms the conditioned walker;
it does not prove native eligibility/navigation, whole End turn or RNG parity.

The public model accepts interpreted tables and a cell(x,y) callback. Original
instruction replay additionally needs retained authorized original assets and
generated reference state. The public matrix gives 15 portable semantic fixture
descriptions. No fresh game, broad 16-start matrix, production/save-schema change
or native Windows access was used. Economy/diplomacy/fleet work remains authorized
and resumable in its separate setup notes. Research promotion precedes Main use.
