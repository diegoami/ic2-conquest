# Garrison and mercenary movement: the inherited guard has a reachable history

**Tag:** [confirmed, partial: original instructions, synthetic caller histories,
stack-write provenance and observer/plain identity].
**Tasks:** [conquest #187](https://github.com/diegoami/ic2-conquest/issues/187),
[Main T212 / #1394](https://github.com/diegoami/imperial_conquest_2/issues/1394).
Promoted by [Research PR73](https://github.com/diegoami/imperial-conquest-2-research/pull/73)
at `2420f67295e39d3a37ce4ff4f7adf242822fe1cb`.
Use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/2420f67295e39d3a37ce4ff4f7adf242822fe1cb/docs/reports/2026-10-24-garrison-mercenary-caller-guards187.md).
Research freshly reproduced every field of all four ledgers, all 88 unobserved
RAM/stack identities and 20 input pairs, with no normalization. It rechecked
the source writers/call sites; see the [safe receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/2420f67295e39d3a37ce4ff4f7adf242822fe1cb/docs/data/navigation187-callers-intake-v1.json).
No fresh game, native comparison, production change or task-label change here.
Main T212 is in progress under a narrowed enemy-army contract; promotion alone
does not expand it. The separate PR190 continuation remains unpromoted.

## Answer

The requested caller tests are complete. The original EBE8 garrison and E84C
mercenary routines do **not** initialize DBA8's direct-continuation guard.
In a full F31C army phase, however, its provenance can be traced. Mercenary
entry inherits zero from the exhausted EE60 army-loop counter. A later garrison
call can inherit zero **or −1**, depending on whether the preceding mercenary
attempt returned no destination. The negative case is reachable through the
original phase's own branches; it is not merely arbitrary stack noise.

Do not initialize every invocation to zero. Do not treat every garrison call as
nonnegative, or propagate every earlier refusal regardless of call depth. The
covered phase histories and their distinct guard values are specified below.

## Minimal paired result

Army (150,70), nine moves, three friendly blockers immediately east. Garrison
target is (155,70) for the nearest-city branch or (170,70) for the capital branch.
The first target-tree branch seeks mercenaries. A potential offer is at (160,80),
across the geographic classification boundary, with a sea cell blocking its
direct line and no fleet available.

| Only changed original input | Mercenary call | Garrison guard | Terminal / moves |
|---|---|---:|---|
| Offer troop word = −1 (absent) | E84C makes no movement request | 0 | (150,70) / 0 |
| Offer troop word = 1,000 (present) | DBA8 → DB38 refuses; no moves spent | −1 | (150,70) / 9 |

Every other captured game-RAM byte is identical. The sole difference is the
signed word at `49DA18` (two bytes). Both garrison branches reproduce this with
stack fills 0/1/FF at two valid low/high 32-bit stack locations. The offer is in
a non-hostile city; its failed navigation does not imply the offer was hired.

A clear-path control with the negative guard still walks normally. The guard
controls **post-walk fallback and recursion**, not permission to make the first
direct walk. Moving the wall two cells farther east gives another contrast:
with an absent offer the original recurses and ends (152,71) with signed moves
**−1**; with the present refused offer it stops at (152,70), retaining seven
moves. The extra decrement after a fallback walk is unconditional, so the
observed −1 is preserved, not clamped away by this analysis.

## Evidence layers and scope

Eighty-eight bounded original executions, not games:

- 24 isolated full EBE8/E84C callers: three caller branches, blocked/clear,
  stack fill and location controls. First guard bytes have no writer inside
  those routines. Fills 0/1/FF produce 0/257/−1. In the blocked fixture,
  nonnegative guards finish (100,41) with zero moves; negative guards retain
  (100,40) and eight moves. All clear controls finish (108,40), zero moves.
- 24 full F31C controls naturally reach the requested garrison/mercenary caller.
  Garrison follows an ordinary no-ferry resupply refusal and inherits coordinate
  Y = 40; mercenary entry inherits counter zero. Both stack locations and fills
  agree. The full budget is nine in these fixtures, not the isolated eight.
- 32 full F31C offer/no-offer history controls establish the paired result above,
  including clear-path controls and both garrison destinations.
- Eight full F31C progress-then-block controls establish the recursion contrast,
  including the signed negative terminal budget.

All original RNG counts are zero; no game/helper/selector/Random/presentation
routine is replaced. Each case also runs **without any observer hooks**. All
88 complete captured game-RAM blocks and all 64 KiB of diagnostic stack match
the observed run/write ledger exactly. Twenty offer/no-offer pairs are checked
for the exact single-word input difference.

These are generated diagnostic maps and projected save containers, not a fresh
campaign or original Save As. City coordinates and the tested corridor are
explicitly synthesized; retained scenario tables are not asserted to form a
new playable scenario. No owner #1355/#1388 state is used. No native comparison,
whole End turn, tactical resolution or Windows acceptance is claimed.

## Source-shaped caller contract

Original EXE SHA256 starts `9d753d5d`; pinned listing starts `2018c205`. Complete
pins, addresses and semantic stack notes are in
`runs/experiments/data/run-exp-navigation187-callers/source-ledger-v1.json`.
Addresses below are hexadecimal; guards are signed 16-bit words.

Let **S** be F31C's stack pointer immediately before its ordinary no-stack-arg
calls. Its direct DBA8 invocation reads its guard at S−18. Its nested
EBE8/E84C → DBA8 invocation reads the deeper slot at **S−42**. These slots must
not be conflated.

| Covered call history | Word inherited by the nested movement call | Observed last writer |
|---|---|---|
| F31C → E84C → DBA8 | EE60's exhausted army-loop counter, 0 | `44EFA7` |
| F31C ordinary destination returns unmoved, then EBE8 | Current-coordinate Y, 40 in the control | `44901F`, upper word of packed coordinate |
| F31C → E84C finds no offer, then EBE8 | Counter still 0 | `44EFA7` |
| F31C → E84C → DBA8/DB38 refuses, then EBE8 | Explicit no-destination sentinel, −1 | `44DB47` |
| Recursive DBA8 after a walker call | Prior D734 goal X, nonnegative in these controls | `44D73D` |
| Arbitrary standalone EBE8/E84C root | Caller residue, not initialized locally | No writer in the isolated controls |

EE60 is called with one stack argument: EBP = S−12, so its remaining-army
counter at EBP−30 is S−42 and exits at zero for the nonempty table containing
the active army. EBE8 and E84C each save five DWORDs. Their child DBA8 entry is
S−28, and entry ESP−14 is the same S−42 word. Their local distance/city lookups
do not overwrite this word on the covered paths.

The ordinary shallower DBA8 return calls distance at `44DC7A`; distance writes
the packed current coordinate at `44901F`, with Y aliasing S−42. A no-waypoint
return here therefore differs from a refusal inside E84C's deeper DBA8 frame.
The latter writes its actual local intermediate X directly to S−42; `44DB47`
sets it to −1. The subsequent AAB4 movement check and EBE8 scans preserve it.

Garrison call-site mapping: **EC7D = capital** (return EC82), **ECD6 = nearest
city** (return ECDB). Mercenary: E913 (return E918). The initial follow-up plan
reversed the two garrison address labels; observed destinations and instruction
flow corrected the labels. Measured semantic case names were already correct.

For a covered direct-line call, the relevant original wrapper behavior is:

```text
walk(requestedTarget)                       # happens regardless of guard sign
if moves unchanged and moves > 0 and inheritedGuard >= 0:
    intermediate = localFallback(currentPosition)
    if intermediate.X != -1: walk(intermediate)
    moves -= 1                             # even if that walk spent the last move
if distance(currentPosition, requestedTarget) > 1 and moves > 0
   and currentGuard >= 0 and requestedTarget.X >= 0:
    recurse(requestedTarget)
```

For a blocked medium line, DB38 writes the intermediate word explicitly before
this logic. The earlier navigation187 waypoint/ferry specification still applies.
A logical implementation can model the covered call history; it need not expose
or emulate raw stack addresses. But replacing this with a universal fresh zero
would fail the original paired controls.

## Deliverable, limits and Main handoff

Public scalar results: `controls-v1.json`, `parent-controls-v1.json`,
`history-controls-v1.json`, `progress-controls-v1.json`, `summary-v3.json`,
`paired-inputs-v3.json`, `observer-identity-v3.json`. Runners are in
`runs/experiments/navigation187-callers/`; all outputs are exclusive/versioned.
The first audit had an incorrect clear-path expected distance for an eight-move
budget; its failed log is retained. Corrected v2 and expanded v3 pass; no game
measurement was replaced.

Private projected save citations (before/after pairs; synthetic input based on
the retained turn-0720 generated Rome state):

- `controls-v1/000-garrison-nearest-blocked-fill0-sp80f000/before.SAV` and
  `after.SAV`, plus the capital/mercenary and other stack cases.
- `parent-v1/000-garrison-nearest-blocked-fill0-sp80f000/before.SAV` and
  `after.SAV`; mercenary parent example is case016.
- `history-v1/000-garrison-nearest-blocked-offers0-fill0-sp80f000/before.SAV`
  and `after.SAV`, paired with case008 (`offers1`). Capital pair is case016/024.
- `progress-v1/000-garrison-nearest-blocked-offers0-fill0-sp80f000/before.SAV`
  and `after.SAV`, paired with case002 (`offers1`).

Raw RAM/SAV containers, full instruction/stack traces and private hashes remain
private under the task artifacts, per #187. No raw asset upload or owner input
is required to read the public decision/evidence ledger.

The requested garrison/mercenary tests now replace an unspecified gap with
explicit, reproducible **positive and negative** F31C histories. This is not a
universal contract for every possible earlier waypoint, failed battle, embarked,
homeland-interception or arbitrary external caller. Do not silently extend
T212's approved scope or claim all strategic callers equivalent. Research has
reviewed and promoted this follow-up. Main still owns any expansion of its
production contract, task status and implementation acceptance.
